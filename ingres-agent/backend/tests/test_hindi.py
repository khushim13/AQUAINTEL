"""Unit and integration tests for Hindi translation and multilingual support."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.translator import (
    detect_language,
    translate_query_to_english,
    translate_answer_to_hindi,
)

client = TestClient(app)


def test_detect_language():
    assert detect_language("2023 में जयपुर में भूजल स्तर क्या था?") == "hi"
    assert detect_language("पुणे में भूजल की स्थिति") == "hi"
    assert detect_language("What is the groundwater level in Jaipur in 2023?") == "en"
    assert detect_language("Jaipur water level 2023") == "en"


def test_translate_query_to_english():
    hi_query = "2023 में जयपुर में भूजल स्तर क्या था?"
    eng = translate_query_to_english(hi_query)
    assert "Jaipur" in eng
    assert "2023" in eng
    assert "groundwater level" in eng


def test_translate_answer_preserves_numbers_and_places():
    answer_en = "The pre-monsoon groundwater level in Jaipur, Rajasthan for year 2023 was **34.2 mbgl**."
    data = {
        "value": 34.2,
        "unit": "mbgl",
        "year": 2023,
        "location": "Jaipur, Rajasthan",
        "source": "INGRES (ingres.iith.ac.in) / CGWB Open Data",
    }
    params = {"location": "Jaipur", "year": 2023, "season": "pre_monsoon"}

    hi_ans = translate_answer_to_hindi(answer_en, "get_groundwater_level", params, data)
    # Check that exact numbers and place names are preserved
    assert "34.2" in hi_ans
    assert "mbgl" in hi_ans
    assert "2023" in hi_ans
    assert "Jaipur, Rajasthan" in hi_ans
    assert "भूजल स्तर" in hi_ans


def test_chat_hindi_query_end_to_end():
    # Submit Hindi question
    response = client.post(
        "/api/chat",
        json={"message": "2023 में जयपुर में भूजल स्तर क्या था?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["detected_language"] == "hi"
    assert res["tool_called"] == "get_groundwater_level"
    assert res["data"]["value"] == 34.2
    assert res["data"]["unit"] == "mbgl"
    # Verify numbers & location in Hindi response
    assert "34.2 mbgl" in res["answer"]
    assert "Jaipur, Rajasthan" in res["answer"]
    assert "2023" in res["answer"]
    assert "भूजल स्तर" in res["answer"]


def test_chat_hindi_category_query():
    # Category query in Hindi
    response = client.post(
        "/api/chat",
        json={"message": "क्या पुणे सुरक्षित है या अत्यधिक दोहित?"},
    )
    assert response.status_code == 200
    res = response.json()
    assert res["detected_language"] == "hi"
    assert res["tool_called"] == "get_category"
    assert res["data"]["value"] == "Safe"
    assert "Pune, Maharashtra" in res["answer"]
    assert "सुरक्षित" in res["answer"]


def test_chat_english_input_with_hindi_language_toggle():
    # User types in English but has the Hindi UI toggle active
    response = client.post(
        "/api/chat",
        json={
            "message": "What is the stage of groundwater extraction in Pune?",
            "language": "hi",
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert res["response_language"] == "hi"
    assert res["tool_called"] == "get_stage_of_extraction"
    assert "67.8%" in res["answer"]
    assert "Pune, Maharashtra" in res["answer"]
    assert "दोहन" in res["answer"]
