"""
Unit types (infantry, tanks) with stats, and per-territory unit stacks.

Unit types are the single source of truth for stats (health, defense).
Per-territory stacks: dict mapping unit type -> count.
Owner is derived from which team has units in the territory.

API:
  unit_types() -> list of unit type ids
  get_unit_stats(unit_type) -> UnitStats
  units(tid) -> UnitCounts for territory
  set_units(tid, counts) -> set unit counts for territory (keyed by team)
  owner_from_units(tid) -> Team | None (None if no units)
  init_game() -> place starting units on all territories
"""

from typing import Literal, TypedDict

from .territory import ALL_TERRITORY_IDS, Team, TerritoryId

# --- Unit types ---

UnitType = Literal["infantry", "tanks"]
ALL_UNIT_TYPES: tuple[UnitType, ...] = ("infantry", "tanks")


class UnitStats(TypedDict):
    """Stats for a unit type."""
    health: int
    defense: int   # threshold: defender wins tie if roll <= defense (used in combat)
    attack: int    # attacker roll bonus (added before comparison)


_UNIT_STATS: dict[UnitType, UnitStats] = {
    "infantry": {"health": 1, "defense": 2, "attack": 0},
    "tanks":    {"health": 2, "defense": 1, "attack": 1},
}


def unit_types() -> list[UnitType]:
    """Return list of all unit type ids."""
    return list(ALL_UNIT_TYPES)


def get_unit_stats(unit_type: UnitType) -> UnitStats:
    """Return stats for the given unit type."""
    return _UNIT_STATS[unit_type].copy()


# --- Per-territory unit stacks ---
# Each territory stores counts per (team, unit_type).
# UnitCounts: {unit_type: count} for a single team in a territory.

UnitCounts = dict[UnitType, int]

# _stacks[tid][team] = {unit_type: count}
_stacks: dict[TerritoryId, dict[Team, UnitCounts]] = {
    tid: {"Red": {"infantry": 0, "tanks": 0}, "Blue": {"infantry": 0, "tanks": 0}}
    for tid in ALL_TERRITORY_IDS
}


def units(tid: TerritoryId, team: Team) -> UnitCounts:
    """Return unit counts for the given team in the given territory."""
    return dict(_stacks[tid][team])


def set_units(tid: TerritoryId, team: Team, counts: UnitCounts) -> None:
    """Set unit counts for the given team in the given territory."""
    _stacks[tid][team] = {"infantry": counts.get("infantry", 0), "tanks": counts.get("tanks", 0)}


def total_units(tid: TerritoryId, team: Team) -> int:
    """Return total number of units for a team in a territory."""
    return sum(_stacks[tid][team].values())


def owner_from_units(tid: TerritoryId) -> Team | None:
    """
    Return the team that owns the territory based on unit presence.
    A team owns a territory if it has more total units than the enemy.
    Returns None if both teams have equal units (including both at 0).
    """
    red_total = total_units(tid, "Red")
    blue_total = total_units(tid, "Blue")
    if red_total > blue_total:
        return "Red"
    if blue_total > red_total:
        return "Blue"
    return None


# Starting units per territory per team: 2 infantry, 1 tank
_STARTING_COUNTS: UnitCounts = {"infantry": 2, "tanks": 1}

# Game start: Red owns first 15 territories, Blue owns last 14 (matching territory._owners initial state)
_STARTING_RED_TERRITORIES: tuple[TerritoryId, ...] = ALL_TERRITORY_IDS[:15]
_STARTING_BLUE_TERRITORIES: tuple[TerritoryId, ...] = ALL_TERRITORY_IDS[15:]


def init_game() -> None:
    """
    Initialize unit stacks for game start.
    Red territories get 2 infantry + 1 tank for Red, 0 for Blue.
    Blue territories get 2 infantry + 1 tank for Blue, 0 for Red.
    """
    empty: UnitCounts = {"infantry": 0, "tanks": 0}
    for tid in _STARTING_RED_TERRITORIES:
        set_units(tid, "Red", dict(_STARTING_COUNTS))
        set_units(tid, "Blue", dict(empty))
    for tid in _STARTING_BLUE_TERRITORIES:
        set_units(tid, "Blue", dict(_STARTING_COUNTS))
        set_units(tid, "Red", dict(empty))


# Initialize on module load so game starts with correct placement
init_game()
