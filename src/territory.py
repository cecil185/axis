"""
Territory IDs, 2×2 grid layout, and ownership.
"""

from typing import Literal

TerritoryId = Literal["A", "B", "C", "D"]
Team = Literal["Red", "Blue"]

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


def neighbors(tid: TerritoryId) -> list[TerritoryId]:
    """Return list of adjacent territory IDs (orthogonal only, no diagonals)."""
    pos = get_position_of(tid)
    if pos is None:
        return []
    row, col = pos
    result: list[TerritoryId] = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        neighbor = get_territory_at(row + dr, col + dc)
        if neighbor is not None:
            result.append(neighbor)
    return result


# Initial state: Red owns A and D; Blue owns B and C (symmetric corners).
_owners: dict[TerritoryId, Team] = {
    "A": "Red",
    "B": "Blue",
    "C": "Blue",
    "D": "Red",
}


def owner(tid: TerritoryId) -> Team:
    """Return the team that owns the territory."""
    return _owners[tid]


def set_owner(tid: TerritoryId, team: Team) -> None:
    """Set the owner of the territory."""
    _owners[tid] = team
