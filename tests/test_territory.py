import pytest
from src.territory import (
    ALL_TERRITORY_IDS,
    GRID_ROWS,
    GRID_COLS,
    get_territory_at,
    get_position_of,
    TerritoryId,
)


def test_exposes_all_four_territory_ids() -> None:
    assert len(ALL_TERRITORY_IDS) == 4
    assert set(ALL_TERRITORY_IDS) == {"A", "B", "C", "D"}


def test_exposes_grid_dimensions_2x2() -> None:
    assert GRID_ROWS == 2
    assert GRID_COLS == 2


def test_maps_grid_positions_to_territory_ids() -> None:
    assert get_territory_at(0, 0) == "A"  # top-left
    assert get_territory_at(0, 1) == "B"  # top-right
    assert get_territory_at(1, 0) == "C"  # bottom-left
    assert get_territory_at(1, 1) == "D"  # bottom-right


def test_returns_none_for_out_of_bounds() -> None:
    assert get_territory_at(-1, 0) is None
    assert get_territory_at(0, -1) is None
    assert get_territory_at(2, 0) is None
    assert get_territory_at(0, 2) is None


def test_returns_position_for_each_territory_id() -> None:
    assert get_position_of("A") == (0, 0)
    assert get_position_of("B") == (0, 1)
    assert get_position_of("C") == (1, 0)
    assert get_position_of("D") == (1, 1)


def test_round_trip_get_territory_at_get_position_of() -> None:
    for tid in ALL_TERRITORY_IDS:
        pos = get_position_of(tid)
        assert pos is not None
        row, col = pos
        assert get_territory_at(row, col) == tid
