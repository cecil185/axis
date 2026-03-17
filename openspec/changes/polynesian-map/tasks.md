# Polynesian Map — Tasks

Tasks are grouped into **parallel workstreams**. Each task is at most ~2 hours. Stream A must complete first; then Stream B and Stream C can run in parallel (C.2 starts after B.1).

---

## From proposal

| Proposal (What Changes) | Workstream | Tasks |
|-------------------------|------------|-------|
| Map: 8 territories, metadata, adjacency, fixed initial ownership | A | A.1, A.2, A.3 |
| Game logic and win condition (all 8 territories) | B | B.1 |
| Tests: graph, metadata, initial ownership, win | C | C.1 |
| UI: replace grid with territory list/layout; click → territory id | C | C.2 |

---

## Sync points

| After | Unblocked |
|-------|-----------|
| **Stream A done** | Stream B and Stream C can start |
| **B.1 done** | C.2 can start (UI needs game loop and valid actions for 8 territories) |

---

## Stream A — Map data & territory module (foundation)

Complete first. A.1 → A.2 → A.3 in order. (bd: axis-0fk → axis-oqj → axis-97i)

- [ ] **A.1** [axis-0fk] Define the Polynesian territory set: 8 territory ids (`hawaii`, `samoa`, `tonga`, `fiji`, `tahiti`, `marquesas`, `cook_islands`, `easter_island`), each with `region` and `display_name` per design. Expose `ALL_TERRITORY_IDS` and metadata accessors (e.g. `region(tid)`, `display_name(tid)` or `territory_info(tid)`). No adjacency or ownership yet.
- [ ] **A.2** [axis-oqj] Add adjacency dict (per design: hawaii–marquesas; samoa–cook_islands, tonga, fiji; etc.) and fixed initial ownership (Red: hawaii, samoa, tonga, fiji; Blue: tahiti, marquesas, cook_islands, easter_island). Expose `neighbors(tid)` and initial ownership for game start.
- [ ] **A.3** [axis-97i] Refactor territory module: remove grid (GRID_ROWS, GRID_COLS, _GRID, `get_territory_at`, `get_position_of`). Implement `neighbors(tid)` and ownership from map data; keep `owner(tid)`, `set_owner(tid, team)` and apply initial ownership when the game starts. TerritoryId becomes string (or union of the 8 ids).

---

## Stream B — Game logic

Start after **Stream A** is done. (bd: axis-l4c)

- [ ] **B.1** [axis-l4c] Update game logic: valid_actions, state, actions, combat (if present) use only `ALL_TERRITORY_IDS`, `neighbors`, `owner`. Change win condition to “own all eight territories.” Ensure turn order and initial current team are consistent (e.g. Red first).

---

## Stream C — Tests & UI

Start after **Stream A** is done. C.1 can run in parallel with B.1. C.2 starts after **B.1**. (bd: axis-5cf, axis-vi5)

- [ ] **C.1** [axis-5cf] Tests: Replace grid layout tests with graph tests—all 8 territories exist, metadata present, adjacency matches design, initial ownership is Red = 4 west / Blue = 4 east, win when one team owns all 8. Keep or add tests for valid_attack_targets and combat flow with new territory set.
- [ ] **C.2** [axis-vi5] UI (minimal): Replace 2×2 grid drawing with a list or simple layout of the 8 territories (e.g. by region). Display owner and territory id/display_name; click selects territory by id for attack target. Map image and hit-test can be a follow-up.

---

## Beads (bd)

**Canonical stream:** Use these IDs for implementation. Order: A.1 → A.2 → A.3 → (B.1 ‖ C.1) → C.2.

| Stream | Bead ID  | Task |
|--------|----------|------|
| A.1    | axis-0fk | Define territory set and metadata |
| A.2    | axis-oqj | Add adjacency and initial ownership |
| A.3    | axis-97i | Refactor territory module off grid |
| B.1    | axis-l4c | Update game logic for 8 territories |
| C.1    | axis-5cf | Tests for graph, metadata, win |
| C.2    | axis-vi5 | UI list/layout and click to territory |

**Duplicate beads (close when using stream above):** axis-9z3, axis-h2d, axis-ibs, axis-2i7, axis-mlq overlap the same work; their descriptions point to the canonical IDs.

**Follow-up:** axis-3nd — Map image and hit-test (after C.2; P3).
