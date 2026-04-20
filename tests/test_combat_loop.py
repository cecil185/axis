"""
Tests for the multi-phase combat loop (axis-6p3).

CombatLoop manages:
- Multi-phase execution via combat_phase()
- After each phase: detect elimination -> award ownership and end
- When both sides survive: await continue/retreat decisions from each side
- If either side retreats: end combat, no ownership change
- If both sides continue: run the next phase
- Expose get_combat_state() returning structured state
"""

import pytest

from src.combat_loop import CombatLoop, CombatState, CombatStatus
from src.units import UnitCounts


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixed_rng(values: list[int]):
    """Return a callable that yields values in sequence."""
    it = iter(values)
    return lambda: next(it)


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------


def test_initial_state_is_awaiting_first_phase() -> None:
    """After construction, combat has not yet begun (phase_index=0, not awaiting decisions)."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
    )
    state = loop.get_combat_state()
    assert state["phase_index"] == 0
    assert state["status"] == CombatStatus.PENDING
    assert state["last_att_rolls"] == []
    assert state["last_def_rolls"] == []
    assert state["last_att_damage"] == 0
    assert state["last_def_damage"] == 0
    assert state["remaining_attackers"] == {"infantry": 2, "tanks": 0}
    assert state["remaining_defenders"] == {"infantry": 2, "tanks": 0}


# ---------------------------------------------------------------------------
# Elimination on first phase -> ownership awarded, loop ends
# ---------------------------------------------------------------------------


def test_attacker_eliminates_defenders_in_first_phase() -> None:
    """When attackers wipe out all defenders in phase 1, loop ends with attacker winning."""
    # 3 attackers all hit (roll 4), 1 defender misses
    loop = CombatLoop(
        attackers={"infantry": 3, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
        rng=_fixed_rng([4, 4, 4, 1]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.ATTACKER_WINS
    assert state["phase_index"] == 1
    assert sum(state["remaining_defenders"].values()) == 0
    assert sum(state["remaining_attackers"].values()) > 0


def test_defender_eliminates_attackers_in_first_phase() -> None:
    """When defenders wipe out all attackers in phase 1, loop ends with defender winning."""
    # 1 attacker misses, 3 defenders all hit
    loop = CombatLoop(
        attackers={"infantry": 1, "tanks": 0},
        defenders={"infantry": 3, "tanks": 0},
        rng=_fixed_rng([1, 4, 4, 4]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.DEFENDER_WINS
    assert state["phase_index"] == 1
    assert sum(state["remaining_attackers"].values()) == 0
    assert sum(state["remaining_defenders"].values()) > 0


def test_mutual_elimination_defender_wins() -> None:
    """When both sides are eliminated simultaneously, defender wins (consistent with phase rules)."""
    # 1 infantry each, both hit — mutual kill
    loop = CombatLoop(
        attackers={"infantry": 1, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
        rng=_fixed_rng([4, 4]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.DEFENDER_WINS


# ---------------------------------------------------------------------------
# Phase result metadata
# ---------------------------------------------------------------------------


def test_phase_result_stored_in_state() -> None:
    """After run_phase(), last_att_rolls, last_def_rolls, and damage are recorded."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert len(state["last_att_rolls"]) == 2
    assert len(state["last_def_rolls"]) == 2
    assert state["last_att_damage"] >= 0
    assert state["last_def_damage"] >= 0


# ---------------------------------------------------------------------------
# Awaiting continue/retreat when both sides survive
# ---------------------------------------------------------------------------


def test_partial_casualties_triggers_decision_phase() -> None:
    """When both sides survive a phase, status becomes AWAITING_DECISION."""
    # Both sides take 1 hit each, both survive
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.AWAITING_DECISION
    assert state["phase_index"] == 1
    # Neither side eliminated
    assert sum(state["remaining_attackers"].values()) > 0
    assert sum(state["remaining_defenders"].values()) > 0


def test_awaiting_decision_no_winner_yet() -> None:
    """When AWAITING_DECISION, neither winner nor retreat has been declared yet."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.AWAITING_DECISION


# ---------------------------------------------------------------------------
# Retreat ends combat, no ownership change
# ---------------------------------------------------------------------------


def test_attacker_retreats_ends_combat() -> None:
    """When attacker chooses Retreat, status becomes RETREAT_NO_CHANGE."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.AWAITING_DECISION
    loop.submit_decision(attacker_continues=False, defender_continues=True)
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.RETREAT_NO_CHANGE


