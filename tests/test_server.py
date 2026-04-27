"""Tests for src/server.py: Flask endpoints."""

import json

import pytest
import src.state as _state
from src.economy import reset_balances
from src.serializer import serialize_state
from src.server import app
from src.territory import ALL_TERRITORY_IDS, is_neutral_start, set_neutral, set_owner
from src.units import init_game, set_units


@pytest.fixture(autouse=True)
def reset_game_state() -> None:
    init_game()
    reset_balances()
    _state._current_team = "Red"
    _state._turn = 1
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        if is_neutral_start(tid):
            set_neutral(tid)
        else:
            set_owner(tid, "Red" if i < 15 else "Blue")


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


def test_get_state_returns_200(client) -> None:
    resp = client.get("/state")
    assert resp.status_code == 200
    assert resp.content_type.startswith("application/json")


def test_get_state_body_matches_serializer(client) -> None:
    expected = serialize_state()
    resp = client.get("/state")
    body = json.loads(resp.data)
    assert body == expected


def test_get_root_returns_200_html(client) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.content_type


def test_get_root_serves_static_html(client) -> None:
    resp = client.get("/")
    assert b"<html" in resp.data.lower()


def test_reset_returns_200(client) -> None:
    resp = client.post("/action/reset")
    assert resp.status_code == 200
    body = json.loads(resp.data)
    assert body.get("status") == "ok"


def test_reset_restores_current_team_to_red(client) -> None:
    _state._current_team = "Blue"
    client.post("/action/reset")
    resp = client.get("/state")
    body = json.loads(resp.data)
    assert body["current_team"] == "Red"


def test_reset_restores_initial_ownership(client) -> None:
    set_owner(ALL_TERRITORY_IDS[0], "Blue")
    client.post("/action/reset")
    resp = client.get("/state")
    body = json.loads(resp.data)
    assert body["territories"][ALL_TERRITORY_IDS[0]]["owner"] == "Red"


def test_reset_restores_initial_units(client) -> None:
    set_units(ALL_TERRITORY_IDS[0], "Red", {"infantry": 99, "tanks": 99})
    client.post("/action/reset")
    resp = client.get("/state")
    body = json.loads(resp.data)
    unit_entry = body["territories"][ALL_TERRITORY_IDS[0]]["units"]["Red"]
    assert unit_entry["infantry"] == 2
    assert unit_entry["tanks"] == 1
