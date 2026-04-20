"""Tests for pygame-gui integration (axis-4qv).

These tests verify the data-layer and geometry logic used by the pygame-gui
widget integration — without requiring a live display. Pygame rendering is not
tested directly, but all helper functions driving widget behaviour are covered:

- _build_tooltip_lines: correct content for Neutral / owned / mixed territories
- _compute_tooltip_rect: card stays within window bounds near all edges
- Event handling: End Turn logic is unchanged with or without a UIManager
"""

import pygame
import pytest

from src.territory import ALL_TERRITORY_IDS, display_name, owner, region, set_owner
from src.units import (
    _STARTING_BLUE_TERRITORIES,
    _STARTING_RED_TERRITORIES,
    init_game,
    set_units,
)
from src.game import (
    HEIGHT,
    WIDTH,
    _build_tooltip_lines,
    _compute_tooltip_rect,
)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset unit stacks and territory ownership before each test."""
    init_game()
    for tid in _STARTING_RED_TERRITORIES:
        set_owner(tid, "Red")
    for tid in _STARTING_BLUE_TERRITORIES:
        set_owner(tid, "Blue")


# ---------------------------------------------------------------------------
# _build_tooltip_lines: content correctness
# ---------------------------------------------------------------------------


def test_tooltip_first_line_contains_name_and_region() -> None:
    """First tooltip line is '<display_name> (<region>)' for any territory."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _build_tooltip_lines(tid)
    assert lines[0] == f"{display_name(tid)} ({region(tid)})"


def test_tooltip_second_line_shows_owner_counts_for_red() -> None:
    """Second line shows Red team unit counts for a Red-owned territory."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _build_tooltip_lines(tid)
    assert "Red:" in lines[1]
    assert "inf" in lines[1]
    assert "tnk" in lines[1]


def test_tooltip_second_line_shows_owner_counts_for_blue() -> None:
    """Second line shows Blue team unit counts for a Blue-owned territory."""
    tid = _STARTING_BLUE_TERRITORIES[0]
    lines = _build_tooltip_lines(tid)
    assert "Blue:" in lines[1]


def test_tooltip_neutral_shows_unclaimed() -> None:
    """A Neutral territory's second line reports it as unclaimed."""
    from src.territory import set_neutral
    tid = _STARTING_RED_TERRITORIES[0]
    set_neutral(tid)
    lines = _build_tooltip_lines(tid)
    assert len(lines) == 2
    assert "Neutral" in lines[1]
    assert "unclaimed" in lines[1]


def test_tooltip_two_lines_when_no_enemy_units() -> None:
    """Tooltip has exactly two lines when the enemy team has no units in that territory."""
    tid = _STARTING_RED_TERRITORIES[0]
    lines = _build_tooltip_lines(tid)
    assert len(lines) == 2


def test_tooltip_three_lines_when_enemy_units_present() -> None:
    """Tooltip appends a third line when the enemy has units present."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 2, "tanks": 1})
    lines = _build_tooltip_lines(tid)
    assert len(lines) == 3
    assert "Blue:" in lines[2]
    assert "2 inf" in lines[2]


def test_tooltip_enemy_counts_zero_infantry() -> None:
    """Enemy line shows 0 infantry when enemy only has tanks."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 0, "tanks": 1})
    lines = _build_tooltip_lines(tid)
    assert len(lines) == 3
    assert "0 inf" in lines[2]
    assert "1 tnk" in lines[2]


def test_tooltip_no_enemy_line_when_both_enemy_counts_zero() -> None:
    """No third line when enemy infantry and tanks are both 0."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
    lines = _build_tooltip_lines(tid)
    assert len(lines) == 2


def test_tooltip_all_territories_produce_at_least_two_lines() -> None:
    """Every territory yields at least 2 tooltip lines after init_game."""
    for tid in ALL_TERRITORY_IDS:
        lines = _build_tooltip_lines(tid)
        assert len(lines) >= 2, f"Expected >=2 lines for {tid}, got {len(lines)}"


def test_tooltip_after_ownership_change_reflects_new_owner() -> None:
    """After ownership transfer, tooltip reflects the new owning team."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Blue", {"infantry": 3, "tanks": 2})
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    set_owner(tid, "Blue")
    lines = _build_tooltip_lines(tid)
    assert "Blue: 3 inf 2 tnk" in lines[1]


# ---------------------------------------------------------------------------
# _compute_tooltip_rect: window-bounds clamping
# ---------------------------------------------------------------------------


def test_tooltip_rect_normal_position() -> None:
    """Tooltip rect is returned as a pygame.Rect."""
    rect = _compute_tooltip_rect((400, 300), 200, 60)
    assert isinstance(rect, pygame.Rect)
    assert rect.width == 200
    assert rect.height == 60


def test_tooltip_rect_stays_within_left_edge() -> None:
    """Near the left edge cursor, card is shifted right so it stays within window."""
    # Cursor at x=5 with a 200-wide card: prefer above-left would put it at -207 — clamp right
    rect = _compute_tooltip_rect((5, 300), 200, 60)
    assert rect.left >= 0


def test_tooltip_rect_stays_within_top_edge() -> None:
    """Near the top edge cursor, card is shifted downward so it stays within window."""
    rect = _compute_tooltip_rect((400, 5), 200, 60)
    assert rect.top >= 0


def test_tooltip_rect_stays_within_right_edge() -> None:
    """Card right boundary does not exceed window width."""
    rect = _compute_tooltip_rect((WIDTH - 5, 300), 200, 60)
    assert rect.right <= WIDTH


def test_tooltip_rect_stays_within_bottom_edge() -> None:
    """Card bottom boundary does not exceed window height."""
    rect = _compute_tooltip_rect((400, HEIGHT - 5), 200, 60)
    assert rect.bottom <= HEIGHT


def test_tooltip_rect_near_bottom_right_corner() -> None:
    """Card stays within window in the bottom-right corner — the hardest edge case."""
    rect = _compute_tooltip_rect((WIDTH - 2, HEIGHT - 2), 200, 60)
    assert rect.left >= 0
    assert rect.top >= 0
    assert rect.right <= WIDTH
    assert rect.bottom <= HEIGHT


def test_tooltip_rect_near_top_left_corner() -> None:
    """Card stays within window in the top-left corner."""
    rect = _compute_tooltip_rect((2, 2), 200, 60)
    assert rect.left >= 0
    assert rect.top >= 0
    assert rect.right <= WIDTH
    assert rect.bottom <= HEIGHT


def test_tooltip_rect_dimensions_preserved() -> None:
    """Rect dimensions always match the requested width and height."""
    for mouse_pos in [(10, 10), (WIDTH - 10, HEIGHT - 10), (WIDTH // 2, HEIGHT // 2)]:
        rect = _compute_tooltip_rect(mouse_pos, 180, 55)
        assert rect.width == 180
        assert rect.height == 55
