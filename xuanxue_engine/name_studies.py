from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

from pypinyin import Style, lazy_pinyin, pinyin

from .bazi import BaziInput, calculate_bazi
from .numerology import name_number
from .parsing import parse_birth_details


COMPOUND_SURNAMES = {
    "欧阳",
    "司马",
    "上官",
    "夏侯",
    "诸葛",
    "东方",
    "独孤",
    "南宫",
    "尉迟",
    "公孙",
    "公治",
    "慈溪",
    "慕容",
    "长孙",
    "宇文",
    "司徒",
    "司空",
}
NEGATIVE_CHARACTERS = set("病死鬼穷衰灾恶丑弱亡贱残")
AMBIGUOUS_BRAND_SYLLABLES = {"si", "shi", "xi", "qi", "zhi", "chi"}
GENERATION_GIRL_HINTS = ("女宝", "女孩", "女宝宝", "女婴", "女娃", "千金")
GENERATION_BOY_HINTS = ("男宝", "男孩", "男宝宝", "男婴", "男娃", "公子")
GENERATION_STYLE_MARKERS: dict[str, tuple[str, ...]] = {
    "bookish": ("文雅", "书卷", "书香", "清雅", "雅致", "温润", "知性"),
    "classic": ("诗经", "楚辞", "古典", "典雅", "国风", "传统"),
    "bright": ("明朗", "开阔", "明亮", "清朗", "灵动", "朝气"),
    "gentle": ("温柔", "柔和", "安宁", "宁静", "娴静", "柔婉"),
    "graceful": ("大气", "端庄", "从容", "气定", "正气", "清正"),
}
GENERATION_STYLE_LABELS = {
    "bookish": "书卷",
    "classic": "古典",
    "bright": "明朗",
    "gentle": "温润",
    "graceful": "大气",
}
STYLE_TAG_ORDER = ("bookish", "classic", "bright", "gentle", "graceful")
FIVE_ELEMENT_ORDER = ("木", "火", "土", "金", "水")
FIVE_ELEMENT_FAVOR_CHARACTERS: dict[str, set[str]] = {
    "木": set("芷若芸梓栖杉苓筠禾槿榆蔚萱"),
    "火": set("昕晗晴炜昭彤煦昀映煊晞"),
    "土": set("安宁岚允依宛垚怡辰予娴"),
    "金": set("钰锦锐珂玥瑜瑶琬珺铭铃"),
    "水": set("涵清沐汐沁澄泠溪渝霖漪"),
}

