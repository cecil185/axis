"""
Tests for the Non-Combat Movement (NCM) phase (CEC-14, axis-7kl).

ncm_move_unit(from_tid, to_tid, team, unit_type, count) -- reposition friendlies-only.
end_ncm_phase() -- finalise the NCM phase.
reset_ncm_phase() -- reset for a new turn.

Rules:
- NCM runs after the combat phase. Destinations MUST be friendly-owned.
- Units that already moved during combat movement may NOT move again in NCM.
- Each territory may move-from at most once per NCM phase.
- Moving more units than present, or zero/negative count, raises ValueError.
- Moving into an enemy or neutral territory raises ValueError (no battles in NCM).
"""

import pytest

from src.territory import TerritoryId, set_neutral
from src.units import units, set_units, init_game
from src.movement_phase import (
    move_unit as combat_move_unit,
    reset_movement_phase,
)
from src.ncm_phase import (
    ncm_move_unit,
    end_ncm_phase,
    reset_ncm_phase,
    current_ncm_phase,
    ncm_moved_from,
)


# ---------------------------------------------------------------------------
# Fixtures / helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_state():
    """Reset both movement and NCM phases plus unit stacks before/after each test."""
    reset_movement_phase()
    reset_ncm_phase()
    init_game()
    yield
    reset_movement_phase()
    reset_ncm_phase()
    init_game()


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


# ---------------------------------------------------------------------------
# Phase state
# ---------------------------------------------------------------------------

class TestPhaseState:
    def test_initial_phase_is_ncm(self) -> None:
        reset_ncm_phase()
        assert current_ncm_phase() == "ncm"

    def test_end_ncm_phase_transitions_to_ended(self) -> None:
        reset_ncm_phase()
        end_ncm_phase()
        assert current_ncm_phase() == "ended"

    def test_reset_ncm_phase_restores_ncm(self) -> None:
        end_ncm_phase()
        reset_ncm_phase()
        assert current_ncm_phase() == "ncm"


# ---------------------------------------------------------------------------
# ncm_move_unit: friendly territory (reposition)
# ---------------------------------------------------------------------------

class TestNcmMoveFriendly:
    def test_move_infantry_to_friendly_repositions(self) -> None:
        _setup(["japan", "minamitori"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert units("japan", "Red")["infantry"] == 1
        assert units("minamitori", "Red")["infantry"] == 3

    def test_move_tanks_to_friendly_repositions(self) -> None:
        _setup(["japan", "minamitori"], [])
        ncm_move_unit("japan", "minamitori", "Red", "tanks", 1)
        assert units("japan", "Red")["tanks"] == 0
        assert units("minamitori", "Red")["tanks"] == 2

    def test_move_partial_count(self) -> None:
        _setup(["japan", "minamitori"], [], red_counts={"infantry": 4, "tanks": 0})
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 2)
        assert units("japan", "Red")["infantry"] == 2
        assert units("minamitori", "Red")["infantry"] == 6

    def test_blue_can_perform_ncm_to_friendly(self) -> None:
        _setup([], ["rapa_nui", "pitcairn"])
        ncm_move_unit("rapa_nui", "pitcairn", "Blue", "infantry", 1)
        assert units("rapa_nui", "Blue")["infantry"] == 1
        assert units("pitcairn", "Blue")["infantry"] == 3


# ---------------------------------------------------------------------------
# ncm_move_unit: enemy and neutral territories rejected
# ---------------------------------------------------------------------------

class TestNcmRejectsHostile:
    def test_move_into_enemy_raises(self) -> None:
        _setup(["japan"], ["minamitori"])
        with pytest.raises(ValueError, match="not owned by team"):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)

    def test_move_into_neutral_raises(self) -> None:
        _setup(["japan", "minamitori"], [])
        # Make minamitori neutral (no units, neutral owner).
        set_neutral("minamitori")
        with pytest.raises(ValueError, match="not owned by team"):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)

    def test_enemy_destination_does_not_move_units(self) -> None:
        """Failed NCM move must not silently transfer units."""
        _setup(["japan"], ["minamitori"])
        with pytest.raises(ValueError):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        # Source units intact, no units leaked into enemy territory.
        assert units("japan", "Red")["infantry"] == 2
        assert units("minamitori", "Red")["infantry"] == 0


# ---------------------------------------------------------------------------
# ncm_move_unit: units that already moved in combat movement
# ---------------------------------------------------------------------------

