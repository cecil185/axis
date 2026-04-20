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
    - Friendly territory at hop N: add to result, continue BFS through it.
    - Enemy territory at hop N: add to result, do NOT expand through it.
    """
    result: set[TerritoryId] = set()
    # Queue entries: (territory_id, hops_remaining)
    # We track visited friendly territories to avoid re-expanding them.
    # Enemy territories are added to result but never expanded (stop there).
    visited_friendly: set[TerritoryId] = {tid}

    # Initial frontier: direct neighbors of source
    frontier: list[tuple[TerritoryId, int]] = [
        (n, 1) for n in neighbors(tid)
    ]

    while frontier:
        current, hop = frontier.pop()

        if owner(current) == team:
            # Friendly territory
            if current not in result:
                result.add(current)
            if hop < 2 and current not in visited_friendly:
                visited_friendly.add(current)
                for n in neighbors(current):
                    if n != tid and n not in visited_friendly:
                        frontier.append((n, hop + 1))
        else:
            # Enemy territory: reachable, but movement stops here
            result.add(current)
            # Do not expand through enemy territory

    return result
