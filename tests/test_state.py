"""Tests for turn state (current_team, end_turn)."""

from src.state import TEAMS, current_team, end_turn

RED, BLUE = TEAMS[0], TEAMS[1]


def test_red_moves_first() -> None:
    assert current_team() == RED


def test_end_turn_flips_to_blue() -> None:
    end_turn()
    assert current_team() == BLUE
    end_turn()  # restore to Red for other tests


def test_end_turn_alternates() -> None:
    # Assume we might be Red or Blue from prior tests; flip twice to verify alternation
    a = current_team()
    end_turn()
    b = current_team()
    end_turn()
    c = current_team()
    assert a != b
    assert b != c
    assert a == c
