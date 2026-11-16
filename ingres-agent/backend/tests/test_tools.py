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
from app.models.schemas import (
    ToolResult,
    ToolError,
    CompareLocationsResult,
    TrendResult,
    RankLocationsResult,
    ListBlocksResult,
)


def test_get_groundwater_level_real_row():
    # Jaipur 2023 pre-monsoon is 34.2 mbgl
    res = get_groundwater_level("Jaipur", year=2023, season="pre_monsoon")
    validated = ToolResult(**res)
    assert validated.value == 34.2
    assert validated.unit == "mbgl"
    assert validated.year == 2023
    assert "Jaipur" in validated.location
    assert "INGRES" in validated.source


def test_get_groundwater_level_post_monsoon():
    # Jaipur 2023 post-monsoon is 32.1 mbgl
    res = get_groundwater_level("Jaipur", year=2023, season="post_monsoon")
    validated = ToolResult(**res)
    assert validated.value == 32.1
    assert validated.unit == "mbgl"


def test_get_groundwater_level_invalid():
    res = get_groundwater_level("NonExistentPlaceXYZ123")
    validated_err = ToolError(**res)
    assert validated_err.error == "data_not_available"


def test_get_stage_of_extraction_real_rows():
    # Jaipur is over-exploited (> 100%)
    res_jaipur = get_stage_of_extraction("Jaipur", year=2023)
    val_jaipur = ToolResult(**res_jaipur)
    assert val_jaipur.value == 202.9
    assert val_jaipur.unit == "%"
    assert val_jaipur.year == 2023

    # Pune is safe (< 70%)
    res_pune = get_stage_of_extraction("Pune", year=2023)
    val_pune = ToolResult(**res_pune)
    assert val_pune.value == 67.8
    assert val_pune.unit == "%"


def test_get_category_real_rows():
    # Safe category
    cat_pune = get_category("Pune", year=2023)
    val_pune = ToolResult(**cat_pune)
    assert val_pune.value == "Safe"
    assert val_pune.unit == "category"

    # Over-Exploited category
    cat_jaipur = get_category("Jaipur", year=2023)
    val_jaipur = ToolResult(**cat_jaipur)
    assert val_jaipur.value == "Over-Exploited"

    # Semi-Critical category
    cat_varanasi = get_category("Varanasi", year=2023)
    val_varanasi = ToolResult(**cat_varanasi)
    assert val_varanasi.value == "Semi-Critical"

    # Critical category
    cat_agra = get_category("Agra", year=2023)
    val_agra = ToolResult(**cat_agra)
    assert val_agra.value == "Critical"


def test_get_recharge_real_row():
    # Pune annual extractable resource is 145200.0 ham
    res = get_recharge("Pune", year=2023)
    validated = ToolResult(**res)
    assert validated.value == 145200.0
    assert validated.unit == "ham"
    assert validated.year == 2023


def test_get_extraction_usages():
    # Total extraction for Jaipur
    total = get_extraction("Jaipur", year=2023, usage="total")
    val_total = ToolResult(**total)
    assert val_total.value == 85420.0
    assert val_total.unit == "ham"

    # Irrigation extraction
    irr = get_extraction("Jaipur", year=2023, usage="irrigation")
    val_irr = ToolResult(**irr)
    assert val_irr.value == 72100.0

    # Domestic extraction
    dom = get_extraction("Jaipur", year=2023, usage="domestic")
    val_dom = ToolResult(**dom)
    assert val_dom.value == 13320.0


def test_compare_locations():
    res = compare_locations(["Pune", "Nagpur"], metric="stage_of_extraction", year=2023)
    validated = CompareLocationsResult(**res)
    assert len(validated.value) == 2
    assert validated.unit == "%"
    locations = [item["location"] for item in validated.value]
    assert any("Pune" in loc for loc in locations)
    assert any("Nagpur" in loc for loc in locations)


def test_get_trend_multi_year():
    # Jaipur water levels from 2021 to 2023: 32.8 -> 33.5 -> 34.2 mbgl (increasing depth)
    trend = get_trend("Jaipur", metric="water_level", start_year=2021, end_year=2023)
    validated = TrendResult(**trend)
    assert len(validated.value) == 3
    assert validated.value[0]["year"] == 2021
    assert validated.value[0]["value"] == 32.8
    assert validated.value[2]["year"] == 2023
    assert validated.value[2]["value"] == 34.2
    assert validated.direction == "increasing"
    assert validated.delta == 1.4


def test_rank_locations():
    # Rank Ludhiana (203.6%), Jaipur (202.9%), Pune (67.8%)
    ranked = rank_locations(["Pune", "Jaipur", "Ludhiana"], metric="stage_of_extraction", year=2023)
    validated = RankLocationsResult(**ranked)
    items = validated.value
    assert len(items) == 3
    assert items[0]["rank"] == 1
    assert "Ludhiana" in items[0]["location"]
    assert items[2]["rank"] == 3
    assert "Pune" in items[2]["location"]


def test_list_blocks_with_category_filter():
    # Jaipur blocks: Amber, Bassi, Chaksu, etc.
    res = list_blocks("Jaipur", year=2023)
    validated = ListBlocksResult(**res)
    assert validated.total_count >= 8
    block_names = [b["block"] for b in validated.value]
    assert "Amber" in block_names
    assert "Sanganer" in block_names

    # Pune blocks filtered by Semi-Critical (Haveli, Baramati, Shirur, Daund)
    res_semi = list_blocks("Pune", category="Semi-Critical", year=2023)
    val_semi = ListBlocksResult(**res_semi)
    semi_blocks = [b["block"] for b in val_semi.value]
    assert "Haveli" in semi_blocks
    assert "Baramati" in semi_blocks


def test_entity_resolution_alias_and_typo():
    # Common alias: "Bangalore" -> "Bengaluru Urban"
    res_bangalore = get_category("Bangalore", year=2023)
    val_bangalore = ToolResult(**res_bangalore)
    assert "Bengaluru Urban" in val_bangalore.location
    assert val_bangalore.value == "Over-Exploited"

    # Typo: "Jaipru" -> "Jaipur"
    res_typo = get_stage_of_extraction("Jaipru", year=2023)
    val_typo = ToolResult(**res_typo)
    assert "Jaipur" in val_typo.location
    assert val_typo.value == 202.9
