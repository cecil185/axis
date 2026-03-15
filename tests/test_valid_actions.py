"""Tests for valid actions API: valid_attack_targets() and can_skip()."""

from src.state import TEAMS, current_team, end_turn
from src.territory import set_owner
from src.valid_actions import can_skip, valid_attack_targets

RED, BLUE = TEAMS[0], TEAMS[1]


def test_can_skip_always_true() -> None:
    assert can_skip() is True


def test_initial_red_valid_attack_targets_are_b_and_c() -> None:
    # Red owns A and D; B and C are enemy and adjacent.
    assert current_team() == RED
    assert set(valid_attack_targets()) == {"B", "C"}
    assert valid_attack_targets() == ["B", "C"]  # sorted


def test_after_end_turn_blue_valid_attack_targets_are_a_and_d() -> None:
    end_turn()
    assert current_team() == BLUE
    assert set(valid_attack_targets()) == {"A", "D"}
    assert valid_attack_targets() == ["A", "D"]
    end_turn()  # restore Red for other tests that assume initial turn


def test_valid_attack_targets_only_enemy_adjacent() -> None:
    # Initial: Red can only attack B, C (both adjacent to A or D, both enemy).
    assert current_team() == RED
    targets = valid_attack_targets()
    for tid in targets:
        assert tid in ("B", "C")
    assert len(targets) == 2


def test_no_valid_targets_when_current_team_owns_all() -> None:
    # If current team owns every territory, there are no enemy adjacent.
    from src.territory import ALL_TERRITORY_IDS

    for tid in ALL_TERRITORY_IDS:
        set_owner(tid, RED)
    assert current_team() == RED
    assert valid_attack_targets() == []
    # Restore initial ownership for other tests
    set_owner("A", RED)
    set_owner("B", BLUE)
    set_owner("C", BLUE)
    set_owner("D", RED)
