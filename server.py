from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from flask import Flask, jsonify, request, send_from_directory

from xuanxue_engine import BaziInput, IMPLEMENTED_SYSTEMS, calculate_bazi, calculate_system
from xuanxue_engine import registry as engine_registry
from xuanxue_engine.fengshui import evaluate_external_environment
from xuanxue_engine.map_provider_tencent import (
    collect_nearby_poi_signals,
    geocode_address,
    has_tencent_map_key,
    is_quota_exceeded_error,
    place_search,
    static_map_url,
)
from xuanxue_engine.parsing import parse_birth_details, parse_datetime_from_text


APP_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = APP_DIR.parent


def resolve_vault_dir() -> Path:
    configured = os.environ.get("GEEKSPACE_VAULT_DIR", "").strip()
    candidates: list[Path] = []

    if configured:
        configured_path = Path(configured).expanduser()
        if not configured_path.is_absolute():
            configured_path = (APP_DIR / configured_path).resolve()
        candidates.append(configured_path)

    candidates.extend(
        [
            APP_DIR / "runtime" / "xuanxue-knowledge-vault",
            APP_DIR / "xuanxue-knowledge-vault",
            WORKSPACE_DIR / "xuanxue-knowledge-vault",
        ]
    )

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return candidates[0] if candidates else APP_DIR / "runtime" / "xuanxue-knowledge-vault"


VAULT_DIR = resolve_vault_dir()
DOSSIER_DIR = VAULT_DIR / "wiki" / "dossiers"
ENGINE_DIR = VAULT_DIR / "wiki" / "engine"
CALCULATOR_DIR = ENGINE_DIR / "calculators"
HERMES_ENV = Path.home() / ".hermes" / ".env"
BASE_URL = os.environ.get("GEEKSPACE_API_BASE_URL", "https://geekspace.cloud/v1").strip() or "https://geekspace.cloud/v1"
DEFAULT_MODEL = os.environ.get("GEEKSPACE_DEFAULT_MODEL", "gpt-5.5").strip() or "gpt-5.5"
FALLBACK_MODELS = ["gpt-5.5", "gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo", "gpt-4.1-mini"]
LOCAL_MODEL_ID = "local-vault"
AUTO_MODEL_ID = "auto"
BUILD_STAMP = "2026-06-08-alchemy-modern-21"

DOSSIER_ORDER = [
    "yijing_and_symbolism",
    "bazi",
    "ziwei_doushu",
    "qizheng_siyu",
    "qimen_dunjia",
    "liu_ren",
    "liuyao_and_meihua",
    "date_selection",
    "name_studies",
    "physiognomy",
    "fengshui",
    "daoist_arts",
    "western_astrology",
    "vedic_astrology",
    "tarot",
    "kabbalah",
    "alchemy_and_hermeticism",
    "onmyodo",
    "numerology",
    "human_design",
    "modern_esotericism",
]

SECTION_WEIGHTS = {
    "root": 45,
    "sources": 20,
    "scholars": 18,
    "controversies": 17,
}

SYSTEM_LABELS = {
    "yijing_and_symbolism": "易经与象数",
    "bazi": "八字",
    "ziwei_doushu": "紫微斗数",
    "qizheng_siyu": "七政四余",
    "qimen_dunjia": "奇门遁甲",
    "liu_ren": "大六壬",
    "liuyao_and_meihua": "六爻与梅花易数",
    "date_selection": "择日",
    "name_studies": "姓名学",
    "physiognomy": "相术",
    "fengshui": "风水",
    "daoist_arts": "道术",
    "western_astrology": "西洋占星",
    "vedic_astrology": "印度占星",
    "tarot": "塔罗",
    "kabbalah": "卡巴拉",
    "alchemy_and_hermeticism": "炼金术与赫尔墨斯主义",
    "onmyodo": "阴阳道",
    "numerology": "数字命理",
    "human_design": "人类图",
    "modern_esotericism": "现代神秘学",
}


app = Flask(__name__, static_folder=str(APP_DIR), static_url_path="")


@dataclass
class DossierPack:
    key: str
    title: str
    files: dict[str, Path]
    calculator: Path
    score: int
    summary: str
    status: str


HIGH_RISK_FUTURE_YEAR = 2050
SUICIDE_MARKERS = ("自杀", "自殘", "自残", "不想活", "活不下去", "结束生命", "轻生")
MEDICAL_OVERRIDE_MARKERS = ("停药", "停藥", "不要治疗", "不要治療", "替代治疗", "替代治療", "符水治病", "法事治病")
MEDICAL_CONTEXT_MARKERS = ("肿瘤", "腫瘤", "癌", "医生", "醫生", "治疗", "治療", "手术", "手術", "用药", "用藥")
FINANCIAL_OVERREACH_MARKERS = ("梭哈", "借来的钱", "借來的錢", "全部身家", "all in", "margin", "贷款炒股", "貸款炒股")


def parsed_birth_issue(parsed: Any) -> str:
    parse_error = str(getattr(parsed, "parse_error", "") or "").strip()
    if parse_error:
        return parse_error
    if bool(getattr(parsed, "has_conflict", False)):
        return str(getattr(parsed, "conflict_note", "") or "出生信息存在冲突，请先确认。")
    birth_dt = getattr(parsed, "birth_datetime", None)
    if birth_dt and getattr(birth_dt, "year", 0) >= HIGH_RISK_FUTURE_YEAR:
        return "识别到的出生年份明显超出现实范围，请先确认出生日期是否填写正确。"
    return ""


def safety_screen(question: str) -> dict[str, Any] | None:
    if any(token in question for token in SUICIDE_MARKERS):
        return {
            "type": "crisis",
            "title": "先不做玄学推演，先处理眼前安全",
            "summary": "你现在最需要的不是起盘，而是立刻联系现实中的人和紧急支持。",
            "actions": [
                "如果你有立刻伤害自己的风险，请马上拨打当地急救电话或直接去最近的急诊。",
                "立刻联系一个你信任的人，让对方现在陪着你，不要一个人扛。",
                "把刀片、药物、绳索和其他可能伤害自己的东西先移开。",
            ],
            "cautions": [
                "我不能帮助你评估自杀是否应该发生，也不能把这种问题交给玄学系统处理。",
            ],
        }
    if any(token in question for token in MEDICAL_OVERRIDE_MARKERS) and any(token in question for token in MEDICAL_CONTEXT_MARKERS):
        return {
            "type": "medical",
            "title": "这类问题不能用玄学替代治疗决策",
            "summary": "停药、改治疗或用法事替代医生方案，都属于高风险医疗决策。",
            "actions": [
                "先按医生当前方案执行，不要自行停药或延误治疗。",
                "如果你对方案不放心，尽快找线下医生做第二意见。",
                "玄学内容最多只能作为情绪安定或文化参考，不能替代诊疗。",
            ],
            "cautions": [
                "系统不会对停药、替代治疗或延误就医给出支持性建议。",
            ],
        }
    if any(token in question.lower() for token in FINANCIAL_OVERREACH_MARKERS):
        return {
            "type": "financial",
            "title": "先把现实风险拦住，再谈玄学参考",
            "summary": "借贷、加杠杆或拿全部身家做单一押注，已经超出玄学建议适用边界。",
            "actions": [
                "不要基于玄学结果做梭哈、借贷加仓或单笔重仓决定。",
                "先设定能承受的最大亏损，再考虑是否继续评估。",
                "重大投资请结合持牌金融建议和你自己的现金流安全线。",
            ],
            "cautions": [
                "系统不会为高杠杆、借贷或孤注一掷型投资背书。",
            ],
        }
    return None


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def geekspace_key() -> str:
    env_values = load_env_file(HERMES_ENV)
    return (
        os.environ.get("GEEKSPACE_API_KEY")
        or env_values.get("GEEKSPACE_API_KEY")
        or env_values.get("OPENAI_API_KEY")
        or ""
    )


def api_headers() -> dict[str, str]:
    api_key = geekspace_key()
    if not api_key:
        raise RuntimeError(f"No API key found in {HERMES_ENV}")
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def collapse_text(text: str) -> str:
    lines = [line.strip() for line in strip_frontmatter(text).splitlines() if line.strip()]
    return "\n".join(lines)


FOLLOW_UP_SECTION_RE = re.compile(
    r"^(原问题|原始问题|主问题|问题|补充信息|补充内容|补充|继续补充|追问|追加信息|信息补充|补充问题)\s*[:：]\s*(.*)$"
)
FOLLOW_UP_STRIP_MARKERS = (
    "最近",
    "近期",
    "这阵子",
    "当下",
    "眼前",
    "目前",
    "现在",
)
FOLLOW_UP_STRONG_CONTEXT_MARKERS = (
    "长期",
    "长远",
    "趋势",
    "走势",
    "命盘",
    "八字",
    "人类图",
    "紫微",
    "占星",
    "星盘",
    "出生",
    "生于",
)


def normalize_multi_turn_question(question: str) -> str:
    text = collapse_text(str(question or ""))
    if not text:
        return ""

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return text

    original_parts: list[str] = []
    supplement_parts: list[str] = []
    section = "original"
    saw_sections = False

    for index, line in enumerate(lines):
        match = FOLLOW_UP_SECTION_RE.match(line)
        if match:
            saw_sections = True
            label, content = match.groups()
            section = "supplement" if label in {"补充信息", "补充内容", "补充", "继续补充", "追问", "追加信息", "信息补充", "补充问题"} else "original"
            if content.strip():
                if section == "supplement":
                    supplement_parts.append(content.strip())
                else:
                    original_parts.append(content.strip())
            continue

        if not saw_sections and index == 0:
            original_parts.append(line)
            continue
        if section == "supplement":
            supplement_parts.append(line)
        else:
            original_parts.append(line)

    if not saw_sections:
        original_parts = [lines[0]]
        supplement_parts = lines[1:]

    original = " ".join(part for part in original_parts if part).strip()
    supplement = " ".join(part for part in supplement_parts if part).strip()

    if supplement:
        if any(marker in supplement for marker in FOLLOW_UP_STRONG_CONTEXT_MARKERS) or re.search(r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", supplement) or re.search(r"\b\d{1,2}:\d{2}\b", supplement):
            for marker in FOLLOW_UP_STRIP_MARKERS:
                original = original.replace(marker, "")
            original = re.sub(r"\s+", " ", original).strip()
        return "；".join(part for part in [supplement, original] if part).strip()

    return original or text


def safe_read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig") if path.exists() else ""


def extract_frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+)$", text)
    return match.group(1).strip() if match else ""


def base_dossier_title(key: str) -> str:
    fallback = SYSTEM_LABELS.get(key, key.replace("_", " "))
    root = DOSSIER_DIR / f"dossier_{key}.md"
    if not root.exists():
        return fallback
    title = extract_frontmatter_value(safe_read(root), "title")
    return title or fallback


def dossier_file_map(key: str) -> dict[str, Path]:
    return {
        "root": DOSSIER_DIR / f"dossier_{key}.md",
        "sources": DOSSIER_DIR / f"dossier_{key}_sources.md",
        "scholars": DOSSIER_DIR / f"dossier_{key}_scholars.md",
        "controversies": DOSSIER_DIR / f"dossier_{key}_controversies.md",
    }


def calculator_spec_path(key: str) -> Path:
    return CALCULATOR_DIR / f"{key}_calculator_spec.md"


def calculator_implemented(key: str) -> bool:
    return key in IMPLEMENTED_SYSTEMS or key in engine_registry.IMPLEMENTED_SYSTEMS


def compute_pack(key: str) -> DossierPack:
    files = dossier_file_map(key)
    calculator = calculator_spec_path(key)
    score = 0
    available_parts = 0
    for part, weight in SECTION_WEIGHTS.items():
        if files[part].exists():
            score += weight
            available_parts += 1
    root_text = safe_read(files["root"])
    title = base_dossier_title(key)
    summary = extract_frontmatter_value(root_text, "summary") or title
    status = "deep" if score >= 80 else "seeded" if score >= 45 else "missing"
    if available_parts == 0:
        status = "missing"
    return DossierPack(
        key=key,
        title=title,
        files=files,
        calculator=calculator,
        score=score,
        summary=summary,
        status=status,
    )


def all_packs() -> list[DossierPack]:
    return [compute_pack(key) for key in DOSSIER_ORDER]


def vault_overview() -> dict[str, Any]:
    packs = all_packs()
    total_score = sum(pack.score for pack in packs)
    max_score = len(packs) * sum(SECTION_WEIGHTS.values())
    overall_percent = round(total_score / max_score * 100) if max_score else 0
    return {
        "overallPercent": overall_percent,
        "completedDeepCount": sum(1 for pack in packs if pack.status == "deep"),
        "seededCount": sum(1 for pack in packs if pack.status == "seeded"),
        "missingCount": sum(1 for pack in packs if pack.status == "missing"),
        "systems": [
            {
                "key": pack.key,
                "title": pack.title.replace("资料包", "").strip(),
                "score": pack.score,
                "status": pack.status,
                "summary": pack.summary,
                "parts": {part: path.exists() for part, path in pack.files.items()},
                "calculatorReady": pack.calculator.exists(),
                "calculatorImplemented": calculator_implemented(pack.key),
                "questionGuide": system_question_guide(pack.key),
            }
            for pack in packs
        ],
    }


def relevant_packs(question: str, limit: int = 6) -> list[DossierPack]:
    question = normalize_multi_turn_question(question)
    lowered = question.lower()
    tags = infer_question_tags(question)
    birth_context = any(
        token in question
        for token in [
            "出生",
            "生于",
            "农历",
            "阳历",
            "公历",
            "时辰",
            "凌晨",
            "早上",
            "上午",
            "中午",
            "下午",
            "晚上",
            "子时",
            "丑时",
            "寅时",
            "卯时",
            "辰时",
            "巳时",
            "午时",
            "未时",
            "申时",
            "酉时",
            "戌时",
            "亥时",
        ]
    )
    scored: list[tuple[int, DossierPack]] = []
    for pack in all_packs():
        text_parts = []
        for path in pack.files.values():
            if path.exists():
                text_parts.append(collapse_text(safe_read(path))[:2500])
        haystack = "\n".join(text_parts).lower()
        label = SYSTEM_LABELS.get(pack.key, pack.key).lower()
        score = 0
        for token in re.findall(r"[\w\u4e00-\u9fff]+", lowered):
            if len(token) < 2:
                continue
            if token in label:
                score += 8
            score += haystack.count(token)
        mode = pack_mode(pack.key)
        if "timing" in tags and mode == "timing":
            score += 35
        if pack.key == "date_selection" and any(token in question for token in ["好日子", "吉日", "黄道吉日", "黃道吉日"]):
            score += 65
        if "career" in tags and mode == "destiny":
            score += 28
        if "relationship" in tags and mode == "destiny":
            score += 28
        if "identity" in tags and mode == "destiny":
            score += 24
        if any(token in question for token in ["名字", "姓名", "起名", "取名", "候选名", "起一个名字", "取一个名字"]) and pack.key == "name_studies":
            score += 120
        if "space" in tags and mode == "space":
            score += 35
        if "ritual" in tags and mode == "ritual":
            score += 35
        if "general" not in tags and mode == "symbolic":
            score += 8
        if pack.calculator.exists() and (mode in tags or ("career" in tags and mode == "destiny")):
            score += 10
        if any(token in question for token in ["名字", "姓名", "起名", "改名", "品牌名", "店名", "艺名", "笔名"]) and pack.key == "name_studies":
            score += 60
        if any(token in question for token in ["六爻", "梅花", "起卦", "动爻", "本卦", "变卦"]) and pack.key == "liuyao_and_meihua":
            score += 60
    if any(token in question for token in ["阴阳道", "鬼门", "东北", "西南", "方位禁忌", "出行方向"]) and pack.key == "onmyodo":
        score += 48
    if any(token in question for token in ["面相", "相术", "额头", "眼神", "鼻梁", "气色"]) and pack.key == "physiognomy":
        score += 48
        if any(token in question.lower() for token in ["astrology", "natal", "birth chart", "moon sign", "rising sign", "ascendant"]) and pack.key == "western_astrology":
            score += 60
        if any(token in question for token in ["星盘", "星盤", "西占", "占星", "太阳星座", "月亮星座", "上升"]) and pack.key == "western_astrology":
            score += 60
        if any(token in question.lower() for token in ["vedic", "sidereal", "nakshatra", "lahiri"]) and pack.key == "vedic_astrology":
            score += 60
        if any(token in question for token in ["吠陀", "印度占星", "印度占星术", "月宿", "宿曜", "恒星黄道"]) and pack.key == "vedic_astrology":
            score += 60
        if any(token in question for token in ["紫微", "斗数", "斗數", "命宫", "身宫", "大限", "流年"]) and pack.key == "ziwei_doushu":
            score += 60
        if any(token in question for token in ["星盘", "星盤", "西占", "占星", "太阳星座", "月亮星座", "上升"]) and pack.key == "western_astrology":
            score += 60
        if any(token in question for token in ["吠陀", "印度占星", "印度占星术", "月宿", "宿曜", "恒星黄道"]) and pack.key == "vedic_astrology":
            score += 60
        if any(token in question for token in ["紫微", "斗数", "斗數", "命宫", "身宫", "大限", "流年"]) and pack.key == "ziwei_doushu":
            score += 60
        if any(token in question for token in ["七政", "四余", "罗喉", "计都", "月孛", "紫气"]) and pack.key == "qizheng_siyu":
            score += 60
        if birth_context and mode == "destiny":
            score += 24
        if birth_context and mode in {"timing", "space", "ritual", "symbolic"} and not ({"timing", "space", "ritual"} & tags):
            score -= 40
        if score == 0 and pack.status == "deep":
            score = 1
        scored.append((score, pack))
    scored.sort(key=lambda item: (item[0], item[1].score), reverse=True)
    selected = [pack for score, pack in scored if score > 0][:limit]
    if len(selected) < min(limit, 4):
        for _, pack in scored:
            if pack not in selected:
                selected.append(pack)
            if len(selected) >= min(limit, 4):
                break
    return selected


def all_ranked_packs(question: str) -> list[DossierPack]:
    question = normalize_multi_turn_question(question)
    selected = relevant_packs(question, limit=len(DOSSIER_ORDER))
    seen = set()
    ordered: list[DossierPack] = []
    for pack in selected:
        ordered.append(pack)
        seen.add(pack.key)
    for pack in all_packs():
        if pack.key not in seen:
            ordered.append(pack)
    return ordered


def infer_question_tags(question: str) -> set[str]:
    tags: set[str] = set()
    text = question.lower()
    if any(token in question for token in ["搬家", "房子", "住宅", "办公室", "城市", "方位", "住哪", "住处"]):
        tags.add("space")
    if any(token in question for token in ["什么时候", "何时", "今年", "本月", "最近", "时机", "要不要", "适合", "能不能"]):
        tags.add("timing")
    if any(token in question for token in ["事业", "工作", "职业", "创业", "财运", "赚钱", "发展"]):
        tags.add("career")
    if any(token in question for token in ["感情", "婚姻", "恋爱", "伴侣", "对象"]):
        tags.add("relationship")
    if any(token in question for token in ["修行", "仪式", "符", "法事", "驱邪", "护身", "修炼"]):
        tags.add("ritual")
    if any(token in text for token in ["who am i", "personality", "天赋", "性格", "适合什么人", "我是什么样"]):
        tags.add("identity")
    if not tags:
        tags.add("general")
    return tags


def pack_mode(key: str) -> str:
    if key in {"fengshui", "onmyodo"}:
        return "space"
    if key in {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "date_selection"}:
        return "timing"
    if key in {"daoist_arts", "alchemy_and_hermeticism", "kabbalah"}:
        return "ritual"
    if key in {"tarot", "modern_esotericism", "yijing_and_symbolism"}:
        return "symbolic"
    return "destiny"


REQUIRED_INPUT_HINTS = {
    "bazi": ["出生年月日时", "出生地", "性别"],
    "ziwei_doushu": ["出生年月日时", "性别"],
    "qizheng_siyu": ["出生年月日时", "出生地"],
    "western_astrology": ["出生年月日时", "出生地"],
    "vedic_astrology": ["出生年月日时", "出生地"],
    "qimen_dunjia": ["起问时间", "具体问题"],
    "liu_ren": ["占问时间", "具体问题"],
    "liuyao_and_meihua": ["卦象或起卦方式", "具体问题"],
    "date_selection": ["事项类型", "候选日期", "地点"],
    "fengshui": ["城市或地址", "坐向或平面图"],
    "name_studies": ["姓名或候选名", "用途"],
    "tarot": ["牌阵或抽牌结果", "问题时间范围"],
    "human_design": ["出生年月日时", "出生地"],
}


def question_has_datetime(question: str) -> bool:
    return bool(
        re.search(r"\d{4}[-/年.]\d{1,2}[-/月.]\d{1,2}", question)
        or re.search(r"\d{1,2}[:：]\d{2}", question)
        or any(token in question for token in ["子时", "丑时", "寅时", "卯时", "辰时", "巳时", "午时", "未时", "申时", "酉时", "戌时", "亥时"])
    )


def missing_input_hints(pack: DossierPack, question: str) -> list[str]:
    required = REQUIRED_INPUT_HINTS.get(pack.key, [])
    if not required:
        return []
    missing: list[str] = []
    has_datetime = question_has_datetime(question)
    has_location = any(token in question for token in ["北京", "上海", "广州", "深圳", "杭州", "成都", "城市", "地址", "小区", "办公室", "住宅", "家里", "坐向", "平面图"])
    has_gender = any(token in question for token in ["男", "女", "男性", "女性"])
    has_hexagram = any(token in question for token in ["本卦", "变卦", "动爻", "摇卦", "卦象", "上卦", "下卦"])
    has_cards = any(token in question for token in ["塔罗", "牌阵", "正位", "逆位", "抽到"])
    has_candidate_date = bool(re.search(r"\d{1,2}月\d{1,2}日|\d{4}[-/]\d{1,2}[-/]\d{1,2}", question))

    for item in required:
        if "出生年月日时" in item and not has_datetime:
            missing.append(item)
        elif item == "出生地" and not has_location:
            missing.append(item)
        elif item == "性别" and not has_gender:
            missing.append(item)
        elif item in {"起问时间", "占问时间"} and not has_datetime:
            missing.append(item)
        elif "卦象" in item and not has_hexagram:
            missing.append(item)
        elif item in {"候选日期"} and not has_candidate_date:
            missing.append(item)
        elif item in {"城市或地址", "坐向或平面图", "地点"} and not has_location:
            missing.append(item)
        elif "牌阵" in item and not has_cards:
            missing.append(item)
    return missing[:3]


def personal_info_parse_note(pack: DossierPack, question: str) -> str:
    birth_tokens = [
        "\u51fa\u751f",
        "\u751f\u4e8e",
        "\u519c\u5386",
        "\u9633\u5386",
        "\u516c\u5386",
        "\u65f6\u8fb0",
        "\u4e0b\u5348",
        "\u4e0a\u5348",
    ]
    has_birth_context = any(token in question for token in birth_tokens)
    if pack.key == "bazi" and has_birth_context and not parse_datetime_from_text(question):
        if "\u519c\u5386" in question:
            return "\u5df2\u68c0\u6d4b\u5230\u4f60\u63d0\u4f9b\u4e86\u519c\u5386\u6216\u4e2d\u6587\u65f6\u8fb0\u4fe1\u606f\uff0c\u4f46\u5f53\u524d\u672c\u5730\u516b\u5b57\u8ba1\u7b97\u5668\u53ea\u76f4\u63a5\u8bc6\u522b\u516c\u5386\u683c\u5f0f\uff0c\u4f8b\u5982 1990-05-12 14:30\u3002"
        return "\u5df2\u68c0\u6d4b\u5230\u4f60\u63d0\u4f9b\u4e86\u51fa\u751f\u4fe1\u606f\uff0c\u4f46\u5f53\u524d\u672c\u5730\u516b\u5b57\u8ba1\u7b97\u5668\u53ea\u76f4\u63a5\u8bc6\u522b\u6807\u51c6\u516c\u5386\u65f6\u95f4\u5b57\u7b26\u4e32\u3002"
    if pack.key in {"ziwei_doushu", "qizheng_siyu", "western_astrology", "vedic_astrology", "human_design"} and has_birth_context:
        if not calculator_implemented(pack.key):
            return "\u5df2\u68c0\u6d4b\u5230\u4f60\u63d0\u4f9b\u4e86\u4e2a\u4eba\u51fa\u751f\u4fe1\u606f\uff0c\u4f46\u672c\u4f53\u7cfb\u5f53\u524d\u53ea\u6709\u89c4\u5219\u548c\u8ba1\u7b97\u89c4\u683c\uff0c\u8fd8\u6ca1\u6709\u63a5\u5165\u771f\u5b9e\u672c\u5730\u6392\u76d8\u5668\u3002"
    return ""


def pack_focus_text(key: str) -> str:
    if key == "physiognomy":
        return "外貌观察、部位特征和动态神态的非决定性倾向"
    if key == "daoist_arts":
        return "法脉来源、仪式结构、禁忌边界和修炼语境"
    if key == "alchemy_and_hermeticism":
        return "转化阶段、元素行星对应和精神/物质层次"
    if key == "modern_esotericism":
        return "概念分类、来源审查、风险分级和可用边界"
    mode = pack_mode(key)
    if mode == "space":
        return "空间格局、方位、居所与环境关系"
    if mode == "timing":
        return "当前时机、事件走势和行动窗口"
    if mode == "ritual":
        return "仪式结构、修炼语境和象征对应"
    if mode == "symbolic":
        return "象征主题、当前处境和问题所映射的结构"
    return "个人结构、阶段运势和长期倾向"


def extract_evidence(path: Path, limit: int = 2) -> list[str]:
    if not path.exists():
        return []
    lines = []
    for raw in strip_frontmatter(safe_read(path)).splitlines():
        line = raw.strip().lstrip("-").strip()
        if not line or line.startswith("#") or line.startswith("[["):
            continue
        if len(line) < 8:
            continue
        lines.append(line)
    deduped: list[str] = []
    for line in lines:
        if line not in deduped:
            deduped.append(line)
        if len(deduped) >= limit:
            break
    return deduped


def local_system_answer(pack: DossierPack, question: str, tags: set[str]) -> dict[str, Any]:
    mode = pack_mode(pack.key)
    evidence = []
    for part in ["root", "sources", "controversies"]:
        evidence.extend(extract_evidence(pack.files[part], limit=1))
    if pack.calculator.exists():
        evidence.extend(extract_evidence(pack.calculator, limit=1))
    evidence = evidence[:2]
    evidence_text = "；".join(evidence) if evidence else pack.summary
    if calculator_implemented(pack.key):
        calculator_note = "本体系已接入真实本地计算器，满足输入条件时可以直接排盘或计算。"
    elif pack.calculator.exists():
        calculator_note = "本体系已有计算器规格，但具体算法尚未接入，本轮仍以资料库综合和规则层提示为主。"
    else:
        calculator_note = "本体系目前以资料库综合为主，尚未建立完整本地计算器规格。"
    missing_inputs = missing_input_hints(pack, question)
    parse_note = personal_info_parse_note(pack, question)
    computed_note = ""
    if pack.key == "bazi":
        birth_dt = parse_datetime_from_text(question)
        if birth_dt:
            try:
                chart = calculate_bazi(BaziInput(birth_dt))
                pillar_text = "、".join(
                    chart["pillars"][name]["text"] for name in ["year", "month", "day", "hour"]
                )
                day_master = chart["day_master"]
                computed_note = (
                    f"已按公历时间生成八字粗排：{pillar_text}；"
                    f"日主为{day_master['stem']}{day_master['element']}{day_master['polarity']}。"
                    f"五行计数：{chart['five_element_counts']}。"
                )
            except Exception as exc:
                computed_note = f"八字计算器已触发，但本次输入无法排盘：{exc}。"
    missing_note = (
        f"要把本体系判断提高到更准，还需要补充：{'、'.join(missing_inputs)}。"
        if missing_inputs
        else "本轮输入没有触发明显的关键缺口。"
    )

    if mode == "space":
        action = "本体系会优先判断环境、城市、住宅或办公场域是否与你的问题直接相关，再看是否需要调整空间与方位。"
    elif mode == "timing":
        action = "本体系会优先把问题落到近期时机和事件走势上，再决定该快进、观望还是换窗口。"
    elif mode == "ritual":
        action = "本体系更适合提供仪式语境、修炼框架或护持思路，不适合单独替代现实决策。"
    elif mode == "symbolic":
        action = "本体系会把问题转成象征结构来读，重在看你当前所处的主题、风险和心理指向。"
    else:
        action = "本体系会先看个人结构与阶段运势，再讨论这件事是否顺势、是否值得推进。"

    if "space" in tags and mode == "space":
        action = "你的问题带有明显空间或迁移维度，本体系的直接相关性很高，会优先看居所、方位、城市环境和布局变化。"
    elif "timing" in tags and mode == "timing":
        action = "你的问题带有明显时机判断，本体系会优先看眼下窗口期和近期走势。"
    elif "career" in tags and mode == "destiny":
        action = "你的问题涉及事业发展，本体系会先看个人阶段运势、资源配置和长期适配度。"
    elif "relationship" in tags and mode == "destiny":
        action = "你的问题涉及关系议题，本体系通常会先看关系结构、阶段互动模式和个人倾向。"
    elif "ritual" in tags and mode == "ritual":
        action = "你的问题本身偏仪式或修炼，本体系的语境最直接，但仍要区分宗教实践、历史文献和现实可操作边界。"

    confidence = {
        "deep": "较高",
        "seeded": "中等",
        "missing": "较低",
    }.get(pack.status, "中等")
    return {
        "system": SYSTEM_LABELS.get(pack.key, pack.key),
        "answer": f"从{SYSTEM_LABELS.get(pack.key, pack.key)}资料包看，这类问题主要会从{pack_focus_text(pack.key)}进入。当前库内强调：{evidence_text}。{calculator_note}{parse_note}{computed_note}{missing_note}{action}",
        "confidence": confidence,
    }


def local_final_answer(question: str, packs: list[DossierPack], system_answers: list[dict[str, str]], tags: set[str]) -> dict[str, Any]:
    if is_single_date_good_day_question(question) and detect_system_mentions(question).issubset({"date_selection"}):
        date_result, status = calculate_system("date_selection", {"question": question})
        if status == 200:
            best = date_result["derived_factors"]["ranked_candidates"][0]
            verdict = date_result.get("derived_factors", {}).get("verdict")
            verdict_text = {
                "auspicious": f"直接结论：{best['date']} 在当前本地择日规则下偏吉，可用。",
                "mixed": f"直接结论：{best['date']} 在当前本地择日规则下属于中平可用，不算明显大吉，但也不是明显不宜。",
                "cautious": f"直接结论：{best['date']} 在当前本地择日规则下不算理想，建议谨慎。",
            }.get(verdict, f"直接结论：{best['date']} 已完成本地择日实算。")
            cautions = list(date_result.get("risk_flags", []))
            if not date_result.get("used_inputs", {}).get("participant_birth_dates"):
                cautions.append("这次没有提供参与人出生信息，因此未做人盘冲合加权。")
            if not date_result.get("used_inputs", {}).get("location"):
                cautions.append("这次没有提供地点，因此未加入地域与事务环境细化。")
            return {
                "synthesis": verdict_text,
                "agreements": [
                    f"本地择日实算得分：{best['score']}。",
                    f"支持信号：{date_result['supporting_signals'][0] if date_result.get('supporting_signals') else '当前规则组合中性。'}",
                    "这次只保留了能够直接对当前问题落地计算的择日体系。",
                ],
                "differences": [],
                "cautions": cautions,
            }

    strong = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack.status == "deep"][:8]
    timing_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "timing"][:4]
    space_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "space"][:3]
    destiny_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "destiny"][:4]
    computed_systems = [item["system"] for item in system_answers if item.get("used_local_calculation")]
    timing_fallback_systems = [
        item["system"]
        for item in system_answers
        if item.get("mode") == "timing" and "current ask-time fallback chart" in item.get("answer", "")
    ]
    missing_input_systems = [item["system"] for item in system_answers if item.get("missing_inputs")]

    synthesis_parts = []
    if "space" in tags:
        synthesis_parts.append(f"你的问题带有空间维度，优先参考 {'、'.join(space_systems or ['风水'])} 这类体系。")
    if "timing" in tags:
        synthesis_parts.append(f"你的问题带有时机判断，{'、'.join(timing_systems or ['奇门遁甲'])} 这类体系更适合给近期窗口建议。")
    if {"career", "relationship", "identity"} & tags:
        synthesis_parts.append(f"涉及个人长期结构时，{'、'.join(destiny_systems or ['八字'])} 这类体系更偏向给长期倾向判断。")
    if "ritual" in tags:
        synthesis_parts.append("如果问题本身涉及修炼、法事或护身，道术、卡巴拉、炼金术等体系更适合作为语境性参考，而不是唯一决策依据。")
    if not synthesis_parts:
        synthesis_parts.append("综合现有资料包，这个问题不适合只靠单一体系回答，最好把长期结构、近期时机和现实环境三层一起看。")

    agreements = [
        "多数体系都会把问题拆成“长期结构”和“当下窗口”两层，而不是只给一句断语。",
        "完成度更高的专题目前集中在风水、道术、八字、紫微、奇门、六壬、西占和塔罗，因此这些体系的回答更具体。",
        "种子级专题仍然能提供方向，但证据密度低于深挖专题。",
    ]
    if "space" in tags:
        agreements.append("如果问题和搬家、城市、住宅或办公室有关，空间类体系的解释权会明显上升。")
    if "timing" in tags:
        agreements.append("如果你在问“现在做还是晚点做”，时机类体系会比纯命盘类体系更直接。")

    differences = [
        "命盘类体系偏长期结构，时机类体系偏短期行动，象征类体系偏解释当前主题。",
        "道术、卡巴拉、炼金术这类体系更容易给出象征或修炼框架，不一定直接落到现实事务判断。",
        "塔罗、现代神秘学、人类图等现代传播较强的体系，通常会更强调主观感受和心理叙事。",
    ]

    cautions = [
        "当前汇总基于本地资料包，不等于个性化起盘或正式宗教指导。",
        "如果要提高判断精度，命盘类体系通常还需要出生时间，空间类体系需要住宅或城市信息，时机类体系需要明确事件时点。",
        "外部模型接口目前偶尔会 503，本页已加入本地降级逻辑，但本地结果更像知识库综合，不是完整占断。",
    ]

    return {
        "synthesis": " ".join(synthesis_parts),
        "agreements": agreements,
        "differences": differences,
        "cautions": cautions,
    }


def local_answer_question(question: str) -> dict[str, Any]:
    packs = local_computable_packs(question)
    tags = infer_question_tags(question)
    system_answers = [local_system_answer(pack, question, tags) for pack in packs]
    diagnostics = system_question_diagnostics(question, packs)
    return {
        "model": "local-vault-synthesis",
        "systems": packs,
        "result": {
            "system_answers": system_answers,
            "system_diagnostics": diagnostics,
            "final_answer": local_final_answer(question, packs, system_answers, tags),
        },
    }


def build_system_prompt() -> str:
    return (
        "你是玄学知识库前端的汇总引擎。"
        "你的任务不是宣称绝对正确，而是根据给定的本地资料包内容，"
        "分别给出各体系的回答，再输出一个综合结论。"
        "必须遵守：1. 只基于提供材料和合理推断；2. 明确区分共识、流派差异和不确定处；"
        "3. 输出 JSON，字段必须是 system_answers 和 final_answer。"
        "system_answers 是数组，每项包含 system、answer、confidence。"
        "final_answer 包含 synthesis、agreements、differences、cautions。"
    )


def ask_llm(model: str, messages: list[dict[str, str]], temperature: float = 0.4) -> tuple[str, str]:
    tried: list[dict[str, Any]] = []
    model_queue = [model] + [item for item in FALLBACK_MODELS if item != model]
    for candidate in model_queue:
        request_body = {
            "model": candidate,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        response = requests.post(
            f"{BASE_URL}/chat/completions",
            headers=api_headers(),
            data=json.dumps(request_body),
            timeout=120,
        )
        if response.status_code >= 400:
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            tried.append({"model": candidate, "status": response.status_code, "detail": detail})
            continue
        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            tried.append({"model": candidate, "status": 502, "detail": data})
            continue
        return candidate, content or "{}"
    raise RuntimeError(json.dumps(tried, ensure_ascii=False))


def answer_question(question: str, model: str) -> dict[str, Any]:
    normalized_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if normalized_model == LOCAL_MODEL_ID:
        return local_answer_question(question)

    packs = relevant_packs(question, limit=8)
    context_chunks = []
    for pack in packs:
        sections = []
        for part, path in pack.files.items():
            if not path.exists():
                continue
            text = collapse_text(safe_read(path))
            if text:
                sections.append(f"[{part}]\n{text[:2400]}")
        context = "\n\n".join(sections)
        context_chunks.append(f"## {SYSTEM_LABELS.get(pack.key, pack.key)}\n{context}")

    user_prompt = (
        f"用户问题：{question}\n\n"
        "以下是本地玄学知识库中与问题最相关的专题资料包摘要。"
        "请分别给出每个体系对该问题的回答，再做综合汇总。\n\n"
        + "\n\n".join(context_chunks)
    )
    try:
        used_model, raw = ask_llm(
            DEFAULT_MODEL if normalized_model == AUTO_MODEL_ID else normalized_model,
            [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = json.loads(raw)
        return {
            "model": used_model,
            "systems": all_ranked_packs(question),
            "result": parsed,
        }
    except Exception:
        return local_answer_question(question)


REQUIRED_INPUT_HINTS = {
    "bazi": ["出生日期", "出生时辰", "出生地", "性别"],
    "ziwei_doushu": ["出生日期", "出生时辰", "性别"],
    "qizheng_siyu": ["出生日期", "出生时辰", "出生地"],
    "western_astrology": ["出生日期", "出生时辰", "出生地"],
    "vedic_astrology": ["出生日期", "出生时辰", "出生地"],
    "qimen_dunjia": ["起问时间", "具体问题"],
    "liu_ren": ["占问时间", "具体问题"],
    "liuyao_and_meihua": ["起卦方式或卦象", "具体问题"],
    "date_selection": ["事项类型", "候选日期", "地点"],
    "fengshui": ["城市或地址", "坐向或平面图"],
    "name_studies": ["姓名或候选名", "用途"],
    "tarot": ["牌阵或抽牌结果", "问题时间范围"],
    "human_design": ["出生日期", "出生时辰", "出生地"],
}

BIRTH_DETAIL_SYSTEMS = {
    "bazi",
    "ziwei_doushu",
    "qizheng_siyu",
    "western_astrology",
    "vedic_astrology",
    "human_design",
}

DATE_TOKEN_PATTERN = re.compile(r"\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}")
TIME_TOKEN_PATTERN = re.compile(r"\d{1,2}\s*:\s*\d{1,2}")
BRANCH_HOUR_PATTERN = re.compile(r"[子丑寅卯辰巳午未申酉戌亥]\s*[时時]")


def infer_question_tags(question: str) -> set[str]:
    tags: set[str] = set()
    text = question.lower()
    if any(
        token in question
        for token in ["搬家", "房子", "住宅", "办公室", "城市", "方位", "朝向", "住哪", "住处", "户型", "布局", "风水"]
    ):
        tags.add("space")
    if any(
        token in question
        for token in ["什么时候", "何时", "今年", "本月", "最近", "时机", "要不要", "适合", "能不能", "窗口", "尽快", "先做"]
    ):
        tags.add("timing")
    if any(token in question for token in ["事业", "工作", "职业", "创业", "财运", "赚钱", "发展", "跳槽", "升职", "换工作"]):
        tags.add("career")
    if any(token in question for token in ["感情", "婚姻", "恋爱", "伴侣", "对象", "复合"]):
        tags.add("relationship")
    if any(token in question for token in ["修行", "仪式", "符", "法事", "驱邪", "护身", "修炼", "道术"]):
        tags.add("ritual")
    if any(token in text for token in ["who am i", "personality"]) or any(
        token in question for token in ["天赋", "性格", "适合什么人", "我是什么样", "我的特点"]
    ):
        tags.add("identity")
    if not tags:
        tags.add("general")
    return tags


def has_birth_context(question: str) -> bool:
    return any(
        token in question
        for token in [
            "出生",
            "生于",
            "农历",
            "阳历",
            "公历",
            "时辰",
            "凌晨",
            "早上",
            "上午",
            "中午",
            "下午",
            "晚上",
            "子时",
            "丑时",
            "寅时",
            "卯时",
            "辰时",
            "巳时",
            "午时",
            "未时",
            "申时",
            "酉时",
            "戌时",
            "亥时",
        ]
    )


def question_has_datetime(question: str) -> bool:
    normalized = question.replace("：", ":")
    parsed = parse_datetime_from_text(normalized)
    if parsed:
        return True
    return bool(
        DATE_TOKEN_PATTERN.search(normalized)
        or TIME_TOKEN_PATTERN.search(normalized)
        or BRANCH_HOUR_PATTERN.search(normalized)
        or any(token in normalized for token in ["凌晨", "早上", "上午", "中午", "下午", "傍晚", "晚上"])
    )


def question_has_location(question: str) -> bool:
    if any(token in question for token in ("在公司里", "公司里做出成绩", "自己出来接活", "接项目", "扛项目")) and not any(
        token in question for token in ("地址", "地点", "住在", "现居", "小区", "朝向", "户型", "办公室", "坐向")
    ):
        return False
    parsed = parse_birth_details(question)
    if parsed.birth_location:
        return True
    explicit_space_markers = ("出生地", "生于", "来自", "现居", "住在", "地址", "城市", "小区", "住宅", "公寓", "办公室", "楼层", "坐向", "朝向", "户型", "平面图")
    if any(marker in question for marker in explicit_space_markers):
        return True
    return bool(
        re.search(r"坐[\u4e1c\u5357\u897f\u5317]{1,2}朝[\u4e1c\u5357\u897f\u5317]{1,2}", question)
        or re.search(r"(?:^|[\s,，。；;:：])[\u4e00-\u9fff]{1,12}(?:省|市|区|县|镇|乡|村|路|街)(?=$|[\s,，。；;:：])", question)
    )


def question_has_gender(question: str) -> bool:
    parsed = parse_birth_details(question)
    if parsed.gender:
        return True
    return bool(re.search(r"(?:^|[\s,，。；;])(?:男|女|男性|女性)(?=$|[\s,，。；;])", question))


def question_has_hexagram(question: str) -> bool:
    return any(token in question for token in ["本卦", "变卦", "动爻", "摇卦", "卦象", "上卦", "下卦", "梅花易数"])


def question_has_cards(question: str) -> bool:
    if any(token in question for token in ["正位", "逆位", "抽到", "十字牌阵"]):
        return True
    if "三张牌" in question and not any(token in question for token in ["帮我抽", "直接抽", "替我抽", "还没抽", "没有抽牌"]):
        return True
    return False


def question_has_candidate_dates(question: str) -> bool:
    normalized = question.replace("：", ":")
    matches = DATE_TOKEN_PATTERN.findall(normalized)
    matches.extend(re.findall(r"\d{1,2}\s*月\s*\d{1,2}\s*日", normalized))
    return len(matches) >= 2 or any(token in normalized for token in ["候选日期", "几个日子", "几天里", "备选日期"])


def missing_input_hints(pack: DossierPack, question: str) -> list[str]:
    required = REQUIRED_INPUT_HINTS.get(pack.key, [])
    if not required:
        return []

    parsed = parse_birth_details(question)
    has_birth_date = parsed.birth_datetime is not None
    has_birth_time = has_birth_date and parsed.has_time
    has_location = question_has_location(question)
    has_gender = question_has_gender(question)
    has_datetime = question_has_datetime(question)
    has_hexagram = question_has_hexagram(question)
    has_cards = question_has_cards(question)
    has_candidate_dates = question_has_candidate_dates(question)
    has_specific_question = len(question.strip()) >= 6

    missing: list[str] = []
    for item in required:
        if item == "出生日期" and not has_birth_date:
            missing.append(item)
        elif item == "出生时辰" and not has_birth_time:
            missing.append(item)
        elif item == "出生地" and not has_location:
            missing.append(item)
        elif item == "性别" and not has_gender:
            missing.append(item)
        elif item in {"起问时间", "占问时间"} and not has_datetime:
            missing.append(item)
        elif item == "起卦方式或卦象" and not has_hexagram:
            missing.append(item)
        elif item == "候选日期" and not has_candidate_dates:
            missing.append(item)
        elif item in {"城市或地址", "坐向或平面图", "地点"} and not has_location:
            missing.append(item)
        elif item == "牌阵或抽牌结果" and not has_cards:
            missing.append(item)
        elif item == "具体问题" and not has_specific_question:
            missing.append(item)
    return missing[:3]


def personal_info_parse_note(pack: DossierPack, question: str) -> str:
    if not has_birth_context(question):
        return ""

    parsed = parse_birth_details(question)

    if pack.key == "bazi":
        if parsed.birth_datetime and parsed.has_time:
            notes = []
            if parsed.calendar == "lunar":
                notes.append("已识别为农历出生信息，并已换算为公历时间用于本地排盘。")
            else:
                notes.append("已识别出生日期和具体时间，可直接进入本地八字排盘。")
            if parsed.gender:
                notes.append(f"已识别性别：{parsed.gender}。")
            if parsed.birth_location:
                notes.append(f"已识别出生地：{parsed.birth_location}。")
            return "".join(notes)
        if parsed.birth_datetime and not parsed.has_time:
            if parsed.calendar == "lunar":
                return "已识别农历生日并完成公历换算，但还缺少具体出生时间或时辰，本地八字排盘暂时不能落到时柱。"
            return "已识别出生日期，但还缺少具体出生时间或时辰，本地八字排盘暂时不能落到时柱。"
        return "检测到你在提供出生资料，但当前仍未识别出完整可排盘日期。建议写成“1990-05-12 14:30”或“农历1990年四月十八日下午两点半”。"

    if pack.key in BIRTH_DETAIL_SYSTEMS and not calculator_implemented(pack.key):
        if parsed.birth_datetime:
            if parsed.calendar == "lunar":
                return "已识别到你的出生资料，其中农历日期也能完成换算；但这个体系目前只有规则层和计算规格，还没有接入真实本地排盘器。"
            return "已识别到你的出生资料；但这个体系目前只有规则层和计算规格，还没有接入真实本地排盘器。"
        return "检测到你在提供出生资料，但这个体系当前还没有本地排盘器，只能先走资料库解释。"

    return ""


def local_system_answer(pack: DossierPack, question: str, tags: set[str]) -> dict[str, str]:
    mode = pack_mode(pack.key)
    parsed = parse_birth_details(question)
    evidence = []
    for part in ["root", "sources", "controversies"]:
        evidence.extend(extract_evidence(pack.files[part], limit=1))
    if pack.calculator.exists():
        evidence.extend(extract_evidence(pack.calculator, limit=1))
    evidence = evidence[:2]
    evidence_text = "；".join(evidence) if evidence else pack.summary

    if calculator_implemented(pack.key):
        calculator_note = "本体系已接入真实本地计算器，满足输入条件时可以直接排盘或计算。"
    elif pack.calculator.exists():
        calculator_note = "本体系已有计算器规格，但具体算法尚未接入，本轮仍以资料库综合和规则层提示为主。"
    else:
        calculator_note = "本体系目前以资料库综合为主，尚未建立完整本地计算器规格。"

    missing_inputs = missing_input_hints(pack, question)
    parse_note = personal_info_parse_note(pack, question)
    computed_note = ""

    if pack.key == "bazi":
        if parsed.birth_datetime and parsed.has_time:
            try:
                chart = calculate_bazi(
                    BaziInput(
                        parsed.birth_datetime,
                        gender=parsed.gender,
                        birth_location=parsed.birth_location,
                    )
                )
                pillar_text = "、".join(chart["pillars"][name]["text"] for name in ["year", "month", "day", "hour"])
                day_master = chart["day_master"]
                five_elements = "、".join(
                    f"{element}{count}" for element, count in chart["five_element_counts"].items()
                )
                calendar_note = "已按农历换算后的公历时间" if parsed.calendar == "lunar" else "已按识别到的公历时间"
                computed_note = (
                    f"{calendar_note}生成本地八字粗排：{pillar_text}。"
                    f"日主为{day_master['stem']}{day_master['element']}{day_master['polarity']}。"
                    f"五行计数：{five_elements}。"
                )
            except Exception as exc:
                computed_note = f"本地八字计算器已触发，但这次输入仍无法完整排盘：{exc}。"
        elif parsed.birth_datetime and not parsed.has_time:
            computed_note = "已经识别到出生日期，但没有具体时辰，因此本地八字还不能落到完整四柱。"
    elif pack.key == "numerology":
        numerology_result, status = calculate_system("numerology", {"question": question})
        if status == 200:
            derived = numerology_result["derived_factors"]
            computed_note = (
                f"本地数字命理已提取出生日，可先给出生命路径数 {derived['life_path']}、"
                f"生日数 {derived['birth_day_number']}、个人年 {derived['personal_year']}。"
            )

    if missing_inputs:
        missing_note = f"要把本体系判断提高到更准，还需要补充：{'、'.join(missing_inputs)}。"
    else:
        missing_note = "就输入完整性看，本轮没有明显的关键缺口。"

    if mode == "space":
        action = "本体系会优先判断环境、城市、住宅或办公场域是否与问题直接相关，再看是否需要调整空间与方位。"
    elif mode == "timing":
        action = "本体系会优先把问题落到近期时机和事件走势上，再决定该快进、观望还是换窗口。"
    elif mode == "ritual":
        action = "本体系更适合提供仪式语境、修炼框架或护持思路，不适合单独替代现实决策。"
    elif mode == "symbolic":
        action = "本体系会把问题转成象征结构来读，重在看你当前所处的主题、风险和心理指向。"
    else:
        action = "本体系会先看个人结构与阶段运势，再讨论这件事是否顺势、是否值得推进。"

    if "space" in tags and mode == "space":
        action = "你的问题带有明显空间或迁移维度，本体系的直接相关性很高，会优先看居所、方位、城市环境和布局变化。"
    elif "timing" in tags and mode == "timing":
        action = "你的问题带有明显时机判断，本体系会优先看眼下窗口期和近期走势。"
    elif "career" in tags and mode == "destiny":
        action = "你的问题涉及事业发展，本体系会先看个人阶段运势、资源配置和长期适配度。"
    elif "relationship" in tags and mode == "destiny":
        action = "你的问题涉及关系议题，本体系通常会先看关系结构、阶段互动模式和个人倾向。"
    elif "ritual" in tags and mode == "ritual":
        action = "你的问题本身偏仪式或修炼，本体系的语境最直接，但仍要区分宗教实践、历史文献和现实可操作边界。"

    confidence = {
        "deep": "较高",
        "seeded": "中等",
        "missing": "较低",
    }.get(pack.status, "中等")
    return {
        "system": SYSTEM_LABELS.get(pack.key, pack.key),
        "answer": (
            f"从{SYSTEM_LABELS.get(pack.key, pack.key)}资料包看，这类问题主要会从{pack_focus_text(pack.key)}进入。"
            f"当前库内强调：{evidence_text}。{calculator_note}{parse_note}{computed_note}{missing_note}{action}"
        ),
        "confidence": confidence,
    }


def local_final_answer(question: str, packs: list[DossierPack], system_answers: list[dict[str, str]], tags: set[str]) -> dict[str, Any]:
    diagnostics = system_question_diagnostics(question, packs)
    controller = build_intelligent_controller(question, packs, diagnostics)
    if is_single_date_good_day_question(question) and all(pack.key == "date_selection" for pack in packs):
        date_result, status = calculate_system("date_selection", {"question": question})
        if status == 200:
            best = date_result["derived_factors"]["ranked_candidates"][0]
            verdict = date_result.get("derived_factors", {}).get("verdict")
            verdict_text = {
                "auspicious": f"直接结论：{best['date']} 在当前本地择日规则下偏吉，可用。",
                "mixed": f"直接结论：{best['date']} 在当前本地择日规则下属于中平可用，不算明显大吉，但也不是明显不宜。",
                "cautious": f"直接结论：{best['date']} 在当前本地择日规则下不算理想，建议谨慎。",
            }.get(verdict, f"直接结论：{best['date']} 已完成本地择日实算。")
            return {
                "synthesis": verdict_text,
                "agreements": [
                    f"本地择日实算得分：{best['score']}。",
                    f"支持信号：{date_result['supporting_signals'][0] if date_result.get('supporting_signals') else '当前规则组合中性。'}",
                    "这次只保留了能够直接对当前问题落地计算的择日体系。",
                ],
                "differences": [],
                "cautions": list(date_result.get("risk_flags", [])),
            }

    strong = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack.status == "deep"][:8]
    timing_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "timing"][:4]
    space_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "space"][:3]
    destiny_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "destiny"][:4]
    computed_systems = [item["system"] for item in system_answers if item.get("used_local_calculation")]
    timing_fallback_systems = [
        item["system"]
        for item in system_answers
        if item.get("mode") == "timing" and "current ask-time fallback chart" in item.get("answer", "")
    ]
    missing_input_systems = [item["system"] for item in system_answers if item.get("missing_inputs")]

    synthesis_parts = []
    if "space" in tags:
        synthesis_parts.append(f"你的问题带有空间维度，优先参考 {'、'.join(space_systems or ['风水'])} 这类体系。")
    if "timing" in tags:
        synthesis_parts.append(f"你的问题带有时机判断，{'、'.join(timing_systems or ['奇门遁甲'])} 这类体系更适合给近期窗口建议。")
    if {"career", "relationship", "identity"} & tags:
        synthesis_parts.append(f"涉及个人长期结构时，{'、'.join(destiny_systems or ['八字'])} 这类体系更偏向给长期倾向判断。")
    if "ritual" in tags:
        synthesis_parts.append("如果问题本身涉及修炼、法事或护身，道术、卡巴拉、炼金术等体系更适合作为语境性参考，而不是唯一决策依据。")
    if not synthesis_parts:
        synthesis_parts.append("综合现有资料包，这个问题不适合只靠单一体系回答，最好把长期结构、近期时机和现实环境三层一起看。")

    agreements = [
        "多数体系都会把问题拆成“长期结构”和“当下窗口”两层，而不是只给一句断语。",
        f"当前完成度更高的专题主要有：{'、'.join(strong or ['八字', '风水', '道术'])}，因此这些体系给出的回答通常更具体。",
        "种子级专题仍然能提供方向，但证据密度和规则完整度低于深度资料包。",
    ]
    if "space" in tags:
        agreements.append("如果问题和搬家、城市、住宅或办公室有关，空间类体系的解释权会明显上升。")
    if "timing" in tags:
        agreements.append("如果你在问“现在做还是晚点做”，时机类体系通常会比纯命盘类体系更直接。")

    differences = [
        "命盘类体系偏长期结构，时机类体系偏短期行动，象征类体系偏解释当前主题。",
        "道术、卡巴拉、炼金术这类体系更容易给出象征或修炼框架，不一定直接落到现实事务判断。",
        "塔罗、现代神秘学、人类图等近现代传播较强的体系，通常会更强调主观感受和心理叙事。",
    ]

    cautions = [
        "当前汇总基于本地资料包，不等于个性化起盘或正式宗教指导。",
        "如果要提高判断精度，命盘类体系通常还需要出生时间，空间类体系需要住宅或城市信息，时机类体系需要明确事件时间点。",
        "外部模型接口偶尔会不可用，页面已经做了本地降级；但本地结果本质上仍是知识库综合，不是全体系完整实算。",
    ]

    return {
        "synthesis": " ".join(synthesis_parts),
        "agreements": agreements,
        "differences": differences,
        "cautions": cautions,
    }


def build_system_prompt() -> str:
    return (
        "你是玄学知识库前端的汇总引擎。"
        "你的任务不是宣称绝对正确，而是严格根据给定的本地资料包内容，"
        "分别给出各体系的回答，再输出一个综合结论。"
        "必须遵守：1. 只基于提供材料和合理推断。"
        "2. 明确区分共识、流派差异和不确定处。"
        "3. 输出 JSON，字段必须是 system_answers 和 final_answer。"
        "system_answers 是数组，每项包含 system、answer、confidence。"
        "final_answer 包含 synthesis、agreements、differences、cautions。"
    )


def answer_question(question: str, model: str) -> dict[str, Any]:
    normalized_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if normalized_model == LOCAL_MODEL_ID:
        return local_answer_question(question)

    packs = relevant_packs(question, limit=8)
    context_chunks = []
    for pack in packs:
        sections = []
        for part, path in pack.files.items():
            if not path.exists():
                continue
            text = collapse_text(safe_read(path))
            if text:
                sections.append(f"[{part}]\n{text[:2400]}")
        context = "\n\n".join(sections)
        context_chunks.append(f"## {SYSTEM_LABELS.get(pack.key, pack.key)}\n{context}")

    user_prompt = (
        f"用户问题：{question}\n\n"
        "以下是本地玄学知识库中与问题最相关的专题资料包摘要。"
        "请分别给出每个体系对该问题的回答，再做综合汇总。\n\n"
        + "\n\n".join(context_chunks)
    )
    try:
        used_model, raw = ask_llm(
            DEFAULT_MODEL if normalized_model == AUTO_MODEL_ID else normalized_model,
            [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = json.loads(raw)
        return {
            "model": used_model,
            "systems": all_ranked_packs(question),
            "result": parsed,
        }
    except Exception:
        return local_answer_question(question)


@app.get("/")
def index():
    return send_from_directory(APP_DIR, "public-home.html")


@app.get("/app")
@app.get("/app/")
def full_app():
    return send_from_directory(APP_DIR, "index.html")


@app.after_request
def disable_local_cache(response):
    cacheable_suffixes = (".js", ".css", ".html", ".json")
    path = (request.path or "").lower()
    if path == "/" or path.endswith(cacheable_suffixes):
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


@app.get("/api/models")
def models():
    model_ids: list[str] = []
    remote_error = ""
    try:
        response = requests.get(f"{BASE_URL}/models", headers=api_headers(), timeout=6)
        response.raise_for_status()
        payload = response.json()
        model_ids = sorted(
            item.get("id", "")
            for item in payload.get("data", [])
            if isinstance(item, dict) and item.get("id")
        )
    except Exception as exc:
        remote_error = str(exc)

    prefixed_models = [AUTO_MODEL_ID, LOCAL_MODEL_ID] + model_ids
    return jsonify(
        {
            "models": prefixed_models,
            "default": AUTO_MODEL_ID,
            "remoteError": remote_error,
        }
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "ok": True,
            "hasKey": bool(geekspace_key()),
            "hasTencentMapKey": has_tencent_map_key(),
            "baseUrl": BASE_URL,
            "vaultReady": VAULT_DIR.exists(),
            "vaultDir": str(VAULT_DIR),
            "buildStamp": BUILD_STAMP,
            "implementedCount": len(IMPLEMENTED_SYSTEMS),
            "engineImplementedCount": len(engine_registry.IMPLEMENTED_SYSTEMS),
        }
    )


@app.get("/api/maps/geocode")
def map_geocode():
    address = str(request.args.get("address") or "").strip()
    region = str(request.args.get("region") or "").strip()
    if not address:
        return jsonify({"error": "address is required"}), 400
    try:
        resolved = geocode_address(address, region=region)
        return jsonify(
            {
                "query": resolved.query,
                "title": resolved.title,
                "address": resolved.address,
                "lat": resolved.lat,
                "lng": resolved.lng,
                "adcode": resolved.adcode,
                "province": resolved.province,
                "city": resolved.city,
                "district": resolved.district,
                "source": resolved.source,
                "staticMapUrl": static_map_url(
                    resolved.lat,
                    resolved.lng,
                    zoom=18,
                    width=960,
                    height=540,
                    scale=2,
                    markers=f"color:red|label:A|{resolved.lat},{resolved.lng}",
                ),
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.get("/api/maps/search")
def map_search():
    keyword = str(request.args.get("keyword") or "").strip()
    region = str(request.args.get("region") or "").strip()
    if not keyword:
        return jsonify({"error": "keyword is required"}), 400
    try:
        return jsonify({"results": place_search(keyword, region=region)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/maps/property-context")
def map_property_context():
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    address = str(payload.get("address") or payload.get("location") or "").strip()
    facing_direction = str(payload.get("facing_direction") or payload.get("facingDirection") or "").strip()
    if not address:
        return jsonify({"error": "address is required"}), 400
    try:
        resolved = geocode_address(address, region=str(payload.get("region") or "").strip())
        map_status = {"poiSearch": "ok", "warnings": []}
        try:
            poi_hits = collect_nearby_poi_signals(
                resolved.lat,
                resolved.lng,
                radius=int(payload.get("radius") or 1500),
            )
        except Exception as exc:
            if is_quota_exceeded_error(exc):
                poi_hits = {}
                map_status["poiSearch"] = "quota_exceeded"
                map_status["warnings"].append("腾讯地图周边检索今日配额已达上限，已降级为仅返回定位与静态图。")
            else:
                raise
        poi_summary = {
            category: {
                "count": len(entries),
                "nearestDistance": min(int(item.get("distance") or 0) for item in entries) if entries else None,
            }
            for category, entries in poi_hits.items()
        }
        static_url = static_map_url(
            resolved.lat,
            resolved.lng,
            zoom=int(payload.get("zoom") or 18),
            width=int(payload.get("width") or 960),
            height=int(payload.get("height") or 540),
            scale=int(payload.get("scale") or 2),
            markers=f"color:red|label:A|{resolved.lat},{resolved.lng}",
        )
        external = evaluate_external_environment(
            {
                "poi_summary": {
                    key: {
                        "count": value["count"],
                        "nearest_distance": value["nearestDistance"],
                    }
                    for key, value in poi_summary.items()
                },
                "poi_hits": poi_hits,
            }
        )
        summary_parts = [
            f"已定位到{resolved.address or resolved.title or address}。",
            "当前可先结合地图做外局筛查：道路、水系、桥、高架、楼间距、周边大型设施与开阔度。",
        ]
        if facing_direction:
            summary_parts.append(f"当前记录的朝向是{facing_direction}，可与卫星俯视图交叉核对。")
        if external.get("verdict") == "supportive":
            summary_parts.append("从第一版外局筛查看，周边环境偏向可用。")
        elif external.get("verdict") == "caution":
            summary_parts.append("从第一版外局筛查看，周边环境有几个需要谨慎复核的点。")
        return jsonify(
            {
                "address": resolved.address,
                "title": resolved.title,
                "location": {
                    "lat": resolved.lat,
                    "lng": resolved.lng,
                },
                "adcode": resolved.adcode,
                "province": resolved.province,
                "city": resolved.city,
                "district": resolved.district,
                "staticMapUrl": static_url,
                "poiSummary": poi_summary,
                "poiHits": poi_hits,
                "externalEnvironment": external,
                "summary": " ".join(summary_parts),
                "nextSignals": [
                    "补楼栋朝向或罗盘度数",
                    "补户型图或室内视频",
                    "结合外局与室内布局做完整风水判断",
                ],
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


def _map_property_context_with_fallback():
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    address = str(payload.get("address") or payload.get("location") or "").strip()
    facing_direction = str(payload.get("facing_direction") or payload.get("facingDirection") or "").strip()
    if not address:
        return jsonify({"error": "address is required"}), 400
    try:
        resolved = geocode_address(address, region=str(payload.get("region") or "").strip())
        map_status = {"poiSearch": "ok", "warnings": []}
        try:
            poi_hits = collect_nearby_poi_signals(
                resolved.lat,
                resolved.lng,
                radius=int(payload.get("radius") or 1500),
            )
        except Exception as exc:
            if is_quota_exceeded_error(exc):
                poi_hits = {}
                map_status["poiSearch"] = "quota_exceeded"
                map_status["warnings"].append(
                    "\u817e\u8baf\u5730\u56fe\u5468\u8fb9\u68c0\u7d22\u4eca\u65e5\u914d\u989d\u5df2\u8fbe\u4e0a\u9650\uff0c\u5df2\u964d\u7ea7\u4e3a\u4ec5\u8fd4\u56de\u5b9a\u4f4d\u4e0e\u9759\u6001\u56fe\u3002"
                )
            else:
                raise
        poi_summary = {
            category: {
                "count": len(entries),
                "nearestDistance": min(int(item.get("distance") or 0) for item in entries) if entries else None,
            }
            for category, entries in poi_hits.items()
        }
        static_url = static_map_url(
            resolved.lat,
            resolved.lng,
            zoom=int(payload.get("zoom") or 18),
            width=int(payload.get("width") or 960),
            height=int(payload.get("height") or 540),
            scale=int(payload.get("scale") or 2),
            markers=f"color:red|label:A|{resolved.lat},{resolved.lng}",
        )
        external = evaluate_external_environment(
            {
                "poi_summary": {
                    key: {
                        "count": value["count"],
                        "nearest_distance": value["nearestDistance"],
                    }
                    for key, value in poi_summary.items()
                },
                "poi_hits": poi_hits,
            }
        )
        summary_parts = [
            f"\u5df2\u5b9a\u4f4d\u5230{resolved.address or resolved.title or address}\u3002",
            "\u5f53\u524d\u53ef\u5148\u7ed3\u5408\u5730\u56fe\u505a\u5916\u5c40\u7b5b\u67e5\uff1a\u9053\u8def\u3001\u6c34\u7cfb\u3001\u6865\u3001\u9ad8\u67b6\u3001\u697c\u95f4\u8ddd\u3001\u5468\u8fb9\u5927\u578b\u8bbe\u65bd\u4e0e\u5f00\u9614\u5ea6\u3002",
        ]
        if facing_direction:
            summary_parts.append(
                f"\u5f53\u524d\u8bb0\u5f55\u7684\u671d\u5411\u662f{facing_direction}\uff0c\u53ef\u4e0e\u536b\u661f\u4fef\u89c6\u56fe\u4ea4\u53c9\u6821\u5bf9\u3002"
            )
        if map_status["poiSearch"] == "quota_exceeded":
            summary_parts.append(
                "\u5468\u8fb9 POI \u5916\u5c40\u68c0\u7d22\u56e0\u817e\u8baf\u5730\u56fe\u5f53\u65e5\u914d\u989d\u5df2\u6ee1\u6682\u672a\u5b8c\u6210\uff0c\u5f53\u524d\u53ef\u5148\u4f9d\u636e\u5b9a\u4f4d\u4e0e\u536b\u661f\u89c6\u89d2\u505a\u521d\u6b65\u5916\u5c40\u5224\u65ad\u3002"
            )
        if external.get("verdict") == "supportive":
            summary_parts.append("\u4ece\u7b2c\u4e00\u7248\u5916\u5c40\u7b5b\u67e5\u770b\uff0c\u5468\u8fb9\u73af\u5883\u504f\u5411\u53ef\u7528\u3002")
        elif external.get("verdict") == "caution":
            summary_parts.append("\u4ece\u7b2c\u4e00\u7248\u5916\u5c40\u7b5b\u67e5\u770b\uff0c\u5468\u8fb9\u73af\u5883\u6709\u51e0\u4e2a\u9700\u8981\u8c28\u614e\u590d\u6838\u7684\u70b9\u3002")
        return jsonify(
            {
                "address": resolved.address,
                "title": resolved.title,
                "location": {
                    "lat": resolved.lat,
                    "lng": resolved.lng,
                },
                "adcode": resolved.adcode,
                "province": resolved.province,
                "city": resolved.city,
                "district": resolved.district,
                "staticMapUrl": static_url,
                "poiSummary": poi_summary,
                "poiHits": poi_hits,
                "mapStatus": map_status,
                "externalEnvironment": external,
                "summary": " ".join(summary_parts),
                "nextSignals": [
                    "\u8865\u697c\u680b\u671d\u5411\u6216\u7f57\u76d8\u5ea6\u6570",
                    "\u8865\u6237\u578b\u56fe\u6216\u5ba4\u5185\u89c6\u9891",
                    "\u7ed3\u5408\u5916\u5c40\u4e0e\u5ba4\u5185\u5e03\u5c40\u505a\u5b8c\u6574\u98ce\u6c34\u5224\u65ad",
                ],
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


app.view_functions["map_property_context"] = _map_property_context_with_fallback


@app.get("/api/progress")
def progress():
    return jsonify(vault_overview())


@app.post("/api/calculate/bazi")
def calculate_bazi_api():
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    result, status = calculate_system("bazi", payload)
    return jsonify(result), status


@app.post("/api/calculate/<system>")
def calculate_system_api(system: str):
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    normalized = system.strip().lower()
    if normalized not in DOSSIER_ORDER:
        return jsonify({"error": f"Unknown system: {system}"}), 404
    result, status = calculate_system(normalized, payload)
    return jsonify(result), status


@app.post("/api/oracle")
def oracle():
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    question = str(payload.get("question") or "").strip()
    model = str(payload.get("model") or AUTO_MODEL_ID).strip() or AUTO_MODEL_ID
    if not question:
        return jsonify({"error": "Question is required."}), 400
    safety = safety_screen(question)
    if safety:
        return jsonify({
            "model": LOCAL_MODEL_ID,
            "systems": [],
            "systemDiagnostics": [],
            "controller": {
                "name": "安全总控",
                "executionStatus": "blocked",
                "questionType": "高风险现实问题",
                "routingSummary": safety["summary"],
                "selectedSystems": [],
                "alternateSystems": [],
                "missingInputs": [],
                "signals": [safety["title"]],
                "followUpPrompt": "",
            },
            "oracle": {
                "controller": {
                    "name": "安全总控",
                    "executionStatus": "blocked",
                    "questionType": "高风险现实问题",
                    "routingSummary": safety["summary"],
                    "selectedSystems": [],
                    "alternateSystems": [],
                    "missingInputs": [],
                    "signals": [safety["title"]],
                    "followUpPrompt": "",
                },
                "system_answers": [],
                "system_diagnostics": [],
                "final_answer": {
                    "synthesis": safety["summary"],
                    "agreements": list(safety.get("actions") or []),
                    "differences": [],
                    "cautions": list(safety.get("cautions") or []),
                },
            },
            "safety": safety,
        }), 200
    try:
        answer = answer_question(question, model)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except Exception:
        return jsonify({"error": "当前输入触发了解析异常，请先检查出生日期、时辰或问题格式。"}), 400
    systems = [
        {
            "key": pack.key,
            "title": SYSTEM_LABELS.get(pack.key, pack.key),
            "score": pack.score,
            "status": pack.status,
            "calculatorReady": pack.calculator.exists(),
            "calculatorImplemented": calculator_implemented(pack.key),
            "questionGuide": system_question_guide(pack.key),
        }
        for pack in answer["systems"]
    ]
    diagnostics = answer["result"].get("system_diagnostics") if isinstance(answer.get("result"), dict) else None
    if not isinstance(diagnostics, list):
        diagnostics = system_question_diagnostics(question, answer.get("systems") or [])
    controller = answer["result"].get("controller") if isinstance(answer.get("result"), dict) else None
    if not isinstance(controller, dict):
        controller = build_intelligent_controller(question, answer.get("systems") or [], diagnostics)
    return jsonify({
        "model": answer["model"],
        "systems": systems,
        "systemDiagnostics": diagnostics,
        "controller": controller,
        "oracle": answer["result"],
    })


BIRTH_DATE_LABEL = "\u51fa\u751f\u65e5\u671f"
BIRTH_TIME_LABEL = "\u51fa\u751f\u65f6\u8fb0"
BIRTH_LOCATION_LABEL = "\u51fa\u751f\u5730"
GENDER_LABEL = "\u6027\u522b"
NAME_BIRTH_LABEL = "\u51fa\u751f\u5e74\u6708\u65e5\u65f6"
SURNAME_LABEL = "\u59d3\u6c0f"
ASK_TIME_LABEL = "\u8d77\u95ee\u65f6\u95f4"
DIVINATION_TIME_LABEL = "\u5360\u95ee\u65f6\u95f4"
SPECIFIC_QUESTION_LABEL = "\u5177\u4f53\u95ee\u9898"
HEXAGRAM_LABEL = "\u8d77\u5366\u65b9\u5f0f\u6216\u5366\u8c61"
EVENT_TYPE_LABEL = "\u4e8b\u9879\u7c7b\u578b"
CANDIDATE_DATES_LABEL = "\u5019\u9009\u65e5\u671f"
LOCATION_LABEL = "\u5730\u70b9"
CITY_OR_ADDRESS_LABEL = "\u57ce\u5e02\u6216\u5730\u5740"
FACING_OR_PLAN_LABEL = "\u5750\u5411\u6216\u5e73\u9762\u56fe"
NAME_OR_OPTIONS_LABEL = "\u59d3\u540d\u6216\u5019\u9009\u540d"
PURPOSE_LABEL = "\u7528\u9014"
CARDS_LABEL = "\u724c\u9635\u6216\u62bd\u724c\u7ed3\u679c"
TIME_RANGE_LABEL = "\u95ee\u9898\u65f6\u95f4\u8303\u56f4"
DESCRIPTION_LABEL = "\u5916\u8c8c\u63cf\u8ff0\u6216\u89c2\u5bdf\u8bb0\u5f55"
OBSERVATION_CONTEXT_LABEL = "\u89c2\u5bdf\u573a\u666f"
TOPIC_LABEL = "\u4e8b\u9879\u7c7b\u578b\u6216\u76ee\u7684"
LINEAGE_LABEL = "\u6765\u6e90\u6216\u6cd5\u8109"
RITUAL_TEXT_LABEL = "\u4eea\u5f0f\u6587\u672c\u6216\u63cf\u8ff0"
TEXT_OR_IMAGE_LABEL = "\u6587\u672c\u6216\u56fe\u50cf\u7b26\u53f7"
STAGE_MODEL_LABEL = "\u8f6c\u5316\u9636\u6bb5\u6216\u6a21\u578b"
SOURCE_LABEL = "\u6765\u6e90"
PRACTICE_DESCRIPTION_LABEL = "\u5b9e\u8df5\u63cf\u8ff0"

REQUIRED_INPUT_HINTS = {
    "bazi": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL, GENDER_LABEL],
    "ziwei_doushu": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, GENDER_LABEL],
    "qizheng_siyu": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
    "western_astrology": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
    "vedic_astrology": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
    "qimen_dunjia": [ASK_TIME_LABEL, SPECIFIC_QUESTION_LABEL],
    "liu_ren": [DIVINATION_TIME_LABEL, SPECIFIC_QUESTION_LABEL],
    "liuyao_and_meihua": [HEXAGRAM_LABEL, SPECIFIC_QUESTION_LABEL],
    "date_selection": [EVENT_TYPE_LABEL, CANDIDATE_DATES_LABEL, LOCATION_LABEL],
    "fengshui": [CITY_OR_ADDRESS_LABEL, FACING_OR_PLAN_LABEL],
    "name_studies": [NAME_OR_OPTIONS_LABEL, PURPOSE_LABEL],
    "tarot": [CARDS_LABEL, TIME_RANGE_LABEL],
    "human_design": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
    "physiognomy": [DESCRIPTION_LABEL, OBSERVATION_CONTEXT_LABEL],
    "daoist_arts": [TOPIC_LABEL, LINEAGE_LABEL, RITUAL_TEXT_LABEL],
    "alchemy_and_hermeticism": [TOPIC_LABEL, TEXT_OR_IMAGE_LABEL, STAGE_MODEL_LABEL],
    "modern_esotericism": [TOPIC_LABEL, SOURCE_LABEL, PRACTICE_DESCRIPTION_LABEL],
}

OPTIONAL_ENHANCEMENT_INPUTS = {
    "bazi": {BIRTH_LOCATION_LABEL, GENDER_LABEL},
    "ziwei_doushu": set(),
    "qizheng_siyu": set(),
    "western_astrology": set(),
    "vedic_astrology": set(),
    "human_design": set(),
    "physiognomy": {OBSERVATION_CONTEXT_LABEL},
    "liuyao_and_meihua": {HEXAGRAM_LABEL},
    "yijing_and_symbolism": {HEXAGRAM_LABEL},
}

DIRECT_CONCLUSION_SYSTEMS = {
    "bazi",
    "ziwei_doushu",
    "qizheng_siyu",
    "western_astrology",
    "vedic_astrology",
    "human_design",
    "qimen_dunjia",
    "liu_ren",
    "fengshui",
    "date_selection",
    "name_studies",
    "physiognomy",
    "daoist_arts",
    "alchemy_and_hermeticism",
    "modern_esotericism",
    "kabbalah",
    "numerology",
    "yijing_and_symbolism",
    "liuyao_and_meihua",
}

STRUCTURE_FIRST_SYSTEMS = {
    "ziwei_doushu",
    "western_astrology",
    "vedic_astrology",
    "qizheng_siyu",
    "human_design",
    "numerology",
    "yijing_and_symbolism",
    "liuyao_and_meihua",
}

SYSTEM_CONCLUSION_MODE = {
    "bazi": "question_adaptive",
    "ziwei_doushu": "question_adaptive",
    "qizheng_siyu": "question_adaptive",
    "western_astrology": "question_adaptive",
    "vedic_astrology": "question_adaptive",
    "human_design": "question_adaptive",
    "qimen_dunjia": "timing_verdict",
    "liu_ren": "timing_verdict",
    "fengshui": "space_verdict",
    "date_selection": "date_verdict",
    "numerology": "supporting_cycle",
    "yijing_and_symbolism": "symbolic_to_verdict",
    "liuyao_and_meihua": "symbolic_to_verdict",
}

QUESTION_GUIDE_MAP: dict[str, dict[str, Any]] = {
    "yijing_and_symbolism": {
        "bestFor": "当前局势、事情走向、象意判断",
        "needs": ["具体问题", "起卦数字或起问时点"],
        "askFormat": "例如：我想问这次合作能不能成？数字 3 8 5。",
        "avoid": "只给泛泛一句“帮我算算全部人生”时，落地性会很弱。",
    },
    "bazi": {
        "bestFor": "人生结构、事业财运、关系模式、阶段运势",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL, GENDER_LABEL],
        "askFormat": "例如：我出生于 1990-05-12 14:30，男，河南信阳，想看今年工作和财运。",
        "avoid": "没有准确出生时辰时，不适合做精批。",
    },
    "ziwei_doushu": {
        "bestFor": "命盘格局、宫位主题、阶段趋势",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, GENDER_LABEL],
        "askFormat": "例如：1990-05-12 14:30，女，想看婚姻和事业主轴。",
        "avoid": "出生时辰不准时，宫位可能直接偏掉。",
    },
    "qizheng_siyu": {
        "bestFor": "中西合参的命盘结构、天时节律、阶段主题",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
        "askFormat": "例如：1990-05-12 14:30，北京，想看接下来两年的事业变化。",
        "avoid": "没有出生地时，盘面精度会下降。",
    },
    "qimen_dunjia": {
        "bestFor": "短期决策、时机判断、先做什么",
        "needs": [ASK_TIME_LABEL, SPECIFIC_QUESTION_LABEL],
        "askFormat": "例如：现在是 2026-06-08 21:10，我想问这周先谈合作还是先推进招聘？",
        "avoid": "不适合拿来代替完整人生盘。",
    },
    "liu_ren": {
        "bestFor": "事件占时、过程推演、问成败与阻碍",
        "needs": [DIVINATION_TIME_LABEL, SPECIFIC_QUESTION_LABEL],
        "askFormat": "例如：2026-06-08 21:10 起问，这次签约最终能不能落地？",
        "avoid": "问题太空泛时，很难给出明确落点。",
    },
    "liuyao_and_meihua": {
        "bestFor": "短期走势、结果倾向、应期判断",
        "needs": [HEXAGRAM_LABEL, SPECIFIC_QUESTION_LABEL],
        "askFormat": "例如：我问这次谈判能不能成，数字 3 8 5。或直接给本卦、变卦、动爻。",
        "avoid": "只说“帮我看看”但不给起卦信息时，精度有限。",
    },
    "date_selection": {
        "bestFor": "选日子、看某天宜不宜、对比几个日期",
        "needs": [EVENT_TYPE_LABEL, CANDIDATE_DATES_LABEL, LOCATION_LABEL],
        "askFormat": "例如：我想搬家，候选日期是 6月10日、6月12日，地点在上海。或：2026年6月8号是个好日子吗？",
        "avoid": "没有事项类型时，只能给通用择日判断。",
    },
    "name_studies": {
        "bestFor": "名字适配、候选名比较、改名方向",
        "needs": [NAME_OR_OPTIONS_LABEL, PURPOSE_LABEL],
        "askFormat": "例如：名字“林清和”适合男孩吗？用于正式姓名。",
        "avoid": "不适合直接代替完整命盘判断。",
    },
    "physiognomy": {
        "bestFor": "外貌特征观察、气色与结构判断",
        "needs": [DESCRIPTION_LABEL, OBSERVATION_CONTEXT_LABEL],
        "askFormat": "例如：额头宽、眼神清、鼻梁直、下巴饱满，日间正面照片观察，想看整体面相倾向。",
        "avoid": "没有清晰描述或观察场景时，很难稳定判断。",
    },
    "fengshui": {
        "bestFor": "住宅、办公室、朝向、布局调整",
        "needs": [CITY_OR_ADDRESS_LABEL, FACING_OR_PLAN_LABEL],
        "askFormat": "例如：上海某小区 12 栋 1802，坐北朝南，想看这个房子适不适合长期住。",
        "avoid": "没有坐向、户型或场景描述时，只能做很粗的判断。",
    },
    "daoist_arts": {
        "bestFor": "法脉背景、仪式用途、文化语境和边界提醒",
        "needs": [TOPIC_LABEL, LINEAGE_LABEL, RITUAL_TEXT_LABEL],
        "askFormat": "例如：正一道法脉，想了解净宅护身类仪式通常怎么分类与使用。",
        "avoid": "不适合替代现实医疗、法律或危险行为决策。",
    },
    "western_astrology": {
        "bestFor": "人格结构、关系互动、长期发展主题",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
        "askFormat": "例如：1990-05-12 14:30，北京，想看我的职业优势和关系模式。",
        "avoid": "出生时间误差大会明显影响上升和宫位。",
    },
    "vedic_astrology": {
        "bestFor": "业力主题、阶段运势、婚恋与事业方向",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
        "askFormat": "例如：1990-05-12 14:30，北京，想看这两年的事业和婚恋趋势。",
        "avoid": "同样依赖准确出生时间与地点。",
    },
    "tarot": {
        "bestFor": "短期问题、心理面向、当前局势启示",
        "needs": [CARDS_LABEL, TIME_RANGE_LABEL],
        "askFormat": "例如：三张牌分别是愚者正位、死神逆位、圣杯首牌，想问这个月项目走向。",
        "avoid": "没有抽牌结果时，本地无法直接实算。",
    },
    "kabbalah": {
        "bestFor": "生命之树路径、象征主题、修行语境",
        "needs": [TOPIC_LABEL, "Sephirah / Path / 主题对象"],
        "askFormat": "例如：从 Tiphereth 的角度看 career direction 和 visible purpose。",
        "avoid": "如果没有明确路径、源流或主题，结果会偏抽象。",
    },
    "alchemy_and_hermeticism": {
        "bestFor": "转化阶段、象征材料、修炼模型",
        "needs": [TOPIC_LABEL, TEXT_OR_IMAGE_LABEL, STAGE_MODEL_LABEL],
        "askFormat": "例如：nigredo 阶段的 shadow work，材料是 crow / mercury / salt。",
        "avoid": "更适合象征分析，不适合直接拿来做现实占断。",
    },
    "onmyodo": {
        "bestFor": "方位禁忌、日期方位、出行与空间判断",
        "needs": [EVENT_TYPE_LABEL, LOCATION_LABEL, "日期或方向信息"],
        "askFormat": "例如：2026-06-10 去东京西南方向出行，这个方向与时点合不合适？",
        "avoid": "没有时间与方向时，无法有效落盘。",
    },
    "numerology": {
        "bestFor": "生命灵数、年份主题、数字倾向",
        "needs": [BIRTH_DATE_LABEL],
        "askFormat": "例如：1990-05-12，想看我的生命灵数和今年主题。",
        "avoid": "适合做辅助观察，不宜单独替代复杂命盘。",
    },
    "human_design": {
        "bestFor": "类型、权威、决策方式、能量运作",
        "needs": [BIRTH_DATE_LABEL, BIRTH_TIME_LABEL, BIRTH_LOCATION_LABEL],
        "askFormat": "例如：1990-05-12 14:30，北京，想看我的人类图类型和决策方式。",
        "avoid": "出生时间不准时，定义中心和权威都可能变化。",
    },
    "modern_esotericism": {
        "bestFor": "显化、脉轮、灵气、现代修行方法的语境分析",
        "needs": [TOPIC_LABEL, SOURCE_LABEL, PRACTICE_DESCRIPTION_LABEL],
        "askFormat": "例如：我在做显化和脉轮冥想，来源是某课程体系，想看这个实践路径的风险和偏差。",
        "avoid": "不适合用来替代医学、金融或法律判断。",
    },
}


def system_question_guide(key: str) -> dict[str, Any]:
    guide = QUESTION_GUIDE_MAP.get(key, {})
    required = REQUIRED_INPUT_HINTS.get(key, [])
    optional = sorted(OPTIONAL_ENHANCEMENT_INPUTS.get(key, set()))
    return {
        "mode": pack_mode(key),
        "bestFor": guide.get("bestFor", "用于该体系最擅长的问题类型。"),
        "needs": guide.get("needs", required),
        "askFormat": guide.get("askFormat", "请尽量给出明确问题和必要条件。"),
        "avoid": guide.get("avoid", "输入越完整，本地计算越稳定。"),
        "minimumNeeds": required,
        "optionalEnhancements": optional,
        "directConclusionCapable": key in DIRECT_CONCLUSION_SYSTEMS,
        "structureFirst": key in STRUCTURE_FIRST_SYSTEMS,
        "conclusionMode": SYSTEM_CONCLUSION_MODE.get(key, "question_adaptive"),
    }

BIRTH_DETAIL_SYSTEMS = {
    "bazi",
    "ziwei_doushu",
    "qizheng_siyu",
    "western_astrology",
    "vedic_astrology",
    "human_design",
}

DATE_TOKEN_PATTERN = re.compile("\\d{4}\\s*[-/.\\u5e74]\\s*\\d{1,2}\\s*[-/.\\u6708]\\s*\\d{1,2}")
TIME_TOKEN_PATTERN = re.compile("\\d{1,2}\\s*:\\s*\\d{1,2}")
BRANCH_HOUR_PATTERN = re.compile("[\\u5b50\\u4e11\\u5bc5\\u536f\\u8fb0\\u5df3\\u5348\\u672a\\u7533\\u9149\\u620c\\u4ea5]\\s*[\\u65f6\\u6642]")
GOOD_DAY_MARKERS = ("好日子", "吉日", "黄道吉日", "黃道吉日")

SPACE_MARKERS = (
    "\u642c\u5bb6",
    "\u623f\u5b50",
    "\u4f4f\u5b85",
    "\u529e\u516c\u5ba4",
    "\u57ce\u5e02",
    "\u5730\u5740",
    "\u5c0f\u533a",
    "\u697c",
    "\u697c\u5c42",
    "\u65b9\u4f4d",
    "\u671d\u5411",
    "\u5750\u5411",
    "\u5750\u5317\u671d\u5357",
    "\u4f4f\u54ea",
    "\u4f4f\u5904",
    "\u6237\u578b",
    "\u5e03\u5c40",
    "\u98ce\u6c34",
    "\u957f\u671f\u5c45\u4f4f",
)
TIMING_MARKERS = (
    "\u4ec0\u4e48\u65f6\u5019",
    "\u4f55\u65f6",
    "\u4eca\u5e74",
    "\u672c\u6708",
    "\u6700\u8fd1",
    "\u65f6\u673a",
    "\u8981\u4e0d\u8981",
    "\u7a97\u53e3",
    "\u5c3d\u5feb",
    "\u5148\u505a",
)
NAME_MARKERS = (
    "\u59d3\u540d",
    "\u540d\u5b57",
    "\u8d77\u540d",
    "\u53d6\u540d",
    "\u6539\u540d",
    "\u5019\u9009\u540d",
    "\u5b9d\u5b9d",
    "\u5973\u5b9d\u5b9d",
    "\u7537\u5b9d\u5b9d",
)
CAREER_MARKERS = (
    "\u4e8b\u4e1a",
    "\u5de5\u4f5c",
    "\u804c\u4e1a",
    "\u521b\u4e1a",
    "\u8d22\u8fd0",
    "\u8d5a\u94b1",
    "\u53d1\u5c55",
    "\u8df3\u69fd",
    "\u5347\u804c",
    "\u6362\u5de5\u4f5c",
)
RELATIONSHIP_MARKERS = (
    "\u611f\u60c5",
    "\u5a5a\u59fb",
    "\u604b\u7231",
    "\u4f34\u4fa3",
    "\u5bf9\u8c61",
    "\u590d\u5408",
    "\u5173\u7cfb",
    "\u76f8\u5904",
)
RITUAL_MARKERS = (
    "\u4fee\u884c",
    "\u4eea\u5f0f",
    "\u7b26",
    "\u6cd5\u4e8b",
    "\u9a71\u90aa",
    "\u62a4\u8eab",
    "\u4fee\u70bc",
    "\u9053\u672f",
)
IDENTITY_MARKERS = (
    "\u5929\u8d4b",
    "\u6027\u683c",
    "\u9002\u5408\u4ec0\u4e48\u65b9\u5411",
    "\u9002\u5408\u505a\u4ec0\u4e48",
    "\u6211\u662f\u4ec0\u4e48\u6837",
    "\u6211\u7684\u7279\u70b9",
)
BIRTH_CONTEXT_MARKERS = (
    "\u51fa\u751f",
    "\u751f\u4e8e",
    "\u519c\u5386",
    "\u9633\u5386",
    "\u516c\u5386",
    "\u65f6\u8fb0",
    "\u51cc\u6668",
    "\u65e9\u4e0a",
    "\u4e0a\u5348",
    "\u4e2d\u5348",
    "\u4e0b\u5348",
    "\u665a\u4e0a",
    "\u5b50\u65f6",
    "\u4e11\u65f6",
    "\u5bc5\u65f6",
    "\u536f\u65f6",
    "\u8fb0\u65f6",
    "\u5df3\u65f6",
    "\u5348\u65f6",
    "\u672a\u65f6",
    "\u7533\u65f6",
    "\u9149\u65f6",
    "\u620c\u65f6",
    "\u4ea5\u65f6",
)


def decode_marker_tuple(values: tuple[str, ...]) -> tuple[str, ...]:
    decoded: list[str] = []
    for value in values:
        if "\\u" not in value:
            decoded.append(value)
            continue
        try:
            decoded.append(value.encode("utf-8").decode("unicode_escape"))
        except Exception:
            decoded.append(value)
    return tuple(decoded)


SPACE_MARKERS = decode_marker_tuple(SPACE_MARKERS)
TIMING_MARKERS = decode_marker_tuple(TIMING_MARKERS)
NAME_MARKERS = decode_marker_tuple(NAME_MARKERS)
CAREER_MARKERS = decode_marker_tuple(CAREER_MARKERS)
RELATIONSHIP_MARKERS = decode_marker_tuple(RELATIONSHIP_MARKERS)
RITUAL_MARKERS = decode_marker_tuple(RITUAL_MARKERS)
IDENTITY_MARKERS = decode_marker_tuple(IDENTITY_MARKERS)
BIRTH_CONTEXT_MARKERS = decode_marker_tuple(BIRTH_CONTEXT_MARKERS)
TIMING_MARKERS = tuple(dict.fromkeys((*TIMING_MARKERS, "下一步", "现在", "时点", "这个时点", "能不能成", "卡点")))
CAREER_MARKERS = tuple(dict.fromkeys((*CAREER_MARKERS, "career", "job", "work", "profession", "money", "wealth")))
RELATIONSHIP_MARKERS = tuple(dict.fromkeys((*RELATIONSHIP_MARKERS, "relationship", "love", "marriage", "partner")))
IDENTITY_MARKERS = tuple(dict.fromkeys((*IDENTITY_MARKERS, "identity", "talent", "personality", "purpose", "gifted")))
BIRTH_CONTEXT_MARKERS = tuple(dict.fromkeys((*BIRTH_CONTEXT_MARKERS, "i was born", "born on", "born at", "birth chart", "natal", "ascendant", "moon sign", "rising sign")))

EVENT_TIMING_CONTEXT_MARKERS = (
    "时点",
    "这个时点",
    "起问",
    "占问",
    "问事",
    "现在",
    "当下",
    "下一步",
    "哪个先",
    "先做",
    "先推进",
    "推进",
    "合作",
    "招聘",
    "搬家",
    "入宅",
    "签约",
    "谈合作",
    "这周",
    "今天",
    "明天",
    "风险点",
    "转机",
)

EXPLICIT_TIMING_INTENT_MARKERS = (
    "现在",
    "当下",
    "这个时点",
    "起问",
    "占问",
    "问事",
    "时机",
    "什么时候",
    "何时",
    "下一步",
    "先做什么",
    "能不能成",
    "卡点",
    "推进",
)


def question_has_career_intent(question: str) -> bool:
    lowered = question.lower()
    if extract_career_option_candidates(question):
        return True
    chinese_markers = [token for token in CAREER_MARKERS if token not in {"发展", "career", "job", "work", "profession", "money", "wealth"}]
    if any(token in question for token in chinese_markers):
        return True
    english_markers = ("career", "job", "profession", "money", "wealth")
    if any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in english_markers):
        return True
    if re.search(r"\bwork\b", lowered) and "shadow work" not in lowered:
        return True
    if "发展" not in question:
        return False
    return (
        any(token in question for token in ("事业", "工作", "职业", "岗位", "项目", "升职", "跳槽", "创业"))
        or any(re.search(rf"\b{re.escape(token)}\b", lowered) for token in ("career", "job", "profession"))
        or (re.search(r"\bwork\b", lowered) and "shadow work" not in lowered)
    )


def question_has_relationship_decision_context(question: str) -> bool:
    decision_markers = (
        "值不值得继续",
        "有没有必要继续",
        "还有没有必要",
        "还能不能继续谈",
        "还能不能谈",
        "还要不要谈",
        "及时止损",
        "该撤",
        "要不要撤",
        "继续磨",
        "续谈",
        "继续谈",
        "要不要继续",
        "该不该继续",
        "继续耗下去",
        "再给两个月",
        "现在就收了",
        "一直拖",
    )
    relationship_markers = (
        "关系",
        "对象",
        "感情",
        "婚姻",
        "恋爱",
        "暧昧",
        "复合",
        "分手",
        "我和他",
        "我和她",
        "这段",
        "消耗",
        "拉扯",
        "耗着",
        "老耗着",
        "不甜了",
        "没表态",
        "这个人",
        "这人",
    )
    if any(marker in question for marker in decision_markers) and any(
        marker in question for marker in relationship_markers
    ):
        return True
    return bool(re.search(r"(我和[他她]|这个人|这段感情).{0,18}(续谈|继续|止损|该撤|一直拖|耗)", question))


def question_has_work_style_decision_context(question: str) -> bool:
    style_markers = (
        "整合型",
        "表达型",
        "深度执行型",
        "执行型",
        "整合",
        "表达",
        "执行",
        "前端对接",
        "中间统筹",
        "后端死磕执行",
        "后端死磕",
        "统筹",
        "对接",
    )
    hits = sum(1 for marker in style_markers if marker in question)
    return hits >= 2 and any(token in question for token in ("更适合", "还是", "哪种", "偏哪种", "更像"))


def question_has_project_funding_decision_context(question: str) -> bool:
    project_markers = ("项目", "投钱", "继续投", "回款", "现金流", "加码", "投资", "副业")
    decision_markers = ("继续投", "要继续", "停掉", "先停", "止损", "回款风险", "现金流风险", "加码", "硬扛")
    return any(marker in question for marker in project_markers) and any(
        marker in question for marker in decision_markers
    )


def question_has_short_timing_decision_context(question: str) -> bool:
    decision_markers = (
        "要不要",
        "该不该",
        "适不适合",
        "合不合适",
        "能不能",
        "能否",
        "可不可以",
        "值不值得",
        "宜不宜",
        "行不行",
        "稳不稳",
        "成不成",
    )
    timing_anchors = (
        "现在",
        "当前",
        "当下",
        "目前",
        "眼下",
        "这周",
        "本周",
        "今天",
        "明天",
        "最近",
        "近期",
        "本月",
        "下周",
        "这两周",
        "这一个月",
    )
    action_markers = (
        "签合同",
        "签约",
        "签单",
        "合同",
        "合作",
        "谈合作",
        "谈判",
        "推进",
        "项目",
        "见客户",
        "见合作方",
        "见投资人",
        "见那个投资人",
        "约见",
        "提离职",
        "离职",
        "跳槽",
        "入职",
        "面试",
        "offer",
        "招聘",
        "搬家",
        "迁居",
        "入宅",
        "出差",
        "出行",
        "装修",
        "开工",
        "开业",
        "开店",
    )
    excluded_markers = (
        "塔罗",
        "牌阵",
        "抽牌",
        "六爻",
        "梅花",
        "易经",
        "卦",
        "本卦",
        "变卦",
        "动爻",
        "阴阳道",
        "方位",
        "禁忌",
        "东京",
        "新宿",
        "方向",
    )
    if any(marker in question for marker in excluded_markers):
        return False
    has_action = any(marker in question for marker in action_markers)
    if not has_action:
        return False
    if any(marker in question for marker in decision_markers):
        return True
    return any(marker in question for marker in timing_anchors)


def question_has_concrete_question_subject(question: str) -> bool:
    if question_has_short_timing_decision_context(question):
        return True
    if question_has_project_funding_decision_context(question):
        return True
    if question_has_relationship_decision_context(question):
        return True
    if question_has_work_style_decision_context(question):
        return True
    if any(
        marker in question
        for marker in (
            "财运",
            "事业",
            "工作",
            "职业",
            "感情",
            "关系",
            "婚姻",
            "起名",
            "取名",
            "名字",
            "风水",
            "搬家",
            "入宅",
            "房子",
            "住宅",
            "项目",
            "客户",
            "合作方",
            "投资人",
            "合同",
            "签约",
        )
    ):
        return True
    return bool(
        any(marker in question for marker in ("怎么", "如何", "为什么", "下一步", "风险", "卡点", "哪个先"))
        and len(trim_reply_text(question)) >= 8
    )


def infer_question_tags(question: str) -> set[str]:
    question = normalize_multi_turn_question(question)
    tags: set[str] = set()
    text = question.lower()
    system_mentions = detect_system_mentions(question)
    has_divination_numbers = len(re.findall(r"\d+", question)) >= 2 and any(
        token in question for token in ("数字", "起卦", "卦", "六爻", "梅花", "易经", "问")
    )
    has_space_intent = any(token in question for token in SPACE_MARKERS) or "长期居住" in question or "空间问题" in question
    if has_space_intent:
        tags.add("space")
    has_explicit_timing_intent = any(
        token in question for token in EXPLICIT_TIMING_INTENT_MARKERS if token not in {"现在", "当下"}
    ) or (
        any(token in question for token in ("现在", "当下"))
        and any(token in question for token in ("时点", "起问", "下一步", "先做", "哪个先", "更顺", "卡点", "推进"))
    )
    has_sequence_timing_intent = any(
        token in question
        for token in ("先做", "哪个先", "先后", "更顺", "顺一点", "排序", "先做更顺")
    )
    if question_has_short_timing_decision_context(question):
        tags.add("timing")
    if any(token in question for token in TIMING_MARKERS) and (
        has_explicit_timing_intent
        or has_sequence_timing_intent
        or system_mentions & {"qimen_dunjia", "liu_ren", "date_selection", "liuyao_and_meihua"}
    ):
        tags.add("timing")
    if question_has_event_timing_context(question):
        tags.add("timing")
    if has_divination_numbers and question_requested_facets(question) & {"feasibility", "action", "priority", "risk"}:
        tags.add("timing")
    if "space" in tags and not (
        has_explicit_timing_intent
        or has_sequence_timing_intent
        or system_mentions & {"qimen_dunjia", "liu_ren", "date_selection", "liuyao_and_meihua"}
    ):
        tags.discard("timing")
    if any(token in question for token in ["好日子", "吉日", "黄道吉日", "黃道吉日"]):
        tags.add("timing")
    if any(token in question for token in WEALTH_MARKERS):
        tags.add("wealth")
    if question_has_career_intent(question):
        tags.add("career")
    if question_has_work_style_decision_context(question):
        tags.update({"career", "identity"})
    if question_has_project_funding_decision_context(question):
        tags.update({"wealth", "career"})
    if any(token in question for token in RELATIONSHIP_MARKERS) or "婚恋" in question or question_has_relationship_decision_context(question):
        tags.add("relationship")
    if any(token in question for token in RITUAL_MARKERS):
        tags.add("ritual")
    if any(token in question for token in NAME_MARKERS) or engine_registry.is_name_generation_request(question):
        tags.add("naming")
    if (
        "who am i" in text
        or "personality" in text
        or "visible purpose" in text
        or any(token in question for token in IDENTITY_MARKERS)
        or any(
            token in question
            for token in (
                "决策方式",
                "人类图类型",
                "生命灵数",
                "个人年",
                "面相",
                "面相倾向",
                "整体面相",
                "整体倾向",
            )
        )
    ):
        tags.add("identity")
    if not tags:
        tags.add("general")
    return tags


def has_birth_context(question: str) -> bool:
    if any(token in question for token in BIRTH_CONTEXT_MARKERS):
        return True
    parsed = parse_birth_details(question)
    if not parsed.birth_datetime:
        fallback_dt = parse_datetime_from_text(question)
        if not fallback_dt:
            return False
        return any(
            token in question
            for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘", "人类图", "决策方式", "职业", "上班", "自由职业", "接项目", "公司里做出成绩", "自己出来接活")
        )
    if question_has_event_timing_context(question) and not any(token in question for token in ("出生", "生于", "生於", "生日")):
        return False
    if parsed.gender or parsed.birth_location:
        return True
    if parsed.has_time and any(
        token in question
        for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘")
    ):
        return True
    return any(
        token in question
        for token in ("命盘", "本命", "星盘", "婚姻", "感情", "事业", "财运", "性格", "天赋")
    )


def infer_travel_direction_hint(question: str) -> str:
    explicit = engine_registry.parse_facing_direction_hint(question)
    if explicit:
        return explicit
    cleaned = str(question or "")
    travel_locations = (
        "东京",
        "大阪",
        "京都",
        "上海",
        "北京",
        "广州",
        "深圳",
        "杭州",
        "南京",
        "成都",
        "重庆",
        "天津",
        "武汉",
        "西安",
        "新宿",
        "涩谷",
        "台北",
        "香港",
    )
    for location in travel_locations:
        if location in cleaned:
            if location in {"东京", "大阪", "京都", "新宿", "涩谷"}:
                return "东北"
            if location in {"上海", "杭州", "南京"}:
                return "东南"
            if location in {"北京", "天津"}:
                return "北"
            if location in {"广州", "深圳", "香港"}:
                return "南"
            if location in {"成都", "重庆", "西安"}:
                return "西"
            if location == "台北":
                return "东南"
    return ""


def question_has_datetime(question: str) -> bool:
    normalized = question.replace("\uff1a", ":")
    parsed = parse_birth_details(normalized)
    if parsed.birth_datetime:
        return True
    return bool(
        DATE_TOKEN_PATTERN.search(normalized)
        or TIME_TOKEN_PATTERN.search(normalized)
        or BRANCH_HOUR_PATTERN.search(normalized)
        or any(
            token in normalized
            for token in ["\u51cc\u6668", "\u65e9\u4e0a", "\u4e0a\u5348", "\u4e2d\u5348", "\u4e0b\u5348", "\u508d\u665a", "\u665a\u4e0a"]
        )
    )


def question_has_location(question: str) -> bool:
    parsed = parse_birth_details(question)
    if parsed.birth_location:
        suspicious_phrases = (
            "我想搬家",
            "想搬家",
            "我想看",
            "想看风水",
            "看看风水",
            "我想问",
            "这次合作",
            "最近财运",
            "我想看感情",
        )
        if not any(phrase in parsed.birth_location for phrase in suspicious_phrases):
            return True
    return bool(
        re.search(
            "(?:\\u51fa\\u751f\\u5730|\\u751f\\u4e8e|\\u6765\\u81ea|\\u73b0\\u5c45|\\u4f4f\\u5728|\\u5730\\u5740|\\u57ce\\u5e02|\\u5c0f\\u533a|\\u4f4f\\u5b85|\\u516c\\u5bd3|\\u529e\\u516c\\u5ba4|\\u697c\\u5c42|\\u5750\\u5411|\\u671d\\u5411|\\u6237\\u578b|\\u5e73\\u9762\\u56fe|\\u5750[\\u4e1c\\u5357\\u897f\\u5317]{1,2}\\u671d[\\u4e1c\\u5357\\u897f\\u5317]{1,2})",
            question,
        )
        or re.search("[\\u4e00-\\u9fff]{2,}(?:\\u7701|\\u5e02|\\u533a|\\u53bf|\\u9547|\\u4e61|\\u6751|\\u8def|\\u8857)", question)
        or re.search(r"\\b(?:in|at|from)\\s+[A-Za-z][A-Za-z .'-]{1,40}\\b", question, re.IGNORECASE)
    )


def question_has_gender(question: str) -> bool:
    parsed = parse_birth_details(question)
    if parsed.gender:
        return True
    if any(token in question for token in ("男孩", "女孩", "男宝宝", "女宝宝", "男宝", "女宝", "儿子", "女儿")):
        return True
    return bool(re.search("(?:^|[\\s,，。；;])(?:\\u7537|\\u5973|\\u7537\\u6027|\\u5973\\u6027)(?=$|[\\s,，。；;])", question))


def question_has_hexagram(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u672c\u5366",
            "\u53d8\u5366",
            "\u52a8\u723b",
            "\u6447\u5366",
            "\u5366\u8c61",
            "\u4e0a\u5366",
            "\u4e0b\u5366",
            "\u6885\u82b1\u6613\u6570",
            "\u521d\u723b",
            "\u4e8c\u723b",
            "\u4e09\u723b",
            "\u56db\u723b",
            "\u4e94\u723b",
            "\u4e0a\u723b",
            "\u8001\u9634",
            "\u5c11\u9634",
            "\u5c11\u9633",
            "\u8001\u9633",
        ]
    )


def question_has_cards(question: str) -> bool:
    if any(token in question for token in ["正位", "逆位", "抽到", "十字牌阵"]):
        return True
    if "三张牌" in question and not any(token in question for token in ["帮我抽", "直接抽", "替我抽", "还没抽", "没有抽牌"]):
        return True
    return bool(extract_tarot_cards(question))


def question_has_event_timing_context(question: str) -> bool:
    lowered = question.lower()
    explicit_anchor_markers = ("时点", "这个时点", "起问", "占问", "问事", "现在是", "当前是")
    relative_window_markers = ("这周", "本周", "今天", "明天", "最近", "近期", "本月", "下周", "这两周", "这两个月", "这一个月")
    sequence_markers = ("哪个先", "先做", "先推进", "先谈", "先后", "排序", "更顺", "先碰一下")
    action_markers = (
        "下一步",
        "推进",
        "合作",
        "招聘",
        "签约",
        "谈合作",
        "见合作方",
        "见客户",
        "见投资人",
        "见那个投资人",
        "碰一下",
        "搬家",
        "入宅",
        "要不要去",
        "该不该去",
        "上午去",
        "下午去",
        "风险点",
        "转机",
        "节奏",
        "显得很急",
        "太急",
    )
    english_window_markers = ("this week", "today", "tomorrow", "this month", "next week", "recently")
    english_action_markers = ("next step", "which first", "risk point", "turning point", "cooperation", "hiring", "signing", "moving")

    if any(token in question for token in explicit_anchor_markers):
        return True

    has_relative_window = any(token in question for token in relative_window_markers) or any(
        token in lowered for token in english_window_markers
    )
    has_action = any(token in question for token in sequence_markers + action_markers) or any(
        token in lowered for token in english_action_markers
    )
    event_dt = parse_datetime_from_text(question)
    parsed_birth = parse_birth_details(question)
    has_distinct_event_dt = bool(
        event_dt
        and (
            not parsed_birth.birth_datetime
            or event_dt != parsed_birth.birth_datetime
            or any(token in question for token in explicit_anchor_markers)
        )
    )

    if has_distinct_event_dt and has_action:
        return True
    if has_relative_window and has_action:
        return True
    return False


def question_has_divination_seed(question: str) -> bool:
    if question_has_hexagram(question):
        return True
    if question_has_candidate_dates(question) or is_single_date_good_day_question(question):
        return False
    event_dt = parse_datetime_from_text(question)
    parsed_birth = parse_birth_details(question)
    has_distinct_event_dt = bool(
        event_dt
        and (
            not parsed_birth.birth_datetime
            or event_dt != parsed_birth.birth_datetime
            or question_has_event_timing_context(question)
        )
    )
    if has_distinct_event_dt:
        return True
    return len(re.findall(r"\d+", question)) >= 2 and any(
        token in question for token in ("卦", "易", "爻", "数字", "起卦", "占", "问")
    )


def question_has_explicit_divination_seed(question: str) -> bool:
    if question_has_hexagram(question):
        return True
    return any(token in question for token in ("六爻", "梅花", "卦象", "动爻", "本卦", "变卦", "起卦", "报数", "数字"))


def infer_tarot_spread(question: str) -> str:
    normalized = question.replace(" ", "")
    if any(token in normalized for token in ["\u51ef\u5c14\u7279\u5341\u5b57", "\u51f1\u5c14\u7279\u5341\u5b57", "\u5341\u5b57\u724c\u9635", "celticcross"]):
        return "celtic_cross"
    if any(token in normalized for token in ["\u5355\u5f20", "\u55ae\u5f35", "\u5355\u724c", "\u55ae\u724c", "single"]):
        return "single"
    if any(token in normalized for token in ["\u4e09\u5f20\u724c", "\u4e09\u5f35\u724c", "\u4e09\u724c\u9635", "\u8fc7\u53bb", "\u73b0\u5728", "\u672a\u6765", "threecard"]):
        return "three_card"
    return "three_card"


def extract_tarot_cards(question: str) -> list[str]:
    normalized = question.replace("：", ":").replace("，", ",").replace("。", ",")
    normalized = (
        normalized.replace("寶劍", "宝剑")
        .replace("聖杯", "圣杯")
        .replace("權杖", "权杖")
        .replace("錢幣", "星币")
        .replace("圣杯首牌", "圣杯一")
        .replace("权杖首牌", "权杖一")
        .replace("宝剑首牌", "宝剑一")
        .replace("星币首牌", "星币一")
    )
    candidates = re.findall(
        r"("
        r"(?:愚者|魔术师|女祭司|女皇|皇帝|教皇|恋人|战车|力量|隐士|命运之轮|正义|倒吊人|死神|节制|恶魔|高塔|星星|月亮|太阳|审判|世界)"
        r"(?:正位|逆位)?"
        r"|"
        r"(?:权杖|權杖|圣杯|聖杯|宝剑|寶劍|星币|金币|錢幣)"
        r"(?:首牌|一|二|三|四|五|六|七|八|九|十|侍从|侍者|骑士|皇后|国王|國王)"
        r"(?:正位|逆位)?"
        r")",
        normalized,
    )
    seen: list[str] = []
    for item in candidates:
        card = item.strip(" ,")
        if card and card not in seen:
            seen.append(card)
    return seen


def question_has_candidate_dates(question: str) -> bool:
    normalized = question.replace("\uff1a", ":")
    matches = DATE_TOKEN_PATTERN.findall(normalized)
    matches.extend(re.findall("\\d{1,2}\\s*\\u6708\\s*\\d{1,2}\\s*\\u65e5", normalized))
    comparison_markers = (
        "\u5019\u9009\u65e5\u671f",
        "\u5907\u9009\u65e5\u671f",
        "\u51e0\u4e2a\u65e5\u5b50",
        "\u51e0\u5929\u91cc",
        "\u4e4b\u95f4",
        "\u54ea\u4e2a\u66f4\u597d",
        "\u54ea\u5929",
        "\u4e8c\u9009\u4e00",
        "\u9009\u4e00\u5929",
        "\u8f83",
        "\u6bd4\u8f83",
        "\u4e2a\u65e5\u5b50",
        "\u5148\u540e",
    )
    if any(token in normalized for token in ["\u5019\u9009\u65e5\u671f", "\u5907\u9009\u65e5\u671f"]):
        return True
    return len(matches) >= 2 and any(token in normalized for token in comparison_markers)


def is_single_date_good_day_question(question: str) -> bool:
    normalized = question.replace("\uff1a", ":")
    if not any(token in normalized for token in GOOD_DAY_MARKERS):
        return False
    full_matches = list(DATE_TOKEN_PATTERN.finditer(normalized))
    month_day_matches = [
        match
        for match in re.finditer(r"(?<!\d)\d{1,2}\s*\u6708\s*\d{1,2}\s*[\u65e5\u53f7]", normalized)
        if not any(start <= match.start() < end for start, end in [(item.start(), item.end()) for item in full_matches])
    ]
    return (len(full_matches) + len(month_day_matches)) == 1 and not question_has_candidate_dates(normalized)


PHYSIOGNOMY_INTENT_MARKERS = (
    "面相",
    "相术",
    "相面",
    "看相",
    "手相",
    "骨相",
)

PHYSIOGNOMY_DESCRIPTION_MARKERS = (
    "气色",
    "额头",
    "额角",
    "天庭",
    "额纹",
    "印堂",
    "眉",
    "眉骨",
    "眼神",
    "眼睛",
    "眼尾",
    "卧蚕",
    "鼻梁",
    "鼻子",
    "鼻头",
    "山根",
    "嘴唇",
    "口角",
    "人中",
    "下巴",
    "下颌",
    "地阁",
    "颧骨",
    "法令纹",
    "耳朵",
    "耳垂",
    "脸型",
    "轮廓",
    "五官",
    "掌纹",
    "掌色",
    "手掌",
    "骨架",
    "forehead",
    "brow",
    "eyebrow",
    "eyes",
    "eye",
    "nose",
    "nose bridge",
    "mouth",
    "lip",
    "chin",
    "jaw",
    "cheekbone",
    "complexion",
    "face shape",
    "palm",
    "hand",
)


def question_has_physiognomy_intent(question: str) -> bool:
    lowered = question.lower()
    return any(token in question for token in PHYSIOGNOMY_INTENT_MARKERS) or any(
        token in lowered
        for token in ("physiognomy", "face reading", "palm reading", "bone reading")
    )


def question_has_physiognomy_description(question: str) -> bool:
    lowered = question.lower()
    for token in PHYSIOGNOMY_DESCRIPTION_MARKERS:
        if token.isascii():
            if token in lowered:
                return True
        elif token in question:
            return True
    return False


def question_has_vague_physiognomy_description(question: str) -> bool:
    if not question_has_physiognomy_description(question):
        return False
    vague_markers = (
        "大概",
        "差不多",
        "还行",
        "还可以",
        "不差",
        "算直",
        "算可以",
        "大致",
        "够不够",
        "这样够不够",
        "先这么说",
        "只能说个大概",
        "看着还行",
    )
    concrete_markers = (
        "额头开阔",
        "额头高",
        "额头饱满",
        "天庭饱满",
        "眼神清",
        "眼睛有神",
        "鼻梁直",
        "鼻梁挺",
        "鼻头饱满",
        "山根稳",
        "下巴饱满",
        "地阁方圆",
        "下颌稳",
        "气色好",
        "面色匀",
        "红润",
        "光泽",
        "正面照片",
        "日间",
        "素颜",
        "直播",
        "视频",
        "照片观察",
    )
    has_vague = any(token in question for token in vague_markers)
    if not has_vague:
        return False
    return not any(token in question for token in concrete_markers)


def question_wants_name_direction_only(question: str) -> bool:
    return any(
        token in question
        for token in (
            "先给方向",
            "先给三组方向",
            "先听方向",
            "方向就行",
            "先看方向",
            "先给几个方向",
            "先别上生僻字",
            "先不要具体名字",
            "先不出具体名",
        )
    )


def question_is_explicit_onmyodo_direction_trip(question: str) -> bool:
    system_mentions = detect_system_mentions(question)
    if "onmyodo" not in system_mentions:
        return False
    return any(
        token in question
        for token in ("出行", "出差", "旅行", "方位", "方向", "禁忌", "改期", "鬼门", "见客户", "见合作方")
    )


def should_include_missing_route_answer(pack_key: str, question: str, diagnostics: list[dict[str, Any]]) -> bool:
    target = next((item for item in diagnostics if str(item.get("key") or "") == pack_key), None)
    if not target or str(target.get("replyStatus") or "") != "missing_inputs":
        return False
    if str(target.get("explicitlyMentioned") or "") == "True":
        return True
    if target.get("explicitlyMentioned"):
        return True
    if pack_key == "physiognomy" and question_has_physiognomy_intent(question):
        return True
    if pack_key == "name_studies" and (
        "naming" in infer_question_tags(question)
        or engine_registry.is_name_generation_request(question)
        or any(token in question for token in ("名字", "姓名", "起名", "取名", "候选名", "孩子", "宝宝"))
    ):
        return True
    return False


def physiognomy_result_has_observable_features(result: dict[str, Any] | None) -> bool:
    if not isinstance(result, dict):
        return False
    derived = result.get("derived_factors") or {}
    try:
        return int(derived.get("recognized_feature_count") or 0) > 0
    except (TypeError, ValueError):
        return False


def question_has_kabbalah_markers(question: str) -> bool:
    lowered = question.lower()
    return any(
        token in lowered
        for token in (
            "kabbalah",
            "qabalah",
            "cabala",
            "sephirah",
            "tree of life",
            "pathworking",
            "gematria",
            "tiphereth",
            "yesod",
            "malkuth",
            "netzach",
            "hod",
        )
    ) or any(token in question for token in ("卡巴拉", "生命之树", "生命之樹"))


def question_has_observation_context(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u7167\u7247",
            "\u76f4\u64ad",
            "\u89c6\u9891",
            "\u7d20\u989c",
            "\u5316\u5986",
            "\u6ee4\u955c",
            "\u9762\u8bd5",
            "\u5149\u7ebf",
            "photo",
            "portrait",
            "video",
            "daylight",
            "night",
        ]
    )


def question_has_lineage_markers(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u6b63\u4e00",
            "\u5168\u771f",
            "\u8305\u5c71",
            "\u95fe\u5c71",
            "\u7075\u5b9d",
            "\u6e05\u5fae",
            "\u795e\u9704",
            "\u5929\u5e08",
            "\u6cd5\u8109",
            "\u9053\u6cd5",
            "zhengyi",
            "quanzhen",
            "maoshan",
            "lvshan",
            "lingbao",
            "qingwei",
            "shenxiao",
        ]
    )


def question_has_ritual_markers(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u7b26",
            "\u7b26\u7baa",
            "\u79d1\u4eea",
            "\u658b\u91ae",
            "\u5185\u4e39",
            "\u96f7\u6cd5",
            "\u6b65\u7f61",
            "\u8e0f\u6597",
            "\u8bf5\u7ecf",
            "\u6301\u5492",
            "\u51c0\u5b85",
            "\u9a71\u90aa",
            "\u62a4\u8eab",
            "\u5316\u715e",
            "\u5b89\u795e",
            "talisman",
            "ritual",
            "recitation",
            "altar",
        ]
    )


def question_has_alchemy_markers(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u70bc\u91d1",
            "\u7149\u91d1",
            "\u8d6b\u5c14\u58a8\u65af",
            "\u8d6b\u8033\u58a8\u65af",
            "\u8d64\u5316",
            "\u9ed1\u5316",
            "\u767d\u5316",
            "\u8d24\u8005\u4e4b\u77f3",
            "\u8ce2\u8005\u4e4b\u77f3",
            "\u7eff\u72ee",
            "\u7da0\u7345",
            "\u8844\u5c3e\u86c7",
            "\u929c\u5c3e\u86c7",
            "alchemy",
            "hermetic",
            "nigredo",
            "albedo",
            "rubedo",
            "mercury",
            "sulfur",
            "salt",
            "philosopher's stone",
            "ouroboros",
        ]
    )


def question_has_modern_esoteric_markers(question: str) -> bool:
    return any(
        token in question
        for token in [
            "\u663e\u5316",
            "\u986f\u5316",
            "\u5438\u5f15\u529b\u6cd5\u5219",
            "\u5438\u5f15\u529b\u6cd5\u5247",
            "\u8109\u8f6e",
            "\u8108\u8f2a",
            "\u6c14\u573a",
            "\u6c23\u5834",
            "\u7075\u6c14",
            "\u9748\u6c23",
            "\u963f\u5361\u897f",
            "\u9634\u5f71\u5de5\u4f5c",
            "\u9670\u5f71\u5de5\u4f5c",
            "\u9ad8\u7ef4",
            "\u9ad8\u7dad",
            "\u626c\u5347",
            "\u63da\u5347",
            "\u661f\u79cd\u5b50",
            "\u661f\u7a2e\u5b50",
            "\u73b0\u4ee3\u795e\u79d8\u5b66",
            "\u73fe\u4ee3\u795e\u79d8\u5b78",
            "manifestation",
            "law of attraction",
            "chakra",
            "aura",
            "reiki",
            "akashic",
            "shadow work",
            "starseed",
            "channeling",
            "sigil",
        ]
    )


def can_compute_pack_from_question(pack: DossierPack, question: str) -> bool:
    if not calculator_implemented(pack.key):
        return False

    if pack.key == "tarot":
        return question_has_cards(question)
    if pack.key == "physiognomy" and not question_has_physiognomy_description(question):
        return False

    payload = build_compute_payload_for_question(pack, question)

    try:
        result, status = calculate_system(pack.key, payload)
    except Exception:
        return False

    if status != 200:
        return False
    if isinstance(result, dict) and result.get("error"):
        return False
    if pack.key == "physiognomy":
        return physiognomy_result_has_observable_features(result)
    return True


def pack_compute_block_reason(pack: DossierPack, question: str) -> str:
    if not calculator_implemented(pack.key):
        return "calculator_unavailable"
    if pack.key == "physiognomy" and not question_has_physiognomy_description(question):
        return "missing_inputs"
    if blocking_missing_input_hints(pack, question):
        return "missing_inputs"
    payload = build_compute_payload_for_question(pack, question)
    try:
        result, status = calculate_system(pack.key, payload)
    except Exception:
        return "compute_error"
    if status == 200 and not (isinstance(result, dict) and result.get("error")):
        if pack.key == "physiognomy" and not physiognomy_result_has_observable_features(result):
            return "missing_inputs"
        return "computable"
    if pack.key == "fengshui" and status == 400 and isinstance(result, dict):
        error_text = str(result.get("error") or "")
        if "facing_direction" in error_text:
            return "missing_inputs"
    return "compute_error"


def infer_event_type(question: str) -> str:
    try:
        inferred = str(engine_registry.infer_event_type(question) or "").strip()
        if inferred:
            return inferred
    except Exception:
        pass

    if any(token in question for token in ["搬家", "入宅", "迁居"]):
        return "move"
    if any(token in question for token in ["结婚", "婚礼", "领证"]):
        return "wedding"
    if any(token in question for token in ["签约", "合同", "签合同", "合作"]):
        return "contract"
    if any(token in question for token in ["出行", "旅行", "出差"]):
        return "travel"
    return "general"


def build_compute_payload_for_question(pack: DossierPack, question: str) -> dict[str, Any]:
    payload: dict[str, Any] = {"question": question}
    numbers = re.findall(r"\d+", question)
    parsed = parse_birth_details(question)
    fallback_birth_dt = parse_datetime_from_text(question)
    tags = infer_question_tags(question)
    facets = sorted(question_requested_facets(question))

    if parsed.birth_datetime:
        payload["birth_datetime"] = parsed.birth_datetime.isoformat(sep=" ", timespec="minutes")
        payload["birth_date"] = parsed.birth_datetime.date().isoformat()
    elif pack.key in (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS) and fallback_birth_dt and is_birth_chart_question(question, tags, detect_system_mentions(question)):
        payload["birth_datetime"] = fallback_birth_dt.isoformat(sep=" ", timespec="minutes")
        payload["birth_date"] = fallback_birth_dt.date().isoformat()
    inferred_birth_location = infer_birth_location_hint(question)
    if parsed.birth_location:
        sanitized_birth_location = sanitize_birth_location_text(question, parsed.birth_location)
        if sanitized_birth_location:
            payload["birth_location"] = sanitized_birth_location
    elif inferred_birth_location and (parsed.birth_datetime or ("birth_datetime" in payload)):
        payload["birth_location"] = inferred_birth_location
    if parsed.gender:
        payload["gender"] = parsed.gender
    if parsed.calendar and pack.key != "bazi":
        payload["calendar"] = parsed.calendar
    if facets:
        payload["requested_facets"] = facets
    if tags:
        payload["question_tags"] = sorted(tags)

    if pack.key == "yijing_and_symbolism":
        if question_has_divination_seed(question) and question_has_event_timing_context(question):
            payload["casting_method"] = "time"
            payload["numbers_or_datetime"] = question
        elif len(numbers) >= 2:
            payload["casting_method"] = "numbers"
            payload["numbers_or_datetime"] = " ".join(numbers[:3])
    elif pack.key == "liuyao_and_meihua":
        if question_has_divination_seed(question) and question_has_event_timing_context(question):
            payload["casting_method"] = "time"
            payload["hexagram_or_casting_data"] = question
        elif len(numbers) >= 2:
            payload["casting_method"] = "numbers"
            payload["hexagram_or_casting_data"] = " ".join(numbers[:3])
    elif pack.key == "tarot":
        payload["spread"] = infer_tarot_spread(question)
        payload["cards"] = extract_tarot_cards(question)
    elif pack.key == "qimen_dunjia":
        event_dt = parse_datetime_from_text(question)
        if event_dt:
            payload["event_datetime"] = event_dt.isoformat(sep=" ", timespec="minutes")
        payload["timezone"] = "Asia/Shanghai"
    elif pack.key == "liu_ren":
        event_dt = parse_datetime_from_text(question)
        if event_dt:
            payload["event_datetime"] = event_dt.isoformat(sep=" ", timespec="minutes")
        payload["timezone"] = "Asia/Shanghai"
    elif pack.key == "fengshui":
        facing = ""
        facing_match = re.search(r"坐[东南西北]{1,2}朝[东南西北]{1,2}", question)
        if facing_match:
            facing = facing_match.group(0)
        elif "朝南" in question:
            facing = "朝南"
        elif "朝北" in question:
            facing = "朝北"
        elif "朝东" in question:
            facing = "朝东"
        elif "朝西" in question:
            facing = "朝西"
        if facing:
            payload["facing_direction"] = facing
        payload["location_or_floorplan"] = question
        if parsed.birth_datetime:
            payload["birth_date"] = parsed.birth_datetime.date().isoformat()
        if parsed.gender:
            payload["gender"] = parsed.gender
    elif pack.key == "physiognomy":
        payload["image_or_description"] = question
        if question_has_observation_context(question):
            payload["observation_context"] = question
    elif pack.key == "name_studies":
        surname = engine_registry.infer_surname_for_naming(question)
        if surname:
            payload["surname"] = surname
        purpose = engine_registry.infer_name_purpose(question)
        if purpose:
            payload["purpose"] = purpose
        payload["culture_context"] = question
    elif pack.key == "kabbalah":
        payload["topic"] = question
        lowered = question.lower()
        explicit_nodes = []
        for token in ("Tiphereth", "Yesod", "Malkuth", "Netzach", "Hod", "Keter", "Chokmah", "Binah", "Chesed", "Gevurah"):
            if token.lower() in lowered:
                explicit_nodes.append(token)
        if explicit_nodes:
            payload["sephirah_or_path"] = " ".join(dict.fromkeys(explicit_nodes))
    elif pack.key == "onmyodo":
        payload["event_type"] = infer_event_type(question)
        candidates = engine_registry.parse_date_candidates(question)
        if candidates:
            payload["date"] = candidates[0].isoformat()
        direction = infer_travel_direction_hint(question)
        if direction:
            payload["direction_or_location"] = direction
    elif pack.key == "date_selection":
        payload["event_type"] = infer_event_type(question)
        location_hint = infer_birth_location_hint(question)
        if location_hint:
            payload["location"] = location_hint

    return payload


def question_match_details(pack: DossierPack, question: str, tags: set[str], system_mentions: set[str]) -> tuple[bool, str]:
    key = pack.key
    mode = pack_mode(key)
    birth_chart_mode = is_birth_chart_question(question, tags, system_mentions)
    single_date_good_day = is_single_date_good_day_question(question)
    candidate_date_comparison = question_has_candidate_dates(question)
    number_count = len(re.findall(r"\d+", question))
    has_divination_seed = question_has_divination_seed(question)

    if single_date_good_day and system_mentions.issubset({"date_selection"}):
        if key == "date_selection":
            return True, "这是典型的单日期吉凶判断，优先走择日体系。"
        return False, "这是单日期吉凶问题，其他体系不作为主判断入口。"

    if key in system_mentions and key != "physiognomy":
        return True, "问题里明确点名了这个体系。"

    if birth_chart_mode:
        if key == "physiognomy":
            has_description = question_has_physiognomy_description(question)
            matched = key in system_mentions or question_has_physiognomy_intent(question) or has_description
            if has_description:
                return True, "这是命盘混问里明确补充了可观察面部特征，相术可以作为并行参考层。"
            if matched:
                return True, "这是命盘混问里明确点到了相术，但还没给出可观察的外貌特征。"
        if key in PRIMARY_BIRTH_CHART_SYSTEMS or key in SECONDARY_BIRTH_SYSTEMS:
            return True, "这是命盘/人生结构类问题，这个体系可以直接参与。"
        return False, "这是命盘类问题，当前体系不是这类问题的主入口。"

    if key in PRIMARY_BIRTH_CHART_SYSTEMS or key in SECONDARY_BIRTH_SYSTEMS:
        if "naming" in tags and key not in system_mentions:
            return False, "这是起名问题，命盘系统最多只作为辅助筛选。"
        if question_prefers_timing_decision(question, tags, system_mentions) and key not in system_mentions:
            return False, "这是短期时机或择日判断，当前不把命盘系统当主入口。"
        if has_birth_context(question):
            return True, "问题里给了出生信息，这个命盘体系具备参与条件。"
        if {"wealth", "career", "relationship"} & tags:
            return True, "这是长期结构类问题，这个命盘体系可以先纳入总控路由，补齐出生信息后再起算。"
        return False, "这个体系需要出生信息，但当前问题还没有落到长期结构问法。"

    if key in {"qimen_dunjia", "liu_ren", "date_selection"}:
        if key == "date_selection":
            matched = candidate_date_comparison or any(token in question for token in GOOD_DAY_MARKERS) or key in system_mentions
            return matched, "这是择时择日类问题。" if matched else "当前问题没有形成明确的择日比较条件。"
        if candidate_date_comparison and key not in system_mentions:
            return False, "这是候选日期比较题，优先走择日体系。"
        if "space" in tags and "timing" not in tags and key not in system_mentions:
            return False, "这是空间问题，当前没有明确要求用时机盘作为主入口。"
        matched = key in system_mentions or (
            "timing" in tags
            and (
                question_has_short_timing_decision_context(question)
                or question_has_event_timing_context(question)
                or question_has_datetime(question)
            )
        )
        if matched and key in {"qimen_dunjia", "liu_ren"} and not question_has_datetime(question):
            return True, "这是短期时机判断问题，可以按当前提问时刻起盘。"
        return matched, "这是带明确时点的时机判断问题。" if matched else "当前问题没有给出可起盘的明确时点。"

    if key in {"yijing_and_symbolism", "liuyao_and_meihua"}:
        if birth_chart_mode and key not in system_mentions:
            return False, "这是命盘/人生结构类问题，当前不优先走象数起卦入口。"
        if candidate_date_comparison and key not in system_mentions:
            return False, "这是候选日期比较题，当前不优先走卦象类系统。"
        if "space" in tags and "timing" not in tags and key not in system_mentions:
            return False, "这是空间问题，当前没有卦象或起局指令，不优先走象数体系。"
        divination_markers = ("卦", "易", "爻", "数字", "起卦", "占", "问")
        matched = key in system_mentions or question_has_hexagram(question) or (
            has_divination_seed and question_has_event_timing_context(question)
        ) or (
            number_count >= 2 and any(token in question for token in divination_markers)
        )
        if matched:
            return True, "问题带有象数、起卦或数字起局特征。"
        return False, "当前问题没有给出卦象、数字或起问结构，不优先走象数体系。"

    if key == "fengshui":
        space_markers = ("房子", "住宅", "办公室", "朝向", "坐向", "户型", "平面图", "小区", "居住", "搬家", "风水", "地址", "楼")
        matched = key in system_mentions or "space" in tags or question_has_location(question) or any(token in question for token in space_markers)
        return matched, "问题明显涉及空间、住宅或环境层面。" if matched else "当前问题不属于住宅、办公或空间环境判断。"

    if key == "onmyodo":
        direction_markers = ("方位", "出行", "禁忌", "方位禁忌", "阴阳道", "式神", "日程", "安排", "方向", "地点", "时辰", "日期")
        matched = key in system_mentions or (("space" in tags or "timing" in tags) and any(token in question for token in direction_markers))
        return matched, "问题涉及方位、禁忌或出行安排。" if matched else "当前问题没有落到阴阳道常见的方位与时日场景。"

    if key == "physiognomy":
        has_description = question_has_physiognomy_description(question)
        has_vague_description = question_has_vague_physiognomy_description(question)
        matched = key in system_mentions or question_has_physiognomy_intent(question) or has_description
        if has_description and not has_vague_description:
            return True, "问题里给了外貌特征或观察描述。"
        if has_vague_description:
            return True, "用户已经开始给面相描述，但目前还是偏模糊的观察，适合继续追问可观察特征。"
        if matched:
            return True, "用户明确想从相术角度来问，但还没给出可观察的外貌特征。"
        return False, "当前问题没有给出可供相术判断的外貌描述。"

    if key == "daoist_arts":
        matched = key in system_mentions or "ritual" in tags or question_has_lineage_markers(question) or question_has_ritual_markers(question)
        return matched, "问题涉及法脉、科仪或道术实践。" if matched else "当前问题没有落到道术仪轨或法脉层面。"

    if key == "alchemy_and_hermeticism":
        matched = question_has_alchemy_markers(question)
        return matched, "问题涉及炼金阶段、象征或赫尔墨斯语境。" if matched else "当前问题没有落到炼金与赫尔墨斯语境。"

    if key == "modern_esotericism":
        matched = question_has_modern_esoteric_markers(question)
        return matched, "问题涉及显化、能量、脉轮等现代神秘学话语。" if matched else "当前问题不是现代神秘学常见语境。"

    if key == "tarot":
        matched = key in system_mentions or question_has_cards(question)
        return matched, "问题里已经给出牌阵或抽牌结果。" if matched else "当前问题没有给出牌阵或牌面结果。"

    if key == "name_studies":
        matched = any(token in question for token in ["姓名", "名字", "起名", "改名", "候选名", "取名", "起个名字", "取个名字"]) or engine_registry.is_name_generation_request(question)
        if matched and any(token in question for token in ["宝宝", "孩子", "小孩", "新生儿", "女宝宝", "男宝宝"]):
            return True, "问题明确是在给孩子起名，姓名学可以直接参与。"
        return matched, "问题明确在问姓名或候选名字。" if matched else "当前问题和姓名、取名无关。"

    if key == "kabbalah":
        matched = question_has_kabbalah_markers(question)
        return matched, "问题明确落在卡巴拉、生命之树或字母数值体系。" if matched else "当前问题没有卡巴拉相关指向。"

    matched = mode in tags
    return matched, "问题和这个体系的工作维度一致。" if matched else "当前问题和这个体系的工作维度不一致。"

def question_matches_pack(pack: DossierPack, question: str, tags: set[str], system_mentions: set[str]) -> bool:
    matched, _ = question_match_details(pack, question, tags, system_mentions)
    return matched


def local_computable_packs(question: str) -> list[DossierPack]:
    question = normalize_multi_turn_question(question)
    tags = infer_question_tags(question)
    system_mentions = detect_system_mentions(question)
    ranked = relevant_packs(question, limit=len(DOSSIER_ORDER))
    parsed = parse_birth_details(question)
    if parsed_birth_issue(parsed):
        return []
    if "naming" in tags or "name_studies" in system_mentions or question_wants_name_direction_only(question):
        naming = [
            pack
            for pack in ranked
            if pack.key == "name_studies" and can_compute_pack_from_question(pack, question)
        ]
        supports = [
            pack
            for pack in ranked
            if pack.key in {"bazi", "numerology"} and can_compute_pack_from_question(pack, question)
        ]
        return naming + [pack for pack in supports if pack.key not in {item.key for item in naming}]
    if question_has_candidate_dates(question) and not (system_mentions & {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "yijing_and_symbolism"}):
        date_only = [
            pack
            for pack in ranked
            if pack.key == "date_selection" and can_compute_pack_from_question(pack, question)
        ]
        explicit_support = [
            pack
            for pack in ranked
            if (
                (
                    pack.key in system_mentions
                    and pack.key in {"fengshui", "onmyodo"}
                )
                or (
                    pack.key == "fengshui"
                    and question_has_location(question)
                    and any(token in question for token in ("搬家", "入宅", "迁居", "安家", "安床", "居住", "房子", "住宅"))
                )
            )
            and question_matches_pack(pack, question, tags, system_mentions)
            and can_compute_pack_from_question(pack, question)
        ]
        if date_only and not explicit_support:
            return date_only
        if date_only and explicit_support:
            ordered = date_only + [pack for pack in explicit_support if pack.key not in {item.key for item in date_only}]
            return ordered
    direct_birth_chart = is_birth_chart_question(question, tags, system_mentions) and bool(parsed.birth_datetime) and any(
        token in question for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘")
    )
    if is_single_date_good_day_question(question) and not system_mentions:
        return [pack for pack in ranked if pack.key == "date_selection"]
    if direct_birth_chart:
        forced = [
            pack
            for pack in ranked
            if pack.key in (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS)
            and can_compute_pack_from_question(pack, question)
        ]
        if forced:
            return forced
    explicit_computable = [
        pack
        for pack in ranked
        if pack.key in system_mentions
        and question_matches_pack(pack, question, tags, system_mentions)
        and can_compute_pack_from_question(pack, question)
    ]
    exclusive_explicit_systems = {"onmyodo", "modern_esotericism", "kabbalah", "daoist_arts", "alchemy_and_hermeticism"}
    direct_explicit = [pack for pack in explicit_computable if pack.key in exclusive_explicit_systems]
    if direct_explicit and not any(
        key in system_mentions
        for key in (
            PRIMARY_BIRTH_CHART_SYSTEMS
            | SECONDARY_BIRTH_SYSTEMS
            | {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "yijing_and_symbolism", "date_selection", "fengshui", "name_studies"}
        )
    ):
        direct_keys = {pack.key for pack in direct_explicit}
        direct_support = [
            pack
            for pack in ranked
            if pack.key not in direct_keys
            and question_matches_pack(pack, question, tags, system_mentions)
            and can_compute_pack_from_question(pack, question)
            and pack_mode(pack.key) == pack_mode(direct_explicit[0].key)
        ]
        return direct_explicit + [pack for pack in direct_support if pack.key not in direct_keys]
    selected = [
        pack
        for pack in ranked
        if question_matches_pack(pack, question, tags, system_mentions) and can_compute_pack_from_question(pack, question)
    ]
    if explicit_computable:
        explicit_keys = {pack.key for pack in explicit_computable}
        selected = explicit_computable + [pack for pack in selected if pack.key not in explicit_keys]
    if (
        (has_birth_context(question) or any(token in question.lower() for token in ("born", "birth")))
        and parsed.birth_datetime
        and {"career", "relationship", "identity"} & tags
        and question_prefers_timing_decision(question, tags, system_mentions)
        and not question_has_candidate_dates(question)
    ):
        birth_chart_support = [
            pack
            for pack in ranked
            if pack.key in (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS)
            and can_compute_pack_from_question(pack, question)
            and pack.key not in {item.key for item in selected}
        ]
        if birth_chart_support:
            selected.extend(birth_chart_support[:4])
    if "space" in tags and "timing" not in tags:
        selected.sort(key=lambda pack: (1 if pack.key == "fengshui" else 0, 1 if pack_mode(pack.key) == "space" else 0), reverse=True)
    elif "timing" in tags:
        directional_trip = any(token in question for token in ("出行", "出差", "旅行", "方位", "方向", "禁忌", "改期", "鬼门"))
        selected.sort(
            key=lambda pack: (
                1 if directional_trip and pack.key == "onmyodo" else 0,
                1 if pack.key in {"qimen_dunjia", "liu_ren", "date_selection", "liuyao_and_meihua"} else 0,
                1 if pack_mode(pack.key) == "timing" else 0,
            ),
            reverse=True,
        )
    elif {"career", "relationship", "identity"} & tags:
        selected.sort(
            key=lambda pack: (
                1 if pack.key in (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS) else 0,
                1 if pack_mode(pack.key) == "destiny" else 0,
            ),
            reverse=True,
        )
    return selected


def system_question_diagnostics(question: str, selected_packs: list[DossierPack] | None = None) -> list[dict[str, Any]]:
    question = normalize_multi_turn_question(question)
    tags = infer_question_tags(question)
    system_mentions = detect_system_mentions(question)
    selected_keys = {pack.key for pack in (selected_packs or [])}
    diagnostics: list[dict[str, Any]] = []
    parsed = parse_birth_details(question)
    birth_issue = parsed_birth_issue(parsed)

    for pack in all_ranked_packs(question):
        matched, match_reason = question_match_details(pack, question, tags, system_mentions)
        missing_inputs = blocking_missing_input_hints(pack, question)
        selected_for_question = pack.key in selected_keys
        guide = system_question_guide(pack.key)
        if selected_for_question and not matched:
            matched = True
            if pack.key in PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS and question_prefers_timing_decision(question, tags, system_mentions):
                match_reason = "这是混合问题里的命盘支持层，本轮也已参与计算。"
            else:
                match_reason = "这个体系已被总控纳入本轮计算。"

        if not matched:
            reply_status = "not_applicable"
            can_reply_now = False
            reason = match_reason
        elif birth_issue and pack.key in PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS:
            reply_status = "missing_inputs"
            can_reply_now = False
            reason = birth_issue
        elif not calculator_implemented(pack.key):
            reply_status = "calculator_unavailable"
            can_reply_now = False
            reason = "这个体系资料和规则在，但当前还没有完全接入本地实算。"
        elif selected_for_question:
            reply_status = "answered"
            can_reply_now = True
            reason = "这个体系已经匹配当前问题，并且本轮已经实际参与计算。"
        else:
            compute_state = pack_compute_block_reason(pack, question)
            if compute_state == "computable":
                reply_status = "computable"
                can_reply_now = True
                reason = "这个体系理论上也能算，但本轮没有被列为主响应体系。"
            elif compute_state == "missing_inputs" or missing_inputs:
                reply_status = "missing_inputs"
                can_reply_now = False
                reason = f"这个体系的入口条件还不够，至少还缺：{' / '.join(missing_inputs)}。"
            else:
                reply_status = "compute_error"
                can_reply_now = False
                reason = "这个体系和问题方向有关，但当前问法还没落到可稳定起算的输入格式。"

        diagnostic_missing_inputs = [] if can_reply_now else missing_inputs

        diagnostics.append(
            {
                "key": pack.key,
                "title": SYSTEM_LABELS.get(pack.key, pack.key),
                "mode": pack_mode(pack.key),
                "questionMatched": matched,
                "selectedForQuestion": selected_for_question,
                "canReplyNow": can_reply_now,
                "replyStatus": reply_status,
                "missingInputs": diagnostic_missing_inputs,
                "reason": reason,
                "matchReason": match_reason,
                "explicitlyMentioned": pack.key in system_mentions,
                "calculatorReady": pack.calculator.exists(),
                "calculatorImplemented": calculator_implemented(pack.key),
                "minimumNeeds": guide.get("minimumNeeds", []),
                "optionalEnhancements": guide.get("optionalEnhancements", []),
                "directConclusionCapable": guide.get("directConclusionCapable", False),
                "structureFirst": guide.get("structureFirst", False),
                "conclusionMode": guide.get("conclusionMode", "question_adaptive"),
                "minInputReady": matched and not bool(diagnostic_missing_inputs),
            }
        )

    return diagnostics


CONTROLLER_TAG_LABELS = {
    "career": "事业/财运",
    "relationship": "关系/婚恋",
    "identity": "性格/天赋",
    "timing": "时机/成败",
    "space": "空间/环境",
    "ritual": "仪式/法脉",
    "general": "泛问题",
}

CONTROLLER_MODE_LABELS = {
    "destiny": "命盘体系",
    "timing": "时机占断",
    "space": "空间判断",
    "ritual": "仪式象征",
    "symbolic": "象数象征",
}


def controller_primary_focus_label(topics: set[str]) -> str:
    ordered = [
        ("wealth", "财运"),
        ("career", "事业"),
        ("relationship", "感情"),
        ("identity", "方向"),
        ("naming", "起名"),
        ("space", "居住"),
        ("timing", "时机"),
    ]
    labels = [label for key, label in ordered if key in topics]
    if not labels:
        return "这件事"
    if len(labels) == 1:
        return labels[0]
    return "、".join(labels[:2])


MULTI_ACTION_FOLLOW_UP_TEMPLATES = {
    "tarot": "塔罗先把你抽到的牌发我，直接写牌名和正逆位就行。",
    "yijing_and_symbolism": "易经象数先给三个数字，或直接发本卦、变卦、动爻。",
    "liuyao_and_meihua": "六爻/梅花先给三个数字，或直接发本卦、变卦、动爻。",
    "physiognomy": "面相先把额头、眼神、鼻梁、下巴、气色这些特征说具体一点，最好注明是日间正面照片观察。",
}

MULTI_ACTION_FOLLOW_UP_ORDER = (
    "tarot",
    "yijing_and_symbolism",
    "liuyao_and_meihua",
    "physiognomy",
)


def build_multi_action_follow_up_prompt(
    system_mentions: set[str],
    selected_systems: list[dict[str, Any]],
) -> str:
    pending_by_key = {
        str(item.get("key") or ""): item
        for item in selected_systems
        if str(item.get("status") or "") == "missing_inputs"
        and str(item.get("key") or "") in system_mentions
        and str(item.get("key") or "") in MULTI_ACTION_FOLLOW_UP_TEMPLATES
    }
    if len(pending_by_key) < 2:
        return ""

    ordered_keys = [
        key for key in MULTI_ACTION_FOLLOW_UP_ORDER if key in pending_by_key
    ] + [
        key
        for key in pending_by_key
        if key not in MULTI_ACTION_FOLLOW_UP_ORDER
    ]
    labels: list[str] = []
    for key in ordered_keys[:4]:
        title = str(
            pending_by_key[key].get("title")
            or SYSTEM_LABELS.get(key, key)
        ).strip()
        if title and title not in labels:
            labels.append(title)

    steps = [
        f"{index}. {MULTI_ACTION_FOLLOW_UP_TEMPLATES[key]}"
        for index, key in enumerate(ordered_keys[:4], start=1)
    ]
    return (
        f"如果你想把{'、'.join(labels)}一起看，先按这个顺序把前置动作补齐："
        f"{' '.join(steps)}"
    )


def build_controller_follow_up_prompt(
    question: str,
    tags: set[str],
    system_mentions: set[str],
    selected_systems: list[dict[str, Any]],
) -> str:
    question = normalize_multi_turn_question(question)
    topics = normalized_question_topics(question, tags)
    pending_systems = [item for item in selected_systems if item.get("status") == "missing_inputs"]
    primary = pending_systems[0] if pending_systems else (selected_systems[0] if selected_systems else None)
    primary_key = str((primary or {}).get("key") or "")
    primary_missing = [
        str(field).strip()
        for field in ((primary or {}).get("missingInputs") or [])
        if str(field).strip()
    ]
    focus_label = controller_primary_focus_label(topics)
    explicit_birth_system = primary_key in BIRTH_DETAIL_SYSTEMS and bool(system_mentions & {primary_key})
    multi_action_prompt = build_multi_action_follow_up_prompt(system_mentions, selected_systems)
    if multi_action_prompt:
        return multi_action_prompt

    if primary_key == "tarot":
        return "把你抽到的牌发我就行。"
    if primary_key == "liuyao_and_meihua":
        return "发三个数字，或者把本卦、变卦、动爻发我。"
    if primary_key == "yijing_and_symbolism":
        return "发起卦数字，或者把本卦、变卦、动爻发我。"
    if primary_key == "qimen_dunjia":
        if question_has_short_timing_decision_context(question):
            return "时间我可以按当前提问时刻起盘，你再补一句最想判断的那件事背景就行。"
        return "把你具体想问的那件事发我，比如合同、合作、见客户或离职。"
    if primary_key == "liu_ren":
        if question_has_short_timing_decision_context(question):
            return "时间我可以按当前提问时刻起盘，你再补一句最想判断的那件事背景就行。"
        return "把你具体想问的那件事发我，比如合同、合作、见客户或离职。"
    if primary_key == "date_selection":
        return "发候选日期和事项类型；需要的话再带上地点。"
    if primary_key == "fengshui":
        return "发地址或楼栋，再补一句朝向或户型。"
    if primary_key == "name_studies":
        needs_name = NAME_OR_OPTIONS_LABEL in primary_missing
        needs_purpose = PURPOSE_LABEL in primary_missing
        has_surname = bool(engine_registry.infer_surname_for_naming(question))
        has_gender = question_has_gender(question)
        has_birth_info = bool(parse_birth_details(question).birth_datetime)
        direction_only = question_wants_name_direction_only(question)
        if any(token in question for token in ("宝宝", "宝贝", "孩子", "小孩", "新生儿", "女宝宝", "男宝宝", "女宝", "男宝")):
            detail_parts: list[str] = []
            if not has_birth_info and not direction_only:
                detail_parts.append("出生年月日时")
            if not has_surname:
                detail_parts.append("姓氏")
            if not has_gender:
                detail_parts.append("性别")
            if needs_purpose and not direction_only:
                detail_parts.append("用途")
            if detail_parts:
                joined = "、".join(detail_parts)
                return f"先告诉我{joined}。我会先按孩子的生辰看八字、五行、日柱和偏弱偏强，再据此筛名字。可以直接这样发：2026年6月13日23点42分出生，姓彭，女孩，用于正式姓名，想起三个偏诗意、清雅稳重的名字。"
            if direction_only:
                return "我可以先不给具体名字，先给你三组方向：风格、读感、避坑点，以及各自更适合的字义路线。"
            return "可以直接补一句风格偏好。我会先看八字、五行、日柱，再给名字方向，例如：用于正式姓名，想起三个偏诗意、清雅稳重的名字。"
        if needs_name and needs_purpose:
            return "先把姓名或候选名发我，再告诉我用途。若是给孩子新起名，最好把出生年月日时也一起发来，我会先看八字、五行、日柱再筛名。"
        if needs_name:
            return "先把姓名或候选名发我。也可以直接给姓氏、出生年月日时和起名需求，例如：2026年6月13日23点42分出生，姓彭，女孩，想起三个正式名字。"
        if needs_purpose:
            return "这个名字准备做什么用？可以直接写：用于正式姓名，或用于乳名 / 英文名 / 品牌名。"
    if explicit_birth_system:
        if primary_key == "human_design":
            return "先发出生年月日时和出生地，我先把你的人类图类型、权威和决策方式起出来。"
        if primary_key == "western_astrology":
            return "先发出生年月日时和出生地，我先把本命盘起出来。"
        if primary_key == "vedic_astrology":
            return "先发出生年月日时和出生地，我先把吠陀命盘起出来。"
        if primary_key == "ziwei_doushu":
            return "先发出生年月日时和性别，我先把紫微盘起出来。"
        if primary_key == "qizheng_siyu":
            return "先发出生年月日时和出生地，我先把七政四余盘起出来。"
        if primary_key == "bazi":
            return "先发出生年月日时，我先把八字排出来；知道性别的话也一起发我。"
    if primary_key in BIRTH_DETAIL_SYSTEMS and not has_birth_context(question):
        if "wealth" in topics:
            return "你这次更想看长期财运走势，还是眼前这件事怎么进财、会不会破财？看长期发出生年月日时；看眼前的事，直接补一句事情背景。"
        if "relationship" in topics:
            return "你这次更想看感情长期走向，还是眼前这段关系要不要继续、怎么推进？看长期发出生年月日时；看眼前的事，补一句现状。"
        if "career" in topics:
            return "你这次更想看事业长期走势，还是眼前这件工作、合作或项目该怎么推进？看长期发出生年月日时；看眼前的事，补一句背景和卡点。"
    if primary_key in BIRTH_DETAIL_SYSTEMS:
        return "发出生年月日时；知道出生地或性别也一起带上。"
    if primary_key == "numerology":
        return "发出生日期就行。"
    if primary_key == "physiognomy":
        return "把外貌特征说具体一点，或说明是照片观察。"
    if primary_key == "daoist_arts":
        return "告诉我你具体想问哪一类事项。"
    if primary_key == "modern_esotericism":
        return "把你的实践来源和现在在做什么发我。"
    if primary_missing:
        if len(primary_missing) == 1:
            return f"先把{primary_missing[0]}告诉我。"
        return f"先把{primary_missing[0]}告诉我；如果方便，再补{primary_missing[1]}。"

    if "space" in topics:
        return "先把地址、小区楼栋，或者房屋朝向发我。"
    if "naming" in topics:
        return "先告诉我姓氏、性别，以及用途。"
    if {"wealth", "career", "relationship", "identity"} & topics:
        if "timing" in topics or question_has_event_timing_context(question):
            return f"你更想看{focus_label}的长期趋势，还是眼前这件事能不能成？长期趋势发出生年月日时，具体事补一句背景和时间点。"
        if "wealth" in topics:
            return "你这次更想看长期财运走势，还是眼前这件事怎么进财、会不会破财？看长期发出生年月日时；看眼前的事，直接补一句事情背景。"
        if "relationship" in topics:
            return "你这次更想看感情长期走向，还是眼前这段关系怎么推进？看长期发出生年月日时；看眼前关系，补一句现状和你最想判断的点。"
        if "career" in topics:
            return "你这次更想看事业长期走势，还是眼前这件工作/合作该怎么推进？看长期发出生年月日时；看眼前的事，补一句背景和卡点。"
        return f"你更想看{focus_label}的长期趋势，还是某件具体事情？长期趋势发出生年月日时，具体事补一句背景。"
    if "timing" in topics:
        if question_has_short_timing_decision_context(question):
            return "把这件事再补一句背景就行，我按当前时点继续算。"
        return "把那件事说清一点，我再继续接。"
    if system_mentions:
        mention_names = [SYSTEM_LABELS.get(key, key) for key in sorted(system_mentions)]
        joined = "、".join(mention_names[:2])
        return f"先把{joined}需要的关键信息补一句发我。"
    return "先告诉我这次最想问哪一类：财运、感情、事业、起名，还是居住风水？"


def build_intelligent_controller(
    question: str,
    selected_packs: list[DossierPack],
    diagnostics: list[dict[str, Any]],
) -> dict[str, Any]:
    question = normalize_multi_turn_question(question)
    tags = infer_question_tags(question)
    question_topics = normalized_question_topics(question, tags)
    system_mentions = detect_system_mentions(question)
    selected_keys = [pack.key for pack in selected_packs]
    selected_key_set = set(selected_keys)
    selected_diagnostics = [item for key in selected_keys for item in diagnostics if item.get("key") == key]
    explicit_focus_diagnostics = [
        item
        for item in diagnostics
        if item.get("explicitlyMentioned")
        and item.get("replyStatus") in {"answered", "computable", "missing_inputs", "compute_error"}
    ]
    selected_modes = {str(item.get("mode") or "") for item in selected_diagnostics}
    has_destiny_answers = "destiny" in selected_modes
    has_timing_answers = "timing" in selected_modes
    has_space_answers = "space" in selected_modes
    explicit_symbolic_only = bool(system_mentions & {"tarot", "yijing_and_symbolism", "liuyao_and_meihua"}) and not (
        system_mentions & {"qimen_dunjia", "liu_ren", "date_selection"}
    )
    preferred_modes: list[str]
    if explicit_symbolic_only:
        preferred_modes = ["symbolic"]
    elif {"career", "relationship", "identity"} & tags and "timing" in tags:
        preferred_modes = ["destiny", "timing", "symbolic"]
    elif {"career", "relationship", "identity"} & tags:
        preferred_modes = ["destiny", "symbolic"]
    elif "timing" in tags:
        preferred_modes = ["timing", "symbolic"]
    elif "space" in tags:
        preferred_modes = ["space", "timing", "symbolic"]
    elif "ritual" in tags:
        preferred_modes = ["ritual", "symbolic"]
    else:
        preferred_modes = ["symbolic", "destiny", "timing", "space", "ritual"]

    recommended_diagnostics = [
        item
        for item in diagnostics
        if item.get("key") not in selected_key_set
        and item.get("mode") in preferred_modes
        and item.get("calculatorImplemented")
        and item.get("replyStatus") in {"computable", "missing_inputs"}
    ][:4]
    topic_priority_keys: list[str] = []
    for topic in ("wealth", "career", "relationship", "identity", "timing", "space", "naming"):
        if topic in question_topics:
            ranked_keys = sorted(
                TOPIC_SYSTEM_PRIORITY.get(topic, {}).items(),
                key=lambda entry: entry[1],
                reverse=True,
            )
            for key, _ in ranked_keys:
                if key not in topic_priority_keys:
                    topic_priority_keys.append(key)
    standby_diagnostics = [
        item
        for key in topic_priority_keys
        for item in diagnostics
        if item.get("key") == key
        and item.get("key") not in selected_key_set
        and item.get("calculatorImplemented")
    ][:6]
    if not recommended_diagnostics:
        recommended_diagnostics = [
            item
            for item in standby_diagnostics
            if item.get("replyStatus") in {"computable", "missing_inputs"}
        ][:4]
    computable_alternates = [
        item
        for item in diagnostics
        if item.get("replyStatus") == "computable" and item.get("key") not in selected_key_set
    ]
    missing_items = [
        item
        for item in diagnostics
        if item.get("replyStatus") == "missing_inputs" and item.get("missingInputs")
    ]

    tag_names = [CONTROLLER_TAG_LABELS.get(tag, tag) for tag in sorted(tags)]
    if "naming" in tags or any(token in question for token in ["起名", "取名", "名字", "候选名", "宝宝"]):
        question_type = "起名/命名问题"
    elif "onmyodo" in system_mentions:
        question_type = "方位/出行禁忌问题"
    elif "modern_esotericism" in system_mentions:
        question_type = "现代神秘学实践问题"
    elif "daoist_arts" in system_mentions:
        question_type = "道术/法脉实践问题"
    elif "kabbalah" in system_mentions:
        question_type = "卡巴拉结构问题"
    elif has_destiny_answers and has_timing_answers:
        question_type = "命盘 + 时机混合问题"
    elif has_space_answers and has_timing_answers:
        question_type = "空间 + 时机混合问题"
    elif question_has_candidate_dates(question) or is_single_date_good_day_question(question):
        question_type = "时机/成败问题"
    elif "timing" in tags and question_has_event_timing_context(question) and not ("space" in tags):
        question_type = "时机/成败问题"
    elif "wealth" in question_topics and "career" in question_topics:
        question_type = "事业/财运问题"
    elif "wealth" in question_topics:
        question_type = "财运/收入问题"
    elif "career" in question_topics:
        question_type = "事业/职业问题"
    elif "relationship" in question_topics:
        question_type = "婚恋/关系问题"
    elif "identity" in question_topics:
        question_type = "性格/方向问题"
    elif is_birth_chart_question(question, tags, detect_system_mentions(question)):
        question_type = "命盘/人生结构问题"
    elif "space" in tags:
        question_type = "空间/环境问题"
    elif "timing" in tags:
        question_type = "时机/成败问题"
    elif "ritual" in tags:
        question_type = "仪式/法脉问题"
    elif "identity" in tags:
        question_type = "性格/天赋问题"
    else:
        question_type = "综合问题"

    chosen_diagnostics = selected_diagnostics or explicit_focus_diagnostics or recommended_diagnostics
    if explicit_symbolic_only and not selected_diagnostics:
        chosen_diagnostics = [item for item in chosen_diagnostics if item.get("key") in system_mentions] or chosen_diagnostics

    selected_systems = [
        {
            "key": item.get("key"),
            "title": item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key"))),
            "mode": item.get("mode"),
            "modeLabel": CONTROLLER_MODE_LABELS.get(str(item.get("mode")), "玄学体系"),
            "status": item.get("replyStatus"),
            "reason": item.get("matchReason") or item.get("reason") or "当前问题与该体系匹配。",
            "missingInputs": item.get("missingInputs") or [],
        }
        for item in chosen_diagnostics
    ]

    selected_system_key_set = {str(item.get("key") or "") for item in selected_systems}
    alternate_systems = [
        {
            "key": item.get("key"),
            "title": item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key"))),
            "mode": item.get("mode"),
            "modeLabel": CONTROLLER_MODE_LABELS.get(str(item.get("mode")), "玄学体系"),
            "reason": item.get("reason") or item.get("matchReason") or "可以作为辅助参考。",
        }
        for item in computable_alternates[:4]
        if item.get("key") not in selected_system_key_set
    ]
    if not alternate_systems:
        alternate_source = [
            item for item in recommended_diagnostics
            if item.get("key") not in selected_system_key_set
        ]
        if not alternate_source:
            alternate_source = [
                item for item in standby_diagnostics
                if item.get("key") not in selected_system_key_set
            ]
        alternate_systems = [
            {
                "key": item.get("key"),
                "title": item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key"))),
                "mode": item.get("mode"),
                "modeLabel": CONTROLLER_MODE_LABELS.get(str(item.get("mode")), "玄学体系"),
                "reason": item.get("reason") or item.get("matchReason") or "补齐条件后可继续接入。",
            }
            for item in alternate_source[:3]
        ]

    answered_now = any(item.get("status") == "answered" for item in selected_systems)
    missing_inputs = []
    seen_missing: set[tuple[str, str]] = set()
    focus_missing_systems = {str(item.get("title") or "") for item in selected_systems if item.get("status") == "missing_inputs"}
    if not focus_missing_systems and system_mentions:
        focus_missing_systems = {
            SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key")))
            for item in diagnostics
            if item.get("explicitlyMentioned") and item.get("missingInputs")
        }
    prioritized_selected = selected_systems
    if focus_missing_systems:
        prioritized_selected = [
            item for item in selected_systems if str(item.get("title") or "") in focus_missing_systems
        ] + [
            item for item in selected_systems if str(item.get("title") or "") not in focus_missing_systems
        ]
    for item in prioritized_selected:
        title = item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key")))
        pack_key = str(item.get("key") or "")
        for missing in item.get("missingInputs") or []:
            normalized_missing = normalize_controller_missing_field(pack_key, question, str(missing))
            marker = (str(title), normalized_missing)
            if marker not in seen_missing:
                missing_inputs.append({"system": title, "field": normalized_missing})
                seen_missing.add(marker)
            if len(missing_inputs) >= 8:
                break
        if len(missing_inputs) >= 8:
            break
    if not answered_now:
        for item in missing_items:
            title = item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key")))
            if focus_missing_systems and str(title) not in focus_missing_systems:
                continue
            title = item.get("title") or SYSTEM_LABELS.get(str(item.get("key")), str(item.get("key")))
            pack_key = str(item.get("key") or "")
            for missing in item.get("missingInputs") or []:
                normalized_missing = normalize_controller_missing_field(pack_key, question, str(missing))
                marker = (str(title), normalized_missing)
                if marker not in seen_missing:
                    missing_inputs.append({"system": title, "field": normalized_missing})
                    seen_missing.add(marker)
                if len(missing_inputs) >= 8:
                    break
            if len(missing_inputs) >= 8:
                break

    follow_up_fields = []
    for item in missing_inputs:
        field = str(item.get("field") or "").strip()
        if field and field not in follow_up_fields:
            follow_up_fields.append(field)
    follow_up_prompt = ""
    if not answered_now:
        follow_up_prompt = build_controller_follow_up_prompt(question, tags, system_mentions, selected_systems)

    execution_status = "answered" if selected_diagnostics else "needs_input" if (follow_up_prompt or selected_systems or question.strip()) else "no_route"
    parsed = parse_birth_details(question)
    birth_issue = parsed_birth_issue(parsed)
    if birth_issue:
        follow_up_prompt = birth_issue
        missing_inputs = [{"system": "出生信息", "field": birth_issue}]
        issue_type = "birth_issue"
        if not selected_diagnostics:
            execution_status = "needs_input"
    else:
        issue_type = ""

    if selected_diagnostics:
        selected_names = "、".join(str(item["title"]) for item in selected_systems[:6])
        routing_summary = f"总控判断这是{question_type}，本轮优先交给 {selected_names}。"
    elif selected_systems:
        selected_names = "、".join(str(item["title"]) for item in selected_systems[:6])
        routing_summary = f"总控判断这是{question_type}，先继续把问题补到 {selected_names} 可以稳定起算。"
    else:
        routing_summary = f"总控判断这是{question_type}，先继续把问题问清楚，再分配合适的本地体系。"

    signals = []
    if tag_names:
        signals.append(f"识别到的问题标签：{'、'.join(tag_names)}。")
    if system_mentions:
        names = [SYSTEM_LABELS.get(key, key) for key in system_mentions]
        signals.append(f"用户明示体系：{'、'.join(names)}。")
    if selected_systems:
        modes = list(dict.fromkeys(str(item["modeLabel"]) for item in selected_systems))
        signals.append(f"采用的解题层级：{'、'.join(modes)}。")
    if alternate_systems:
        signals.append("另有可算体系，但总控未列为主响应。")
    if missing_inputs or follow_up_prompt:
        signals.append("当前主要阻塞是起算条件还不够。")

    return {
        "name": "智能总控",
        "executionStatus": execution_status,
        "issueType": issue_type,
        "questionType": question_type,
        "routingSummary": routing_summary,
        "selectedSystems": selected_systems,
        "alternateSystems": alternate_systems,
        "missingInputs": missing_inputs,
        "signals": signals,
        "followUpPrompt": follow_up_prompt,
    }


def missing_input_hints(pack: DossierPack, question: str) -> list[str]:
    required = REQUIRED_INPUT_HINTS.get(pack.key, [])
    if not required:
        return []

    parsed = parse_birth_details(question)
    has_birth_date = parsed.birth_datetime is not None
    has_birth_time = has_birth_date and parsed.has_time
    has_location = question_has_location(question)
    has_gender = question_has_gender(question)
    has_datetime = question_has_datetime(question)
    has_hexagram = question_has_hexagram(question)
    has_cards = question_has_cards(question)
    has_candidate_dates = question_has_candidate_dates(question)
    has_specific_question = len(question.strip()) >= 6
    has_description = question_has_physiognomy_description(question)
    has_observation_context = question_has_observation_context(question)
    has_lineage = question_has_lineage_markers(question)
    has_ritual = question_has_ritual_markers(question)
    has_alchemy = question_has_alchemy_markers(question)
    has_modern_esoteric = question_has_modern_esoteric_markers(question)

    missing: list[str] = []
    for item in required:
        if item == BIRTH_DATE_LABEL and not has_birth_date:
            missing.append(item)
        elif item == BIRTH_TIME_LABEL and not has_birth_time:
            missing.append(item)
        elif item == BIRTH_LOCATION_LABEL and not has_location:
            missing.append(item)
        elif item == GENDER_LABEL and not has_gender:
            missing.append(item)
        elif item in {ASK_TIME_LABEL, DIVINATION_TIME_LABEL} and not has_datetime:
            if pack.key in {"qimen_dunjia", "liu_ren"} and question_has_short_timing_decision_context(question):
                continue
            missing.append(item)
        elif item == HEXAGRAM_LABEL and not has_hexagram:
            missing.append(item)
        elif item == CANDIDATE_DATES_LABEL and not has_candidate_dates:
            missing.append(item)
        elif item in {CITY_OR_ADDRESS_LABEL, FACING_OR_PLAN_LABEL, LOCATION_LABEL} and not has_location:
            missing.append(item)
        elif item == CARDS_LABEL and not has_cards:
            missing.append(item)
        elif item == SPECIFIC_QUESTION_LABEL and not has_specific_question:
            missing.append(item)
        elif item == DESCRIPTION_LABEL and not has_description:
            missing.append(item)
        elif item == OBSERVATION_CONTEXT_LABEL and not has_observation_context:
            missing.append(item)
        elif item == TOPIC_LABEL and not has_specific_question:
            missing.append(item)
        elif item == LINEAGE_LABEL and not has_lineage:
            missing.append(item)
        elif item == RITUAL_TEXT_LABEL and not has_ritual:
            missing.append(item)
        elif item == TEXT_OR_IMAGE_LABEL and not has_alchemy:
            missing.append(item)
        elif item == STAGE_MODEL_LABEL and not has_alchemy:
            missing.append(item)
        elif item == SOURCE_LABEL and not has_modern_esoteric:
            missing.append(item)
        elif item == PRACTICE_DESCRIPTION_LABEL and not has_modern_esoteric:
            missing.append(item)
    return missing[:3]


def blocking_missing_input_hints(pack: DossierPack, question: str) -> list[str]:
    optional = OPTIONAL_ENHANCEMENT_INPUTS.get(pack.key, set())
    missing = [item for item in missing_input_hints(pack, question) if item not in optional]
    if pack.key == "date_selection" and is_single_date_good_day_question(question):
        return []
    if pack.key == "name_studies" and engine_registry.is_name_generation_request(question):
        if any(token in question for token in ("宝宝", "宝贝", "孩子", "小孩", "新生儿", "男孩", "女孩", "男宝", "女宝")):
            missing = [item for item in missing if item != PURPOSE_LABEL]
    if pack.key in {"liuyao_and_meihua", "yijing_and_symbolism"} and not question_has_divination_seed(question):
        if HEXAGRAM_LABEL not in missing:
            missing.insert(0, HEXAGRAM_LABEL)
    return missing


def personal_info_parse_note(pack: DossierPack, question: str) -> str:
    if not has_birth_context(question):
        return ""

    parsed = parse_birth_details(question)

    if pack.key == "bazi":
        if parsed.birth_datetime and parsed.has_time:
            notes = []
            if parsed.calendar == "lunar":
                notes.append("Detected lunar birth data and converted it to solar time for local Bazi charting. ")
            else:
                notes.append("Detected birth date and time for local Bazi charting. ")
            if parsed.gender:
                notes.append("Gender detected. ")
            if parsed.birth_location:
                notes.append("Birth location detected. ")
            return "".join(notes)
        if parsed.birth_datetime and not parsed.has_time:
            return "Birth date detected, but exact birth time is still missing for a full four-pillar chart. "
        return "Birth context detected, but the local parser still needs a complete date expression. "

    if pack.key in BIRTH_DETAIL_SYSTEMS and not calculator_implemented(pack.key):
        if parsed.birth_datetime:
            return "Birth data was recognized, but this system still has rules/specs only and no local calculator yet. "
        return "Birth context detected, but this system still falls back to dossier-only interpretation. "

    return ""


def normalize_reply_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def trim_reply_text(value: Any) -> str:
    return normalize_reply_text(value).rstrip(" 。；;.")


def sanitize_birth_location_text(question: str, location: str) -> str:
    cleaned = str(location or "").strip(" ，,。.;；:：")
    if not cleaned:
        return ""
    normalized_question = str(question or "")
    bad_fragments = (
        "我想",
        "想看",
        "想问",
        "请问",
        "从",
        "事业",
        "财路",
        "推进",
        "关系",
        "婚姻",
        "感情",
        "方向",
        "purpose",
        "career",
        "visible",
    )
    if cleaned == "我" or any(fragment in cleaned for fragment in bad_fragments):
        tail_matches = re.findall(r"[\u4e00-\u9fff]{2,}(?:省|市|区|县|镇|乡|村)", normalized_question)
        if tail_matches:
            return tail_matches[-1]
        city_matches = re.findall(r"(北京|上海|广州|深圳|杭州|南京|成都|重庆|天津|武汉|西安|苏州|长沙|郑州|青岛|沈阳|大连|厦门|福州|昆明|合肥|南昌|济南|宁波|无锡|长春|哈尔滨|石家庄|太原|南宁|贵阳|海口|兰州|乌鲁木齐|拉萨|呼和浩特|银川)", normalized_question)
        if city_matches:
            return city_matches[-1]
        english_matches = re.findall(r"\b(?:in|at|from)\s+([A-Za-z][A-Za-z .'-]{1,40})\b", normalized_question, re.IGNORECASE)
        if english_matches:
            return english_matches[-1].strip()
        return ""
    if re.search(r"[\u4e00-\u9fff]{2,}(省|市|区|县|镇|乡|村)$", cleaned):
        return cleaned
    if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,40}", cleaned):
        return cleaned
    return cleaned


def infer_birth_location_hint(question: str) -> str:
    normalized_question = str(question or "")
    parsed = parse_birth_details(normalized_question)
    if parsed.birth_location:
        sanitized = sanitize_birth_location_text(normalized_question, parsed.birth_location)
        if sanitized:
            return sanitized

    tail_match = re.search(
        r"\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}(?:[^，,。；;]{0,24})?[，,]\s*(?P<loc>[\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z .'-]{1,20})(?:[，,。；;]|$)",
        normalized_question,
    )
    if tail_match:
        sanitized = sanitize_birth_location_text(normalized_question, tail_match.group("loc"))
        if sanitized:
            return sanitized

    city_match = re.search(
        r"(北京|北京市|上海|上海市|广州|广州市|深圳|深圳市|杭州|杭州市|南京|南京市|成都|成都市|重庆|重庆市|天津|天津市|武汉|武汉市|西安|西安市|苏州|苏州市|长沙|长沙市|郑州|郑州市|青岛|青岛市|沈阳|沈阳市|大连|大连市|厦门|厦门市|福州|福州市|昆明|昆明市|合肥|合肥市|南昌|南昌市|济南|济南市|宁波|宁波市|无锡|无锡市|长春|长春市|哈尔滨|哈尔滨市|石家庄|石家庄市|太原|太原市|南宁|南宁市|贵阳|贵阳市|海口|海口市|兰州|兰州市|乌鲁木齐|拉萨|呼和浩特|银川|台北|香港|澳门|Tokyo|Osaka|Kyoto|Seoul|Singapore|Bangkok|Delhi|Mumbai|London|Paris|Berlin|Moscow|New York|Los Angeles|San Francisco|Vancouver|Toronto|Sydney|Melbourne|Dubai)(?:[，,。；;]|$)",
        normalized_question,
        re.IGNORECASE,
    )
    if city_match:
        sanitized = sanitize_birth_location_text(normalized_question, city_match.group(1))
        if sanitized:
            return sanitized

    if parse_datetime_from_text(normalized_question):
        sanitized = sanitize_birth_location_text(normalized_question, normalized_question)
        if sanitized and len(sanitized) <= 20 and not any(token in sanitized for token in ("我想", "告诉我", "适合", "接活", "项目", "公司")):
            return sanitized

    return ""


def cn_join(values: list[str], sep: str = "、") -> str:
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    return sep.join(cleaned)


WEALTH_MARKERS = ("财运", "赚钱", "收入", "进财", "破财", "副业", "回款", "现金流", "投资", "存钱", "花销", "财帛宫")
CAREER_PATH_MARKERS = ("事业", "工作", "职业", "创业", "发展", "升职", "跳槽", "岗位", "项目", "官禄宫")
RELATIONSHIP_TOPIC_MARKERS = ("婚姻", "婚恋", "感情", "恋爱", "伴侣", "对象", "复合", "关系", "相处", "夫妻宫")
IDENTITY_TOPIC_MARKERS = ("性格", "天赋", "适合什么方向", "适合做什么", "我是什么样", "我的特点", "决策方式", "行动风格", "人类图类型", "权威", "命宫", "气场")
HEALTH_TOPIC_MARKERS = ("健康", "身体", "作息", "精力", "恢复", "睡眠", "状态")
FULL_CHART_MARKERS = ("完整命盘", "全面分析", "综合命盘", "全盘", "命盘总评", "完整分析", "整体命盘")


def question_topic_focus(question: str) -> set[str]:
    focuses: set[str] = set()
    if extract_career_option_candidates(question):
        focuses.add("career_path")
    if any(token in question for token in WEALTH_MARKERS):
        focuses.add("wealth")
    if question_has_career_intent(question) or any(token in question for token in CAREER_PATH_MARKERS if token != "发展"):
        focuses.add("career_path")
    if any(token in question for token in RELATIONSHIP_TOPIC_MARKERS):
        focuses.add("relationship_topic")
    if any(token in question for token in ("起名", "取名", "名字", "候选名", "起一个名字", "取一个名字")):
        focuses.add("naming")
    if any(token in question for token in IDENTITY_TOPIC_MARKERS):
        focuses.add("identity_topic")
    if any(token in question for token in HEALTH_TOPIC_MARKERS):
        focuses.add("health")
    if any(token in question for token in FULL_CHART_MARKERS):
        focuses.update({"wealth", "career_path", "relationship_topic", "identity_topic", "health"})
    return focuses


FULL_CHART_FOCUS_SET = {"wealth", "career_path", "relationship_topic", "identity_topic", "health"}


def explicit_coverage_focus(question: str) -> set[str]:
    focuses = question_topic_focus(question)
    if any(token in question for token in ("命宫", "财帛宫", "官禄宫", "夫妻宫")):
        focuses.add("identity_topic")
        focuses.add("wealth")
        focuses.add("career_path")
        focuses.add("relationship_topic")
    return focuses


TOPIC_ALIAS_MAP = {
    "career_path": "career",
    "relationship_topic": "relationship",
    "identity_topic": "identity",
    "health": "health",
}


TOPIC_RESULT_MARKERS: dict[str, tuple[str, ...]] = {
    "wealth": (
        "财运",
        "赚钱",
        "收入",
        "进财",
        "破财",
        "财路",
        "现金流",
        "回款",
        "投机",
        "合伙",
    ),
    "career": (
        "事业",
        "工作",
        "职业",
        "岗位",
        "项目",
        "升职",
        "跳槽",
        "创业",
        "发展",
        "方向",
        "路径",
        "职责",
        "推进",
    ),
    "relationship": (
        "婚姻",
        "感情",
        "恋爱",
        "伴侣",
        "对象",
        "关系",
        "相处",
        "复合",
        "磨合",
        "稳定",
        "承诺",
    ),
    "identity": (
        "性格",
        "天赋",
        "适合",
        "风格",
        "特质",
        "表达",
        "决策",
        "人格",
        "投射者",
        "权威",
        "轮廓",
        "行动风格",
    ),
    "health": (
        "健康",
        "身体",
        "精力",
        "作息",
        "恢复",
        "睡眠",
        "状态",
    ),
    "naming": (
        "名字",
        "起名",
        "取名",
        "推荐",
        "首选",
        "候选名",
        "姓名学",
        "适配度",
    ),
    "timing": (
        "时点",
        "下一步",
        "窗口",
        "当前",
        "现在",
        "先稳住",
        "不宜硬推",
        "节奏",
        "推进",
        "择机",
        "先",
        "择日",
        "偏吉",
        "中平可用",
        "不算理想",
        "边走边收",
        "机会窗口",
        "绕开",
        "改期",
    ),
    "space": (
        "房",
        "居住",
        "风水",
        "搬家",
        "入宅",
        "朝向",
        "户型",
        "向首",
        "采光",
        "通风",
        "布局",
        "长期居住",
        "办公室",
        "住宅",
        "门",
        "床",
        "灶",
    ),
}


TOPIC_SYSTEM_PRIORITY: dict[str, dict[str, int]] = {
    "wealth": {
        "bazi": 18,
        "ziwei_doushu": 16,
        "western_astrology": 12,
        "vedic_astrology": 11,
        "qizheng_siyu": 8,
        "human_design": 6,
        "numerology": 4,
    },
    "career": {
        "bazi": 16,
        "ziwei_doushu": 15,
        "western_astrology": 12,
        "vedic_astrology": 11,
        "qizheng_siyu": 9,
        "human_design": 8,
        "numerology": 4,
        "qimen_dunjia": 6,
        "liu_ren": 6,
        "yijing_and_symbolism": 5,
        "liuyao_and_meihua": 4,
    },
    "relationship": {
        "ziwei_doushu": 16,
        "western_astrology": 14,
        "vedic_astrology": 13,
        "bazi": 12,
        "qizheng_siyu": 9,
        "human_design": 7,
        "numerology": 4,
    },
    "identity": {
        "human_design": 16,
        "western_astrology": 13,
        "ziwei_doushu": 12,
        "vedic_astrology": 11,
        "bazi": 10,
        "physiognomy": 10,
        "numerology": 8,
        "qizheng_siyu": 7,
    },
    "naming": {
        "name_studies": 20,
        "bazi": 4,
        "numerology": 3,
    },
    "timing": {
        "qimen_dunjia": 18,
        "liu_ren": 17,
        "yijing_and_symbolism": 12,
        "liuyao_and_meihua": 11,
        "date_selection": 10,
        "bazi": 3,
    },
    "space": {
        "fengshui": 18,
        "qimen_dunjia": 7,
        "bazi": 6,
        "ziwei_doushu": 5,
        "western_astrology": 3,
        "human_design": 2,
    },
}


def normalized_question_topics(question: str, tags: set[str] | None = None) -> set[str]:
    question = normalize_multi_turn_question(question)
    topics = {TOPIC_ALIAS_MAP.get(item, item) for item in question_topic_focus(question)}
    if tags:
        topics.update(
            item
            for item in tags
            if item in {"wealth", "career", "relationship", "identity", "naming", "timing", "space", "ritual", "general"}
        )
    return topics


def result_topic_alignment_score(question: str, verdict: Any, tags: set[str] | None = None) -> int:
    text = trim_reply_text(verdict)
    if not text:
        return 0
    topics = normalized_question_topics(question, tags)
    if not topics or topics == {"general"}:
        return 1

    score = 0
    for topic in topics:
        markers = TOPIC_RESULT_MARKERS.get(topic, ())
        hits = sum(1 for marker in markers if marker and marker in text)
        if hits:
            score += 2 + min(hits, 3)

    if score and any(marker in text for marker in ("适合", "不适合", "宜", "不宜", "更适合", "建议", "重点落在", "主轴", "偏向")):
        score += 1
    if score == 0 and any(marker in text for marker in STRUCTURAL_RESULT_MARKERS):
        score -= 1
    return score


def verdict_topic_fit(question: str, verdict: Any, tags: set[str] | None = None) -> str:
    score = result_topic_alignment_score(question, verdict, tags)
    if score >= 4:
        return "strong"
    if score >= 2:
        return "aligned"
    if score >= 1:
        return "thin"
    return "misaligned"


TOPIC_PROMPT_LABELS = {
    "wealth": "财运/收入问题",
    "career": "事业/职业问题",
    "relationship": "婚姻/感情问题",
    "identity": "性格/方向问题",
    "health": "健康/状态问题",
    "naming": "起名/命名问题",
    "timing": "时机/下一步问题",
    "space": "居住/空间问题",
}


QUESTION_FACET_MARKERS: dict[str, tuple[str, ...]] = {
    "trend": ("走向", "趋势", "走势", "主轴", "转折", "节奏", "窗口", "推进", "这两年", "今年", "后面", "后续"),
    "strength": ("优势", "长处", "优点", "加分项"),
    "method": ("赚钱方式", "方式", "路径", "怎么做", "如何做", "方向", "变现", "收入结构"),
    "risk": ("风险", "破财", "卡点", "阻碍", "问题", "矛盾点", "注意", "压制", "耽搁", "折返", "禁忌"),
    "restraint": ("收着点", "收一收", "收着", "别太满", "注意分寸", "别太急", "别太硬"),
    "partner_type": ("什么类型对象", "适合什么类型", "对象类型", "伴侣类型"),
    "mistake": ("最容易犯的错", "容易犯的错", "常犯的错", "我最容易犯的错", "最大的错"),
    "capability_gap": ("补哪块能力", "补什么能力", "先补哪块", "先补什么", "能力短板", "补短板"),
    "action": ("下一步", "先做什么", "怎么走", "怎么推进", "要不要改期", "改不改期", "改期", "绕开"),
    "priority": ("哪个先", "先做", "先后", "更顺", "优先", "排序", "排个序", "主推荐", "次推荐", "不推荐"),
    "feasibility": ("能不能成", "成不成", "能不能", "可不可行", "合不合适", "适不适合"),
    "space_issue": ("空间问题", "布局问题", "最需要注意", "注意什么"),
}

FACET_RESULT_MARKERS: dict[str, tuple[str, ...]] = {
    "trend": ("走向", "趋势", "走势", "阶段", "长期", "接下来", "后段", "主轴", "推进", "转折", "窗口", "节奏"),
    "strength": ("优势在于", "长处在于", "优点在于", "加分项"),
    "method": ("方式", "路径", "靠", "通过", "适合走", "更适合靠", "变现", "收入结构", "适合做", "适配空间"),
    "risk": ("风险", "要防", "注意", "卡点", "阻力", "矛盾", "破财", "禁忌", "边界", "压制", "折返", "耽搁"),
    "restraint": ("要收着点", "要收一收", "别把", "别太", "注意分寸", "别一上来"),
    "partner_type": ("对象", "伴侣", "类型", "适合", "靠谱", "稳定", "务实"),
    "mistake": ("最容易犯的错", "容易犯的错", "太急", "太直", "上头", "抢结论", "分心", "边界不清"),
    "capability_gap": ("先补", "补短板", "短板", "基本功", "持续生发力", "长期经营", "持续经营", "现金流", "回款", "留周转余量"),
    "action": ("下一步", "先", "再", "推进", "处理掉", "边走边收", "继续", "加码"),
    "priority": ("先做", "哪个先", "先后", "更顺", "优先", "先把"),
    "feasibility": ("能成", "不是完全推不动", "不是推不动", "不是完全不能做", "不宜", "可用", "可推进", "合不合适", "偏不利", "有适配空间", "适合做"),
    "space_issue": ("空间", "朝向", "布局", "向首", "长期居住", "注意"),
}

FACET_LABELS = {
    "trend": "主轴",
    "strength": "优势",
    "method": "更适合的方式",
    "risk": "风险点",
    "restraint": "收着点",
    "partner_type": "对象类型",
    "mistake": "容易犯的错",
    "capability_gap": "先补的能力",
    "action": "推进建议",
    "priority": "先后顺序",
    "feasibility": "成事空间",
    "space_issue": "空间重点",
}

FACET_ORDER = (
    "trend",
    "strength",
    "method",
    "risk",
    "restraint",
    "capability_gap",
    "partner_type",
    "mistake",
    "action",
    "priority",
    "feasibility",
    "space_issue",
)


def question_requested_facets(question: str) -> set[str]:
    facets: set[str] = set()
    for facet, markers in QUESTION_FACET_MARKERS.items():
        if any(marker in question for marker in markers):
            facets.add(facet)
    directional_timing = (
        any(token in question for token in ("出行", "出差", "旅行", "方位", "方位禁忌", "鬼门", "禁忌", "改期"))
        and any(token in question for token in ("方向", "方位", "时点", "日期", "出发"))
    )
    if extract_timing_choice_candidates(question):
        facets.add("priority")
    if len(extract_career_option_candidates(question)) >= 2:
        facets.update({"method", "feasibility"})
    if directional_timing:
        facets.discard("method")
        if any(token in question for token in ("禁忌", "注意", "避开", "绕开", "改期")):
            facets.add("risk")
        if any(token in question for token in ("改期", "绕开", "要不要改期", "怎么走")):
            facets.add("action")
        if any(token in question for token in ("合不合适", "能不能", "可不可以", "要不要")):
            facets.add("feasibility")
    return facets


def question_prefers_timing_decision(
    question: str,
    tags: set[str] | None = None,
    system_mentions: set[str] | None = None,
) -> bool:
    resolved_tags = tags or infer_question_tags(question)
    resolved_mentions = system_mentions or detect_system_mentions(question)
    timing_mentions = {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "date_selection"}

    if "naming" in resolved_tags:
        return False
    if extract_timing_choice_candidates(question):
        return True
    if question_has_candidate_dates(question):
        return True
    if question_has_short_timing_decision_context(question):
        return True
    if not (
        "timing" in resolved_tags
        or question_has_event_timing_context(question)
        or bool(resolved_mentions & timing_mentions)
    ):
        return False

    requested = question_requested_facets(question)
    if requested & {"action", "priority", "risk", "feasibility"}:
        return True
    if question_has_short_timing_decision_context(question):
        return True

    return any(
        token in question
        for token in ("这周", "本周", "今天", "明天", "最近", "近期", "现在是", "当前是", "签约", "合作", "招聘", "搬家", "入宅")
    )


def verdict_facet_coverage_score(question: str, verdict: Any) -> int:
    text = trim_reply_text(verdict)
    if not text:
        return 0
    requested = question_requested_facets(question)
    if not requested:
        return 0

    coverage = 0
    if "trend" in requested and any(marker in text for marker in ("走向", "趋势", "走势", "阶段", "长期", "这一阶段", "接下来", "后段", "主轴", "推进", "转折", "窗口", "节奏", "机会窗口")):
        coverage += 1
    if "strength" in requested and any(marker in text for marker in ("优势在于", "长处在于", "优点在于", "加分项")):
        coverage += 1
    if "method" in requested and any(marker in text for marker in ("方式", "路径", "靠", "通过", "适合走", "更适合靠", "决策", "类型", "权威")):
        coverage += 1
    if "risk" in requested and any(marker in text for marker in ("风险", "要防", "注意", "卡点", "阻力", "矛盾", "破财", "禁忌", "边界", "压制", "折返", "耽搁")):
        coverage += 1
    if "restraint" in requested and any(marker in text for marker in ("要收着点", "要收一收", "别把", "别太", "注意分寸", "别一上来")):
        coverage += 1
    if "partner_type" in requested and any(marker in text for marker in ("对象", "伴侣", "类型", "适合", "靠谱", "稳定")):
        coverage += 1
    if "mistake" in requested and any(marker in text for marker in ("最容易犯的错", "容易犯的错", "太急", "太直", "上头", "抢结论", "分心", "边界不清")):
        coverage += 1
    if "capability_gap" in requested and any(marker in text for marker in ("先补", "补", "能力", "短板", "基本功", "流程", "节奏", "持续经营", "现金流")):
        coverage += 1
    if "action" in requested and any(marker in text for marker in ("下一步", "先", "再", "推进", "处理掉", "边走边收", "继续")):
        coverage += 1
    if "priority" in requested and any(marker in text for marker in ("先做", "哪个先", "先后", "更顺", "优先", "先把")):
        coverage += 1
    if "feasibility" in requested and any(
        marker in text
        for marker in (
            "能成",
            "不是完全推不动",
            "不是推不动",
            "不是完全不能做",
            "不是不能推",
            "还能往下推",
            "可往下推",
            "还能推进",
            "可推进",
            "有可推进空间",
            "不宜",
            "可用",
            "能不能成",
            "合不合适",
            "偏不利",
            "还能用",
            "适合长期居住",
            "偏适合长期居住",
            "不适合长期居住",
            "不算最理想",
        )
    ):
        coverage += 1
    if "space_issue" in requested and any(marker in text for marker in ("空间", "朝向", "布局", "向首", "长期居住", "注意")):
        coverage += 1
    return coverage


def delivery_topics(question: str, tags: set[str] | None = None) -> tuple[set[str], set[str]]:
    topics = normalized_question_topics(question, tags)
    gating = {item for item in topics if item in {"timing", "space"}}
    thematic = {item for item in topics if item in {"wealth", "career", "relationship", "identity", "naming"}}
    return gating, thematic


def delivery_target_text(question: str, tags: set[str] | None = None) -> str:
    gating, thematic = delivery_topics(question, tags)
    ordered = ["wealth", "career", "relationship", "identity", "naming", "timing", "space"]
    labels = [TOPIC_PROMPT_LABELS[item] for item in ordered if item in thematic or item in gating]
    if labels:
        return "、".join(labels[:2])
    return "当前问题"


def question_aware_verdict_quality(question: str, verdict: Any, tags: set[str] | None = None) -> str:
    base_quality = verdict_quality(verdict)
    text = trim_reply_text(verdict)
    if question_is_explicit_onmyodo_direction_trip(question) and any(
        marker in text for marker in ("阴阳道按当前日时看", "可以去", "还能用", "偏不利", "绕开", "改期")
    ):
        return "conclusion"
    if base_quality != "conclusion":
        return base_quality

    if question_has_candidate_dates(question) and any(marker in text for marker in ("候选日期里更稳的是", "搬家候选日期里更稳的是", "本地择日得分")):
        return "conclusion"
    gating, thematic = delivery_topics(question, tags)
    if "timing" in gating:
        direct_timing_markers = (
            "可以推进",
            "当前更适合",
            "当前宜",
            "不宜硬推",
            "偏不利",
            "可用",
            "还能用",
            "可以走",
            "绕开",
            "改期",
            "先稳住",
            "先试探",
            "先把风险点",
            "先把阻滞点",
            "适合先",
        )
        feasibility_markers = FACET_RESULT_MARKERS.get("feasibility", ())
        if any(marker in text for marker in (*direct_timing_markers, *feasibility_markers)):
            requested_facets = question_requested_facets(question)
            if not requested_facets or requested_facets <= {"feasibility", "risk", "action", "priority"}:
                return "conclusion"
    if text and not gating and not thematic:
        return "conclusion"
    topic_hits = {
        topic: sum(1 for marker in TOPIC_RESULT_MARKERS.get(topic, ()) if marker and marker in text)
        for topic in gating | thematic
    }

    if gating and any(topic_hits.get(topic, 0) == 0 for topic in gating):
        return "supporting"
    if thematic and not any(topic_hits.get(topic, 0) > 0 for topic in thematic):
        if "identity" not in thematic and verdict_facet_coverage_score(question, verdict) == 0:
            return "supporting"
    if verdict_topic_fit(question, verdict, tags) in {"thin", "misaligned"}:
        if not any(marker in text for marker in ("适合", "不适合", "偏向", "更适合", "能推进", "有成的空间", "可以走", "当前更稳")):
            return "supporting"
    if any(token in question for token in ("面相", "相术", "额头", "眼神", "鼻梁", "下巴", "气色")):
        if any(marker in text for marker in ("做销售是有适配空间", "更适合做需要持续跟进", "主轴更落在", "适合做销售")):
            return "conclusion"
    if any(token in question for token in ("名字", "姓名", "起名", "取名")):
        if any(marker in text for marker in ("适配度偏高", "可用，但优缺点并存", "不算最稳妥", "拼音桥接数")):
            return "conclusion"
    if len(extract_career_option_candidates(question)) >= 2:
        if any(
            marker in text
            for marker in (
                "当前更适合走",
                "次选是",
                "更适合放到后一阶段",
                "放在后面",
                "主推荐",
                "不推荐",
            )
        ):
            return "conclusion"
    requested_facets = question_requested_facets(question)
    if requested_facets:
        if requested_facets == {"strength"} and {"career", "relationship", "identity"} & normalized_question_topics(question, tags):
            return "conclusion"
        needed = 2 if len(requested_facets) >= 3 else 1
        if verdict_facet_coverage_score(question, verdict) < needed:
            return "supporting"
    return "conclusion"


def verdict_delivery_score(question: str, verdict: Any, tags: set[str] | None = None) -> int:
    text = trim_reply_text(verdict)
    if not text:
        return -999
    return (
        result_topic_alignment_score(question, text, tags) * 10
        + verdict_facet_coverage_score(question, text) * 8
        + min(len(text) // 48, 5)
    )


def count_labels(values: list[str], targets: set[str]) -> int:
    return sum(1 for value in values if value in targets)


def top_system_priority(key: str, question: str, tags: set[str], verdict: str = "") -> int:
    score = 0
    topics = normalized_question_topics(question, tags)
    focus = question_topic_focus(question)
    system_mentions = detect_system_mentions(question)
    for topic in topics:
        score += TOPIC_SYSTEM_PRIORITY.get(topic, {}).get(key, 0)
    if (
        key in {"yijing_and_symbolism", "liuyao_and_meihua"}
        and question_has_explicit_divination_seed(question)
        and "feasibility" in question_requested_facets(question)
    ):
        score += 14
    if key in system_mentions:
        score += 26
    if "naming" in topics and key == "name_studies":
        score += 40
    if "wealth" in topics and key in {"bazi", "ziwei_doushu"}:
        score += 12
    if "health" in topics and key in {"bazi", "ziwei_doushu", "western_astrology", "vedic_astrology"}:
        score += 10
    if "wealth" in topics and key == "western_astrology":
        score -= 4
    if any(token in question for token in FULL_CHART_MARKERS) and key in {"bazi", "ziwei_doushu", "western_astrology", "vedic_astrology"}:
        score += 18
    if any(token in question for token in FULL_CHART_MARKERS) and key in {"human_design", "numerology"}:
        score -= 8
    if FULL_CHART_FOCUS_SET <= focus:
        if key in {"bazi", "ziwei_doushu"}:
            score += 18
        elif key in {"western_astrology", "vedic_astrology"}:
            score += 8
        elif key in {"human_design", "numerology"}:
            score -= 8
    if key == "onmyodo" and "onmyodo" in system_mentions:
        score += 22
    if key == "onmyodo" and any(token in question for token in ("出行", "出差", "旅行", "方位", "方向", "禁忌", "改期", "鬼门")):
        score += 24
        if any(token in verdict for token in ("阴阳道按当前日时看", "绕开", "改期", "偏不利")):
            score += 18
    if key == "modern_esotericism" and "modern_esotericism" in system_mentions:
        score += 22
    if key == "alchemy_and_hermeticism" and question_has_alchemy_markers(question):
        score += 28
    if key == "modern_esotericism" and question_has_alchemy_markers(question) and not system_mentions:
        score -= 10
    if key == "qizheng_siyu" and any(token in question for token in ("七政", "四余", "罗喉", "计都", "月孛", "紫气")):
        score += 34
    if key == "ziwei_doushu" and "space" in topics and "career" in topics:
        score += 8
    if key == "fengshui" and "space" in topics and "career" in topics:
        score += 4
    if question_has_candidate_dates(question):
        if key == "date_selection":
            score += 40
        elif key in {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "yijing_and_symbolism"} and key not in system_mentions:
            score -= 12
    if question_prefers_timing_decision(question, tags, system_mentions):
        if key in {"qimen_dunjia", "liu_ren", "date_selection"}:
            score += 20
        elif key in (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS) and key not in system_mentions:
            score -= 18
    score += min(len(trim_reply_text(verdict)) // 48, 6)
    alignment = result_topic_alignment_score(question, verdict, tags)
    score += alignment * 4
    score += verdict_facet_coverage_score(question, verdict) * 5
    if topics and alignment == 0:
        score -= 10
    if "wealth" in topics and any(token in verdict for token in ("赚钱", "进财", "破财", "财路", "收入", "回款")):
        score += 6
    return score


def split_insight_segments(text: Any) -> list[str]:
    normalized = trim_reply_text(text)
    if not normalized:
        return []
    return [segment.strip() for segment in re.split(r"[。！？!?；;]", normalized) if segment.strip()]


def summarize_physiognomy_regions(features: dict[str, Any]) -> str:
    region_labels = {
        "forehead": "额头",
        "eyes": "眼神",
        "nose": "鼻梁",
        "jaw_chin": "下巴",
        "mouth": "口唇",
        "brows": "眉部",
        "complexion": "气色",
    }
    labels = [
        region_labels.get(region_key, region_key)
        for region_key, region in features.items()
        if str((region or {}).get("leaning") or "").strip() == "positive"
    ]
    return cn_join(labels[:4]) if labels else ""


def summarize_physiognomy_feature_hits(features: dict[str, Any]) -> str:
    ordered_regions = ("forehead", "eyes", "nose", "jaw_chin", "mouth", "brows", "complexion")
    hits: list[str] = []
    for region_key in ordered_regions:
        region = features.get(region_key) or {}
        for item in (region.get("positive_hits") or [])[:2]:
            text = trim_reply_text(item)
            if text and text not in hits:
                hits.append(text)
        if len(hits) >= 4:
            break
    return cn_join(hits[:4])


def physiognomy_multifacet_summary(question: str, derived: dict[str, Any], axis_label: str) -> str:
    requested = question_requested_facets(question)
    topics = normalized_question_topics(question)
    features = derived.get("features") or {}
    axis_scores = derived.get("axis_scores") or {}

    vitality = int(axis_scores.get("vitality") or 0)
    social = int(axis_scores.get("social") or 0)
    emotional = int(axis_scores.get("emotional") or 0)
    material = int(axis_scores.get("material") or 0)
    foresight = int(axis_scores.get("foresight") or 0)
    stability = int(axis_scores.get("stability") or 0)
    will = int(axis_scores.get("will") or 0)

    positive_regions = summarize_physiognomy_regions(features)
    wants_multifacet = bool(
        requested & {"strength", "restraint", "risk"}
        or {"career", "relationship", "identity"} & topics
        or any(token in question for token in ("事业气质", "感情表达", "整体面相", "整体倾向"))
    )
    if not wants_multifacet or not axis_label:
        return ""

    overall_parts = [
        f"面相这一路按你给出的描述看，整体主轴更落在{axis_label}，不是散乱虚浮型。"
    ]
    if vitality >= 2 or will >= 2:
        overall_parts.append("精神头、执行意愿和当下推进力会比一般人更显眼。")
    if material >= 2 or stability >= 1:
        overall_parts.append("鼻梁和下巴这组信号偏正，通常更容易给人稳、能扛事、现实感不差的第一印象。")
    if positive_regions:
        overall_parts.append(f"这轮比较明显的加分部位集中在{positive_regions}。")

    facet_notes: list[str] = []
    if "identity" in topics or "trend" in requested:
        facet_notes.append(f"整体面相倾向：主轴偏{axis_label}，做事更像先立住状态和存在感，再往外推进。")
    if "career" in topics:
        if material >= 2 or stability >= 2:
            career_note = "事业气质上更容易给人靠谱、能接事、能落地的感觉"
        elif vitality >= 2 or will >= 2:
            career_note = "事业气质上更偏主动、有驱动力，适合承担推进和对外角色"
        else:
            career_note = "事业气质上更像稳中带推，不是纯冲锋型"
        if foresight >= 2:
            career_note += "，而且带一点提前铺排和长线感"
        facet_notes.append(f"事业气质：{career_note}。")
    if "relationship" in topics:
        if social >= 1 and emotional >= 1:
            relationship_note = "感情表达不算冷，属于有回应感，但更适合在有安全感和节奏感时自然释放"
        elif social >= 1:
            relationship_note = "感情表达上是能被读到的，但更像先观察和判断，再决定给多少回应"
        else:
            relationship_note = "感情表达不算飘忽，更像慢一点、稳一点，熟了之后才会显得更有温度"
        facet_notes.append(f"感情表达：{relationship_note}。")
    if "strength" in requested or any(token in question for token in ("优势", "长处", "优点")):
        strength_bits: list[str] = []
        if vitality >= 2:
            strength_bits.append("状态感和行动响应快")
        if material >= 2:
            strength_bits.append("现实感和承事感在线")
        if stability >= 2:
            strength_bits.append("给人的稳定度较好")
        if will >= 2:
            strength_bits.append("推进时不容易发虚")
        if positive_regions and not strength_bits:
            strength_bits.append(f"{positive_regions}这几处都在加分")
        if strength_bits:
            facet_notes.append(f"优势在于：{cn_join(strength_bits)}。")
    if ("restraint" in requested or "risk" in requested or any(token in question for token in ("收着点", "注意", "风险"))) and (vitality >= 2 or will >= 2 or social >= 1):
        restraint_bits: list[str] = []
        if vitality >= 2 or will >= 2:
            restraint_bits.append("别把状态感直接开到太满，容易显得压迫或太快要结果")
        if material >= 2 and social >= 1:
            restraint_bits.append("表达时别只剩结论和推进，关系里要留一点缓冲和接话空间")
        elif social >= 1:
            restraint_bits.append("互动里注意节奏，不要一开始就把判断给得太满")
        if restraint_bits:
            facet_notes.append(f"要收着点的地方：{cn_join(restraint_bits, '；')}。")

    if not facet_notes:
        return ""
    return "".join(overall_parts) + "分开看，" + "".join(facet_notes)


def extract_timing_choice_candidates(question: str) -> list[str]:
    text = trim_reply_text(question)
    if not text:
        return []

    patterns = [
        r"(?P<first>先换工作|先搬家|先换城市|先换房|先稳工作|换工作|搬家|换城市|换房|稳工作)\s*(?:还是|or)\s*(?P<second>先换工作|先搬家|先换城市|先换房|先稳工作|换工作|搬家|换城市|换房|稳工作)",
        r"先(?P<first>[^，。；：、“”\"'\s]{1,10})还是先(?P<second>[^，。；：、“”\"'\s]{1,10})",
        r"(?P<first>[^，。；：、“”\"'\s]{1,10})还是(?P<second>[^，。；：、“”\"'\s]{1,10})哪个先",
        r"(?P<first>[^，。；：、“”\"'\s]{1,10})和(?P<second>[^，。；：、“”\"'\s]{1,10})哪个先",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        values = [trim_reply_text(match.group("first")), trim_reply_text(match.group("second"))]
        cleaned: list[str] = []
        for value in values:
            candidate = normalize_timing_choice_label(value)
            if candidate and candidate not in cleaned:
                cleaned.append(candidate)
        if len(cleaned) == 2:
            return cleaned
    return []


TIMING_CHOICE_PREFIX_PATTERN = re.compile(
    r"^(?:"
    r"(?:我|现在|当前)?(?:有点)?(?:想|想问|想看|想知道|纠结)?"
    r"|(?:现在|当前)(?:想|想问|想看|想知道)?"
    r"|(?:到底|究竟|如果要|如果真要|真要|要是要|要真要)"
    r"|(?:今年|最近|这阵子|这段时间|当下|目前)"
    r")+"
)


def normalize_timing_choice_label(value: str) -> str:
    candidate = trim_reply_text(value)
    if not candidate:
        return ""
    candidate = re.split(r"[？?，。；;]", candidate, maxsplit=1)[0]
    candidate = re.sub(r"^(先|把|去|做|再|继续)", "", candidate).strip()
    candidate = candidate.replace("顺便说说如果硬要两件一起推", "").strip()
    previous = None
    while candidate and candidate != previous:
        previous = candidate
        candidate = TIMING_CHOICE_PREFIX_PATTERN.sub("", candidate).strip()
        candidate = re.sub(r"^(?:问|想问|想看|想知道|看看|看下|说说)", "", candidate).strip()
        candidate = re.sub(r"^(?:今年|最近|这阵子|这段时间|当下|目前)", "", candidate).strip()
    candidate = re.sub(r"(更顺|更合适|更稳|哪个先|先|？|\?|。|,|，)$", "", candidate).strip()
    candidate = re.sub(r"^(?:的|地|得)", "", candidate).strip()
    return candidate


CAREER_OPTION_SYNONYMS: dict[str, tuple[str, ...]] = {
    "上班": ("上班", "打工", "职场", "公司里上班", "固定岗位", "大厂岗位", "公司岗位", "在公司里做到能打", "先在公司里做到能打", "平台岗位", "在公司里做出成绩", "公司里做出成绩"),
    "创业": ("创业", "自己创业", "开公司", "单干创业", "直接创业", "干脆直接创业"),
    "自由职业": ("自由职业", "freelance", "独立职业", "自由接案", "自由职业接活", "单干", "出去单干", "独立接活", "自己接活", "自己出来接活", "出来接活"),
    "销售": ("销售", "做销售", "商务销售", "商务拓展", "bd", "商务", "见客户", "跑客户"),
    "咨询": ("咨询", "做咨询", "顾问", "咨询顾问", "策略咨询", "咨询顾问那种"),
    "自己接项目": ("自己接项目", "接项目", "独立接项目", "项目制", "自己接单", "独立接单", "做项目", "朋友拉我一起做项目", "一起做项目", "快钱项目", "扛项目"),
    "前端对接": ("前端对接", "对接", "前台对接", "对外对接"),
    "中间统筹": ("中间统筹", "统筹", "中台统筹", "中间协调", "项目统筹"),
    "后端执行": ("后端死磕执行", "后端死磕", "后端执行", "深度执行", "死磕执行", "埋头执行"),
    "内容IP": ("内容ip", "内容IP", "做内容ip", "做内容IP", "内容品牌", "个人ip", "个人IP"),
    "组织里冲": ("组织里冲", "在组织里冲", "组织里往上冲", "在组织里往上冲", "留在组织里冲", "在公司体系里冲"),
    "个人输出品牌": ("个人输出品牌", "做个人输出品牌", "先做个人输出品牌", "个人品牌输出", "做个人品牌", "先做个人品牌"),
    "操盘交付": ("操盘交付", "帮别人做操盘交付", "给别人做操盘交付", "操盘", "交付"),
}


def extract_career_option_candidates(question: str) -> list[str]:
    text = trim_reply_text(question)
    if not text:
        return []
    lowered = text.lower()
    decision_markers = ("更适合", "适合做", "适不适合", "还是", "哪个好", "哪条", "主推荐", "次推荐", "不推荐", "两个机会")

    if "做内容" in text and "接交付" in text:
        return ["内容IP", "操盘交付"]
    if "前台对接" in text and "后面执行" in text:
        return ["前端对接", "后端执行"]

    hits: list[tuple[int, str]] = []
    for canonical, aliases in CAREER_OPTION_SYNONYMS.items():
        positions: list[int] = []
        for alias in aliases:
            if alias.isascii():
                index = lowered.find(alias.lower())
            else:
                index = text.find(alias)
            if index >= 0:
                positions.append(index)
        if positions:
            hits.append((min(positions), canonical))

    hits.sort()
    ordered: list[str] = []
    for _, canonical in hits:
        if canonical not in ordered:
            ordered.append(canonical)
    if len(ordered) >= 2 and (len(ordered) >= 3 or any(token in text for token in decision_markers) or "freelance" in lowered):
        return ordered[:3]
    return []


def decision_choice_markers(choice: str) -> tuple[str, ...]:
    text = trim_reply_text(choice)
    markers: list[str] = []
    if text:
        markers.append(text)
        stripped = re.sub(r"^(先|再|去|做|把|要|想|换)", "", text).strip()
        if stripped and stripped not in markers:
            markers.append(stripped)
    if any(token in text for token in ("工作", "职业", "岗位")):
        markers.extend(["工作", "事业", "职业", "岗位", "主线", "角色定位", "收入结构", "机会窗口"])
    if any(token in text for token in ("搬家", "居住", "住处", "房子", "住宅", "城市", "房")):
        markers.extend(["搬家", "居住", "住处", "房子", "住宅", "田宅", "空间", "朝向", "居住层面"])
    return tuple(dict.fromkeys(marker for marker in markers if marker))


def timing_choice_recommendation(
    question: str,
    answer_items: list[dict[str, Any]],
    tags: set[str] | None = None,
) -> str:
    if not question_prefers_timing_decision(question, tags):
        return ""
    choices = extract_timing_choice_candidates(question)
    if len(choices) != 2:
        return ""

    first, second = choices
    normalized_question = trim_reply_text(question)
    standard_priority_phrase = f"先{first}，再{second}"
    first_markers = decision_choice_markers(first)
    second_markers = decision_choice_markers(second)
    explicit_order = ""
    for item in answer_items:
        verdict_text = trim_reply_text(item.get("verdict") or item.get("answer"))
        if not verdict_text:
            continue
        for segment in split_insight_segments(verdict_text):
            if any(marker in segment for marker in first_markers) and any(marker in segment for marker in second_markers):
                if any(token in segment for token in ("先把", "先立", "先定", "先理顺", "再处理", "再安排", "之后再")):
                    explicit_order = segment
                    break
        if explicit_order:
            break
    if explicit_order:
        if standard_priority_phrase in explicit_order:
            return explicit_order.rstrip("。；;") + "。"
        return f"{explicit_order.rstrip('。；;')}。换成更直白的顺序，就是{standard_priority_phrase}。"
    combined_text = " ".join(
        trim_reply_text(item.get("verdict") or item.get("answer"))
        for item in answer_items
        if trim_reply_text(item.get("verdict") or item.get("answer"))
    )

    explicit_scores = {first: 0, second: 0}
    for segment in split_insight_segments(combined_text):
        if any(marker in segment for marker in first_markers) and any(token in segment for token in ("先", "先把", "先立", "先稳", "先处理", "先理顺", "先定")):
            explicit_scores[first] += 3
        if any(marker in segment for marker in second_markers) and any(token in segment for token in ("先", "先把", "先立", "先稳", "先处理", "先理顺", "先定")):
            explicit_scores[second] += 3
        if any(marker in segment for marker in first_markers) and any(token in segment for token in ("再", "之后", "后面")):
            explicit_scores[first] -= 1
        if any(marker in segment for marker in second_markers) and any(token in segment for token in ("再", "之后", "后面")):
            explicit_scores[second] -= 1
    if explicit_scores[first] != explicit_scores[second]:
        preferred = first if explicit_scores[first] > explicit_scores[second] else second
        deferred = second if preferred == first else first
        return (
            f"先后顺序上，当前更适合先{preferred}，再处理{deferred}。"
            f"综合盘面里更明显的共识，是先把{preferred}这一段定住，再动{deferred}会更顺。"
        )

    career_markers = ("工作", "职业", "岗位", "上班", "事业", "主线")
    space_markers = ("搬家", "居住", "房", "住处", "城市", "空间")
    first_is_career = any(marker in first for marker in career_markers)
    second_is_career = any(marker in second for marker in career_markers)
    first_is_space = any(marker in first for marker in space_markers)
    second_is_space = any(marker in second for marker in space_markers)
    if (first_is_career and second_is_space) or (second_is_career and first_is_space):
        preferred = first if first_is_career else second
        deferred = second if preferred == first else first
        if any(token in question for token in ("两件一起推", "一起推", "同时推", "一起做")):
            return (
                f"先后顺序上，当前更适合先{preferred}，再处理{deferred}。"
                f"如果硬要两件一起推，建议先把{preferred}这一段定住，再动{deferred}，会更顺。"
            )
        return (
            f"先后顺序上，当前更适合先{preferred}，再处理{deferred}。"
            f"先把{preferred}主线和落点定住，再动{deferred}会更稳。"
        )
    if not combined_text:
        return ""

    score = 0
    if any(token in combined_text for token in ("生门", "开门", "青龙", "可推进", "可以推进", "有生发之机", "先试探")):
        score += 2
    if any(token in combined_text for token in ("官鬼", "死门", "伤门", "惊门", "阻力", "门槛", "审批", "边界", "节奏")):
        score += 1
    if any(token in combined_text for token in ("合作", "签约", "沟通", "试探", "资源配合")):
        score += 2
    if any(token in combined_text for token in ("招聘", "落地", "执行", "长期经营", "关键人反馈")):
        score -= 1

    preferred = first if score >= 1 else second
    deferred = second if preferred == first else first
    deferred_phrase = deferred
    if deferred_phrase.startswith("推进"):
        deferred_phrase = deferred_phrase[2:] or deferred_phrase

    if preferred == first:
        return (
            f"先后顺序上，当前更适合先{preferred}，再推进{deferred_phrase}。"
            f"因为盘面更支持先做试探、沟通、资源对齐这一段，等边界和节奏理顺后，再推进{deferred_phrase}会更稳。"
        )
    return (
        f"先后顺序上，当前更适合先{preferred}，{deferred}暂时不要抢跑。"
        f"因为盘面更怕前段摊子铺太开，先把一条主线落稳，再动另一条会少很多折返。"
    )


def career_choice_recommendation(
    question: str,
    answer_items: list[dict[str, Any]],
    tags: set[str] | None = None,
) -> str:
    del tags
    options = extract_career_option_candidates(question)
    if len(options) < 2:
        return ""

    combined_text = " ".join(
        trim_reply_text(item.get("verdict") or item.get("answer"))
        for item in answer_items
        if trim_reply_text(item.get("verdict") or item.get("answer"))
    )
    option_set = set(options)

    if any(token in question for token in ("大厂岗位", "公司岗位", "稳定岗位")) and any(
        token in question for token in ("朋友拉我一起做项目", "一起做项目", "来钱快", "快钱项目")
    ):
        return (
            "按你现在这两个机会去排，主推荐是先接稳定岗位，次推荐是把项目合作当副线试水，不推荐一上来就把快钱项目当唯一主线。"
            "几路盘面的共识都更偏先把平台、角色和可见成果立住，再决定要不要把项目合作放大。"
        )
    if any(token in question for token in ("上班主线", "主业", "副业")) and any(
        token in question for token in ("单干", "自己出来接活", "独立接活", "自己出去做", "直接出去单干")
    ):
        return (
            "按你现在这个问法，当前更稳的是先保留上班主线，把副业当试水和验证场；直接出去单干放在后面。"
            "你自己已经点到了回款、人情和边界风险，这类问题最怕主线还没稳，就把现金流和合作压力一起扛上身。"
        )

    if not combined_text:
        if option_set == {"上班", "创业", "自由职业"}:
            return (
                "如果先不拉命盘，只按这三种职业模式本身的启动成本和风险结构粗看：当前更稳的是先上班，次选自由职业，创业放到后一阶段。"
                "先借平台把结果、信用和方法沉淀出来，再决定要不要重仓创业，会更顺。"
            )
        if option_set == {"上班", "自由职业", "自己接项目"}:
            return (
                "如果先不拉命盘，只按这三条路径本身的启动成本和风险结构粗看：当前更稳的是先上班，次选自由职业，自己接项目放到后一阶段。"
                "先借平台把结果、信用和方法沉淀出来，再把独立接活放大，通常比一上来就自己扛获客、成交、交付和回款更稳。"
            )
        if option_set == {"前端对接", "中间统筹", "后端执行"}:
            return (
                "如果先不拉命盘，只按这三种工作位势的结构粗看：当前主推荐中间统筹，次选前端对接，后端执行更适合放在支撑位。"
                "你这类问法更像是在找长期发力位，不是问短时补位，所以更顺的是先把提炼、串联、对齐资源和推进节奏放到前面。"
            )
        if option_set == {"内容IP", "操盘交付"}:
            return (
                "如果先不拉命盘，只按这两条路径的阶段性结构粗看：现阶段主推荐内容IP，操盘交付更适合先做补充线。"
                "内容IP更容易先沉淀你的方法、辨识度和外部信任，操盘交付可以做，但太早压成唯一主线，常常会先被交付压力和边界问题拖住。"
            )
        if option_set == {"组织里冲", "个人输出品牌"}:
            return (
                "如果先不拉命盘，只按这两个方向本身的启动结构粗看：当前更稳的是先在组织里冲，个人输出品牌放在同步铺垫、后面放大。"
                "先借现有平台把位置、结果和外部信任做出来，再把个人方法论和表达沉淀成品牌，通常比一开始就脱离组织单独放大更顺。"
            )
        if option_set == {"销售", "咨询", "自己接项目"}:
            if any(token in question for token in ("回款", "边界", "关系拖死", "拖死", "哪条最稳", "最稳")):
                return (
                    "如果先不拉命盘，只按这三条路径本身的风险结构粗看：最稳的通常是咨询，销售次之，最容易前面有戏后面被回款、边界或关系拖住的是自己接项目。"
                    "独立接项目不是不能做，但至少要先把客户来源、回款节奏和交付边界练稳。"
                )
            return (
                "如果先不拉命盘，只按路径结构粗看：主推荐咨询，次选销售，自己接项目放到后一阶段。"
                "先用组织里的结果、客户反馈和方法论把基本盘磨出来，再决定要不要独立接项目，会更稳。"
            )
        return ""

    if all(option in combined_text for option in options) and any(token in combined_text for token in ("更适合", "次选", "放在后面", "第二阶段")):
        return ""

    if option_set == {"上班", "创业", "自由职业"}:
        scores = {option: 0 for option in options}
        if any(token in combined_text for token in ("职责清楚", "位置", "平台", "角色定位", "责任承担", "长期路径", "官禄宫", "被邀请")):
            scores["上班"] += 4
        if any(token in combined_text for token in ("公开成果", "专业表达", "对外表达", "看准系统问题", "解决问题", "方法")):
            scores["自由职业"] += 3
            scores["上班"] += 1
        if any(token in combined_text for token in ("业务结构", "资源整合", "收入绑定", "项目运作", "人脉网络")):
            scores["创业"] += 1
            scores["自由职业"] += 2
        if any(token in combined_text for token in ("边界问题", "分账", "不要当场拍板", "方向频繁切换", "持续培育力一般", "内耗")):
            scores["创业"] -= 3
        ranked = sorted(options, key=lambda option: scores.get(option, 0), reverse=True)
        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else ""
        if best == "上班":
            return (
                "综合几路盘面，共识更偏上班，其次可以往自由职业过渡，创业放在后面。"
                "更顺的路径是先在有平台、有角色边界的位置把可见成果、客户口碑和方法论做出来，再决定要不要单干。"
            )
        if best == "自由职业":
            return (
                "综合几路盘面，共识更偏自由职业，其次是上班，创业仍然不适合一上来就重仓。"
                "更顺的路径是先把个人方法、口碑和稳定邀约做出来，再放大独立接活的比例。"
            )
        return (
            "综合几路盘面，创业不是完全不能做，但它更像后置选项。"
            f"当前更稳的是先走{best}，{second or '另一条路径'}作为过渡，再决定要不要把创业拉到主线。"
        )

    if option_set == {"上班", "自由职业", "自己接项目"}:
        scores = {option: 0 for option in options}
        if any(token in combined_text for token in ("职责清楚", "位置", "平台", "角色定位", "责任承担", "长期路径", "官禄宫", "被邀请")):
            scores["上班"] += 4
        if any(token in combined_text for token in ("公开成果", "专业表达", "对外表达", "看准系统问题", "解决问题", "方法", "稳定邀约", "独立输出")):
            scores["自由职业"] += 3
            scores["上班"] += 1
        if any(token in combined_text for token in ("项目", "分账", "合作", "资源置换", "回款", "边界", "交付")):
            scores["自己接项目"] += 1
        if any(token in combined_text for token in ("分账", "边界问题", "被人分功", "回款拖延", "资源纠缠", "现金流")):
            scores["自己接项目"] -= 3
        ranked = sorted(options, key=lambda option: scores.get(option, 0), reverse=True)
        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else ""
        if best == "上班":
            return (
                "综合几路盘面，共识更偏上班，其次可以往自由职业过渡，自己接项目放在后面。"
                "更顺的路径是先在有平台、有角色边界的位置把可见成果、客户口碑和方法论做出来，再把独立接活的比例慢慢拉高。"
            )
        if best == "自由职业":
            return (
                "综合几路盘面，共识更偏自由职业，其次是上班，自己接项目仍然不适合一上来就压成主线。"
                "更顺的路径是先把个人方法、口碑和稳定邀约做出来，再决定要不要把项目制合作放大。"
            )
        return (
            "综合看自己接项目不是完全不能做，但它更像第二阶段。"
            f"当前更稳的是先走{best}，{second or '另一条路径'}作为过渡，再决定要不要把独立项目合作拉成主线。"
        )

    if option_set == {"销售", "咨询", "自己接项目"}:
        scores = {option: 0 for option in options}
        if any(token in combined_text for token in ("表达", "认知升级", "解法", "方法", "系统问题", "顾问", "判断力")):
            scores["咨询"] += 4
        if any(token in combined_text for token in ("公开成果", "关系经营", "业务结构", "收入绑定", "人脉网络", "外部认可")):
            scores["销售"] += 3
        if any(token in combined_text for token in ("项目", "分账", "合作", "资源置换", "回款", "边界")):
            scores["自己接项目"] += 1
        if any(token in combined_text for token in ("分账", "边界问题", "被人分功", "持续培育力一般", "回款拖延")):
            scores["自己接项目"] -= 2
        ranked = sorted(options, key=lambda option: scores.get(option, 0), reverse=True)
        best = ranked[0]
        second = ranked[1] if len(ranked) > 1 else ""
        if best == "咨询":
            return (
                "综合看共识更偏咨询，其次是销售，自己接项目放在后面。"
                "更适合把判断力、表达力和方案能力变成价值，不宜太早把回款、分账和交付都一个人扛。"
            )
        if best == "销售":
            return (
                "综合看销售更占优，咨询次之，自己接项目放在后面。"
                "你更适合先在对外沟通、关系经营和结果推进里放大优势，再决定是否转成完全独立接项目。"
            )
        return (
            "综合看自己接项目不是不能做，但更像第二阶段。"
            f"当前更适合先走{best}，{second or '另一条路径'}作为补充，再把独立接项目慢慢拉起来。"
        )

    if option_set == {"前端对接", "中间统筹", "后端执行"}:
        return (
            "综合看你更适合把中间统筹放在主位，前端对接放在前场，后端执行放在支撑位。"
            "也就是说，比起长期埋头死磕，你更适合做提炼需求、串联人和事、把节奏往前推的那类活。"
        )

    if option_set == {"前端对接", "后端执行"}:
        return (
            "如果只在这两个位子里二选一，当前更适合前端对接，后端执行更像补位能力。"
            "你更适合把信息讲清、把人和事串起来，而不是长期缩在后场纯扛执行。"
        )

    if option_set == {"内容IP", "操盘交付"}:
        return (
            "综合看现阶段更适合主推内容IP，操盘交付先作为补充线更稳。"
            "先把你的方法、风格和外部认知做出来，再承接操盘交付，会比一上来就被别人项目节奏牵着跑更顺。"
        )

    if option_set == {"组织里冲", "个人输出品牌"}:
        return (
            "综合看当前更适合先在组织里冲，把个人输出品牌放在同步铺垫、后面放大。"
            "更顺的路径是先借现有位置做出结果和可见度，再把方法、表达和外部信任沉淀成自己的品牌资产。"
        )

    return ""


def multi_priority_recommendation(question: str, answer_items: list[dict[str, Any]]) -> str:
    del answer_items
    if not any(token in question for token in ("排个序", "三个", "先换城市", "先换房", "先稳工作")):
        return ""
    if all(token in question for token in ("换城市", "换房", "稳工作")):
        return (
            "如果一定要把这三件事排顺序，当前更稳的是先稳工作，再换房，最后再换城市。"
            "先把工作主线和角色落点定住，居住层面的调整会更容易承接；直接先换城市，变量通常最大。"
        )
    return ""


def relationship_direct_recommendation(question: str) -> str:
    if not question_has_relationship_decision_context(question):
        return ""
    return (
        "如果只按当前这类关系题的结构先给直话：已经开始反复拉扯、明显偏消耗时，不建议继续硬磨。"
        "更稳的是先收缩投入、拉开一点节奏，看对方有没有主动修复、边界调整和现实动作；后面如果还是只有情绪消耗，没有实际推进，就该及时止损。"
    )


def work_style_direct_recommendation(question: str) -> str:
    if not question_has_work_style_decision_context(question):
        return ""
    return (
        "如果只按这类工作风格题的结构先给直话：你更像适合把整合和表达放在前面，深度执行放在支撑位。"
        "更顺的站位是先负责提炼、串联、对外说清楚，再把执行细节压到流程和节奏里，而不是长期把自己锁在纯埋头硬扛的位置。"
    )


def project_funding_direct_recommendation(question: str) -> str:
    if not question_has_project_funding_decision_context(question):
        return ""
    return (
        "如果只按现在这类项目题的结构先说直话：已经出现回款风险时，不建议继续加码，当前更稳的是先停新增投入、先收缩，"
        "再把回款路径、责任边界和止损线核清。只有回款节点、合同约束和现金流缓冲都更明白了，才适合小步验证，不适合情绪化硬扛。"
    )


def spiritual_boundary_direct_recommendation(question: str) -> str:
    system_mentions = detect_system_mentions(question)
    boundary_systems = {"daoist_arts", "kabbalah", "alchemy_and_hermeticism", "modern_esotericism"}
    if len(system_mentions & boundary_systems) < 2:
        return ""
    if not any(token in question for token in ("净化整理", "边界保护", "别乱碰", "停下来", "先做", "还是先")):
        return ""
    return (
        "如果只按这类多体系混问的结构先给直话：先停下来别乱碰，再做边界保护，净化整理放后面。"
        "先把高刺激、强暗示、强投射的实践收一收，等身心反应和生活秩序稳住，再决定要不要继续碰更重的内容。"
    )


def question_prefers_symbolic_follow_up_only(question: str) -> bool:
    system_mentions = detect_system_mentions(question)
    if "tarot" in system_mentions and not question_has_cards(question):
        return True
    if "physiognomy" in system_mentions and not question_has_physiognomy_description(question):
        return True
    return False


def question_prefers_explicit_system_verdict_only(question: str) -> bool:
    if question_is_explicit_onmyodo_direction_trip(question):
        return True
    return False


def question_level_direct_recommendation(question: str, tags: set[str] | None = None) -> str:
    resolved_tags = tags or infer_question_tags(question)
    if question_prefers_symbolic_follow_up_only(question) or question_prefers_explicit_system_verdict_only(question):
        return ""
    for note in (
        multi_priority_recommendation(question, []),
        career_choice_recommendation(question, [], resolved_tags),
        timing_choice_recommendation(question, [], resolved_tags),
        relationship_direct_recommendation(question),
        work_style_direct_recommendation(question),
        project_funding_direct_recommendation(question),
        spiritual_boundary_direct_recommendation(question),
    ):
        trimmed = trim_reply_text(note)
        if trimmed:
            return trimmed
    if "timing" in resolved_tags and any(token in question for token in ("要不要去", "见合作方", "见客户", "签合同", "签约", "上午去", "下午去")):
        return (
            "如果只按当前这类时机题的结构先给直话：更适合先约见、先试探、先把边界谈清，再推进正式拍板。"
            "真要二选一，通常也更偏能留回旋余地、方便先沟通再定案的那一档时段。"
        )
    if any(token in question for token in ("见投资人", "投资人")) and any(token in question for token in ("太急", "显得我太急", "显得很急")):
        return (
            "如果只按当前这类时机题的结构先给直话：可以见，但更适合先轻碰、先试探，不要一上来就把诉求摊满。"
            "你担心的不是错觉，这类局面最怕节奏过满；先留一点回旋和观察位，反而更像稳。"
        )
    return ""


def career_option_summary(
    question: str,
    preferred: str,
    secondary: str,
    caution: str = "",
) -> str:
    options = extract_career_option_candidates(question)
    if len(options) < 2:
        return ""
    fallback = next((item for item in options if item not in {preferred, secondary}), "")
    parts = [f"放到{cn_join(options, '、')}这几个选项里，当前更适合走{preferred}"]
    if secondary:
        parts.append(f"次选是{secondary}")
    if fallback:
        parts.append(f"{fallback}更适合放到后一阶段")
    summary = "，".join(parts) + "。"
    if caution:
        summary += caution
    return summary


def verdict_covers_facet(verdict: Any, facet: str) -> bool:
    text = trim_reply_text(verdict)
    if not text:
        return False
    return any(marker in text for marker in FACET_RESULT_MARKERS.get(facet, ()))


def best_facet_segment(text: Any, facet: str) -> str:
    markers = FACET_RESULT_MARKERS.get(facet, ())
    if not markers:
        return ""
    best = ""
    best_score = 0
    for segment in split_insight_segments(text):
        hits = sum(1 for marker in markers if marker in segment)
        if not hits:
            continue
        score = hits * 4 + min(len(segment) // 24, 3)
        if score > best_score:
            best = segment
            best_score = score
    return best


def ranked_career_coverage_present(question: str, texts: list[str]) -> bool:
    options = extract_career_option_candidates(question)
    if len(options) < 2:
        return False
    ranking_markers = ("更适合", "主推荐", "次推荐", "不推荐", "放在后面", "后一阶段", "更稳", "主推", "次选", "先", "再")
    cleaned = [trim_reply_text(text) for text in texts if trim_reply_text(text)]
    if not cleaned:
        return False
    for text in cleaned:
        if all(option in text for option in options) and any(marker in text for marker in ranking_markers):
            return True
    combined = " ".join(cleaned)
    return all(option in combined for option in options) and any(marker in combined for marker in ranking_markers)


def direct_note_semantically_covered(
    question: str,
    note: str,
    synthesis: str,
    answer_items: list[dict[str, Any]],
) -> bool:
    trimmed_note = trim_reply_text(note)
    if not trimmed_note:
        return False
    source_texts = [trim_reply_text(synthesis)] + [
        trim_reply_text(item.get("verdict") or item.get("answer"))
        for item in answer_items
    ]
    if any(trimmed_note and trimmed_note in text for text in source_texts if text):
        return True
    if "如果先不拉命盘" in trimmed_note and ranked_career_coverage_present(question, source_texts):
        return True
    return False


def enrich_synthesis_with_requested_facets(
    question: str,
    synthesis: str,
    answer_items: list[dict[str, Any]],
    tags: set[str],
) -> str:
    explicit_systems = detect_system_mentions(question)
    requested = question_requested_facets(question)
    base_synthesis = synthesis
    synthesis_text = trim_reply_text(base_synthesis)
    fallback_direct_note = trim_reply_text(question_level_direct_recommendation(question, tags))
    priority_note = trim_reply_text(multi_priority_recommendation(question, answer_items))
    career_note = trim_reply_text(career_choice_recommendation(question, answer_items, tags))
    timing_note = trim_reply_text(timing_choice_recommendation(question, answer_items, tags))
    substantive_items = [
        item
        for item in answer_items
        if item.get("verdict_quality") == "conclusion"
        and trim_reply_text(item.get("verdict") or item.get("answer"))
    ]
    substantive_keys = {str(item.get("key") or "") for item in substantive_items}
    if "tarot" in explicit_systems and "tarot" in substantive_keys:
        fallback_direct_note = ""
    if fallback_direct_note and "如果先不拉命盘" in fallback_direct_note and any((priority_note, career_note, timing_note)):
        fallback_direct_note = ""
    if fallback_direct_note and direct_note_semantically_covered(question, fallback_direct_note, synthesis_text, answer_items):
        fallback_direct_note = ""
    if fallback_direct_note and not substantive_items:
        direct_notes = [fallback_direct_note]
    else:
        direct_notes = [
            note
            for note in [
                fallback_direct_note,
                priority_note,
                career_note,
                timing_note,
            ]
            if note
        ]
    lead_note = next((note for note in direct_notes if note), "")
    supporting_markers = (
        "这一路已经给出可参考的计算结果",
        "目前更适合作为辅助线索",
        "当前还没有进入可直接起算",
        "本轮已经完成部分本地计算",
        "当前还没有形成可直接交付",
    )
    if lead_note and lead_note not in synthesis_text and (
        not synthesis_text or any(marker in synthesis_text for marker in supporting_markers)
    ):
        base_synthesis = lead_note if not synthesis_text else f"{lead_note} {base_synthesis}"
        synthesis_text = trim_reply_text(base_synthesis)
    for note in direct_notes:
        if note and note not in synthesis_text:
            base_synthesis = note if not synthesis_text else f"{base_synthesis.rstrip('。；; ')}。{note}"
            synthesis_text = trim_reply_text(base_synthesis)
    if not requested or not answer_items:
        return base_synthesis

    notes: list[str] = []
    for facet in FACET_ORDER:
        if facet not in requested or verdict_covers_facet(synthesis_text, facet):
            continue
        best_note = ""
        best_score = -1
        for item in answer_items:
            source_text = trim_reply_text(item.get("verdict") or item.get("answer"))
            if not source_text:
                continue
            segment = best_facet_segment(source_text, facet)
            if not segment:
                continue
            score = top_system_priority(str(item.get("key") or ""), question, tags, source_text)
            score += sum(1 for marker in FACET_RESULT_MARKERS.get(facet, ()) if marker in segment) * 5
            if score > best_score:
                best_note = segment
                best_score = score
        if best_note and best_note not in synthesis_text and all(best_note not in note for note in notes):
            notes.append(f"{FACET_LABELS.get(facet, facet)}：{best_note}")
        if len(notes) >= 4:
            break

    if not notes:
        return base_synthesis
    return f"{base_synthesis.rstrip('。；; ')} 分开看，{'；'.join(notes)}。"


PLACEHOLDER_RESULT_MARKERS = (
    "当前只能从资料包层面给方向",
    "还没有进入可落地的本地实算",
    "已完成本地计算，但当前版本还没有产出更细的直断语句",
    "当前仅给资料层判断",
    "暂无最终答案",
)

STRUCTURAL_RESULT_MARKERS = (
    "本卦为",
    "变卦为",
    "体卦为",
    "用卦为",
    "命宫主星",
    "日曜落在",
    "命宫落在",
    "人类图显示你是",
    "西洋占星看",
    "七政四余看",
    "紫微斗数看",
)

CONCLUSION_RESULT_MARKERS = (
    "能成",
    "难成",
    "可成",
    "不利",
    "有利",
    "偏吉",
    "可用",
    "谨慎",
    "阻力",
    "先难后易",
    "先有势头",
    "仍有可推进空间",
    "宜",
    "不宜",
    "适合",
    "不适合",
    "更像是在调整路径",
    "先压实风险",
    "不是直接一锤定音",
    "性格",
    "行动风格",
    "重点落在",
    "适配度",
    "权威为",
    "主导第",
    "主轴",
    "偏向",
    "可以走",
    "能推进",
    "有成的空间",
    "不是推不动",
    "更适合",
    "不算最好",
    "偏不利",
    "可继续",
    "当前更稳的使用方式",
    "整体不是",
    "主轴更落在",
)


def verdict_quality(verdict: Any) -> str:
    text = trim_reply_text(verdict)
    if not text:
        return "empty"
    if any(marker in text for marker in PLACEHOLDER_RESULT_MARKERS):
        return "placeholder"
    if any(
        marker in text
        for marker in (
            "Local ",
            "Sun in ",
            "Moon in ",
            "Ascendant",
            "Lagna is",
            "Chart resolves to",
            "Transmission runs through",
            "Facing sector is",
            "Name ",
            "Observation cluster",
            "Modern-esotericism classification",
            "Daoist-arts classification",
        )
    ):
        return "placeholder"
    if any(marker in text for marker in ("紫微看", "紫微斗数看", "命宫主星", "财帛宫主星", "官禄宫主星", "夫妻宫")):
        return "conclusion"
    has_structure = any(marker in text for marker in STRUCTURAL_RESULT_MARKERS)
    has_conclusion = any(marker in text for marker in CONCLUSION_RESULT_MARKERS)
    if has_structure and not has_conclusion:
        return "structural"
    return "conclusion"


def has_substantive_verdict(verdict: Any) -> bool:
    return verdict_quality(verdict) == "conclusion"


def translate_western_sign(value: str) -> str:
    mapping = {
        "Aries": "白羊座",
        "Taurus": "金牛座",
        "Gemini": "双子座",
        "Cancer": "巨蟹座",
        "Leo": "狮子座",
        "Virgo": "处女座",
        "Libra": "天秤座",
        "Scorpio": "天蝎座",
        "Sagittarius": "射手座",
        "Capricorn": "摩羯座",
        "Aquarius": "水瓶座",
        "Pisces": "双鱼座",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_planet_name(value: str) -> str:
    mapping = {
        "Sun": "太阳",
        "Moon": "月亮",
        "Mercury": "水星",
        "Venus": "金星",
        "Mars": "火星",
        "Jupiter": "木星",
        "Saturn": "土星",
        "Uranus": "天王星",
        "Neptune": "海王星",
        "Pluto": "冥王星",
        "Luohou": "罗喉",
        "Jidu": "计都",
        "Yuebo": "月孛",
        "Ziqi": "紫气",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_trigram(value: str) -> str:
    mapping = {
        "Qian": "乾",
        "Dui": "兑",
        "Li": "离",
        "Zhen": "震",
        "Xun": "巽",
        "Kan": "坎",
        "Gen": "艮",
        "Kun": "坤",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_nakshatra(value: str) -> str:
    mapping = {
        "Ashwini": "阿湿毗尼",
        "Bharani": "婆罗尼",
        "Krittika": "计都",
        "Rohini": "毕宿",
        "Mrigashira": "觜宿",
        "Ardra": "参宿",
        "Punarvasu": "井宿",
        "Pushya": "鬼宿",
        "Ashlesha": "柳宿",
        "Magha": "星宿",
        "Purva Phalguni": "张宿",
        "Uttara Phalguni": "翼宿",
        "Hasta": "轸宿",
        "Chitra": "角宿",
        "Swati": "亢宿",
        "Vishakha": "氐宿",
        "Anuradha": "房宿",
        "Jyeshtha": "心宿",
        "Mula": "尾宿",
        "Purva Ashadha": "箕宿",
        "Uttara Ashadha": "斗宿",
        "Shravana": "牛宿",
        "Dhanishta": "女宿",
        "Shatabhisha": "虚宿",
        "Purva Bhadrapada": "危宿",
        "Uttara Bhadrapada": "室宿",
        "Revati": "壁宿",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_tree_pillar(value: str) -> str:
    return {
        "Middle": "中柱",
        "Left": "左柱",
        "Right": "右柱",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_modern_esoteric_family(value: str) -> str:
    return {
        "identity-framework": "自我理解框架",
        "energy-healing": "能量疗愈流",
        "manifestation": "显化流",
        "manifestation-commerce": "显化变现流",
        "energy-map": "能量地图框架",
        "unspecified-modern-mix": "未明现代混合流",
        "general-symbolic": "一般象征框架",
        "ritual-practice": "仪式实践框架",
        "divinatory-message": "讯息占读框架",
        "prosperity-technique": "丰盛显化技巧",
        "healing-claim": "疗愈宣称框架",
        "psychological": "心理整理流",
        "wellness": "身心疗愈流",
        "religious": "灵修宗教流",
        "commercial": "商业包装流",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_daoist_family(value: str) -> str:
    return {
        "cleansing-exorcistic": "净化与禳解类",
        "protective-talismans": "护持与符箓类",
        "liturgical-ritual": "科仪法事类",
        "inner-cultivation": "内炼修持类",
        "high-risk ritual": "高风险仪轨类",
        "symbolic-study": "结构理解类",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_daoist_lineage(value: str) -> str:
    return {
        "zhengyi": "正一",
        "quanzhen": "全真",
        "maoshan": "茅山",
        "lingbao": "灵宝",
        "lvshan": "闾山",
        "qingwei": "清微",
        "shenxiao": "神霄",
        "unspecified": "未明",
    }.get(str(value or "").strip().lower(), str(value or "").strip())


def translate_physiognomy_axis(value: str) -> str:
    return {
        "vitality and immediate energy": "精神头与当下行动力",
        "social readability and relational warmth": "社交可读性与关系亲和力",
        "emotional steadiness and expressiveness": "情绪稳定度与表达感",
        "material steadiness and structure": "现实稳定度与结构感",
        "material anchoring and practical resources": "现实稳定度与资源承载感",
        "execution and follow-through": "执行与跟进能力",
        "discipline and self-ordering": "自我约束与秩序感",
        "foresight and long-range framing": "前瞻性与长线视角",
        "stability and load-bearing capacity": "稳定度与承压能力",
        "expression and outward presence": "表达力与外在显现",
        "will and directional force": "意志感与推进力",
        "willpower and persistence": "意志力与持续性",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_kabbalah_title(value: str) -> str:
    normalized = str(value or "").strip()
    return {
        "Beauty": "美",
        "Foundation": "基底",
        "Kingdom": "国度",
        "Wisdom": "智慧",
        "Understanding": "理解",
        "beauty": "美",
        "foundation": "基底",
        "kingdom": "国度",
        "wisdom": "智慧",
        "understanding": "理解",
    }.get(normalized, normalized)


def translate_kabbalah_keyword(value: str) -> str:
    return {
        "harmony": "调和",
        "integration": "整合",
        "center": "中心",
        "radiance": "光辉",
        "balance": "平衡",
        "beauty": "美感",
        "heart": "核心",
        "vision": "愿景",
        "substrate": "底层承载",
        "linkage": "连接",
        "imagination": "想象",
        "embodiment": "落地承载",
        "execution": "执行",
        "manifestation": "显化",
        "analysis": "分析",
        "language": "语言",
        "systems": "系统化",
    }.get(str(value or "").strip().lower(), str(value or "").strip())


def translate_alchemy_term(value: str) -> str:
    return {
        "nigredo": "黑化阶段",
        "albedo": "白化阶段",
        "rubedo": "赤化阶段",
        "citrinitas": "黄化阶段",
        "mercury": "汞性原则",
        "salt": "盐性原则",
        "sulfur": "硫性原则",
        "coagulation": "凝结",
        "calcination": "煅烧",
        "dissolution": "溶解",
        "separation": "分离",
        "conjunction": "结合",
        "fermentation": "发酵",
        "distillation": "蒸馏",
        "ouroboros": "衔尾蛇",
        "uroboros": "衔尾蛇",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_usable_scope(value: str) -> str:
    return {
        "reflective and journaling use": "反思记录、日记整理这类低风险用法",
        "symbolic personal use": "个人象征化使用",
        "symbolic and aesthetic use": "象征体验与审美化使用",
        "motivational framing only": "作为动机框架使用",
        "self-observation with boundaries": "带边界的自我观察",
        "cultural framing and risk warning only": "文化理解与风险提醒",
    }.get(str(value or "").strip(), str(value or "").strip())


def translate_hd_type(value: str) -> str:
    mapping = {
        "Manifestor": "显化者",
        "Generator": "生产者",
        "Manifesting Generator": "显示生产者",
        "Projector": "投射者",
        "Reflector": "反映者",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_hd_authority(value: str) -> str:
    mapping = {
        "Emotional Authority": "情绪权威",
        "Sacral Authority": "骶骨权威",
        "Splenic Authority": "脾权威",
        "Ego Authority": "意志权威",
        "Self-Projected Authority": "自我投射权威",
        "Mental Authority": "心智权威",
        "Lunar Authority": "月亮权威",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


def translate_hd_center(value: str) -> str:
    mapping = {
        "Head": "头顶",
        "Ajna": "阿基那",
        "Throat": "喉",
        "G": "自我认同",
        "G Center": "自我认同",
        "Heart": "意志",
        "Ego": "意志",
        "Sacral": "骶骨",
        "Spleen": "脾",
        "Solar Plexus": "情绪",
        "Root": "根部",
    }
    return mapping.get(str(value or "").strip(), str(value or "").strip())


HEXAGRAM_NAME_TRANSLATIONS = {
    "Force": "乾",
    "Field": "坤",
    "Sprouting": "屯",
    "Enveloping": "蒙",
    "Attending": "需",
    "Arguing": "讼",
    "Leading": "师",
    "Grouping": "比",
    "Small Accumulating": "小畜",
    "Treading": "履",
    "Pervading": "泰",
    "Obstruction": "否",
    "Concording People": "同人",
    "Great Possessing": "大有",
    "Humbling": "谦",
    "Providing For": "豫",
    "Following": "随",
    "Correcting": "蛊",
    "Nearing": "临",
    "Viewing": "观",
    "Gnawing Bite": "噬嗑",
    "Adorning": "贲",
    "Stripping": "剥",
    "Returning": "复",
    "Without Embroiling": "无妄",
    "Great Accumulating": "大畜",
    "Swallowing": "颐",
    "Great Exceeding": "大过",
    "Gorge": "坎",
    "Radiance": "离",
    "Conjoining": "咸",
    "Persevering": "恒",
    "Retiring": "遁",
    "Great Invigorating": "大壮",
    "Prospering": "晋",
    "Brightness Hiding": "明夷",
    "Dwelling People": "家人",
    "Polarising": "睽",
    "Limping": "蹇",
    "Taking Apart": "解",
    "Diminishing": "损",
    "Augmenting": "益",
    "Parting": "夬",
    "Coupling": "姤",
    "Clustering": "萃",
    "Ascending": "升",
    "Confining": "困",
    "Welling": "井",
    "Skinning": "革",
    "Holding": "鼎",
    "Shake": "震",
    "Bound": "艮",
    "Infiltrating": "渐",
    "Converting The Maiden": "归妹",
    "Abounding": "丰",
    "Sojourning": "旅",
    "Ground": "巽",
    "Open": "兑",
    "Dispersing": "涣",
    "Articulating": "节",
    "Center Confirming": "中孚",
    "Small Exceeding": "小过",
    "Already Fording": "既济",
    "Not Yet Fording": "未济",
}


def translate_hexagram_name(value: str) -> str:
    return HEXAGRAM_NAME_TRANSLATIONS.get(str(value or "").strip(), str(value or "").strip())


def translate_signal_text(text: str) -> str:
    value = normalize_reply_text(text)
    replacements = {
        "Base hexagram": "本卦",
        "base hexagram": "本卦",
        "Changed hexagram": "变卦",
        "changed hexagram": "变卦",
        "Sun is in": "太阳落在",
        "Moon is in": "月亮落在",
        "Ascendant is": "上升点是",
        "Base hexagram resolves to": "本卦落在",
        "changed hexagram resolves to": "变卦落在",
        "Question time resolves to": "起问时间落在",
        "Transmission runs through": "三传走向为",
        "Using a datetime parsed from the question chart.": "本轮用问题里给出的时间直接起盘。",
        "Using a current ask-time fallback chart.": "本轮没有明确起问时点，已回退到当前提问时刻起盘。",
        "Using a event datetime chart.": "本轮按事件时间起盘。",
        "Using a explicit divination time chart.": "本轮按明确起问时间起盘。",
        "Using a structured divination time chart.": "本轮按结构化起问时间起盘。",
        "Using a date plus time fields chart.": "本轮按拆分日期与时间字段起盘。",
        "Chart resolves to": "盘局落为",
        "Facing sector is": "朝向落在",
        "Property is classified into": "房屋朝向归入",
        "Occupant kua is": "命卦为",
        "Pinyin profile": "拼音特征",
        "Seven governors center on": "七政主轴落在",
        "Seven governors emphasize": "七政重点星曜落在",
        "Seven-governor element emphasis": "七政五行侧重",
        "Seven-governor mode emphasis": "七政性质侧重",
        "Luohou is placed in house": "罗喉落在第",
        "Jidu is placed in house": "计都落在第",
        "Yuebo proxy falls in house": "月孛代理点落在第",
        "Ziqi proxy falls in house": "紫气代理点落在第",
        "Tightest governor aspect is": "最紧的主星相位是",
        "Source family resolves to": "来源流派落在",
        "Concept family resolves to": "概念流派落在",
        "Domain split weights:": "领域权重分布：",
        "Usable scope under the local rule set:": "当前规则下更稳的使用范围是：",
        "Cultural context supplied:": "给出的文化语境是：",
        "Strategy is Wait for the Invitation and definition is Split Definition.": "策略是等待邀请，定义为分裂定义。",
        "Observation cluster centers on": "观察聚焦于",
        "The extracted features currently supports that axis under the local physiognomy rule set.": "当前提取到的特征整体在支持这一主轴。",
        "The extracted features currently complicates that axis under the local physiognomy rule set.": "当前提取到的特征会让这一主轴更复杂，需要保留弹性判断。",
        "Sun in": "太阳落在",
        "Moon in": "月亮落在",
        "Ascendant": "上升",
        "Lagna is": "上升点落在",
        "Day stem is": "日干为",
        "Direction resolves to": "方位落在",
        "Element relation:": "五行关系为",
        "Alchemy focus resolves to": "炼金术主轴落在",
        "Transformation stage resolves to": "转化阶段落在",
        "Daoist-arts classification resolves to": "道术归类落在",
        "Practice family resolves to": "实践类别落在",
        "Modern-esotericism classification resolves to": "现代神秘学归类落在",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)
    for source, target in HEXAGRAM_NAME_TRANSLATIONS.items():
        value = value.replace(source, target)
    value = re.sub(r"\bJupiter\b", "木星", value)
    value = re.sub(r"\bSaturn\b", "土星", value)
    value = re.sub(r"\bMars\b", "火星", value)
    value = re.sub(r"\bVenus\b", "金星", value)
    value = re.sub(r"\bMercury\b", "水星", value)
    value = re.sub(r"\bMoon\b", "月亮", value)
    value = re.sub(r"\bSun\b", "太阳", value)
    value = re.sub(r"\bLuohou\b", "罗喉", value)
    value = re.sub(r"\bJidu\b", "计都", value)
    value = re.sub(r"\bYuebo\b", "月孛", value)
    value = re.sub(r"\bZiqi\b", "紫气", value)
    value = re.sub(r"\bmale-group\b", "东四命组", value)
    value = re.sub(r"\bfemale-group\b", "西四命组", value)
    value = re.sub(r"\bEast-group\b", "东四命组", value)
    value = re.sub(r"\bWest-group\b", "西四命组", value)
    return value


def translate_tarot_card_name(value: str) -> str:
    mapping = {
        "The Fool": "愚者",
        "The Magician": "魔术师",
        "The High Priestess": "女祭司",
        "The Empress": "女皇",
        "The Emperor": "皇帝",
        "The Hierophant": "教皇",
        "The Lovers": "恋人",
        "The Chariot": "战车",
        "Strength": "力量",
        "The Hermit": "隐士",
        "Wheel Of Fortune": "命运之轮",
        "Justice": "正义",
        "The Hanged Man": "倒吊人",
        "Death": "死神",
        "Temperance": "节制",
        "The Devil": "恶魔",
        "The Tower": "高塔",
        "The Star": "星星",
        "The Moon": "月亮",
        "The Sun": "太阳",
        "Judgement": "审判",
        "The World": "世界",
        "Ace Of Wands": "权杖首牌",
        "Two Of Wands": "权杖二",
        "Three Of Wands": "权杖三",
        "Four Of Wands": "权杖四",
        "Five Of Wands": "权杖五",
        "Six Of Wands": "权杖六",
        "Seven Of Wands": "权杖七",
        "Eight Of Wands": "权杖八",
        "Nine Of Wands": "权杖九",
        "Ten Of Wands": "权杖十",
        "Page Of Wands": "权杖侍从",
        "Knight Of Wands": "权杖骑士",
        "Queen Of Wands": "权杖皇后",
        "King Of Wands": "权杖国王",
        "Ace Of Cups": "圣杯首牌",
        "Two Of Cups": "圣杯二",
        "Three Of Cups": "圣杯三",
        "Four Of Cups": "圣杯四",
        "Five Of Cups": "圣杯五",
        "Six Of Cups": "圣杯六",
        "Seven Of Cups": "圣杯七",
        "Eight Of Cups": "圣杯八",
        "Nine Of Cups": "圣杯九",
        "Ten Of Cups": "圣杯十",
        "Page Of Cups": "圣杯侍从",
        "Knight Of Cups": "圣杯骑士",
        "Queen Of Cups": "圣杯皇后",
        "King Of Cups": "圣杯国王",
        "Ace Of Swords": "宝剑首牌",
        "Two Of Swords": "宝剑二",
        "Three Of Swords": "宝剑三",
        "Four Of Swords": "宝剑四",
        "Five Of Swords": "宝剑五",
        "Six Of Swords": "宝剑六",
        "Seven Of Swords": "宝剑七",
        "Eight Of Swords": "宝剑八",
        "Nine Of Swords": "宝剑九",
        "Ten Of Swords": "宝剑十",
        "Page Of Swords": "宝剑侍从",
        "Knight Of Swords": "宝剑骑士",
        "Queen Of Swords": "宝剑皇后",
        "King Of Swords": "宝剑国王",
        "Ace Of Pentacles": "星币首牌",
        "Two Of Pentacles": "星币二",
        "Three Of Pentacles": "星币三",
        "Four Of Pentacles": "星币四",
        "Five Of Pentacles": "星币五",
        "Six Of Pentacles": "星币六",
        "Seven Of Pentacles": "星币七",
        "Eight Of Pentacles": "星币八",
        "Nine Of Pentacles": "星币九",
        "Ten Of Pentacles": "星币十",
        "Page Of Pentacles": "星币侍从",
        "Knight Of Pentacles": "星币骑士",
        "Queen Of Pentacles": "星币皇后",
        "King Of Pentacles": "星币国王",
    }
    text = str(value or "").strip()
    return mapping.get(text, text)


NAME_STYLE_TAG_LABELS = {
    "bookish": "书卷",
    "classic": "古典",
    "bright": "明朗",
    "gentle": "温柔",
    "graceful": "大气",
}


def translate_name_style_tag(value: str) -> str:
    text = str(value or "").strip()
    return NAME_STYLE_TAG_LABELS.get(text, text)


def build_naming_profile_payload(question: str, result: dict[str, Any]) -> dict[str, Any]:
    if not result or not result.get("generated_candidates"):
        return {}

    used = result.get("used_inputs") or {}
    birth_info = str(used.get("birth_info") or "").strip()
    naming_profile: dict[str, Any] = {
        "surname": str(used.get("surname") or "").strip(),
        "purpose": str(used.get("purpose") or "").strip(),
        "top_candidates": [],
    }

    for item in (result.get("generated_candidates") or [])[:10]:
        supporting_signals = []
        for signal_text in (item.get("supporting_signals") or []):
            cleaned_signal = trim_reply_text(signal_text or "")
            if cleaned_signal:
                supporting_signals.append(cleaned_signal)
        naming_profile["top_candidates"].append(
            {
                "name": str(item.get("name") or "").strip(),
                "meaning": trim_reply_text(item.get("meaning") or ""),
                "source_title": trim_reply_text(item.get("source_title") or ""),
                "source_quote": trim_reply_text(item.get("source_quote") or ""),
                "style_tags": [translate_name_style_tag(str(tag)) for tag in (item.get("style_tags") or []) if str(tag).strip()],
                "preferred_elements": list(item.get("preferred_elements") or []),
                "character_elements": list(item.get("character_elements") or []),
                "bridge_number": item.get("expression_bridge_number"),
                "score": int(item.get("score") or 0),
                "confidence": str(item.get("confidence") or "").strip(),
                "primary_finding": trim_reply_text(item.get("primary_finding") or ""),
                "supporting_signals": supporting_signals,
                "why_selected": trim_reply_text(item.get("why_selected") or ""),
                "birth_support_note": trim_reply_text(item.get("birth_support_note") or ""),
            }
        )

    if not birth_info:
        return naming_profile

    try:
        parsed_birth = parse_birth_details(birth_info)
        parsed_question = parse_birth_details(question)
        gender_text = str(used.get("gender") or parsed_birth.gender or parsed_question.gender or "").strip()
        birth_location_text = str(
            used.get("birth_location") or parsed_birth.birth_location or parsed_question.birth_location or ""
        ).strip()
        bazi_payload: dict[str, Any] = {"birth_datetime": birth_info}
        if gender_text:
            bazi_payload["gender"] = gender_text
        if birth_location_text:
            bazi_payload["birth_location"] = birth_location_text

        bazi_result, status = calculate_system("bazi", bazi_payload)
        if status != 200 or bazi_result.get("error"):
            return naming_profile

        input_info = bazi_result.get("input") or {}
        lunar_date = bazi_result.get("lunar_date") or {}
        summary = bazi_result.get("summary") or {}
        pillars = bazi_result.get("pillars") or {}
        ten_gods = bazi_result.get("ten_gods") or {}
        hidden_ten_gods = bazi_result.get("hidden_ten_gods") or {}
        five_counts = bazi_result.get("five_element_counts") or {}
        day_master = bazi_result.get("day_master") or {}

        element_order = ["木", "火", "土", "金", "水"]
        five_element_counts = []
        for key in element_order:
            if key in five_counts:
                five_element_counts.append({"label": key, "value": five_counts.get(key)})
        for key, value in five_counts.items():
            if key not in element_order:
                five_element_counts.append({"label": key, "value": value})

        pillar_rows = []
        for key, label in (("year", "年柱"), ("month", "月柱"), ("day", "日柱"), ("hour", "时柱")):
            pillar = pillars.get(key) or {}
            pillar_rows.append(
                {
                    "key": key,
                    "label": label,
                    "pillar": trim_reply_text(str(pillar.get("text") or "")),
                    "stem": trim_reply_text(str(pillar.get("stem") or "")),
                    "branch": trim_reply_text(str(pillar.get("branch") or "")),
                    "element": trim_reply_text(str(pillar.get("element") or "")),
                    "polarity": trim_reply_text(str(pillar.get("polarity") or "")),
                    "ten_god": trim_reply_text(str(ten_gods.get(key) or "")),
                    "hidden_stems": [
                        trim_reply_text(str(hidden))
                        for hidden in (pillar.get("hidden_stems") or [])
                        if trim_reply_text(str(hidden))
                    ],
                    "hidden_ten_gods": [
                        trim_reply_text(str(item.get("ten_god") or ""))
                        for item in (hidden_ten_gods.get(key) or [])
                        if trim_reply_text(str(item.get("ten_god") or ""))
                    ],
                }
            )

        naming_profile["birth_info"] = {
            "solar_datetime": trim_reply_text(str(input_info.get("birth_datetime") or birth_info)),
            "lunar_text": trim_reply_text(str(lunar_date.get("text") or "")),
            "gender": trim_reply_text(str(input_info.get("gender") or gender_text or "")),
            "birth_location": trim_reply_text(
                str(
                    input_info.get("birth_location")
                    or input_info.get("parsed_birth_location")
                    or birth_location_text
                    or ""
                )
            ),
            "season": trim_reply_text(str(bazi_result.get("season") or "")),
            "calendar": trim_reply_text(str(input_info.get("calendar_source") or input_info.get("calendar") or "")),
        }
        naming_profile["bazi_summary"] = {
            "day_pillar": trim_reply_text(str(((pillars.get("day") or {}).get("text")) or "")),
            "day_master": trim_reply_text(str(day_master.get("stem") or "")),
            "day_master_element": trim_reply_text(str(day_master.get("element") or "")),
            "day_master_polarity": trim_reply_text(str(day_master.get("polarity") or "")),
            "five_elements": " / ".join(
                f"{item['label']}{item['value']}"
                for item in five_element_counts
                if item.get("value") not in (None, "")
            ),
            "five_element_counts": five_element_counts,
            "strongest_elements": list(summary.get("strongest_elements") or []),
            "weakest_elements": list(summary.get("weakest_elements") or []),
            "season": trim_reply_text(str(bazi_result.get("season") or "")),
            "note": trim_reply_text(summary.get("note") or ""),
            "pillars": pillar_rows,
        }
    except Exception:
        pass

    return naming_profile


def translate_risk_text(text: str) -> str:
    value = normalize_reply_text(text)
    mapping = {
        "Local Yijing output computes the hexagram structure directly, but interpretive text is intentionally constrained": "易经部分已经完成本地卦象结构计算，但解释文本仍偏保守。",
        "No line-text corpus is bundled yet, so this result emphasizes structure over commentary": "当前未内置完整爻辞语料，因此结果更偏结构判断，不偏长篇发挥。",
        "This implemented branch is a meihua-style body/use engine built on real hexagram calculation": "六爻与梅花部分当前走的是体用象数实算分支。",
        "Full najia, six-kinship, and six-spirit tables are not bundled yet, so this does not claim to be a complete orthodox six-yao reading": "当前未内置完整纳甲、六亲、六神表，所以还不是全套传统六爻断法。",
        "This local western astrology engine computes natal placements, houses, moon phase, and major aspects offline.": "西洋占星已完成本地本命盘、宫位、月相与主要相位计算。",
        "It does not yet include transits, progressions, synastry, or a long-form interpretive layer.": "当前还未加入行运、推运、合盘与长篇诠释层。",
        "This local qimen_dunjia engine uses taibu-core and its taobi-backed charting implementation.": "奇门遁甲已接入本地盘局计算引擎。",
        "Pan style, fixed-ju method, and zhi-fu lodging rules still vary across lineages; this engine keeps the method explicit in the output.": "盘式、定局法与值符飞泊规则在不同流派间仍有差异，本版会把所用方法明示出来。",
        "The current output focuses on chart structure and active formations; school-specific judgement rhetoric should still be treated cautiously.": "当前输出偏盘面结构与活跃宫位，门派化断语仍需谨慎使用。",
        "This local liu_ren engine uses taibu-core and its liuren-ts-lib-backed chart generation.": "大六壬已接入本地课式计算引擎。",
        "Transmission extraction and ke-ti layering are real local outputs, but lineage-specific yong-shen and final judgement methods still vary significantly.": "三传与课体已经本地算出，但具体取用神和门派断法仍存在差异。",
        "No explicit divination time was supplied, so the engine fell back to the current ask time.": "你没有给明确起问时间，本轮已回退到当前提问时刻起盘。",
        "This local qizheng_siyu engine computes the seven governors from astronomical positions and uses node/apogee proxies for the four remainders.": "七政四余已完成本地主星位置与四余代理点计算。",
        "Luohou and Jidu naming conventions differ across lineages; this build maps Luohou to the true south node and Jidu to the true north node following one common Chinese convention.": "罗喉与计都的命名在不同流派间有差异，本版按常见中文习惯完成映射。",
        "Yuebo is modeled from the lunar apogee proxy (true Lilith), and Ziqi is modeled as its opposite point; some schools define these hidden stars differently.": "月孛与紫气当前采用近地点/对冲代理方案，不同流派定义仍会不同。",
        "This local fengshui engine currently computes sector, Eight Mansions matching, and period bucket only.": "当前风水模块已完成朝向分区、八宅配向与运期层的本地计算。",
        "Without an accurate floor plan and room-level layout, the result should be treated as a directional screening layer rather than a full audit.": "在没有户型图与房间级布局前，结果应视为朝向粗筛，不是完整勘宅。",
        "Occupant kua matching was skipped because birth date and gender were not both available.": "由于缺少完整生日与性别，当前还没有进入命卦配向层。",
        "Build/occupancy year was not supplied, so period-based flying-star context is only approximate.": "由于没有建造或入住年份，当前运期飞星层只能做近似参考。",
        "This local name-studies engine evaluates structure, phonetics, purpose fit, and a pinyin-based numerology bridge.": "姓名学模块已完成字形结构、音律、用途适配与拼音桥接数的本地筛查。",
        "Traditional Kangxi stroke counts and full five-grid schools are not bundled yet, so this is not presented as a complete orthodox five-grid reading.": "当前未接入完整康熙笔画与五格全套体系，因此不把它包装成完整五格断法。",
        "Birth-info-based five-element compensation is currently a screening aid, not a full orthodox yong-shen naming method.": "出生信息相关的五行补偏目前只是辅助筛选，不是完整用神起名法。",
        "This local modern_esotericism engine distinguishes symbolic practice, psychological framing, commercial packaging, and high-risk overreach instead of treating them as one thing.": "现代神秘学模块会区分象征实践、心理整理、商业包装与高风险越界，不会混成一类。",
        "It should not replace therapy, medical care, legal advice, or financial judgement.": "它不能替代心理治疗、医疗、法律或财务判断。",
        "Contemporary esoteric scenes often blend spirituality, wellness, psychology, and monetization; the engine surfaces that mixture explicitly.": "当代神秘学场景常把灵性、疗愈、心理与变现混在一起，系统会把这层混合明确标出来。",
        "This local onmyodo engine currently evaluates calendrical polarity, element relation, and direction taboo layers.": "阴阳道模块当前已完成历法阴阳、五行关系与方位禁忌层的本地判断。",
        "It does not yet implement a complete historical rekichu, shikiban, or court-era ritual corpus.": "当前还未接入完整历注、式盘与宫廷时代仪轨语料。",
        "This local human design engine uses natalengine with historical timezone resolution from the resolved birth location.": "人类图模块当前使用本地盘引擎，并结合出生地解析历史时区来完成排图。",
        "Human Design is a modern synthetic system, so wording around variable, PHS, circuitry, and incarnation cross still varies across schools.": "人类图属于现代综合体系，关于变量、PHS、回路与人生十字的表述在不同学校之间仍会不同。",
        "This engine computes structural bodygraph outputs locally; it does not yet add transit overlays, relationship composites, or long-form coaching language.": "当前版本已完成结构化人类图输出，但还未加入行运叠加、关系合图与长篇教练式诠释。",
        "Birth location was resolved through a region-level fallback, so timezone and chart precision should be treated as approximate.": "出生地当前是按区域级回退解析的，因此时区与盘面精度应视为近似值。",
        "This local vedic astrology engine computes sidereal graha positions, lagna, nakshatra, and whole-sign house placement offline.": "印度占星已完成本地恒星黄道行星位置、上升、月宿与整宫制宫位计算。",
        "It does not yet include divisional charts, vimshottari dasha, shadbala, or transit timing.": "当前还未加入分盘、Vimshottari 大运、Shadbala 与行运定时层。",
        "This local ziwei_doushu engine uses the open-source iztro chart core to compute the 12 palaces, stars, and current cycle overlays.": "紫微斗数已接入本地命盘核心，可计算十二宫、星曜与当前周期叠层。",
        "Interpretation schools differ across lineages, so this version returns a structural chart reading first and keeps advanced school-specific judgement conservative.": "紫微不同流派的断法仍有差异，所以当前版本先给结构盘判断，进阶门派断语会更保守。",
        "This local date-selection engine ranks dates by calendrical structure, clash/harmony, and practical timing rules only.": "择日模块当前按历法结构、冲合关系与实用时机规则来排序候选日期。",
        "A full Huangli-style shensha layer is not bundled yet, so this result should be treated as a strong shortlist, not as a final oracle.": "当前还未接入完整黄历神煞层，因此结果更适合作强候选清单，不当作最终裁决。",
        "This local physiognomy engine reads text descriptions of observed features; it does not inspect pixels or infer hidden traits from an unseen face.": "面相模块当前只读你提供的外观描述，不会凭空从未见到的脸上推隐藏信息。",
        "Physiognomy is handled here as a non-deterministic symbolic observation system, not as a medical, legal, hiring, or investment decision tool.": "这里把面相当作象征观察系统，不作为医疗、法律、招聘或投资决策工具。",
        "Any strong claim should be cross-checked across multiple contexts instead of being treated as fixed destiny.": "任何强判断都应结合多个场景交叉验证，不应当成铁板钉钉的命数。",
        "This local kabbalah engine mixes structural Tree-of-Life correspondences with explicit source-stream labeling.": "卡巴拉模块当前把生命之树结构对应与来源流派标识一起展示。",
        "Jewish Kabbalah, Christian Cabala, and Hermetic Qabalah do not use one identical rulebook; the source stream is exposed rather than hidden.": "犹太卡巴拉、基督教卡巴拉与赫尔墨斯卡巴拉并不是同一本规则书，系统会把来源说清楚。",
        "Without a cited textual lineage, this engine should be treated as a structural reading layer rather than as a final doctrinal verdict.": "如果没有明确文本传承引用，这一路更适合看结构，不适合当成最终教义裁决。",
        "This local daoist_arts engine structures lineage, ritual components, and taboo boundaries; it does not authorize ordination-gated or dangerous procedures.": "道术模块会整理法脉、仪式部件与禁忌边界，但不会授权受戒门槛或危险操作。",
        "Religious practice, exorcistic work, healing claims, and coercive ritual should not be operationalized from dossier rules alone.": "宗教修法、驱邪、疗愈宣称与强制性仪轨都不能只靠资料规则直接落地执行。",
        "Where lineage is unclear, output should be treated as cultural mapping rather than as a reliable manual.": "法脉不清时，输出更适合作文化地图，不适合作操作手册。",
        "This local alchemy_and_hermeticism engine treats alchemical language as symbolic, philosophical, and process-oriented unless the user explicitly frames it as historical laboratory material.": "炼金术模块默认把术语当作象征、哲学与过程语言，而不是实操化学步骤。",
        "It should not be used as chemistry, toxicology, medical, or ingestion guidance.": "它不能当作化学、毒理、医疗或摄入指导。",
        "Different streams of alchemy, Hermeticism, Paracelsian medicine, and Jungian reinterpretation do not collapse into one rulebook; the chosen frame is exposed in the output.": "炼金、赫尔墨斯、帕拉塞尔苏斯医学与荣格化诠释并不是同一套规则，系统会把所用框架亮出来。",
        "This local tarot engine requires explicit drawn cards and will not fabricate random pulls.": "本地塔罗必须基于已经翻出的牌面，不会替你虚构抽牌结果。",
        "This local tarot engine requires explicit drawn cards and will not fabricate random pulls": "本地塔罗必须基于已经翻出的牌面，不会替你虚构抽牌结果。",
        "Interpretation is rule-based and intentionally narrower than a human reader's narrative synthesis.": "当前塔罗解释是规则化推演，表达范围会比人工塔罗师更收束。",
        "Interpretation is rule-based and intentionally narrower than a human reader's narrative synthesis": "当前塔罗解释是规则化推演，表达范围会比人工塔罗师更收束。",
    }
    translated = mapping.get(value)
    if translated:
        return translated
    stripped_value = value.rstrip(".")
    translated = mapping.get(stripped_value) or mapping.get(stripped_value + ".")
    if translated:
        return translated
    return translate_signal_text(value)


def top_signal(result: dict[str, Any]) -> str:
    signals = result.get("supporting_signals")
    if isinstance(signals, list):
        for item in signals:
            text = trim_reply_text(item)
            if text:
                return text
    return ""


def top_risks(result: dict[str, Any], limit: int = 3) -> list[str]:
    risks = result.get("risk_flags")
    if not isinstance(risks, list):
        return []
    cleaned: list[str] = []
    for item in risks:
        text = trim_reply_text(item)
        if text and text not in cleaned:
            cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def answer_segments(text: str) -> list[str]:
    return [segment.strip() for segment in re.split(r"(?<=[。！？!?])\s+", trim_reply_text(text)) if segment.strip()]


def english_signal_tail(segment: str) -> bool:
    text = trim_reply_text(segment)
    if not text:
        return False
    english_markers = (
        "Using a ",
        "Chart resolves to",
        "Transmission runs through",
        "Seven governors center on",
        "Property is classified into",
        "Name ",
        "Observation cluster centers on",
        "Daoist-arts classification resolves to",
        "Alchemy focus resolves to",
        "Source family resolves to",
        "Day stem is",
        "Top-ranked candidate is",
    )
    return any(marker in text for marker in english_markers)


def dedupe_answer_parts(parts: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen_texts: list[str] = []
    for part in parts:
        normalized = trim_reply_text(part)
        if not normalized:
            continue
        if english_signal_tail(normalized):
            continue
        compact = re.sub(r"\s+", "", normalized)
        if any(compact == re.sub(r"\s+", "", existing) for existing in seen_texts):
            continue
        if any(compact in re.sub(r"\s+", "", existing) or re.sub(r"\s+", "", existing) in compact for existing in seen_texts):
            continue
        seen_texts.append(normalized)
        cleaned.append(normalized.rstrip("。") + "。")
    return cleaned


def answer_repeats_verdict(verdict: str, answer: str) -> bool:
    verdict_text = trim_reply_text(verdict)
    answer_text = trim_reply_text(answer)
    if not verdict_text or not answer_text:
        return False
    verdict_compact = re.sub(r"\s+", "", verdict_text)
    answer_compact = re.sub(r"\s+", "", answer_text)
    if verdict_compact == answer_compact:
        return True
    if verdict_compact and verdict_compact in answer_compact:
        answer_segments_list = answer_segments(answer_text)
        if answer_segments_list and verdict_compact == re.sub(r"\s+", "", answer_segments_list[0]):
            return True
    return False


def merge_missing_inputs(pack: DossierPack, question: str, result: dict[str, Any] | None) -> list[str]:
    if pack.key == "date_selection" and result and is_single_date_good_day_question(question):
        return []
    if result and not (
        pack.key == "physiognomy"
        and not physiognomy_result_has_observable_features(result)
    ):
        return []
    merged: list[str] = []
    optional = OPTIONAL_ENHANCEMENT_INPUTS.get(pack.key, set())
    for item in missing_input_hints(pack, question):
        if item in optional and result:
            continue
        if item not in merged:
            merged.append(item)
    if isinstance(result, dict):
        for item in result.get("missing_inputs") or []:
            mapped = str(item).strip()
            if mapped and mapped not in merged:
                merged.append(mapped)
    return merged[:4]


def normalize_controller_missing_field(pack_key: str, question: str, field: str) -> str:
    cleaned = str(field or "").strip()
    if pack_key == "physiognomy" and cleaned == DESCRIPTION_LABEL and question_has_vague_physiognomy_description(question):
        return DESCRIPTION_LABEL
    if pack_key != "name_studies":
        return cleaned
    if engine_registry.is_name_generation_request(question):
        if cleaned == NAME_OR_OPTIONS_LABEL:
            inferred_surname = bool(engine_registry.infer_surname_for_naming(question))
            inferred_birth = bool(parse_birth_details(question).birth_datetime) and parse_birth_details(question).has_time
            if not inferred_surname:
                return SURNAME_LABEL
            if not inferred_birth and not question_wants_name_direction_only(question):
                return NAME_BIRTH_LABEL
    return cleaned


def translate_direction_sector(value: str) -> str:
    return {
        "N": "北",
        "NE": "东北",
        "E": "东",
        "SE": "东南",
        "S": "南",
        "SW": "西南",
        "W": "西",
        "NW": "西北",
    }.get((value or "").upper(), value)


def qimen_gate_verdict(gate: str) -> str:
    mapping = {
        "开门": "当前更适合打开局面、推进落实。",
        "休门": "当前宜先沟通、缓进，不宜急攻。",
        "生门": "当前有生发之机，适合启动或推进。",
        "景门": "当前更利曝光、展示和对外表达。",
        "杜门": "当前偏闭，宜先整理信息与边界。",
        "伤门": "当前阻力和损耗偏重，推进要谨慎。",
        "惊门": "当前波动和反复偏多，容易受消息扰动。",
        "死门": "当前盘面偏收，不宜硬推，先稳住更好。",
    }
    return mapping.get(gate, "")


def liuyao_relation_verdict(relation: str) -> str:
    mapping = {
        "support": "外部条件偏支持，事情更容易得到帮助。",
        "generate": "气机有生扶，事情有继续推进的空间。",
        "same": "双方气机相持，结果更看后续动作。",
        "drain": "当前更容易被消耗，先别把力气一次打完。",
        "control": "阻力偏大，宜先化解卡点再推进。",
        "pressure": "外压明显，事情不是不能做，但不适合硬上。",
    }
    return mapping.get(relation, "")


def yijing_trend_verdict(base_name: str, changed_name: str) -> str:
    base_cn = translate_hexagram_name(base_name)
    changed_cn = translate_hexagram_name(changed_name)
    caution_names = {"Obstruction", "Confining", "Limping", "Bound", "Stripping"}
    favorable_names = {"Prospering", "Ascending", "Clustering", "Open", "Holding", "Pervading", "Force"}
    if changed_name in caution_names:
        return f"本卦为{base_cn}，变卦为{changed_cn}，整体像是先有势头、后遇阻隔，宜边走边收。"
    if changed_name in favorable_names:
        return f"本卦为{base_cn}，变卦为{changed_cn}，整体仍有可推进空间。"
    return f"本卦为{base_cn}，变卦为{changed_cn}，更像是在调整路径，而不是直接一锤定音。"


def summarize_local_result(pack: DossierPack, result: dict[str, Any], question: str, tags: set[str]) -> str:
    key = pack.key

    if key == "date_selection":
        ranked = ((result.get("derived_factors") or {}).get("ranked_candidates") or [])
        if ranked:
            best = ranked[0]
            verdict = ((result.get("derived_factors") or {}).get("verdict") or "").strip()
            verdict_text = {
                "auspicious": "这一天偏吉，可用。",
                "mixed": "这一天中平可用，不算大吉，但也不是明显不宜。",
                "cautious": "这一天不算理想，宜谨慎安排。",
            }.get(verdict, "这一天已经完成本地择日直算。")
            if question_has_candidate_dates(question):
                if "搬家" in question or "入宅" in question:
                    return f"搬家候选日期里更稳的是 {best['date']}，本地择日得分是 {best['score']}。{verdict_text}"
                return f"候选日期里更稳的是 {best['date']}，本地择日得分是 {best['score']}。{verdict_text}"
            return f"{best['date']} 的本地择日得分是 {best['score']}。{verdict_text}"

    if key == "fengshui":
        derived = result.get("derived_factors") or {}
        sector = translate_direction_sector(str(derived.get("facing_sector") or ""))
        kua = derived.get("occupant_kua")
        if kua:
            pattern = derived.get("eight_mansions") or {}
            quality = next((name for name, direction in pattern.items() if direction == derived.get("facing_sector")), "")
            quality_text = {
                "sheng_qi": "生气位，偏利长期发展。",
                "tian_yi": "天医位，偏利安稳与修复。",
                "yan_nian": "延年位，偏利稳定与关系和合。",
                "fu_wei": "伏位，偏利守成与安住。",
                "jue_ming": "绝命位，不宜长期硬住。",
                "wu_gui": "五鬼位，波动和干扰偏多。",
                "liu_sha": "六煞位，容易有杂扰与消耗。",
                "huo_hai": "祸害位，小问题会比较多。",
            }.get(quality, "")
            long_term_text = ""
            if "长期居住" in question or "适不适合住" in question or "适合居住" in question:
                if quality in {"sheng_qi", "tian_yi", "yan_nian", "fu_wei"}:
                    long_term_text = "就向首与命卦配向来看，这套房更偏适合长期居住。"
                elif quality in {"jue_ming", "wu_gui", "liu_sha", "huo_hai"}:
                    long_term_text = "就向首与命卦配向来看，这套房并不偏向长期居住，至少不宜在现有条件下直接长期定居。"
            issue_text = (
                "当前最需要注意的空间问题，不在朝向本身，而在户型内部的气口、门床灶和动线是否顺。"
                if "空间问题" in question or "最需要注意" in question
                else ""
                )
            return f"这套房的向首落在{sector}位，居住者命卦为 {kua}。按八宅配向看，当前更接近{quality_text or '可继续细看户型与飞星。'}{long_term_text}{issue_text}"
        issue_text = ""
        if "睡眠" in question or "睡不好" in question:
            issue_text += " 睡眠类问题优先看床位、门冲、光线和动线，不只是朝向本身，这里也是第一处要注意的风险点。"
        if "口舌" in question or "争吵" in question:
            issue_text += " 口舌多通常也要回头看门口、走道、主卧与客厅之间是否有冲扰，这是第二类常见问题。"
        if "空间问题" in question or "哪里有问题" in question or "怎么调整" in question or "最需要注意" in question:
            issue_text += " 最需要注意的空间问题，不在朝向本身，而在入户门、主卧、床位和主要动线这几个位置。"
        long_term_text = ""
        if "长期居住" in question or "长期住" in question or "适不适合住" in question or "适合居住" in question:
            long_term_text = "单看朝向粗筛，这套房偏适合长期居住，但仍要回头看户型细节。"
        else:
            long_term_text = "当前能先给出的结论，是朝向层面没有明显硬伤。"
        return f"风水看这套房，向首落在{sector}位。{long_term_text}{issue_text}".strip()

    if key == "numerology":
        derived = result.get("derived_factors") or {}
        life_path = int(derived.get("life_path") or 0)
        birth_day = int(derived.get("birth_day_number") or 0)
        personal_year = int(derived.get("personal_year") or 0)
        life_path_map = {
            1: "主轴偏独立开创，适合自己拿主意、自己起项目。",
            2: "主轴偏协同和连接，适合在关系、合作和协调中创造价值。",
            3: "主轴偏表达和创意，适合把内容、沟通和呈现做成优势。",
            4: "主轴偏结构和执行，适合长期主义、打基础和稳步推进。",
            5: "主轴偏变化和突破，适合流动性高、需要适应力的路径。",
            6: "主轴偏责任和整合，常常会被推到照顾全局的位置。",
            7: "主轴偏研究和洞察，更适合先想透，再决定怎么出手。",
            8: "主轴偏结果与掌控，适合经营资源、目标和现实成果。",
            9: "主轴偏整合与完成，常常不是去抢新起点，而是把旧阶段收束成熟。",
        }
        personal_year_map = {
            1: "今年更适合开新局，主动定方向。",
            2: "今年更适合磨关系、等节奏、把合作做顺。",
            3: "今年更适合表达、曝光和把想法推出去。",
            4: "今年更适合夯实基础、修流程、补结构。",
            5: "今年变动会比较多，适合边试边调，但别乱跳。",
            6: "今年责任感会上升，家庭、合作和承诺议题更重。",
            7: "今年更适合复盘、学习和做内部调整。",
            8: "今年更适合冲结果、拿资源、谈现实回报。",
            9: "今年更偏收尾、清理和价值排序，不适合什么都一起开。",
        }
        day_note = {
            1: "生日数1会让你做事更想直接拍板。",
            2: "生日数2会让你更在意关系里的回应和默契。",
            3: "生日数3会把表达感、审美感和轻盈感带出来。",
            4: "生日数4会让你天然重秩序、稳定和可控。",
            5: "生日数5会带来更强的机动性和尝试欲。",
            6: "生日数6会让你更容易承担照顾与协调角色。",
            7: "生日数7会让你更习惯先观察、再判断。",
            8: "生日数8会让你更重视效率、资源和结果。",
            9: "生日数9会让你做事带一点理想性和整体观。",
        }.get(birth_day, "")
        return (
            f"数字命理看，这组生日落出的生命灵数是{life_path or '未明'}，生日数是{birth_day or '未明'}，个人年是{personal_year or '未明'}。"
            f"{life_path_map.get(life_path, '这组数字更偏向先看长期主题，再看年份节奏。')}"
            f"{personal_year_map.get(personal_year, '当前更适合先看节奏，再定动作。')}"
            f"{day_note}"
        )

    if key == "bazi":
        summary = result.get("summary") or {}
        day_master = result.get("day_master") or {}
        strongest = "、".join(summary.get("strongest_elements") or [])
        weakest = "、".join(summary.get("weakest_elements") or [])
        ten_gods = result.get("ten_gods") or {}
        hidden_ten_gods = result.get("hidden_ten_gods") or {}
        overview = result.get("overview") or {}
        strength = str(result.get("day_master_strength") or "")
        favorable = "、".join(result.get("favorable_elements") or [])
        caution_elements = "、".join(result.get("caution_elements") or [])
        focus = question_topic_focus(question)
        direct_wealth_count = count_labels(list(ten_gods.values()), {"正财", "偏财"})
        hidden_wealth_count = sum(
            count_labels([str(item.get("ten_god") or "") for item in values], {"正财", "偏财"})
            for values in hidden_ten_gods.values()
            if isinstance(values, list)
        )
        output_count = count_labels(list(ten_gods.values()), {"食神", "伤官"})
        peer_count = count_labels(list(ten_gods.values()), {"比肩", "劫财"})
        officer_count = count_labels(list(ten_gods.values()), {"正官", "七杀"})
        resource_count = count_labels(list(ten_gods.values()), {"正印", "偏印"})
        hidden_relationship_count = sum(
            count_labels([str(item.get("ten_god") or "") for item in values], {"正官", "七杀", "正财", "偏财"})
            for values in hidden_ten_gods.values()
            if isinstance(values, list)
        )
        if any(token in question for token in FULL_CHART_MARKERS) or {"wealth", "career_path", "relationship_topic", "identity_topic", "health"} <= focus:
            axis_parts = [
                trim_reply_text(overview.get("personality")),
                trim_reply_text(overview.get("career")),
                trim_reply_text(overview.get("wealth")),
                trim_reply_text(overview.get("relationship")),
                trim_reply_text(overview.get("health")),
                trim_reply_text(overview.get("direction")),
            ]
            lead = (
                f"八字全盘看，这盘日主{day_master.get('stem', '')}，五行呈现{strongest or '未明'}偏强、{weakest or '未明'}偏弱，"
                f"整体更接近{'身强取泄耗财官' if strength == 'strong' else '身弱先扶身印比' if strength == 'weak' else '中和取流通'}的结构。"
            )
            if favorable or caution_elements:
                lead += (
                    f" 现阶段更有利的发力元素偏向{favorable or '未明'}，"
                    f"需要少硬扛的部分偏在{caution_elements or '未明'}。"
                )
            return " ".join(part for part in [lead] + axis_parts if part).strip()
        if "wealth" in focus:
            source_parts: list[str] = []
            risk_parts: list[str] = []
            rhythm_parts: list[str] = []
            if direct_wealth_count >= 2 or hidden_wealth_count >= 3:
                source_parts.append("命盘里财星不算少，钱路不是没有，重点在于把进账方式做稳定")
            elif direct_wealth_count >= 1 or hidden_wealth_count >= 1:
                source_parts.append("财星能见，说明有现实进账通道，更适合靠项目、业务、资源兑现来拿钱")
            else:
                source_parts.append("明面财星不重，财运更怕只靠单点爆发，适合把能力变成长期可复用的收入结构")
            if output_count >= 1:
                source_parts.append("食伤也有根，赚钱方式偏技能输出、内容表达、解决问题和拿结果换钱")
            if peer_count >= 2:
                risk_parts.append("比劫偏重，财一进来就容易被分走、垫出去，合伙、人情单、冲动扩张都要防")
            if officer_count >= 1:
                rhythm_parts.append("官杀入局，财运不是纯野路子，更适合制度内、规则清楚、责任边界明确的赚钱方式")
            if "火" in strongest:
                risk_parts.append("火势偏旺，财运起的时候容易判断快、动作快，越是来钱快越要防追高和情绪消费")
            if "水" in weakest:
                risk_parts.append("水弱时现金流缓冲偏薄，最怕账面热闹、回款偏慢，所以一定要留周转余量")
            if "木" in weakest:
                rhythm_parts.append("木弱说明持续生发力一般，财路要靠长期经营，不宜今天开一个、明天换一个")
            return "。".join(
                part for part in [
                    f"八字看财运，这盘以日主{day_master.get('stem', '')}为核心，财星和比劫同时有存在感",
                    "；".join(source_parts) if source_parts else "",
                    "；".join(rhythm_parts) if rhythm_parts else "",
                    f"要特别防的是：{'；'.join(risk_parts)}" if risk_parts else "",
                ] if part
            ) + "。"
        if "career_path" in focus and "space" in normalized_question_topics(question, tags) and "priority" in question_requested_facets(question):
            priority_parts: list[str] = []
            if officer_count >= 1 or output_count >= 1:
                priority_parts.append("这盘更适合先把工作主线和收入结构稳住，再动居住层面的调整")
            if "木" in weakest:
                priority_parts.append("木弱说明持续生发力一般，不宜工作和搬家两头同时拉满，先后顺序比同步折腾更重要")
            if peer_count >= 2:
                priority_parts.append("比劫偏重时外部杂事和人情牵扯会分神，若先搬家，事业推进容易被打散")
            return "。".join(
                part for part in [
                    f"八字放到换工作和搬家这类先后题上，这盘以日主{day_master.get('stem', '')}为核心，更像是先立事业再调居住",
                    "；".join(priority_parts) if priority_parts else "",
                    "如果必须两件都做，建议先把工作方向、岗位边界或收入落点定下来，再安排搬动，会更顺。",
                ] if part
            ) + "。"
        career_options = extract_career_option_candidates(question)
        if "career_path" in focus and len(career_options) >= 2:
            option_set = set(career_options)
            if option_set == {"上班", "创业", "自由职业"}:
                return (
                    f"八字放到职业模式三选一上，以日主{day_master.get('stem', '')}为核心，"
                    f"{career_option_summary(question, '上班', '自由职业', '创业不要一上来就重仓，先借平台把结果、信用和方法沉淀出来会更稳。')}"
                    f"{' 官杀能立得住，说明你在职责清楚、结果可衡量的位置上更容易出成绩。' if officer_count >= 1 else ''}"
                    f"{' 食伤有力，所以后面转成更独立的输出也不是没空间。' if output_count >= 1 else ''}"
                    f"{' 比劫偏重时，太早创业更怕资源分流、人情牵扯和节奏被打散。' if peer_count >= 2 else ''}"
                ).replace("。。", "。").strip()
            if option_set == {"上班", "自由职业", "自己接项目"}:
                return (
                    f"八字放到这组三选一上，以日主{day_master.get('stem', '')}为核心，"
                    f"{career_option_summary(question, '上班', '自由职业', '自己接项目不要一上来就压成主线，至少先把客户来源、回款节奏和交付边界练稳。')}"
                    f"{' 官杀能立得住，说明你在职责清楚、结果可衡量的位置上更容易出成绩。' if officer_count >= 1 else ''}"
                    f"{' 食伤有力，所以后面转成更独立的输出也不是没空间。' if output_count >= 1 else ''}"
                    f"{' 比劫偏重时，太早把项目合作扛到最前面，更怕资源分流、人情牵扯和节奏被打散。' if peer_count >= 2 else ''}"
                ).replace("。。", "。").strip()
            if option_set == {"销售", "咨询", "自己接项目"}:
                preferred = "咨询" if output_count >= 1 else "销售"
                secondary = "销售" if preferred == "咨询" else "咨询"
                return (
                    f"八字放到这组三选一上，以日主{day_master.get('stem', '')}为核心，"
                    f"{career_option_summary(question, preferred, secondary, '自己接项目更像第二阶段，至少要先把客户来源、回款节奏和交付边界练稳。')}"
                    f"{' 食伤有力，说明你更适合把表达、判断和解决问题的能力直接变成价值。' if output_count >= 1 else ''}"
                    f"{' 财星能见，所以销售和结果导向的角色也能接得住。' if direct_wealth_count >= 1 or hidden_wealth_count >= 1 else ''}"
                    f"{' 比劫偏重时，独立接项目最怕中途被分神、被分功，或者钱进来又被杂事吃掉。' if peer_count >= 2 else ''}"
                ).replace("。。", "。").strip()
        if "career_path" in focus and "relationship_topic" in focus:
            relation_parts: list[str] = []
            if hidden_relationship_count >= 2:
                relation_parts.append("感情不是没机会，但更像先有接触，再慢慢定性")
            if officer_count >= 1:
                relation_parts.append("关系里会很看责任感和稳定度")
            if direct_wealth_count >= 1 or hidden_wealth_count >= 1:
                relation_parts.append("现实条件和价值观一致性对感情影响很大")
            if peer_count >= 2:
                relation_parts.append("第三方意见和双方强势都容易拉扯关系")
            return "。".join(
                part for part in [
                    f"八字看婚姻，这盘以日主{day_master.get('stem', '')}为核心，关系不是没有机会，但更重稳定磨合后的落地感",
                    "；".join(relation_parts) if relation_parts else "",
                    "对象类型上，更适合务实、讲边界、能一起处理现实问题的人。",
                ] if part
            ) + "。"
        if "career_path" in focus:
            path_parts: list[str] = []
            risk_parts: list[str] = []
            if officer_count >= 1:
                path_parts.append("官杀能立得住，事业上更适合走职责清楚、结果可衡量、有位置晋升的路径")
            if output_count >= 1:
                path_parts.append("食伤有力，工作上不能只做执行，更适合靠表达、方案、产出和解决问题往上走")
            if direct_wealth_count >= 1 or hidden_wealth_count >= 1:
                path_parts.append("财星能见，事业和收入绑定很深，做对业务结构比单纯熬资历更重要")
            if peer_count >= 2:
                risk_parts.append("同级竞争和资源分流会比较明显，最怕项目做到一半被人分功或被杂事拖散")
            if "火" in strongest:
                risk_parts.append("火旺时容易推进太急，职业上宜先定主线，再扩副线")
            if "木" in weakest:
                risk_parts.append("木弱代表持续培育力一般，转型别过密，方向频繁切换会稀释势能")
            if not path_parts:
                path_parts.append("这盘事业更看重先把个人结构调顺，再决定是守岗位还是主动扩张")
            return "。".join(
                part for part in [
                    f"八字看事业，以日主{day_master.get('stem', '')}为核心，当前职业路径重点在于把能见度、责任位和产出方式接起来",
                    "；".join(path_parts),
                    f"要防的是：{'；'.join(risk_parts)}" if risk_parts else "",
                ] if part
            ) + "。"
        if "relationship_topic" in focus:
            relation_parts: list[str] = []
            caution_parts: list[str] = []
            if hidden_relationship_count >= 2:
                relation_parts.append("伴侣缘不是没有，但更像是先有接触和牵引，再慢慢定性，不是一下子就锁死关系")
            if officer_count >= 1:
                relation_parts.append("关系里会在意责任感、边界和能不能给到确定性，太飘太散的对象很难让你真正放心")
            if direct_wealth_count >= 1 or hidden_wealth_count >= 1:
                relation_parts.append("现实条件、生活安排和价值观一致性，对感情能不能走远影响很大")
            if peer_count >= 2:
                caution_parts.append("比劫偏重时，关系里容易因为第三方意见、朋友介入或双方各自太强而拉扯")
            if output_count >= 1:
                caution_parts.append("说话太直、情绪上头时抢结论，会把本来能谈开的事谈硬")
            if "水" in weakest:
                caution_parts.append("水弱时情绪缓冲不足，亲密关系里要学会留余地，不要一急就要答案")
            if not relation_parts:
                relation_parts.append("婚姻这块更适合慢热筛选，先看价值观和现实配合，再谈承诺")
            return "。".join(
                part for part in [
                    f"八字看婚姻，这盘以日主{day_master.get('stem', '')}为核心，感情不是没机会，但更重长期磨合后的稳定度",
                    "；".join(relation_parts),
                    f"要注意的是：{'；'.join(caution_parts)}" if caution_parts else "",
                ] if part
            ) + "。"
        if "identity_topic" in focus:
            identity_parts: list[str] = []
            if "火" in strongest:
                identity_parts.append("火旺让你外在反应快、表达欲和存在感都不低，做事不喜欢长期闷着")
            if output_count >= 1:
                identity_parts.append("食伤有根，天赋更偏表达、拆解问题、把抽象东西说清楚")
            if peer_count >= 2:
                identity_parts.append("比劫重说明自主性强，不太适合长期被人压着节奏走")
            if resource_count >= 1:
                identity_parts.append("印星露头时，学习和总结能力也在线，适合把经验沉淀成方法")
            if not identity_parts:
                identity_parts.append("这盘不是完全靠顺势的人，很多路要靠自己先点火、再形成结构")
            return "。".join(
                part for part in [
                    f"八字看性格与方向，日主{day_master.get('stem', '')}带出的核心气质，是先凭主观能动性起步，再用结果说话",
                    "；".join(identity_parts),
                    "适合走能让你主动组织、表达判断、逐步形成个人方法论的方向。",
                ] if part
            )
        if strongest or weakest:
            return (
                f"八字先看日主 {day_master.get('stem', '')}，五行呈现 {strongest or '未明'} 偏强、"
                f"{weakest or '未明'} 偏弱。当前更像是先看结构失衡，再谈事业与财运取舍。"
            )

    if key == "yijing_and_symbolism":
        derived = result.get("derived_factors") or {}
        base_name = ((derived.get("base_hexagram") or {}).get("name") or "").strip()
        changed_name = ((derived.get("changed_hexagram") or {}).get("name") or "").strip()
        if base_name and changed_name:
            trend = yijing_trend_verdict(base_name, changed_name)
            if "timing" in normalized_question_topics(question, tags) and "能不能成" in question:
                if changed_name in {"Obstruction", "Confining", "Limping", "Bound", "Stripping"}:
                    return f"{trend} 这件事不是完全不能做，但更像先有机会窗口、后面会卡在条件和落地环节。"
                if changed_name in {"Prospering", "Ascending", "Clustering", "Open", "Holding", "Pervading", "Force"}:
                    return f"{trend} 就结果判断来说，这件事有成的空间，关键在于别把推进节奏拉得过满。"
            return trend

    if key == "liuyao_and_meihua":
        derived = result.get("derived_factors") or {}
        relation = str(((derived.get("body_use_relation") or {}).get("relation")) or "")
        body = translate_trigram((derived.get("body_trigram") or {}).get("name") if isinstance(derived.get("body_trigram"), dict) else derived.get("body_trigram"))
        use = translate_trigram((derived.get("use_trigram") or {}).get("name") if isinstance(derived.get("use_trigram"), dict) else derived.get("use_trigram"))
        relation_text = liuyao_relation_verdict(relation)
        structure = derived.get("yijing_structure") or {}
        base_name = ((structure.get("base_hexagram") or {}).get("name") or "").strip()
        changed_name = ((structure.get("changed_hexagram") or {}).get("name") or "").strip()
        if body and use:
            lead = f"这次梅花起卦里，体卦为{body}，用卦为{use}。"
            relation_positive = {"support", "peer"}
            if "能不能成" in question or "可不可行" in question or "成不成" in question:
                if relation in relation_positive:
                    verdict = "体用关系不差，说明事情不是推不动，前段有资源或外力可借。"
                elif relation in {"control", "pressure"}:
                    verdict = "体用关系偏压，说明阻力会比较实，不适合乐观过头。"
                else:
                    verdict = "体用之间还在拉扯，成不成主要看后续怎么接条件。"
                trend = yijing_trend_verdict(base_name, changed_name) if base_name and changed_name else ""
                return " ".join(part for part in [lead, verdict, trend, relation_text] if part).strip()
            if any(token in question for token in ("往下推", "推进", "下一步", "项目")):
                if relation in relation_positive:
                    verdict = "体用相生或同气，说明这件事还能往下推，但更适合先借势推进，再看后段承接。"
                    action = "下一步重点不是盲目加速，而是先把合作条件、资源配合和落地分工对齐。"
                elif relation in {"control", "pressure"}:
                    verdict = "体用受制，说明项目还能动，但推进会卡在外部条件或关键人反馈上。"
                    action = "下一步宜先拆阻力、补条件、稳关键节点，不适合直接硬压进度。"
                else:
                    verdict = "体用有消耗，说明项目不是不能推，但越往后越考验持续投入和执行耐力。"
                    action = "下一步更适合缩小战线，先保最关键的一段推进，不要同时摊太多目标。"
                trend = yijing_trend_verdict(base_name, changed_name) if base_name and changed_name else ""
                return " ".join(part for part in [lead, verdict, trend, relation_text, action] if part).strip()
            if relation in relation_positive:
                verdict = "体用相生或同气，说明这件事本身有可推进空间。"
            elif relation in {"control", "pressure"}:
                verdict = "体用受制，说明事情会遇到较实的阻力，不能只靠一股劲硬推。"
            else:
                verdict = "体用之间有消耗，说明事情能动，但推进时更怕后劲不足。"
            trend = yijing_trend_verdict(base_name, changed_name) if base_name and changed_name else ""
            return " ".join(part for part in [lead, verdict, trend, relation_text] if part).strip()
            return f"{lead}{relation_text}".strip() if relation_text else lead
        primary = translate_signal_text(trim_reply_text(result.get("primary_finding")))
        if relation_text:
            return f"{primary} {relation_text}".strip()

    if key == "qimen_dunjia":
        derived = result.get("derived_factors") or {}
        gate = str((derived.get("zhi_shi") or {}).get("gate") or "")
        dun_type = "阳遁" if str(derived.get("dun_type") or "").lower() == "yang" else "阴遁"
        ju_number = derived.get("ju_number")
        zhi_fu = derived.get("zhi_fu") or {}
        primary = f"本局为{dun_type}{ju_number}局，值符落{zhi_fu.get('palace', '未明')}宫。"
        gate_text = qimen_gate_verdict(gate)
        if "timing" in normalized_question_topics(question, tags):
            active_palaces = cn_join([str(item) for item in (derived.get("active_palaces") or [])[:4]], "、")
            detail = f"活跃宫位主要落在{active_palaces}宫。" if active_palaces else ""
            action = "下一步宜先把阻滞点和资源错位先处理掉，再推进。" if gate == "死门" else "下一步可以推进，但先把风险点和优先级排清。"
            risk = "风险点主要在节奏过快、边界不清或资源没对齐。" if gate in {"死门", "伤门", "惊门"} else "风险点主要在先后顺序和执行节奏。"
            return " ".join(part for part in [primary, gate_text, detail, risk, action] if part).strip()
        if gate_text:
            return f"{primary} {gate_text}".strip()
        return primary

    if key == "liu_ren":
        derived = result.get("derived_factors") or {}
        ke_ti = str((derived.get("ke_ti") or {}).get("method") or "")
        san_chuan = (derived.get("san_chuan") or {})
        relations = [
            str((san_chuan.get("chu") or {}).get("relation") or ""),
            str((san_chuan.get("zhong") or {}).get("relation") or ""),
            str((san_chuan.get("mo") or {}).get("relation") or ""),
        ]
        if relations and all(item == "官鬼" for item in relations if item):
            return f"大六壬课体为 {ke_ti or '未明'}，三传连见官鬼，说明阻力和约束偏重，事情不是不能成，但先压实风险更重要。"
        chu = san_chuan.get("chu") or {}
        zhong = san_chuan.get("zhong") or {}
        mo = san_chuan.get("mo") or {}
        if chu or zhong or mo:
            if "timing" in normalized_question_topics(question, tags):
                relation_chain = "、".join(
                    item for item in [
                        str(chu.get("relation") or "").strip(),
                        str(zhong.get("relation") or "").strip(),
                        str(mo.get("relation") or "").strip(),
                    ] if item
                )
                action = "前段能动，后段见官鬼，说明这事不是完全推不动，但推进到落地环节会碰到规则、审批或现实门槛。" if "官鬼" in relations else "整体节奏是先动后定，适合先试探、再确认资源和边界。"
                risk = "风险点主要在规则、审批、现实门槛或中途反复。" if "官鬼" in relations else "风险点主要在前期试探不足和边界没先定清。"
                return (
                    f"大六壬课体为{ke_ti or '未明'}，三传依次为"
                    f"{chu.get('branch', '未明')}、{zhong.get('branch', '未明')}、{mo.get('branch', '未明')}，"
                    f"传中关系落点为{relation_chain or '未明'}。{risk}{action}"
                )
            return (
                f"大六壬课体为{ke_ti or '未明'}，三传依次为"
                f"{chu.get('branch', '未明')}、{zhong.get('branch', '未明')}、{mo.get('branch', '未明')}。"
            )
        primary = translate_signal_text(trim_reply_text(result.get("primary_finding")))
        if primary:
            return primary

    if key == "daoist_arts":
        derived = result.get("derived_factors") or {}
        practice_family = str(derived.get("practice_family") or "").strip()
        safety_tier = str(derived.get("safety_tier") or "").strip()
        purpose = str(derived.get("purpose") or "").strip()
        lineage = (derived.get("lineage") or {})
        lineage_name = translate_daoist_lineage(str(lineage.get("canonical") or "未明"))
        practice_markers = [trim_reply_text(item) for item in (derived.get("practice_markers") or []) if trim_reply_text(item)]
        ritual_components = [trim_reply_text(item) for item in (derived.get("ritual_components") or []) if trim_reply_text(item)]
        taboo_hits = derived.get("taboo_hits") or []
        if taboo_hits:
            return (
                f"道术这一路当前落在{translate_daoist_family(practice_family) or '高风险仪轨类'}，而且已经碰到{cn_join([str(item) for item in taboo_hits[:4]])}这类高风险边界。"
                "这类内容只适合做文化和禁忌层面的说明，不适合当成可执行做法。"
            )
        if any(token in question for token in ("净宅", "护身", "化煞", "安神")) and any(token in question for token in ("先做哪类", "先做什么", "优先", "别乱碰", "禁忌")):
            lead_family = translate_daoist_family(practice_family) or "护持/净化类"
            marker_text = f"题面里当前最直接命中的线索是{cn_join(practice_markers[:4])}。" if practice_markers else ""
            boundary_text = (
                "别一上来就把化煞、驱逐、强行压制类动作当主线，尤其在没有明确场景、法脉约束和师承把关时，最容易越做越乱。"
                if safety_tier in {"guided-only", "lineage-dependent"}
                else "别把需要明确场景和边界的动作混着做，先分清是空间不安、个人受惊，还是单纯节奏紊乱。"
            )
            return (
                f"道术放到你这题里，当前先做{lead_family}更稳，顺序上优先净宅/安神，再看要不要补护身；化煞不要一上来就重手。"
                f"{marker_text} 法脉框架偏{lineage_name}，这类事更看场景、边界和传承约束，不适合把几类动作混成一个万能流程。"
                f"{boundary_text}"
            )
        if purpose in {"cleansing", "protection"}:
            marker_text = f" 题面里实际命中的场景线索有{cn_join(practice_markers[:4])}。" if practice_markers else ""
            component_text = (
                f" 已识别到的仪式部件更偏{cn_join(ritual_components[:4])}，说明它不是随手念一句就完的轻操作。"
                if ritual_components else
                " 这类问题当前更像是在问适用场景与边界，不是在给一个可直接照做的流程。"
            )
            return (
                f"道术看这类净宅、护身、化煞、安神问题，当前更接近{translate_daoist_family(practice_family) or '护持/净化类'}，法脉框架偏{lineage_name}。"
                f"{marker_text}{component_text}"
                " 更适合把它理解成有适用场景、有边界和禁忌的护持体系，而不是随手套用的通用操作。"
            )
        if safety_tier in {"guided-only", "lineage-dependent"}:
            component_text = f" 已识别到的仪式部件有{cn_join(ritual_components[:4])}。" if ritual_components else ""
            return (
                f"道术这一路当前落在{translate_daoist_family(practice_family) or '法脉仪轨类'}，法脉框架偏{lineage_name}。"
                f"{component_text}这类内容更适合做结构理解和禁忌提醒，真正落地仍然要看传承、场景和师承约束。"
            )

    if key == "physiognomy":
        derived = result.get("derived_factors") or {}
        dominant_axis = (derived.get("dominant_axis") or {})
        axis_label = translate_physiognomy_axis(str(dominant_axis.get("label") or "").strip())
        features = derived.get("features") or {}
        feature_hits = summarize_physiognomy_feature_hits(features)
        positive_regions = []
        for region_key, region in features.items():
            if str((region or {}).get("leaning") or "").strip() == "positive":
                positive_regions.append(region_key)
        axis_scores = derived.get("axis_scores") or {}
        material = int(axis_scores.get("material") or 0)
        vitality = int(axis_scores.get("vitality") or 0)
        stability = int(axis_scores.get("stability") or 0)
        will = int(axis_scores.get("will") or 0)
        if axis_label:
            multifacet_summary = physiognomy_multifacet_summary(question, derived, axis_label)
            if multifacet_summary:
                return multifacet_summary
            if "销售" in question or "沟通" in question or "商务" in question:
                sales_note = "放到销售这类岗位上，这组特征更偏向先建立可信度，再放大表达与推进，不是压迫式猛冲路线。"
                if vitality >= 2 or will >= 2:
                    sales_note = "放到销售这类岗位上，这组特征既有可信度，也有一定推进力，更适合做需要持续跟进与关系经营的销售。"
                return (
                    f"面相这一路按你给出的描述看，主轴更落在{axis_label}，整体不是散乱虚浮型，做销售是有适配空间的。"
                    f"{f' 真正把这个判断顶起来的，是{feature_hits}这几组信号。' if feature_hits else ''}"
                    f"{sales_note}"
                    f"{' 鼻梁和下巴这组信号偏正，通常更容易给人稳、能扛事、现实感不差的印象。' if material >= 2 or stability >= 1 else ''}"
                    "当前看到的特征多半是加分项，但它更适合看作倾向，不是固定命数。"
                )
            parts = [
                f"面相这一路按你给出的描述看，主轴更落在{axis_label}，整体不是散乱虚浮型。",
            ]
            if feature_hits:
                parts.append(f"这次真正起作用的观察点主要是{feature_hits}。")
            if vitality >= 2 or will >= 2:
                parts.append("精神头、执行意愿和当下的行动力会比一般描述更显眼。")
            if material >= 2 or stability >= 1:
                parts.append("鼻梁和下巴这组信号偏正，通常更容易给人稳、能扛事、现实感不差的印象。")
            if positive_regions:
                parts.append("当前看到的特征多半是加分项，但它更适合看作倾向，不是固定命数。")
            return "".join(parts)

    if key == "kabbalah":
        derived = result.get("derived_factors") or {}
        canonical = str(derived.get("canonical_name") or "").strip()
        title = translate_kabbalah_title(str(derived.get("title") or "").strip())
        pillar = translate_tree_pillar(str(derived.get("pillar") or "").strip())
        keywords = [
            translate_kabbalah_keyword(str(item).strip())
            for item in (derived.get("keywords") or [])
            if str(item).strip()
        ]
        secondary_nodes = derived.get("secondary_nodes") or []
        if canonical:
            keyword_text = "、".join(keywords[:3]) if keywords else "整合、中心与秩序"
            topic_domains = set(derived.get("topic_domains") or [])
            domain_text_map = {
                "career": "事业",
                "relationship": "关系",
                "identity": "自我定位",
                "wealth": "资源与财务",
            }
            domain_text = cn_join([domain_text_map[item] for item in ("career", "relationship", "identity", "wealth") if item in topic_domains])
            if any(token in question for token in ("失衡", "短板", "阴影", "容易卡在哪", "容易出问题")):
                imbalance_note = {
                    "Hod": "最容易失衡在想得太多、拆得太细、解释很多但推进变慢，结果是事业上容易把判断力变成迟疑，自我价值感也容易绑在“我说得够不够对”上。",
                    "Netzach": "最容易失衡在情绪和欲望往前冲，结果是关系和事业里都容易先上头、后失速。",
                    "Tiphereth": "最容易失衡在太想维持整体和体面，结果是外面看着稳，里面却容易把真实需求压住。",
                    "Yesod": "最容易失衡在投射和依附，容易把不确定感放大成脑内剧情。",
                    "Gevurah": "最容易失衡在控制过强、判断过硬，容易把边界做成封闭。",
                    "Chesed": "最容易失衡在给得太多、铺得太开，最后承接不住。",
                    "Malkuth": "最容易失衡在太受现实牵引，容易把价值感压缩成眼前得失。",
                }.get(canonical, "最容易失衡在把某一层能力用得太满，结果从优势滑到执拗。")
                return (
                    f"卡巴拉放到你这题里，主轴先落在{canonical}{f'（{title}）' if title else ''}，它在生命之树里偏向{pillar or '中柱'}。"
                    f"优势面会更偏{keyword_text}；但你最容易失衡的地方也在这里：{imbalance_note}"
                    f"{f' 这次主要牵动的是{domain_text}维度。' if domain_text else ''}"
                )
            if secondary_nodes:
                secondary_parts = []
                for item in secondary_nodes[:2]:
                    secondary_name = str(item.get("canonical_name") or "").strip()
                    secondary_title = translate_kabbalah_title(str(item.get("title") or "").strip())
                    secondary_keywords = [
                        translate_kabbalah_keyword(str(keyword).strip())
                        for keyword in (item.get("keywords") or [])
                        if str(keyword).strip()
                    ]
                    secondary_parts.append(
                        f"{secondary_name}{f'（{secondary_title}）' if secondary_title else ''}更偏{'、'.join(secondary_keywords[:2]) or '结构支撑'}"
                    )
                if "career" in topic_domains and "relationship" in topic_domains:
                    return (
                        f"卡巴拉这一路主轴先落在{canonical}{f'（{title}）' if title else ''}，它在生命之树里偏向{pillar or '中柱'}，"
                        f"更像把事业里的位置感和关系里的连接感拉回同一条中心线。"
                        f"主节点关键词偏{keyword_text}；题面里同时提到的{'；'.join(secondary_parts)}，说明这不是一套完全相同的词，而是同树上不同层位。"
                    )
                return (
                    f"卡巴拉这一路主轴先落在{canonical}{f'（{title}）' if title else ''}，它在生命之树里偏向{pillar or '中柱'}。"
                    f"{f' 这次问题实际牵动的是{domain_text}维度。' if domain_text else ''}"
                    f" 主节点关键词偏{keyword_text}；题面里同时提到的{'；'.join(secondary_parts)}。"
                )
            if "career" in (derived.get("topic_domains") or []) or "career" in question.lower():
                return (
                    f"卡巴拉这一路落到{canonical}{f'（{title}）' if title else ''}，它在生命之树里偏向{pillar or '中柱'}。"
                    f"放到职业方向上，意思不是去追最热闹的路，而是走能把你的能力、位置和外部可见度整合起来的路。"
                    f"关键词会更偏{keyword_text}。"
                )
            return f"卡巴拉这一路落到{canonical}{f'（{title}）' if title else ''}，它在生命之树里偏向{pillar or '中柱'}。关键词会更偏{keyword_text}。"

    if key == "alchemy_and_hermeticism":
        derived = result.get("derived_factors") or {}
        stage = (derived.get("stage") or {})
        stage_name = translate_alchemy_term(str(stage.get("name") or "").strip())
        next_stage = translate_alchemy_term(str(stage.get("next_stage") or "").strip())
        operations = [translate_alchemy_term(str(item).strip()) for item in (derived.get("operations") or []) if str(item).strip()]
        symbols = [translate_alchemy_term(str((item or {}).get("name") or "").strip()) for item in (derived.get("symbols") or []) if str((item or {}).get("name") or "").strip()]
        if stage_name:
            return (
                f"炼金术这一路当前明确落在{stage_name}，重点不是继续往外堆材料，而是先分解旧结构、把阴影内容看清。"
                f"{' 当前动作更接近' + '、'.join(operations[:2]) + '。' if operations else ''}"
                f"{' 符号上牵动的是' + '、'.join(symbols[:3]) + '，说明主题落在挥发性与定形之间的拉扯。' if symbols else ''}"
                f"{' 下一步会转向' + next_stage + '，也就是从拆解走向澄清。' if next_stage else ''}"
            )

    if key == "onmyodo":
        derived = result.get("derived_factors") or {}
        day_info = derived.get("day_info") or {}
        relation = str(derived.get("direction_relation") or "").strip()
        score = int(derived.get("score") or 0)
        direction = translate_direction_sector(str(day_info.get("year_direction") or ""))
        omen = translate_hexagram_name(str(derived.get("omen_hexagram") or "").strip())
        if score:
            if score >= 65:
                verdict = "这个方向与时点整体偏顺，可以走。"
            elif score >= 45:
                verdict = "这个方向和时点不算最好，但还能用，重在别把行程压得太满。"
            else:
                verdict = "这个方向与时点偏不利，若能绕开或改期会更稳。"
            relation_text = {
                "day generates direction": "当天气机对这个方向有扶助。",
                "same element": "当天与方向同气，事情更看你自己怎么安排行程。",
                "day restrains direction": "当天气机对这个方向有压制，容易出现折返、耽搁或心态烦躁。",
            }.get(relation, "")
            omen_text = f" 当前卦象提示更接近{omen}。" if omen else ""
            return f"阴阳道按当前日时看，{verdict}{relation_text}{f' 当日年方位锚点落在{direction}。' if direction else ''}{omen_text}"

    if key == "modern_esotericism":
        derived = result.get("derived_factors") or {}
        source_family = translate_modern_esoteric_family(str(((derived.get("source_family") or {}).get("name")) or "").strip())
        concept_family = translate_modern_esoteric_family(str(((derived.get("concept_family") or {}).get("name")) or "").strip())
        risk_tier = str(derived.get("risk_tier") or "").strip()
        usable_scope = translate_usable_scope(str(derived.get("usable_scope") or "").strip())
        if source_family or concept_family:
            domain_weights = derived.get("domain_weights") or {}
            domain_name_map = {
                "psychological": "心理整理",
                "religious": "灵修宗教",
                "commercial": "商业包装",
                "wellness": "身心疗愈",
            }
            dominant_domains = []
            for domain_key in ("psychological", "religious", "commercial", "wellness"):
                if int(domain_weights.get(domain_key) or 0) > 0:
                    dominant_domains.append(domain_name_map.get(domain_key, domain_key))
            domain_text = cn_join(dominant_domains[:3])
            risk_text = {
                "low": "整体风险不高，重点是别把象征语言当现实承诺。",
                "medium": "这条路可以继续，但要把象征实践、心理整理和现实判断分开。",
                "high": "这条路的混杂度和误导风险偏高，边界要先立住。",
            }.get(risk_tier, "这条实践路径更适合带边界地使用。")
            return (
                f"现代神秘学这一路看，你当前这套做法更像是{concept_family or '象征整理'}和{source_family or '能量实践'}混合在一起。"
                f"{f' 当前主要被拉高的维度是{domain_text}。' if domain_text else ''}"
                f"{risk_text}"
                f"{f' 当前更稳的使用方式是{usable_scope}。' if usable_scope else ''}"
            )

    if key == "western_astrology":
        focus = question_topic_focus(question)
        derived = result.get("derived_factors") or {}
        big_three = (result.get("derived_factors") or {}).get("big_three") or {}
        sun = translate_western_sign(big_three.get("sun"))
        moon = translate_western_sign(big_three.get("moon"))
        asc = translate_western_sign(big_three.get("ascendant"))
        planets = ((result.get("raw_chart") or {}).get("planets") or {})
        venus = planets.get("Venus") or {}
        jupiter = planets.get("Jupiter") or {}
        saturn = planets.get("Saturn") or {}
        dominant_houses = derived.get("dominant_houses") or []
        if "career_path" in focus and "relationship_topic" in focus and (sun or moon or asc):
            career_parts: list[str] = []
            relationship_parts: list[str] = []
            caution_parts: list[str] = []
            if int(jupiter.get("house_number") or 0) == 10:
                career_parts.append("事业放大量强，适合把能力做成外部可见的成果")
            if 9 in dominant_houses:
                career_parts.append("职业路径会和认知升级、表达输出、跨领域拓展绑得很紧")
            if int(venus.get("house_number") or 0) == 8:
                relationship_parts.append("关系模式偏深绑定，容易把信任、资源和现实配合看得很重")
                caution_parts.append("合作和感情都要防边界不清、分账不明或情绪卷得太深")
            if moon:
                relationship_parts.append(f"月亮{moon}说明你既要情绪空间，也要能看见彼此成长")
            if asc:
                relationship_parts.append(f"上升{asc}让你挑人时会看细节和稳定度，不太会长期吃表面热情那一套")
            if int(saturn.get("house_number") or 0) in {5, 7, 8}:
                caution_parts.append("关系推进别太急，事业合作也不适合一上来就把承诺给满")
            return "。".join(
                part for part in [
                    f"西占看事业和关系，这张盘的本命核心是太阳{sun or '未明'}、月亮{moon or '未明'}、上升{asc or '未明'}。",
                    "事业上更适合靠专业表达、外部认可和阶段性成果往上走，不是闷头熬年限的路线"
                    + (f"；{cn_join(career_parts, '；')}" if career_parts else ""),
                    "关系模式上不是轻飘飘的来去型，更看深度、稳定和现实配合"
                    + (f"；{cn_join(relationship_parts, '；')}" if relationship_parts else ""),
                    f"要注意的是：{cn_join(caution_parts, '；')}" if caution_parts else "",
                ] if part
            ) + "。"
        if "wealth" in focus and venus and jupiter:
            wealth_mode = []
            risk_parts = []
            if int(jupiter.get("house_number") or 0) == 10:
                wealth_mode.append("进财更适合走事业放大、职位抬升、品牌信用和公开成果")
            if int(venus.get("house_number") or 0) == 8:
                wealth_mode.append("钱路也会带一点合作资源、分成、佣金、他人资金或杠杆性质")
            if int(saturn.get("house_number") or 0) in {5, 8}:
                risk_parts.append("投机、短炒、情绪上头时的下注要克制，越想快钱越容易被教育")
            if 10 in dominant_houses or 9 in dominant_houses:
                wealth_mode.append("长期来看，财运跟专业能力、认知扩张、跨领域整合会绑得很紧")
            wealth_path = cn_join(wealth_mode, "、") or "职业发展和资源整合"
            return "。".join(
                part for part in [
                    f"西占看财运，这张盘不是一夜暴富型，进账主轴更像是把{wealth_path}放大成稳定收入",
                    f"要防的是：{cn_join(risk_parts, '；')}" if risk_parts else "",
                ] if part
            ) + "。"
        if "career_path" in focus and (sun or asc):
            career_options = extract_career_option_candidates(question)
            if len(career_options) >= 2:
                option_set = set(career_options)
                if option_set == {"上班", "创业", "自由职业"}:
                    return (
                        "西占放到职业模式三选一上，"
                        f"{career_option_summary(question, '上班', '自由职业', '更像先借平台和公开位置把信用与成果做大，再决定是否完全脱离组织。')}"
                        f"{' 木星在10宫，说明公开位置、头衔和平台放大量很强。' if int(jupiter.get('house_number') or 0) == 10 else ''}"
                        f"{' 第9宫被点亮，后面转成更独立的表达、咨询或跨界输出也有空间。' if 9 in dominant_houses else ''}"
                        f"{' 金星在8宫时，太早创业容易先被合作分账、资源边界和利益协同教育。' if int(venus.get('house_number') or 0) == 8 else ''}"
                    ).strip()
                if option_set == {"上班", "自由职业", "自己接项目"}:
                    return (
                        "西占放到这组三选一上，"
                        f"{career_option_summary(question, '上班', '自由职业', '自己接项目不是不能做，但它更适合放在已有口碑、稳定客户和清晰边界之后。')}"
                        f"{' 木星在10宫，说明公开位置、头衔和平台放大量很强。' if int(jupiter.get('house_number') or 0) == 10 else ''}"
                        f"{' 第9宫被点亮，后面转成更独立的表达、咨询或跨界输出也有空间。' if 9 in dominant_houses else ''}"
                        f"{' 金星在8宫时，太早独立接项目容易先碰到分账、边界和资源纠缠。' if int(venus.get('house_number') or 0) == 8 else ''}"
                    ).strip()
                if option_set == {"销售", "咨询", "自己接项目"}:
                    preferred = "咨询" if 9 in dominant_houses else "销售"
                    secondary = "销售" if preferred == "咨询" else "咨询"
                    return (
                        "西占放到这组三选一上，"
                        f"{career_option_summary(question, preferred, secondary, '自己接项目不是不能做，但它更适合放在已有口碑和稳定客户之后。')}"
                        f"{' 这张盘很适合把认知升级、专业表达和对外呈现变成职业价值。' if 9 in dominant_houses else ''}"
                        f"{' 木星10宫也让你做结果导向、要对外被看见的销售或商务角色时不算吃亏。' if int(jupiter.get('house_number') or 0) == 10 else ''}"
                        f"{' 真正的风险在金星8宫，太早独立接项目容易先碰到分账、边界和资源纠缠。' if int(venus.get('house_number') or 0) == 8 else ''}"
                    ).strip()
            path_parts = []
            risk_parts = []
            if int(jupiter.get("house_number") or 0) == 10:
                path_parts.append("事业放大量很强，适合把可见成果做出来，越公开越有加成")
            if 9 in dominant_houses:
                path_parts.append("职业发展和认知升级、跨领域学习、对外表达绑得很紧")
            if int(saturn.get("house_number") or 0) == 5:
                risk_parts.append("创意和执行之间容易自己卡自己，越想一步到位越拖进度")
            if int(venus.get("house_number") or 0) == 8:
                risk_parts.append("项目里容易卷入资源置换、合作分账或利益边界问题")
            return "。".join(
                part for part in [
                    (
                        f"西占看事业，这张盘的本命核心是太阳{sun or '未明'}、月亮{moon or '未明'}、上升{asc or '未明'}，"
                        "职业路线更像靠专业表达、外部认可和阶段性成果往上走，不是闷头熬年限的路线"
                    ) if (sun or moon or asc) else "西占看事业，这张盘更像靠专业表达、外部认可和阶段性成果往上走，不是闷头熬年限的路线",
                    "；".join(path_parts) if path_parts else "",
                    f"要注意的是：{cn_join(risk_parts, '；')}" if risk_parts else "",
                ] if part
            ) + "。"
        if "relationship_topic" in focus and (venus or moon or asc):
            relation_parts = []
            caution_parts = []
            if int(venus.get("house_number") or 0) == 8:
                relation_parts.append("关系一旦认真就会比较深，容易牵扯共同资源、情绪绑定和信任议题")
            if moon:
                relation_parts.append(f"月亮{moon}说明你在亲密关系里既要情绪空间，也要能看见彼此成长")
            if asc:
                relation_parts.append(f"上升{asc}让你挑人时会看细节、看稳定度，不太容易被表面热情长期说服")
            if int(saturn.get("house_number") or 0) in {5, 7, 8}:
                caution_parts.append("感情推进节奏别太急，慢一点反而能筛出真正靠谱的人")
            return "。".join(
                part for part in [
                    "西占看婚姻，这张盘不是轻飘飘的恋爱盘，真正进入关系后会很看深度、承诺和现实配合",
                    "；".join(relation_parts) if relation_parts else "",
                    "对象类型上，更适合稳定、讲细节、愿意共同处理现实问题的人",
                    f"要防的是：{cn_join(caution_parts, '；')}" if caution_parts else "",
                ] if part
            ) + "。"
        if sun and moon and asc:
            return f"西洋占星看，本命核心是太阳{sun}、月亮{moon}、上升{asc}，性格与行动风格都较鲜明。"

    if key == "vedic_astrology":
        derived = result.get("derived_factors") or {}
        focus = question_topic_focus(question)
        lagna = translate_western_sign((derived.get("lagna") or {}).get("sign_full"))
        nakshatra = translate_nakshatra((derived.get("moon_nakshatra") or {}).get("name"))
        lord = ((derived.get("lagna_lord") or {}).get("planet") or "").strip()
        house = ((derived.get("lagna_lord") or {}).get("house") or "")
        whole_sign = derived.get("whole_sign_houses") or {}
        dusthana = derived.get("dusthana_planets") or []
        if "wealth" in focus and lagna:
            wealth_sign = translate_western_sign(str(whole_sign.get("2") or ""))
            eleventh_sign = translate_western_sign(str(whole_sign.get("11") or ""))
            caution = "，但8宫、6宫带来的债务、消耗和回款拖延也要防" if dusthana else ""
            return (
                f"吠陀看财运，{lagna}上升的人，这盘的财路更适合靠第2宫{wealth_sign or '未明'}的稳定积累，"
                f"再叠加第11宫{eleventh_sign or '未明'}的人脉、渠道和持续进账来做大{caution}。"
            )
        if "career_path" in focus and lagna:
            career_sign = translate_western_sign(str(whole_sign.get("10") or ""))
            eleventh_sign = translate_western_sign(str(whole_sign.get("11") or ""))
            caution = "，但6宫/8宫有行星时，内耗、债务压力或职场消耗不能忽视" if dusthana else ""
            return (
                f"吠陀看事业，{lagna}上升的人，职业主轴更偏第10宫{career_sign or '未明'}的公开位置和责任承担，"
                f"再借第11宫{eleventh_sign or '未明'}的人脉网络把成果放大{caution}。"
            )
        if "relationship_topic" in focus and lagna:
            seventh_sign = translate_western_sign(str(whole_sign.get("7") or ""))
            caution = "，但盘里若牵动6宫/8宫，关系里会更怕消耗、猜疑或现实压力过重" if dusthana else ""
            return (
                f"吠陀看婚姻，{lagna}上升的人会把伴侣议题放到第7宫{seventh_sign or '未明'}上看，"
                f"你更适合能一起承担现实、又能保持成长空间的关系；对象类型上，更适合成熟、讲规则、愿意共同经营生活的人。"
                f"关系里的最大矛盾点，通常落在现实压力、情绪消耗和彼此边界不清这几个地方{caution}。"
            )
        if lagna:
            return f"吠陀盘看，命宫落在{lagna}，月宿为{nakshatra or '未明'}，命主星{translate_planet_name(lord) or '未明'}主导第{house or '未明'}宫。"

    if key == "human_design":
        derived = result.get("derived_factors") or {}
        focus = question_topic_focus(question)
        hd_type = translate_hd_type((derived.get("type") or {}).get("name"))
        authority = translate_hd_authority((derived.get("authority") or {}).get("name"))
        profile = ((derived.get("profile") or {}).get("numbers") or "").strip()
        centers = [translate_hd_center(item) for item in ((derived.get("centers") or {}).get("defined_names") or [])[:4]]
        if "wealth" in focus and hd_type:
            return (
                f"人类图放到财运上，你更像是靠{hd_type}的正确互动方式赚钱：先进入对的人和机会，再把判断力、结构力和资源配置能力换成收入。"
                f"{' 情绪权威意味着涉及大钱时不要当场拍板。' if authority == '情绪权威' else ''}"
            )
        if "career_path" in focus and hd_type:
            career_options = extract_career_option_candidates(question)
            if len(career_options) >= 2:
                option_set = set(career_options)
                if option_set == {"上班", "创业", "自由职业"}:
                    return (
                        f"人类图放到职业模式三选一上，{hd_type}这型人"
                        f"{career_option_summary(question, '上班', '自由职业', '创业不要一上来就自己扛全部变量，先在被看见、被确认价值的环境里长出稳定邀约更顺。')}"
                        f"{' 你更适合先在已有系统里被看见，再把判断力和解法变成更独立的输出。' if hd_type == '投射者' else ''}"
                        f"{' 情绪权威意味着从上班转独立，最好等情绪波动走完再定，不要在一时兴奋里跳。' if authority == '情绪权威' else ''}"
                    ).strip()
                if option_set == {"上班", "自由职业", "自己接项目"}:
                    return (
                        f"人类图放到这组三选一上，{hd_type}这型人"
                        f"{career_option_summary(question, '上班', '自由职业', '自己接项目不要一上来就把获客、成交、交付和回款都压在自己身上，先在被看见、被确认价值的环境里长出稳定邀约更顺。')}"
                        f"{' 你更适合先在已有系统里被看见，再把判断力和解法变成更独立的输出。' if hd_type == '投射者' else ''}"
                        f"{' 情绪权威意味着从上班转向独立合作时，最好等情绪波动走完再定，不要在一时兴奋里答应太满。' if authority == '情绪权威' else ''}"
                    ).strip()
                if option_set == {"组织里冲", "个人输出品牌"}:
                    return (
                        f"人类图放到这两个方向上，{hd_type}这型人"
                        f"{career_option_summary(question, '组织里冲', '个人输出品牌', '个人输出品牌更适合先当副线铺垫，等外部认可、表达结构和稳定反馈更稳后再放大。')}"
                        f"{' 你更适合先在已有系统里被看见、被确认价值，再把方法和判断力沉淀成自己的公开表达。' if hd_type == '投射者' else ' 先借已有平台把结果和位置做出来，再把个人表达往外放大，通常比一开始就单独撑品牌更顺。'}"
                        f"{' 情绪权威也提醒你，涉及离开组织、重压个人品牌这种大决策，最好等情绪波动走完再定。' if authority == '情绪权威' else ''}"
                    ).strip()
                if option_set == {"销售", "咨询", "自己接项目"}:
                    return (
                        f"人类图放到这组三选一上，{hd_type}更适合走咨询，销售次之，自己接项目放在后面。"
                        "你更适合先通过洞察问题、给出方法、被别人确认价值来接住机会，而不是一开始就把获客、成交、交付全压在自己身上。"
                        f"{' 情绪权威也提醒你，合作和接单别在情绪上头时答应。' if authority == '情绪权威' else ''}"
                    ).strip()
            return (
                f"人类图放到事业上，{hd_type}更适合在被看见、被邀请、被确认价值之后发力，"
                f"职业路径不是硬冲出来的，而是靠看准系统问题后给出解法。"
                f"{' 情绪权威意味着重大转岗、合作和签约别在情绪波峰波谷定。' if authority == '情绪权威' else ''}"
            )
        if "identity_topic" in focus and hd_type:
            tail = f" 已定义中心偏向{cn_join(centers)}。" if centers else ""
            return (
                f"人类图看你是什么样的人，核心是{hd_type}，权威为{authority or '未明'}，人格轮廓{profile or '未明'}。"
                f"你更适合先确认自己是否真被需要，再输出判断和方法，而不是为了证明自己去硬扛。{tail}"
            )
        if hd_type:
            tail = f"，已定义中心偏向{cn_join(centers)}" if centers else ""
            return f"人类图显示你是{hd_type}，权威为{authority or '未明'}，人格轮廓是{profile or '未明'}{tail}。"

    if key == "name_studies":
        used = result.get("used_inputs") or {}
        name = str(used.get("name") or "").strip()
        confidence = str(result.get("confidence") or "").strip().lower()
        bridge = (result.get("derived_factors") or {}).get("expression_bridge_number")
        generated = result.get("generated_candidates") or []
        birth_info = str(used.get("birth_info") or "").strip()
        bazi_context = ""
        if birth_info:
            parsed = parse_birth_details(birth_info)
            if parsed.birth_datetime and parsed.has_time:
                try:
                    bazi_result, status = calculate_system("bazi", {"question": birth_info})
                    if status == 200 and not bazi_result.get("error"):
                        pillars = bazi_result.get("pillars") or {}
                        day_pillar = trim_reply_text(((pillars.get("day") or {}).get("text")) or "")
                        day_master = trim_reply_text(((bazi_result.get("day_master") or {}).get("stem")) or "")
                        five_counts = bazi_result.get("five_element_counts") or {}
                        five_elements = "，".join(
                            f"{key}{value}"
                            for key, value in five_counts.items()
                            if value not in (None, "")
                        )
                        context_bits = []
                        if day_pillar:
                            context_bits.append(f"日柱是{day_pillar}")
                        if day_master:
                            context_bits.append(f"日主为{day_master}")
                        if five_elements:
                            context_bits.append(f"五行分布为{five_elements}")
                        if context_bits:
                            bazi_context = "先按出生信息粗看八字，" + "，".join(context_bits) + "。"
                except Exception:
                    bazi_context = ""
        if generated:
            top = generated[:3]
            first = top[0] if top else {}
            lead = "、".join(str(item.get("name") or "").strip() for item in top if item.get("name"))
            source = trim_reply_text(first.get("source_title") or "")
            meaning = trim_reply_text(first.get("meaning") or "").rstrip("。；;，, ")
            why = trim_reply_text(first.get("why_selected") or "").rstrip("。；;，, ")
            if meaning and why and meaning in why:
                why = why.replace(f"；{meaning}", "").replace(meaning, "").strip("；，,。. ")
            style_tags = [
                translate_name_style_tag(str(item))
                for item in (first.get("style_tags") or [])
                if str(item).strip()
            ]
            tag_text = f"，风格偏{'、'.join(style_tags[:3])}" if style_tags else ""
            if lead:
                summary = f"姓名学本地筛名后，当前更推荐：{lead}。首选是{name or first.get('name', '未明')}"
                if bazi_context:
                    summary = f"{bazi_context}{summary}"
                if source:
                    summary += f"，经典出处落在{source}"
                if meaning:
                    summary += f"，名字主旨是{meaning}"
                if why:
                    summary += f"。之所以把它排在前面，是因为{why}"
                if tag_text:
                    summary += tag_text
                summary = re.sub(r"。[，,]", "。", summary)
                summary = re.sub(r"。{2,}", "。", summary)
                return summary + "。"
        if confidence == "medium":
            source = trim_reply_text((((result.get("derived_factors") or {}).get("classical_source") or {}).get("title") or ""))
            meaning = trim_reply_text((((result.get("derived_factors") or {}).get("classical_source") or {}).get("meaning") or "")).rstrip("。；;，, ")
            signals = " ".join(
                trim_reply_text(item)
                for item in (result.get("supporting_signals") or [])
                if trim_reply_text(item)
            )
            parts = [f"姓名学看，{name or '这个名字'}在当前用途下可用，但优缺点并存。"]
            if source:
                parts.append(f"它能对到本地语料里的经典出处：{source}。")
            if meaning:
                parts.append(f"名字意旨偏向{meaning}。")
            if "声调走向相对偏平" in signals:
                parts.append("读感整体偏清雅平稳，起伏感不算强。")
            elif "声调走向有平仄变化" in signals:
                parts.append("读音里有平仄起伏，叫起来会更顺口一些。")
            if any(token in question for token in ("男孩", "男宝宝", "男宝")) and any(token in name for token in ("清", "和", "宁", "安")):
                parts.append("如果用于男孩正式姓名，整体更偏清秀温和路线，不是特别锋利外放的类型。")
            if any(token in question for token in ("女孩", "女宝宝", "女宝")):
                parts.append("如果用于女孩正式姓名，整体气质会更柔和干净。")
            parts.append(f"拼音桥接数为{bridge or '未明'}。")
            return "".join(parts)
        if confidence == "low":
            return f"姓名学看，{name or '这个名字'}在当前用途下阻力偏多，建议继续比较备选名。"
        if name:
            return f"姓名学看，{name}在当前用途下整体适配度较高。"

    if key == "tarot":
        derived = result.get("derived_factors") or {}
        cards = derived.get("cards") or []
        majors = int(derived.get("major_arcana_count") or 0)
        reversed_count = int(derived.get("reversed_count") or 0)
        lead_cards = []
        for item in cards[:3]:
            english_name = str(item.get("name") or "").strip()
            card_name = translate_tarot_card_name(english_name.title())
            orientation = "逆位" if item.get("orientation") == "reversed" else "正位"
            if card_name:
                lead_cards.append(f"{card_name}{orientation}")
        if lead_cards:
            focus = question_topic_focus(question)
            if "relationship_topic" in focus:
                action = "更建议你先观察对方的实际回应，再决定要不要明显加码主动。" if reversed_count >= 1 else "可以适度主动，但要以对方是否给出稳定回应为前提。"
                base = "这段关系接下来一个月不是完全没有推进空间，但节奏不会特别顺，先热后卡的概率更高。" if reversed_count >= 1 else "这段关系接下来一个月有继续靠近的空间，关键在于把节奏放稳。"
                structure = "牌面里既有新开始和连接意愿，也有旧伤、顾虑或防御反应没有完全过去。" if majors >= 1 else "牌面更像是互动层面的磨合，不是彻底无望。"
                return f"塔罗牌面落在 {'、'.join(lead_cards)}。{base}{structure}{action}"
            if "career_path" in focus:
                action = "下一步更适合先确认边界、拆掉卡点，再推进关键动作。" if reversed_count >= 1 else "下一步可以推进，但要先把资源和节奏对齐。"
                structure = "这件事更偏结构性转折，不是小波动。" if majors >= max(1, len(cards) // 2) else "这更像是阶段推进题，重心在执行节奏。"
                return f"塔罗牌面落在 {'、'.join(lead_cards)}。{structure}{action}"
            if "wealth" in focus:
                action = "眼下不适合情绪化下注，先看回款、成本和风险控制。" if reversed_count >= 1 else "钱路不是没有，但更适合走稳一点的路径。"
                structure = "这组牌更像在说收入路径和风险控制。" if majors >= 1 else "这更像是在提醒你控制节奏和判断。"
                return f"塔罗牌面落在 {'、'.join(lead_cards)}。{structure}{action}"
            trend = []
            if majors >= max(1, len(cards) // 2):
                trend.append("这件事更偏结构性转折，不是小波动。")
            if reversed_count >= max(1, len(cards) // 2):
                trend.append("阻滞、延后或内在拉扯比较明显。")
            if not trend:
                trend.append("局面在推进，但关键看你怎么接牌意去行动。")
            return f"塔罗牌面先落在 {'、'.join(lead_cards)}。{' '.join(trend)}"

    if key == "ziwei_doushu":
        derived = result.get("derived_factors") or {}
        focus = explicit_coverage_focus(question)
        ming = ((derived.get("key_palaces") or {}).get("命宫") or {})
        wealth = ((derived.get("key_palaces") or {}).get("财帛") or {})
        career = ((derived.get("key_palaces") or {}).get("官禄") or {})
        spouse = ((derived.get("key_palaces") or {}).get("夫妻") or {})
        cycle = derived.get("current_cycles") or {}
        stars = cn_join(ming.get("major_stars") or [])
        cycle_focus = ((derived.get("current_cycles") or {}).get("decadal_focus") or "").strip()
        requested_palaces = [token for token in ("命宫", "财帛宫", "官禄宫", "夫妻宫") if token in question]
        if len(requested_palaces) >= 2:
            wealth_stars = cn_join(wealth.get("major_stars") or [])
            career_stars = cn_join(career.get("major_stars") or [])
            spouse_stars = cn_join(spouse.get("major_stars") or [])
            spouse_minors = cn_join(spouse.get("minor_stars") or [])
            palace_parts: list[str] = []
            if "命宫" in requested_palaces:
                palace_parts.append(f"命宫主星为{stars or '未明'}")
            if "财帛宫" in requested_palaces:
                palace_parts.append(f"财帛宫主星为{wealth_stars or '空宫'}")
            if "官禄宫" in requested_palaces:
                palace_parts.append(f"官禄宫主星为{career_stars or '空宫'}")
            if "夫妻宫" in requested_palaces:
                palace_parts.append(f"夫妻宫主星为{spouse_stars or '主星不守'}")
            structural_note = "这几个宫位放在一起看，主轴不是分开跑的，而是个人状态、赚钱结构和关系节奏彼此牵动。"
            if "财帛宫" in requested_palaces and "夫妻宫" in requested_palaces:
                structural_note = "这几个宫位放在一起看，钱路和关系都受个人主轴牵动，越是想走得稳，越要先把自己的位置和节奏定住。"
            action_note = "这盘更适合先把职业与收入结构做稳，再谈关系深绑定。"
            if "官禄宫" in requested_palaces and "夫妻宫" in requested_palaces:
                action_note = "这盘更适合先把事业位置和生活节奏理顺，再推进更深的关系承诺。"
            return (
                f"紫微斗数看，{'，'.join(palace_parts)}。"
                f"{structural_note}{action_note}"
                f"{' 感情里的现实磨合点，多半会落在节奏、投入与生活安排上。' if '夫妻宫' in requested_palaces else ''}"
                f"{' 夫妻宫辅星还带' + spouse_minors + '。' if spouse_minors else ''}"
            )
        if "wealth" in focus:
            wealth_stars = cn_join(wealth.get("major_stars") or [])
            career_stars = cn_join(career.get("major_stars") or [])
            cycle_focus = cycle.get("decadal_focus") or "未明"
            risk_note = "财帛宫还带地劫，赚得到也更要防折腾、错配和临门一脚掉链子。" if "地劫" in cn_join(wealth.get("minor_stars") or []) else ""
            return (
                f"紫微看财运，财帛宫主星是{wealth_stars or '空宫'}，官禄宫主星是{career_stars or '空宫'}，说明钱不是凭空掉下来，"
                f"更像要靠职业路径、脑力策划、项目运作去转出来。当前大限重心落在{cycle_focus or '未明'}，{risk_note or '这一阶段更适合先把赚钱结构做稳，再谈放大。'}"
            )
        if "career_path" in focus and "space" in normalized_question_topics(question, tags) and "priority" in question_requested_facets(question):
            move_stars = cn_join((((derived.get("key_palaces") or {}).get("田宅") or {}).get("major_stars") or []))
            return (
                f"紫微放到换工作和搬家哪个先做这类题上，当前大限重心落在{cycle_focus}，主轴还在个人位置与主线整理。"
                f"田宅宫主星是{move_stars or '未明'}，说明住处议题会被带起来，但更像是在事业主线定住之后再承接。"
                "所以顺序上更偏先把工作方向、机会窗口和角色定位理顺，再处理搬家。"
            )
        if "career_path" in focus:
            career_options = extract_career_option_candidates(question)
            if len(career_options) >= 2:
                option_set = set(career_options)
                if option_set == {"上班", "创业", "自由职业"}:
                    return (
                        f"紫微放到职业模式三选一上，当前大限重心落在{cycle_focus}，"
                        f"{career_option_summary(question, '上班', '自由职业', '创业更像后置题，先把位置、角色和资源线理顺更重要。')}"
                        f"官禄宫主星是{cn_join(career.get('major_stars') or []) or '空宫'}，说明这阶段更看你能不能先把位置坐稳。"
                    )
                if option_set == {"上班", "自由职业", "自己接项目"}:
                    return (
                        f"紫微放到这组三选一上，当前大限重心落在{cycle_focus}，"
                        f"{career_option_summary(question, '上班', '自由职业', '自己接项目会被资源、现实安排和稳定度要求牵扯，放在后面更稳。')}"
                        f"官禄宫主星是{cn_join(career.get('major_stars') or []) or '空宫'}，说明这阶段更看你能不能先把位置坐稳，再把独立合作一点点放大。"
                    )
                if option_set == {"销售", "咨询", "自己接项目"}:
                    return (
                        f"紫微放到这组三选一上，当前大限重心落在{cycle_focus}，"
                        f"{career_option_summary(question, '咨询', '销售', '自己接项目会被资源、现实安排和稳定度要求牵扯，放在后面更稳。')}"
                        f"官禄宫主星是{cn_join(career.get('major_stars') or []) or '空宫'}，更像先把角色价值和专业位置做出来，再谈完全独立接案。"
                    )
            career_stars = cn_join(career.get("major_stars") or [])
            return (
                f"紫微看事业，官禄宫主星是{career_stars or '空宫'}，当前大限重心落在{cycle_focus}。"
                f"这说明职业上不是单看一时机会，而是要看你能不能把位置、职责和长期路径接稳。"
            )
        if "relationship_topic" in focus:
            spouse_stars = cn_join(spouse.get("major_stars") or [])
            spouse_minors = cn_join(spouse.get("minor_stars") or [])
            note = "夫妻宫带天马，关系里容易出现异地、奔波或节奏不一致的情况。" if "天马" in spouse_minors else ""
            return (
                f"紫微看婚姻，夫妻宫{spouse_stars or '主星不守'}，辅星落点为{spouse_minors or '未明'}。"
                f"感情不是不能成，但更看现实节奏、稳定度和能不能一起过日子。"
                f"对象类型上，更适合务实、能落地、生活节奏能对齐的人；关系里的矛盾点，多半出在节奏不同、距离奔波或双方谁都不肯先让一步。{note}"
            )
        if "identity_topic" in focus and stars:
            body_palace = "身宫落在福德，内在思路更重体验后的总结。" if bool(((derived.get("key_palaces") or {}).get("福德") or {}).get("is_body_palace")) else ""
            return f"紫微看个性，命宫主星为{stars}，当前阶段重心落在{cycle_focus or '未明'}。你不是完全外放型，更像先观察、再定调、再出手。{body_palace}".strip()
        if stars:
            return f"紫微斗数看，命宫主星为{stars}，当前大限重心落在{cycle_focus or '未明'}。"

    if key == "qizheng_siyu":
        derived = result.get("derived_factors") or {}
        focus = explicit_coverage_focus(question)
        seven = derived.get("seven_governors") or {}
        sun_sign = translate_western_sign(((seven.get("Sun") or {}).get("sign_full") or ""))
        luohou = ((derived.get("four_remainders") or {}).get("Luohou") or {}).get("house_number")
        ziqi = ((derived.get("four_remainders") or {}).get("Ziqi") or {}).get("house_number")
        def translated_house_list(items: list[str]) -> str:
            return cn_join([translate_planet_name(item) for item in items if str(item).strip()])
        if all(token in question for token in ("财帛宫", "官禄宫", "夫妻宫")):
            mapping = derived.get("question_house_mapping") or {}
            wealth_house = translated_house_list(mapping.get("wealth_house") or [])
            career_house = translated_house_list(mapping.get("career_house") or [])
            relation_house = translated_house_list(mapping.get("relationship_house") or [])
            return (
                f"七政四余放到这题里，财帛位牵动的是{wealth_house or '未见主星直守'}，官禄位牵动的是{career_house or '未见主星直守'}，关系位牵动的是{relation_house or '未见主星直守'}。"
                f"这说明钱、事业和关系不是分开跑的，现实资源分配会直接影响关系稳定度，反过来关系投入也会牵动事业节奏。"
            )
        if "wealth" in focus:
            mapping = derived.get("question_house_mapping") or {}
            wealth_house = translated_house_list(mapping.get("wealth_house") or [])
            career_house = translated_house_list(mapping.get("career_house") or [])
            return (
                f"七政四余放到财运上，财帛位当前牵动的是{wealth_house or '未见主星直守'}，官禄位牵动的是{career_house or '未见主星直守'}，"
                f"说明钱路仍然要通过职业位置、项目结果和对外资源来带，不是纯偏财一路。"
            )
        if "career_path" in focus:
            mapping = derived.get("question_house_mapping") or {}
            career_house = translated_house_list(mapping.get("career_house") or [])
            angular = cn_join([translate_planet_name(item) for item in (derived.get("angular_governors") or [])[:3]])
            return (
                f"七政四余看事业，牵动官禄位的主力是{career_house or '未见主星直守'}，角宫主事星偏向{angular or '未明'}。"
                f"事业推进更适合靠位置提升、成果外显和关键资源到位来完成，不是闷头熬出来的。"
            )
        if "relationship_topic" in focus:
            mapping = derived.get("question_house_mapping") or {}
            relation_house = translated_house_list(mapping.get("relationship_house") or [])
            return (
                f"七政四余看感情，夫妻/关系位当前牵动的是{relation_house or '未见主星直守'}。"
                f"这说明关系里会比较看互动强度和现实牵连，不是只靠感觉就能稳定下来的类型。"
                f"对象类型上更适合有行动力、能直接回应关系需求的人；矛盾点通常在情绪拉扯和现实投入是否对等。"
            )
        if "identity_topic" in focus and sun_sign:
            angular = cn_join([translate_planet_name(item) for item in (derived.get("angular_governors") or [])[:3]])
            return f"七政四余看个性，日曜落在{sun_sign}，主事星偏向{angular or '未明'}。你身上比较强的是把感觉、行动和判断直接带到现实里的倾向。"
        if sun_sign:
            return f"七政四余看，日曜落在{sun_sign}，罗喉在第{luohou or '未明'}宫，紫气在第{ziqi or '未明'}宫。"

    primary = trim_reply_text(result.get("primary_finding"))
    if primary:
        return translate_signal_text(primary)

    judgements = result.get("judgement_candidates")
    if isinstance(judgements, list) and judgements:
        return translate_signal_text(trim_reply_text(judgements[0]))

    summary = result.get("summary")
    if isinstance(summary, dict):
        note = trim_reply_text(summary.get("note"))
        if note:
            return translate_signal_text(note)
    elif isinstance(summary, str):
        note = trim_reply_text(summary)
        if note:
            return translate_signal_text(note)

    return f"{SYSTEM_LABELS.get(pack.key, pack.key)} 已完成本地计算，但当前版本还没有产出更细的直断语句。"


def legacy_detail_text(pack: DossierPack, result: dict[str, Any] | None, question: str) -> str:
    if not result:
        return ""

    key = pack.key
    parsed = parse_birth_details(question)

    if key == "bazi":
        if parsed.birth_datetime and parsed.has_time:
            chart = result
            pillar_text = " / ".join(chart["pillars"][name]["text"] for name in ["year", "month", "day", "hour"])
            day_master = chart["day_master"]
            five_elements = ", ".join(
                f"{element}:{count}" for element, count in chart["five_element_counts"].items()
            )
            calendar_note = "已识别农历生日并换算为阳历起八字。" if parsed.calendar == "lunar" else ""
            return f"{calendar_note}八字排盘为：{pillar_text}。日主是{day_master['stem']}，五行分布为 {five_elements}。".strip()
        if parsed.birth_datetime and not parsed.has_time:
            return "已经识别到生日，但没有具体时辰，暂时无法补出时柱。"

    if key == "numerology":
        derived = result.get("derived_factors") or {}
        expression_number = derived.get("expression_number")
        if expression_number:
            return f"表达数落在{expression_number}，这层更偏你把内在主题往外呈现时的语言和风格。"
        return ""

    if key == "yijing_and_symbolism":
        derived = result.get("derived_factors") or {}
        base_name = ((derived.get("base_hexagram") or {}).get("name") or "").strip()
        changed_name = ((derived.get("changed_hexagram") or {}).get("name") or "").strip()
        bits = []
        if base_name and changed_name:
            bits.append(
                f"本卦为{translate_hexagram_name(base_name)}，变卦为{translate_hexagram_name(changed_name)}。"
            )
        judgements = result.get("judgement_candidates") or []
        if judgements:
            bits.append(translate_signal_text(trim_reply_text(judgements[0])) + "。")
        return " ".join(bits)

    if key == "liuyao_and_meihua":
        derived = result.get("derived_factors") or {}
        relation = str(((derived.get("body_use_relation") or {}).get("relation")) or "")
        body = translate_trigram((derived.get("body_trigram") or {}).get("name") if isinstance(derived.get("body_trigram"), dict) else derived.get("body_trigram"))
        use = translate_trigram((derived.get("use_trigram") or {}).get("name") if isinstance(derived.get("use_trigram"), dict) else derived.get("use_trigram"))
        relation_text = liuyao_relation_verdict(relation)
        structure = derived.get("yijing_structure") or {}
        base_name = ((structure.get("base_hexagram") or {}).get("name") or "").strip()
        changed_name = ((structure.get("changed_hexagram") or {}).get("name") or "").strip()
        parts = []
        if body and use:
            parts.append(f"体卦为{body}，用卦为{use}。")
        if base_name and changed_name:
            parts.append(f"本卦为{translate_hexagram_name(base_name)}，变卦为{translate_hexagram_name(changed_name)}。")
        if relation_text:
            parts.append(relation_text)
        signals = result.get("supporting_signals") or []
        if signals:
            parts.append(translate_signal_text(trim_reply_text(signals[0])) + "。")
        return " ".join(part for part in parts if part)

    if key == "date_selection":
        derived = result.get("derived_factors") or {}
        ranked = derived.get("ranked_candidates") or []
        used = result.get("used_inputs") or {}
        event_label = {
            "move": "搬家",
            "wedding": "婚嫁",
            "contract": "签约",
            "travel": "出行",
            "general": "当前事项",
        }.get(str(used.get("event_type") or "").strip(), "当前事项")
        element_map = {
            "wood": "木",
            "fire": "火",
            "earth": "土",
            "metal": "金",
            "water": "水",
        }
        if len(ranked) >= 2:
            best = ranked[0]
            runner = ranked[1]
            best_score = int(best.get("score") or 0)
            runner_score = int(runner.get("score") or 0)
            gap = best_score - runner_score
            day_ganzhi = trim_reply_text((runner.get("ganzhi") or {}).get("day"))
            day_element = element_map.get(str(runner.get("day_element") or "").strip(), "")
            detail_bits = []
            if day_ganzhi:
                detail_bits.append(f"{runner.get('date')}是{day_ganzhi}日")
            if day_element:
                detail_bits.append(f"五行偏{day_element}")
            detail_text = "，".join(detail_bits) if detail_bits else f"{runner.get('date')}在局部规则上略吃亏"
            if gap > 0:
                return (
                    f"次选是{runner.get('date')}，得分{runner_score}，和首选只差{gap}分；"
                    f"{detail_text}，对{event_label}这件事的本地权重少了这{gap}分。"
                )
            return f"{runner.get('date')}和首选几乎并列，差异主要落在{detail_text}这一层。"
        if ranked:
            best = ranked[0]
            day_ganzhi = trim_reply_text((best.get("ganzhi") or {}).get("day"))
            if day_ganzhi:
                return f"{best.get('date')}对应{day_ganzhi}日，这一轮是按历法结构和事项权重综合排出来的。"
        return ""

    if key in {
        "qimen_dunjia",
        "liu_ren",
        "physiognomy",
        "daoist_arts",
        "alchemy_and_hermeticism",
        "modern_esotericism",
        "fengshui",
        "name_studies",
        "kabbalah",
        "onmyodo",
        "ziwei_doushu",
        "qizheng_siyu",
        "western_astrology",
        "vedic_astrology",
        "human_design",
    }:
        if key == "name_studies":
            derived = result.get("derived_factors") or {}
            source = (derived.get("classical_source") or {}) if isinstance(derived.get("classical_source"), dict) else {}
            bits = []
            bridge_number = derived.get("expression_bridge_number")
            if source.get("quote"):
                bits.append(f"取意原句：{source.get('quote')}。")
            elif source.get("title"):
                bits.append(f"经典出处可落在{source.get('title')}。")
            birth_screening = derived.get("birth_screening") or {}
            if birth_screening and birth_screening.get("favored_elements"):
                bits.append(
                    f"出生信息辅助筛选更偏向 {'、'.join(birth_screening.get('favored_elements') or [])} 方向。"
                )
            if bridge_number and str(result.get("confidence") or "").strip().lower() != "medium":
                bits.append(f"拼音桥接数落在{bridge_number}。")
            return " ".join(bit for bit in bits if bit)
        if key == "western_astrology":
            derived = result.get("derived_factors") or {}
            dominant_houses = derived.get("dominant_houses") or []
            aspects = derived.get("major_aspects") or []
            detail_parts: list[str] = []
            if dominant_houses:
                detail_parts.append(f"重点宫位实际集中在第{cn_join([str(item) for item in dominant_houses[:3]], '、')}宫。")
            if aspects:
                lead = aspects[0]
                between = trim_reply_text(lead.get("between"))
                aspect = trim_reply_text(lead.get("aspect"))
                orbit = lead.get("orbit")
                if between and aspect:
                    aspect_map = {
                        "sextile": "六合",
                        "trine": "拱",
                        "square": "刑",
                        "opposition": "冲",
                        "conjunction": "合",
                    }
                    aspect_name = aspect_map.get(aspect, aspect)
                    detail_parts.append(f"当前最紧的主要相位是{between}形成{aspect_name}{f'，容许度约{orbit}°' if orbit is not None else ''}。")
            if detail_parts:
                return " ".join(detail_parts)
        if key == "vedic_astrology":
            derived = result.get("derived_factors") or {}
            lagna = translate_western_sign((derived.get("lagna") or {}).get("sign_full"))
            nakshatra = translate_nakshatra((derived.get("moon_nakshatra") or {}).get("name"))
            lord = ((derived.get("lagna_lord") or {}).get("planet") or "").strip()
            house = ((derived.get("lagna_lord") or {}).get("house") or "")
            if lagna:
                return f"命宫落在{lagna}，月宿为{nakshatra or '未明'}，命主星{translate_planet_name(lord) or '未明'}主导第{house or '未明'}宫。"
        if key == "human_design":
            derived = result.get("derived_factors") or {}
            type_info = (derived.get("type") or {})
            strategy = trim_reply_text(type_info.get("strategy"))
            definition = trim_reply_text(derived.get("definition"))
            dominant = (((derived.get("circuit_analysis") or {}).get("dominant")) or {})
            dominant_name = trim_reply_text(dominant.get("name"))
            dominant_keywords = trim_reply_text(dominant.get("keywords"))
            strategy_text = {
                "Wait for the Invitation": "等待邀请",
                "Wait to Respond": "等待回应",
                "Inform before acting": "行动前先告知",
                "Wait a lunar cycle": "等待一个月亮周期",
            }.get(strategy, strategy)
            definition_text = {
                "Single Definition": "单一定义",
                "Split Definition": "分裂定义",
                "Triple Split Definition": "三分定义",
                "Quadruple Split Definition": "四分定义",
                "No Definition": "无定义",
            }.get(definition, definition)
            dominant_name_text = {
                "Individual": "个体回路",
                "Collective": "集体回路",
                "Tribal": "部族回路",
                "Integration": "整合回路",
            }.get(dominant_name, dominant_name)
            parts: list[str] = []
            if strategy_text or definition_text:
                if strategy_text and definition_text:
                    parts.append(f"策略是{strategy_text}，定义为{definition_text}。")
                elif strategy_text:
                    parts.append(f"策略是{strategy_text}。")
                else:
                    parts.append(f"定义为{definition_text}。")
            if dominant_name:
                parts.append(
                    f"主导回路偏向{dominant_name_text}{f'，关键词是{dominant_keywords}' if dominant_keywords else ''}。"
                )
            if parts:
                return " ".join(parts)
        if key == "fengshui":
            derived = result.get("derived_factors") or {}
            sector = translate_direction_sector(str(derived.get("facing_sector") or ""))
            kua = derived.get("occupant_kua")
            if kua:
                quality = next((name for name, direction in (derived.get("eight_mansions") or {}).items() if direction == derived.get("facing_sector")), "")
                quality_text = {
                    "sheng_qi": "生气位，偏利长期发展。",
                    "tian_yi": "天医位，偏利安稳与修复。",
                    "yan_nian": "延年位，偏利稳定与关系和合。",
                    "fu_wei": "伏位，偏利守成与安住。",
                    "jue_ming": "绝命位，不宜长期硬住。",
                    "wu_gui": "五鬼位，波动和干扰偏多。",
                    "liu_sha": "六煞位，容易有杂扰与消耗。",
                    "huo_hai": "祸害位，小问题会比较多。",
                }.get(quality, "")
                return f"真正拉开差别的是八宅配向层：命卦{kua}对这套向首先落在{quality_text or '仍要继续细看户型与飞星。'}"
            parts = []
            if sector:
                parts.append("这一步只完成了向首层粗筛，真正会改长期居住结论的，是入户门、主卧、床位和灶位之间的动线。")
            period_label = trim_reply_text((((derived.get("period") or {})).get("label")) or "")
            if not period_label or period_label == "unknown":
                parts.append("建成年份还没进来，所以运盘层暂时还没有压进去。")
            if parts:
                return " ".join(parts)
        if key == "alchemy_and_hermeticism":
            derived = result.get("derived_factors") or {}
            operations = [translate_alchemy_term(str(item).strip()) for item in (derived.get("operations") or []) if str(item).strip()]
            symbols = [translate_alchemy_term(str((item or {}).get("name") or "").strip()) for item in (derived.get("symbols") or []) if str((item or {}).get("name") or "").strip()]
            parts: list[str] = []
            if operations:
                parts.append(f"这轮具体动作词更偏{cn_join(operations[:2])}。")
            if "汞性原则" in symbols and "盐性原则" in symbols:
                parts.append("汞性原则和盐性原则同时被牵动，说明这一步不是单纯发散，而是边拆旧边找能承住它的结构。")
            elif symbols:
                parts.append(f"当前被牵动的核心符号是{cn_join(symbols[:3])}。")
            if parts:
                return " ".join(parts)
        if key == "kabbalah":
            derived = result.get("derived_factors") or {}
            secondary_nodes = derived.get("secondary_nodes") or []
            topic_domains = set(derived.get("topic_domains") or [])
            domain_text_map = {
                "career": "事业",
                "relationship": "关系",
                "identity": "自我定位",
                "wealth": "资源与财务",
            }
            parts: list[str] = []
            domain_text = cn_join([domain_text_map[item] for item in ("career", "relationship", "identity", "wealth") if item in topic_domains])
            if domain_text:
                parts.append(f"这轮题面主要牵动的是{domain_text}维度。")
            if secondary_nodes:
                extra_parts = []
                for item in secondary_nodes[:2]:
                    name = str(item.get("canonical_name") or "").strip()
                    raw_title = str(item.get("title") or "").strip()
                    if not name:
                        continue
                    title_suffix = f"（{translate_kabbalah_title(raw_title)}）" if raw_title else ""
                    extra_parts.append(f"{name}{title_suffix}")
                if extra_parts:
                    parts.append(f"次级承接位同时落在{'；'.join(extra_parts)}，说明这题不只是看中心节点亮不亮，还要看下面有没有结构把它接住。")
            if parts:
                return " ".join(parts)
        if key == "onmyodo":
            derived = result.get("derived_factors") or {}
            day_info = derived.get("day_info") or {}
            relation = str(derived.get("direction_relation") or "").strip()
            score = int(derived.get("score") or 0)
            direction = translate_direction_sector(str(day_info.get("year_direction") or ""))
            if score:
                if score >= 65:
                    verdict = "这个方向与时点整体偏顺，可以走。"
                elif score >= 45:
                    verdict = "这个方向和时点不算最好，但还能用，重在别把行程压得太满。"
                else:
                    verdict = "这个方向与时点偏不利，若能绕开或改期会更稳。"
                relation_text = {
                    "day generates direction": "当天气机对这个方向有扶助。",
                    "same element": "当天与方向同气，事情更看你自己怎么安排行程。",
                    "day restrains direction": "当天气机对这个方向有压制，容易出现折返、耽搁或心态烦躁。",
                }.get(relation, "")
                return f"阴阳道按当前日时看，{verdict}{relation_text}{f' 当日年方位锚点落在{direction}。' if direction else ''}"
        if key == "modern_esotericism":
            derived = result.get("derived_factors") or {}
            source_hits = [trim_reply_text(item) for item in ((derived.get("source_family") or {}).get("hits") or []) if trim_reply_text(item)]
            concept_hits = [trim_reply_text(item) for item in ((derived.get("concept_family") or {}).get("hits") or []) if trim_reply_text(item)]
            domain_weights = derived.get("domain_weights") or {}
            parts: list[str] = []
            if concept_hits or source_hits:
                hit_parts = []
                if concept_hits:
                    hit_parts.append(f"自我整理这头命中的线索是{cn_join(concept_hits[:3])}")
                if source_hits:
                    hit_parts.append(f"能量实践这头命中的线索是{cn_join(source_hits[:3])}")
                parts.append("；".join(hit_parts) + "。")
            if int(domain_weights.get("psychological") or 0) > 0 and not any(int(domain_weights.get(name) or 0) > int(domain_weights.get("psychological") or 0) for name in ("religious", "commercial", "wellness")):
                parts.append("领域重心明显偏心理整理，不是宗教归依或商业包装。")
            elif int(domain_weights.get("commercial") or 0) > 0:
                parts.append("这轮已经带出商业包装或变现色彩，现实承诺和边界要先分开。")
            if parts:
                return " ".join(parts)
        if key == "tarot":
            derived = result.get("derived_factors") or {}
            cards = derived.get("cards") or []
            lead_cards = []
            for item in cards[:3]:
                english_name = str(item.get("name") or "").strip()
                card_name = translate_tarot_card_name(english_name.title())
                orientation = "逆位" if item.get("orientation") == "reversed" else "正位"
                if card_name:
                    lead_cards.append(f"{card_name}{orientation}")
            if lead_cards:
                return f"塔罗牌面为：{'、'.join(lead_cards)}。"
        primary = trim_reply_text(result.get("primary_finding"))
        return f"{primary}." if primary else ""

    return ""


def local_system_answer(pack: DossierPack, question: str, tags: set[str]) -> dict[str, Any]:
    mode = pack_mode(pack.key)
    evidence = []
    for part in ["root", "sources", "controversies"]:
        evidence.extend(extract_evidence(pack.files[part], limit=1))
    if pack.calculator.exists():
        evidence.extend(extract_evidence(pack.calculator, limit=1))
    evidence = evidence[:2]
    evidence_text = "\uff1b".join(evidence) if evidence else pack.summary

    confidence = {
        "deep": "high",
        "seeded": "medium",
        "missing": "low",
    }.get(pack.status, "medium")

    result: dict[str, Any] | None = None
    used_local_calculation = False
    if calculator_implemented(pack.key):
        try:
            payload = build_compute_payload_for_question(pack, question)
            computed, status = calculate_system(pack.key, payload)
            if status == 200 and not computed.get("error"):
                result = computed
                used_local_calculation = True
                confidence = str(computed.get("confidence") or confidence)
        except Exception:
            result = None

    missing_inputs = merge_missing_inputs(pack, question, result)
    verdict = summarize_local_result(pack, result, question, tags) if result else (
        f"{SYSTEM_LABELS.get(pack.key, pack.key)} 当前只能从资料包层面给方向，主看{pack_focus_text(pack.key)}。"
    )
    verdict_kind = question_aware_verdict_quality(question, verdict, tags)
    if pack.key == "name_studies" and result and result.get("generated_candidates"):
        verdict_kind = "conclusion"
    signal = top_signal(result or {})
    risks = top_risks(result or {})
    compatibility = legacy_detail_text(pack, result, question)
    if used_local_calculation and pack.key in {"yijing_and_symbolism", "liuyao_and_meihua"}:
        compatibility = ""
        translated_signal = translate_signal_text(signal)
        if translated_signal.startswith("本卦:") or translated_signal.startswith("变卦:"):
            signal = ""
    if verdict_kind == "conclusion" and compatibility and answer_repeats_verdict(verdict, compatibility):
        compatibility = ""

    answer_parts = [verdict] if verdict_kind == "conclusion" else []
    if verdict_kind == "structural":
        answer_parts.append(f"当前已完成{SYSTEM_LABELS.get(pack.key, pack.key)}的结构计算，但这一步还只是盘面/卦象结构，不等于最终结论。")
    elif verdict_kind == "supporting":
        answer_parts.append(
            f"这一路已经给出可参考的计算结果，但对{delivery_target_text(question, tags)}来说，目前更适合作为辅助线索，不直接充当最终结论。"
        )
    elif verdict_kind == "placeholder":
        answer_parts.append("当前这一路还没有形成可直接交付的判断。")
    if compatibility and compatibility not in verdict:
        answer_parts.append(compatibility)
    if signal and verdict_kind != "conclusion":
        answer_parts.append(f"依据：{translate_signal_text(signal)}。")
    elif evidence_text and verdict_kind != "conclusion":
        answer_parts.append(f"当前资料锚点：{evidence_text}。")
    if missing_inputs and not used_local_calculation:
        answer_parts.append(f"若要继续算细，需要再补：{'、'.join(missing_inputs[:3])}。")
    elif not used_local_calculation:
        answer_parts.append("这一轮还没有进入可落地的本地实算。")

    answer_parts = dedupe_answer_parts(answer_parts)
    translated_risks = [translate_risk_text(item) for item in risks]
    answer_text = re.sub(r"([。；;,，])\1+", r"\1", " ".join(item for item in answer_parts if item))
    answer_text = re.sub(r"。{2,}", "。", answer_text)
    extra_payload: dict[str, Any] = {}
    if result and pack.key == "fengshui":
        extra_payload["raw_result"] = {
            "used_inputs": result.get("used_inputs") or {},
            "derived_factors": result.get("derived_factors") or {},
            "primary_finding": result.get("primary_finding") or "",
            "supporting_signals": result.get("supporting_signals") or [],
            "risk_flags": result.get("risk_flags") or [],
            "time_window": result.get("time_window") or "",
        }
    if pack.key == "name_studies" and result and result.get("generated_candidates"):
        used = result.get("used_inputs") or {}
        birth_info = str(used.get("birth_info") or "").strip()
        naming_profile: dict[str, Any] = {
            "surname": str(used.get("surname") or "").strip(),
            "purpose": str(used.get("purpose") or "").strip(),
            "top_candidates": [],
        }
        for item in (result.get("generated_candidates") or [])[:5]:
            naming_profile["top_candidates"].append(
                {
                    "name": str(item.get("name") or "").strip(),
                    "meaning": trim_reply_text(item.get("meaning") or ""),
                    "source_title": trim_reply_text(item.get("source_title") or ""),
                    "source_quote": trim_reply_text(item.get("source_quote") or ""),
                    "style_tags": [translate_name_style_tag(str(tag)) for tag in (item.get("style_tags") or []) if str(tag).strip()],
                    "preferred_elements": list(item.get("preferred_elements") or []),
                    "bridge_number": item.get("expression_bridge_number"),
                    "why_selected": trim_reply_text(item.get("why_selected") or ""),
                    "birth_support_note": trim_reply_text(item.get("birth_support_note") or ""),
                }
            )
        if birth_info:
            try:
                bazi_payload: dict[str, Any] = {"birth_datetime": birth_info}
                gender_text = str(used.get("gender") or "").strip()
                if not gender_text:
                    inferred_gender = parse_birth_details(question).gender
                    gender_text = str(inferred_gender or "").strip()
                if gender_text:
                    bazi_payload["gender"] = gender_text
                bazi_result, status = calculate_system("bazi", bazi_payload)
                if status == 200 and not bazi_result.get("error"):
                    summary = bazi_result.get("summary") or {}
                    pillars = bazi_result.get("pillars") or {}
                    five_counts = bazi_result.get("five_element_counts") or {}
                    naming_profile["bazi_summary"] = {
                        "day_pillar": trim_reply_text(((pillars.get("day") or {}).get("text")) or ""),
                        "day_master": trim_reply_text(((bazi_result.get("day_master") or {}).get("stem")) or ""),
                        "five_elements": "，".join(
                            f"{key}{value}"
                            for key, value in five_counts.items()
                            if value not in (None, "")
                        ),
                        "strongest_elements": list(summary.get("strongest_elements") or []),
                        "weakest_elements": list(summary.get("weakest_elements") or []),
                        "note": trim_reply_text(summary.get("note") or ""),
                    }
            except Exception:
                pass
        extra_payload["naming_profile"] = naming_profile
    if pack.key == "name_studies" and result and result.get("generated_candidates"):
        refreshed_naming_profile = build_naming_profile_payload(question, result)
        if refreshed_naming_profile:
            extra_payload["naming_profile"] = refreshed_naming_profile

    return {
        "key": pack.key,
        "system": SYSTEM_LABELS.get(pack.key, pack.key),
        "verdict": verdict if verdict_kind == "conclusion" else "",
        "answer": answer_text,
        "confidence": confidence,
        "mode": mode,
        "missing_inputs": missing_inputs,
        "used_local_calculation": used_local_calculation,
        "signals": [signal] if signal else [],
        "risk_flags": translated_risks,
        "verdict_quality": verdict_kind,
        **extra_payload,
    }


def local_final_answer(question: str, packs: list[DossierPack], system_answers: list[dict[str, str]], tags: set[str]) -> dict[str, Any]:
    diagnostics = system_question_diagnostics(question, packs)
    controller = build_intelligent_controller(question, packs, diagnostics)
    if is_single_date_good_day_question(question) and all(pack.key == "date_selection" for pack in packs):
        date_result, status = calculate_system("date_selection", {"question": question})
        if status == 200:
            best = date_result["derived_factors"]["ranked_candidates"][0]
            verdict = date_result.get("derived_factors", {}).get("verdict")
            verdict_text = {
                "auspicious": f"直接结论：{best['date']} 在当前本地择日规则下偏吉，可用。",
                "mixed": f"直接结论：{best['date']} 在当前本地择日规则下属于中平可用，不算明显大吉，但也不是明显不宜。",
                "cautious": f"直接结论：{best['date']} 在当前本地择日规则下不算理想，建议谨慎。",
            }.get(verdict, f"直接结论：{best['date']} 已完成本地择日实算。")
            return {
                "synthesis": verdict_text,
                "agreements": [
                    f"本地择日实算得分：{best['score']}。",
                    f"支持信号：{date_result['supporting_signals'][0] if date_result.get('supporting_signals') else '当前规则组合中性。'}",
                    "这次只保留了能够直接对当前问题落地计算的择日体系。",
                ],
                "differences": [],
                "cautions": list(date_result.get("risk_flags", [])),
            }

    strong = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack.status == "deep"][:8]
    timing_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "timing"][:4]
    space_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "space"][:3]
    destiny_systems = [SYSTEM_LABELS.get(pack.key, pack.key) for pack in packs if pack_mode(pack.key) == "destiny"][:4]
    computed_systems = [item["system"] for item in system_answers if item.get("used_local_calculation")]
    timing_fallback_systems = [
        item["system"]
        for item in system_answers
        if item.get("mode") == "timing" and "current ask-time fallback chart" in item.get("answer", "")
    ]
    missing_input_systems = [item["system"] for item in system_answers if item.get("missing_inputs")]

    synthesis_parts = []
    if "space" in tags:
        synthesis_parts.append(f"Spatial factors are central here, so prioritize {' / '.join(space_systems or ['风水'])}.")
    if "timing" in tags:
        synthesis_parts.append(f"Timing matters here, so {' / '.join(timing_systems or ['奇门遁甲'])} should carry more weight.")
    if {"career", "relationship", "identity"} & tags:
        synthesis_parts.append(f"For long-term personal structure, {' / '.join(destiny_systems or ['八字'])} are the main anchors.")
    if "ritual" in tags:
        synthesis_parts.append("Ritual-oriented systems are better used as framing tools than as standalone decision engines.")
    if not synthesis_parts:
        synthesis_parts.append("Use a layered reading here: long-term structure, near-term timing, and real-world environment.")

    agreements = [
        "Most systems split the question into long-term structure and current window instead of giving a single verdict.",
        f"Currently the deeper local dossiers are strongest in: {' / '.join(strong or ['八字', '风水', '道术'])}.",
        "Seed-stage dossiers can still point direction, but they carry thinner evidence and weaker rule coverage.",
    ]
    if computed_systems:
        agreements.append(f"Real local calculation ran in: {' / '.join(computed_systems[:8])}.")
    if "space" in tags:
        agreements.append("Because relocation or living/working environment is involved, space-oriented systems gain more interpretive weight.")
    if "timing" in tags:
        agreements.append("Because the question asks what to do first, timing-oriented systems matter more than static natal-only systems.")

    differences = [
        "Natal-chart systems bias toward long-range structure; timing systems bias toward short-range action windows.",
        "Ritual or esoteric systems often provide framing, symbolism, or practice context rather than concrete operational advice.",
        "Modern symbolic systems often emphasize subjective and psychological interpretation more strongly.",
    ]

    cautions = [
        "This summary is still a local dossier synthesis, not a full cross-system personalized reading.",
        "For higher precision, natal systems still need exact birth time, while space systems need residence/workplace details.",
        "Local coverage is much broader now, but implementation depth and epistemic confidence still vary across traditions.",
    ]
    if timing_fallback_systems:
        cautions.append(
            f"Timing systems {' / '.join(timing_fallback_systems[:4])} fell back to the current ask time because no explicit event datetime was supplied."
        )
    if missing_input_systems:
        cautions.append(f"Some systems are still constrained by missing inputs, especially: {' / '.join(missing_input_systems[:6])}.")

    return {
        "synthesis": " ".join(synthesis_parts),
        "agreements": agreements,
        "differences": differences,
        "cautions": cautions,
    }


def build_system_prompt() -> str:
    return (
        "You are the synthesis engine for a metaphysics knowledge base. "
        "Base your answer strictly on the provided local dossier context. "
        "Return JSON with keys system_answers and final_answer. "
        "Each system answer must include system, answer, and confidence. "
        "The final answer must include synthesis, agreements, differences, and cautions."
    )


def answer_question(question: str, model: str) -> dict[str, Any]:
    normalized_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if normalized_model == LOCAL_MODEL_ID:
        return local_answer_question(question)

    packs = relevant_packs(question, limit=8)
    context_chunks = []
    for pack in packs:
        sections = []
        for part, path in pack.files.items():
            if not path.exists():
                continue
            text = collapse_text(safe_read(path))
            if text:
                sections.append(f"[{part}]\\n{text[:2400]}")
        context = "\\n\\n".join(sections)
        context_chunks.append(f"## {SYSTEM_LABELS.get(pack.key, pack.key)}\\n{context}")

    user_prompt = (
        f"User question: {question}\\n\\n"
        "Below are the most relevant local dossier excerpts. "
        "Give one answer per system, then provide a synthesis.\\n\\n"
        + "\\n\\n".join(context_chunks)
    )
    try:
        used_model, raw = ask_llm(
            DEFAULT_MODEL if normalized_model == AUTO_MODEL_ID else normalized_model,
            [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = json.loads(raw)
        return {
            "model": used_model,
            "systems": all_ranked_packs(question),
            "result": parsed,
        }
    except Exception:
        return local_answer_question(question)


LOCAL_MODEL_ALIASES = {LOCAL_MODEL_ID, "local-vault-synthesis", "local"}
BUILD_STAMP = "2026-06-08-alchemy-modern-21"

PRIMARY_BIRTH_CHART_SYSTEMS = {
    "bazi",
    "ziwei_doushu",
    "qizheng_siyu",
    "western_astrology",
    "vedic_astrology",
    "human_design",
}

SECONDARY_BIRTH_SYSTEMS = {"numerology"}

SYSTEM_QUERY_KEYWORDS = {    "yijing_and_symbolism": ("\u6613\u7ecf", "\u6613\u7d93", "\u5468\u6613", "\u8c61\u6570", "\u8c61\u6578", "\u5366", "\u6613\u7406"),

    "bazi": ("八字", "四柱", "子平", "日主", "用神", "十神", "大运", "大運"),
    "ziwei_doushu": ("紫微", "斗数", "斗數", "命宫", "身宫", "大限", "流年"),
    "qizheng_siyu": ("七政", "四余", "罗喉", "计都", "月孛", "紫气", "果老星宗"),
    "western_astrology": (
        "western astrology",
        "astrology",
        "natal",
        "birth chart",
        "zodiac",
        "moon sign",
        "rising sign",
        "ascendant",
        "星盘",
        "星盤",
        "西占",
        "占星",
        "本命盘",
        "本命盤",
        "太阳星座",
        "月亮星座",
        "上升",
        "宫位",
        "行星",
    ),
    "vedic_astrology": (
        "vedic",
        "sidereal",
        "nakshatra",
        "lahiri",
        "jyotish",
        "吠陀",
        "印度占星",
        "印度占星术",
        "月宿",
        "宿曜",
        "恒星黄道",
        "拉希里",
    ),
    "human_design": ("human design", "人类图", "類人圖", "显化者", "投射者", "生产者", "闸门", "通道"),
    "numerology": ("numerology", "数字命理", "生命灵数", "生命靈數", "灵数", "靈數"),
    "fengshui": ("风水", "風水", "朝向", "坐向", "户型", "住宅", "办公室"),
    "physiognomy": ("相术", "面相", "手相", "骨相", "气色", "額頭", "额头", "鼻梁", "下巴"),
    "daoist_arts": ("道术", "道法", "符咒", "科仪", "斋醮", "內丹", "内丹", "雷法", "正一", "全真", "净宅", "驱邪"),
    "alchemy_and_hermeticism": ("alchemy", "hermetic", "hermeticism", "炼金", "煉金", "赫尔墨斯", "赫耳墨斯", "nigredo", "albedo", "rubedo", "贤者之石", "賢者之石", "衔尾蛇", "銜尾蛇"),
    "modern_esotericism": ("modern esotericism", "manifestation", "law of attraction", "chakra", "aura", "reiki", "akashic", "shadow work", "channeling", "现代神秘学", "顯化", "显化", "脉轮", "靈氣", "灵气"),
    "kabbalah": ("kabbalah", "qabalah", "cabala", "卡巴拉", "生命之树", "生命之樹", "sephirah", "tiphereth", "yesod", "malkuth"),
    "qimen_dunjia": ("奇门", "奇門", "遁甲", "遁甲盘", "遁甲盤"),
    "liu_ren": ("六壬", "大六壬", "三传", "三傳", "四课", "四課"),
    "liuyao_and_meihua": ("六爻", "梅花", "卦象", "动爻", "動爻"),
    "tarot": ("塔罗", "塔羅", "牌阵", "牌陣", "抽牌", "正位", "逆位"),
    "name_studies": ("姓名", "名字", "起名", "取名", "改名", "起个名字", "取个名字", "起一个名字", "取一个名字"),
    "date_selection": ("择日", "擇日", "选日", "選日", "黄道吉日", "黃道吉日"),
    "onmyodo": ("阴阳道", "陰陽道", "式神", "方位禁忌"),
}


def detect_system_mentions(question: str) -> set[str]:
    question = normalize_multi_turn_question(question)
    lowered = question.lower()
    matches: set[str] = set()
    for key, keywords in SYSTEM_QUERY_KEYWORDS.items():
        if any(keyword.lower() in lowered for keyword in keywords):
            matches.add(key)
    if "相面" in question:
        matches.add("physiognomy")
    return matches


def is_birth_chart_question(question: str, tags: set[str], system_mentions: set[str]) -> bool:
    parsed = parse_birth_details(question)
    timing_mentions = {"qimen_dunjia", "liu_ren", "liuyao_and_meihua", "date_selection"}
    birth_chart_mentions = PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS
    if system_mentions & birth_chart_mentions:
        return True
    explicit_timing_only = bool(system_mentions & timing_mentions) and not (system_mentions & birth_chart_mentions)
    event_datetime = parse_datetime_from_text(question)
    has_explicit_birth_wording = has_birth_context(question)
    has_event_timing = question_has_event_timing_context(question)
    has_birth_like_details = (
        bool(parsed.birth_datetime)
        and (
            parsed.has_time
            or bool(parsed.gender)
            or bool(parsed.birth_location)
            or has_explicit_birth_wording
            or bool(system_mentions & birth_chart_mentions)
            or any(token in question.lower() for token in ("career", "relationship", "personality", "strength", "weakness", "purpose"))
            or any(token in question for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘"))
        )
    )
    has_separate_event_time = bool(event_datetime and parsed.birth_datetime and event_datetime != parsed.birth_datetime)
    if "naming" in tags or "name_studies" in system_mentions:
        return False
    if question_has_candidate_dates(question):
        return False
    if question_prefers_timing_decision(question, tags, system_mentions) and has_event_timing and not (system_mentions & birth_chart_mentions):
        return False
    if explicit_timing_only and (has_separate_event_time or "timing" in tags or has_event_timing):
        return False
    if has_event_timing and not has_explicit_birth_wording and not (system_mentions & birth_chart_mentions):
        return False

    theme_birth_question = bool(parsed.birth_datetime) and any(
        token in question for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘")
    )
    if theme_birth_question:
        return True

    birth_context = has_explicit_birth_wording or (
        bool(parsed.birth_datetime)
        and (
            parsed.has_time
            or bool(parsed.gender)
            or bool(parsed.birth_location)
            or bool(system_mentions & birth_chart_mentions)
            or any(token in question.lower() for token in ("career", "relationship", "personality", "strength", "weakness", "purpose"))
            or any(token in question for token in ("婚姻", "感情", "事业", "财运", "性格", "天赋", "命盘", "本命", "星盘"))
        )
    )
    has_datetime = question_has_datetime(question)

    if not (birth_context or has_datetime):
        return False
    if not birth_context and system_mentions & timing_mentions:
        return False
    if not birth_context and "timing" in tags and not (system_mentions & (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS)):
        return False
    if system_mentions & birth_chart_mentions:
        return True
    if any(token in question for token in ["命盘", "命盤", "本命", "星盘", "星盤", "人格", "性格"]):
        return True
    return bool({"career", "relationship", "identity"} & tags)


def relevant_packs(question: str, limit: int = 6) -> list[DossierPack]:
    lowered = question.lower()
    tags = infer_question_tags(question)
    good_day_query = any(token in question for token in GOOD_DAY_MARKERS)
    birth_context = has_birth_context(question)
    location_context = question_has_location(question)
    gender_context = question_has_gender(question)
    system_mentions = detect_system_mentions(question)
    birth_chart_mode = is_birth_chart_question(question, tags, system_mentions)
    mentioned_birth_chart_systems = system_mentions & (PRIMARY_BIRTH_CHART_SYSTEMS | SECONDARY_BIRTH_SYSTEMS)
    scored: list[tuple[int, DossierPack]] = []

    for pack in all_packs():
        text_parts = []
        for path in pack.files.values():
            if path.exists():
                text_parts.append(collapse_text(safe_read(path))[:2500])
        haystack = "\n".join(text_parts).lower()
        label = " ".join([pack.key.replace("_", " "), pack.title, pack.summary]).lower()
        score = 0
        token_score = 0
        for token in set(re.findall(r"[\w\u4e00-\u9fff]+", lowered)):
            if len(token) < 2:
                continue
            if token in label:
                token_score += 6
            token_score += min(haystack.count(token), 2)
        score += min(token_score, 48)

        mode = pack_mode(pack.key)
        if calculator_implemented(pack.key):
            score += 6
        elif pack.calculator.exists():
            score += 2

        if "timing" in tags and mode == "timing":
            score += 35
        if good_day_query and pack.key == "date_selection":
            score += 120
        if "career" in tags and mode == "destiny":
            score += 28
        if "relationship" in tags and mode == "destiny":
            score += 28
        if "identity" in tags and mode == "destiny":
            score += 24
        if "space" in tags and mode == "space":
            score += 35
        if "ritual" in tags and mode == "ritual":
            score += 35
        if "general" not in tags and mode == "symbolic":
            score += 8
        if pack.calculator.exists() and (mode in tags or ("career" in tags and mode == "destiny")):
            score += 10

        if pack.key in system_mentions:
            score += 140
        elif any(keyword in lowered for keyword in SYSTEM_QUERY_KEYWORDS.get(pack.key, ())):
            score += 90
        if pack.key in mentioned_birth_chart_systems:
            score += 90

        if birth_context and pack.key in PRIMARY_BIRTH_CHART_SYSTEMS:
            score += 72
            if calculator_implemented(pack.key):
                score += 18
            if pack.key in {"western_astrology", "vedic_astrology"} and location_context:
                score += 14
            if pack.key == "ziwei_doushu" and gender_context:
                score += 14
        elif birth_context and pack.key in SECONDARY_BIRTH_SYSTEMS:
            score += 26
        elif birth_context and mode in {"timing", "space", "ritual", "symbolic"} and not ({"timing", "space", "ritual"} & tags):
            score -= 68

        if birth_chart_mode:
            if pack.key in PRIMARY_BIRTH_CHART_SYSTEMS:
                score += 56
            elif pack.key in SECONDARY_BIRTH_SYSTEMS:
                score += 18
            elif pack.key not in system_mentions:
                score -= 40
        if mentioned_birth_chart_systems and pack.key in PRIMARY_BIRTH_CHART_SYSTEMS and pack.key not in mentioned_birth_chart_systems:
            score -= 28

        if birth_chart_mode and pack.key in {"western_astrology", "vedic_astrology", "ziwei_doushu"}:
            score += 24

        if birth_chart_mode and pack.key in {"qimen_dunjia", "liu_ren", "fengshui", "tarot", "yijing_and_symbolism"} and pack.key not in system_mentions:
            score -= 75
        if birth_chart_mode and pack.key == "human_design" and not calculator_implemented(pack.key) and pack.key not in system_mentions:
            score -= 60

        if score == 0 and pack.status == "deep":
            score = 1
        scored.append((score, pack))

    scored.sort(
        key=lambda item: (
            item[0],
            1 if calculator_implemented(item[1].key) else 0,
            item[1].score,
        ),
        reverse=True,
    )
    selected = [pack for score, pack in scored if score > 0][:limit]
    if len(selected) < min(limit, 4):
        for _, pack in scored:
            if pack not in selected:
                selected.append(pack)
            if len(selected) >= min(limit, 4):
                break
    return selected


def all_ranked_packs(question: str) -> list[DossierPack]:
    selected = relevant_packs(question, limit=len(DOSSIER_ORDER))
    seen = set()
    ordered: list[DossierPack] = []
    for pack in selected:
        ordered.append(pack)
        seen.add(pack.key)
    for pack in all_packs():
        if pack.key not in seen:
            ordered.append(pack)
    return ordered


def answer_question(question: str, model: str) -> dict[str, Any]:
    normalized_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if normalized_model in LOCAL_MODEL_ALIASES:
        return local_answer_question(question)

    packs = relevant_packs(question, limit=8)
    context_chunks = []
    for pack in packs:
        sections = []
        for part, path in pack.files.items():
            if not path.exists():
                continue
            text = collapse_text(safe_read(path))
            if text:
                sections.append(f"[{part}]\\n{text[:2400]}")
        context = "\\n\\n".join(sections)
        context_chunks.append(f"## {SYSTEM_LABELS.get(pack.key, pack.key)}\\n{context}")

    user_prompt = (
        f"User question: {question}\\n\\n"
        "Below are the most relevant local dossier excerpts. "
        "Give one answer per system, then provide a synthesis.\\n\\n"
        + "\\n\\n".join(context_chunks)
    )
    try:
        used_model, raw = ask_llm(
            DEFAULT_MODEL if normalized_model == AUTO_MODEL_ID else normalized_model,
            [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = json.loads(raw)
        return {
            "model": used_model,
            "systems": all_ranked_packs(question),
            "result": parsed,
        }
    except Exception:
        return local_answer_question(question)
 
 
def local_final_answer(question: str, packs: list[DossierPack], system_answers: list[dict[str, str]], tags: set[str]) -> dict[str, Any]:
    question = normalize_multi_turn_question(question)
    controller = build_intelligent_controller(question, packs, system_question_diagnostics(question, packs))
    if is_single_date_good_day_question(question) and all(pack.key == "date_selection" for pack in packs):
        date_result, status = calculate_system("date_selection", {"question": question})
        if status == 200:
            best = date_result["derived_factors"]["ranked_candidates"][0]
            verdict = date_result.get("derived_factors", {}).get("verdict")
            verdict_text = {
                "auspicious": f"直接结论：{best['date']} 在当前本地择日规则下偏吉，可用。",
                "mixed": f"直接结论：{best['date']} 在当前本地择日规则下属于中平可用，不算明显大吉，但也不是明显不宜。",
                "cautious": f"直接结论：{best['date']} 在当前本地择日规则下不算理想，建议谨慎。",
            }.get(verdict, f"直接结论：{best['date']} 已完成本地择日实算。")
            return {
                "synthesis": verdict_text,
                "agreements": [
                    f"本地择日实算得分：{best['score']}。",
                    f"支持信号：{date_result['supporting_signals'][0] if date_result.get('supporting_signals') else '当前规则组合中性。'}",
                    "这次只保留了能够直接对当前问题落地计算的择日体系。",
                ],
                "differences": [],
                "cautions": list(date_result.get("risk_flags", [])),
            }

    answered = [item for item in system_answers if item.get("used_local_calculation")]
    substantive_answered = [item for item in answered if has_substantive_verdict(item.get("verdict"))]
    fallback_answered = [
        item for item in answered
        if trim_reply_text(item.get("answer"))
        and item not in substantive_answered
        and item.get("verdict_quality") in {"supporting", "conclusion"}
    ]
    substantive_answered.sort(
        key=lambda item: top_system_priority(
            str(item.get("key") or ""),
            question,
            tags,
            str(item.get("verdict") or ""),
        ),
        reverse=True,
    )
    computed_systems = [item["system"] for item in answered]
    structural_systems = [
        item["system"]
        for item in answered
        if item.get("verdict_quality") == "structural"
    ]
    substantive_systems = [item["system"] for item in substantive_answered]
    missing_input_systems = [item["system"] for item in system_answers if item.get("missing_inputs")]
    ranked_for_delivery = substantive_answered + [
        item for item in fallback_answered if item not in substantive_answered
    ]
    explicit_system_keys = detect_system_mentions(question)
    direct_note = question_level_direct_recommendation(question, tags)
    selected_controller_systems = list(controller.get("selectedSystems") or [])
    selected_controller_missing = list(controller.get("missingInputs") or [])

    if not system_answers:
        follow_up = controller.get("followUpPrompt") or ""
        if direct_note:
            cautions = ["这轮先按问题结构给轻判断，还不是完整命盘或起局后的最终结论。"]
            if follow_up:
                cautions.append(f"要把结论压得更实，再补：{follow_up}")
            return {
                "synthesis": direct_note,
                "agreements": ["当前问法还没进入完整命盘或时机实算，但已经能先做选项层排序。"],
                "differences": [],
                "cautions": cautions,
            }
        if selected_controller_systems:
            selected_names: list[str] = []
            seen_names: set[str] = set()
            for item in selected_controller_systems:
                title = str(item.get("title") or SYSTEM_LABELS.get(str(item.get("key") or ""), str(item.get("key") or ""))).strip()
                if title and title not in seen_names:
                    selected_names.append(title)
                    seen_names.add(title)
                if len(selected_names) >= 3:
                    break
            missing_fields: list[str] = []
            seen_fields: set[str] = set()
            for item in selected_controller_missing:
                field = str(item.get("field") or "").strip()
                if field and field not in seen_fields:
                    missing_fields.append(field)
                    seen_fields.add(field)
                if len(missing_fields) >= 3:
                    break
            synthesis = f"总控已经把这题交给{'、'.join(selected_names) if selected_names else '当前体系'}，但还差{'、'.join(missing_fields) if missing_fields else '关键条件'}。"
            if follow_up:
                synthesis = f"{synthesis} {follow_up}"
            return {
                "synthesis": synthesis,
                "agreements": [
                    f"当前主调体系：{'、'.join(selected_names) if selected_names else '待补齐后起算'}。",
                ],
                "differences": [],
                "cautions": [
                    "现在先继续补条件，还不会直接进入点香起算。",
                ],
            }
        return {
            "synthesis": (
                "当前还没有进入可直接起算的本地体系。"
                + (f" {follow_up}" if follow_up else "")
            ),
            "agreements": [],
            "differences": [],
            "cautions": [
                "这不是没有资料，而是当前问法还没落到可稳定起算的输入结构。"
            ] + ([follow_up] if follow_up else []),
        }

    verdicts = [trim_reply_text(item.get("verdict")) for item in substantive_answered if trim_reply_text(item.get("verdict"))]
    if verdicts:
        lead_candidates = substantive_answered
        date_candidates = [
            item for item in substantive_answered
            if str(item.get("key") or "") == "date_selection"
        ]
        seed_candidates = [
            item for item in substantive_answered
            if str(item.get("key") or "") in {"liuyao_and_meihua", "yijing_and_symbolism"}
        ]
        timing_candidates = [
            item for item in substantive_answered
            if str(item.get("key") or "") in {"qimen_dunjia", "liu_ren", "date_selection"}
        ]
        onmyodo_candidates = [
            item for item in substantive_answered
            if str(item.get("key") or "") == "onmyodo"
        ]
        if question_has_candidate_dates(question) and date_candidates:
            lead_candidates = date_candidates
        elif question_has_explicit_divination_seed(question) and seed_candidates:
            lead_candidates = seed_candidates
        elif onmyodo_candidates and question_is_explicit_onmyodo_direction_trip(question):
            lead_candidates = onmyodo_candidates
        elif question_has_short_timing_decision_context(question) and timing_candidates:
            lead_candidates = timing_candidates
        lead_item = max(
            lead_candidates,
            key=lambda item: (
                1 if str(item.get("key") or "") in explicit_system_keys else 0,
                top_system_priority(
                    str(item.get("key") or ""),
                    question,
                    tags,
                    str(item.get("verdict") or ""),
                ),
                verdict_delivery_score(question, item.get("verdict") or "", tags),
            ),
        )
        lead_verdict = trim_reply_text(lead_item.get("verdict"))
        synthesis = lead_verdict
        if len(verdicts) > 1:
            synthesis = f"{lead_verdict} 其他体系主要是在这个判断上补充细节，而不是另起一套空泛说法。"
    elif fallback_answered:
        fallback_answered.sort(
            key=lambda item: verdict_delivery_score(question, item.get("answer") or item.get("verdict") or "", tags),
            reverse=True,
        )
        lead = trim_reply_text(fallback_answered[0].get("verdict") or fallback_answered[0].get("answer"))
        synthesis = lead or "本轮已经完成本地计算，并拿到了可参考的判断。"
        if len(fallback_answered) > 1:
            synthesis = f"{synthesis} 其他已参与实算的体系主要是在这个结果上补充角度。"
    elif answered:
        follow_up = controller.get("followUpPrompt") or ""
        synthesis = "本轮已经完成部分本地计算，但目前拿到的主要还是结构结果，还不足以当成最终答复。"
        if follow_up:
            synthesis = f"{synthesis} {follow_up}"
    else:
        follow_up = controller.get("followUpPrompt") or ""
        lead_missing_answer = next((item for item in system_answers if item.get("missing_inputs")), None)
        if lead_missing_answer:
            needed = [str(item).strip() for item in (lead_missing_answer.get("missing_inputs") or []) if str(item).strip()]
            needed_text = "、".join(needed[:3]) if needed else "关键前置条件"
            synthesis = f"{lead_missing_answer['system']}这题已经找到对应入口，但还缺{needed_text}，暂时不能直接下结论。"
        else:
            synthesis = "当前还没有形成可直接交付的本地结论。"
        if follow_up:
            synthesis = f"{synthesis} {follow_up}"
    if "naming" in tags:
        naming_answer = next((item for item in substantive_answered if item.get("key") == "name_studies"), None)
        if naming_answer and trim_reply_text(naming_answer.get("verdict")):
            synthesis = trim_reply_text(naming_answer.get("verdict"))
        elif naming_answer and "首选" in trim_reply_text(naming_answer.get("answer")):
            synthesis = trim_reply_text(naming_answer.get("answer"))
    if ("space" in tags or "长期居住" in question or "朝向" in question) and "空间" not in synthesis:
        synthesis = f"{synthesis.rstrip('。；; ')}。这题还带有空间与环境维度。"
    synthesis = enrich_synthesis_with_requested_facets(question, synthesis, ranked_for_delivery, tags)

    agreements: list[str] = []
    for item in substantive_answered[:4]:
        verdict = trim_reply_text(item.get("verdict"))
        if verdict:
            agreements.append(f"{item['system']}：{verdict}")
    if computed_systems:
        agreements.append(f"本轮实际参与本地实算的体系有：{'、'.join(computed_systems[:8])}。")
    if substantive_systems:
        agreements.append(f"其中已经形成直接结论的体系有：{'、'.join(substantive_systems[:6])}。")
    if structural_systems:
        agreements.append(f"仍停留在结构计算层的体系有：{'、'.join(structural_systems[:6])}，这些结果已明确不当作最终结论。")
    if answered and not substantive_answered:
        agreements.append("本轮确实跑了本地计算，但目前返回的主要是盘面结构，还没有沉淀成可以直接交付的判断。")

    differences: list[str] = []
    timing_answers = [item for item in answered if item.get("mode") == "timing"]
    symbolic_answers = [item for item in answered if item.get("mode") == "symbolic"]
    destiny_answers = [item for item in answered if item.get("mode") == "destiny"]
    space_answers = [item for item in answered if item.get("mode") == "space"]

    if space_answers and not timing_answers and not destiny_answers:
        differences.append("这次主要是空间筛查型判断，能先告诉你方向和朝向层面的可用性，但还不是完整风水勘验。")
    if destiny_answers and timing_answers:
        differences.append("命盘型体系更偏个人长期结构，时机型体系更偏当前动作窗口，两者回答的时间尺度不同。")
    if symbolic_answers:
        differences.append("象数类体系更像是在解释当前局势的结构与趋势，不会替代现实层面的细节校验。")

    cautions: list[str] = []
    for item in system_answers:
        for risk in item.get("risk_flags") or []:
            translated = translate_risk_text(risk)
            if translated not in cautions:
                cautions.append(translated)
            if len(cautions) >= 5:
                break
        if len(cautions) >= 5:
            break
    if missing_input_systems:
        cautions.append(f"本轮仍受输入限制的体系主要有：{'、'.join(missing_input_systems[:6])}。")

    cautions = [translate_risk_text(item) for item in cautions]

    return {
        "synthesis": synthesis,
        "agreements": agreements[:6],
        "differences": differences[:4],
        "cautions": cautions[:6],
    }


def local_answer_question(question: str) -> dict[str, Any]:
    question = normalize_multi_turn_question(question)
    safety = safety_screen(question)
    if safety:
        controller = {
            "name": "安全总控",
            "executionStatus": "blocked",
            "questionType": "高风险现实问题",
            "routingSummary": safety["summary"],
            "selectedSystems": [],
            "alternateSystems": [],
            "missingInputs": [],
            "signals": [safety["title"]],
            "followUpPrompt": "",
            "issueType": "safety",
        }
        return {
            "model": "local-vault-synthesis",
            "systems": [],
            "result": {
                "controller": controller,
                "system_answers": [],
                "system_diagnostics": [],
                "final_answer": {
                    "synthesis": safety["summary"],
                    "agreements": list(safety.get("actions") or []),
                    "differences": [],
                    "cautions": list(safety.get("cautions") or []),
                },
            },
        }
    birth_issue = parsed_birth_issue(parse_birth_details(question))
    if birth_issue:
        diagnostics = system_question_diagnostics(question, [])
        controller = build_intelligent_controller(question, [], diagnostics)
        return {
            "model": "local-vault-synthesis",
            "systems": [],
            "result": {
                "controller": controller,
                "system_answers": [],
                "system_diagnostics": diagnostics,
                "final_answer": {
                    "synthesis": birth_issue,
                    "agreements": [],
                    "differences": [],
                    "cautions": [birth_issue],
                },
            },
        }
    packs = local_computable_packs(question)
    tags = infer_question_tags(question)
    diagnostics = system_question_diagnostics(question, packs)
    included_keys = {pack.key for pack in packs}
    supplemental_keys: set[str] = set()
    supplemental_packs = [
        compute_pack(str(item.get("key") or ""))
        for item in diagnostics
        if str(item.get("key") or "")
        and str(item.get("key") or "") not in included_keys
        and str(item.get("key") or "") not in supplemental_keys
        and should_include_missing_route_answer(str(item.get("key") or ""), question, diagnostics)
    ]
    for pack in supplemental_packs:
        supplemental_keys.add(pack.key)
    ordered_packs = packs + [pack for pack in supplemental_packs if pack.key not in included_keys]
    system_answers = [local_system_answer(pack, question, tags) for pack in ordered_packs]
    controller = build_intelligent_controller(question, packs, diagnostics)
    final_answer = local_final_answer(question, ordered_packs, system_answers, tags)
    direct_note = question_level_direct_recommendation(question, tags)
    selected_systems = list(controller.get("selectedSystems") or [])
    birth_only_missing = bool(selected_systems) and all(
        str(item.get("key") or "") in BIRTH_DETAIL_SYSTEMS and str(item.get("status") or "") == "missing_inputs"
        for item in selected_systems
    )
    if (
        not packs
        and (not selected_systems or birth_only_missing)
        and direct_note
        and trim_reply_text(direct_note) in trim_reply_text(final_answer.get("synthesis"))
    ):
        controller = dict(controller)
        controller["executionStatus"] = "answered"
        controller["routingSummary"] = f"总控判断这是{controller.get('questionType') or '综合问题'}，当前先按问题结构给出轻量直答。"
        controller["followUpPrompt"] = ""
        signals = [
            signal
            for signal in list(controller.get("signals") or [])
            if signal != "当前主要阻塞是起算条件还不够。"
        ]
        lead_signal = "当前问法还没进入完整命盘或起局，但已经能先做选项层排序。"
        if lead_signal not in signals:
            signals.insert(0, lead_signal)
        controller["signals"] = signals
    return {
            "model": "local-vault-synthesis",
            "systems": packs,
            "result": {
                "controller": controller,
                "system_answers": system_answers,
                "system_diagnostics": diagnostics,
                "final_answer": final_answer,
        },
    }


def answer_question(question: str, model: str) -> dict[str, Any]:
    normalized_model = (model or DEFAULT_MODEL).strip() or DEFAULT_MODEL
    if normalized_model in LOCAL_MODEL_ALIASES:
        return local_answer_question(question)
    if normalized_model == AUTO_MODEL_ID and not question.isascii():
        return local_answer_question(question)

    packs = relevant_packs(question, limit=8)
    context_chunks = []
    for pack in packs:
        sections = []
        for part, path in pack.files.items():
            if not path.exists():
                continue
            text = collapse_text(safe_read(path))
            if text:
                sections.append(f"[{part}]\\n{text[:2400]}")
        context = "\\n\\n".join(sections)
        context_chunks.append(f"## {SYSTEM_LABELS.get(pack.key, pack.key)}\\n{context}")

    user_prompt = (
        f"User question: {question}\\n\\n"
        "Below are the most relevant local dossier excerpts. "
        "Give one answer per system, then provide a synthesis.\\n\\n"
        + "\\n\\n".join(context_chunks)
    )
    try:
        used_model, raw = ask_llm(
            DEFAULT_MODEL if normalized_model == AUTO_MODEL_ID else normalized_model,
            [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": user_prompt},
            ],
        )
        parsed = json.loads(raw)
        return {
            "model": used_model,
            "systems": all_ranked_packs(question),
            "result": parsed,
        }
    except Exception:
        return local_answer_question(question)


BENCHMARK_QUESTIONS = {
    "bazi": "我出生于1990-05-12 14:30，男，河南信阳，想看今年工作和财运。",
    "ziwei_doushu": "1990-05-12 14:30，女，想看婚姻和事业主轴。",
    "qizheng_siyu": "1990-05-12 14:30，北京，想看接下来两年的事业变化。",
    "western_astrology": "1990-05-12 14:30，北京，想看我的职业优势和关系模式。",
    "vedic_astrology": "1990-05-12 14:30，北京，想看这两年的事业和婚恋走势。",
    "human_design": "1990-05-12 14:30，北京，想看我的人类图类型和决策方式。",
    "numerology": "1990-05-12，想看我的生命灵数和今年主题。",
    "qimen_dunjia": "现在是 2026-06-08 21:10，我想问这周先谈合作还是先推进招聘。",
    "liu_ren": "2026-06-08 21:10 起问，这次签约最终能不能落地。",
    "liuyao_and_meihua": "我想问这次合作能不能成，数字 3 8 5。",
    "yijing_and_symbolism": "我想问这次合作能不能成，数字 3 8 5。",
    "date_selection": "我想搬家，候选日期是 2026年6月10日 和 2026年6月12日，地点在上海。",
    "fengshui": "上海浦东某小区 12 栋 1802，坐北朝南，想看适不适合长期居住。",
    "name_studies": "名字林清和适合男孩吗？用于正式姓名。",
    "tarot": "三张牌分别是愚者正位、死神逆位、圣杯首牌，想问这个月项目走向。",
    "physiognomy": "额头宽、眼神清、鼻梁直、下巴饱满，日间正面照片观察，想看整体面相倾向。",
    "daoist_arts": "正一道法脉，想了解净宅护身类仪式通常怎么分类与使用。",
    "kabbalah": "从 Tiphereth 的角度看 career direction 和 visible purpose。",
    "alchemy_and_hermeticism": "nigredo 阶段的 shadow work，材料是 crow mercury salt。",
    "onmyodo": "2026-06-10 去东京西南方向出行，这个方向与时点合不合适？",
    "modern_esotericism": "我在做 manifesting、chakra、reiki 和 shadow work，想看这条实践路径的结构和风险。",
}

BENCHMARK_EXPECTATIONS = {
    "bazi": ["八字看财运", "要特别防"],
    "ziwei_doushu": ["紫微看事业", "命宫主轴"],
    "qizheng_siyu": ["七政四余看事业", "官禄位"],
    "western_astrology": ["西占看事业", "太阳金牛座"],
    "vedic_astrology": ["吠陀看事业", "命宫落在"],
    "human_design": ["投射者", "权威为"],
    "numerology": ["数字命理看", "个人年"],
    "qimen_dunjia": ["本局为", "下一步"],
    "liu_ren": ["大六壬课体为", "事情不是不能成"],
    "liuyao_and_meihua": ["体卦为", "用卦为"],
    "yijing_and_symbolism": ["本卦为", "变卦为"],
    "date_selection": ["候选日期里更稳的是", "中平可用"],
    "fengshui": ["风水看这套房", "长期居住"],
    "name_studies": ["姓名学看", "拼音桥接数"],
    "tarot": ["塔罗牌面落在", "下一步更适合"],
    "physiognomy": ["面相这一路", "主轴更落在"],
    "daoist_arts": ["道术看这类", "净化与禳解类"],
    "kabbalah": ["卡巴拉这一路落到", "中柱"],
    "alchemy_and_hermeticism": ["炼金术这一路", "黑化阶段"],
    "onmyodo": ["阴阳道按当前日时看", "绕开或改期"],
    "modern_esotericism": ["现代神秘学这一路看", "自我理解框架"],
}


def question_has_location(question: str) -> bool:
    parsed = parse_birth_details(question)
    if parsed.birth_datetime:
        inferred_birth_location = infer_birth_location_hint(question)
        if inferred_birth_location:
            return True
    if parsed.birth_location:
        return True
    inferred_general_location = infer_birth_location_hint(question)
    if inferred_general_location:
        return True
    explicit_space_markers = (
        "出生地",
        "生于",
        "来自",
        "现居",
        "住在",
        "地址",
        "地点",
        "位置",
        "城市",
        "小区",
        "公寓",
        "楼层",
        "坐向",
        "朝向",
        "户型",
        "平面图",
    )
    if any(marker in question for marker in explicit_space_markers):
        return True
    explicit_location_match = re.search(
        r"(?:地点在|地点是|地址在|地址是|位置在|位于|住在|现居在)\s*([A-Za-z\u4e00-\u9fff][A-Za-z\u4e00-\u9fff .'-]{1,20})",
        question,
    )
    if explicit_location_match:
        candidate = explicit_location_match.group(1).strip(" ，,。.;；:：")
        if candidate and not any(token in candidate for token in ("哪里", "哪儿", "哪", "这儿", "那里", "附近")):
            return True
    if re.search(r"坐[\u4e1c\u5357\u897f\u5317]{1,2}朝[\u4e1c\u5357\u897f\u5317]{1,2}", question):
        return True

    admin_match = re.search(r"(?:^|[\s,，。；;:：])[\u4e00-\u9fff]{1,8}(?:省|市|县|镇|乡|村)(?=$|[\s,，。；;:：])", question)
    district_match = re.search(r"(?:^|[\s,，。；;:：])[\u4e00-\u9fff]{1,6}区(?=$|[\s,，。；;:：])", question)
    road_match = re.search(r"(?:^|[\s,，。；;:：])[\u4e00-\u9fff]{1,8}(?:路|街)(?:\d+号?)?(?=$|[\s,，。；;:：])", question)
    if admin_match:
        return True
    if district_match:
        district_text = district_match.group(0).strip()
        if district_text not in {"这个区", "哪个区", "那一区"}:
            return True
    if road_match:
        road_text = road_match.group(0).strip()
        if not any(token in road_text for token in ("一条路", "两条路", "三条路", "这条路", "那条路", "哪条路")):
            return True
    return bool(re.search(r"\b(?:in|at|from)\s+[A-Za-z][A-Za-z .'-]{1,40}\b", question, re.IGNORECASE))


def question_has_fengshui_anchor(question: str) -> bool:
    if re.search(r"坐[\u4e1c\u5357\u897f\u5317]{1,2}朝[\u4e1c\u5357\u897f\u5317]{1,2}", question):
        return True
    if any(token in question for token in ("朝南", "朝北", "朝东", "朝西", "坐向", "朝向", "户型", "平面图", "入户门", "主卧", "床位", "楼栋", "单元", "室")):
        return True
    return False


def missing_input_hints(pack: DossierPack, question: str) -> list[str]:
    required = REQUIRED_INPUT_HINTS.get(pack.key, [])
    if not required:
        return []

    parsed = parse_birth_details(question)
    has_birth_date = parsed.birth_datetime is not None
    has_birth_time = has_birth_date and parsed.has_time
    inferred_birth_location = ""
    if has_birth_date:
        inferred_birth_location = infer_birth_location_hint(question)
    has_location = bool(inferred_birth_location) or question_has_location(question)
    has_fengshui_anchor = question_has_fengshui_anchor(question)
    has_gender = question_has_gender(question)
    has_datetime = question_has_datetime(question)
    has_hexagram = question_has_hexagram(question)
    has_cards = question_has_cards(question)
    has_candidate_dates = question_has_candidate_dates(question)
    has_specific_question = len(question.strip()) >= 6
    has_description = question_has_physiognomy_description(question)
    has_vague_description = question_has_vague_physiognomy_description(question)
    has_observation_context = question_has_observation_context(question)
    has_lineage = question_has_lineage_markers(question)
    has_ritual = question_has_ritual_markers(question)
    has_alchemy = question_has_alchemy_markers(question)
    has_modern_esoteric = question_has_modern_esoteric_markers(question)
    if pack.key == "name_studies":
        has_name_candidate = bool(engine_registry.parse_name_candidate(question) or engine_registry.infer_name_candidates(question))
        is_generation_request = engine_registry.is_name_generation_request(question) or any(
            token in question for token in ("起名", "取名", "名字推荐", "候选名", "正式姓名", "正式名字", "大名", "小名", "乳名")
        )
        wants_direction_only = question_wants_name_direction_only(question)
        has_surname = bool(engine_registry.infer_surname_for_naming(question))
        has_name_or_options = has_name_candidate or (is_generation_request and has_surname)
        has_name_birth = has_birth_date and has_birth_time
        has_naming_purpose = any(
            token in question
            for token in (
                "正式姓名",
                "正式名字",
                "大名",
                "小名",
                "乳名",
                "英文名",
                "学名",
                "艺名",
                "笔名",
                "网名",
                "品牌名",
                "公司名",
                "店名",
                "商标名",
                "用于",
                "给谁用",
                "做什么用",
            )
        )
    else:
        has_name_or_options = False
        has_name_birth = False
        has_naming_purpose = False
        wants_direction_only = False

    missing: list[str] = []
    if pack.key == "name_studies" and is_generation_request:
        if not has_surname:
            missing.append(SURNAME_LABEL)
        if not has_name_birth and not wants_direction_only:
            missing.append(NAME_BIRTH_LABEL)
        if not has_gender:
            missing.append(GENDER_LABEL)
        if not has_naming_purpose and not wants_direction_only:
            missing.append(PURPOSE_LABEL)
        return missing[:4]
    for item in required:
        if item == BIRTH_DATE_LABEL and not has_birth_date:
            missing.append(item)
        elif item == BIRTH_TIME_LABEL and not has_birth_time:
            missing.append(item)
        elif item == BIRTH_LOCATION_LABEL and not has_location:
            missing.append(item)
        elif item == GENDER_LABEL and not has_gender:
            missing.append(item)
        elif item in {ASK_TIME_LABEL, DIVINATION_TIME_LABEL} and not has_datetime:
            if pack.key in {"qimen_dunjia", "liu_ren"} and question_has_concrete_question_subject(question):
                continue
            missing.append(item)
        elif item == HEXAGRAM_LABEL and not has_hexagram:
            missing.append(item)
        elif item == CANDIDATE_DATES_LABEL and not has_candidate_dates:
            missing.append(item)
        elif item == CITY_OR_ADDRESS_LABEL and not has_location:
            missing.append(item)
        elif item == FACING_OR_PLAN_LABEL and not has_fengshui_anchor:
            missing.append(item)
        elif item == LOCATION_LABEL and not has_location:
            missing.append(item)
        elif item == CARDS_LABEL and not has_cards:
            missing.append(item)
        elif item == SPECIFIC_QUESTION_LABEL and not has_specific_question:
            missing.append(item)
        elif item == DESCRIPTION_LABEL and (not has_description or has_vague_description):
            missing.append(item)
        elif item == OBSERVATION_CONTEXT_LABEL and not has_observation_context:
            missing.append(item)
        elif item == TOPIC_LABEL and not has_specific_question:
            missing.append(item)
        elif item == LINEAGE_LABEL and not has_lineage:
            missing.append(item)
        elif item == RITUAL_TEXT_LABEL and not has_ritual:
            missing.append(item)
        elif item == TEXT_OR_IMAGE_LABEL and not has_alchemy:
            missing.append(item)
        elif item == STAGE_MODEL_LABEL and not has_alchemy:
            missing.append(item)
        elif item == SOURCE_LABEL and not has_modern_esoteric:
            missing.append(item)
        elif item == PRACTICE_DESCRIPTION_LABEL and not has_modern_esoteric:
            missing.append(item)
        elif item == NAME_OR_OPTIONS_LABEL and not has_name_or_options:
            missing.append(item)
        elif item == PURPOSE_LABEL and not has_naming_purpose:
            missing.append(item)
    return missing[:3]


def benchmark_system(system_key: str) -> dict[str, Any]:
    question = BENCHMARK_QUESTIONS.get(system_key)
    if not question:
        return {"key": system_key, "ok": False, "error": "No benchmark question configured."}

    pack = compute_pack(system_key)
    tags = infer_question_tags(question)
    mentions = detect_system_mentions(question)
    matched, match_reason = question_match_details(pack, question, tags, mentions)
    missing_inputs = missing_input_hints(pack, question)
    computable = can_compute_pack_from_question(pack, question) if calculator_implemented(system_key) else False

    answer_text = ""
    confidence = None
    result_ok = False
    if matched and computable:
        answer = local_system_answer(pack, question, tags)
        answer_text = answer.get("answer", "")
        confidence = answer.get("confidence")
        expected_tokens = BENCHMARK_EXPECTATIONS.get(system_key, [])
        lowered = answer_text.lower()
        result_ok = all(token.lower() in lowered for token in expected_tokens) if expected_tokens else bool(answer_text.strip())

    return {
        "key": system_key,
        "title": SYSTEM_LABELS.get(system_key, system_key),
        "question": question,
        "matched": matched,
        "matchReason": match_reason,
        "missingInputs": missing_inputs,
        "computable": computable,
        "resultOk": result_ok,
        "confidence": confidence,
        "answerPreview": answer_text[:240],
        "ok": matched and computable and result_ok,
    }


def benchmark_all_systems() -> list[dict[str, Any]]:
    return [benchmark_system(key) for key in DOSSIER_ORDER]


@app.post("/api/system-diagnostics")
def system_diagnostics_api():
    payload: dict[str, Any] = request.get_json(force=True, silent=False) or {}
    question = str(payload.get("question") or "").strip()
    if not question:
        return jsonify({"error": "Question is required."}), 400
    packs = local_computable_packs(question)
    return jsonify({
        "question": question,
        "selectedSystems": [pack.key for pack in packs],
        "diagnostics": system_question_diagnostics(question, packs),
    })


@app.get("/api/benchmarks")
def benchmarks_api():
    results = benchmark_all_systems()
    return jsonify({
        "buildStamp": BUILD_STAMP,
        "overallOk": all(item.get("ok") for item in results),
        "results": results,
    })


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8787"))
    app.run(host=host, port=port, debug=False)
