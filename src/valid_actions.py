"""
Valid actions API: which actions the current team can take (attack targets, skip).
"""

from .territory import ALL_TERRITORY_IDS, TerritoryId, neighbors, owner
from .state import current_team


def valid_attack_targets() -> list[TerritoryId]:
    """
    Return enemy territory IDs that are adjacent to at least one territory owned by
    current team. Neutral territories are NOT valid attack targets. Empty if none.
    """
    team = current_team()
    targets: set[TerritoryId] = set()
    for tid in ALL_TERRITORY_IDS:
        if owner(tid) != team:
            continue
        for n in neighbors(tid):
            n_owner = owner(n)
            # Only non-team, non-neutral territories are valid attack targets
            if n_owner != team and n_owner != "Neutral":
                targets.add(n)
    return sorted(targets)


def can_skip() -> bool:
    """Skip is always allowed in this game; returns True."""
    return True
