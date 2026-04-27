"""Tests for src/serializer.py: serialize_state()."""

import src.state as _state
from src.economy import get_balance, reset_balances
from src.serializer import serialize_state
from src.territory import ALL_TERRITORY_IDS, is_neutral_start, owner, set_neutral, set_owner
from src.units import init_game


def setup_function() -> None:
    init_game()
    reset_balances()
    _state._current_team = "Red"
    _state._turn = 1
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        if is_neutral_start(tid):
            set_neutral(tid)
        else:
            set_owner(tid, "Red" if i < 15 else "Blue")


def test_serialize_state_has_territories() -> None:
    result = serialize_state()
    assert "territories" in result
    assert set(result["territories"].keys()) == set(ALL_TERRITORY_IDS)


def test_serialize_state_territory_has_owner() -> None:
    result = serialize_state()
    for tid in ALL_TERRITORY_IDS:
        assert "owner" in result["territories"][tid]
        assert result["territories"][tid]["owner"] == owner(tid)


def test_serialize_state_territory_has_units() -> None:
    result = serialize_state()
    for tid in ALL_TERRITORY_IDS:
        unit_entry = result["territories"][tid]["units"]
        assert "Red" in unit_entry
        assert "Blue" in unit_entry
        for team in ("Red", "Blue"):
            assert "infantry" in unit_entry[team]
            assert "tanks" in unit_entry[team]


def test_serialize_state_has_current_team() -> None:
    result = serialize_state()
    assert result["current_team"] == _state.current_team()


def test_serialize_state_has_balances() -> None:
    result = serialize_state()
    assert "balances" in result
    assert result["balances"]["Red"] == get_balance("Red")
    assert result["balances"]["Blue"] == get_balance("Blue")


def test_serialize_state_has_turn_number() -> None:
    result = serialize_state()
    assert "turn" in result
    assert isinstance(result["turn"], int)
