# Multi-Phase Battle Units — Tasks

Tasks are grouped into **parallel workstreams**. Each task is at most ~2 hours. Stream A must complete before B and C can start; then B and C can run in parallel. Sync where noted.

---

## From proposal

| Proposal (What Changes) | Workstream | Tasks |
|-------------------------|------------|-------|
| Unit types; territories hold stacks; game start conditions | A | A.1, A.2 |
| Multi-phase combat; retreat or continue; game integration | B | B.1, B.2, B.3 |
| UI: board units, combat phase display, Continue/Retreat | C | C.1, C.2, C.3 |

---

## Sync points

| After | Unblocked |
|-------|-----------|
| **Stream A done** | Stream B and Stream C can start |
| **B.1 done** | C.2 can start (combat phase UI needs phase result shape) |
| **B.2 done** | C.3 can start (retreat/continue UI needs combat flow) |
| **B.3 done** | — (game loop integrated; C can already be in progress) |

---

## Stream A — State & units (foundation)

Complete first. No dependency on B or C.

- [ ] **A.1** Define unit types: infantry and tanks, each with health and defense (e.g. constants or config). Expose type ids and stats (e.g. `get_unit_stats(unit_type)`). No territory changes yet.
- [ ] **A.2** Add per-territory unit stacks: each territory holds counts per type (e.g. `{infantry: n, tanks: m}`) and owner derived from presence of units. Game start conditions: apply a set number of units on each territory (e.g. 2 infantry, 1 tank per territory); two territories per team, same counts on all. API: e.g. `units(territory_id)`, `set_units(territory_id, counts)`, `owner(territory_id)` from units.

---

## Stream B — Combat logic

Start after **Stream A** is done. B.1 → B.2 → B.3 in order.

- [ ] **B.1** Implement one combat phase: given attacker/defender unit stacks, roll (e.g. dice), apply damage by unit type health/defense, return updated stacks and phase result (rolls, damage, remaining units). Support injectable RNG for tests. Do not yet change game state.
- [ ] **B.2** Combat flow: after each phase, accept choice (continue or retreat) from each side; if either retreats, end combat (no ownership change, turn ends); if both continue, run next phase; if one side has no units, assign ownership of contested territory to winner and end turn. Expose state for UI (e.g. `get_combat_state()`: phase index, rolls, damage, remaining units, and whether waiting for continue/retreat).
- [ ] **B.3** Integrate combat into game: on attack action, start multi-phase combat; use B.1/B.2 to resolve; update territory ownership and unit stacks when combat ends (elimination); on retreat, leave ownership and units as-is, end turn. Valid attack targets and win condition remain unit-based (territory with no units = no owner).

---

## Stream C — UI

Start after **Stream A** is done. C.1 can start immediately; C.2 after **B.1**; C.3 after **B.2**. Run in parallel with Stream B where possible.

- [ ] **C.1** Board UI: display each territory with owner and unit counts by type (e.g. "A: Red — 2 infantry, 1 tank"). Ensure runner/UI reads from `units(territory_id)` and `owner(territory_id)` so any state change is visible.
- [ ] **C.2** Combat phase UI: during combat, show current phase number, last rolls, damage applied, and remaining units for attacker and defender after each phase. Hook into combat state from B.2 so UI updates after every phase.
- [ ] **C.3** Retreat/Continue UI: after each phase (when both sides have units), present "Continue" and "Retreat" (or equivalent); on choice, pass decision into combat flow and show next state (next phase or combat ended). Ensure prompt and result are clear (e.g. "Combat ended — defender retreated").

---

## Beads (bd)

**Canonical stream:** A.1 → A.2 → (B.1 ‖ C.1); B.1 → B.2 → B.3; C.2 after B.1, C.3 after B.2.

| Stream | Bead ID   | Task |
|--------|-----------|------|
| A.1    | axis-kp2  | Unit types (infantry, tanks) |
| A.2    | axis-dro  | Per-territory unit stacks and game start |
| B.1    | axis-i75  | One combat phase (roll, damage, stacks) |
| B.2    | axis-6p3  | Combat flow (continue/retreat, ownership on elimination) |
| B.3    | axis-96u  | Integrate multi-phase combat into game loop |
| C.1    | axis-8qj  | Board UI — show units per territory |
| C.2    | axis-2nk  | Combat phase UI (depends on B.2 for get_combat_state()) |
| C.3    | axis-111  | Retreat/Continue UI |