CLASSICAL_NAME_ENTRIES: list[dict[str, Any]] = [
    {
        "given_name": "书雅",
        "source_title": "《大戴礼记·保傅》",
        "source_quote": "答远方诸侯，不知文雅之辞。",
        "meaning": "书卷气足，言行雅正，适合希望名字文气端雅的女孩。",
        "style_tags": ["bookish", "graceful", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"木", "金"},
    },
    {
        "given_name": "清妍",
        "source_title": "《月池》",
        "source_quote": "寒池月下明，新月池边曲；若不妬清妍，却成相映烛。",
        "meaning": "清而有华，妍而不俗，整体气质清亮秀雅。",
        "style_tags": ["bright", "graceful", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"水", "金"},
    },
    {
        "given_name": "清婉",
        "source_title": "《诗经·郑风·野有蔓草》",
        "source_quote": "有美一人，清扬婉兮。",
        "meaning": "清丽婉转，读音柔和，带古典闺秀气质。",
        "style_tags": ["gentle", "classic", "graceful"],
        "gender_bias": "female",
        "preferred_elements": {"水", "木"},
    },
    {
        "given_name": "令仪",
        "source_title": "《诗经·小雅·湛露》",
        "source_quote": "岂弟君子，莫不令仪。",
        "meaning": "仪度端整，气质大方，适合想要端庄典雅感的名字。",
        "style_tags": ["graceful", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"火", "木"},
    },
    {
        "given_name": "嘉卉",
        "source_title": "《谷风》",
        "source_quote": "习习谷风，以阴以雨。黾勉同心，不宜有怒。采葑采菲，无以下体？德音莫违，及尔同死。行道迟迟，中心有违。不远伊迩，薄送我畿。谁谓荼苦，其甘如荠。宴尔新昏，如兄如弟。泾以渭浊，湜湜其沚。宴尔新昏，不我屑以。毋逝我梁，毋发我笱。我躬不阅，遑恤我后。就其深矣，方之舟之。就其浅矣，泳之游之。何有何亡，黾勉求之。凡民有丧，匍匐救之。不我能慉，反以我为雠。既阻我德，贾用不售。昔育恐育鞫，及尔颠覆。既生既育，比予于毒。我有旨蓄，亦以御冬。宴尔新昏，以我御穷。有洸有溃，既诒我肄。不念昔者，伊余来塈。",
        "source_excerpt": "原句不便直用，取“嘉卉”之意，偏向美善芳华。",
        "meaning": "嘉为美善，卉为百草，整体有草木生发、秀润温和之意。",
        "style_tags": ["classic", "gentle", "bright"],
        "gender_bias": "female",
        "preferred_elements": {"木"},
    },
    {
        "given_name": "若棠",
        "source_title": "《诗经·召南·甘棠》",
        "source_quote": "蔽芾甘棠，勿翦勿伐，召伯所茇。",
        "meaning": "棠木有护佑、生机之意，“若棠”既柔又有骨。",
        "style_tags": ["classic", "bookish", "gentle"],
        "gender_bias": "female",
        "preferred_elements": {"木"},
    },
    {
        "given_name": "攸宁",
        "source_title": "《诗经·大雅·斯干》",
        "source_quote": "君子攸宁。",
        "meaning": "安定宁和，格局平稳，适合希望名字温定而不弱的气质。",
        "style_tags": ["gentle", "graceful", "classic"],
        "gender_bias": "neutral",
        "preferred_elements": {"土", "水"},
    },
    {
        "given_name": "舒窈",
        "source_title": "《诗经·陈风·月出》",
        "source_quote": "舒窈纠兮，劳心悄兮。",
        "meaning": "舒展从容，窈然有致，整体有婉丽和松弛感。",
        "style_tags": ["gentle", "graceful", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"金", "土"},
    },
    {
        "given_name": "静姝",
        "source_title": "《诗经·邶风·静女》",
        "source_quote": "静女其姝，俟我于城隅。",
        "meaning": "静而美好，传统审美非常稳妥，读感也柔中有定。",
        "style_tags": ["gentle", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"金", "土"},
    },
    {
        "given_name": "清芷",
        "source_title": "《楚辞·九歌·湘夫人》",
        "source_quote": "沅有芷兮澧有兰。",
        "meaning": "芷兰清芬，名字带水木气，气质清芬自持。",
        "style_tags": ["classic", "bookish", "bright"],
        "gender_bias": "female",
        "preferred_elements": {"水", "木"},
    },
    {
        "given_name": "沐兰",
        "source_title": "《楚辞·离骚》",
        "source_quote": "浴兰汤兮沐芳。",
        "meaning": "带有兰芷芬芳与自洁之意，名字轻盈而有古意。",
        "style_tags": ["classic", "gentle", "bright"],
        "gender_bias": "female",
        "preferred_elements": {"水", "木"},
    },
    {
        "given_name": "芳菲",
        "source_title": "《楚辞·九章》",
        "source_quote": "芳与泽其杂糅兮。",
        "meaning": "芳菲自成春意，适合希望名字有灵气和生机的方向。",
        "style_tags": ["bright", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"木", "火"},
    },
    {
        "given_name": "云舒",
        "source_title": "《菜根谭》",
        "source_quote": "去留无意，漫随天外云卷云舒。",
        "meaning": "松弛舒展，气质通透，现代接受度也高。",
        "style_tags": ["bookish", "graceful", "bright"],
        "gender_bias": "neutral",
        "preferred_elements": {"水", "土"},
    },
    {
        "given_name": "知夏",
        "source_title": "《论语·子罕》",
        "source_quote": "知者不惑。",
        "source_excerpt": "借“知”取识见，又以“夏”取明朗生机。",
        "meaning": "知性明朗，有辨识度，既不甜腻也不冷硬。",
        "style_tags": ["bookish", "bright"],
        "gender_bias": "female",
        "preferred_elements": {"火", "木"},
    },
    {
        "given_name": "知柔",
        "source_title": "《道德经》",
        "source_quote": "天下莫柔弱于水，而攻坚强者莫之能胜。",
        "meaning": "柔而不弱，名字有力量感，适合偏温润却不虚软的气质。",
        "style_tags": ["bookish", "gentle", "graceful"],
        "gender_bias": "female",
        "preferred_elements": {"水"},
    },
    {
        "given_name": "令姝",
        "source_title": "《诗经·东方之日》",
        "source_quote": "彼姝者子，在我室兮。",
        "meaning": "姝指美好女子，配“令”更显端方清丽。",
        "style_tags": ["classic", "graceful"],
        "gender_bias": "female",
        "preferred_elements": {"火", "金"},
    },
    {
        "given_name": "安禾",
        "source_title": "《诗经·周颂·丰年》",
        "source_quote": "丰年多黍多稌。",
        "source_excerpt": "取“禾”之丰实安稳意。",
        "meaning": "安稳、丰实、带成长感，适合希望名字温厚好养的方向。",
        "style_tags": ["gentle", "bright"],
        "gender_bias": "neutral",
        "preferred_elements": {"木", "土"},
    },
    {
        "given_name": "瑞禾",
        "source_title": "《尚书》与“嘉禾”文化意象",
        "source_quote": "嘉禾生，邦家宁。",
        "source_excerpt": "取嘉禾、瑞禾的丰年祥瑞传统意象。",
        "meaning": "祥瑞丰实，既有吉意，也不失自然生长之感。",
        "style_tags": ["graceful", "bright", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"木", "土"},
    },
    {
        "given_name": "栖月",
        "source_title": "唐诗月意象",
        "source_quote": "明月松间照，清泉石上流。",
        "source_excerpt": "借月色与栖居之意，重在清夜、安定、澄明。",
        "meaning": "名字偏清冷雅致，适合希望气质更轻盈一点的风格。",
        "style_tags": ["bookish", "gentle", "classic"],
        "gender_bias": "female",
        "preferred_elements": {"木", "水"},
    },
    {
        "given_name": "景宁",
        "source_title": "《诗经》宁字传统与“景行”典故",
        "source_quote": "高山仰止，景行行止。",
        "meaning": "景有光明与大气，宁有安定与持重，搭配比较稳。",
        "style_tags": ["graceful", "bright", "bookish"],
        "gender_bias": "neutral",
        "preferred_elements": {"火", "土"},
    },
    {
        "given_name": "予晴",
        "source_title": "宋词晴景意象",
        "source_quote": "水光潋滟晴方好。",
        "meaning": "名字明朗柔和，带一点温暖开阔感。",
        "style_tags": ["bright", "gentle"],
        "gender_bias": "female",
        "preferred_elements": {"火", "水"},
    },
]

