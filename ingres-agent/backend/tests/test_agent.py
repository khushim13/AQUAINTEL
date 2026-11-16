"""Integration tests for agent execution and POST /api/chat endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_groundwater_level():
    response = client.post(
        "/api/chat",
        json={"message": "What is the groundwater level in Jaipur in 2023?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "get_groundwater_level"
    assert res["data"] is not None
    assert res["data"]["value"] == 34.2
    assert res["data"]["unit"] == "mbgl"
    assert "34.2 mbgl" in res["answer"]
    assert "Jaipur" in res["answer"]
    assert "INGRES" in res["answer"]


def test_chat_default_latest_year_and_category():
    # When year is omitted, agent must default to 2023 and say so
    response = client.post(
        "/api/chat",
        json={"message": "Is Pune safe or over-exploited?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "get_category"
    assert res["data"]["value"] == "Safe"
    assert "Defaulting to the latest available assessment year (2023)" in res["answer"]
    assert "Safe" in res["answer"]


def test_chat_stage_of_extraction():
    response = client.post(
        "/api/chat",
        json={"message": "What is the stage of groundwater extraction in Ludhiana in 2023?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "get_stage_of_extraction"
    assert res["data"]["value"] == 203.6
    assert "203.6%" in res["answer"]


def test_chat_recharge_query():
    response = client.post(
        "/api/chat",
        json={"message": "What is the annual groundwater recharge in Pune in 2023?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "get_recharge"
    assert res["data"]["value"] == 145200.0
    assert "145,200.0 ham" in res["answer"]


def test_chat_compare_locations():
    response = client.post(
        "/api/chat",
        json={"message": "Compare Pune and Nagpur groundwater in 2023"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "compare_locations"
    assert len(res["data"]["value"]) == 2


def test_chat_list_blocks():
    response = client.post(
        "/api/chat",
        json={"message": "List all over-exploited blocks in Jaipur in 2023"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "list_blocks"
    assert "Amber" in res["answer"]
    assert "Sanganer" in res["answer"]


def test_chat_misspelling_normalization():
    # Misspelled "Jaipru" should resolve to Jaipur
    response = client.post(
        "/api/chat",
        json={"message": "water level in Jaipru in 2023"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["tool_called"] == "get_groundwater_level"
    assert res["params"]["location"] == "Jaipur"
    assert res["data"]["value"] == 34.2


def test_chat_missing_data():
    response = client.post(
        "/api/chat",
        json={"message": "groundwater level in Atlantis12345 in 2023"},
    )
    assert response.status_code == 200
    res = response.json()
    assert "data not available" in res["answer"].lower()
