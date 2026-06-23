from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import re

import sxtwl


CN_DIGITS = {
    "零": 0,
    "〇": 0,
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "正": 1,
    "元": 1,
    "冬": 11,
    "腊": 12,
}

BRANCH_HOURS = {
    "子": 23,
    "丑": 1,
    "寅": 3,
    "卯": 5,
    "辰": 7,
    "巳": 9,
    "午": 11,
    "未": 13,
    "申": 15,
    "酉": 17,
    "戌": 19,
    "亥": 21,
}

INVALID_LOCATION_TOKENS = {
    "现在",
    "目前",
    "想问",
    "想看",
    "请问",
    "事业",
    "性格",
    "后续发展",
}

INVALID_LOCATION_MARKERS = (
    "我",
    "你",
    "他",
    "她",
    "它",
    "想",
    "问",
    "看",
    "说",
    "听",
    "答",
    "纠结",
    "反复",
    "模板",
    "人话",
    "项目",
    "工作",
    "房子",
    "机会",
)

COMMON_CITY_TOKENS = (
    "北京",
    "上海",
    "广州",
    "深圳",
    "杭州",
    "南京",
    "成都",
    "重庆",
    "天津",
    "武汉",
    "西安",
    "苏州",
    "长沙",
    "郑州",
    "青岛",
    "沈阳",
    "大连",
    "厦门",
    "福州",
    "昆明",
    "合肥",
    "南昌",
    "济南",
    "宁波",
    "无锡",
    "长春",
    "哈尔滨",
    "石家庄",
    "太原",
    "南宁",
    "贵阳",
    "海口",
    "兰州",
    "乌鲁木齐",
    "拉萨",
    "呼和浩特",
    "银川",
    "台北",
    "香港",
    "澳门",
    "东京",
    "大阪",
    "京都",
    "首尔",
    "新加坡",
    "曼谷",
    "新德里",
    "德里",
    "孟买",
    "伦敦",
    "巴黎",
    "柏林",
    "莫斯科",
    "纽约",
    "洛杉矶",
    "旧金山",
    "温哥华",
    "多伦多",
    "悉尼",
    "墨尔本",
    "迪拜",
)

COMMON_CITY_PATTERN = "|".join(sorted((re.escape(token) for token in COMMON_CITY_TOKENS), key=len, reverse=True))

EXPLICIT_BIRTH_MARKERS = (
    "出生",
    "生于",
    "生於",
    "生日",
    "八字",
    "四柱",
    "命盘",
    "命盤",
    "本命",
    "星盘",
    "星盤",
)

EXPLICIT_BIRTH_MARKERS_EN = (
    "i was born",
    "born on",
    "born at",
    "birth chart",
    "date of birth",
    "natal",
)

BIRTH_TOPIC_MARKERS = (
    "婚姻",
    "感情",
    "恋爱",
    "事业",
    "工作",
    "职业",
    "财运",
    "赚钱",
    "性格",
    "天赋",
    "运势",
    "人生",
    "关系",
    "命盘",
    "本命",
    "星盘",
    "人类图",
    "类型",
    "决策方式",
    "权威",
)

BIRTH_TOPIC_MARKERS_EN = (
    "career",
    "relationship",
    "personality",
    "purpose",
    "strength",
    "weakness",
    "wealth",
    "money",
)

NON_BIRTH_EVENT_MARKERS = (
    "出发",
    "出差",
    "出行",
    "旅行",
    "行程",
    "入住",
    "住在",
    "住新宿",
    "住酒店",
    "搬家",
    "入宅",
    "签约",
    "合同",
    "合作",
    "招聘",
    "起问",
    "占问",
    "问事",
    "现在是",
    "当前是",
    "这周",
    "本周",
    "今天",
    "明天",
    "近期",
    "最近",
    "候选日期",
    "黄道吉日",
    "好日子",
)

NON_BIRTH_EVENT_MARKERS_EN = (
    "departure",
    "depart",
    "travel",
    "trip",
    "moving",
    "signing",
    "cooperation",
    "hiring",
    "this week",
    "today",
    "tomorrow",
    "recently",
    "candidate date",
)

EN_MONTHS = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}


