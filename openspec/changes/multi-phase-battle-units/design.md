# Multi-Phase Battle Units — Design

## Context

The territory game currently has four territories, two teams, turn-based attack/skip, and single-roll dice combat. We are adding two unit types (infantry, tanks) with health and defense, and replacing instant combat with multi-phase combat where either side may retreat after each phase. UI must show units and combat state at every step.

## Goals / Non-Goals

**Goals:**
- Per-territory unit stacks: infantry and tanks with numeric health and defense (Axis & Allies style).
- Combat as a sequence of phases: each phase applies damage to both sides; after each phase, attacker and defender can choose to continue or retreat.
- UI: display unit counts and types on the board; during combat show phase number, rolls, damage, remaining units; after each phase show "Continue" / "Retreat" with clear outcome.

**Non-Goals:**
- No movement of units between friendly territories; no new unit types; no persistence of combat log beyond current battle.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Unit stats | Infantry: 1 health, 1 defense; Tanks: 2 health, 2 defense (or 1/2, 2/3—tune in impl) | Simple A&A-like differentiation; exact numbers can be constants. |
| Territory state | Owner + counts per type (e.g. `{infantry: n, tanks: m}`) | Owner derived from who has units; empty territory is neutral or reverts. |
| Combat phase flow | Roll for attacker and defender → apply damage to units (by type) → check eliminated → offer retreat/continue | One "round" per phase; damage reduces unit health; when a type reaches 0 it is removed. |
| Who can retreat | Attacker and defender each choose after phase (e.g. defender first, then attacker, or simultaneous choice) | Reduces complexity to "after phase, either side can retreat"; if both continue, next phase. |
| Retreat outcome | Combat ends; no ownership change; turn ends | Attacker returns to origin territory (no unit loss beyond what happened in phases). |
| Game start conditions | Fixed initial unit counts per territory (e.g. 2 infantry, 1 tank on every territory at start) | Deterministic, symmetric start; same set number on each territory so no territory is empty and balance is even. |
| UI surface | Same runner (e.g. terminal or minimal 2D): board shows units; combat sub-flow prompts phase result then Continue/Retreat | Keeps one entry point; each step emits clear state for UI to render. |

## Risks / Trade-offs

- **Multi-phase can lengthen battles** → Cap phases or allow quick "resolve all" option in a later iteration; v1 is explicit phase-by-phase.
- **UI and game logic coupling** → Expose clear state (e.g. `get_combat_state()`, `get_board_state()`) so UI only displays; no game logic in UI layer.
- **Retreat semantics** → Define whether retreating attacker keeps surviving units in origin; spec: attacker keeps remaining units in source territory, defender keeps remaining in contested territory.

## Migration Plan

- Implement in feature branch: add unit model and phased combat alongside existing combat; then switch game to use new combat and unit-aware ownership. No data migration (no persistence yet). Rollback: revert to single-roll combat and ignore unit counts if needed.

## Open Questions

- Exact infantry/tank attack and defense values (e.g. 1/1 and 2/2, or 1/2 and 2/3) to be fixed in implementation; design keeps them configurable.
