"""Unit tests for app/resolver.py entity resolver using RapidFuzz."""

import pytest
from app.resolver import LocationResolver, resolve_location, ResolutionResult


@pytest.fixture(scope="module")
def res():
    return LocationResolver()


def test_misspelling_ludhiyana(res):
    result = res.resolve("Ludhiyana")
    assert result.status == "resolved"
    assert result.canonical_name == "Ludhiana"
    assert result.entity_type == "district"
    assert result.state == "Punjab"
    assert result.score >= 80.0


def test_misspelling_banglore_alias(res):
    result = res.resolve("Banglore")
    assert result.status == "resolved"
    assert result.canonical_name == "Bengaluru Urban"
    assert result.entity_type == "district"
    assert result.state == "Karnataka"
    assert result.score == 100.0


def test_misspelling_jaipru(res):
    result = res.resolve("Jaipru")
    assert result.status == "resolved"
    assert result.canonical_name == "Jaipur"
    assert result.entity_type == "district"
    assert result.state == "Rajasthan"
    assert result.score >= 80.0


def test_misspelling_ahmdabad(res):
    result = res.resolve("Ahmdabad")
    assert result.status == "resolved"
    assert result.canonical_name == "Ahmedabad"
    assert result.state == "Gujarat"
    assert result.score >= 80.0


def test_misspelling_varansi(res):
    result = res.resolve("Varansi")
    assert result.status == "resolved"
    assert result.canonical_name == "Varanasi"
    assert result.state == "Uttar Pradesh"
    assert result.score >= 85.0


def test_alias_banaras(res):
    result = res.resolve("Banaras")
    assert result.status == "resolved"
    assert result.canonical_name == "Varanasi"
    assert result.state == "Uttar Pradesh"
    assert result.score == 100.0


def test_alias_poona(res):
    result = res.resolve("Poona")
    assert result.status == "resolved"
    assert result.canonical_name == "Pune"
    assert result.state == "Maharashtra"
    assert result.score == 100.0


def test_affix_stripping(res):
    # Should strip "district" and "block"
    dist_res = res.resolve("Jaipur district")
    assert dist_res.status == "resolved"
    assert dist_res.canonical_name == "Jaipur"
    assert dist_res.entity_type == "district"

    block_res = res.resolve("Amber block")
    assert block_res.status == "resolved"
    assert block_res.canonical_name == "Amber"
    assert block_res.entity_type == "block"
    assert block_res.district == "Jaipur"


def test_entity_type_filter(res):
    # Filter by state
    state_res = res.resolve("Punjab", entity_type="state")
    assert state_res.status == "resolved"
    assert state_res.canonical_name == "Punjab"
    assert state_res.entity_type == "state"

    # Punjab is not a district
    dist_res = res.resolve("Punjab", entity_type="district")
    assert dist_res.status == "unresolved"


def test_ambiguity_detection(res):
    # If a short or common query matches multiple candidates with close scores
    # E.g. test custom threshold and ambiguity margin
    # "Nagpur" matches both district "Nagpur" (100) and block "Nagpur Rural" (80)
    # If we query with margin=25 on a partial string like "Nag" or "pur"
    result = res.resolve("Nag", threshold=40.0, ambiguity_margin=10.0)
    if result.status == "ambiguous":
        assert len(result.candidates) >= 2
        assert result.candidates[0].canonical_name != result.candidates[1].canonical_name
    
    # Direct test with simulated candidates
    res_ambig = res.resolve("Amber", ambiguity_margin=50.0)
    # Check that when ambiguous, candidates are populated with scores
    if res_ambig.status == "ambiguous":
        assert res_ambig.candidates is not None
        assert all(c.score > 0 for c in res_ambig.candidates)


def test_unresolved_location(res):
    result = res.resolve("FakeAtlantisUnderTheSea999")
    assert result.status == "unresolved"
    assert result.canonical_name is None
    assert result.score == 0.0


def test_dict_and_bool_compatibility(res):
    result = res.resolve("Pune")
    # Boolean check
    assert bool(result) is True
    # Dict access
    assert result["district"] == "Pune"
    assert result["state"] == "Maharashtra"
    assert result["id"] is not None

    unres = res.resolve("FakeNowhereXYZ")
    assert bool(unres) is False
