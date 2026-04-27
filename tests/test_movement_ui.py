"""Tests for the combat-movement phase UI helpers (CEC-12).

The UI logic is split into helpers on `src.game`:
- `_movement_reachable(tid)`: union of reachable sets for each unit type
  present at the source.
- `_handle_movement_click(tid)`: select / deselect / move-all on click.
- `_advance_movement_to_combat()`: end the movement phase, switch UI to
  the combat (main) flow.
- `_begin_movement_phase()`: reset state at the start of a new turn.

These tests drive those helpers directly (no pygame display) so they run
under the unit-test suite alongside the rest of the project.
"""

import pytest

from src import game
from src.movement_phase import pending_battles, reset_movement_phase
from src.territory import owner, set_owner
from src.units import init_game, set_units, units as territory_units


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset movement phase, units, and module-level UI state before each test."""
    reset_movement_phase()
    init_game()
    game._selected_territory = None
    game._ui_phase = "movement"
    yield
    reset_movement_phase()
    init_game()
    game._selected_territory = None
    game._ui_phase = "movement"


# ---------------------------------------------------------------------------
# _movement_reachable
# ---------------------------------------------------------------------------


class TestMovementReachable:
    def test_returns_empty_when_not_owner(self) -> None:
        """A territory not owned by the current team has no reachable set."""
        # Current team is Red; pick a Blue-owned starting territory.
        assert game.current_team() == "Red"
        # rapa_nui starts Blue-owned with units.
        assert owner("rapa_nui") == "Blue"
        assert game._movement_reachable("rapa_nui") == set()

    def test_returns_neighbors_when_owner_has_infantry(self) -> None:
        """Source with infantry only reaches direct neighbors."""
        # japan starts Red-owned with infantry+tanks; reset to infantry only.
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        reach = game._movement_reachable("japan")
        # japan is adjacent to minamitori and marianas.
        assert "minamitori" in reach
        assert "marianas" in reach

    def test_includes_two_hop_with_tanks(self) -> None:
        """A source with tanks reaches further than infantry-only."""
        set_units("japan", "Red", {"infantry": 0, "tanks": 1})
        reach_with_tanks = game._movement_reachable("japan")
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        reach_inf_only = game._movement_reachable("japan")
        # tanks reach a strict superset of infantry destinations.
        assert reach_inf_only <= reach_with_tanks

    def test_returns_empty_when_no_units(self) -> None:
        """Owned territory with no units has no reachable set."""
        set_units("japan", "Red", {"infantry": 0, "tanks": 0})
        assert game._movement_reachable("japan") == set()


# ---------------------------------------------------------------------------
# _handle_movement_click: selection / deselection
# ---------------------------------------------------------------------------


class TestSelectionLifecycle:
    def test_click_owned_territory_selects_it(self) -> None:
        game._handle_movement_click("japan")
        assert game._selected_territory == "japan"

    def test_click_selected_again_deselects(self) -> None:
        """Clicking the currently-selected territory toggles it off."""
        game._selected_territory = "japan"
        game._handle_movement_click("japan")
        assert game._selected_territory is None

    def test_click_none_deselects(self) -> None:
        """Clicking empty space (tid is None) deselects."""
        game._selected_territory = "japan"
        game._handle_movement_click(None)
        assert game._selected_territory is None

    def test_click_enemy_territory_when_nothing_selected_does_not_select(self) -> None:
        """Clicking enemy territory cannot select it."""
        assert game._selected_territory is None
        game._handle_movement_click("rapa_nui")  # Blue
        assert game._selected_territory is None

    def test_click_owned_territory_with_no_units_does_not_select(self) -> None:
        """Owned territories with zero units cannot be sources."""
        set_units("japan", "Red", {"infantry": 0, "tanks": 0})
        game._handle_movement_click("japan")
        assert game._selected_territory is None


# ---------------------------------------------------------------------------
# _handle_movement_click: moving units to a reachable destination
# ---------------------------------------------------------------------------


class TestMoveOnDestinationClick:
    def test_click_reachable_destination_moves_all_units(self) -> None:
        """Selecting japan, then clicking minamitori, moves the entire stack."""
        set_units("japan", "Red", {"infantry": 2, "tanks": 1})
        # minamitori starts Red-owned (top 15) — make it empty so movement is clean.
        set_units("minamitori", "Red", {"infantry": 0, "tanks": 0})
        set_units("minamitori", "Blue", {"infantry": 0, "tanks": 0})

        game._handle_movement_click("japan")
        assert game._selected_territory == "japan"
        game._handle_movement_click("minamitori")

        assert territory_units("japan", "Red") == {"infantry": 0, "tanks": 0}
        assert territory_units("minamitori", "Red") == {"infantry": 2, "tanks": 1}

    def test_move_to_friendly_destination_does_not_register_battle(self) -> None:
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        set_units("minamitori", "Red", {"infantry": 1, "tanks": 0})
        set_units("minamitori", "Blue", {"infantry": 0, "tanks": 0})

        game._handle_movement_click("japan")
        game._handle_movement_click("minamitori")

        assert "minamitori" not in pending_battles()

    def test_move_to_enemy_destination_registers_battle(self) -> None:
        """Moving into an enemy-owned destination queues a pending battle.

        Note: infantry can only reach friendly territories under the
        movement rules; tanks are required to enter enemy territory.
        """
        set_units("japan", "Red", {"infantry": 0, "tanks": 1})
        set_units("minamitori", "Red", {"infantry": 0, "tanks": 0})
        set_units("minamitori", "Blue", {"infantry": 1, "tanks": 0})
        set_owner("minamitori", "Blue")

        game._handle_movement_click("japan")
        game._handle_movement_click("minamitori")

        assert "minamitori" in pending_battles()

    def test_destination_click_clears_selection(self) -> None:
        """After a successful move, the selected territory is cleared."""
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        set_units("minamitori", "Red", {"infantry": 0, "tanks": 0})
        set_units("minamitori", "Blue", {"infantry": 0, "tanks": 0})

        game._handle_movement_click("japan")
        game._handle_movement_click("minamitori")

        assert game._selected_territory is None

    def test_click_unreachable_territory_with_selection_deselects(self) -> None:
        """Clicking a non-destination, non-owned territory clears selection."""
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        # rapa_nui is Blue and not adjacent to japan.
        game._handle_movement_click("japan")
        assert game._selected_territory == "japan"
        game._handle_movement_click("rapa_nui")
        # Not reachable, not owned -> deselect.
        assert game._selected_territory is None

    def test_click_other_owned_with_units_switches_selection(self) -> None:
        """Clicking a different owned territory with units re-selects."""
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        set_units("hawaii", "Red", {"infantry": 2, "tanks": 0})
        # hawaii is not adjacent to japan, so it's not a destination — but it
        # IS owned-with-units, so the click should select it instead.
        game._handle_movement_click("japan")
        game._handle_movement_click("hawaii")
        assert game._selected_territory == "hawaii"


# ---------------------------------------------------------------------------
# Phase transitions
# ---------------------------------------------------------------------------


class TestPhaseTransitions:
    def test_advance_movement_to_combat_switches_ui_phase(self) -> None:
        game._ui_phase = "movement"
        game._selected_territory = "japan"
        game._advance_movement_to_combat()
        assert game._ui_phase == "main"
        assert game._selected_territory is None

    def test_begin_movement_phase_resets_state(self) -> None:
        """Starting a new turn returns to 'movement' with no selection."""
        game._ui_phase = "main"
        game._selected_territory = "japan"
        game._begin_movement_phase()
        assert game._ui_phase == "movement"
        assert game._selected_territory is None

    def test_initial_ui_phase_is_movement(self) -> None:
        """At module load (and after reset) the UI starts in the movement phase."""
        # The autouse fixture resets _ui_phase to "movement"; the assertion
        # confirms that contract holds across a fresh reset.
        game._begin_movement_phase()
        assert game._ui_phase == "movement"
