from __future__ import annotations

from datetime import date, datetime
import re
from typing import Any
from zoneinfo import ZoneInfo

from .alchemy_and_hermeticism import AlchemyHermeticismInput, calculate_alchemy_and_hermeticism
from .bazi import BaziInput, calculate_bazi
from .date_selection import DateSelectionInput, calculate_date_selection
from .daoist_arts import DaoistArtsInput, calculate_daoist_arts
from .fengshui import FengShuiInput, calculate_fengshui
from .map_provider_tencent import collect_nearby_poi_signals, geocode_address, has_tencent_map_key, static_map_url
from .human_design import HumanDesignInput, calculate_human_design
from .kabbalah import KabbalahInput, calculate_kabbalah
from .liu_ren import LiuRenInput, calculate_liu_ren
from .liuyao import LiuyaoInput, calculate_liuyao
from .name_studies import NameStudiesInput, calculate_name_studies, generate_name_candidates
from .numerology import NumerologyInput, calculate_numerology
from .onmyodo import OnmyodoInput, calculate_onmyodo
from .physiognomy import PhysiognomyInput, calculate_physiognomy
from .qimen_dunjia import QimenDunjiaInput, calculate_qimen_dunjia
from .parsing import parse_birth_details, parse_datetime_from_text
from .qizheng_siyu import QizhengSiyuInput, calculate_qizheng_siyu
from .tarot import TarotInput, calculate_tarot, normalize_cards
from .vedic_astrology import VedicAstrologyInput, calculate_vedic_astrology
from .western_astrology import WesternAstrologyInput, calculate_western_astrology
from .yijing import YijingInput, calculate_yijing, parse_numbers
from .ziwei_doushu import ZiweiDoushuInput, calculate_ziwei_doushu
from .modern_esotericism import ModernEsotericismInput, calculate_modern_esotericism


HIGH_RISK_FUTURE_YEAR = 2050


IMPLEMENTED_SYSTEMS = {
    "bazi",
    "numerology",
    "yijing_and_symbolism",
    "liuyao_and_meihua",
    "date_selection",
    "fengshui",
    "tarot",
    "name_studies",
    "onmyodo",
    "western_astrology",
    "vedic_astrology",
    "ziwei_doushu",
    "qizheng_siyu",
    "human_design",
    "qimen_dunjia",
    "liu_ren",
    "kabbalah",
    "physiognomy",
    "daoist_arts",
    "alchemy_and_hermeticism",
    "modern_esotericism",
}


def birth_details_error(details: Any) -> str:
    if getattr(details, "parse_error", ""):
        return str(details.parse_error)
    if getattr(details, "has_conflict", False):
        return str(details.conflict_note or "出生信息存在冲突，请先确认。")
    birth_dt = getattr(details, "birth_datetime", None)
    if birth_dt and birth_dt.year >= HIGH_RISK_FUTURE_YEAR:
        return "识别到的出生年份明显超出现实范围，请先确认出生日期是否填写正确。"
    return ""

REQUIRED_INPUTS = {
    "bazi": ["birth_datetime"],
    "numerology": ["birth_date"],
    "yijing_and_symbolism": ["question", "casting_method", "numbers_or_datetime"],
    "qizheng_siyu": ["birth_datetime", "birth_location"],
    "ziwei_doushu": ["birth_datetime", "gender"],
    "qimen_dunjia": ["event_datetime", "question"],
    "liu_ren": ["event_datetime", "question"],
    "liuyao_and_meihua": ["hexagram_or_casting_data", "question"],
    "date_selection": ["event_type", "candidate_dates", "location"],
    "name_studies": ["name", "purpose"],
    "physiognomy": ["image_or_description", "observation_context"],
    "fengshui": ["location_or_floorplan", "facing_direction"],
    "daoist_arts": ["topic", "source_or_lineage"],
    "western_astrology": ["birth_datetime", "birth_location"],
    "vedic_astrology": ["birth_datetime", "birth_location"],
    "tarot": ["question", "spread", "cards"],
    "kabbalah": ["topic", "sephirah_or_path"],
    "alchemy_and_hermeticism": ["topic", "text_or_image"],
    "onmyodo": ["date", "direction_or_location", "event_type"],
    "human_design": ["birth_datetime", "birth_location"],
    "modern_esotericism": ["topic", "source"],
}

KNOWN_SYSTEMS = set(REQUIRED_INPUTS)

BIRTH_CONTEXT_MARKERS = (
    "出生",
    "生于",
    "生於",
    "生日",
    "诞生",
    "誕生",
    "农历",
    "農曆",
    "阴历",
    "陰曆",
    "阳历",
    "陽曆",
    "公历",
    "公曆",
)

QUESTION_DATETIME_SNIPPET_RE = re.compile(
    r"("
    r"\d{4}\s*[-/.]\s*\d{1,2}\s*[-/.]\s*\d{1,2}(?:\s+\d{1,2}\s*:\s*\d{1,2})?"
    r"|"
    r"\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日"
    r"(?:\s*(?:凌晨|早上|上午|中午|下午|傍晚|晚上)?\s*\d{1,2}\s*(?:点|時|时)"
    r"(?:\s*(?:半|一刻|三刻|\d{1,2}\s*分?))?)?"
    r")"
)

