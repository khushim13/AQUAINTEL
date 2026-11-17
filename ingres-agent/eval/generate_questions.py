"""Generates 100+ evaluation questions computed directly from the INGRES database."""

import json
import sqlite3
from pathlib import Path
import sys

# Add backend to path to import tools
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

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
from app.resolver import resolver


def generate_golden_dataset():
    questions = []
    qid = 1

    # -------------------------------------------------------------
    # Category 1: Groundwater Level (mbgl) - 15 questions
    # -------------------------------------------------------------
    gw_samples = [
        ("What is the groundwater level in Jaipur in 2023?", "Jaipur", 2023, "pre_monsoon"),
        ("Pre-monsoon water level in Jaipur for 2023", "Jaipur", 2023, "pre_monsoon"),
        ("What was the post-monsoon water level in Jaipur in 2023?", "Jaipur", 2023, "post_monsoon"),
        ("Groundwater level in Jaipur in 2022", "Jaipur", 2022, "pre_monsoon"),
        ("Groundwater depth in Pune in 2023", "Pune", 2023, "pre_monsoon"),
        ("What is the post-monsoon water level in Pune in 2023?", "Pune", 2023, "post_monsoon"),
        ("Depth to groundwater in Ludhiana in 2023", "Ludhiana", 2023, "pre_monsoon"),
        ("Water level in Amritsar in 2023", "Amritsar", 2023, "pre_monsoon"),
        ("Water level depth in Bengaluru Urban in 2023", "Bengaluru Urban", 2023, "pre_monsoon"),
        ("Pre-monsoon water table in Varanasi in 2023", "Varanasi", 2023, "pre_monsoon"),
        ("Groundwater level in Agra in 2023", "Agra", 2023, "pre_monsoon"),
        ("What is the water level in Chennai in 2023?", "Chennai", 2023, "pre_monsoon"),
        ("Water level in Coimbatore in 2023", "Coimbatore", 2023, "pre_monsoon"),
        # Misspelling
        ("Water level in Jaipru in 2023", "Jaipru", 2023, "pre_monsoon"),
        # Missing year (defaults to 2023)
        ("What is the groundwater level in Pune?", "Pune", None, "pre_monsoon"),
    ]

    for q_text, loc, yr, season in gw_samples:
        ans = get_groundwater_level(loc, year=yr, season=season)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "water_level",
            "expected_tool": "get_groundwater_level",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "year": yr, "season": season},
            "expected_value": ans.get("value"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 2: Stage of Extraction (%) - 15 questions
    # -------------------------------------------------------------
    soe_samples = [
        ("What is the stage of groundwater extraction in Jaipur in 2023?", "Jaipur", 2023),
        ("Stage of extraction percentage in Jaipur in 2022", "Jaipur", 2022),
        ("What is the stage of groundwater extraction in Pune in 2023?", "Pune", 2023),
        ("Groundwater extraction rate in Nagpur in 2023", "Nagpur", 2023),
        ("Stage of extraction in Nashik in 2023", "Nashik", 2023),
        ("What is the stage of extraction in Ludhiana in 2023?", "Ludhiana", 2023),
        ("Stage of extraction percentage in Amritsar in 2023", "Amritsar", 2023),
        ("Groundwater extraction percentage in Bengaluru Urban in 2023", "Bengaluru Urban", 2023),
        ("Extraction stage of Mysuru in 2023", "Mysuru", 2023),
        ("What is the stage of extraction in Varanasi in 2023?", "Varanasi", 2023),
        ("Stage of extraction in Agra in 2023", "Agra", 2023),
        ("What is the stage of extraction in Chennai in 2023?", "Chennai", 2023),
        # Misspelling
        ("Stage of extraction in Ludhiyana in 2023", "Ludhiyana", 2023),
        # Alias
        ("What is the stage of extraction in Banglore in 2023?", "Banglore", 2023),
        # Missing year
        ("What is the stage of extraction in Pune?", "Pune", None),
    ]

    for q_text, loc, yr in soe_samples:
        ans = get_stage_of_extraction(loc, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "stage_of_extraction",
            "expected_tool": "get_stage_of_extraction",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "year": yr},
            "expected_value": ans.get("value"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 3: Category Status - 15 questions
    # -------------------------------------------------------------
    cat_samples = [
        ("Is Jaipur over-exploited or safe in 2023?", "Jaipur", 2023),
        ("Groundwater category of Jaipur in 2022", "Jaipur", 2022),
        ("Is Pune safe or over-exploited?", "Pune", None),
        ("Category of Nagpur in 2023", "Nagpur", 2023),
        ("Is Ludhiana over-exploited in 2023?", "Ludhiana", 2023),
        ("Groundwater category status of Amritsar in 2023", "Amritsar", 2023),
        ("Is Varanasi safe or critical in 2023?", "Varanasi", 2023),
        ("Category of Agra in 2023", "Agra", 2023),
        ("Is Chennai over-exploited in 2023?", "Chennai", 2023),
        ("Category of Coimbatore in 2023", "Coimbatore", 2023),
        ("Is Ahmedabad critical or safe in 2023?", "Ahmedabad", 2023),
        ("Groundwater status of Hyderabad in 2023", "Hyderabad", 2023),
        # Misspelling
        ("Is Ahmdabad critical in 2023?", "Ahmdabad", 2023),
        # Alias
        ("Is Banaras safe or semi-critical in 2023?", "Banaras", 2023),
        # Block category
        ("Is Amber block safe or over-exploited?", "Amber", None),
    ]

    for q_text, loc, yr in cat_samples:
        ans = get_category(loc, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "category",
            "expected_tool": "get_category",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "year": yr},
            "expected_value": ans.get("value"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 4: Annual Recharge - 12 questions
    # -------------------------------------------------------------
    rech_samples = [
        ("What is the annual groundwater recharge in Pune in 2023?", "Pune", 2023),
        ("Annual extractable groundwater resource in Pune in 2022", "Pune", 2022),
        ("Annual recharge in Jaipur in 2023", "Jaipur", 2023),
        ("Recharge in Nagpur in 2023", "Nagpur", 2023),
        ("Annual groundwater recharge in Nashik in 2023", "Nashik", 2023),
        ("Annual extractable resource in Ludhiana in 2023", "Ludhiana", 2023),
        ("Recharge in Amritsar in 2023", "Amritsar", 2023),
        ("Annual recharge in Varanasi in 2023", "Varanasi", 2023),
        ("Extractable groundwater resource in Agra in 2023", "Agra", 2023),
        ("Annual recharge in Coimbatore in 2023", "Coimbatore", 2023),
        # Missing year
        ("How much groundwater is recharged annually in Pune?", "Pune", None),
        # Misspelling
        ("Annual recharge in Varansi in 2023?", "Varansi", 2023),
    ]

    for q_text, loc, yr in rech_samples:
        ans = get_recharge(loc, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "recharge",
            "expected_tool": "get_recharge",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "year": yr},
            "expected_value": ans.get("value"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 5: Extraction Usages - 12 questions
    # -------------------------------------------------------------
    ext_samples = [
        ("Total groundwater extraction in Jaipur in 2023", "Jaipur", 2023, "total"),
        ("Groundwater extracted for irrigation in Jaipur in 2023", "Jaipur", 2023, "irrigation"),
        ("Domestic groundwater extraction in Jaipur in 2023", "Jaipur", 2023, "domestic"),
        ("Total groundwater extraction in Pune in 2023", "Pune", 2023, "total"),
        ("Irrigation groundwater extraction in Pune in 2023", "Pune", 2023, "irrigation"),
        ("Domestic extraction in Pune in 2023", "Pune", 2023, "domestic"),
        ("Total extraction in Ludhiana in 2023", "Ludhiana", 2023, "total"),
        ("Irrigation extraction in Ludhiana in 2023", "Ludhiana", 2023, "irrigation"),
        ("Total extraction in Nagpur in 2023", "Nagpur", 2023, "total"),
        ("Total extraction in Varanasi in 2023", "Varanasi", 2023, "total"),
        # Missing year
        ("Total groundwater extraction in Jaipur", "Jaipur", None, "total"),
        # Misspelling
        ("Total extraction in Jaipru in 2023", "Jaipru", 2023, "total"),
    ]

    for q_text, loc, yr, usage in ext_samples:
        ans = get_extraction(loc, year=yr, usage=usage)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "extraction",
            "expected_tool": "get_extraction",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "year": yr, "usage": usage},
            "expected_value": ans.get("value"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 6: Compare Locations - 10 questions
    # -------------------------------------------------------------
    comp_samples = [
        ("Compare Pune and Nagpur in 2023", ["Pune", "Nagpur"], "stage_of_extraction", 2023),
        ("Compare groundwater extraction between Pune and Nagpur in 2023", ["Pune", "Nagpur"], "stage_of_extraction", 2023),
        ("Compare water level between Jaipur and Jodhpur in 2023", ["Jaipur", "Jodhpur"], "water_level", 2023),
        ("Compare recharge between Pune and Nashik in 2023", ["Pune", "Nashik"], "recharge", 2023),
        ("Compare Ludhiana and Amritsar extraction in 2023", ["Ludhiana", "Amritsar"], "extraction", 2023),
        ("Compare Varanasi and Agra in 2023", ["Varanasi", "Agra"], "stage_of_extraction", 2023),
        ("Compare Chennai and Coimbatore in 2023", ["Chennai", "Coimbatore"], "stage_of_extraction", 2023),
        ("Compare Pune and Nagpur", ["Pune", "Nagpur"], "stage_of_extraction", None),
        ("Compare Jaipur and Jodhpur", ["Jaipur", "Jodhpur"], "stage_of_extraction", None),
        ("Compare Ahmedabad and Hyderabad in 2023", ["Ahmedabad", "Hyderabad"], "stage_of_extraction", 2023),
    ]

    for q_text, locs, metric, yr in comp_samples:
        ans = compare_locations(locs, metric=metric, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "compare",
            "expected_tool": "compare_locations",
            "expected_params": {"locations": locs, "metric": metric, "year": yr},
            "expected_value": [item["value"] for item in ans.get("value", [])] if isinstance(ans.get("value"), list) else None,
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 7: Historical Trends - 8 questions
    # -------------------------------------------------------------
    trend_samples = [
        ("What is the historical trend of groundwater in Jaipur?", "Jaipur", "stage_of_extraction"),
        ("Groundwater trend in Jaipur", "Jaipur", "stage_of_extraction"),
        ("Historical trend for Pune groundwater", "Pune", "stage_of_extraction"),
        ("Trend of extraction in Ludhiana", "Ludhiana", "stage_of_extraction"),
        ("Historical water level trend in Jodhpur", "Jodhpur", "water_level"),
        ("Groundwater change over years in Ajmer", "Ajmer", "stage_of_extraction"),
        ("Historical trend in Nagpur", "Nagpur", "stage_of_extraction"),
        ("Groundwater trend in Varanasi over time", "Varanasi", "stage_of_extraction"),
    ]

    for q_text, loc, metric in trend_samples:
        ans = get_trend(loc, metric=metric)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "trend",
            "expected_tool": "get_trend",
            "expected_params": {"location": resolver.resolve(loc).canonical_name if resolver.resolve(loc) else loc, "metric": metric},
            "expected_value": ans.get("delta"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 8: Rank Locations - 8 questions
    # -------------------------------------------------------------
    rank_samples = [
        ("Rank Pune, Jaipur, Ludhiana by extraction", ["Pune", "Jaipur", "Ludhiana"], "stage_of_extraction", None),
        ("Rank Ludhiana, Amritsar, Pune by groundwater extraction in 2023", ["Ludhiana", "Amritsar", "Pune"], "stage_of_extraction", 2023),
        ("Rank Jaipur, Jodhpur, Pune", ["Jaipur", "Jodhpur", "Pune"], "stage_of_extraction", None),
        ("Rank Nagpur, Nashik, Pune by extraction", ["Nagpur", "Nashik", "Pune"], "stage_of_extraction", None),
        ("Top groundwater extraction between Jaipur and Pune", ["Jaipur", "Pune"], "stage_of_extraction", None),
        ("Rank Varanasi and Agra by extraction in 2023", ["Varanasi", "Agra"], "stage_of_extraction", 2023),
        ("Rank Chennai and Coimbatore in 2023", ["Chennai", "Coimbatore"], "stage_of_extraction", 2023),
        ("Rank Ahmedabad and Hyderabad by extraction", ["Ahmedabad", "Hyderabad"], "stage_of_extraction", None),
    ]

    for q_text, locs, metric, yr in rank_samples:
        ans = rank_locations(locs, metric=metric, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "rank",
            "expected_tool": "rank_locations",
            "expected_params": {"locations": locs, "metric": metric, "year": yr},
            "expected_value": [item["rank"] for item in ans.get("value", [])] if isinstance(ans.get("value"), list) else None,
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 9: List Blocks - 10 questions
    # -------------------------------------------------------------
    block_samples = [
        ("List all blocks in Jaipur in 2023", "Jaipur", None, 2023),
        ("Show all blocks in Jaipur", "Jaipur", None, None),
        ("List all over-exploited blocks in Jaipur in 2023", "Jaipur", "Over-Exploited", 2023),
        ("List over-exploited blocks in Jaipur", "Jaipur", "Over-Exploited", None),
        ("List all blocks in Pune", "Pune", None, None),
        ("List semi-critical blocks in Pune in 2023", "Pune", "Semi-Critical", 2023),
        ("List safe blocks in Pune", "Pune", "Safe", None),
        ("List all blocks in Ludhiana in 2023", "Ludhiana", None, 2023),
        ("List over-exploited blocks in Ludhiana", "Ludhiana", "Over-Exploited", None),
        ("Show all blocks in Varanasi in 2023", "Varanasi", None, 2023),
    ]

    for q_text, dist, cat, yr in block_samples:
        ans = list_blocks(dist, category=cat, year=yr)
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "list_blocks",
            "expected_tool": "list_blocks",
            "expected_params": {"district": dist, "category": cat, "year": yr},
            "expected_value": ans.get("total_count"),
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 10: Ambiguous Location Names - 5 questions
    # -------------------------------------------------------------
    ambig_samples = [
        "Groundwater status in Ban",                # Matches Bangalore North and Bangalore South
        "Water level in Nag",                       # Matches Nagpur and Nagpur Rural
        "Groundwater category in Bil",              # Partial match
        "Status of Bar",                            # Partial match
        "Water level in Kot",                       # Partial match
    ]
    for q_text in ambig_samples:
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "ambiguous",
            "expected_tool": None,  # Or ambiguity handling
            "expected_params": None,
            "expected_value": "ambiguous_or_clarification",
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 11: No-Data / Unmatched Entities - 6 questions
    # -------------------------------------------------------------
    no_data_samples = [
        "groundwater level in Atlantis12345 in 2023",
        "What is the extraction stage of Wakanda?",
        "Is ElDorado over-exploited or safe?",
        "Annual recharge in GothamCity in 2023",
        "Groundwater level in MiddleEarth in 2021",
        "Water table depth in Narnia in 2023",
    ]
    for q_text in no_data_samples:
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "no_data",
            "expected_tool": None,
            "expected_params": None,
            "expected_value": "data_not_available",
        })
        qid += 1

    # -------------------------------------------------------------
    # Category 12: Out-of-Scope Queries (Refusals) - 6 questions
    # -------------------------------------------------------------
    oos_samples = [
        "What is the capital of France?",
        "Can you write a poem about rain?",
        "Who is the current prime minister of India?",
        "What is the recipe for masala chai?",
        "How do I install python on windows?",
        "Who won the cricket world cup?",
    ]
    for q_text in oos_samples:
        questions.append({
            "id": f"Q{qid:03d}",
            "question": q_text,
            "query_type": "out_of_scope",
            "expected_tool": None,
            "expected_params": None,
            "expected_value": "refusal",
        })
        qid += 1

    return questions


if __name__ == "__main__":
    out_file = Path(__file__).resolve().parent / "test_questions.json"
    dataset = generate_golden_dataset()
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    print(f"Generated {len(dataset)} evaluation questions in {out_file}")