@dataclass(frozen=True)
class ParsedBirthDetails:
    birth_datetime: datetime | None
    has_time: bool
    calendar: str
    gender: str
    birth_location: str
    parse_error: str = ""
    has_conflict: bool = False
    conflict_note: str = ""


def normalize_text(text: str) -> str:
    return (
        text.replace("：", ":")
        .replace("，", ",")
        .replace("、", ",")
        .replace("\u3000", " ")
        .replace("（", "(")
        .replace("）", ")")
        .replace("農曆", "农历")
        .replace("陰曆", "阴历")
        .replace("陽曆", "阳历")
        .replace("公曆", "公历")
        .replace("出生於", "出生于")
        .replace("兩點", "两点")
        .replace("點", "点")
        .replace("時", "时")
        .strip()
    )


def parse_chinese_number(token: str) -> int | None:
    if not token:
        return None
    token = token.strip()
    if token.isdigit():
        return int(token)
    if token in {"正", "元", "冬", "腊"}:
        return CN_DIGITS[token]
    if token.startswith("初"):
        rest = token[1:]
        if rest == "十":
            return 10
        return CN_DIGITS.get(rest)
    if token.startswith("廿"):
        rest = token[1:]
        return 20 if not rest else 20 + (parse_chinese_number(rest) or 0)
    if token.startswith("卅"):
        rest = token[1:]
        return 30 if not rest else 30 + (parse_chinese_number(rest) or 0)
    if "十" in token:
        left, right = token.split("十", 1)
        tens = 1 if left == "" else CN_DIGITS.get(left)
        if tens is None:
            return None
        ones = 0 if right == "" else CN_DIGITS.get(right)
        if ones is None:
            return None
        return tens * 10 + ones
    if all(char in CN_DIGITS for char in token):
        return int("".join(str(CN_DIGITS[char]) for char in token))
    return None


def parse_time_from_text(text: str) -> tuple[int, int, bool]:
    normalized = normalize_text(text)
    english = re.search(
        r"\b(?P<h>\d{1,2})\s*:\s*(?P<m>\d{1,2})\s*(?P<ampm>am|pm)\b",
        normalized,
        re.IGNORECASE,
    )
    if english:
        hour = int(english.group("h"))
        minute = int(english.group("m"))
        ampm = english.group("ampm").lower()
        if ampm == "pm" and hour < 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        return hour, minute, True

    explicit = re.search(r"(?P<h>\d{1,2})\s*:\s*(?P<m>\d{1,2})", normalized)
    if explicit:
        return int(explicit.group("h")), int(explicit.group("m")), True

    branch = re.search(r"(?P<b>[子丑寅卯辰巳午未申酉戌亥])\s*[时時]", normalized)
    if branch:
        return BRANCH_HOURS[branch.group("b")], 0, True

    match = re.search(
        r"(?P<meridiem>凌晨|早上|上午|中午|下午|傍晚|晚上)?\s*"
        r"(?P<h>[\d零〇一二两三四五六七八九十]{1,3})\s*"
        r"(?:[点點时時])"
        r"(?P<m>半|一刻|三刻|[\d零〇一二两三四五六七八九十]{1,3}\s*[分]?)?",
        normalized,
    )
    if not match:
        return 0, 0, False

    hour = parse_chinese_number(match.group("h")) or 0
    minute_token = (match.group("m") or "").replace("分", "").strip()
    minute = 0
    if minute_token == "半":
        minute = 30
    elif minute_token == "一刻":
        minute = 15
    elif minute_token == "三刻":
        minute = 45
    elif minute_token:
        minute = parse_chinese_number(minute_token) or 0

    meridiem = match.group("meridiem") or ""
    if meridiem in {"下午", "傍晚", "晚上"} and 0 < hour < 12:
        hour += 12
    elif meridiem == "中午" and 0 < hour < 11:
        hour += 12
    elif meridiem in {"凌晨", "早上", "上午"} and hour == 12:
        hour = 0

    return hour, minute, True


