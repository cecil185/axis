"""Tests for board UI soldier and tank icon rendering (axis-uhy).

Tests verify the data-layer logic for icon positioning and count extraction
used by the icon renderer. Pygame drawing is not tested directly (requires display),
but the helper functions that compute icon positions and unit data are covered.
"""

import pytest
from src.territory import ALL_TERRITORY_IDS, owner, set_owner
from src.units import (
    _STARTING_BLUE_TERRITORIES,
    _STARTING_RED_TERRITORIES,
    init_game,
    set_units,
    units,
)
from src.game import (
    MARKER_RADIUS,
    _icon_positions_for_territory,
    _unit_icon_data,
)


@pytest.fixture(autouse=True)
def reset_state() -> None:
    """Reset unit stacks and territory ownership before each test."""
    init_game()
    for tid in _STARTING_RED_TERRITORIES:
        set_owner(tid, "Red")
    for tid in _STARTING_BLUE_TERRITORIES:
        set_owner(tid, "Blue")


# --- Icon position logic ---


def test_icon_positions_returns_dict_with_infantry_and_tanks() -> None:
    """_icon_positions_for_territory returns positions for both unit types."""
    pos = _icon_positions_for_territory(100, 100, MARKER_RADIUS)
    assert "infantry" in pos
    assert "tanks" in pos


def test_infantry_icon_offset_from_center() -> None:
    """Infantry icon is placed offset to the left of the territory circle."""
    cx, cy = 200, 200
    pos = _icon_positions_for_territory(cx, cy, MARKER_RADIUS)
    inf_x, inf_y = pos["infantry"]
    # Infantry should be offset from center (not at exact center)
    assert inf_x != cx or inf_y != cy


def test_tank_icon_offset_from_center() -> None:
    """Tank icon is placed offset to the right of the territory circle."""
    cx, cy = 200, 200
    pos = _icon_positions_for_territory(cx, cy, MARKER_RADIUS)
    tnk_x, tnk_y = pos["tanks"]
    assert tnk_x != cx or tnk_y != cy


def test_infantry_and_tank_positions_differ() -> None:
    """Infantry and tank icons are placed at different positions."""
    pos = _icon_positions_for_territory(100, 100, MARKER_RADIUS)
    assert pos["infantry"] != pos["tanks"]


def test_icon_positions_scale_with_center() -> None:
    """Icon offsets move proportionally when the center changes."""
    pos_a = _icon_positions_for_territory(100, 100, MARKER_RADIUS)
    pos_b = _icon_positions_for_territory(300, 250, MARKER_RADIUS)
    # The offset delta should be the same regardless of center
    dx_a = pos_a["infantry"][0] - 100
    dy_a = pos_a["infantry"][1] - 100
    dx_b = pos_b["infantry"][0] - 300
    dy_b = pos_b["infantry"][1] - 250
    assert dx_a == dx_b
    assert dy_a == dy_b


def test_icon_positions_scale_with_radius() -> None:
    """Icon offsets are proportional to MARKER_RADIUS so they don't overlap the circle."""
    pos_small = _icon_positions_for_territory(100, 100, 6)
    pos_large = _icon_positions_for_territory(100, 100, 12)
    # With a larger radius the icons must be further from the center
    small_dist = abs(pos_small["infantry"][0] - 100) + abs(pos_small["infantry"][1] - 100)
    large_dist = abs(pos_large["infantry"][0] - 100) + abs(pos_large["infantry"][1] - 100)
    assert large_dist > small_dist


# --- Unit icon data extraction ---


def test_unit_icon_data_returns_counts_for_owner() -> None:
    """_unit_icon_data returns the owning team's infantry and tank counts."""
    tid = _STARTING_RED_TERRITORIES[0]
    data = _unit_icon_data(tid)
    assert data["team"] == "Red"
    assert data["infantry"] == 2
    assert data["tanks"] == 1


def test_unit_icon_data_blue_territory() -> None:
    """_unit_icon_data works for Blue-owned territories."""
    tid = _STARTING_BLUE_TERRITORIES[0]
    data = _unit_icon_data(tid)
    assert data["team"] == "Blue"
    assert data["infantry"] == 2
    assert data["tanks"] == 1


def test_unit_icon_data_reflects_updated_counts() -> None:
    """_unit_icon_data returns updated counts after set_units call."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 3, "tanks": 2})
    data = _unit_icon_data(tid)
    assert data["infantry"] == 3
    assert data["tanks"] == 2


def test_unit_icon_data_zero_counts() -> None:
    """_unit_icon_data handles zero units gracefully."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    data = _unit_icon_data(tid)
    assert data["infantry"] == 0
    assert data["tanks"] == 0


def test_unit_icon_data_neutral_territory() -> None:
    """_unit_icon_data returns zeroed counts for Neutral territories."""
    from src.territory import set_neutral
    tid = _STARTING_RED_TERRITORIES[0]
    set_neutral(tid)
    data = _unit_icon_data(tid)
    assert data["infantry"] == 0
    assert data["tanks"] == 0


def test_unit_icon_data_all_territories() -> None:
    """_unit_icon_data returns valid data for every territory after init."""
    for tid in ALL_TERRITORY_IDS:
        data = _unit_icon_data(tid)
        assert "team" in data
        assert "infantry" in data
        assert "tanks" in data
        assert isinstance(data["infantry"], int)
        assert isinstance(data["tanks"], int)
        assert data["infantry"] >= 0
        assert data["tanks"] >= 0


def test_unit_icon_data_zero_infantry_only() -> None:
    """When a territory has only tanks, infantry count is 0 (suppresses infantry icon)."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 0, "tanks": 1})
    data = _unit_icon_data(tid)
    assert data["infantry"] == 0
    assert data["tanks"] == 1
    # Consuming code: only draw infantry icon when count > 0
    assert not data["infantry"]


def test_unit_icon_data_zero_tanks_only() -> None:
    """When a territory has only infantry, tanks count is 0 (suppresses tank icon)."""
    tid = _STARTING_RED_TERRITORIES[0]
    set_units(tid, "Red", {"infantry": 3, "tanks": 0})
    data = _unit_icon_data(tid)
    assert data["infantry"] == 3
    assert data["tanks"] == 0
    # Consuming code: only draw tank icon when count > 0
    assert not data["tanks"]
