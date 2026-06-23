from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import re
from typing import Any, Iterable

from kerykeion import NatalAspects


SIGN_FULL_NAMES = {
    "Ari": "Aries",
    "Tau": "Taurus",
    "Gem": "Gemini",
    "Can": "Cancer",
    "Leo": "Leo",
    "Vir": "Virgo",
    "Lib": "Libra",
    "Sco": "Scorpio",
    "Sag": "Sagittarius",
    "Cap": "Capricorn",
    "Aqu": "Aquarius",
    "Pis": "Pisces",
}

SIGN_INDEX_TO_NAME = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

HOUSE_LABELS = {
    "First_House": 1,
    "Second_House": 2,
    "Third_House": 3,
    "Fourth_House": 4,
    "Fifth_House": 5,
    "Sixth_House": 6,
    "Seventh_House": 7,
    "Eighth_House": 8,
    "Ninth_House": 9,
    "Tenth_House": 10,
    "Eleventh_House": 11,
    "Twelfth_House": 12,
}

HOUSE_KEYS = [
    "first_house",
    "second_house",
    "third_house",
    "fourth_house",
    "fifth_house",
    "sixth_house",
    "seventh_house",
    "eighth_house",
    "ninth_house",
    "tenth_house",
    "eleventh_house",
    "twelfth_house",
]

MAJOR_ASPECTS = {"conjunction", "opposition", "trine", "square", "sextile"}

ELEMENT_ORDER = ["Fire", "Earth", "Air", "Water"]
QUALITY_ORDER = ["Cardinal", "Fixed", "Mutable"]


@dataclass(frozen=True)
class ResolvedBirthLocation:
    query: str
    display_name: str
    lat: float
    lng: float
    tz_str: str
    source: str
    approximate: bool = False


def _location_spec(
    display_name: str,
    lat: float,
    lng: float,
    tz_str: str,
    aliases: list[str],
    source: str = "builtin-city",
    approximate: bool = False,
) -> dict[str, Any]:
    return {
        "display_name": display_name,
        "lat": lat,
        "lng": lng,
        "tz_str": tz_str,
        "aliases": aliases,
        "source": source,
        "approximate": approximate,
    }


