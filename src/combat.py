"""
Combat dice rolls (1–6 per side) and winner resolution. No ownership changes in this module.
"""

import random
from typing import Callable, Literal

from .territory import Team

CombatRolls = tuple[int, int]  # (attacker_roll, defender_roll)
CombatWinner = Literal["attacker", "defender"]


def resolve_combat(att_roll: int, def_roll: int) -> CombatWinner:
    """
    Resolve combat from rolls: higher roll wins; tie goes to defender.
    Returns 'attacker' or 'defender'.
    """
    return "attacker" if att_roll > def_roll else "defender"


def _roll_d6(rng: random.Random) -> int:
    """Return a single die roll in [1, 6] using the given RNG."""
    return rng.randint(1, 6)


def roll_combat(
    *,
    rng: Callable[[], int] | None = None,
    seed: int | None = None,
) -> CombatRolls:
    """
    Roll one die (1–6) for attacker and one for defender; return (attacker_roll, defender_roll).

    Optional:
    - rng: callable that returns 1–6 per call; used for both rolls (e.g. for tests).
    - seed: if rng is None, use random.Random(seed) for deterministic rolls.
    """
    if rng is not None:
        a = rng()
        b = rng()
        if not (1 <= a <= 6 and 1 <= b <= 6):
            raise ValueError("rng must return values in 1–6")
        return (a, b)
    gen = random.Random(seed) if seed is not None else random
    return (_roll_d6(gen), _roll_d6(gen))
