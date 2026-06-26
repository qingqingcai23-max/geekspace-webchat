from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .astro_common import resolve_birth_location
from .node_bridge import run_node_bridge


BRIDGE_PATH = Path(__file__).resolve().with_name("human_design_bridge.cjs")


@dataclass(frozen=True)
class HumanDesignInput:
    birth_datetime: datetime
    birth_location: str
    birth_lat: float | None = None
    birth_lng: float | None = None
    tz_str: str = ""
    node_type: str = "true"


def run_bridge(payload: dict[str, Any]) -> dict[str, Any]:
    return run_node_bridge(BRIDGE_PATH, payload, "human design bridge")


def center_names(items: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for item in items:
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def gate_signature(chart: dict[str, Any], side: str, planet: str) -> dict[str, Any]:
    activation = dict(((chart.get("gates") or {}).get(side) or {}).get(planet) or {})
    return {
        "planet": str(activation.get("planet") or planet),
        "gate": int(activation.get("gate", 0)),
        "line": int(activation.get("line", 0)),
        "color": int(activation.get("color", 0)),
        "tone": int(activation.get("tone", 0)),
        "base": int(activation.get("base", 0)),
        "center": str(activation.get("center") or ""),
        "name": str(activation.get("name") or ""),
        "theme": str(activation.get("theme") or ""),
        "longitude": round(float(activation.get("longitude", 0.0)), 4),
    }


def calculate_human_design(data: HumanDesignInput) -> dict[str, Any]:
    resolved = resolve_birth_location(
        data.birth_location,
        lat=data.birth_lat,
        lng=data.birth_lng,
        tz_str=data.tz_str,
    )
    payload = {
        "birthDate": data.birth_datetime.date().isoformat(),
        "birthTime": data.birth_datetime.strftime("%H:%M"),
        "tzStr": resolved.tz_str,
        "nodeType": (data.node_type or "true").strip().lower() or "true",
    }
    raw = run_bridge(payload)
    chart = dict(raw.get("chart") or {})
    utc_offset = float(raw.get("utcOffset"))

    type_info = dict(chart.get("type") or {})
    authority = dict(chart.get("authority") or {})
    profile = dict(chart.get("profile") or {})
    incarnation_cross = dict(chart.get("incarnationCross") or {})
    centers = dict(chart.get("centers") or {})
    variable = dict(chart.get("variable") or {})
    circuit_analysis = dict(chart.get("circuitAnalysis") or {})
    channels = list(chart.get("channels") or [])

    defined_centers = center_names(list(centers.get("defined") or []))
    undefined_centers = center_names(list(centers.get("undefined") or []))
    open_centers = center_names(list(centers.get("open") or []))
    channel_names = [str(item.get("name") or "") for item in channels if item.get("name")]

    summary = str(chart.get("summary") or "").strip()
    primary_finding = (
        summary
        or f"{type_info.get('name', 'Unknown type')} with {authority.get('name', 'Unknown authority')}, profile {profile.get('numbers', '?/?')}."
    )

    strategy_map = {
        "Wait for the Invitation": "等待邀请",
        "Wait to Respond": "等待回应",
        "Inform Before Acting": "行动前先告知",
        "Wait a Lunar Cycle": "等待一个月亮周期",
    }
    definition_map = {
        "Split Definition": "分裂定义",
        "Single Definition": "单一定义",
        "Triple Split Definition": "三重分裂定义",
        "Quadruple Split Definition": "四重分裂定义",
        "No Definition": "无定义",
    }

    supporting_signals = [
        f"策略是{strategy_map.get(type_info.get('strategy', ''), type_info.get('strategy', '未明'))}，定义为{definition_map.get(chart.get('definition', ''), chart.get('definition', '未明'))}。",
        f"已定义中心有：{', '.join(defined_centers) if defined_centers else '无'}；开放中心有：{', '.join(open_centers) if open_centers else '无'}。",
        f"人生十字落在：{incarnation_cross.get('fullName', incarnation_cross.get('name', '未明'))}。",
        f"变量标记为：{variable.get('notation', '未明')}。",
    ]
    if channel_names:
        supporting_signals.append(
            "当前激活通道包括：" + ", ".join(channel_names[:6]) + "。"
        )
    dominant_circuit = dict(circuit_analysis.get("dominant") or {})
    if dominant_circuit:
        supporting_signals.append(
            f"主导回路偏向{dominant_circuit.get('name', '未明')}，主题更接近{dominant_circuit.get('theme', '未明')}。"
        )

    risk_flags = [
        "This local human design engine uses natalengine with historical timezone resolution from the resolved birth location.",
        "Human Design is a modern synthetic system, so wording around variable, PHS, circuitry, and incarnation cross still varies across schools.",
        "This engine computes structural bodygraph outputs locally; it does not yet add transit overlays, relationship composites, or long-form coaching language.",
    ]
    if resolved.approximate:
        risk_flags.append(
            "Birth location was resolved through a region-level fallback, so timezone and chart precision should be treated as approximate."
        )

    return {
        "system": "human_design",
        "question_type": "destiny",
        "used_inputs": {
            "birth_datetime": data.birth_datetime.isoformat(sep=" ", timespec="minutes"),
            "birth_location": data.birth_location,
            "resolved_location": resolved.display_name,
            "lat": resolved.lat,
            "lng": resolved.lng,
            "tz_str": resolved.tz_str,
            "location_source": resolved.source,
            "utc_offset_hours": utc_offset,
            "node_type": payload["nodeType"],
            "engine": "natalengine",
        },
        "missing_inputs": [],
        "derived_factors": {
            "type": type_info,
            "authority": authority,
            "profile": profile,
            "definition": str(chart.get("definition") or ""),
            "incarnation_cross": incarnation_cross,
            "centers": {
                "defined_names": defined_centers,
                "undefined_names": undefined_centers,
                "open_names": open_centers,
                "all_undefined_names": list(centers.get("allUndefinedNames") or []),
            },
            "channel_count": len(channels),
            "channels": channels,
            "circuit_analysis": circuit_analysis,
            "key_activations": {
                "personality_sun": gate_signature(chart, "personality", "sun"),
                "personality_earth": gate_signature(chart, "personality", "earth"),
                "design_sun": gate_signature(chart, "design", "sun"),
                "design_earth": gate_signature(chart, "design", "earth"),
            },
            "variable": variable,
        },
        "raw_chart": {
            "centers": centers,
            "gates": dict(chart.get("gates") or {}),
            "positions": dict(chart.get("positions") or {}),
            "meta": dict(chart.get("meta") or {}),
        },
        "primary_finding": primary_finding,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use the bodygraph as a stable constitutional layer; add transits or relationship overlays separately when timing matters.",
        "confidence": "medium",
        "rules_path": [
            "birth-location resolution",
            "historical utc offset resolution",
            "human design activation calculation",
            "center and channel extraction",
            "profile, authority, and variable synthesis",
        ],
    }
