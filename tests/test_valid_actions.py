"""Tests for valid actions API: valid_attack_targets() and can_skip()."""

from unittest.mock import patch

from src.state import TEAMS, current_team, end_turn
from src.territory import ALL_TERRITORY_IDS, owner, set_owner
from src.valid_actions import can_skip, valid_attack_targets

RED, BLUE = TEAMS[0], TEAMS[1]


def test_can_skip_always_true() -> None:
    assert can_skip() is True


def test_initial_valid_attack_targets_includes_border_enemies() -> None:
    """With adjacency, Red (first turn) can attack Blue territories adjacent to Red-held territories."""
    while current_team() != RED:
        end_turn()
    targets = valid_attack_targets()
    # Red borders Blue at e.g. papua_new_guinea–vanuatu, solomon–vanuatu/fiji, tuvalu–fiji
    assert len(targets) > 0, "Red should have at least one attackable Blue neighbor"
    assert "vanuatu" in targets or "fiji" in targets


def test_after_end_turn_blue_has_valid_attack_targets() -> None:
    """Blue's turn: can attack Red territories adjacent to Blue-held territories."""
    while current_team() != RED:
        end_turn()
    end_turn()
    assert current_team() == BLUE
    targets = valid_attack_targets()
    assert len(targets) > 0, "Blue should have at least one attackable Red neighbor"
    end_turn()


def test_with_mocked_neighbors_returns_adjacent_enemy_targets() -> None:
    """When neighbors exist, only enemy territories adjacent to current team are valid."""
    while current_team() != RED:
        end_turn()
    # Red owns first 15 (e.g. hawaii); Blue owns last 15 (e.g. tonga).
    # Mock: hawaii (Red) adjacent to tonga (Blue) -> Red can attack tonga.
    with patch("src.valid_actions.neighbors") as mock_neighbors:
        mock_neighbors.side_effect = lambda tid: ["tonga"] if tid == "hawaii" else []
        assert set(valid_attack_targets()) == {"tonga"}
        assert valid_attack_targets() == ["tonga"]


def test_no_valid_targets_when_current_team_owns_all() -> None:
    for tid in ALL_TERRITORY_IDS:
        set_owner(tid, RED)
    assert current_team() == RED
    assert valid_attack_targets() == []
    # Restore initial ownership (first 15 Red, last 15 Blue)
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, RED if i < 15 else BLUE)


def test_neutral_territories_not_in_valid_attack_targets() -> None:
    """Neutral territories should not appear as valid attack targets."""
    while current_team() != RED:
        end_turn()
    # Make a Blue territory adjacent to Red into Neutral
    # tuvalu is Blue and adjacent to kiribati (Red) in initial setup
    set_owner("tuvalu", "Neutral")
    try:
        targets = valid_attack_targets()
        assert "tuvalu" not in targets
    finally:
        set_owner("tuvalu", BLUE)