COMMON_LOCATION_SPECS = [
    _location_spec("Beijing, China", 39.9042, 116.4074, "Asia/Shanghai", ["beijing", "北京", "北京市"]),
    _location_spec("Shanghai, China", 31.2304, 121.4737, "Asia/Shanghai", ["shanghai", "上海", "上海市"]),
    _location_spec("Guangzhou, China", 23.1291, 113.2644, "Asia/Shanghai", ["guangzhou", "广州", "广州市"]),
    _location_spec("Shenzhen, China", 22.5431, 114.0579, "Asia/Shanghai", ["shenzhen", "深圳", "深圳市"]),
    _location_spec("Hangzhou, China", 30.2741, 120.1551, "Asia/Shanghai", ["hangzhou", "杭州", "杭州市"]),
    _location_spec("Nanjing, China", 32.0603, 118.7969, "Asia/Shanghai", ["nanjing", "南京", "南京市"]),
    _location_spec("Suzhou, China", 31.2989, 120.5853, "Asia/Shanghai", ["suzhou", "苏州", "苏州市"]),
    _location_spec("Wuhan, China", 30.5928, 114.3055, "Asia/Shanghai", ["wuhan", "武汉", "武汉市"]),
    _location_spec("Chengdu, China", 30.5728, 104.0668, "Asia/Shanghai", ["chengdu", "成都", "成都市"]),
    _location_spec("Chongqing, China", 29.4316, 106.9123, "Asia/Shanghai", ["chongqing", "重庆", "重庆市"]),
    _location_spec("Xi'an, China", 34.3416, 108.9398, "Asia/Shanghai", ["xian", "xi'an", "西安", "西安市"]),
    _location_spec("Tianjin, China", 39.0842, 117.2000, "Asia/Shanghai", ["tianjin", "天津", "天津市"]),
    _location_spec("Zhengzhou, China", 34.7466, 113.6254, "Asia/Shanghai", ["zhengzhou", "郑州", "郑州市"]),
    _location_spec("Xinyang, Henan, China", 32.1470, 114.0928, "Asia/Shanghai", ["xinyang", "信阳", "河南信阳", "信阳市"]),
    _location_spec("Changsha, China", 28.2282, 112.9388, "Asia/Shanghai", ["changsha", "长沙", "长沙市"]),
    _location_spec("Kunming, China", 25.0389, 102.7183, "Asia/Shanghai", ["kunming", "昆明", "昆明市"]),
    _location_spec("Xiamen, China", 24.4798, 118.0894, "Asia/Shanghai", ["xiamen", "厦门", "厦门市"]),
    _location_spec("Fuzhou, China", 26.0745, 119.2965, "Asia/Shanghai", ["fuzhou", "福州", "福州市"]),
    _location_spec("Jinan, China", 36.6512, 117.1201, "Asia/Shanghai", ["jinan", "济南", "济南市"]),
    _location_spec("Qingdao, China", 36.0671, 120.3826, "Asia/Shanghai", ["qingdao", "青岛", "青岛市"]),
    _location_spec("Shenyang, China", 41.8057, 123.4315, "Asia/Shanghai", ["shenyang", "沈阳", "沈阳市"]),
    _location_spec("Harbin, China", 45.8038, 126.5350, "Asia/Shanghai", ["harbin", "哈尔滨", "哈尔滨市"]),
    _location_spec("Taipei, Taiwan", 25.0330, 121.5654, "Asia/Taipei", ["taipei", "台北", "臺北", "台北市", "臺北市"]),
    _location_spec("Hong Kong", 22.3193, 114.1694, "Asia/Hong_Kong", ["hongkong", "hong kong", "香港"]),
    _location_spec("Macau", 22.1987, 113.5439, "Asia/Macau", ["macau", "macao", "澳门", "澳門"]),
    _location_spec("Tokyo, Japan", 35.6762, 139.6503, "Asia/Tokyo", ["tokyo", "东京", "東京"]),
    _location_spec("Osaka, Japan", 34.6937, 135.5023, "Asia/Tokyo", ["osaka", "大阪"]),
    _location_spec("Seoul, South Korea", 37.5665, 126.9780, "Asia/Seoul", ["seoul", "首尔", "서울"]),
    _location_spec("Singapore", 1.3521, 103.8198, "Asia/Singapore", ["singapore", "新加坡"]),
    _location_spec("Bangkok, Thailand", 13.7563, 100.5018, "Asia/Bangkok", ["bangkok", "曼谷"]),
    _location_spec("Delhi, India", 28.6139, 77.2090, "Asia/Kolkata", ["delhi", "newdelhi", "新德里", "德里"]),
    _location_spec("Mumbai, India", 19.0760, 72.8777, "Asia/Kolkata", ["mumbai", "bombay", "孟买", "孟買"]),
    _location_spec("London, United Kingdom", 51.5072, -0.1276, "Europe/London", ["london", "伦敦", "倫敦"]),
    _location_spec("Paris, France", 48.8566, 2.3522, "Europe/Paris", ["paris", "巴黎"]),
    _location_spec("Berlin, Germany", 52.5200, 13.4050, "Europe/Berlin", ["berlin", "柏林"]),
    _location_spec("Moscow, Russia", 55.7558, 37.6173, "Europe/Moscow", ["moscow", "莫斯科"]),
    _location_spec("New York, USA", 40.7128, -74.0060, "America/New_York", ["newyork", "new york", "纽约", "紐約", "nyc"]),
    _location_spec("Los Angeles, USA", 34.0522, -118.2437, "America/Los_Angeles", ["losangeles", "los angeles", "洛杉矶", "洛杉磯", "la"]),
    _location_spec("San Francisco, USA", 37.7749, -122.4194, "America/Los_Angeles", ["sanfrancisco", "san francisco", "旧金山", "舊金山"]),
    _location_spec("Vancouver, Canada", 49.2827, -123.1207, "America/Vancouver", ["vancouver", "温哥华", "溫哥華"]),
    _location_spec("Toronto, Canada", 43.6532, -79.3832, "America/Toronto", ["toronto", "多伦多", "多倫多"]),
    _location_spec("Sydney, Australia", -33.8688, 151.2093, "Australia/Sydney", ["sydney", "悉尼", "雪梨"]),
    _location_spec("Melbourne, Australia", -37.8136, 144.9631, "Australia/Melbourne", ["melbourne", "墨尔本", "墨爾本"]),
    _location_spec("Dubai, UAE", 25.2048, 55.2708, "Asia/Dubai", ["dubai", "迪拜", "杜拜"]),
    _location_spec(
        "Henan, China (approximated as Zhengzhou)",
        34.7466,
        113.6254,
        "Asia/Shanghai",
        ["henan", "河南", "河南省"],
        source="builtin-region",
        approximate=True,
    ),
    _location_spec(
        "Hunan, China (approximated as Changsha)",
        28.2282,
        112.9388,
        "Asia/Shanghai",
        ["hunan", "湖南", "湖南省"],
        source="builtin-region",
        approximate=True,
    ),
    _location_spec(
        "Sichuan, China (approximated as Chengdu)",
        30.5728,
        104.0668,
        "Asia/Shanghai",
        ["sichuan", "四川", "四川省"],
        source="builtin-region",
        approximate=True,
    ),
    _location_spec(
        "Guangdong, China (approximated as Guangzhou)",
        23.1291,
        113.2644,
        "Asia/Shanghai",
        ["guangdong", "广东", "廣東", "广东省", "廣東省"],
        source="builtin-region",
        approximate=True,
    ),
]

