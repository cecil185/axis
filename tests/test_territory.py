import pytest
from src.territory import (
    ALL_TERRITORY_IDS,
    GRID_ROWS,
    GRID_COLS,
    get_territory_at,
    get_position_of,
    neighbors,
    owner,
    set_owner,
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


def test_neighbors_returns_exactly_two_orthogonal_neighbors() -> None:
    """Each territory has exactly two neighbors (orthogonal only, no diagonals)."""
    assert set(neighbors("A")) == {"B", "C"}  # top-left: right B, below C
    assert set(neighbors("B")) == {"A", "D"}  # top-right: left A, below D
    assert set(neighbors("C")) == {"A", "D"}  # bottom-left: above A, right D
    assert set(neighbors("D")) == {"B", "C"}  # bottom-right: above B, left C


def test_neighbors_is_symmetric() -> None:
    """If X is in neighbors(Y), then Y is in neighbors(X)."""
    for tid in ALL_TERRITORY_IDS:
        for n in neighbors(tid):
            assert tid in neighbors(n)


def test_initial_ownership_red_owns_a_and_d() -> None:
    assert owner("A") == "Red"
    assert owner("D") == "Red"


def test_initial_ownership_blue_owns_b_and_c() -> None:
    assert owner("B") == "Blue"
    assert owner("C") == "Blue"


def test_set_owner_updates_ownership() -> None:
    set_owner("A", "Blue")
    assert owner("A") == "Blue"
    set_owner("A", "Red")
    assert owner("A") == "Red"
