"""
Combat dice rolls (1–6 per side). No winner resolution or ownership changes.
"""

import random
from typing import Callable

from .territory import Team, TerritoryId

CombatRolls = tuple[int, int]  # (attacker_roll, defender_roll)


def _roll_d6(rng: random.Random) -> int:
    """Return a single die roll in [1, 6] using the given RNG."""
    return rng.randint(1, 6)


def roll_combat(
    attacker_team: Team,
    defender_team: Team,
    contested_territory_id: TerritoryId,
    *,
    rng: Callable[[], int] | None = None,
    seed: int | None = None,
) -> CombatRolls:
    """
    Roll one die (1–6) for attacker and one for defender; return (attacker_roll, defender_roll).

    Optional:
    - rng: callable that returns 1–6 per call; used for both rolls (e.g. for tests).
    - seed: if rng is None, use random.Random(seed) for deterministic rolls.

    contested_territory_id is for logging/context; no ownership or winner resolution here.
    """
    if rng is not None:
        a = rng()
        b = rng()
        if not (1 <= a <= 6 and 1 <= b <= 6):
            raise ValueError("rng must return values in 1–6")
        return (a, b)
    gen = random.Random(seed) if seed is not None else random
    return (_roll_d6(gen), _roll_d6(gen))