GENERATIVE_NAME_PREFIXES: list[dict[str, Any]] = [
    {
        "char": "景",
        "gender_bias": "male",
        "style_tags": ["bright", "bookish", "graceful", "classic"],
        "preferred_elements": {"火", "土"},
        "source_title": "《诗经·小雅·车舝》",
        "source_quote": "高山仰止，景行行止。",
        "meaning": "取光明坦荡、器度开阔之意。",
        "allowed_suffixes": ["行", "岳", "川", "宁", "泽"],
        "common": True,
    },
    {
        "char": "修",
        "gender_bias": "male",
        "style_tags": ["bookish", "classic", "graceful"],
        "preferred_elements": {"木", "金"},
        "source_title": "《楚辞·离骚》",
        "source_quote": "路漫漫其修远兮。",
        "meaning": "取修为不辍、自持向远之意。",
        "allowed_suffixes": ["远", "言", "宁", "德", "泽"],
        "common": True,
    },
    {
        "char": "怀",
        "gender_bias": "male",
        "style_tags": ["bookish", "classic", "graceful"],
        "preferred_elements": {"水", "金"},
        "source_title": "《楚辞·离骚》",
        "source_quote": "怀瑾握瑜兮。",
        "meaning": "取怀德守正、温润有骨之意。",
        "allowed_suffixes": ["瑾", "泽", "安", "德"],
        "common": True,
    },
    {
        "char": "知",
        "gender_bias": "neutral",
        "style_tags": ["bookish", "classic"],
        "preferred_elements": {"火", "木"},
        "source_title": "《论语·子罕》",
        "source_quote": "知者不惑。",
        "meaning": "取明辨通达、识见清明之意。",
        "allowed_suffixes": ["远", "言", "安", "川"],
        "common": True,
    },
    {
        "char": "明",
        "gender_bias": "male",
        "style_tags": ["bright", "graceful", "classic"],
        "preferred_elements": {"火"},
        "source_title": "《大学》",
        "source_quote": "大学之道，在明明德。",
        "meaning": "取明朗磊落、心性清正之意。",
        "allowed_suffixes": ["德", "岳", "川", "安"],
        "common": True,
    },
    {
        "char": "允",
        "gender_bias": "male",
        "style_tags": ["graceful", "classic", "bookish"],
        "preferred_elements": {"土", "金"},
        "source_title": "《尚书·大禹谟》",
        "source_quote": "惟精惟一，允执厥中。",
        "meaning": "取持中守正、分寸稳当之意。",
        "allowed_suffixes": ["泽", "宁", "安"],
        "common": True,
    },
    {
        "char": "承",
        "gender_bias": "male",
        "style_tags": ["graceful", "classic"],
        "preferred_elements": {"土", "金"},
        "source_title": "《诗经·大雅·下武》",
        "source_quote": "昭兹来许，绳其祖武。",
        "source_excerpt": "借承其志、续其武之意，取担当与延续。",
        "meaning": "取担当稳健、有承接力之意。",
        "allowed_suffixes": ["泽", "岳", "宁", "安"],
        "common": True,
    },
]