def parse_solar_date(text: str) -> tuple[int, int, int] | None:
    normalized = normalize_text(text)
    numeric = re.search(
        r"(?P<y>\d{4})\s*[-/.年]\s*(?P<m>\d{1,2})\s*[-/.月]\s*(?P<d>\d{1,2})\s*日?",
        normalized,
    )
    if numeric:
        return int(numeric.group("y")), int(numeric.group("m")), int(numeric.group("d"))

    english_month_first = re.search(
        r"\b(?P<month>[A-Za-z]+)\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?\s*,?\s*(?P<year>\d{4})\b",
        normalized,
        re.IGNORECASE,
    )
    if english_month_first:
        month = EN_MONTHS.get(english_month_first.group("month").lower())
        if month:
            return int(english_month_first.group("year")), month, int(english_month_first.group("day"))

    english_day_first = re.search(
        r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+(?P<month>[A-Za-z]+)\s*,?\s*(?P<year>\d{4})\b",
        normalized,
        re.IGNORECASE,
    )
    if english_day_first:
        month = EN_MONTHS.get(english_day_first.group("month").lower())
        if month:
            return int(english_day_first.group("year")), month, int(english_day_first.group("day"))

    chinese = re.search(
        r"(?P<y>\d{4})\s*年\s*(?P<m>[\d正元冬腊零〇一二两三四五六七八九十]{1,3})\s*月\s*"
        r"(?P<d>[\d初廿卅零〇一二两三四五六七八九十]{1,4})\s*日?",
        normalized,
    )
    if not chinese:
        return None
    chinese_match_start = chinese.start()
    lookback = normalized[max(0, chinese_match_start - 8) : chinese_match_start]
    if "农历" in lookback or "阴历" in lookback:
        return None
    month = parse_chinese_number(chinese.group("m"))
    day = parse_chinese_number(chinese.group("d"))
    if month is None or day is None:
        return None
    return int(chinese.group("y")), month, day


def parse_lunar_date(text: str) -> tuple[int, int, int, bool] | None:
    normalized = normalize_text(text)
    match = re.search(
        r"(?:农历|阴历)\s*(?P<y>\d{4})\s*年\s*(?P<leap>闰)?\s*"
        r"(?P<m>[\d正元冬腊零〇一二两三四五六七八九十]{1,3})\s*月\s*"
        r"(?P<d>[\d初廿卅零〇一二两三四五六七八九十]{1,4})\s*日?",
        normalized,
    )
    if not match:
        return None
    month = parse_chinese_number(match.group("m"))
    day = parse_chinese_number(match.group("d"))
    if month is None or day is None:
        return None
    return int(match.group("y")), month, day, bool(match.group("leap"))


def extract_gender(text: str) -> str:
    normalized = normalize_text(text)
    if any(token in normalized for token in ("女宝宝", "女宝", "女孩", "女婴", "女娃", "千金", "女寶寶", "女嬰")):
        return "女"
    if any(token in normalized for token in ("男宝宝", "男宝", "男孩", "男婴", "男娃", "公子", "男寶寶", "男嬰")):
        return "男"
    normalized = re.sub(
        r"(?P<loc>[\u4e00-\u9fff]{2,12})(?P<g>男|女)(?=[,，。；;:：\s]|$)",
        r"\g<loc> \g<g>",
        normalized,
    )
    match = re.search(r"(?:^|[\s,，。；;:：])(?P<g>男性|女性|男|女)(?:[\s,，。；;:：]|$)", normalized)
    if not match:
        return ""
    value = match.group("g")
    if value.startswith("男"):
        return "男"
    if value.startswith("女"):
        return "女"
    return ""


