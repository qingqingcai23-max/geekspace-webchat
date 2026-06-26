from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import requests


TENCENT_LBS_BASE_URL = "https://apis.map.qq.com"


@dataclass(frozen=True)
class TencentMapResolvedLocation:
    query: str
    address: str
    title: str
    lat: float
    lng: float
    adcode: str
    province: str
    city: str
    district: str
    source: str = "tencent-geocoder"


POI_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hospital": ("医院", "诊所", "急救", "卫生服务中心"),
    "funeral": ("殡仪馆", "公墓", "陵园", "骨灰堂"),
    "school": ("学校", "中学", "小学", "幼儿园", "大学"),
    "mall": ("商场", "广场", "购物中心", "商业", "万达"),
    "park": ("公园", "绿地", "植物园"),
    "water": ("江", "河", "湖", "溪", "水库", "海"),
    "bridge": ("桥", "大桥", "立交桥"),
    "elevated": ("高架", "快速路", "环路", "立交"),
    "subway": ("地铁站", "地铁", "轨道交通"),
    "government": ("政府", "派出所", "法院"),
}


def tencent_map_key() -> str:
    return (
        os.environ.get("TENCENT_MAP_KEY")
        or os.environ.get("QQ_MAP_KEY")
        or os.environ.get("TX_MAP_KEY")
        or ""
    ).strip()


def has_tencent_map_key() -> bool:
    return bool(tencent_map_key())


def _request(path: str, params: dict[str, Any], timeout: float = 8.0) -> dict[str, Any]:
    key = tencent_map_key()
    if not key:
        raise RuntimeError("Tencent map key is not configured. Set TENCENT_MAP_KEY first.")
    merged = dict(params)
    merged["key"] = key
    response = requests.get(f"{TENCENT_LBS_BASE_URL}{path}", params=merged, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    status = int(payload.get("status", -1))
    if status != 0:
        message = str(payload.get("message") or "Tencent map API request failed.")
        raise ValueError(message)
    return payload


def geocode_address(address: str, region: str = "", timeout: float = 8.0) -> TencentMapResolvedLocation:
    cleaned = str(address or "").strip()
    if not cleaned:
        raise ValueError("address is required for geocoding")
    params: dict[str, Any] = {"address": cleaned}
    if region:
        params["region"] = str(region).strip()
    payload = _request("/ws/geocoder/v1/", params=params, timeout=timeout)
    result = payload.get("result") or {}
    location = result.get("location") or {}
    ad_info = result.get("ad_info") or {}
    address_components = result.get("address_components") or {}
    return TencentMapResolvedLocation(
        query=cleaned,
        address=str(result.get("address") or cleaned),
        title=str(result.get("title") or result.get("address") or cleaned),
        lat=float(location.get("lat")),
        lng=float(location.get("lng")),
        adcode=str(ad_info.get("adcode") or ""),
        province=str(address_components.get("province") or ""),
        city=str(address_components.get("city") or ""),
        district=str(address_components.get("district") or ""),
    )


def place_search(keyword: str, region: str = "", page_size: int = 5, timeout: float = 8.0) -> list[dict[str, Any]]:
    cleaned = str(keyword or "").strip()
    if not cleaned:
        raise ValueError("keyword is required for place search")
    boundary = f"region({region},0)" if region else "nearby(39.9042,116.4074,50000,0)"
    payload = _request(
        "/ws/place/v1/search",
        params={
            "keyword": cleaned,
            "boundary": boundary,
            "page_size": max(1, min(int(page_size), 20)),
        },
        timeout=timeout,
    )
    return list(payload.get("data") or [])


def nearby_search(lat: float, lng: float, keyword: str, radius: int = 1500, page_size: int = 8, timeout: float = 8.0) -> list[dict[str, Any]]:
    cleaned = str(keyword or "").strip()
    if not cleaned:
        raise ValueError("keyword is required for nearby search")
    payload = _request(
        "/ws/place/v1/search",
        params={
            "keyword": cleaned,
            "boundary": f"nearby({float(lat)},{float(lng)},{max(100, min(int(radius), 20000))},0)",
            "orderby": "_distance",
            "page_size": max(1, min(int(page_size), 20)),
        },
        timeout=timeout,
    )
    return list(payload.get("data") or [])


def collect_nearby_poi_signals(lat: float, lng: float, radius: int = 1500) -> dict[str, list[dict[str, Any]]]:
    results: dict[str, list[dict[str, Any]]] = {}
    for category, keywords in POI_CATEGORY_KEYWORDS.items():
        category_hits: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for keyword in keywords:
            try:
                entries = nearby_search(lat, lng, keyword, radius=radius, page_size=6)
            except Exception:
                entries = []
            for item in entries:
                uid = str(item.get("id") or item.get("title") or "")
                if uid and uid in seen_ids:
                    continue
                seen_ids.add(uid)
                location = item.get("location") or {}
                category_hits.append(
                    {
                        "id": uid,
                        "title": str(item.get("title") or ""),
                        "address": str(item.get("address") or ""),
                        "category": category,
                        "distance": int(item.get("_distance") or item.get("distance") or 0),
                        "lat": location.get("lat"),
                        "lng": location.get("lng"),
                    }
                )
        category_hits.sort(key=lambda item: int(item.get("distance") or 0))
        if category_hits:
            results[category] = category_hits[:6]
    return results


def static_map_url(
    lat: float,
    lng: float,
    zoom: int = 18,
    width: int = 960,
    height: int = 540,
    scale: int = 2,
    markers: str = "",
) -> str:
    key = tencent_map_key()
    if not key:
        return ""
    params = {
        "center": f"{float(lat)},{float(lng)}",
        "zoom": str(max(3, min(int(zoom), 20))),
        "size": f"{max(100, min(int(width), 1800))}*{max(100, min(int(height), 1800))}",
        "scale": str(2 if int(scale) >= 2 else 1),
        "key": key,
    }
    if markers:
        params["markers"] = markers
    query = "&".join(f"{name}={value}" for name, value in params.items())
    return f"{TENCENT_LBS_BASE_URL}/ws/staticmap/v2/?{query}"
