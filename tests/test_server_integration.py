"""Live HTTP integration tests for the Flask server at http://localhost:5000.

These tests hit the real running server (not Flask test client) and verify
end-to-end HTTP behaviour for all three endpoints.

Run with the server already running:
    poetry run pytest tests/test_server_integration.py -v
"""

import pytest
import requests

BASE_URL = "http://localhost:5000"


@pytest.fixture(autouse=True)
def reset_server():
    """Reset server state before each test so each test starts clean."""
    resp = requests.post(f"{BASE_URL}/action/reset", timeout=5)
    assert resp.status_code == 200, f"Reset failed with status {resp.status_code}"
    yield


# ---------------------------------------------------------------------------
# GET /state
# ---------------------------------------------------------------------------

def test_get_state_returns_200():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    assert resp.status_code == 200


def test_get_state_content_type_is_json():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    assert "application/json" in resp.headers.get("Content-Type", "")


def test_get_state_has_29_territories():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert len(body["territories"]) == 29


def test_get_state_current_team_is_red_after_reset():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert body["current_team"] == "Red"


def test_get_state_turn_is_1_after_reset():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert body["turn"] == 1


def test_get_state_balances_has_red_and_blue_keys():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert "Red" in body["balances"]
    assert "Blue" in body["balances"]


def test_get_state_each_territory_has_owner_and_units():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    for tid, territory in body["territories"].items():
        assert "owner" in territory, f"Territory {tid} missing 'owner'"
        assert "units" in territory, f"Territory {tid} missing 'units'"


def test_get_state_each_territory_units_has_red_and_blue():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    for tid, territory in body["territories"].items():
        assert "Red" in territory["units"], f"Territory {tid} units missing 'Red'"
        assert "Blue" in territory["units"], f"Territory {tid} units missing 'Blue'"


def test_get_state_territory_owner_is_valid_team():
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    valid_owners = {"Red", "Blue", "Neutral"}
    for tid, territory in body["territories"].items():
        assert territory["owner"] in valid_owners, (
            f"Territory {tid} has unexpected owner: {territory['owner']!r}"
        )


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------

def test_get_root_returns_200():
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    assert resp.status_code == 200


def test_get_root_content_type_is_html():
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    assert "text/html" in resp.headers.get("Content-Type", "")


def test_get_root_body_contains_html_tag():
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    assert "<html" in resp.text.lower()


# ---------------------------------------------------------------------------
# POST /action/reset
# ---------------------------------------------------------------------------

def test_post_reset_returns_200():
    resp = requests.post(f"{BASE_URL}/action/reset", timeout=5)
    assert resp.status_code == 200


def test_post_reset_returns_status_ok():
    resp = requests.post(f"{BASE_URL}/action/reset", timeout=5)
    body = resp.json()
    assert body == {"status": "ok"}


def test_post_reset_content_type_is_json():
    resp = requests.post(f"{BASE_URL}/action/reset", timeout=5)
    assert "application/json" in resp.headers.get("Content-Type", "")


# ---------------------------------------------------------------------------
# POST /action/reset → GET /state: state is valid after reset
# ---------------------------------------------------------------------------

def test_state_after_reset_has_29_territories():
    requests.post(f"{BASE_URL}/action/reset", timeout=5)
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert len(body["territories"]) == 29


def test_state_after_reset_current_team_is_red():
    requests.post(f"{BASE_URL}/action/reset", timeout=5)
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert body["current_team"] == "Red"


def test_state_after_reset_turn_is_1():
    requests.post(f"{BASE_URL}/action/reset", timeout=5)
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert body["turn"] == 1


def test_state_after_reset_balances_present():
    requests.post(f"{BASE_URL}/action/reset", timeout=5)
    resp = requests.get(f"{BASE_URL}/state", timeout=5)
    body = resp.json()
    assert "Red" in body["balances"]
    assert "Blue" in body["balances"]
