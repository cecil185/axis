"""
Unit type IDs and stats (infantry, tanks). Single source of truth for type metadata.
"""

from typing import Literal, TypedDict

UnitTypeId = Literal["infantry", "tanks"]

ALL_UNIT_TYPE_IDS: tuple[UnitTypeId, ...] = ("infantry", "tanks")


class UnitStats(TypedDict):
    """Health and defense for a unit type."""

    health: int
    defense: int


# Stats per type: health and defense (constants).
_UNIT_STATS: dict[UnitTypeId, UnitStats] = {
    "infantry": {"health": 1, "defense": 1},
    "tanks": {"health": 2, "defense": 2},
}


def get_unit_stats(unit_type: UnitTypeId) -> UnitStats:
    """Return health and defense for the given unit type."""
    return _UNIT_STATS[unit_type].copy()
