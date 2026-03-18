"""
Combat dice rolls (1–6 per side) and winner resolution. No ownership changes in this module.

Unit stats are applied in resolve_combat_with_units:
- Tanks get +1 attack bonus (applied to attacker roll)
- Infantry get +2 defense bonus (ties go to defender by default; defense stat further shifts threshold)
"""

import random
from typing import Callable, Literal, TypedDict

from .territory import Team, TerritoryId
from .units import UnitCounts, UnitType, get_unit_stats

CombatRolls = tuple[int, int]  # (attacker_roll, defender_roll)
CombatWinner = Literal["attacker", "defender"]


class PhaseResult(TypedDict):
    """Result of a single combat phase."""
    att_roll: int
    def_roll: int
    att_bonus: int
    def_bonus: int
    winner: CombatWinner
    damage_dealt: int
    att_remaining: UnitCounts
    def_remaining: UnitCounts


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


def _bonus_from_stack(stack: UnitCounts, stat: Literal["attack", "defense"]) -> int:
    """Compute total bonus from a unit stack for the given stat (capped at +3)."""
    bonus = 0
    for unit_type, count in stack.items():
        stats = get_unit_stats(unit_type)
        bonus += stats[stat] * count
    return min(bonus, 3)


def _apply_casualty(stack: UnitCounts, damage: int) -> UnitCounts:
    """
    Remove `damage` units from stack, lowest-health units first (infantry before tanks).
    Returns a new dict; does not mutate the input.
    """
    result: UnitCounts = dict(stack)
    remaining_damage = damage
    # Sort unit types by health ascending so cheapest die first
    sorted_types: list[UnitType] = sorted(
        result.keys(), key=lambda ut: get_unit_stats(ut)["health"]
    )
    for ut in sorted_types:
        if remaining_damage <= 0:
            break
        can_remove = min(result[ut], remaining_damage)
        result[ut] -= can_remove
        remaining_damage -= can_remove
    return result


def combat_phase(
    att_stack: UnitCounts,
    def_stack: UnitCounts,
    *,
    rng: Callable[[], int] | None = None,
    seed: int | None = None,
) -> PhaseResult:
    """
    Execute one combat phase as a pure function.

    Rolls one die per side, applies attack/defense bonuses from the stacks,
    resolves winner, and applies 1 casualty to the loser's stack.
    Does not mutate game state.

    Args:
        att_stack: Attacker's unit counts (e.g. {"infantry": 2, "tanks": 1})
        def_stack: Defender's unit counts
        rng: Optional callable returning 1–6 for deterministic testing
        seed: Optional seed for reproducible rolls (ignored if rng provided)

    Returns:
        PhaseResult with rolls, bonuses, winner, damage dealt, and remaining stacks.
    """
    att_roll, def_roll = roll_combat(rng=rng, seed=seed)
    att_bonus = _bonus_from_stack(att_stack, "attack")
    def_bonus = _bonus_from_stack(def_stack, "defense")
    effective_att = att_roll + att_bonus
    effective_def = def_roll + def_bonus
    winner = resolve_combat(effective_att, effective_def)
    damage = 1
    if winner == "attacker":
        new_def = _apply_casualty(def_stack, damage)
        new_att = dict(att_stack)
    else:
        new_att = _apply_casualty(att_stack, damage)
        new_def = dict(def_stack)
    return PhaseResult(
        att_roll=att_roll,
        def_roll=def_roll,
        att_bonus=att_bonus,
        def_bonus=def_bonus,
        winner=winner,
        damage_dealt=damage,
        att_remaining=new_att,
        def_remaining=new_def,
    )
