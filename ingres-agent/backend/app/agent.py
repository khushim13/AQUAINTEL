"""INGRES Virtual Assistant Agent using Gemini Function Calling.

Orchestrates:
1. User query -> Gemini Function Calling
2. Entity resolution via RapidFuzz
3. Tool execution over INGRES SQLite database
4. Final grounded response composition adhering to strict guidelines
"""

import os
import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.config import settings
from app.resolver import resolver
from app.tools import (
    get_groundwater_level,
    get_stage_of_extraction,
    get_category,
    get_recharge,
    get_extraction,
    compare_locations,
    get_trend,
    rank_locations,
    list_blocks,
)

SYSTEM_INSTRUCTION = """You are INGRES-Agent, the authoritative groundwater virtual assistant for India (INGRES / CGWB open data, SIH25066).
You help citizens, farmers, researchers, and government officials query official groundwater resource statistics.

Strict Operating Rules:
1. NEVER state any numbers or quantitative statistics that were not explicitly returned by a tool call. Zero hallucination.
2. If the user does not specify a year, default to the latest available assessment year (2023) and explicitly state: "Defaulting to the latest available assessment year (2023)".
3. If the tool returns an error or data is missing, state clearly: "data not available".
4. Always explicitly cite:
   - value (the real number or category)
   - unit (e.g., 'mbgl', '%', 'ham', 'category')
   - year (e.g., 2023)
   - location (canonical district/block and state)
   - source: "INGRES (ingres.iith.ac.in) / CGWB Open Data"
5. If the location is ambiguous, politely list the matching candidates and ask the user to clarify.
6. Provide a concise, professional, and accessible response.
"""

TOOL_REGISTRY = {
    "get_groundwater_level": get_groundwater_level,
    "get_stage_of_extraction": get_stage_of_extraction,
    "get_category": get_category,
    "get_recharge": get_recharge,
    "get_extraction": get_extraction,
    "compare_locations": compare_locations,
    "get_trend": get_trend,
    "rank_locations": rank_locations,
    "list_blocks": list_blocks,
}


class AgentOutput(BaseModel):
    answer: str
    tool_called: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None


def get_gemini_tools():
    """Build Gemini function declarations for the tools."""
    try:
        from google.genai import types

        return [
            types.Tool(
                function_declarations=[
                    types.FunctionDeclaration(
                        name="get_groundwater_level",
                        description="Retrieve depth to groundwater level in meters below ground level (mbgl) for pre-monsoon or post-monsoon seasons.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="Name of district, block, or city (e.g. 'Jaipur', 'Pune')"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year (e.g. 2023, 2022)"),
                                "season": types.Schema(type=types.Type.STRING, description="'pre_monsoon' or 'post_monsoon'. Defaults to 'pre_monsoon'"),
                            },
                            required=["location"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_stage_of_extraction",
                        description="Retrieve the Stage of Groundwater Extraction percentage (SOE %).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="District or block name"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                            },
                            required=["location"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_category",
                        description="Retrieve groundwater assessment category (Safe, Semi-Critical, Critical, Over-Exploited).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="District or block name"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                            },
                            required=["location"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_recharge",
                        description="Retrieve Annual Extractable Groundwater Resource (in ham / hectare-meters).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="District or block name"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                            },
                            required=["location"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_extraction",
                        description="Retrieve Current Annual Groundwater Extraction in ham (total, irrigation, domestic/industrial).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="District or block name"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                                "usage": types.Schema(type=types.Type.STRING, description="'total', 'irrigation', or 'domestic'"),
                            },
                            required=["location"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="compare_locations",
                        description="Compare groundwater metrics (stage_of_extraction, water_level, recharge, extraction) across multiple locations.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "locations": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(type=types.Type.STRING),
                                    description="List of district or block names to compare",
                                ),
                                "metric": types.Schema(type=types.Type.STRING, description="Metric to compare: 'stage_of_extraction', 'water_level', 'recharge', 'extraction'"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                            },
                            required=["locations", "metric"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="get_trend",
                        description="Retrieve historical trend for a metric over multiple years at a specific location.",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "location": types.Schema(type=types.Type.STRING, description="District or block name"),
                                "metric": types.Schema(type=types.Type.STRING, description="Metric: 'water_level', 'stage_of_extraction', 'recharge', 'extraction'"),
                                "start_year": types.Schema(type=types.Type.INTEGER, description="Start year"),
                                "end_year": types.Schema(type=types.Type.INTEGER, description="End year"),
                            },
                            required=["location", "metric"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="rank_locations",
                        description="Rank a list of locations by a metric (highest or lowest first).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "locations": types.Schema(
                                    type=types.Type.ARRAY,
                                    items=types.Schema(type=types.Type.STRING),
                                    description="List of location names",
                                ),
                                "metric": types.Schema(type=types.Type.STRING, description="Metric to rank by"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                                "ascending": types.Schema(type=types.Type.BOOLEAN, description="False for highest first, True for lowest first"),
                            },
                            required=["locations", "metric"],
                        ),
                    ),
                    types.FunctionDeclaration(
                        name="list_blocks",
                        description="List all assessment blocks in a district, optionally filtered by category (Safe, Semi-Critical, Critical, Over-Exploited).",
                        parameters=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "district": types.Schema(type=types.Type.STRING, description="District name"),
                                "category": types.Schema(type=types.Type.STRING, description="Optional category filter (e.g. 'Over-Exploited')"),
                                "year": types.Schema(type=types.Type.INTEGER, description="Assessment year"),
                            },
                            required=["district"],
                        ),
                    ),
                ]
            )
        ]
    except Exception:
        return []


