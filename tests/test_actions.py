"""Tests for skip() and attack() (axis-48n)."""

from src.state import TEAMS, current_team
from src.actions import attack, set_combat_hook, skip

RED, BLUE = TEAMS[0], TEAMS[1]


def test_skip_flips_turn() -> None:
    before = current_team()
    skip()
    assert current_team() != before
    skip()  # restore


def test_attack_invalid_target_raises() -> None:
    # Red's turn, valid targets are B, C. A is invalid.
    while current_team() != RED:
        skip()
    try:
        attack("A")  # type: ignore[arg-type]
    except ValueError as e:
        assert "Invalid attack target" in str(e)
        assert "A" in str(e)
    else:
        raise AssertionError("expected ValueError")
    assert current_team() == RED  # turn unchanged


def test_attack_valid_calls_combat_hook_and_ends_turn() -> None:
    while current_team() != RED:
        skip()
    called_with: list[str] = []
    set_combat_hook(lambda tid: called_with.append(tid))
    try:
        attack("B")
        assert called_with == ["B"]
        assert current_team() == BLUE
    finally:
        set_combat_hook(None)
    skip()  # restore to Red for other tests
