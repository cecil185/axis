"""
Multi-phase combat loop (axis-6p3).

CombatLoop manages the full combat interaction:
- Runs sequential combat phases using combat_phase().
- After each phase:
  - If either side has no remaining units: award ownership to survivors and end.
  - If both sides still have units: await a continue/retreat decision.
- When awaiting a decision:
  - If either side retreats: end combat with no ownership change.
  - If both continue: run the next phase.

Usage
-----
    loop = CombatLoop(attackers=..., defenders=..., rng=rng_fn)
    loop.run_phase()
    state = loop.get_combat_state()
    if state["status"] == CombatStatus.AWAITING_DECISION:
        loop.submit_decision(attacker_continues=True, defender_continues=False)
    # Check state["status"] for ATTACKER_WINS / DEFENDER_WINS / RETREAT_NO_CHANGE
"""

from enum import Enum
from typing import Callable, TypedDict

from .combat_phase import combat_phase
from .units import UnitCounts


class CombatStatus(str, Enum):
    """Lifecycle state of a CombatLoop."""
    PENDING = "pending"               # Not yet started
    AWAITING_DECISION = "awaiting_decision"  # Phase done; need continue/retreat from both sides
    ATTACKER_WINS = "attacker_wins"   # Defenders eliminated; attacker takes territory
    DEFENDER_WINS = "defender_wins"   # Attackers eliminated; no ownership change
    RETREAT_NO_CHANGE = "retreat_no_change"  # At least one side retreated; no ownership change


class CombatState(TypedDict):
    """Snapshot of the current combat loop state returned by get_combat_state()."""
    phase_index: int           # How many phases have completed
    status: CombatStatus       # Current lifecycle status
    last_att_rolls: list[int]  # Die rolls from the most recent phase (attacker)
    last_def_rolls: list[int]  # Die rolls from the most recent phase (defender)
    last_att_damage: int       # HP removed from defenders in the most recent phase
    last_def_damage: int       # HP removed from attackers in the most recent phase
    remaining_attackers: UnitCounts  # Current attacker unit counts
    remaining_defenders: UnitCounts  # Current defender unit counts


# Terminal statuses — no further actions allowed.
_TERMINAL_STATUSES = {
    CombatStatus.ATTACKER_WINS,
    CombatStatus.DEFENDER_WINS,
    CombatStatus.RETREAT_NO_CHANGE,
}


class CombatLoop:
    """
    Stateful multi-phase combat loop.

    Parameters
    ----------
    attackers:
        Starting unit counts for the attacking side (not mutated).
    defenders:
        Starting unit counts for the defending side (not mutated).
    rng:
        Optional zero-arg callable returning int in [1, 6].
        If omitted, real random rolls are used (random.Random().randint).
        Accepted forms mirror combat_phase():
          - ``lambda: random.randint(1, 6)``
          - ``random.Random(seed).randint``  (two-arg form; auto-wrapped)
    """

    def __init__(
        self,
        attackers: UnitCounts,
        defenders: UnitCounts,
        rng: Callable | None = None,
    ) -> None:
        import random

        # Store defensive copies so callers' dicts are not mutated.
        self._attackers: UnitCounts = dict(attackers)
        self._defenders: UnitCounts = dict(defenders)

        if rng is None:
            _rand = random.Random()
            self._rng: Callable = lambda: _rand.randint(1, 6)
        else:
            self._rng = rng

        self._status = CombatStatus.PENDING
        self._phase_index: int = 0
        self._last_att_rolls: list[int] = []
        self._last_def_rolls: list[int] = []
        self._last_att_damage: int = 0
        self._last_def_damage: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_phase(self) -> None:
        """
        Execute the next combat phase.

        Raises
        ------
        RuntimeError
            If the loop has already ended (terminal status).
        RuntimeError
            If called when AWAITING_DECISION (must call submit_decision first).
        """
        if self._status in _TERMINAL_STATUSES:
            raise RuntimeError(
                f"Combat already ended with status {self._status!r}; "
                "run_phase() cannot be called after combat ends."
            )
        if self._status == CombatStatus.AWAITING_DECISION:
            raise RuntimeError(
                "Combat is awaiting a continue/retreat decision; "
                "call submit_decision() before running the next phase."
            )

        result = combat_phase(self._attackers, self._defenders, self._rng)

        self._phase_index += 1
        self._last_att_rolls = result["att_rolls"]
        self._last_def_rolls = result["def_rolls"]
        self._last_att_damage = result["att_damage"]
        self._last_def_damage = result["def_damage"]
        self._attackers = result["remaining_attackers"]
        self._defenders = result["remaining_defenders"]

        winner = result["winner"]
        if winner == "attacker":
            self._status = CombatStatus.ATTACKER_WINS
        elif winner == "defender":
            self._status = CombatStatus.DEFENDER_WINS
        else:
            # Both sides still have units; await continue/retreat.
            self._status = CombatStatus.AWAITING_DECISION

    def submit_decision(
        self,
        *,
        attacker_continues: bool,
        defender_continues: bool,
    ) -> None:
        """
        Submit the continue/retreat decision for both sides.

        - If either side retreats: status -> RETREAT_NO_CHANGE (no ownership change).
        - If both continue: run the next phase immediately.

        Parameters
        ----------
        attacker_continues:
            True if the attacker chooses to continue; False to retreat.
        defender_continues:
            True if the defender chooses to continue; False to retreat.

        Raises
        ------
        RuntimeError
            If the loop is not in AWAITING_DECISION state.
        """
        if self._status in _TERMINAL_STATUSES:
            raise RuntimeError(
                f"Combat already ended with status {self._status!r}; "
                "submit_decision() cannot be called after combat ends."
            )
        if self._status != CombatStatus.AWAITING_DECISION:
            raise RuntimeError(
                f"Combat is not awaiting a decision (current status: {self._status!r}); "
                "call run_phase() first."
            )

        if not attacker_continues or not defender_continues:
            self._status = CombatStatus.RETREAT_NO_CHANGE
            return

        # Both continue: run the next phase.
        self._status = CombatStatus.PENDING  # reset so run_phase() accepts the call
        self.run_phase()

    def get_combat_state(self) -> CombatState:
        """
        Return a snapshot of the current combat state.

        Returns
        -------
        CombatState TypedDict with:
          - phase_index: number of completed phases
          - status: CombatStatus enum value
          - last_att_rolls / last_def_rolls: rolls from the most recent phase
          - last_att_damage / last_def_damage: HP removed from each side in last phase
          - remaining_attackers / remaining_defenders: current unit counts
        """
        return CombatState(
            phase_index=self._phase_index,
            status=self._status,
            last_att_rolls=list(self._last_att_rolls),
            last_def_rolls=list(self._last_def_rolls),
            last_att_damage=self._last_att_damage,
            last_def_damage=self._last_def_damage,
            remaining_attackers=dict(self._attackers),
            remaining_defenders=dict(self._defenders),
        )
