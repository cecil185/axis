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
    # Red's turn; with no adjacency valid_attack_targets() is [], so any attack is invalid.
    while current_team() != RED:
        skip()
    try:
        attack("hawaii")  # owned by Red, not a valid target
    except ValueError as e:
        assert "Invalid attack target" in str(e)
        assert "hawaii" in str(e)
    else:
        raise AssertionError("expected ValueError")
    assert current_team() == RED  # turn unchanged


def test_attack_valid_calls_combat_hook_and_ends_turn() -> None:
    from unittest.mock import patch

    while current_team() != RED:
        skip()
    called_with: list[str] = []
    set_combat_hook(lambda tid: called_with.append(tid))
    # With no adjacency, no valid targets; mock neighbors so tonga is attackable by Red.
    with patch("src.valid_actions.neighbors") as mock_n:
        mock_n.side_effect = lambda tid: ["tonga"] if tid == "hawaii" else []
        try:
            attack("tonga")
            assert called_with == ["tonga"]
            assert current_team() == BLUE
        finally:
            set_combat_hook(None)
    skip()  # restore to Red for other tests