NORMALIZED_LOCATION_ALIASES: list[tuple[str, dict[str, Any]]] = []
for spec in COMMON_LOCATION_SPECS:
    for alias in spec["aliases"]:
        NORMALIZED_LOCATION_ALIASES.append((alias, spec))
NORMALIZED_LOCATION_ALIASES.sort(key=lambda item: len(item[0]), reverse=True)


def ordinal(value: int) -> str:
    if 10 <= value % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(value % 10, "th")
    return f"{value}{suffix}"


def normalize_lookup_text(value: str) -> str:
    text = (value or "").strip().lower()
    for token in ["出生地", "生于", "生於", "来自", "來自", "中国", "中國", "china"]:
        text = text.replace(token, "")
    text = re.sub(r"[\s,.;:(){}\[\]<>，。；：、/\\_-]+", "", text)
    return text


def house_label_to_number(value: str | None) -> int | None:
    if not value:
        return None
    return HOUSE_LABELS.get(value)


def sign_name_from_index(sign_index: int) -> str:
    return SIGN_INDEX_TO_NAME[int(sign_index) % 12]


def normalize_chart_point(raw: dict[str, Any], name_override: str | None = None) -> dict[str, Any]:
    sign = str(raw.get("sign") or "")
    house = raw.get("house")
    return {
        "name": name_override or str(raw.get("name") or ""),
        "sign": sign,
        "sign_full": SIGN_FULL_NAMES.get(sign, sign),
        "sign_index": int(raw.get("sign_num", 0)),
        "degree_in_sign": round(float(raw.get("position", 0.0)), 2),
        "absolute_degree": round(float(raw.get("abs_pos", 0.0)), 2),
        "house": house,
        "house_number": house_label_to_number(str(house) if house else None),
        "retrograde": bool(raw.get("retrograde")) if raw.get("retrograde") is not None else False,
        "element": str(raw.get("element") or ""),
        "quality": str(raw.get("quality") or ""),
        "speed": round(float(raw.get("speed", 0.0)), 4) if raw.get("speed") is not None else None,
    }


def extract_points(
    chart_dump: dict[str, Any],
    keys: Iterable[str],
    name_overrides: dict[str, str] | None = None,
) -> dict[str, dict[str, Any]]:
    points: dict[str, dict[str, Any]] = {}
    overrides = name_overrides or {}
    for key in keys:
        raw = chart_dump.get(key)
        if not isinstance(raw, dict):
            continue
        normalized = normalize_chart_point(raw, overrides.get(key))
        points[normalized["name"]] = normalized
    return points


def extract_houses(chart_dump: dict[str, Any]) -> dict[str, dict[str, Any]]:
    houses: dict[str, dict[str, Any]] = {}
    for key in HOUSE_KEYS:
        raw = chart_dump.get(key)
        if not isinstance(raw, dict):
            continue
        normalized = normalize_chart_point(raw)
        number = house_label_to_number(str(raw.get("name") or ""))
        if number is None:
            continue
        houses[str(number)] = normalized
    return houses


def count_by_key(points: dict[str, dict[str, Any]], key: str, ordered_keys: list[str]) -> dict[str, int]:
    counter = Counter(str(point.get(key) or "") for point in points.values() if point.get(key))
    return {item: counter.get(item, 0) for item in ordered_keys}


def dominant_keys(distribution: dict[str, int]) -> list[str]:
    positive = {key: value for key, value in distribution.items() if value > 0}
    if not positive:
        return []
    strongest = max(positive.values())
    return [key for key, value in positive.items() if value == strongest]


def normalize_aspects(subject: Any, allowed_points: set[str], limit: int = 8) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for item in NatalAspects(subject).all_aspects:
        data = item.model_dump()
        if data["aspect"] not in MAJOR_ASPECTS:
            continue
        if data["p1_name"] not in allowed_points or data["p2_name"] not in allowed_points:
            continue
        entries.append(
            {
                "between": f"{data['p1_name']} - {data['p2_name']}",
                "aspect": data["aspect"],
                "degrees": int(data["aspect_degrees"]),
                "orbit": round(float(data["orbit"]), 2),
                "movement": data["aspect_movement"],
            }
        )
    entries.sort(key=lambda item: (item["orbit"], item["between"]))
    return entries[:limit]