GENERATIVE_NAME_SUFFIXES: list[dict[str, Any]] = [
    {
        "char": "行",
        "gender_bias": "male",
        "style_tags": ["classic", "graceful"],
        "preferred_elements": {"土"},
        "source_title": "《诗经·小雅·车舝》",
        "source_quote": "高山仰止，景行行止。",
        "meaning": "取行止有度、道路正大之意。",
        "common": True,
    },
    {
        "char": "远",
        "gender_bias": "male",
        "style_tags": ["bookish", "classic", "graceful"],
        "preferred_elements": {"木", "水"},
        "source_title": "《楚辞·离骚》",
        "source_quote": "路漫漫其修远兮。",
        "meaning": "取志向深远、眼界长阔之意。",
        "common": True,
    },
    {
        "char": "瑾",
        "gender_bias": "male",
        "style_tags": ["bookish", "classic", "graceful"],
        "preferred_elements": {"金", "火"},
        "source_title": "《楚辞·离骚》",
        "source_quote": "怀瑾握瑜兮。",
        "meaning": "以美玉比德，重清贵与自守。",
        "common": True,
    },
    {
        "char": "德",
        "gender_bias": "male",
        "style_tags": ["classic", "graceful", "bookish"],
        "preferred_elements": {"土", "火"},
        "source_title": "《大学》",
        "source_quote": "大学之道，在明明德。",
        "meaning": "取德性自持、内里稳实之意。",
        "common": True,
    },
    {
        "char": "泽",
        "gender_bias": "male",
        "style_tags": ["bright", "graceful", "gentle"],
        "preferred_elements": {"水"},
        "source_title": "《楚辞·九章》",
        "source_quote": "芳与泽其杂糅兮。",
        "meaning": "取润泽广被、气象宽厚之意。",
        "common": True,
    },
    {
        "char": "川",
        "gender_bias": "male",
        "style_tags": ["bright", "bookish"],
        "preferred_elements": {"水"},
        "source_title": "《长歌行》",
        "source_quote": "百川东到海，何时复西归。",
        "meaning": "取胸襟开阔、行气舒展之意。",
        "common": True,
    },
    {
        "char": "岳",
        "gender_bias": "male",
        "style_tags": ["graceful", "bright"],
        "preferred_elements": {"土"},
        "source_title": "《诗经·小雅·车舝》",
        "source_quote": "高山仰止，景行行止。",
        "source_excerpt": "借高山意象取岳峙持重。",
        "meaning": "取格局挺拔、气骨稳重之意。",
        "common": True,
    },
    {
        "char": "宁",
        "gender_bias": "neutral",
        "style_tags": ["gentle", "graceful", "classic"],
        "preferred_elements": {"土", "水"},
        "source_title": "《诗经·大雅·斯干》",
        "source_quote": "君子攸宁。",
        "meaning": "取安定从容、收得住心气之意。",
        "common": True,
    },
    {
        "char": "安",
        "gender_bias": "neutral",
        "style_tags": ["gentle", "graceful"],
        "preferred_elements": {"土"},
        "source_title": "《周易·系辞下》",
        "source_quote": "安而不忘危，存而不忘亡，治而不忘乱。",
        "meaning": "取内心有定、处事有分寸之意。",
        "common": True,
    },
    {
        "char": "言",
        "gender_bias": "male",
        "style_tags": ["bookish", "classic"],
        "preferred_elements": {"木", "金"},
        "source_title": "《周易·家人》",
        "source_quote": "君子以言有物而行有恒。",
        "meaning": "取言有物、行有据之意。",
        "common": True,
    },
]

GENERATIVE_NAME_PAIR_OVERRIDES: dict[str, dict[str, Any]] = {
    "景行": {
        "source_title": "《诗经·小雅·车舝》",
        "source_quote": "高山仰止，景行行止。",
        "meaning": "取光明坦荡、行止有度之意。",
        "style_tags": ["bright", "bookish", "graceful", "classic"],
    },
    "修远": {
        "source_title": "《楚辞·离骚》",
        "source_quote": "路漫漫其修远兮。",
        "meaning": "取修为不辍、志向深远之意。",
        "style_tags": ["bookish", "classic", "graceful"],
    },
    "怀瑾": {
        "source_title": "《楚辞·离骚》",
        "source_quote": "怀瑾握瑜兮。",
        "meaning": "取怀德守正、温润有骨之意。",
        "style_tags": ["bookish", "classic", "graceful"],
    },
    "明德": {
        "source_title": "《大学》",
        "source_quote": "大学之道，在明明德。",
        "meaning": "取明朗磊落、德性自持之意。",
        "style_tags": ["bright", "classic", "graceful", "bookish"],
    },
}

GENERATIVE_SUFFIX_BY_CHAR = {item["char"]: item for item in GENERATIVE_NAME_SUFFIXES}


@dataclass(frozen=True)
class NameStudiesInput:
    name: str
    purpose: str
    birth_info: str = ""
    culture_context: str = ""


def infer_gender_preference(value: str) -> str:
    text = str(value or "")
    if any(token in text for token in GENERATION_GIRL_HINTS):
        return "female"
    if any(token in text for token in GENERATION_BOY_HINTS):
        return "male"
    return ""


def normalize_purpose(value: str) -> str:
    text = (value or "").strip().lower()
    aliases = {
        "起名": "personal",
        "改名": "personal",
        "本人": "personal",
        "品牌": "brand",
        "公司": "brand",
        "店名": "brand",
        "艺名": "stage",
        "笔名": "stage",
    }
    return aliases.get(text, text or "general")


def is_cjk_text(value: str) -> bool:
    return bool(value) and all("\u4e00" <= char <= "\u9fff" for char in value)


def split_name(value: str) -> tuple[str, str]:
    cleaned = re.sub(r"\s+", "", value)
    if len(cleaned) >= 2 and cleaned[:2] in COMPOUND_SURNAMES:
        return cleaned[:2], cleaned[2:]
    if cleaned:
        return cleaned[:1], cleaned[1:]
    return "", ""


def tone_profile(value: str) -> dict[str, Any]:
    tones = []
    syllables = lazy_pinyin(value, style=Style.NORMAL, strict=False)
    tone_marks = pinyin(value, style=Style.TONE3, strict=False)
    for item in tone_marks:
        syllable = item[0]
        tone = 5
        match = re.search(r"([1-5])$", syllable)
        if match:
            tone = int(match.group(1))
        tones.append(tone)
    flat_count = sum(1 for tone in tones if tone in {1, 2})
    oblique_count = sum(1 for tone in tones if tone in {3, 4})
    neutral_count = sum(1 for tone in tones if tone == 5)
    return {
        "syllables": syllables,
        "tones": tones,
        "flat_count": flat_count,
        "oblique_count": oblique_count,
        "neutral_count": neutral_count,
    }


