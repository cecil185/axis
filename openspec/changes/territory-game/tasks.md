# Territory Game — Tasks

Tasks are ordered by dependency. Each task is at most ~2 hours. Implement in order; blocked tasks list their dependencies.

---

## Dependencies (blocker → blocked)

| Task | Depends on | Description |
|------|------------|-------------|
| 1.2 | 1.1 | Adjacency needs territory IDs |
| 1.3 | 1.1, 1.2 | Ownership needs board shape |
| 2.1 | 1.3 | Turn state needs ownership + teams |
| 2.2 | 2.1 | Valid actions need current player + adjacency |
| 2.3 | 2.2 | Execute skip/attack from valid choices |
| 3.1 | 2.3 | Combat invoked when attack is chosen |
| 3.2 | 3.1 | Resolve dice and transfer ownership |
| 4.1 | 3.2 | Win check after ownership change |
| 4.2 | 4.1 | Game loop: turn → action → combat/win → next |
| 5.1 | 4.2 | Runner/UI consumes game loop |

---

## 1. Board and territories

- [ ] **1.1** Define territory IDs and 2×2 grid (A top-left, B top-right, C bottom-left, D bottom-right). Expose list of territories and grid layout (no adjacency yet).
- [ ] **1.2** Implement adjacency: each territory has exactly two neighbors (orthogonal only). Provide API: `neighbors(territory_id)` → list of territory ids.
- [ ] **1.3** Add ownership: each territory has one owner (Red or Blue). Initial state: e.g. Red = A, D; Blue = B, C. API: `owner(territory_id)`, `set_owner(territory_id, team)`.

## 2. Turn and actions

- [ ] **2.1** Turn state: current team (Red or Blue). API: `current_team()`, `end_turn()` (flip current team). No actions yet.
- [ ] **2.2** Valid actions: given current team, compute (1) list of enemy territories that are adjacent to any territory owned by current team (valid attack targets), (2) option to skip. API: `valid_attack_targets()`, `can_skip()`.
- [ ] **2.3** Execute action: `skip()` (just call `end_turn()`), `attack(target_territory_id)` (validate target then invoke combat; do not resolve combat in this task—stub or callback). After action, turn ends.

## 3. Combat

- [ ] **3.1** Combat input: attacker team, defender team, contested territory id. Roll one die (1–6) for each side; return rolls (e.g. for tests, support seeded or injectable RNG).
- [ ] **3.2** Resolve combat: compare rolls; if attacker > defender, set territory owner to attacker; else leave owner unchanged. Tie → defender wins. After resolve, end turn (current player flips).

## 4. Win condition and game loop

- [ ] **4.1** Win check: if any team owns all four territories, game over. API: `winner()` → team or None, `is_game_over()`.
- [ ] **4.2** Game loop: after each action (and combat if attack), check `is_game_over()`; if not over, next player’s turn. Ensure turn alternation and that no actions are allowed when game is over.

## 5. Runner / minimal interface

- [ ] **5.1** Minimal runnable game: start game, loop (show board + current team, prompt attack or skip; if attack, choose valid target; roll dice and show result; repeat until winner). Terminal or minimal 2D UI acceptable.