FULL_DATE_SNIPPET_RE = re.compile(
    r"(?P<y>\d{4})\s*(?:[-/.]|年)\s*(?P<m>\d{1,2})\s*(?:[-/.]|月)\s*(?P<d>\d{1,2})\s*日?"
)

MONTH_DAY_SNIPPET_RE = re.compile(r"(?<!\d)(?P<m>\d{1,2})\s*月\s*(?P<d>\d{1,2})\s*日")


def missing_inputs(system: str, payload: dict[str, Any]) -> list[str]:
    required = REQUIRED_INPUTS.get(system, [])
    missing = []
    for item in required:
        value = payload.get(item)
        if value in (None, "", []):
            missing.append(item)
    return missing


def parse_birth_date(value: str) -> date | None:
    details = parse_birth_details(value)
    if details.birth_datetime:
        return details.birth_datetime.date()
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def parse_event_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    return parse_datetime_from_text(text)


def parse_question_event_datetime(question: str) -> datetime | None:
    normalized = str(question or "").strip()
    if not normalized:
        return None

    for match in QUESTION_DATETIME_SNIPPET_RE.finditer(normalized):
        context = normalized[max(0, match.start() - 10) : min(len(normalized), match.end() + 10)]
        if any(marker in context for marker in BIRTH_CONTEXT_MARKERS):
            continue
        parsed = parse_datetime_from_text(match.group(0))
        if parsed:
            return parsed

    if any(marker in normalized for marker in BIRTH_CONTEXT_MARKERS):
        return None
    return parse_datetime_from_text(normalized)


def parse_relative_event_date(value: Any) -> date | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    today = date.today()
    relative_map = {
        "今天": 0,
        "今日": 0,
        "明天": 1,
        "明日": 1,
        "后天": 2,
        "後天": 2,
        "大后天": 3,
        "大後天": 3,
    }
    for token, delta in relative_map.items():
        if token in text:
            return today.fromordinal(today.toordinal() + delta)
    week_map = {
        "这周": 0,
        "本周": 0,
        "下周": 7,
        "下下周": 14,
    }
    for token, delta in week_map.items():
        if token in text:
            return today.fromordinal(today.toordinal() + delta)
    return None


def parse_age_hint(value: Any) -> int | None:
    if value in (None, ""):
        return None
    text = str(value)
    match = re.search(r"(\d{1,3})\s*(?:岁|歲)?", text)
    if not match:
        return None
    age = int(match.group(1))
    return age if 0 < age < 120 else None


def default_now_in_timezone(timezone_name: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(timezone_name)).replace(second=0, microsecond=0, tzinfo=None)
    except Exception:
        return datetime.now().replace(second=0, microsecond=0)


def resolve_divination_datetime(
    payload: dict[str, Any],
    question: str,
    default_timezone: str = "Asia/Shanghai",
) -> tuple[datetime, str, str]:
    timezone_name = str(payload.get("timezone") or payload.get("tz_str") or default_timezone).strip() or default_timezone

    year = payload.get("year")
    month = payload.get("month")
    day = payload.get("day")
    hour = payload.get("hour")
    minute = int(payload.get("minute") or 0)
    if all(value not in (None, "") for value in [year, month, day, hour]):
        return (
            datetime(int(year), int(month), int(day), int(hour), minute),
            timezone_name,
            "structured-input",
        )

    explicit_event = parse_event_datetime(payload.get("event_datetime"))
    if explicit_event:
        return explicit_event, timezone_name, "event_datetime"

    date_text = str(payload.get("date") or "").strip()
    if date_text:
        try:
            base_date = date.fromisoformat(date_text[:10])
            return (
                datetime(base_date.year, base_date.month, base_date.day, int(payload.get("hour") or 0), minute),
                timezone_name,
                "date+time",
            )
        except ValueError:
            pass

    parsed_question_dt = parse_question_event_datetime(question)
    if parsed_question_dt:
        return parsed_question_dt, timezone_name, "question-datetime"

    return default_now_in_timezone(timezone_name), timezone_name, "inferred-current-time"


