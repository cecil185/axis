"""Tests for the multi-battle combat UI helpers (CEC-17).

The UI logic is split into pure helpers exposed by `src.game`:
- `battle_queue_label_text`: text for the sidebar counter; pluralised, blank when empty.
- `next_battle_button_rect` and `skip_all_battles_button_rect`: rect geometry
  inside the right-hand sidebar, stacked above the End Turn button.

These tests exercise the helpers without a live pygame display so they pass
under `make test-unit` (which excludes browser-based tests).
"""

import pygame
import pytest

from src.game import (
    BUTTON_HEIGHT,
    HEIGHT,
    SIDEBAR_PAD,
    SIDEBAR_RIGHT_WIDTH,
    battle_queue_label_text,
    end_turn_button_rect,
    next_battle_button_rect,
    right_sidebar_rect,
    skip_all_battles_button_rect,
)
from src.movement_phase import (
    move_unit,
    pending_battles,
    reset_movement_phase,
    skip_all_battles,
)
from src.units import init_game, set_units


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset pending battles and units before each test."""
    reset_movement_phase()
    init_game()
    yield
    reset_movement_phase()
    init_game()


# ---------------------------------------------------------------------------
# battle_queue_label_text
# ---------------------------------------------------------------------------


class TestBattleQueueLabelText:
    def test_empty_queue_returns_blank(self) -> None:
        """No pending battles: returns empty string."""
        assert battle_queue_label_text(0) == ""
        # When count omitted and queue empty, also blank.
        assert pending_battles() == []
        assert battle_queue_label_text() == ""

    def test_one_battle_singular(self) -> None:
        assert battle_queue_label_text(1) == "1 battle remaining"

    def test_multiple_battles_plural(self) -> None:
        assert battle_queue_label_text(2) == "2 battles remaining"
        assert battle_queue_label_text(7) == "7 battles remaining"

    def test_negative_count_is_blank(self) -> None:
        """Defensive: negative or zero counts both produce empty text."""
        assert battle_queue_label_text(-1) == ""

    def test_count_defaults_to_live_pending_battles(self) -> None:
        """When count is None, the label reflects len(pending_battles())."""
        # Queue two battles via move_unit
        set_units("japan", "Red", {"infantry": 2, "tanks": 0})
        set_units("minamitori", "Blue", {"infantry": 1, "tanks": 0})
        set_units("minamitori", "Red", {"infantry": 0, "tanks": 0})
        set_units("marianas", "Red", {"infantry": 2, "tanks": 0})
        set_units("micronesia", "Blue", {"infantry": 1, "tanks": 0})
        set_units("micronesia", "Red", {"infantry": 0, "tanks": 0})
        from src.territory import set_owner
        set_owner("japan", "Red")
        set_owner("minamitori", "Blue")
        set_owner("marianas", "Red")
        set_owner("micronesia", "Blue")

        move_unit("japan", "minamitori", "Red", "infantry", 1)
        move_unit("marianas", "micronesia", "Red", "infantry", 1)
        assert len(pending_battles()) == 2
        assert battle_queue_label_text() == "2 battles remaining"

        skip_all_battles("Red")
        assert battle_queue_label_text() == ""


# ---------------------------------------------------------------------------
# next_battle_button_rect / skip_all_battles_button_rect
# ---------------------------------------------------------------------------


class TestBattleButtonRects:
    def test_next_battle_button_uses_sidebar_width(self) -> None:
        rect = next_battle_button_rect()
        assert rect.width == SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD

    def test_skip_all_button_uses_sidebar_width(self) -> None:
        rect = skip_all_battles_button_rect()
        assert rect.width == SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD

    def test_buttons_have_standard_height(self) -> None:
        assert next_battle_button_rect().height == BUTTON_HEIGHT
        assert skip_all_battles_button_rect().height == BUTTON_HEIGHT

    def test_skip_all_sits_above_end_turn(self) -> None:
        """Skip All button is placed directly above End Turn (with a gap)."""
        end_btn = end_turn_button_rect()
        skip_btn = skip_all_battles_button_rect()
        assert skip_btn.bottom < end_btn.top
        assert skip_btn.right == end_btn.right
        assert skip_btn.left == end_btn.left

    def test_next_battle_sits_above_skip_all(self) -> None:
        """Next Battle button is placed directly above Skip All (with a gap)."""
        skip_btn = skip_all_battles_button_rect()
        next_btn = next_battle_button_rect()
        assert next_btn.bottom < skip_btn.top
        assert next_btn.right == skip_btn.right
        assert next_btn.left == skip_btn.left

    def test_buttons_inside_sidebar(self) -> None:
        """Both buttons sit inside the right sidebar horizontally."""
        sidebar = right_sidebar_rect()
        for rect in (next_battle_button_rect(), skip_all_battles_button_rect()):
            assert rect.left >= sidebar.left
            assert rect.right <= sidebar.right

    def test_buttons_within_window(self) -> None:
        """Buttons fit vertically within the window."""
        for rect in (next_battle_button_rect(), skip_all_battles_button_rect()):
            assert rect.top >= 0
            assert rect.bottom <= HEIGHT

    def test_explicit_sidebar_argument_is_respected(self) -> None:
        """Passing a custom sidebar rect shifts both buttons accordingly."""
        custom = pygame.Rect(100, 0, SIDEBAR_RIGHT_WIDTH, HEIGHT)
        skip_btn = skip_all_battles_button_rect(custom)
        next_btn = next_battle_button_rect(custom)
        assert skip_btn.left == 100 + SIDEBAR_PAD
        assert next_btn.left == 100 + SIDEBAR_PAD
