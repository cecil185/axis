"""Tests for per-territory unit stacks, unit types, and game start (axis-dro, axis-kp2)."""

import pytest

from src.units import (
    get_unit_stats,
    init_game,
    owner_from_units,
    set_units,
    total_units,
    unit_types,
    units,
    _STARTING_COUNTS,
    _STARTING_RED_TERRITORIES,
    _STARTING_BLUE_TERRITORIES,
)
from src.territory import ALL_TERRITORY_IDS, owner


@pytest.fixture(autouse=True)
def reset_stacks() -> None:
    """Re-initialize unit stacks before each test to ensure a clean state."""
    init_game()


# --- Unit types ---


def test_unit_types_returns_infantry_and_tanks() -> None:
    assert set(unit_types()) == {"infantry", "tanks"}


def test_get_unit_stats_infantry() -> None:
    stats = get_unit_stats("infantry")
    assert stats["health"] == 1
    assert stats["defense"] == 2
    assert stats["attack"] == 0


def test_get_unit_stats_tanks() -> None:
    stats = get_unit_stats("tanks")
    assert stats["health"] == 2
    assert stats["defense"] == 1
    assert stats["attack"] == 1


def test_get_unit_stats_returns_copy() -> None:
    """Mutating returned stats does not affect source."""
    stats = get_unit_stats("infantry")
    stats["health"] = 999
    assert get_unit_stats("infantry")["health"] == 1


# --- Per-territory unit stacks ---


def test_units_returns_counts_for_team() -> None:
    # After init_game, Red has units in first 15 territories
    tid = _STARTING_RED_TERRITORIES[0]
    red_units = units(tid, "Red")
    assert red_units["infantry"] == _STARTING_COUNTS["infantry"]
    assert red_units["tanks"] == _STARTING_COUNTS["tanks"]


def test_units_blue_zero_in_red_territories() -> None:
    tid = _STARTING_RED_TERRITORIES[0]
    blue_units = units(tid, "Blue")
    assert blue_units["infantry"] == 0
    assert blue_units["tanks"] == 0


def test_set_units_updates_counts() -> None:
    tid = "hawaii"
    orig = units(tid, "Red")
    try:
        set_units(tid, "Red", {"infantry": 5, "tanks": 3})
        assert units(tid, "Red") == {"infantry": 5, "tanks": 3}
    finally:
        set_units(tid, "Red", orig)


def test_set_units_returns_copy_not_reference() -> None:
    """units() returns a copy; modifying it doesn't change internal state."""
    tid = "hawaii"
    orig = units(tid, "Red")
    try:
        set_units(tid, "Red", {"infantry": 2, "tanks": 1})
        fetched = units(tid, "Red")
        fetched["infantry"] = 999
        assert units(tid, "Red")["infantry"] == 2
    finally:
        set_units(tid, "Red", orig)


def test_total_units_sums_all_unit_types() -> None:
    tid = _STARTING_RED_TERRITORIES[0]
    # init_game sets 2 inf + 1 tank = 3 total
    assert total_units(tid, "Red") == 3
    assert total_units(tid, "Blue") == 0


# --- owner_from_units ---


def test_owner_from_units_red_has_more() -> None:
    tid = "hawaii"
    orig_red = units(tid, "Red")
    orig_blue = units(tid, "Blue")
    try:
        set_units(tid, "Red", {"infantry": 2, "tanks": 0})
        set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
        assert owner_from_units(tid) == "Red"
    finally:
        set_units(tid, "Red", orig_red)
        set_units(tid, "Blue", orig_blue)


def test_owner_from_units_blue_has_more() -> None:
    tid = "hawaii"
    orig_red = units(tid, "Red")
    orig_blue = units(tid, "Blue")
    try:
        set_units(tid, "Red", {"infantry": 0, "tanks": 0})
        set_units(tid, "Blue", {"infantry": 3, "tanks": 1})
        assert owner_from_units(tid) == "Blue"
    finally:
        set_units(tid, "Red", orig_red)
        set_units(tid, "Blue", orig_blue)


def test_owner_from_units_returns_none_when_equal() -> None:
    tid = "hawaii"
    orig_red = units(tid, "Red")
    orig_blue = units(tid, "Blue")
    try:
        set_units(tid, "Red", {"infantry": 0, "tanks": 0})
        set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
        assert owner_from_units(tid) is None
    finally:
        set_units(tid, "Red", orig_red)
        set_units(tid, "Blue", orig_blue)


# --- Game start (init_game) ---


def test_init_game_red_territories_have_correct_stacks() -> None:
    for tid in _STARTING_RED_TERRITORIES:
        red_stack = units(tid, "Red")
        assert red_stack["infantry"] == 2
        assert red_stack["tanks"] == 1
        blue_stack = units(tid, "Blue")
        assert blue_stack["infantry"] == 0
        assert blue_stack["tanks"] == 0


def test_init_game_blue_territories_have_correct_stacks() -> None:
    for tid in _STARTING_BLUE_TERRITORIES:
        blue_stack = units(tid, "Blue")
        assert blue_stack["infantry"] == 2
        assert blue_stack["tanks"] == 1
        red_stack = units(tid, "Red")
        assert red_stack["infantry"] == 0
        assert red_stack["tanks"] == 0


def test_owner_from_units_matches_territory_owner_after_init() -> None:
    """After init_game, territory.owner() should match owner_from_units() for all territories."""
    for tid in _STARTING_RED_TERRITORIES:
        assert owner(tid) == "Red", f"{tid} should be Red"
    for tid in _STARTING_BLUE_TERRITORIES:
        assert owner(tid) == "Blue", f"{tid} should be Blue"


def test_two_territories_per_team_with_same_counts() -> None:
    """Both teams have the same unit counts in their starting territories."""
    red_stacks = [units(tid, "Red") for tid in _STARTING_RED_TERRITORIES]
    blue_stacks = [units(tid, "Blue") for tid in _STARTING_BLUE_TERRITORIES]
    # All starting stacks for Red should be identical
    assert all(s == red_stacks[0] for s in red_stacks)
    # All starting stacks for Blue should be identical
    assert all(s == blue_stacks[0] for s in blue_stacks)
    # Both teams get the same starting counts
    assert red_stacks[0] == blue_stacks[0]
