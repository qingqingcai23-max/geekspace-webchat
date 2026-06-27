from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import requests


TENCENT_LBS_BASE_URL = "https://apis.map.qq.com"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"


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


@dataclass(frozen=True)
class TencentMapApiError(Exception):
    message: str
    status: int | None = None
    raw_payload: dict[str, Any] | None = None

    def __str__(self) -> str:
        return self.message


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


def _nominatim_user_agent() -> str:
    return (
        os.environ.get("NOMINATIM_USER_AGENT")
        or "geekspace-webchat/1.0 (map geocode fallback)"
    ).strip()


def _first_text(mapping: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = str(mapping.get(key) or "").strip()
        if value:
            return value
    return ""


def is_quota_exceeded_error(exc: Exception) -> bool:
    if isinstance(exc, TencentMapApiError):
        message = exc.message
    else:
        message = str(exc or "")
    normalized = message.lower()
    return (
        "达到上限" in message
        or "调用量已达到上限" in message
        or "quota" in normalized
        or "limit exceeded" in normalized
        or "over the quota" in normalized
    )


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
        raise TencentMapApiError(message=message, status=status, raw_payload=payload)
    return payload


def _build_tencent_geocode_result(cleaned: str, payload: dict[str, Any]) -> TencentMapResolvedLocation:
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


def openstreetmap_geocode_address(address: str, region: str = "", timeout: float = 8.0) -> TencentMapResolvedLocation:
    cleaned = str(address or "").strip()
    if not cleaned:
        raise ValueError("address is required for geocoding")
    query = cleaned
    normalized_region = str(region or "").strip()
    if normalized_region and normalized_region not in cleaned:
        query = f"{normalized_region} {cleaned}".strip()
    response = requests.get(
        NOMINATIM_SEARCH_URL,
        params={
            "q": query,
            "format": "jsonv2",
            "limit": 1,
            "addressdetails": 1,
        },
        headers={
            "User-Agent": _nominatim_user_agent(),
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.6",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        raise ValueError("OpenStreetMap geocoding returned no result.")
    result = payload[0] or {}
    address_parts = result.get("address") or {}
    display_name = str(result.get("display_name") or query)
    title = str(result.get("name") or display_name.split(",")[0].strip() or query)
    province = _first_text(address_parts, "state", "province", "region")
    city = _first_text(address_parts, "city", "municipality", "town", "county", "state_district")
    district = _first_text(address_parts, "suburb", "city_district", "district", "borough", "quarter", "township")
    return TencentMapResolvedLocation(
        query=cleaned,
        address=display_name,
        title=title,
        lat=float(result.get("lat")),
        lng=float(result.get("lon")),
        adcode="",
        province=province,
        city=city,
        district=district,
        source="osm-nominatim",
    )


def geocode_address(address: str, region: str = "", timeout: float = 8.0) -> TencentMapResolvedLocation:
    cleaned = str(address or "").strip()
    if not cleaned:
        raise ValueError("address is required for geocoding")
    params: dict[str, Any] = {"address": cleaned}
    if region:
        params["region"] = str(region).strip()
    try:
        payload = _request("/ws/geocoder/v1/", params=params, timeout=timeout)
        return _build_tencent_geocode_result(cleaned, payload)
    except Exception as exc:
        if is_quota_exceeded_error(exc) or str(exc).startswith("Tencent map key is not configured"):
            return openstreetmap_geocode_address(cleaned, region=region, timeout=timeout)
        raise


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
            except Exception as exc:
                if is_quota_exceeded_error(exc):
                    raise
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
