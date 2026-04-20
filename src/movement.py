"""
Movement rules: compute reachable territories for a unit given source, team, and unit type.

Rules:
  - Infantry: may move to any friendly-owned territory within 1 hop.
  - Tanks: may move up to 2 hops.
      - Can pass through friendly territories to continue further.
      - Can enter an enemy territory (capturing it) but stop there — cannot continue through it.
  - The source territory is never included in the result.
  - No state mutation; purely reads current ownership.

Public API:
  reachable_territories(tid, team, unit_type) -> set[TerritoryId]
"""

from .territory import TerritoryId, Team, neighbors, owner
from .units import UnitType


def reachable_territories(tid: TerritoryId, team: Team, unit_type: UnitType) -> set[TerritoryId]:
    """
    Return the set of valid destination territories for a unit at `tid` belonging to `team`.

    Infantry (1-hop): only adjacent territories owned by `team`.
    Tanks (up to 2 hops): BFS up to depth 2.
      - May pass through friendly territories to reach further destinations.
      - May enter (and stop at) an enemy territory at any hop.
      - Cannot traverse through an enemy territory.

    The source territory `tid` is never included in the result.
    """
    if unit_type == "infantry":
        return _infantry_reachable(tid, team)
    elif unit_type == "tanks":
        return _tank_reachable(tid, team)
    else:
        raise ValueError(f"Unknown unit type: {unit_type!r}")


def _infantry_reachable(tid: TerritoryId, team: Team) -> set[TerritoryId]:
    """Infantry: all adjacent territories owned by `team`."""
    result: set[TerritoryId] = set()
    for neighbor in neighbors(tid):
        if owner(neighbor) == team:
            result.add(neighbor)
    return result


def _tank_reachable(tid: TerritoryId, team: Team) -> set[TerritoryId]:
    """
    Tanks: BFS up to depth 2.
    - Friendly territory at hop N: add to result, continue expanding from it (if hop < 2).
    - Non-friendly territory (enemy or neutral) at hop N: add to result, stop — do not expand.

    We track expanded friendly territories to avoid processing the same waypoint twice.
    Non-friendly territories are never expanded so they only need to be added to result once.
    """
    result: set[TerritoryId] = set()
    # expanded: friendly territories we have already expanded outward from (to avoid cycles).
    expanded: set[TerritoryId] = {tid}

    # Frontier entries: (territory_id, hop_count)
    frontier: list[tuple[TerritoryId, int]] = [
        (n, 1) for n in neighbors(tid)
    ]

    while frontier:
        current, hop = frontier.pop()

        if owner(current) == team:
            # Friendly: reachable destination and eligible waypoint
            result.add(current)
            if hop < 2 and current not in expanded:
                expanded.add(current)
                for n in neighbors(current):
                    if n not in expanded:
                        frontier.append((n, hop + 1))
        else:
            # Non-friendly: reachable destination, movement stops here
            result.add(current)
            # Do not expand beyond non-friendly territory

    return result
