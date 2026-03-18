"""
Movement range: reachable_territories(tid, team, unit_type) -> set[TerritoryId].

Infantry: 1 hop to any friendly-owned adjacent territory.
Tanks: up to 2 hops through friendly territories; entering an enemy territory stops movement.
No state mutation.
"""

from .territory import Team, TerritoryId, neighbors, owner
from .units import UnitType


def reachable_territories(
    tid: TerritoryId, team: Team, unit_type: UnitType
) -> set[TerritoryId]:
    """
    Return all valid destination territories for a unit moving from tid.

    Infantry: can move to any adjacent territory owned by the same team (1 hop).
    Tanks: can move up to 2 hops. Intermediate territories must be friendly to
    continue through. Entering an enemy territory stops movement (the enemy
    territory is reachable but the tank cannot continue past it).
    """
    if unit_type == "infantry":
        return _infantry_reachable(tid, team)
    return _tank_reachable(tid, team)


def _infantry_reachable(tid: TerritoryId, team: Team) -> set[TerritoryId]:
    """Infantry: 1-hop to friendly neighbors only."""
    result: set[TerritoryId] = set()
    for n in neighbors(tid):
        if owner(n) == team:
            result.add(n)
    return result


def _tank_reachable(tid: TerritoryId, team: Team) -> set[TerritoryId]:
    """Tanks: up to 2 hops; stop on entering enemy territory."""
    result: set[TerritoryId] = set()
    for hop1 in neighbors(tid):
        result.add(hop1)
        # Can only continue through hop1 if it is friendly
        if owner(hop1) == team:
            for hop2 in neighbors(hop1):
                if hop2 != tid:
                    result.add(hop2)
    return result
