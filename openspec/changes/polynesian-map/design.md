# Polynesian Map — Design

## Context

Follow-on to territory-game: swap 2×2 grid for a fixed Polynesian map. Same combat and win rules; board and initial state are fully specified and identical every game.

## Goals / Non-goals

**Goals:**
- Exact territory set (Polynesian island groups) with explicit adjacency.
- Thematic, fixed initial ownership (e.g. west vs east).
- Per-territory metadata: `region`, `display_name` (and stable `id`).
- Every game starts in the same state.

**Non-goals:**
- No new mechanics; no randomness in setup.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Territory set | 8 territories: Hawaii, Samoa, Tonga, Fiji, Tahiti, Marquesas, Cook Islands, Easter Island | Covers Polynesia; 8 is enough for interesting play, small enough to specify and test. |
| Territory ID | Lowercase slug, e.g. `hawaii`, `samoa` | Stable, readable, no spaces. |
| Metadata | `region`, `display_name` on every territory | Region for grouping/UI; display_name for labels. |
| Adjacency | Explicit graph (see below) | Sea connections between island groups; no grid. |
| Initial ownership | Red: Hawaii, Samoa, Tonga, Fiji. Blue: Tahiti, Marquesas, Cook Islands, Easter Island. | Thematic west (Red) vs east (Blue); 4v4; fixed. |
| Start state | Single canonical initial state; no RNG | Reproducible games; same every time. |

## Exact territory set and metadata

| id | display_name | region |
|----|--------------|--------|
| hawaii | Hawaii | North Pacific |
| samoa | Samoa | Western Polynesia |
| tonga | Tonga | Western Polynesia |
| fiji | Fiji | Western Polynesia |
| tahiti | Tahiti | Eastern Polynesia |
| marquesas | Marquesas | Eastern Polynesia |
| cook_islands | Cook Islands | Southern Polynesia |
| easter_island | Easter Island | Eastern Polynesia |

## Adjacency (undirected; attack allowed between these pairs)

- **hawaii**: marquesas
- **samoa**: cook_islands, tonga, fiji
- **tonga**: samoa, fiji
- **fiji**: samoa, tonga
- **tahiti**: marquesas, cook_islands
- **marquesas**: hawaii, tahiti, easter_island
- **cook_islands**: tahiti, samoa
- **easter_island**: marquesas

```
        hawaii
           |
      marquesas ---- easter_island
        /    \
    tahiti   ...
      |   \
cook_islands  ...
      |
    samoa ---- fiji
      \   /
     tonga
```

## Initial ownership (fixed)

| Team | Territories |
|------|-------------|
| Red | hawaii, samoa, tonga, fiji |
| Blue | tahiti, marquesas, cook_islands, easter_island |

Turn order: Red moves first (or as already defined in territory-game; keep consistent).

## Data model (conceptual)

- **Territories**: List of `{ id, display_name, region }`. Order fixed (e.g. by id).
- **Adjacency**: `dict[id, list[id]]` or equivalent; both directions implied.
- **Ownership**: `dict[id, Team]`; at game start, set from table above.
- No `get_territory_at(row, col)`; no grid. UI uses id + metadata + (later) map art and hit-test.

## Risks / trade-offs

- 8 territories and fixed start may feel repetitive over many games; acceptable for v1; scenarios or variants can be a later change.
- Map art and hit-test are out of scope for this change’s core; graph + metadata first, then UI can be updated to use it.