def parse_date_candidates(value: Any) -> tuple[date, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        results = []
        for item in value:
            parsed = parse_birth_date(str(item))
            if parsed:
                results.append(parsed)
        return tuple(results)

    text = str(value)
    results: list[date] = []
    for match in re.finditer(r"(\d{4})[-/.年]\s*(\d{1,2})[-/.月]\s*(\d{1,2})", text):
        lookback = text[max(0, match.start() - 8) : match.start()]
        if any(token in lookback for token in ["出生", "生于", "生日", "农历", "阳历", "公历"]):
            continue
        year, month, day = match.groups()
        results.append(date(int(year), int(month), int(day)))
    current_year = date.today().year
    for match in re.finditer(r"(?<!\d)(\d{1,2})\s*月\s*(\d{1,2})\s*日", text):
        lookback = text[max(0, match.start() - 8) : match.start()]
        if any(token in lookback for token in ["出生", "生于", "生日", "农历", "阳历", "公历"]):
            continue
        month, day = match.groups()
        candidate = date(current_year, int(month), int(day))
        if candidate not in results:
            results.append(candidate)
    return tuple(results)


def parse_single_date_candidate(value: Any) -> date | None:
    candidates = parse_date_candidates(value)
    if candidates:
        return candidates[0]
    return None


def infer_event_type(question: str) -> str:
    if any(token in question for token in ["搬家", "入宅", "迁居"]):
        return "move"
    if any(token in question for token in ["结婚", "婚礼", "领证"]):
        return "wedding"
    if any(token in question for token in ["签约", "合同", "签合同", "合作"]):
        return "contract"
    if any(token in question for token in ["出行", "旅行", "出差"]):
        return "travel"
    return "general"


def infer_name_purpose(question: str) -> str:
    text = str(question or "")
    if any(token in text for token in ["品牌", "品牌名", "公司", "公司名", "店名", "商标", "商标名"]):
        return "brand"
    if any(token in text for token in ["正式姓名", "正式名字", "大名", "乳名", "孩子", "宝宝", "小孩", "新生儿", "男孩", "女孩"]):
        return "personal"
    if any(token in text for token in ["艺名", "笔名"]):
        return "stage"
    if "网名" in text and not any(token in text for token in ["别太像网名", "不要网名", "不像网名", "别像网名"]):
        return "stage"
    return "personal"


def parse_participant_birth_dates(payload: dict[str, Any], question: str) -> tuple[date, ...]:
    values: list[date] = []
    raw_list = payload.get("participant_birth_dates")
    if isinstance(raw_list, (list, tuple)):
        for item in raw_list:
            parsed = parse_birth_date(str(item))
            if parsed:
                values.append(parsed)
    for key in ["participant_birth", "birth_datetime", "birth_date"]:
        raw = payload.get(key)
        if raw:
            parsed = parse_birth_date(str(raw))
            if parsed and parsed not in values:
                values.append(parsed)
    if any(token in question for token in BIRTH_CONTEXT_MARKERS):
        question_birth = parse_birth_details(question)
        if question_birth.birth_datetime:
            parsed = question_birth.birth_datetime.date()
            if parsed not in values:
                values.append(parsed)
    return tuple(values)


def parse_facing_direction_hint(question: str) -> str:
    directional_patterns = [
        r"坐[东南西北]{1,2}朝[东南西北]{1,2}",
        r"往[东南西北]{1,2}(?:方向)?",
        r"朝[东南西北]{1,2}(?:方向)?",
        r"[东南西北]{1,2}向",
        r"[东南西北]{1,2}朝向",
        r"[东南西北]{1,2}方向",
        r"\d{1,3}(?:\.\d+)?\s*度",
    ]
    for pattern in directional_patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(0).lstrip("往朝")
    return ""


def parse_build_year(value: Any) -> int | None:
    if value is None:
        return None
    text = str(value)
    match = re.search(r"(19\d{2}|20\d{2})", text)
    return int(match.group(1)) if match else None


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def parse_name_candidate(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text in {
        "我想起个名字",
        "我想起一个名字",
        "我想取个名字",
        "我想取一个名字",
        "帮我起个名字",
        "帮我取个名字",
        "起个名字",
        "取个名字",
        "起一个名字",
        "取一个名字",
    }:
        return ""
    explicit = re.search(r"(?:候选名是|名字是|姓名是|备选名是|叫|名为)[：:\s]*([A-Za-z\u4e00-\u9fff]{2,12})", text)
    if explicit:
        candidate = re.split(r"(?:适合|好吗|行吗|怎么样|如何|命格|五行|用途|吗|么|呢|，|。|,)", explicit.group(1))[0]
        return candidate
    scoped = re.search(r"(?:名字|姓名)[：:\s]*([A-Za-z\u4e00-\u9fff]{2,12})", text)
    if scoped:
        candidate = re.split(r"(?:适合|好吗|行吗|怎么样|如何|命格|五行|用途|吗|么|呢|，|。|,)", scoped.group(1))[0]
        if candidate in {"的名字", "这名字"}:
            candidate = ""
        if candidate.startswith("这事") or candidate.startswith("这个事") or candidate.startswith("这件事"):
            candidate = ""
        return candidate
    quoted = re.search(r"[\"'“”‘’]([A-Za-z\u4e00-\u9fff]{2,12})[\"'“”‘’]", text)
    if quoted:
        return quoted.group(1)
    if any(token in text for token in ("姓", "男孩", "女孩", "宝宝", "小孩", "孩子", "想要", "最好", "方向", "生僻字", "正式姓名", "正式名字")):
        return ""
    if any(token in text for token in ("起名", "取名", "名字", "候选名")) and len(text) > 4:
        return ""
    pure = re.fullmatch(r"[A-Za-z\u4e00-\u9fff]{2,12}", text)
    return pure.group(0) if pure else ""


def infer_name_candidates(question: str) -> list[str]:
    text = str(question or "")
    explicit = re.search(r"(?:候选名是|名字是|姓名是|备选名是)\s*([A-Za-z\u4e00-\u9fff、，,\s]{2,40})", text)
    if explicit:
        raw = re.split(r"(?:主要用于|用于|想看|适不适合|好不好|怎么样|出生于|出生在|生于|生日是|，出|, ?born)", explicit.group(1))[0]
        return [item.strip() for item in re.split(r"[、，,\s]+", raw) if 1 < len(item.strip()) <= 12][:4]
    return []


def infer_surname_for_naming(question: str) -> str:
    text = str(question or "")
    patterns = [
        r"姓[：:\s]*([A-Za-z\u4e00-\u9fff]{1,3}?)(?=(?:起名|取名|起什么名字|取什么名字|起一个名字|取一个名字|名字|名|，|,|。|；|;|\s|$))",
        r"([A-Za-z\u4e00-\u9fff]{1,3})姓",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            value = re.split(r"(?:的|，|,|。|；|;|\s|起名|取名|起什么名字|取什么名字|名字)", match.group(1))[0].strip()
            if 0 < len(value) <= 3:
                return value
    return ""


def is_name_generation_request(question: str) -> bool:
    text = str(question or "")
    naming_markers = ("起名", "取名", "起什么名字", "取什么名字", "起个名字", "取个名字", "起一个名字", "取一个名字", "名字怎么起", "帮起名", "帮取名")
    target_markers = ("宝宝", "宝贝", "小孩", "孩子", "婴儿", "新生儿", "女宝宝", "男宝宝", "女宝", "男宝")
    gender_markers = ("男孩", "女孩", "男宝宝", "女宝宝", "男宝", "女宝", "儿子", "女儿")
    purpose_or_style_markers = (
        "正式姓名",
        "正式名字",
        "大名",
        "小名",
        "乳名",
        "英文名",
        "候选名",
        "名字推荐",
        "诗意",
        "顺口",
        "不土",
        "不网红",
        "清雅",
        "大气",
        "稳重",
        "风格",
    )
    if any(token in text for token in naming_markers) and any(token in text for token in target_markers):
        return True
    if any(token in text for token in naming_markers) and "姓" in text and any(
        token in text for token in (*gender_markers, *purpose_or_style_markers)
    ):
        return True
    if any(token in text for token in ("候选名", "名字推荐", "起三个名字", "取三个名字", "起几个名字", "取几个名字")) and (
        "姓" in text or any(token in text for token in gender_markers)
    ):
        return True
    if "姓" in text and any(token in text for token in (*gender_markers, *purpose_or_style_markers, "方向", "先给方向", "先听方向", "三组方向")):
        return True
    return "姓" in text and any(token in text for token in target_markers) and any(
        token in text for token in ("名字", "这事", "起名", "取名", "方向", "顺口", "不土", "不网红")
    )


def infer_birth_context_payload(payload: dict[str, Any]) -> tuple[Any, str]:
    raw_birth_datetime = str(payload.get("birth_datetime") or "").strip()
    raw_birth_info = str(payload.get("birth_info") or "").strip()
    raw_question = str(payload.get("question") or "").strip()
    raw = raw_birth_datetime or raw_birth_info or raw_question
    details = parse_birth_details(raw)
    if not details.birth_datetime and raw_birth_datetime:
        details = parse_birth_details(f"出生于{raw_birth_datetime}")
    birth_location = str(payload.get("birth_location") or details.birth_location or "").strip()
    if not birth_location:
        fallback_location = str(payload.get("birth_city") or payload.get("location") or "").strip()
        birth_location = fallback_location
    return details, birth_location


def build_fengshui_map_context(location_text: str) -> dict[str, Any]:
    cleaned = str(location_text or "").strip()
    if not cleaned or not has_tencent_map_key():
        return {}
    resolved = geocode_address(cleaned)
    static_url = static_map_url(
        resolved.lat,
        resolved.lng,
        zoom=18,
        width=960,
        height=540,
        scale=2,
        markers=f"color:red|label:A|{resolved.lat},{resolved.lng}",
    )
    poi_hits = collect_nearby_poi_signals(resolved.lat, resolved.lng, radius=1500)
    poi_summary = {
        category: {
            "count": len(entries),
            "nearest_distance": min(int(item.get("distance") or 0) for item in entries) if entries else None,
        }
        for category, entries in poi_hits.items()
    }
    return {
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
        "static_map_url": static_url,
        "poi_summary": poi_summary,
        "poi_hits": poi_hits,
    }


def calculate_system(system: str, payload: dict[str, Any]) -> tuple[dict[str, Any], int]:
    if system not in KNOWN_SYSTEMS:
        return {"error": f"Unknown system: {system}"}, 404

    if system == "bazi":
        details, inferred_birth_location = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "\u9700\u8981 birth_datetime\uff0c\u4f8b\u5982 1990-05-12 14:30\uff0c\u6216\u519c\u53861990\u5e74\u56db\u6708\u5341\u516b\u65e5\u4e0b\u5348\u4e24\u70b9\u534a\u3002"
            }, 400
        if not details.has_time:
            return {
                "error": "\u5df2\u8bc6\u522b\u51fa\u751f\u65e5\u671f\uff0c\u4f46\u8fd8\u7f3a\u5c11\u51fa\u751f\u65f6\u95f4\u6216\u65f6\u8fb0\uff0c\u4f8b\u5982 14:30 \u6216 \u4e0b\u5348\u4e24\u70b9\u534a\u3002"
            }, 400
        try:
            result = calculate_bazi(
                BaziInput(
                    birth_datetime=details.birth_datetime,
                    gender=str(payload.get("gender") or details.gender or ""),
                    birth_location=str(payload.get("birth_location") or inferred_birth_location or details.birth_location or ""),
                    calendar=str(payload.get("calendar") or "solar") or "solar",
                    use_true_solar_time=bool(payload.get("use_true_solar_time") or False),
                    late_zi_hour_next_day=bool(payload.get("late_zi_hour_next_day") or False),
                )
            )
            result["input"]["calendar_source"] = details.calendar
            result["input"]["parsed_gender"] = details.gender
            result["input"]["parsed_birth_location"] = details.birth_location
            return result, 200
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "numerology":
        raw = str(payload.get("birth_date") or payload.get("birth_datetime") or payload.get("question") or "")
        birth = parse_birth_date(raw)
        if not birth:
            return {"error": "\u9700\u8981 birth_date\uff0c\u4f8b\u5982 1990-05-12\u3002"}, 400
        return (
            calculate_numerology(
                NumerologyInput(
                    birth_date=birth,
                    name=str(payload.get("name") or ""),
                    system=str(payload.get("numerology_system") or "pythagorean"),
                )
            ),
            200,
        )

    if system == "yijing_and_symbolism":
        question = str(payload.get("question") or "").strip()
        method = str(payload.get("casting_method") or "").strip().lower()
        raw_cast = payload.get("numbers_or_datetime") or payload.get("cast_datetime") or payload.get("event_datetime")
        if not question:
            return {"error": "question is required for yijing_and_symbolism"}, 400
        if not method:
            if parse_numbers(raw_cast):
                method = "numbers"
            elif parse_event_datetime(raw_cast):
                method = "time"
        if method == "numbers":
            numbers = parse_numbers(raw_cast)
            if len(numbers) < 2:
                return {"error": "numbers casting requires numbers_or_datetime with at least two integers"}, 400
            try:
                return (
                    calculate_yijing(
                        YijingInput(
                            question=question,
                            casting_method=method,
                            numbers=numbers,
                            moving_line=int(payload["moving_line"]) if payload.get("moving_line") else None,
                            background=str(payload.get("background") or ""),
                        )
                    ),
                    200,
                )
            except Exception as exc:
                return {"error": str(exc)}, 400
        if method == "time":
            cast_dt = parse_event_datetime(raw_cast)
            if not cast_dt:
                return {"error": "time casting requires a parseable datetime string"}, 400
            try:
                return (
                    calculate_yijing(
                        YijingInput(
                            question=question,
                            casting_method=method,
                            cast_datetime=cast_dt,
                            moving_line=int(payload["moving_line"]) if payload.get("moving_line") else None,
                            background=str(payload.get("background") or ""),
                        )
                    ),
                    200,
                )
            except Exception as exc:
                return {"error": str(exc)}, 400
        return {"error": "casting_method must be numbers or time"}, 400

    if system == "liuyao_and_meihua":
        question = str(payload.get("question") or "").strip()
        method = str(payload.get("casting_method") or "").strip().lower()
        raw_cast = payload.get("hexagram_or_casting_data") or payload.get("numbers_or_datetime") or payload.get("cast_datetime") or payload.get("event_datetime")
        if not question:
            return {"error": "question is required for liuyao_and_meihua"}, 400
        if not method:
            if parse_numbers(raw_cast):
                method = "numbers"
            elif parse_event_datetime(raw_cast):
                method = "time"
        if method == "numbers":
            numbers = parse_numbers(raw_cast)
            if len(numbers) < 2:
                return {"error": "numbers casting requires at least two integers"}, 400
            try:
                return (
                    calculate_liuyao(
                        LiuyaoInput(
                            question=question,
                            casting_method=method,
                            numbers=numbers,
                            moving_line=int(payload["moving_line"]) if payload.get("moving_line") else None,
                            background=str(payload.get("background") or ""),
                        )
                    ),
                    200,
                )
            except Exception as exc:
                return {"error": str(exc)}, 400
        if method == "time":
            cast_dt = parse_event_datetime(raw_cast)
            if not cast_dt:
                return {"error": "time casting requires a parseable datetime string"}, 400
            try:
                return (
                    calculate_liuyao(
                        LiuyaoInput(
                            question=question,
                            casting_method=method,
                            cast_datetime=cast_dt,
                            moving_line=int(payload["moving_line"]) if payload.get("moving_line") else None,
                            background=str(payload.get("background") or ""),
                        )
                    ),
                    200,
                )
            except Exception as exc:
                return {"error": str(exc)}, 400
        return {"error": "casting_method must be numbers or time"}, 400

    if system == "tarot":
        question = str(payload.get("question") or "").strip()
        spread = str(payload.get("spread") or "").strip()
        cards = normalize_cards(payload.get("cards"))
        if not question:
            return {"error": "question is required for tarot"}, 400
        if not spread:
            return {"error": "spread is required for tarot"}, 400
        if not cards:
            return {"error": "cards are required for tarot; the local engine will not fabricate random draws"}, 400
        try:
            return (
                calculate_tarot(
                    TarotInput(
                        question=question,
                        spread=spread,
                        cards=cards,
                        time_range=str(payload.get("time_range") or ""),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "date_selection":
        question = str(payload.get("question") or "").strip()
        event_type = str(payload.get("event_type") or infer_event_type(question))
        candidate_dates = parse_date_candidates(payload.get("candidate_dates") or question)
        if not candidate_dates:
            single = parse_single_date_candidate(payload.get("date") or question)
            if single:
                candidate_dates = (single,)
        if not candidate_dates:
            return {"error": "candidate_dates are required for date_selection"}, 400
        try:
            return (
                calculate_date_selection(
                    DateSelectionInput(
                        event_type=event_type,
                        candidate_dates=candidate_dates,
                        location=str(payload.get("location") or ""),
                        participant_birth_dates=parse_participant_birth_dates(payload, question),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "fengshui":
        question = str(payload.get("question") or "").strip()
        details, _ = infer_birth_context_payload(
            {
                "birth_datetime": payload.get("birth_datetime"),
                "birth_info": payload.get("occupant_birth"),
                "question": question,
            }
        )
        raw_direction = str(payload.get("facing_direction") or parse_facing_direction_hint(question) or "")
        if not raw_direction:
            return {"error": "facing_direction is required for fengshui"}, 400
        location_text = str(payload.get("location_or_floorplan") or payload.get("location") or question or "")
        map_context = {}
        try:
            map_context = build_fengshui_map_context(location_text)
        except Exception:
            map_context = {}
        try:
            return (
                calculate_fengshui(
                    FengShuiInput(
                        location_or_floorplan=location_text,
                        facing_direction=raw_direction,
                        birth_date=details.birth_datetime.date() if details.birth_datetime else parse_birth_date(str(payload.get("birth_date") or "")),
                        gender=str(payload.get("gender") or details.gender or ""),
                        build_year=parse_build_year(payload.get("build_year") or question),
                        map_context=map_context or None,
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "name_studies":
        question = str(payload.get("question") or "").strip()
        candidates = infer_name_candidates(question)
        parsed_name = parse_name_candidate(question)
        if parsed_name.startswith("是") and len(parsed_name) > 2:
            parsed_name = parsed_name[1:]
        name = str(payload.get("name") or (candidates[0] if candidates else "") or parsed_name).strip()
        if not name and is_name_generation_request(question):
            surname = str(payload.get("surname") or infer_surname_for_naming(question)).strip()
            generated = generate_name_candidates(
                surname=surname,
                purpose=str(payload.get("purpose") or infer_name_purpose(question)),
                birth_info=str(payload.get("birth_info") or payload.get("birth_datetime") or question),
                gender_hint=str(payload.get("gender") or question),
                culture_context=str(payload.get("culture_context") or question),
                limit=10,
            )
            if generated:
                scored: list[dict[str, Any]] = []
                for candidate in generated:
                    candidate_name = str(candidate.get("name") or "").strip()
                    if not candidate_name:
                        continue
                    evaluated = calculate_name_studies(
                        NameStudiesInput(
                            name=candidate_name,
                            purpose=str(payload.get("purpose") or infer_name_purpose(question)),
                            birth_info=str(payload.get("birth_info") or payload.get("birth_datetime") or question),
                            culture_context=str(payload.get("culture_context") or question),
                        )
                    )
                    scored.append(
                        {
                            "name": candidate_name,
                            "score": int(evaluated.get("score") or 0),
                            "confidence": candidate.get("confidence") or evaluated.get("confidence") or "",
                            "primary_finding": evaluated.get("primary_finding") or "",
                            "supporting_signals": list(candidate.get("supporting_signals") or evaluated.get("supporting_signals") or [])[:3],
                            "expression_bridge_number": candidate.get("expression_bridge_number")
                            or (evaluated.get("derived_factors") or {}).get("expression_bridge_number"),
                            "source_title": candidate.get("source_title") or "",
                            "source_quote": candidate.get("source_quote") or "",
                            "source_excerpt": candidate.get("source_excerpt") or "",
                            "meaning": candidate.get("meaning") or "",
                            "style_tags": list(candidate.get("style_tags") or []),
                            "preferred_elements": list(candidate.get("preferred_elements") or []),
                            "character_elements": list(candidate.get("character_elements") or []),
                            "why_selected": candidate.get("why_selected") or "",
                            "birth_support_note": candidate.get("birth_support_note") or "",
                        }
                    )
                scored.sort(key=lambda item: (item["score"], item["name"]), reverse=True)
                best_name = scored[0]["name"]
                best_result = calculate_name_studies(
                    NameStudiesInput(
                        name=best_name,
                        purpose=str(payload.get("purpose") or infer_name_purpose(question)),
                        birth_info=str(payload.get("birth_info") or payload.get("birth_datetime") or question),
                        culture_context=str(payload.get("culture_context") or question),
                    )
                )
                best_result["question_type"] = "name_generation"
                best_result["generated_candidates"] = scored
                best_result["used_inputs"]["surname"] = surname
                best_result["used_inputs"]["gender"] = str(payload.get("gender") or parse_birth_details(question).gender or "").strip()
                return best_result, 200
        if not name:
            return {"error": "name is required for name_studies"}, 400
        try:
            return (
                calculate_name_studies(
                    NameStudiesInput(
                        name=name,
                        purpose=str(payload.get("purpose") or infer_name_purpose(question)),
                        birth_info=str(payload.get("birth_info") or payload.get("birth_datetime") or ""),
                        culture_context=str(payload.get("culture_context") or ""),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "physiognomy":
        question = str(payload.get("question") or "").strip()
        description = str(payload.get("image_or_description") or payload.get("description") or question).strip()
        if len(description) < 6:
            return {"error": "image_or_description is required for physiognomy"}, 400
        details = parse_birth_details(question)
        try:
            return (
                calculate_physiognomy(
                    PhysiognomyInput(
                        image_or_description=description,
                        observation_context=str(payload.get("observation_context") or payload.get("context") or "").strip(),
                        age=parse_age_hint(payload.get("age") or question),
                        gender=str(payload.get("gender") or details.gender or "").strip(),
                        time_state=str(payload.get("time_state") or "").strip(),
                        question_type=str(payload.get("question_type") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "daoist_arts":
        question = str(payload.get("question") or "").strip()
        topic = str(payload.get("topic") or question).strip()
        if not topic:
            return {"error": "topic is required for daoist_arts"}, 400
        try:
            return (
                calculate_daoist_arts(
                    DaoistArtsInput(
                        topic=topic,
                        source_or_lineage=str(payload.get("source_or_lineage") or payload.get("source") or "").strip(),
                        ritual_text=str(payload.get("ritual_text") or payload.get("text") or question).strip(),
                        region=str(payload.get("region") or "").strip(),
                        ethics_limit=str(payload.get("ethics_limit") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "alchemy_and_hermeticism":
        question = str(payload.get("question") or "").strip()
        topic = str(payload.get("topic") or question).strip()
        if not topic:
            return {"error": "topic is required for alchemy_and_hermeticism"}, 400
        try:
            return (
                calculate_alchemy_and_hermeticism(
                    AlchemyHermeticismInput(
                        topic=topic,
                        text_or_image=str(payload.get("text_or_image") or payload.get("text") or question).strip(),
                        stage_model=str(payload.get("stage_model") or payload.get("stage") or "").strip(),
                        tradition=str(payload.get("tradition") or payload.get("source") or "").strip(),
                        practical_context=str(payload.get("practical_context") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "modern_esotericism":
        question = str(payload.get("question") or "").strip()
        topic = str(payload.get("topic") or question).strip()
        if not topic:
            return {"error": "topic is required for modern_esotericism"}, 400
        try:
            return (
                calculate_modern_esotericism(
                    ModernEsotericismInput(
                        topic=topic,
                        source=str(payload.get("source") or "").strip(),
                        practice_description=str(payload.get("practice_description") or payload.get("text") or question).strip(),
                        cultural_context=str(payload.get("cultural_context") or "").strip(),
                        risk_level=str(payload.get("risk_level") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "kabbalah":
        question = str(payload.get("question") or "").strip()
        topic = str(payload.get("topic") or question).strip()
        if not topic:
            return {"error": "topic is required for kabbalah"}, 400
        try:
            return (
                calculate_kabbalah(
                    KabbalahInput(
                        topic=topic,
                        sephirah_or_path=str(
                            payload.get("sephirah_or_path")
                            or payload.get("sephirah")
                            or payload.get("path")
                            or ""
                        ).strip(),
                        source=str(payload.get("source") or payload.get("source_or_lineage") or "").strip(),
                        intention=str(payload.get("intention") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "western_astrology":
        details, birth_location = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "birth_datetime is required for western_astrology, for example 1990-05-12 14:30."
            }, 400
        if not details.has_time:
            return {
                "error": "western_astrology requires a specific birth time to compute houses and ascendant."
            }, 400
        if not birth_location and parse_float(payload.get("birth_lat")) is None:
            return {"error": "birth_location or birth_lat/birth_lng is required for western_astrology."}, 400
        try:
            return (
                calculate_western_astrology(
                    WesternAstrologyInput(
                        birth_datetime=details.birth_datetime,
                        birth_location=birth_location,
                        birth_lat=parse_float(payload.get("birth_lat")),
                        birth_lng=parse_float(payload.get("birth_lng")),
                        tz_str=str(payload.get("tz_str") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "ziwei_doushu":
        details, _ = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "birth_datetime is required for ziwei_doushu, for example 1990-05-12 14:30."
            }, 400
        if not details.has_time:
            return {
                "error": "ziwei_doushu requires a specific birth time or shichen."
            }, 400
        gender = str(payload.get("gender") or details.gender or "").strip()
        if not gender:
            return {"error": "gender is required for ziwei_doushu."}, 400
        try:
            return (
                calculate_ziwei_doushu(
                    ZiweiDoushuInput(
                        birth_datetime=details.birth_datetime,
                        gender=gender,
                        calendar=details.calendar,
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "qizheng_siyu":
        details, birth_location = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "birth_datetime is required for qizheng_siyu, for example 1990-05-12 14:30."
            }, 400
        if not details.has_time:
            return {
                "error": "qizheng_siyu requires a specific birth time to place governors and remainders into houses."
            }, 400
        if not birth_location and parse_float(payload.get("birth_lat")) is None:
            return {"error": "birth_location or birth_lat/birth_lng is required for qizheng_siyu."}, 400
        try:
            return (
                calculate_qizheng_siyu(
                    QizhengSiyuInput(
                        birth_datetime=details.birth_datetime,
                        birth_location=birth_location,
                        birth_lat=parse_float(payload.get("birth_lat")),
                        birth_lng=parse_float(payload.get("birth_lng")),
                        tz_str=str(payload.get("tz_str") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "vedic_astrology":
        details, birth_location = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "birth_datetime is required for vedic_astrology, for example 1990-05-12 14:30."
            }, 400
        if not details.has_time:
            return {
                "error": "vedic_astrology requires a specific birth time to compute lagna and house structure."
            }, 400
        if not birth_location and parse_float(payload.get("birth_lat")) is None:
            return {"error": "birth_location or birth_lat/birth_lng is required for vedic_astrology."}, 400
        try:
            return (
                calculate_vedic_astrology(
                    VedicAstrologyInput(
                        birth_datetime=details.birth_datetime,
                        birth_location=birth_location,
                        ayanamsa=str(payload.get("ayanamsa") or "LAHIRI").strip() or "LAHIRI",
                        birth_lat=parse_float(payload.get("birth_lat")),
                        birth_lng=parse_float(payload.get("birth_lng")),
                        tz_str=str(payload.get("tz_str") or "").strip(),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "human_design":
        details, birth_location = infer_birth_context_payload(payload)
        details_error = birth_details_error(details)
        if details_error:
            return {"error": details_error}, 400
        if not details.birth_datetime:
            return {
                "error": "birth_datetime is required for human_design, for example 1990-05-12 14:30."
            }, 400
        if not details.has_time:
            return {
                "error": "human_design requires a specific birth time to derive profile, authority, and full bodygraph structure."
            }, 400
        if not birth_location and parse_float(payload.get("birth_lat")) is None:
            return {"error": "birth_location or birth_lat/birth_lng is required for human_design."}, 400
        try:
            return (
                calculate_human_design(
                    HumanDesignInput(
                        birth_datetime=details.birth_datetime,
                        birth_location=birth_location,
                        birth_lat=parse_float(payload.get("birth_lat")),
                        birth_lng=parse_float(payload.get("birth_lng")),
                        tz_str=str(payload.get("tz_str") or "").strip(),
                        node_type=str(payload.get("node_type") or payload.get("nodeType") or "true").strip() or "true",
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "qimen_dunjia":
        question = str(payload.get("question") or "").strip()
        event_datetime, timezone_name, time_source = resolve_divination_datetime(payload, question)
        try:
            return (
                calculate_qimen_dunjia(
                    QimenDunjiaInput(
                        event_datetime=event_datetime,
                        timezone=timezone_name,
                        question=question,
                        pan_type=str(payload.get("pan_type") or payload.get("panType") or "zhuan").strip() or "zhuan",
                        ju_method=str(payload.get("ju_method") or payload.get("juMethod") or "chaibu").strip() or "chaibu",
                        zhi_fu_ji_gong=str(payload.get("zhi_fu_ji_gong") or payload.get("zhiFuJiGong") or "ji_liuyi").strip() or "ji_liuyi",
                        time_source=time_source,
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "liu_ren":
        question = str(payload.get("question") or "").strip()
        details = parse_birth_details(str(payload.get("birth_datetime") or question or ""))
        event_datetime, timezone_name, time_source = resolve_divination_datetime(payload, question)
        birth_year = payload.get("birth_year") or payload.get("birthYear")
        if birth_year in (None, "") and details.birth_datetime:
            birth_year = details.birth_datetime.year
        try:
            return (
                calculate_liu_ren(
                    LiuRenInput(
                        event_datetime=event_datetime,
                        timezone=timezone_name,
                        question=question,
                        birth_year=int(birth_year) if birth_year not in (None, "") else None,
                        gender=str(payload.get("gender") or details.gender or ""),
                        time_source=time_source,
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    if system == "onmyodo":
        question = str(payload.get("question") or "").strip()
        direction = str(payload.get("direction_or_location") or payload.get("location") or payload.get("facing_direction") or parse_facing_direction_hint(question) or "")
        event_date = parse_birth_date(str(payload.get("date") or payload.get("event_datetime") or "")) or (
            parse_date_candidates(question)[0] if parse_date_candidates(question) else None
        )
        if not event_date:
            event_date = parse_relative_event_date(question)
        if not event_date:
            return {"error": "date is required for onmyodo"}, 400
        if not direction:
            return {"error": "direction_or_location is required for onmyodo"}, 400
        try:
            return (
                calculate_onmyodo(
                    OnmyodoInput(
                        event_date=event_date,
                        direction_or_location=direction,
                        event_type=str(payload.get("event_type") or infer_event_type(question)),
                    )
                ),
                200,
            )
        except Exception as exc:
            return {"error": str(exc)}, 400

    return {"error": f"No active handler found for system: {system}"}, 500
