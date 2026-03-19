"""Tests for movement phase: move_unit, end_movement_phase, pending battles."""

import pytest

from src.movement_phase import (
    current_phase,
    end_movement_phase,
    move_unit,
    moved_stacks,
    pending_battles,
    reset_phase,
)
from src.state import current_team, end_turn
from src.territory import ALL_TERRITORY_IDS, neighbors, owner, set_owner
from src.units import init_game, set_units, units, total_units


def _reset() -> None:
    """Reset game state to defaults."""
    init_game()
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, "Red" if i < 15 else "Blue")
    reset_phase()
    # Ensure Red's turn
    while current_team() != "Red":
        end_turn()


class TestMoveUnit:
    """move_unit(from_tid, to_tid, team, unit_type, count) repositions units."""

    def setup_method(self) -> None:
        _reset()

    def test_move_infantry_to_friendly_neighbor(self) -> None:
        # japan has 2 infantry for Red; marianas is friendly neighbor
        before_from = units("japan", "Red")["infantry"]
        before_to = units("marianas", "Red")["infantry"]
        move_unit("japan", "marianas", "Red", "infantry", 1)
        assert units("japan", "Red")["infantry"] == before_from - 1
        assert units("marianas", "Red")["infantry"] == before_to + 1

    def test_move_tanks_to_friendly_neighbor(self) -> None:
        before_from = units("japan", "Red")["tanks"]
        before_to = units("marianas", "Red")["tanks"]
        move_unit("japan", "marianas", "Red", "tanks", 1)
        assert units("japan", "Red")["tanks"] == before_from - 1
        assert units("marianas", "Red")["tanks"] == before_to + 1

    def test_move_multiple_units(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 2)
        assert units("japan", "Red")["infantry"] == 0
        assert units("marianas", "Red")["infantry"] == 4  # 2 original + 2 moved

    def test_move_raises_if_not_enough_units(self) -> None:
        with pytest.raises(ValueError, match="Not enough"):
            move_unit("japan", "marianas", "Red", "infantry", 5)

    def test_move_raises_if_count_zero_or_negative(self) -> None:
        with pytest.raises(ValueError, match="count must be"):
            move_unit("japan", "marianas", "Red", "infantry", 0)
        with pytest.raises(ValueError, match="count must be"):
            move_unit("japan", "marianas", "Red", "infantry", -1)

    def test_move_raises_if_destination_not_reachable(self) -> None:
        # hawaii is not adjacent to japan
        with pytest.raises(ValueError, match="not reachable"):
            move_unit("japan", "hawaii", "Red", "infantry", 1)

    def test_move_raises_if_wrong_team(self) -> None:
        # Blue can't move Red's units
        with pytest.raises(ValueError, match="not reachable"):
            move_unit("japan", "marianas", "Blue", "infantry", 1)

    def test_move_raises_if_not_movement_phase(self) -> None:
        end_movement_phase()
        with pytest.raises(ValueError, match="not.*movement"):
            move_unit("japan", "marianas", "Red", "infantry", 1)


class TestMovedStacks:
    """Each unit stack may move at most once per phase."""

    def setup_method(self) -> None:
        _reset()

    def test_stack_can_move_once(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 1)
        assert ("japan", "infantry") in moved_stacks()

    def test_same_stack_cannot_move_twice(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 1)
        with pytest.raises(ValueError, match="already moved"):
            move_unit("japan", "marianas", "Red", "infantry", 1)

    def test_different_unit_type_same_territory_can_move(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 1)
        # Tanks from same territory should be independent
        move_unit("japan", "marianas", "Red", "tanks", 1)
        assert ("japan", "infantry") in moved_stacks()
        assert ("japan", "tanks") in moved_stacks()

    def test_moved_stacks_reset_after_phase(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 1)
        end_movement_phase()
        reset_phase()  # start new movement phase
        assert moved_stacks() == set()


class TestPendingBattles:
    """Moving into enemy territory registers a pending battle."""

    def setup_method(self) -> None:
        _reset()

    def test_move_into_enemy_registers_pending_battle(self) -> None:
        # tuvalu (index 14) is last Red territory; neighbors include tokelau (Blue, idx 19)
        # Actually let's use a concrete example: Red's nauru borders solomon
        # nauru is index 12 (Red); solomon is index 16 (Blue)
        # nauru neighbors: marshall, kiribati, solomon, papua_new_guinea
        assert owner("solomon") == "Blue"
        assert "solomon" in neighbors("nauru")
        # Tanks can reach enemy territory at 1 hop
        move_unit("nauru", "solomon", "Red", "tanks", 1)
        assert "solomon" in pending_battles()

    def test_move_into_friendly_no_pending_battle(self) -> None:
        move_unit("japan", "marianas", "Red", "infantry", 1)
        assert "marianas" not in pending_battles()

    def test_pending_battles_cleared_after_phase_reset(self) -> None:
        assert owner("solomon") == "Blue"
        move_unit("nauru", "solomon", "Red", "tanks", 1)
        assert "solomon" in pending_battles()
        end_movement_phase()
        reset_phase()
        assert pending_battles() == set()


class TestEndMovementPhase:
    """end_movement_phase() transitions from movement to combat phase."""

    def setup_method(self) -> None:
        _reset()

    def test_phase_starts_as_movement(self) -> None:
        assert current_phase() == "movement"

    def test_end_movement_transitions_to_combat(self) -> None:
        end_movement_phase()
        assert current_phase() == "combat"

    def test_end_movement_raises_if_already_combat(self) -> None:
        end_movement_phase()
        with pytest.raises(ValueError, match="not.*movement"):
            end_movement_phase()

    def test_reset_phase_returns_to_movement(self) -> None:
        end_movement_phase()
        reset_phase()
        assert current_phase() == "movement"
