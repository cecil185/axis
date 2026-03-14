"""
Territory IDs and 2×2 grid layout.
No adjacency or ownership logic.
"""

from typing import Literal

TerritoryId = Literal["A", "B", "C", "D"]

# All four territory IDs in grid order (A, B, C, D).
ALL_TERRITORY_IDS: tuple[TerritoryId, ...] = ("A", "B", "C", "D")

# Grid dimensions: 2 rows, 2 columns.
GRID_ROWS = 2
GRID_COLS = 2

# 2×2 grid: row 0 = top, 1 = bottom; col 0 = left, 1 = right.
_GRID: tuple[tuple[TerritoryId, ...], ...] = (
    ("A", "B"),  # row 0: top-left A, top-right B
    ("C", "D"),  # row 1: bottom-left C, bottom-right D
)


def get_territory_at(row: int, col: int) -> TerritoryId | None:
    """Return the territory ID at (row, col), or None if out of bounds."""
    if row < 0 or row >= GRID_ROWS or col < 0 or col >= GRID_COLS:
        return None
    return _GRID[row][col]


def get_position_of(tid: TerritoryId) -> tuple[int, int] | None:
    """Return (row, col) for a territory ID, or None if invalid."""
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            if _GRID[r][c] == tid:
                return (r, c)
    return None
