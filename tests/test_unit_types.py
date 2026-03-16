"""Tests for unit types (infantry, tanks) and get_unit_stats."""

import pytest

from src.unit_types import ALL_UNIT_TYPE_IDS, get_unit_stats


def test_all_unit_type_ids() -> None:
    """ALL_UNIT_TYPE_IDS contains infantry and tanks."""
    assert ALL_UNIT_TYPE_IDS == ("infantry", "tanks")


def test_get_unit_stats_infantry() -> None:
    """Infantry has health 1, defense 1."""
    stats = get_unit_stats("infantry")
    assert stats["health"] == 1
    assert stats["defense"] == 1


def test_get_unit_stats_tanks() -> None:
    """Tanks has health 2, defense 2."""
    stats = get_unit_stats("tanks")
    assert stats["health"] == 2
    assert stats["defense"] == 2


def test_get_unit_stats_returns_copy() -> None:
    """get_unit_stats returns a copy so caller cannot mutate internal state."""
    stats = get_unit_stats("infantry")
    stats["health"] = 99
    assert get_unit_stats("infantry")["health"] == 1
