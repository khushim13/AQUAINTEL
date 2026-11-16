"""Translation and multilingual support for INGRES-Agent (English <-> Hindi).

Preserves all numbers, percentages, units, and place names unchanged.
"""

import re
from typing import Any, Dict, Optional
from app.config import settings

# Mapping of Hindi terminology to English for agent understanding
HINDI_TERM_MAP = [
    # Metrics
    (r"(?:भूजल स्तर|जल स्तर|पानी का स्तर|जलस्तर)", "groundwater level"),
    (r"(?:दोहन दर|दोहन प्रतिशत|दोहन की स्थिति|दोहन अवस्था|दोहन)", "stage of extraction"),
    (r"(?:पुनर्भरण|रिचार्ज|जल पुनर्भरण)", "groundwater recharge"),
    (r"(?:निकासी|निष्कर्षण)", "extraction"),
    (r"(?:सिंचाई|कृषि)", "irrigation"),
    (r"(?:घरेलू|पेयजल)", "domestic"),
    # Categories
    (r"(?:अत्यधिक दोहित|अति दोहित|अतिदोहित|ओवरएक्सप्लॉइटेड)", "over-exploited"),
    (r"(?:सुरक्षित|सेफ)", "safe"),
    (r"(?:गंभीर|क्रिटिकल)", "critical"),
    (r"(?:अर्ध गंभीर|अर्ध-गंभीर|सेमी क्रिटिकल)", "semi-critical"),
    (r"(?:श्रेणी|स्थिति|स्टेटस)", "category"),
    # Actions
    (r"(?:तुलना|कंपेयर|मुकाबला)", "compare"),
    (r"(?:सूची|लिस्ट|दिखाएं|बताएं)", "list"),
    (r"(?:ब्लॉक|प्रखंड)", "blocks"),
    (r"(?:रुझान|ट्रेंड|इतिहास|परिवर्तन)", "historical trend"),
    (r"(?:रैंक|दर्जा|क्रम)", "rank"),
    # Seasons
    (r"(?:पूर्व मानसून|प्री मानसून|मानसून पूर्व)", "pre-monsoon"),
    (r"(?:मानसून बाद|उत्तर मानसून|पोस्ट मानसून)", "post-monsoon"),
    # Place names in Hindi
    (r"जयपुर", "Jaipur"),
    (r"जोधपुर", "Jodhpur"),
    (r"पुणे", "Pune"),
    (r"नागपुर", "Nagpur"),
    (r"नासिक", "Nashik"),
    (r"लुधियाना", "Ludhiana"),
    (r"अमृतसर", "Amritsar"),
    (r"बेंगलुरु|बैंगलोर", "Bengaluru Urban"),
    (r"मैसूर", "Mysuru"),
    (r"वाराणसी|बनारस|काशी", "Varanasi"),
    (r"आगरा", "Agra"),
    (r"चेन्नई", "Chennai"),
    (r"कोयंबटूर", "Coimbatore"),
    (r"अहमदाबाद", "Ahmedabad"),
    (r"हैदराबाद", "Hyderabad"),
    (r"अजमेर", "Ajmer"),
]

HINDI_CATEGORY_NAMES = {
    "Safe": "सुरक्षित (Safe)",
    "Semi-Critical": "अर्ध-गंभीर (Semi-Critical)",
    "Critical": "गंभीर (Critical)",
    "Over-Exploited": "अत्यधिक दोहित (Over-Exploited)",
    "Saline": "लवणीय (Saline)",
}


def detect_language(text: str) -> str:
    """Detect if input text contains Devanagari script (Hindi)."""
    if re.search(r"[\u0900-\u097F]", text):
        return "hi"
    return "en"