def purpose_assessment(name: str, purpose: str, syllables: list[str]) -> tuple[int, list[str]]:
    score = 50
    notes: list[str] = []
    length = len(name)
    if purpose == "personal":
        if 2 <= length <= 4:
            score += 6
            notes.append("personal-name length is within the common range")
        else:
            score -= 5
            notes.append("personal-name length is outside the common range")
    elif purpose == "brand":
        if 2 <= length <= 4:
            score += 8
            notes.append("brand-name length is compact and memorable")
        else:
            score -= 4
            notes.append("brand-name length may be harder to retain")
        if any(syllable in AMBIGUOUS_BRAND_SYLLABLES for syllable in syllables):
            score -= 2
            notes.append("brand pronunciation may blur in fast speech")
    elif purpose == "stage":
        if 2 <= length <= 4:
            score += 5
            notes.append("stage-name length is workable for repetition and recall")
    return score, notes


def normalize_style_preferences(text: str) -> set[str]:
    normalized = str(text or "")
    styles: set[str] = set()
    for style, markers in GENERATION_STYLE_MARKERS.items():
        if any(marker in normalized for marker in markers):
            styles.add(style)
    return styles


def sort_style_tags(values: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    seen = {str(value).strip() for value in values if str(value).strip()}
    ordered = [tag for tag in STYLE_TAG_ORDER if tag in seen]
    ordered.extend(sorted(tag for tag in seen if tag not in STYLE_TAG_ORDER))
    return ordered


def sort_elements(values: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    seen = {str(value).strip() for value in values if str(value).strip()}
    ordered = [tag for tag in FIVE_ELEMENT_ORDER if tag in seen]
    ordered.extend(sorted(tag for tag in seen if tag not in FIVE_ELEMENT_ORDER))
    return ordered


def humanize_style_tags(values: set[str] | list[str] | tuple[str, ...]) -> list[str]:
    return [GENERATION_STYLE_LABELS.get(tag, tag) for tag in sort_style_tags(values)]


def infer_generation_constraints(*values: str) -> dict[str, bool]:
    text = " ".join(str(value or "") for value in values)
    return {
        "avoid_feminine": any(token in text for token in ("别太娘", "不要太娘", "别太秀气", "不要太秀气")),
        "avoid_obscure": any(token in text for token in ("不生僻", "别用生僻字", "不要生僻字", "别太生僻")),
        "avoid_trendy": any(token in text for token in ("不网红", "别太网红", "不要太网红", "别像网名", "不要像网名")),
    }


def birth_element_preference(birth_info: str) -> dict[str, Any]:
    text = str(birth_info or "").strip()
    if not text:
        return {"favorable": set(), "strongest": set(), "weakest": set(), "note": ""}
    details = parse_birth_details(text)
    if not details.birth_datetime or not details.has_time:
        return {"favorable": set(), "strongest": set(), "weakest": set(), "note": ""}
    try:
        result = calculate_bazi(
            BaziInput(
                birth_datetime=details.birth_datetime,
                gender=str(details.gender or ""),
                birth_location=str(details.birth_location or ""),
                calendar=str(details.calendar or "solar") if str(details.calendar or "") in {"solar", "lunar"} else "solar",
            )
        )
    except Exception:
        return {"favorable": set(), "strongest": set(), "weakest": set(), "note": ""}
    summary = result.get("summary") or {}
    strongest = set(summary.get("strongest_elements") or [])
    weakest = set(summary.get("weakest_elements") or [])
    return {
        "favorable": weakest,
        "strongest": strongest,
        "weakest": weakest,
        "note": "出生时刻已接入本地八字结构，仅作为起名辅助筛选，不替代完整用神判断。",
    }


def given_name_character_elements(given_name: str) -> set[str]:
    matched: set[str] = set()
    for element, chars in FIVE_ELEMENT_FAVOR_CHARACTERS.items():
        if any(char in chars for char in given_name):
            matched.add(element)
    return matched


def resolve_generation_gender(parts: list[dict[str, Any]]) -> str:
    genders = {str(item.get("gender_bias") or "").strip() for item in parts if str(item.get("gender_bias") or "").strip()}
    if "male" in genders and "female" not in genders:
        return "male"
    if "female" in genders and "male" not in genders:
        return "female"
    return "neutral"


def build_generated_entry(prefix: dict[str, Any], suffix: dict[str, Any]) -> dict[str, Any] | None:
    if str(suffix.get("char") or "") not in set(prefix.get("allowed_suffixes") or []):
        return None
    given_name = f"{prefix['char']}{suffix['char']}"
    override = dict(GENERATIVE_NAME_PAIR_OVERRIDES.get(given_name) or {})
    style_tags = sort_style_tags(
        set(override.get("style_tags") or [])
        | set(prefix.get("style_tags") or [])
        | set(suffix.get("style_tags") or [])
    )
    preferred_elements = set(override.get("preferred_elements") or set()) | set(prefix.get("preferred_elements") or set()) | set(
        suffix.get("preferred_elements") or set()
    )
    source_title = str(override.get("source_title") or "").strip()
    if not source_title:
        prefix_title = str(prefix.get("source_title") or "").strip()
        suffix_title = str(suffix.get("source_title") or "").strip()
        source_title = prefix_title if prefix_title == suffix_title else " / ".join(item for item in [prefix_title, suffix_title] if item)
    source_quote = str(override.get("source_quote") or "").strip()
    if not source_quote:
        quotes = []
        for text in (prefix.get("source_quote"), suffix.get("source_quote")):
            cleaned = str(text or "").strip()
            if cleaned and cleaned not in quotes:
                quotes.append(cleaned)
        source_quote = "；".join(quotes[:2])
    source_excerpt = str(override.get("source_excerpt") or "").strip()
    if not source_excerpt:
        prefix_excerpt = str(prefix.get("source_excerpt") or "").strip()
        suffix_excerpt = str(suffix.get("source_excerpt") or "").strip()
        source_excerpt = prefix_excerpt or suffix_excerpt or f"由“{prefix['char']}”与“{suffix['char']}”两字重新组合，整体更偏端正清朗的正式姓名路线。"
    meaning = str(override.get("meaning") or "").strip()
    if not meaning:
        meaning = f"{str(prefix.get('meaning') or '').rstrip('。')}，{str(suffix.get('meaning') or '').rstrip('。')}。"
    return {
        "given_name": given_name,
        "source_title": source_title,
        "source_quote": source_quote,
        "source_excerpt": source_excerpt,
        "meaning": meaning,
        "style_tags": style_tags,
        "gender_bias": str(override.get("gender_bias") or resolve_generation_gender([prefix, suffix])),
        "preferred_elements": preferred_elements,
        "generated_from_parts": True,
        "generation_mode": "composite",
    }


def generated_name_metadata(given_name: str) -> dict[str, Any] | None:
    if len(given_name) != 2:
        return None
    prefix_char, suffix_char = given_name[0], given_name[1]
    suffix = GENERATIVE_SUFFIX_BY_CHAR.get(suffix_char)
    if not suffix:
        return None
    prefix = next((item for item in GENERATIVE_NAME_PREFIXES if item["char"] == prefix_char), None)
    if not prefix:
        return None
    return build_generated_entry(prefix, suffix)


def generate_composite_name_entries(
    preferred_gender: str,
    style_preferences: set[str],
    constraints: dict[str, bool],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for prefix in GENERATIVE_NAME_PREFIXES:
        if preferred_gender == "male" and str(prefix.get("gender_bias") or "") == "female":
            continue
        if constraints.get("avoid_obscure") and not bool(prefix.get("common")):
            continue
        for suffix_char in prefix.get("allowed_suffixes") or []:
            suffix = GENERATIVE_SUFFIX_BY_CHAR.get(str(suffix_char))
            if not suffix:
                continue
            if constraints.get("avoid_obscure") and not bool(suffix.get("common")):
                continue
            if preferred_gender == "male" and resolve_generation_gender([prefix, suffix]) == "female":
                continue
            entry = build_generated_entry(prefix, suffix)
            if not entry:
                continue
            if constraints.get("avoid_feminine") and str(entry.get("gender_bias") or "") == "female":
                continue
            if constraints.get("avoid_trendy") and bool(entry.get("trendy")):
                continue
            if style_preferences and not (set(entry.get("style_tags") or []) & style_preferences):
                # 允许进入候选，但把风格明显不贴的组合放后面
                entry = {**entry, "style_miss": True}
            entries.append(entry)
    return entries


def classical_name_metadata(given_name: str) -> dict[str, Any] | None:
    for entry in CLASSICAL_NAME_ENTRIES:
        if entry["given_name"] == given_name:
            return dict(entry)
    return generated_name_metadata(given_name)


def name_generation_rationale(entry: dict[str, Any], favored_elements: set[str], style_preferences: set[str]) -> str:
    reasons: list[str] = []
    style_tags = set(entry.get("style_tags") or [])
    if entry.get("generated_from_parts"):
        reasons.append("这个名字是按姓氏、性别和风格倾向重新组合出来的，不是直接套现成模板")
    if style_preferences and style_tags & style_preferences:
        reasons.append(f"风格上更贴近你要的{'、'.join(humanize_style_tags(style_tags & style_preferences))}方向")
    if favored_elements and set(entry.get("preferred_elements") or set()) & favored_elements:
        reasons.append("字义和字形偏向补足出生盘里相对偏弱的五行气质")
    if entry.get("meaning"):
        reasons.append(str(entry["meaning"]))
    return "；".join(reasons[:3])


def score_generation_entry(
    surname: str,
    entry: dict[str, Any],
    preferred_gender: str,
    style_preferences: set[str],
    favored_elements: set[str],
) -> tuple[int, dict[str, Any]]:
    given_name = str(entry.get("given_name") or "").strip()
    full_name = f"{surname}{given_name}"
    score = 72
    notes: list[str] = []
    gender_bias = str(entry.get("gender_bias") or "neutral")
    if preferred_gender and gender_bias == preferred_gender:
        score += 6
        notes.append("性别气质匹配度较高")
    elif preferred_gender and gender_bias == "neutral":
        score += 3
        notes.append("名字气质中性，适配面较宽")

    style_tags = set(entry.get("style_tags") or [])
    if style_preferences and style_tags & style_preferences:
        score += 7
        notes.append("风格方向贴合当前偏好")
    elif style_preferences:
        score -= 2

    element_tags = set(entry.get("preferred_elements") or set())
    if favored_elements and element_tags & favored_elements:
        score += 8
        notes.append("字义意象能呼应出生信息里的偏弱五行")

    if entry.get("generated_from_parts"):
        score += 4
        notes.append("名字由本地字义库重新组合，不是固定模板名")

    phonetic = tone_profile(full_name)
    if phonetic["flat_count"] and phonetic["oblique_count"]:
        score += 4
        notes.append("读音平仄有起伏，叫起来更顺")
    elif len(phonetic["tones"]) >= 2:
        score -= 2

    if len(set(full_name)) == len(full_name):
        score += 2
    else:
        score -= 3

    if NEGATIVE_CHARACTERS & set(full_name):
        score -= 12
        notes.append("名字含有本地过滤字")

    surname_pinyin = lazy_pinyin(surname, style=Style.NORMAL, strict=False)
    given_pinyin = lazy_pinyin(given_name, style=Style.NORMAL, strict=False)
    repeated = surname_pinyin and given_pinyin and surname_pinyin[-1] == given_pinyin[0]
    if repeated:
        score -= 2
        notes.append("姓与名首音较近，口呼辨识度稍弱")

    romanized_name = "".join(phonetic["syllables"])
    expression = name_number(romanized_name)
    if expression in {1, 3, 5, 6, 8, 9}:
        score += 2
        notes.append(f"拼音桥接数落在 {expression}")

    derived = {
        "phonetic_profile": phonetic,
        "expression_bridge_number": expression,
        "style_tags": sort_style_tags(style_tags),
        "preferred_elements": sort_elements(element_tags),
        "character_elements": sort_elements(given_name_character_elements(given_name)),
        "source_title": entry.get("source_title") or "",
        "source_quote": entry.get("source_quote") or "",
        "source_excerpt": entry.get("source_excerpt") or "",
        "meaning": entry.get("meaning") or "",
        "why_selected": name_generation_rationale(entry, favored_elements, style_preferences),
        "notes": notes,
    }
    return score, derived


def generate_name_candidates(
    surname: str,
    purpose: str = "personal",
    birth_info: str = "",
    gender_hint: str = "",
    culture_context: str = "",
    limit: int = 10,
) -> list[dict[str, Any]]:
    cleaned_surname = re.sub(r"\s+", "", surname or "")
    if not cleaned_surname:
        return []
    if purpose and normalize_purpose(purpose) != "personal":
        return []

    preferred_gender = infer_gender_preference(gender_hint or birth_info or culture_context)
    style_preferences = normalize_style_preferences(" ".join(filter(None, [gender_hint, birth_info, culture_context])))
    birth_pref = birth_element_preference(birth_info)
    favored_elements = set(birth_pref.get("favorable") or set())
    constraints = infer_generation_constraints(gender_hint, birth_info, culture_context)

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    source_entries: list[dict[str, Any]] = []
    if preferred_gender == "male" or constraints.get("avoid_feminine"):
        source_entries.extend(generate_composite_name_entries(preferred_gender, style_preferences, constraints))
    if preferred_gender != "male" or len(source_entries) < max(6, limit):
        source_entries.extend(CLASSICAL_NAME_ENTRIES)

    for entry in source_entries:
        given_name = str(entry.get("given_name") or "").strip()
        if not given_name:
            continue
        if preferred_gender == "male" and entry.get("gender_bias") == "female":
            continue
        full_name = f"{cleaned_surname}{given_name}"
        if full_name in seen:
            continue
        seen.add(full_name)
        score, derived = score_generation_entry(
            cleaned_surname,
            entry,
            preferred_gender,
            style_preferences,
            favored_elements,
        )
        candidates.append(
            {
                "name": full_name,
                "surname": cleaned_surname,
                "given_name": given_name,
                "score": score,
                "confidence": "medium" if score >= 84 else "low" if score < 75 else "medium",
                "source_title": derived["source_title"],
                "source_quote": derived["source_quote"],
                "source_excerpt": derived["source_excerpt"],
                "meaning": derived["meaning"],
                "style_tags": derived["style_tags"],
                "preferred_elements": derived["preferred_elements"],
                "character_elements": derived["character_elements"],
                "expression_bridge_number": derived["expression_bridge_number"],
                "why_selected": derived["why_selected"],
                "supporting_signals": list(derived["notes"][:3]),
                "birth_support_note": birth_pref.get("note") or "",
            }
        )

    candidates.sort(
        key=lambda item: (
            int(item.get("score") or 0),
            len(item.get("style_tags") or []),
            item.get("name") or "",
        ),
        reverse=True,
    )
    return candidates[: max(1, limit)]


def calculate_name_studies(data: NameStudiesInput) -> dict[str, Any]:
    name = re.sub(r"\s+", "", data.name or "")
    if not name:
        raise ValueError("name is required")

    purpose = normalize_purpose(data.purpose)
    script = "cjk" if is_cjk_text(name) else "latin" if name.isascii() else "mixed"
    surname, given_name = split_name(name) if script == "cjk" else ("", name)

    score = 50
    supporting_signals: list[str] = []
    risk_flags = [
        "This local name-studies engine evaluates structure, phonetics, purpose fit, and a pinyin-based numerology bridge.",
        "Traditional Kangxi stroke counts and full five-grid schools are not bundled yet, so this is not presented as a complete orthodox five-grid reading.",
    ]

    derived_factors: dict[str, Any] = {
        "script": script,
        "length": len(name),
        "unique_character_count": len(set(name)),
    }

    if script == "cjk":
        phonetic = tone_profile(name)
        syllable_text = " ".join(phonetic["syllables"])
        romanized_name = "".join(phonetic["syllables"])
        derived_factors["surname"] = surname
        derived_factors["given_name"] = given_name
        derived_factors["phonetic_profile"] = phonetic
        supporting_signals.append(f"拼音特征为：{syllable_text}。")

        if phonetic["flat_count"] and phonetic["oblique_count"]:
            score += 4
            supporting_signals.append("声调走向有平仄变化，整体节奏会更顺。")
        elif len(phonetic["tones"]) >= 2:
            score -= 3
            supporting_signals.append("声调走向相对偏平，读起来的起伏感会弱一些。")

        if len(set(name)) == len(name):
            score += 2
            supporting_signals.append("字形没有重复，辨识度会更好。")
        else:
            score -= 3
            supporting_signals.append("字形重复会拉低名字辨识度。")

        if NEGATIVE_CHARACTERS & set(name):
            score -= 12
            supporting_signals.append("名字里出现了本地负面字筛查项。")
        else:
            score += 2

        expression = name_number(romanized_name)
        derived_factors["expression_bridge_number"] = expression
        if expression in {1, 3, 5, 6, 8, 9}:
            score += 2
            supporting_signals.append(f"拼音桥接数落在{expression}。")

        metadata = classical_name_metadata(given_name)
        if metadata:
            derived_factors["classical_source"] = {
                "title": metadata.get("source_title") or "",
                "quote": metadata.get("source_quote") or "",
                "excerpt": metadata.get("source_excerpt") or "",
                "meaning": metadata.get("meaning") or "",
                "style_tags": list(metadata.get("style_tags") or []),
                "preferred_elements": sort_elements(metadata.get("preferred_elements") or set()),
            }
            score += 7
            supporting_signals.append("在本地命名语料里命中了经典出处。")

        birth_pref = birth_element_preference(data.birth_info)
        favored = set(birth_pref.get("favorable") or set())
        if favored and metadata and set(metadata.get("preferred_elements") or set()) & favored:
            score += 5
            supporting_signals.append("按出生信息粗筛，这个名字的语义五行倾向是加分项。")
            derived_factors["birth_screening"] = {
                "favored_elements": sorted(favored),
                "note": birth_pref.get("note") or "",
            }
        elif birth_pref.get("note"):
            derived_factors["birth_screening"] = {
                "favored_elements": sorted(favored),
                "note": birth_pref.get("note") or "",
            }
    else:
        romanized_name = re.sub(r"[^A-Za-z]", "", name)
        expression = name_number(romanized_name)
        derived_factors["expression_bridge_number"] = expression
        if expression is not None:
            supporting_signals.append(f"字母表达数落在{expression}。")
            score += 2
        if script == "mixed":
            score -= 4
            risk_flags.append("Mixed-script names are harder to score consistently across pronunciation systems.")

    purpose_score, purpose_notes = purpose_assessment(
        name,
        purpose,
        derived_factors.get("phonetic_profile", {}).get("syllables", []),
    )
    score += purpose_score - 50
    supporting_signals.extend(note.capitalize() + "." for note in purpose_notes)

    if data.birth_info:
        risk_flags.append("Birth-info-based five-element compensation is currently a screening aid, not a full orthodox yong-shen naming method.")

    if score >= 65:
        primary = f"姓名学看，{name}对当前{purpose or '通用'}用途的适配度较强。"
        confidence = "medium"
    elif score >= 50:
        primary = f"姓名学看，{name}在当前用途下可用，但优缺点并存。"
        confidence = "medium"
    else:
        primary = f"姓名学看，{name}在当前规则下有比较明显的音义阻力。"
        confidence = "low"

    return {
        "system": "name_studies",
        "question_type": "naming",
        "score": score,
        "used_inputs": {
            "name": data.name,
            "purpose": purpose,
            "birth_info": data.birth_info,
            "culture_context": data.culture_context,
        },
        "missing_inputs": [],
        "derived_factors": derived_factors,
        "primary_finding": primary,
        "supporting_signals": supporting_signals,
        "risk_flags": risk_flags,
        "time_window": "Use this as a screening layer before any final naming decision.",
        "confidence": confidence,
        "rules_path": [
            "script normalization",
            "surname/given split",
            "pinyin and tone analysis",
            "classical corpus matching",
            "purpose-fit heuristics",
            "birth-info screening",
            "pinyin numerology bridge",
        ],
    }
