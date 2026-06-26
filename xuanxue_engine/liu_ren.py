from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .node_bridge import run_node_bridge


BRIDGE_PATH = Path(__file__).resolve().with_name("daliuren_bridge.mjs")


@dataclass(frozen=True)
class LiuRenInput:
    event_datetime: datetime
    timezone: str = "Asia/Shanghai"
    question: str = ""
    birth_year: int | None = None
    gender: str = ""
    time_source: str = "explicit"


def normalize_gender(value: str) -> str:
    lowered = (value or "").strip().lower()
    if lowered in {"m", "male", "男", "男性"}:
        return "male"
    if lowered in {"f", "female", "女", "女性"}:
        return "female"
    return ""


def run_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    return run_node_bridge(BRIDGE_PATH, payload, "daliuren bridge")


def transmission_entry(label: str, values: list[str]) -> dict[str, str]:
    padded = list(values) + ["", "", "", ""]
    return {
        "label": label,
        "branch": padded[0],
        "general": padded[1],
        "relation": padded[2],
        "hidden_stem": padded[3],
    }


def format_time_source(value: str) -> str:
    mapping = {
        "explicit": "explicit divination time",
        "structured-input": "structured divination time",
        "event_datetime": "event datetime",
        "date+time": "date plus time fields",
        "question-datetime": "datetime parsed from the question",
        "inferred-current-time": "current ask-time fallback",
    }
    return mapping.get(value, value)


def calculate_liu_ren(data: LiuRenInput) -> dict[str, Any]:
    normalized_gender = normalize_gender(data.gender)
    raw = run_bridge(
        {
            "date": data.event_datetime.date().isoformat(),
            "hour": data.event_datetime.hour,
            "minute": data.event_datetime.minute,
            "timezone": data.timezone,
            "question": data.question,
            "birthYear": data.birth_year,
            "gender": normalized_gender or None,
        }
    )
    date_info = dict(raw.get("dateInfo") or {})
    san_chuan = dict(raw.get("sanChuan") or {})
    ke_ti = dict(raw.get("keTi") or {})
    si_ke = dict(raw.get("siKe") or {})

    chu = transmission_entry("chu", list(san_chuan.get("chu") or []))
    zhong = transmission_entry("zhong", list(san_chuan.get("zhong") or []))
    mo = transmission_entry("mo", list(san_chuan.get("mo") or []))

    time_note = ""
    if data.time_source != "explicit":
        time_note = f"Using a {format_time_source(data.time_source)} chart. "

    primary_finding = (
        f"{time_note}Transmission runs through {san_chuan.get('method', '')}: "
        f"chu {chu['branch']}/{chu['general']}, zhong {zhong['branch']}/{zhong['general']}, "
        f"mo {mo['branch']}/{mo['general']}; ke-ti resolves to {ke_ti.get('method', '')}."
    )

    supporting_signals = [
        f"Question time resolves to {data.event_datetime.isoformat(sep=' ', timespec='minutes')} in {data.timezone}.",
        f"Yue Jiang is {date_info.get('yueJiang', '')} ({date_info.get('yueJiangName', '')}), with xun {date_info.get('xun', '')}.",
        f"Kong wang: {', '.join(list(date_info.get('kongWang') or [])) or 'none'}; yi ma {date_info.get('yiMa', '')}; tian ma {date_info.get('tianMa', '')}.",
        f"Extra ke-ti markers: {', '.join(list(ke_ti.get('extraTypes') or [])) or 'none'}.",
    ]
    if raw.get("benMing") or raw.get("xingNian"):
        supporting_signals.append(
            f"Ben ming {raw.get('benMing', '') or 'n/a'}; xing nian {raw.get('xingNian', '') or 'n/a'}."
        )

    risk_flags = [
        "This local liu_ren engine uses taibu-core and its liuren-ts-lib-backed chart generation.",
        "Transmission extraction and ke-ti layering are real local outputs, but lineage-specific yong-shen and final judgement methods still vary significantly.",
        "The current output emphasizes tian-di-pan, si-ke, san-chuan, and ke-ti structure before any school-specific judgement overlay.",
    ]
    if data.time_source == "inferred-current-time":
        risk_flags.append(
            "No explicit divination time was supplied, so the engine fell back to the current ask time."
        )

    return {
        "system": "liu_ren",
        "question_type": "timing",
        "used_inputs": {
            "event_datetime": data.event_datetime.isoformat(sep=" ", timespec="minutes"),
            "timezone": data.timezone,
            "question": data.question,
            "birth_year": data.birth_year,
            "gender": normalized_gender,
            "time_source": data.time_source,
        },
        "missing_inputs": [],
        "derived_factors": {
            "yue_jiang": str(date_info.get("yueJiang") or ""),
            "yue_jiang_name": str(date_info.get("yueJiangName") or ""),
            "xun": str(date_info.get("xun") or ""),
            "kong_wang": list(date_info.get("kongWang") or []),
            "yi_ma": str(date_info.get("yiMa") or ""),
            "ding_ma": str(date_info.get("dingMa") or ""),
            "tian_ma": str(date_info.get("tianMa") or ""),
            "diurnal": bool(date_info.get("diurnal")),
            "ke_name": str(raw.get("keName") or ""),
            "ke_ti": ke_ti,
            "transmission_method": str(san_chuan.get("method") or ""),
            "san_chuan": {
                "chu": chu,
                "zhong": zhong,
                "mo": mo,
            },
            "si_ke": si_ke,
        },
        "raw_chart": {
            "date_info": date_info,
            "tian_di_pan": dict(raw.get("tianDiPan") or {}),
            "gong_infos": list(raw.get("gongInfos") or []),
            "shen_sha": list(raw.get("shenSha") or []),
            "dun_gan": dict(raw.get("dunGan") or {}),
            "jian_chu": dict(raw.get("jianChu") or {}),
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "This chart is tied to the divination moment and is strongest for short-range event flow, momentum, and situational judgement.",
        "confidence": "medium",
        "rules_path": [
            "divination-time normalization",
            "daliuren chart generation",
            "si-ke extraction",
            "san-chuan extraction",
            "ke-ti summarization",
        ],
    }