class TestNcmExcludesAlreadyMoved:
    def test_territory_that_moved_in_combat_cannot_move_in_ncm(self) -> None:
        """A territory moved-from during combat movement may not move-from in NCM."""
        _setup(["japan", "minamitori", "marianas"], [])
        # Combat-move from japan -> minamitori (friendly hop, no battle).
        combat_move_unit("japan", "minamitori", "Red", "infantry", 1)
        # Now NCM: japan should be locked from further movement this turn.
        with pytest.raises(ValueError, match="combat movement"):
            ncm_move_unit("japan", "marianas", "Red", "infantry", 1)

    def test_territory_with_no_combat_move_can_ncm(self) -> None:
        _setup(["japan", "minamitori", "marianas"], [])
        # Combat-move only marianas, leave japan alone.
        combat_move_unit("marianas", "micronesia", "Red", "infantry", 1)
        # japan can still NCM to a friendly neighbour.
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert units("minamitori", "Red")["infantry"] == 3


# ---------------------------------------------------------------------------
# ncm_move_unit: once-per-territory restriction within NCM
# ---------------------------------------------------------------------------

class TestNcmOncePerTerritory:
    def test_moving_from_same_territory_twice_in_ncm_raises(self) -> None:
        _setup(["japan", "minamitori", "marianas"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        with pytest.raises(ValueError, match="already moved this NCM phase"):
            ncm_move_unit("japan", "marianas", "Red", "infantry", 1)

    def test_different_source_territories_in_ncm_are_independent(self) -> None:
        _setup(["japan", "marianas", "minamitori", "micronesia"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        ncm_move_unit("marianas", "micronesia", "Red", "infantry", 1)  # should not raise

    def test_ncm_moved_from_tracks_sources(self) -> None:
        _setup(["japan", "minamitori"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert "japan" in ncm_moved_from()
        assert "minamitori" not in ncm_moved_from()


# ---------------------------------------------------------------------------
# ncm_move_unit: insufficient units / bad counts
# ---------------------------------------------------------------------------

class TestNcmInsufficientUnits:
    def test_move_more_than_present_raises(self) -> None:
        _setup(["japan", "minamitori"], [], red_counts={"infantry": 1, "tanks": 0})
        with pytest.raises(ValueError, match="Not enough"):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", 5)

    def test_move_zero_units_raises(self) -> None:
        _setup(["japan", "minamitori"], [])
        with pytest.raises(ValueError, match="count must be"):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", 0)

    def test_move_negative_units_raises(self) -> None:
        _setup(["japan", "minamitori"], [])
        with pytest.raises(ValueError, match="count must be"):
            ncm_move_unit("japan", "minamitori", "Red", "infantry", -1)


# ---------------------------------------------------------------------------
# Reset / new turn
# ---------------------------------------------------------------------------

class TestNcmReset:
    def test_reset_clears_moved_from(self) -> None:
        _setup(["japan", "minamitori"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        assert "japan" in ncm_moved_from()
        reset_ncm_phase()
        assert ncm_moved_from() == set()

    def test_after_reset_territory_can_move_again(self) -> None:
        _setup(["japan", "minamitori", "marianas"], [])
        ncm_move_unit("japan", "minamitori", "Red", "infantry", 1)
        reset_ncm_phase()
        # Also reset combat movement so japan isn't locked from prior turn.
        reset_movement_phase()
        ncm_move_unit("japan", "marianas", "Red", "infantry", 1)  # should not raise


# ---------------------------------------------------------------------------
# Integration: full turn flow
# ---------------------------------------------------------------------------

class TestFullTurnFlow:
    def test_combat_then_ncm_then_reset(self) -> None:
        """Combat movement then NCM, both contribute, then reset for next turn."""
        _setup(["japan", "marianas", "minamitori", "micronesia"], [])
        # Combat movement: japan -> minamitori.
        combat_move_unit("japan", "minamitori", "Red", "infantry", 1)
        # NCM: marianas -> micronesia (japan is locked, marianas was untouched).
        ncm_move_unit("marianas", "micronesia", "Red", "infantry", 1)
        assert units("micronesia", "Red")["infantry"] == 3
        # End the turn — both phases reset.
        reset_movement_phase()
        reset_ncm_phase()
        # Next turn: japan free to move again.
        combat_move_unit("japan", "marianas", "Red", "infantry", 1)