def occupied_houses(points: dict[str, dict[str, Any]], house_field: str = "house_number") -> dict[str, list[str]]:
    occupied: dict[str, list[str]] = {}
    for name, point in points.items():
        house = point.get(house_field)
        if house is None:
            continue
        key = str(int(house))
        occupied.setdefault(key, []).append(name)
    return dict(sorted(occupied.items(), key=lambda item: int(item[0])))


def parse_coordinate_hint(value: str) -> tuple[float, float, str]:
    text = (value or "").strip()
    if not text:
        raise ValueError("empty location string")
    timezone_match = re.search(r"([A-Za-z]+/[A-Za-z_]+(?:/[A-Za-z_]+)?)", text)
    numeric_pairs = re.findall(r"[+-]?\d+(?:\.\d+)?", text)
    if len(numeric_pairs) < 2:
        raise ValueError("location string does not contain coordinates")
    lat = float(numeric_pairs[0])
    lng = float(numeric_pairs[1])
    return lat, lng, timezone_match.group(1) if timezone_match else ""


def infer_timezone(location_text: str, lat: float | None, lng: float | None) -> str:
    normalized = normalize_lookup_text(location_text)
    if any(token in normalized for token in ["香港", "hongkong", "hongkongsar"]):
        return "Asia/Hong_Kong"
    if any(token in normalized for token in ["澳门", "澳門", "macau", "macao"]):
        return "Asia/Macau"
    if any(token in normalized for token in ["台北", "臺北", "taipei", "taiwan", "台湾", "臺灣"]):
        return "Asia/Taipei"
    if any(token in normalized for token in ["东京", "東京", "tokyo", "osaka", "大阪"]):
        return "Asia/Tokyo"
    if any(token in normalized for token in ["首尔", "seoul", "서울"]):
        return "Asia/Seoul"
    if any(token in normalized for token in ["新加坡", "singapore"]):
        return "Asia/Singapore"
    if any(token in normalized for token in ["新德里", "德里", "mumbai", "bombay", "delhi", "india", "孟买", "孟買"]):
        return "Asia/Kolkata"
    if lat is not None and lng is not None:
        if 21.5 <= lat <= 25.6 and 119.0 <= lng <= 122.5:
            return "Asia/Taipei"
        if 22.0 <= lat <= 22.5 and 113.4 <= lng <= 113.7:
            return "Asia/Macau"
        if 22.1 <= lat <= 22.6 and 113.8 <= lng <= 114.5:
            return "Asia/Hong_Kong"
        if 18.0 <= lat <= 54.5 and 73.0 <= lng <= 135.5:
            return "Asia/Shanghai"
    return ""


def resolve_birth_location(
    location: str,
    lat: float | None = None,
    lng: float | None = None,
    tz_str: str = "",
) -> ResolvedBirthLocation:
    cleaned_location = (location or "").strip()
    provided_timezone = (tz_str or "").strip()

    if lat is not None and lng is not None:
        resolved_timezone = provided_timezone or infer_timezone(cleaned_location, lat, lng)
        if not resolved_timezone:
            raise ValueError("tz_str is required when coordinates do not map to a known timezone.")
        return ResolvedBirthLocation(
            query=cleaned_location or f"{lat},{lng}",
            display_name=cleaned_location or f"lat {lat}, lng {lng}",
            lat=float(lat),
            lng=float(lng),
            tz_str=resolved_timezone,
            source="coordinates",
            approximate=False,
        )

    if cleaned_location:
        try:
            parsed_lat, parsed_lng, parsed_timezone = parse_coordinate_hint(cleaned_location)
            resolved_timezone = provided_timezone or parsed_timezone or infer_timezone(cleaned_location, parsed_lat, parsed_lng)
            if not resolved_timezone:
                raise ValueError("timezone is required when passing coordinates inside birth_location.")
            return ResolvedBirthLocation(
                query=cleaned_location,
                display_name=f"lat {parsed_lat}, lng {parsed_lng}",
                lat=parsed_lat,
                lng=parsed_lng,
                tz_str=resolved_timezone,
                source="coordinates",
                approximate=False,
            )
        except ValueError:
            pass

    normalized = normalize_lookup_text(cleaned_location)
    for alias, spec in NORMALIZED_LOCATION_ALIASES:
        if alias and alias in normalized:
            return ResolvedBirthLocation(
                query=cleaned_location,
                display_name=str(spec["display_name"]),
                lat=float(spec["lat"]),
                lng=float(spec["lng"]),
                tz_str=str(spec["tz_str"]),
                source=str(spec["source"]),
                approximate=bool(spec["approximate"]),
            )

    raise ValueError(
        "birth_location could not be resolved locally; provide a known city or explicit lat/lng with tz_str."
    )


def whole_sign_house(sign_index: int, ascendant_sign_index: int) -> int:
    return ((int(sign_index) - int(ascendant_sign_index)) % 12) + 1
