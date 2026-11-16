"""Unit tests for INGRES database tool functions using real rows from ingres.db."""

import pytest
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
from app.models.schemas import ToolResult, ToolError


def test_get_groundwater_level_real_row():
    # Jaipur 2023 pre-monsoon is 34.2 mbgl
    res = get_groundwater_level("Jaipur", year=2023, season="pre_monsoon")
    assert "error" not in res
    assert res["value"] == 34.2
    assert res["unit"] == "mbgl"
    assert res["year"] == 2023
    assert "Jaipur" in res["location"]
    assert "INGRES" in res["source"]


def test_get_groundwater_level_post_monsoon():
    # Jaipur 2023 post-monsoon is 32.1 mbgl
    res = get_groundwater_level("Jaipur", year=2023, season="post_monsoon")
    assert "error" not in res
    assert res["value"] == 32.1
    assert res["unit"] == "mbgl"


def test_get_groundwater_level_invalid():
    res = get_groundwater_level("NonExistentPlaceXYZ123")
    assert res == {"error": "data_not_available"}


def test_get_stage_of_extraction_real_rows():
    # Jaipur is over-exploited (> 100%)
    res_jaipur = get_stage_of_extraction("Jaipur", year=2023)
    assert "error" not in res_jaipur
    assert res_jaipur["value"] == 202.9
    assert res_jaipur["unit"] == "%"
    assert res_jaipur["year"] == 2023

    # Pune is safe (< 70%)
    res_pune = get_stage_of_extraction("Pune", year=2023)
    assert "error" not in res_pune
    assert res_pune["value"] == 67.8
    assert res_pune["unit"] == "%"


def test_get_category_real_rows():
    # Safe category
    cat_pune = get_category("Pune", year=2023)
    assert cat_pune["value"] == "Safe"
    assert cat_pune["unit"] == "category"

    # Over-Exploited category
    cat_jaipur = get_category("Jaipur", year=2023)
    assert cat_jaipur["value"] == "Over-Exploited"

    # Semi-Critical category
    cat_varanasi = get_category("Varanasi", year=2023)
    assert cat_varanasi["value"] == "Semi-Critical"

    # Critical category
    cat_agra = get_category("Agra", year=2023)
    assert cat_agra["value"] == "Critical"


def test_get_recharge_real_row():
    # Pune annual extractable resource is 145200.0 ham
    res = get_recharge("Pune", year=2023)
    assert "error" not in res
    assert res["value"] == 145200.0
    assert res["unit"] == "ham"
    assert res["year"] == 2023


def test_get_extraction_usages():
    # Total extraction for Jaipur
    total = get_extraction("Jaipur", year=2023, usage="total")
    assert total["value"] == 85420.0
    assert total["unit"] == "ham"

    # Irrigation extraction
    irr = get_extraction("Jaipur", year=2023, usage="irrigation")
    assert irr["value"] == 72100.0

    # Domestic extraction
    dom = get_extraction("Jaipur", year=2023, usage="domestic")
    assert dom["value"] == 13320.0


def test_compare_locations():
    res = compare_locations(["Pune", "Nagpur"], metric="stage_of_extraction", year=2023)
    assert "error" not in res
    assert len(res["value"]) == 2
    assert res["unit"] == "%"
    locations = [item["location"] for item in res["value"]]
    assert any("Pune" in loc for loc in locations)
    assert any("Nagpur" in loc for loc in locations)


def test_get_trend_multi_year():
    # Jaipur water levels from 2021 to 2023: 32.8 -> 33.5 -> 34.2 mbgl (increasing depth)
    trend = get_trend("Jaipur", metric="water_level", start_year=2021, end_year=2023)
    assert "error" not in trend
    assert len(trend["value"]) == 3
    assert trend["value"][0]["year"] == 2021
    assert trend["value"][0]["value"] == 32.8
    assert trend["value"][2]["year"] == 2023
    assert trend["value"][2]["value"] == 34.2
    assert trend["direction"] == "increasing"
    assert trend["delta"] == 1.4


def test_rank_locations():
    # Rank Ludhiana (203.6%), Jaipur (202.9%), Pune (67.8%)
    ranked = rank_locations(["Pune", "Jaipur", "Ludhiana"], metric="stage_of_extraction", year=2023)
    assert "error" not in ranked
    items = ranked["value"]
    assert len(items) == 3
    # Top rank should be Ludhiana or Jaipur (both > 200%)
    assert items[0]["rank"] == 1
    assert "Ludhiana" in items[0]["location"]
    # Lowest rank should be Pune
    assert items[2]["rank"] == 3
    assert "Pune" in items[2]["location"]


def test_list_blocks_with_category_filter():
    # Jaipur blocks: Amber, Bassi, Chaksu, etc.
    res = list_blocks("Jaipur", year=2023)
    assert "error" not in res
    assert res["total_count"] >= 8
    block_names = [b["block"] for b in res["value"]]
    assert "Amber" in block_names
    assert "Sanganer" in block_names

    # Pune blocks filtered by Semi-Critical (Haveli, Baramati, Shirur, Daund)
    res_semi = list_blocks("Pune", category="Semi-Critical", year=2023)
    assert "error" not in res_semi
    semi_blocks = [b["block"] for b in res_semi["value"]]
    assert "Haveli" in semi_blocks
    assert "Baramati" in semi_blocks


def test_entity_resolution_alias_and_typo():
    # Common alias: "Bangalore" -> "Bengaluru Urban"
    res_bangalore = get_category("Bangalore", year=2023)
    assert "error" not in res_bangalore
    assert "Bengaluru Urban" in res_bangalore["location"]
    assert res_bangalore["value"] == "Over-Exploited"

    # Typo: "Jaipru" -> "Jaipur"
    res_typo = get_stage_of_extraction("Jaipru", year=2023)
    assert "error" not in res_typo
    assert "Jaipur" in res_typo["location"]
    assert res_typo["value"] == 202.9