def test_defender_retreats_ends_combat() -> None:
    """When defender chooses Retreat, status becomes RETREAT_NO_CHANGE."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.AWAITING_DECISION
    loop.submit_decision(attacker_continues=True, defender_continues=False)
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.RETREAT_NO_CHANGE


def test_both_retreat_ends_combat() -> None:
    """When both sides choose Retreat, status becomes RETREAT_NO_CHANGE."""
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1]),
    )
    loop.run_phase()
    loop.submit_decision(attacker_continues=False, defender_continues=False)
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.RETREAT_NO_CHANGE


# ---------------------------------------------------------------------------
# Both continue -> runs next phase
# ---------------------------------------------------------------------------


def test_both_continue_advances_phase_index() -> None:
    """When both sides choose Continue, the phase index advances and combat proceeds."""
    # Phase 1: both survive (1 inf each dies); Phase 2 RNG provided
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1,   # phase 1: att hits+miss, def hits+miss
                         3, 3]),         # phase 2: both miss -> still alive
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.AWAITING_DECISION

    loop.submit_decision(attacker_continues=True, defender_continues=True)
    # After decision, loop should have auto-advanced to next phase
    state = loop.get_combat_state()
    assert state["phase_index"] == 2


def test_both_continue_phase2_no_winner_awaits_again() -> None:
    """After second phase with survivors, loop again awaits decision."""
    loop = CombatLoop(
        attackers={"infantry": 3, "tanks": 0},
        defenders={"infantry": 3, "tanks": 0},
        rng=_fixed_rng([4, 1, 1, 4, 1, 1,   # phase 1: att hits once, def hits once
                         4, 1, 1, 4, 1, 1]), # phase 2: att hits once, def hits once
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.AWAITING_DECISION
    loop.submit_decision(attacker_continues=True, defender_continues=True)
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.AWAITING_DECISION
    assert state["phase_index"] == 2


def test_multi_phase_continuation_leads_to_elimination() -> None:
    """Multi-phase combat eventually eliminates a side after enough phases."""
    # Phase 1: both 2 inf, att hits 1, def hits 1 -> each at 1 inf
    # Phase 2: att hits 1, def misses -> defender eliminated
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1,   # phase 1
                         4, 1]),        # phase 2 (att hits, def misses)
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.AWAITING_DECISION
    loop.submit_decision(attacker_continues=True, defender_continues=True)
    state = loop.get_combat_state()
    assert state["status"] == CombatStatus.ATTACKER_WINS
    assert state["phase_index"] == 2


# ---------------------------------------------------------------------------
# Unit stacks updated across phases
# ---------------------------------------------------------------------------


def test_unit_stacks_carry_over_between_phases() -> None:
    """Remaining stacks from phase N are inputs to phase N+1."""
    # Phase 1: 2v2 infantry, 1 each dies
    # After submit_decision(continue,continue), phase 2 starts with 1v1
    loop = CombatLoop(
        attackers={"infantry": 2, "tanks": 0},
        defenders={"infantry": 2, "tanks": 0},
        rng=_fixed_rng([4, 1, 4, 1,   # phase 1
                         4, 1]),        # phase 2
    )
    loop.run_phase()
    state1 = loop.get_combat_state()
    assert state1["remaining_attackers"]["infantry"] == 1
    assert state1["remaining_defenders"]["infantry"] == 1

    loop.submit_decision(attacker_continues=True, defender_continues=True)
    state2 = loop.get_combat_state()
    # Attacker won phase 2 by hitting (defender missed)
    assert state2["status"] == CombatStatus.ATTACKER_WINS
    assert state2["remaining_defenders"]["infantry"] == 0


# ---------------------------------------------------------------------------
# Error handling: invalid transitions
# ---------------------------------------------------------------------------


def test_submit_decision_before_phase_raises() -> None:
    """Calling submit_decision when not AWAITING_DECISION should raise an error."""
    loop = CombatLoop(
        attackers={"infantry": 1, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
    )
    with pytest.raises(RuntimeError, match="not awaiting"):
        loop.submit_decision(attacker_continues=True, defender_continues=True)


def test_run_phase_after_combat_ends_raises() -> None:
    """Calling run_phase() after a terminal state should raise an error."""
    loop = CombatLoop(
        attackers={"infantry": 3, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
        rng=_fixed_rng([4, 4, 4, 1]),
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.ATTACKER_WINS
    with pytest.raises(RuntimeError, match="already ended"):
        loop.run_phase()


def test_submit_decision_after_combat_ends_raises() -> None:
    """Calling submit_decision after a terminal state should raise an error."""
    loop = CombatLoop(
        attackers={"infantry": 3, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
        rng=_fixed_rng([4, 4, 4, 1]),
    )
    loop.run_phase()
    assert loop.get_combat_state()["status"] == CombatStatus.ATTACKER_WINS
    with pytest.raises(RuntimeError, match="already ended"):
        loop.submit_decision(attacker_continues=True, defender_continues=True)


# ---------------------------------------------------------------------------
# get_combat_state returns correct shape
# ---------------------------------------------------------------------------


def test_get_combat_state_returns_typed_dict() -> None:
    """get_combat_state() must return a dict with all required keys."""
    loop = CombatLoop(
        attackers={"infantry": 1, "tanks": 0},
        defenders={"infantry": 1, "tanks": 0},
    )
    state = loop.get_combat_state()
    required_keys = {
        "phase_index",
        "status",
        "last_att_rolls",
        "last_def_rolls",
        "last_att_damage",
        "last_def_damage",
        "remaining_attackers",
        "remaining_defenders",
    }
    assert required_keys.issubset(state.keys())


# ---------------------------------------------------------------------------
# No mutation of constructor inputs
# ---------------------------------------------------------------------------


def test_constructor_inputs_not_mutated() -> None:
    """CombatLoop must not mutate the initial attacker/defender dicts."""
    attackers: UnitCounts = {"infantry": 2, "tanks": 1}
    defenders: UnitCounts = {"infantry": 1, "tanks": 1}
    att_copy = dict(attackers)
    def_copy = dict(defenders)
    loop = CombatLoop(
        attackers=attackers,
        defenders=defenders,
        rng=_fixed_rng([4, 4, 4, 1, 2]),
    )
    loop.run_phase()
    assert attackers == att_copy
    assert defenders == def_copy