def translate_query_to_english(query: str, api_key: Optional[str] = None) -> str:
    """Translate Hindi natural language query to English for the agent.

    Preserves numbers and locations accurately.
    """
    key = api_key or settings.GEMINI_API_KEY
    if key and key != "your_gemini_api_key_here":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            prompt = (
                f"Translate this Indian citizen groundwater query from Hindi to English: '{query}'.\n"
                "Keep all numbers (e.g. 2023) and place names (e.g. Jaipur, Pune) unchanged. "
                "Only return the translated query string."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.0),
            )
            if response.text:
                return response.text.strip()
        except Exception:
            pass

    # Heuristic translation replacement
    translated = query
    for pattern, replacement in HINDI_TERM_MAP:
        translated = re.sub(pattern, replacement, translated, flags=re.IGNORECASE)

    # Standardize common connecting words
    translated = re.sub(r"\bमें\b", "in", translated)
    translated = re.sub(r"\bका\b|\bकी\b|\bके\b", "of", translated)
    translated = re.sub(r"\bऔर\b", "and", translated)
    translated = re.sub(r"\bक्या\b", "what is", translated)
    translated = re.sub(r"\bथा\b|\bहै\b", "", translated)

    return translated.strip()


def translate_answer_to_hindi(
    english_answer: str,
    tool_name: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    tool_data: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None,
) -> str:
    """Translate agent's English answer to Hindi.

    Strictly preserves:
    - All numbers and percentages (34.2, 202.9%, 2023, 145,200.0)
    - All place names (Jaipur, Rajasthan, Pune, Maharashtra)
    - Technical units (mbgl, %, ham)
    """
    key = api_key or settings.GEMINI_API_KEY
    if key and key != "your_gemini_api_key_here":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            prompt = (
                f"Translate this groundwater assistant response into clear, natural Hindi:\n\n{english_answer}\n\n"
                "STRICT RULES:\n"
                "1. Keep ALL numbers, percentages, and metrics EXACTLY as they are (do NOT convert to Hindi numerals).\n"
                "2. Keep all place names (e.g. Jaipur, Rajasthan, Pune, Amber) EXACTLY as they appear.\n"
                "3. Keep units ('mbgl', '%', 'ham') intact.\n"
                "4. Keep the source citation intact.\n"
                "Only return the translated Hindi text."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.1),
            )
            if response.text:
                return response.text.strip()
        except Exception:
            pass

    # Fallback: Synthesize formatted Hindi response directly from tool data
    if not tool_data or "error" in tool_data:
        loc_str = params.get("location") or params.get("district") if params else "अपेक्षित स्थान"
        return f"अनुरोधित प्रश्न ({loc_str}) के लिए डेटा उपलब्ध नहीं है।\n\n• स्रोत: INGRES (ingres.iith.ac.in) / CGWB Open Data"

    val = tool_data.get("value")
    unit = tool_data.get("unit", "")
    year = tool_data.get("year", 2023)
    location = tool_data.get("location", "")
    source = tool_data.get("source", "INGRES (ingres.iith.ac.in) / CGWB Open Data")

    default_prefix = ""
    if params and params.get("year") is None:
        default_prefix = "नवीनतम उपलब्ध मूल्यांकन वर्ष (2023) का स्वतः चयन किया गया। "

    if tool_name == "get_groundwater_level":
        season = params.get("season", "pre_monsoon") if params else "pre_monsoon"
        season_hi = "मानसून बाद" if "post" in season else "पूर्व-मानसून"
        return (
            f"{default_prefix}वर्ष {year} के लिए {location} में {season_hi} भूजल स्तर **{val} {unit}** (मीटर भूतल नीचे) था।\n\n"
            f"• **मान:** {val} {unit}\n"
            f"• **वर्ष:** {year}\n"
            f"• **स्थान:** {location}\n"
            f"• **स्रोत:** {source}"
        )

    elif tool_name == "get_stage_of_extraction":
        return (
            f"{default_prefix}वर्ष {year} के लिए {location} में भूजल दोहन की अवस्था (Stage of Extraction) **{val}{unit}** है।\n\n"
            f"• **मान:** {val}{unit}\n"
            f"• **वर्ष:** {year}\n"
            f"• **स्थान:** {location}\n"
            f"• **स्रोत:** {source}"
        )

    elif tool_name == "get_category":
        cat_hi = HINDI_CATEGORY_NAMES.get(str(val), str(val))
        return (
            f"{default_prefix}वर्ष {year} में {location} के लिए आधिकारिक भूजल मूल्यांकन श्रेणी **{cat_hi}** है।\n\n"
            f"• **श्रेणी:** {val}\n"
            f"• **इकाई:** {unit}\n"
            f"• **वर्ष:** {year}\n"
            f"• **स्थान:** {location}\n"
            f"• **स्रोत:** {source}"
        )

    elif tool_name == "get_recharge":
        return (
            f"{default_prefix}वर्ष {year} के लिए {location} में वार्षिक निष्कर्षण योग्य भूजल संसाधन (पुनर्भरण) **{val:,.1f} {unit}** है।\n\n"
            f"• **मान:** {val:,.1f} {unit}\n"
            f"• **वर्ष:** {year}\n"
            f"• **स्थान:** {location}\n"
            f"• **स्रोत:** {source}"
        )

    elif tool_name == "get_extraction":
        usage = params.get("usage", "total") if params else "total"
        usage_hi = "सिंचाई" if "irr" in usage else ("घरेलू/औद्योगिक" if "dom" in usage else "कुल")
        return (
            f"{default_prefix}वर्ष {year} के लिए {location} में वर्तमान वार्षिक भूजल दोहन ({usage_hi}) **{val:,.1f} {unit}** है।\n\n"
            f"• **मान:** {val:,.1f} {unit}\n"
            f"• **वर्ष:** {year}\n"
            f"• **स्थान:** {location}\n"
            f"• **स्रोत:** {source}"
        )

    elif tool_name == "compare_locations" and isinstance(val, list):
        metric = params.get("metric", "भूजल माप") if params else "भूजल माप"
        lines = [f"{default_prefix}वर्ष {year} के लिए **{metric}** की तुलना:"]
        for it in val:
            lines.append(f"• **{it['location']}:** {it['value']} {unit}")
        lines.append(f"\n• **वर्ष:** {year}")
        lines.append(f"• **स्रोत:** {source}")
        return "\n".join(lines)

    elif tool_name == "get_trend" and isinstance(val, list):
        delta = tool_data.get("delta")
        direction = tool_data.get("direction", "stable")
        dir_hi = "बढ़ रहा है" if direction == "increasing" else ("घट रहा है" if direction == "decreasing" else "स्थिर")
        lines = [
            f"{location} में {year} के दौरान ऐतिहासिक रुझान:",
            f"• **दिशा:** {dir_hi} (शुद्ध परिवर्तन: {delta:+.2f} {unit})",
        ]
        for pt in val:
            lines.append(f"  - {pt['year']}: {pt['value']} {unit}")
        lines.append(f"\n• **स्रोत:** {source}")
        return "\n".join(lines)

    elif tool_name == "list_blocks" and isinstance(val, list):
        count = tool_data.get("total_count", len(val))
        cat_filter = params.get("category", "") if params else ""
        lines = [f"{default_prefix}{location} में कुल {count} मूल्यांकन ब्लॉक पाए गए {cat_filter}:"]
        for b in val[:15]:
            cat_badge = HINDI_CATEGORY_NAMES.get(b.get("category", ""), b.get("category", ""))
            lines.append(f"• **{b['block']}** — {cat_badge} (SOE: {b.get('stage_of_extraction_pct')}%)")
        lines.append(f"\n• **वर्ष:** {year}")
        lines.append(f"• **स्रोत:** {source}")
        return "\n".join(lines)

    # General fallback replacement
    translated = english_answer
    translated = translated.replace("The pre-monsoon groundwater level in", "में पूर्व-मानसून भूजल स्तर")
    translated = translated.replace("The Stage of Groundwater Extraction in", "में भूजल दोहन की अवस्था")
    translated = translated.replace("The groundwater assessment category for", "के लिए भूजल मूल्यांकन श्रेणी")
    translated = translated.replace("Defaulting to the latest available assessment year (2023).", "नवीनतम उपलब्ध मूल्यांकन वर्ष (2023) का स्वतः चयन किया गया।")
    translated = translated.replace("Data not available", "डेटा उपलब्ध नहीं है")
    return translated
