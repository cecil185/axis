"""
Combat dice rolls (1–6 per side) and winner resolution. No ownership changes in this module.

Unit stats are applied in resolve_combat_with_units:
- Tanks get +1 attack bonus (applied to attacker roll)
- Infantry get +2 defense bonus (ties go to defender by default; defense stat further shifts threshold)
"""

import random
from typing import Callable, Literal

from .territory import Team, TerritoryId

CombatRolls = tuple[int, int]  # (attacker_roll, defender_roll)
CombatWinner = Literal["attacker", "defender"]


def resolve_combat(att_roll: int, def_roll: int) -> CombatWinner:
    """
    Resolve combat from rolls: higher roll wins; tie goes to defender.
    Returns 'attacker' or 'defender'.
    """
    return "attacker" if att_roll > def_roll else "defender"


def _effective_attack_bonus(attacking_team: Team, attacking_tid: TerritoryId) -> int:
    """
    Compute the effective attack bonus from unit types in attacking territory.
    Tanks contribute +1 attack each; infantry +0.
    Returns total bonus (capped at +3 to keep rolls in sensible range).
    """
    from .units import units, get_unit_stats  # noqa: PLC0415
    stack = units(attacking_tid, attacking_team)
    bonus = 0
    for unit_type, count in stack.items():
        stats = get_unit_stats(unit_type)
        bonus += stats["attack"] * count
    return min(bonus, 3)  # cap bonus


def _effective_defense_bonus(defending_team: Team, defending_tid: TerritoryId) -> int:
    """
    Compute the effective defense bonus from unit types in defending territory.
    Infantry contribute +2 defense each; tanks +1.
    Returns total bonus (capped at +3).
    """
    from .units import units, get_unit_stats  # noqa: PLC0415
    stack = units(defending_tid, defending_team)
    bonus = 0
    for unit_type, count in stack.items():
        stats = get_unit_stats(unit_type)
        bonus += stats["defense"] * count
    return min(bonus, 3)  # cap bonus


def resolve_combat_with_units(
    att_roll: int,
    def_roll: int,
    attacking_team: Team,
    attacking_tid: TerritoryId,
    defending_tid: TerritoryId,
) -> CombatWinner:
    """
    Resolve combat applying unit stats from the territory stacks.
    Attack bonus is added to attacker's roll; defense bonus is added to defender's roll.
    Higher effective roll wins; defender wins ties.
    """
    defending_team: Team = "Blue" if attacking_team == "Red" else "Red"
    att_bonus = _effective_attack_bonus(attacking_team, attacking_tid)
    def_bonus = _effective_defense_bonus(defending_team, defending_tid)
    effective_att = att_roll + att_bonus
    effective_def = def_roll + def_bonus
    return resolve_combat(effective_att, effective_def)


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
