"""
Integration tests for DFA Simulator Flask API endpoints.
=========================================================
Tests retained core endpoints:
- GET /
- GET /api/presets
- POST /api/validate (valid and invalid definitions)
- POST /api/simulate (accepted and rejected strings)
"""

import pytest
from app import app, PRESETS


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test that GET / returns 200 and serves the index.html page."""
    res = client.get("/")
    assert res.status_code == 200
    assert b"DFA Simulator" in res.data
    assert b"CSET302" in res.data


def test_api_presets(client):
    """Test that /api/presets returns the demonstration presets."""
    res = client.get("/api/presets")
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["success"] is True
    assert "ends_with_01" in json_data["presets"]
    assert "contains_101" in json_data["presets"]
    assert "even_zeros" in json_data["presets"]
    assert "divisible_by_3" in json_data["presets"]
    assert len(json_data["presets"]) == 6


def test_api_validate_valid(client):
    """Test /api/validate with a valid DFA definition."""
    dfa_data = PRESETS["ends_with_01"]
    res = client.post("/api/validate", json=dfa_data)
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert "dfa" in data


def test_api_validate_invalid(client):
    """Test /api/validate with invalid DFA (start state not in Q)."""
    invalid_data = {
        "states": ["q0"],
        "alphabet": ["0"],
        "start_state": "qGhost",
        "accepting_states": [],
        "transitions": {},
    }
    res = client.post("/api/validate", json=invalid_data)
    assert res.status_code == 400
    data = res.get_json()
    assert data["success"] is False
    assert "Start state 'qGhost' is not in the set of states" in data["error"]


def test_api_simulate_accepted(client):
    """Test /api/simulate with an accepted string."""
    dfa_data = PRESETS["ends_with_01"]
    res = client.post("/api/simulate", json={"dfa": dfa_data, "input_string": "1001"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["result"]["accepted"] is True
    assert data["result"]["final_state"] == "q2"


def test_api_simulate_rejected(client):
    """Test /api/simulate with a rejected string."""
    dfa_data = PRESETS["ends_with_01"]
    res = client.post("/api/simulate", json={"dfa": dfa_data, "input_string": "100"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["success"] is True
    assert data["result"]["accepted"] is False
    assert data["result"]["final_state"] == "q1"
