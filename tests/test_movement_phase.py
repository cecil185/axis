"""
Tests for the Combat Movement phase (axis-2il).

move_unit(from_tid, to_tid, team, unit_type, count) -- reposition units.
end_movement_phase() -- advance turn from movement phase to combat phase.

Rules:
- Each turn begins in the MOVEMENT phase; the player may move any number of units.
- Each territory (stack) may be moved from at most once per phase.
- Moving into an enemy-owned territory registers it as a pending battle.
- Moving into a friendly territory simply repositions units (no battle queued).
- end_movement_phase() finalises movement and advances to the COMBAT phase.
- pending_battles() returns territories with pending battles (in insertion order).
- Attempting to move from the same territory twice in one phase raises ValueError.
- Attempting to move more units than are present raises ValueError.
- After end_movement_phase(), the pending battles list is cleared (ready for next turn).
"""

import pytest

from src.territory import TerritoryId, set_owner
from src.units import set_units, init_game
from src.movement_phase import (
    move_unit,
    end_movement_phase,
    pending_battles,
    reset_movement_phase,
    current_phase,
    PhaseState,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_state():
    """Reset movement phase and unit stacks before and after each test."""
    reset_movement_phase()
    init_game()
    yield
    reset_movement_phase()
    init_game()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _setup(
    red_territories: list[TerritoryId],
    blue_territories: list[TerritoryId],
    red_counts: dict | None = None,
    blue_counts: dict | None = None,
) -> None:
    """Set ownership and unit stacks for a subset of territories."""
    rc = red_counts or {"infantry": 2, "tanks": 1}
    bc = blue_counts or {"infantry": 2, "tanks": 1}
    for tid in red_territories:
        set_units(tid, "Red", rc)
        set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
    for tid in blue_territories:
        set_units(tid, "Blue", bc)
        set_units(tid, "Red", {"infantry": 0, "tanks": 0})


def _fresh() -> None:
    """Reset movement phase state (fixture handles init_game)."""
    reset_movement_phase()


# ---------------------------------------------------------------------------
# Phase state
# ---------------------------------------------------------------------------

class TestPhaseState:
    def test_initial_phase_is_movement(self) -> None:
        _fresh()
        assert current_phase() == "movement"

    def test_end_movement_phase_transitions_to_combat(self) -> None:
        _fresh()
        end_movement_phase()
        assert current_phase() == "combat"

    def test_reset_movement_phase_restores_movement(self) -> None:
        _fresh()
        end_movement_phase()
        reset_movement_phase()
        assert current_phase() == "movement"


# ---------------------------------------------------------------------------
# move_unit: friendly territory (reposition, no battle)
# ---------------------------------------------------------------------------

class TestMoveUnitFriendly:
    def test_move_infantry_to_friendly_territory_repositions_units(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [])
        # Move 1 infantry from japan to minamitori
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        from src.units import units
        # minamitori should have gained 1 infantry
        assert units("minamitori", "Red")["infantry"] == 3
        # japan should have lost 1 infantry
        assert units("japan", "Red")["infantry"] == 1

    def test_move_tanks_to_friendly_territory(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [])
        move_unit("japan", "minamitori", "Red", "tanks", 1)
        from src.units import units
        assert units("minamitori", "Red")["tanks"] == 2
        assert units("japan", "Red")["tanks"] == 0

    def test_move_to_friendly_does_not_add_pending_battle(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert "minamitori" not in pending_battles()

    def test_move_partial_count(self) -> None:
        """Moving fewer units than available leaves the rest in place."""
        _fresh()
        _setup(["japan", "minamitori"], [], red_counts={"infantry": 4, "tanks": 0})
        move_unit("japan", "minamitori", "Red", "infantry", 2)
        from src.units import units
        assert units("japan", "Red")["infantry"] == 2
        assert units("minamitori", "Red")["infantry"] == 6  # 4 already there + 2 moved

    def test_move_all_units_leaves_zero(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [], red_counts={"infantry": 2, "tanks": 0})
        move_unit("japan", "minamitori", "Red", "infantry", 2)
        from src.units import units
        assert units("japan", "Red")["infantry"] == 0


# ---------------------------------------------------------------------------
# move_unit: enemy territory (pending battle)
# ---------------------------------------------------------------------------

class TestMoveUnitEnemy:
    def test_move_into_enemy_registers_pending_battle(self) -> None:
        _fresh()
        _setup(["japan"], ["minamitori"])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert "minamitori" in pending_battles()

    def test_move_into_enemy_moves_units(self) -> None:
        """Units should actually be repositioned when attacking."""
        _fresh()
        _setup(["japan"], ["minamitori"])
        from src.units import units
        before = units("japan", "Red")["infantry"]
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert units("japan", "Red")["infantry"] == before - 1
        assert units("minamitori", "Red")["infantry"] == 1

    def test_multiple_attacks_register_multiple_pending_battles(self) -> None:
        """Moving into two different enemy territories registers both."""
        _fresh()
        # japan can only move to minamitori/marianas; use two different source territories
        _setup(["japan", "marianas"], ["minamitori", "micronesia"])
        # japan -> minamitori (enemy)
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        # marianas -> micronesia (enemy)
        move_unit("marianas", "micronesia", "Red", "infantry", 1)
        battles = pending_battles()
        assert "minamitori" in battles
        assert "micronesia" in battles

    def test_pending_battles_order_is_insertion_order(self) -> None:
        _fresh()
        _setup(["japan", "marianas"], ["minamitori", "micronesia"])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        move_unit("marianas", "micronesia", "Red", "infantry", 1)
        battles = pending_battles()
        assert battles.index("minamitori") < battles.index("micronesia")


# ---------------------------------------------------------------------------
# move_unit: once-per-territory restriction
# ---------------------------------------------------------------------------

class TestOncePerTerritory:
    def test_moving_from_same_territory_twice_raises(self) -> None:
        _fresh()
        _setup(["japan", "minamitori", "marianas"], [])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        with pytest.raises(ValueError, match="already moved"):
            move_unit("japan", "marianas", "Red", "infantry", 1)

    def test_different_source_territories_are_independent(self) -> None:
        """Moving from two different territories in the same phase is valid."""
        _fresh()
        _setup(["japan", "marianas", "minamitori", "micronesia"], [])
        # japan -> minamitori, marianas -> micronesia (both friendly moves)
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        move_unit("marianas", "micronesia", "Red", "infantry", 1)  # should not raise


# ---------------------------------------------------------------------------
# move_unit: insufficient units
# ---------------------------------------------------------------------------

class TestInsufficientUnits:
    def test_move_more_infantry_than_present_raises(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [], red_counts={"infantry": 1, "tanks": 0})
        with pytest.raises(ValueError, match="Not enough"):
            move_unit("japan", "minamitori", "Red", "infantry", 5)

    def test_move_zero_units_raises(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [])
        with pytest.raises(ValueError, match="count must be"):
            move_unit("japan", "minamitori", "Red", "infantry", 0)

    def test_move_negative_units_raises(self) -> None:
        _fresh()
        _setup(["japan", "minamitori"], [])
        with pytest.raises(ValueError, match="count must be"):
            move_unit("japan", "minamitori", "Red", "infantry", -1)


# ---------------------------------------------------------------------------
# end_movement_phase
# ---------------------------------------------------------------------------

class TestEndMovementPhase:
    def test_end_movement_phase_advances_to_combat(self) -> None:
        _fresh()
        end_movement_phase()
        assert current_phase() == "combat"

    def test_end_movement_phase_clears_moved_from_set(self) -> None:
        """After end_movement_phase + reset, territory can be moved from again."""
        _fresh()
        _setup(["japan", "minamitori", "marianas"], [])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        end_movement_phase()
        reset_movement_phase()
        # japan should be moveable again
        move_unit("japan", "marianas", "Red", "infantry", 1)  # should not raise

    def test_end_movement_phase_clears_pending_battles(self) -> None:
        _fresh()
        _setup(["japan"], ["minamitori"])
        move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert len(pending_battles()) == 1
        end_movement_phase()
        reset_movement_phase()
        assert pending_battles() == []

    def test_end_movement_phase_with_no_moves_is_valid(self) -> None:
        """Player may end movement phase without moving any units."""
        _fresh()
        end_movement_phase()  # should not raise
        assert current_phase() == "combat"


# ---------------------------------------------------------------------------
# Blue team
# ---------------------------------------------------------------------------

class TestBlueTeamMovement:
    def test_blue_can_move_to_friendly_territory(self) -> None:
        _fresh()
        _setup([], ["rapa_nui", "french_polynesia"])
        move_unit("rapa_nui", "french_polynesia", "Blue", "infantry", 1)
        from src.units import units
        assert units("rapa_nui", "Blue")["infantry"] == 1
        assert units("french_polynesia", "Blue")["infantry"] == 3

    def test_blue_attack_registers_pending_battle(self) -> None:
        _fresh()
        _setup(["rapa_nui"], ["french_polynesia", "pitcairn"])
        move_unit("pitcairn", "rapa_nui", "Blue", "infantry", 1)
        assert "rapa_nui" in pending_battles()


# ---------------------------------------------------------------------------
# Claiming neutral territories (CEC-15 / axis-cx5)
# ---------------------------------------------------------------------------

class TestClaimNeutralOnMove:
    def test_red_moving_into_neutral_claims_it(self) -> None:
        """Moving into a Neutral territory transfers ownership to the moving team."""
        _fresh()
        # marshall (Red, adjacency includes nauru which is a Neutral start).
        from src.territory import owner as territory_owner
        from src.units import init_game as reset_units
        reset_units()  # ensure nauru is Neutral
        assert territory_owner("nauru") == "Neutral"
        move_unit("marshall", "nauru", "Red", "infantry", 1)
        assert territory_owner("nauru") == "Red"

    def test_blue_moving_into_neutral_claims_it(self) -> None:
        _fresh()
        from src.territory import owner as territory_owner
        from src.units import init_game as reset_units
        reset_units()
        assert territory_owner("pitcairn") == "Neutral"
        # french_polynesia is Blue and adjacent to pitcairn (Neutral).
        move_unit("french_polynesia", "pitcairn", "Blue", "infantry", 1)
        assert territory_owner("pitcairn") == "Blue"

    def test_claiming_neutral_does_not_register_pending_battle(self) -> None:
        """Claiming is silent — no battle queued for combat phase."""
        _fresh()
        from src.units import init_game as reset_units
        reset_units()
        move_unit("marshall", "nauru", "Red", "infantry", 1)
        assert "nauru" not in pending_battles()

    def test_claiming_neutral_moves_units(self) -> None:
        """The moved unit stack lands in the claimed territory."""
        _fresh()
        from src.units import init_game as reset_units, units
        reset_units()
        move_unit("marshall", "nauru", "Red", "infantry", 2)
        assert units("nauru", "Red")["infantry"] == 2