def normalize_tool_parameters(tool_name: str, raw_params: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
    """Normalize location names in parameters using RapidFuzz resolver."""
    params = dict(raw_params)
    ambiguity_msg = None

    # Handle single location param
    if "location" in params and isinstance(params["location"], str):
        res = resolver.resolve(params["location"])
        if res.status == "ambiguous":
            candidates_str = ", ".join([f"{c.canonical_name} ({c.entity_type}, {c.state})" for c in res.candidates[:4]])
            ambiguity_msg = f"The location '{params['location']}' is ambiguous. Did you mean one of these: {candidates_str}?"
        elif res.status == "resolved":
            params["location"] = res.canonical_name

    # Handle district param (for list_blocks)
    if "district" in params and isinstance(params["district"], str):
        res = resolver.resolve(params["district"], entity_type="district")
        if res.status == "resolved":
            params["district"] = res.canonical_name

    # Handle multiple locations list
    if "locations" in params and isinstance(params["locations"], list):
        norm_list = []
        for loc_item in params["locations"]:
            res = resolver.resolve(loc_item)
            norm_list.append(res.canonical_name if res.status == "resolved" else loc_item)
        params["locations"] = norm_list

    return params, ambiguity_msg


def compose_grounded_answer(tool_name: str, params: Dict[str, Any], tool_data: Dict[str, Any], raw_message: str) -> str:
    """Compose the final grounded answer following the system prompt rules."""
    if "error" in tool_data:
        return f"Data not available for the requested query ({params.get('location') or params.get('district') or 'location'}). Source: INGRES (ingres.iith.ac.in) / CGWB Open Data."

    year_stated = params.get("year") is not None
    year_prefix = "" if year_stated else "Defaulting to the latest available assessment year (2023). "

    val = tool_data.get("value")
    unit = tool_data.get("unit", "")
    year = tool_data.get("year", 2023)
    location = tool_data.get("location", "the specified region")
    source = tool_data.get("source", "INGRES (ingres.iith.ac.in) / CGWB Open Data")

    if tool_name == "get_groundwater_level":
        season = params.get("season", "pre_monsoon").replace("_", "-")
        return (
            f"{year_prefix}The {season} groundwater level in {location} for year {year} was "
            f"**{val} {unit}** (meters below ground level).\n\n"
            f"• **Value:** {val} {unit}\n"
            f"• **Year:** {year}\n"
            f"• **Location:** {location}\n"
            f"• **Source:** {source}"
        )

    elif tool_name == "get_stage_of_extraction":
        return (
            f"{year_prefix}The Stage of Groundwater Extraction in {location} for year {year} is "
            f"**{val}{unit}**.\n\n"
            f"• **Value:** {val}{unit}\n"
            f"• **Year:** {year}\n"
            f"• **Location:** {location}\n"
            f"• **Source:** {source}"
        )

    elif tool_name == "get_category":
        return (
            f"{year_prefix}The groundwater assessment category for {location} in year {year} is "
            f"**{val}**.\n\n"
            f"• **Value:** {val}\n"
            f"• **Unit:** {unit}\n"
            f"• **Year:** {year}\n"
            f"• **Location:** {location}\n"
            f"• **Source:** {source}"
        )

    elif tool_name == "get_recharge":
        return (
            f"{year_prefix}The Annual Extractable Groundwater Resource (Recharge) in {location} for year {year} is "
            f"**{val:,.1f} {unit}**.\n\n"
            f"• **Value:** {val:,.1f} {unit}\n"
            f"• **Year:** {year}\n"
            f"• **Location:** {location}\n"
            f"• **Source:** {source}"
        )

    elif tool_name == "get_extraction":
        usage = params.get("usage", "total")
        return (
            f"{year_prefix}The current annual groundwater extraction ({usage}) in {location} for year {year} is "
            f"**{val:,.1f} {unit}**.\n\n"
            f"• **Value:** {val:,.1f} {unit}\n"
            f"• **Year:** {year}\n"
            f"• **Location:** {location}\n"
            f"• **Source:** {source}"
        )

    elif tool_name == "compare_locations":
        lines = [f"{year_prefix}Comparison of **{params.get('metric', 'metrics')}** for {year}:"]
        for item in val:
            lines.append(f"• **{item['location']}:** {item['value']} {unit}")
        lines.append(f"\n• **Year:** {year}")
        lines.append(f"• **Source:** {source}")
        return "\n".join(lines)

    elif tool_name == "get_trend":
        delta = tool_data.get("delta")
        direction = tool_data.get("direction", "stable")
        lines = [
            f"Historical trend for **{params.get('metric', 'groundwater metric')}** in {location} over {year}:",
            f"• **Direction:** {direction.capitalize()} (Net change: {delta:+.2f} {unit})",
        ]
        for pt in val:
            lines.append(f"  - {pt['year']}: {pt['value']} {unit}")
        lines.append(f"\n• **Source:** {source}")
        return "\n".join(lines)

    elif tool_name == "rank_locations":
        lines = [f"{year_prefix}Rankings by **{params.get('metric')}** ({tool_data.get('rank_order', 'descending')}):"]
        for item in val:
            lines.append(f"  {item['rank']}. **{item['location']}:** {item['value']} {unit}")
        lines.append(f"\n• **Year:** {year}")
        lines.append(f"• **Source:** {source}")
        return "\n".join(lines)

    elif tool_name == "list_blocks":
        cat_filter = params.get("category", "")
        filter_text = f" ({cat_filter})" if cat_filter else ""
        lines = [f"{year_prefix}Found {tool_data.get('total_count', len(val))} assessment blocks in {location}{filter_text}:"]
        for b in val[:15]:
            cat_info = f" — {b['category']}" if b.get("category") else ""
            soe_info = f" (SOE: {b['stage_of_extraction_pct']}%)" if b.get("stage_of_extraction_pct") is not None else ""
            lines.append(f"• **{b['block']}**{cat_info}{soe_info}")
        if len(val) > 15:
            lines.append(f"...and {len(val) - 15} more blocks.")
        lines.append(f"\n• **Year:** {year}")
        lines.append(f"• **Source:** {source}")
        return "\n".join(lines)

    return f"Result: {val} {unit} for {location} ({year}). Source: {source}."


def heuristic_intent_parser(user_message: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """Semantic intent parser for natural language queries (works offline and as zero-latency fallback)."""
    msg = user_message.lower()

    # Extract year if present (e.g. 2021, 2022, 2023)
    year_match = re.search(r"\b(202[0-5])\b", msg)
    year = int(year_match.group(1)) if year_match else None

    # Check for compare queries
    if "compare" in msg or " vs " in msg or " versus " in msg or "between" in msg:
        locations_found = []
        for name in ["jaipur", "jodhpur", "pune", "nagpur", "nashik", "ludhiana", "amritsar", "bengaluru", "bangalore", "mysuru", "varanasi", "agra", "chennai", "coimbatore", "ahmedabad", "hyderabad"]:
            if name in msg:
                locations_found.append(name.capitalize())
        if len(locations_found) >= 2:
            metric = "stage_of_extraction"
            if "water level" in msg or "depth" in msg or "mbgl" in msg:
                metric = "water_level"
            elif "recharge" in msg or "resource" in msg:
                metric = "recharge"
            elif "extract" in msg:
                metric = "extraction"
            return "compare_locations", {"locations": locations_found, "metric": metric, "year": year}

    # Check for rank queries
    if "rank" in msg or "top" in msg or "highest" in msg or "lowest" in msg:
        locations_found = []
        for name in ["jaipur", "jodhpur", "pune", "nagpur", "nashik", "ludhiana", "amritsar", "bengaluru", "bangalore", "mysuru", "varanasi", "agra", "chennai", "coimbatore", "ahmedabad", "hyderabad"]:
            if name in msg:
                locations_found.append(name.capitalize())
        if locations_found:
            return "rank_locations", {"locations": locations_found, "metric": "stage_of_extraction", "year": year}

    # Check for list blocks query
    if "block" in msg and ("list" in msg or "all" in msg or "show" in msg or "find" in msg or "what are" in msg or "critical" in msg or "over" in msg):
        cat = None
        if "over-exploited" in msg or "overexploited" in msg or "over exploited" in msg:
            cat = "Over-Exploited"
        elif "critical" in msg and "semi" not in msg:
            cat = "Critical"
        elif "semi-critical" in msg or "semi critical" in msg:
            cat = "Semi-Critical"
        elif "safe" in msg:
            cat = "Safe"
        
        # Extract district name
        dist_candidates = ["jaipur", "jodhpur", "pune", "nagpur", "nashik", "ludhiana", "amritsar", "bengaluru urban", "bengaluru", "bangalore", "mysuru", "varanasi", "agra", "chennai", "coimbatore", "ahmedabad", "hyderabad"]
        dist = next((d.capitalize() for d in dist_candidates if d in msg), "Jaipur")
        params = {"district": dist, "year": year}
        if cat:
            params["category"] = cat
        return "list_blocks", params

    # Check for historical trend query
    if "trend" in msg or "historical" in msg or "over time" in msg or "change" in msg or "past years" in msg:
        loc_candidates = ["jaipur", "jodhpur", "pune", "nagpur", "nashik", "ludhiana", "amritsar", "bengaluru", "bangalore", "mysuru", "varanasi", "agra", "ajmer", "chennai", "coimbatore", "ahmedabad", "hyderabad"]
        loc = next((l.capitalize() for l in loc_candidates if l in msg), "Jaipur")
        metric = "water_level" if "level" in msg or "depth" in msg or "mbgl" in msg else "stage_of_extraction"
        return "get_trend", {"location": loc, "metric": metric}

    # Extract primary location
    loc_candidates = [
        "jaipur", "jodhpur", "pune", "nagpur", "nashik", "ludhiana", "amritsar",
        "bengaluru urban", "bengaluru", "bangalore", "mysuru", "varanasi", "agra",
        "ajmer", "chennai", "coimbatore", "ahmedabad", "hyderabad", "amber",
        "bassi", "chaksu", "jhotwara", "haveli", "baramati", "shirur", "daund",
        "khanna", "samrala", "doraha", "jagraon"
    ]
    target_loc = None
    for cand in loc_candidates:
        if cand in msg:
            target_loc = cand.capitalize()
            break

    if not target_loc:
        # Extract location after prepositions like 'in', 'for', 'of', 'at'
        prep_match = re.search(r"\b(?:in|at|for|of)\s+([A-Za-z0-9_-]+)", user_message)
        if prep_match:
            candidate = prep_match.group(1).strip()
            if candidate.lower() not in ("district", "block", "state", "the", "year", "all"):
                target_loc = candidate

    if not target_loc:
        # Try finding location via words
        words = re.findall(r"\b[A-Z][a-z0-9]+\b", user_message)
        for w in words:
            if w.lower() not in ("what", "is", "the", "in", "for", "district", "block", "state", "show", "tell", "groundwater", "annual", "level", "current"):
                target_loc = w
                break

    if not target_loc:
        target_loc = "unknown"

    # Route based on metric intent
    if "level" in msg or "depth" in msg or "mbgl" in msg or "water table" in msg:
        season = "post_monsoon" if "post" in msg else "pre_monsoon"
        return "get_groundwater_level", {"location": target_loc, "year": year, "season": season}

    if "stage" in msg or "soe" in msg or "%" in msg or "percent" in msg or "percentage" in msg:
        return "get_stage_of_extraction", {"location": target_loc, "year": year}

    if "category" in msg or "status" in msg or "safe" in msg or "critical" in msg or "over-exploited" in msg or "overexploited" in msg:
        return "get_category", {"location": target_loc, "year": year}

    if "recharge" in msg or "resource" in msg or "replenish" in msg:
        return "get_recharge", {"location": target_loc, "year": year}

    if "extract" in msg or "draft" in msg or "usage" in msg or "pump" in msg:
        usage = "irrigation" if "irrigation" in msg or "agri" in msg else ("domestic" if "domestic" in msg or "drinking" in msg else "total")
        return "get_extraction", {"location": target_loc, "year": year, "usage": usage}

    # Default fallback to category / status
    return "get_category", {"location": target_loc, "year": year}


async def run_agent(user_message: str, api_key: Optional[str] = None) -> AgentOutput:
    """Execute the INGRES virtual assistant agent flow."""
    key = api_key or settings.GEMINI_API_KEY
    tool_name: Optional[str] = None
    raw_params: Dict[str, Any] = {}

    # 1. Attempt Gemini Function Calling if API key is provided
    if key and key != "your_gemini_api_key_here":
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=key)
            tools = get_gemini_tools()

            config = types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                tools=tools,
                temperature=0.1,
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_message,
                config=config,
            )

            # Check if Gemini called a function
            if response.function_calls:
                call = response.function_calls[0]
                tool_name = call.name
                raw_params = dict(call.args or {})
        except Exception:
            # Fall back smoothly to semantic intent parser
            tool_name = None

    # 2. Heuristic fallback parser if Gemini wasn't used or didn't return a function call
    if not tool_name:
        parsed = heuristic_intent_parser(user_message)
        if parsed:
            tool_name, raw_params = parsed
        else:
            return AgentOutput(
                answer="I couldn't identify the groundwater metric or location you are querying. Please ask e.g.: 'What is the groundwater level in Jaipur in 2023?' or 'Is Pune safe or over-exploited?'",
                tool_called=None,
                params=None,
                data=None,
            )

    # 3. Entity Resolution: Normalize location names using RapidFuzz
    normalized_params, ambiguity_msg = normalize_tool_parameters(tool_name, raw_params)

    if ambiguity_msg:
        return AgentOutput(
            answer=ambiguity_msg,
            tool_called=tool_name,
            params=normalized_params,
            data={"status": "ambiguous"},
        )

    # 4. Tool Execution: Run DB function
    tool_func = TOOL_REGISTRY.get(tool_name)
    if not tool_func:
        return AgentOutput(
            answer=f"Tool '{tool_name}' is not registered.",
            tool_called=tool_name,
            params=normalized_params,
            data=None,
        )

    tool_data = tool_func(**normalized_params)

    # 5. Model Composes Final Answer (Grounded synthesis)
    # If Gemini client is active, we can also pass function response back
    final_answer = compose_grounded_answer(tool_name, normalized_params, tool_data, user_message)

    return AgentOutput(
        answer=final_answer,
        tool_called=tool_name,
        params=normalized_params,
        data=tool_data,
    )