def clean_location(value: str) -> str:
    cleaned = value.strip(" ,，。；;.")
    cleaned = re.sub(r"^(?:出生地|生于|来自|在)\s*", "", cleaned)
    cleaned = re.sub(r"^(?:in|from)\b\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.split(r"(?:现在|目前|想问|想看|请问|please|and|for|to)", cleaned, maxsplit=1, flags=re.IGNORECASE)[0]
    return cleaned.strip(" ,，。；;.")


def looks_like_birth_location(value: str) -> bool:
    location = clean_location(value)
    if not location or location in INVALID_LOCATION_TOKENS:
        return False
    if any(marker in location for marker in INVALID_LOCATION_MARKERS):
        return False
    if re.search(r"\d", location):
        return False
    if all("\u4e00" <= char <= "\u9fff" for char in location):
        return 2 <= len(location) <= 12
    if re.fullmatch(r"[A-Za-z][A-Za-z .'-]{1,40}", location):
        return True
    return False


def should_treat_as_birth_context(
    text: str,
    *,
    has_date: bool,
    has_time: bool,
    gender: str,
    location: str,
) -> bool:
    if not has_date:
        return False

    normalized = normalize_text(text)
    lowered = normalized.lower()
    explicit_birth = any(token in normalized for token in EXPLICIT_BIRTH_MARKERS) or any(
        token in lowered for token in EXPLICIT_BIRTH_MARKERS_EN
    )
    if explicit_birth:
        return True

    has_birth_topics = any(token in normalized for token in BIRTH_TOPIC_MARKERS) or any(
        re.search(rf"\b{re.escape(token)}\b", lowered) for token in BIRTH_TOPIC_MARKERS_EN
    )
    has_event_markers = any(token in normalized for token in NON_BIRTH_EVENT_MARKERS) or any(
        token in lowered for token in NON_BIRTH_EVENT_MARKERS_EN
    )
    has_self_reference = any(token in normalized for token in ("我", "本人", "自己", "宝宝", "孩子", "小孩", "新生儿")) or any(
        re.search(rf"\b{re.escape(token)}\b", lowered) for token in ("i", "my", "me", "baby", "child", "newborn")
    )
    profile_signals = sum(1 for item in (has_time, bool(gender), bool(location)) if item)
    leading_profile_pattern = bool(
        re.match(
            r"^\s*\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}(?:\s+\d{1,2}\s*:\s*\d{1,2})?\s*[,，]\s*[\u4e00-\u9fffA-Za-z .'-]{2,20}",
            normalized,
        )
    )
    mixed_birth_timing_pattern = bool(
        re.search(r"(出生|生于|生於).{0,24}\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}", normalized)
        and re.search(r"(现在是|当前是).{0,16}\d{4}\s*[-/.年]\s*\d{1,2}\s*[-/.月]\s*\d{1,2}", normalized)
    )

    if has_event_markers and not mixed_birth_timing_pattern and not leading_profile_pattern:
        return False
    if profile_signals >= 2:
        return True
    if leading_profile_pattern and (has_birth_topics or location):
        return True
    if has_birth_topics and (profile_signals >= 1 or has_self_reference):
        return True
    return False


def extract_birth_location(text: str) -> str:
    normalized = normalize_text(text)
    patterns = [
        r"(?:出生地|生于|来自)\s*[:：]?\s*(?P<loc>[\u4e00-\u9fff]{2,16})(?:[,，。；;\s]|$)",
        rf"\d{{4}}\s*[-/.\u5e74]\s*\d{{1,2}}\s*[-/.\u6708]\s*\d{{1,2}}(?:[^,，。；;]{{0,24}})?[,，]\s*(?P<loc>(?:{COMMON_CITY_PATTERN}|[\u4e00-\u9fff]{{2,16}}(?:省|市|区|县|镇|乡|村)|[A-Za-z][A-Za-z .'-]{{1,40}}))(?:[,，。；;]|$)",
        r"(?:^|[,，。\s])(?P<loc>[\u4e00-\u9fff]{2,16})\s*[,，]\s*(?:男|女|男性|女性)(?:[,，。；;]|$)",
        r"(?:^|[,，。\s])(?P<loc>[\u4e00-\u9fff]{2,16})(?:男|女)(?:[,，。；;]|$)",
        r"(?:男|女|男性|女性)\s*[,，]\s*(?P<loc>[\u4e00-\u9fff]{2,16})(?:[,，。；;]|(?:现在|目前|想问|想看|请问)|$)",
        r"\bin\s+(?P<loc>[A-Za-z][A-Za-z .'-]{1,40})(?:[,.;]|\s+(?:please|and|for|to)\b|$)",
        r"\bfrom\s+(?P<loc>[A-Za-z][A-Za-z .'-]{1,40})(?:[,.;]|\s+(?:please|and|for|to)\b|$)",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, re.IGNORECASE)
        if not match:
            continue
        location = clean_location(match.group("loc"))
        if looks_like_birth_location(location):
            return location
    return ""


def parse_birth_details(text: str) -> ParsedBirthDetails:
    normalized = normalize_text(text)
    gender = extract_gender(normalized)
    location = extract_birth_location(normalized)
    hour, minute, has_time = parse_time_from_text(normalized)

    lunar = parse_lunar_date(normalized)
    solar = parse_solar_date(normalized)
    should_parse_as_birth = should_treat_as_birth_context(
        normalized,
        has_date=bool(lunar or solar),
        has_time=has_time,
        gender=gender,
        location=location,
    )
    if not should_parse_as_birth:
        return ParsedBirthDetails(
            birth_datetime=None,
            has_time=False,
            calendar="unknown",
            gender="",
            birth_location="",
        )
    explicit_lunar = any(token in normalized for token in ("农历", "阴历"))
    explicit_solar = any(token in normalized for token in ("公历", "阳历"))
    if lunar and explicit_lunar and not explicit_solar:
        solar = None
    has_conflict = False
    conflict_note = ""

    if lunar and solar:
        try:
            lunar_year, lunar_month, lunar_day, is_leap = lunar
            solar_day = sxtwl.fromLunar(lunar_year, lunar_month, lunar_day, is_leap)
            converted = (solar_day.getSolarYear(), solar_day.getSolarMonth(), solar_day.getSolarDay())
            if converted != solar:
                has_conflict = True
                conflict_note = "同时识别到公历和农历生日，但两套日期换算结果不一致，请先确认出生信息。"
        except Exception:
            has_conflict = True
            conflict_note = "同时识别到公历和农历生日，但农历换算失败，请先确认出生信息。"

    if lunar:
        try:
            year, month, day, is_leap = lunar
            solar_day = sxtwl.fromLunar(year, month, day, is_leap)
            birth_dt = datetime(solar_day.getSolarYear(), solar_day.getSolarMonth(), solar_day.getSolarDay(), hour, minute)
            return ParsedBirthDetails(
                birth_datetime=birth_dt,
                has_time=has_time,
                calendar="lunar",
                gender=gender,
                birth_location=location,
                has_conflict=has_conflict,
                conflict_note=conflict_note,
            )
        except Exception as exc:
            return ParsedBirthDetails(
                birth_datetime=None,
                has_time=has_time,
                calendar="lunar",
                gender=gender,
                birth_location=location,
                parse_error=f"农历日期无法换算：{exc}",
                has_conflict=has_conflict,
                conflict_note=conflict_note,
            )

    if solar:
        try:
            year, month, day = solar
            birth_dt = datetime(year, month, day, hour, minute)
            return ParsedBirthDetails(
                birth_datetime=birth_dt,
                has_time=has_time,
                calendar="solar",
                gender=gender,
                birth_location=location,
                has_conflict=has_conflict,
                conflict_note=conflict_note,
            )
        except ValueError as exc:
            return ParsedBirthDetails(
                birth_datetime=None,
                has_time=has_time,
                calendar="solar",
                gender=gender,
                birth_location=location,
                parse_error=f"公历日期无效：{exc}",
                has_conflict=has_conflict,
                conflict_note=conflict_note,
            )

    return ParsedBirthDetails(
        birth_datetime=None,
        has_time=False,
        calendar="unknown",
        gender=gender,
        birth_location=location,
        has_conflict=has_conflict,
        conflict_note=conflict_note,
    )


def parse_datetime_from_text(text: str) -> datetime | None:
    normalized = normalize_text(text)
    hour, minute, has_time = parse_time_from_text(normalized)
    explicit_lunar = any(token in normalized for token in ("农历", "阴历"))
    lunar = parse_lunar_date(normalized)
    if lunar and explicit_lunar:
        try:
            year, month, day, is_leap = lunar
            solar_day = sxtwl.fromLunar(year, month, day, is_leap)
            return datetime(
                solar_day.getSolarYear(),
                solar_day.getSolarMonth(),
                solar_day.getSolarDay(),
                hour if has_time else 0,
                minute if has_time else 0,
            )
        except Exception:
            return None

    solar = parse_solar_date(normalized)
    if not solar:
        return None

    try:
        year, month, day = solar
        return datetime(year, month, day, hour if has_time else 0, minute if has_time else 0)
    except ValueError:
        return None
