# Territory Game — Design

## Context

Spec-driven change for a minimal 2D territory battle game: 4 territories, 2 teams, turn-based, attack/skip, dice combat. Tech stack: Python; domain: 2D video game.

## Goals / Non-Goals

**Goals:**
- Clear game state (board, ownership, current turn).
- One attack per turn; combat by 1v1 dice; defender wins ties.
- Win when one team controls all 4 territories.

**Non-Goals:**
- No unit counts, reinforcements, or movement. No persistence, AI, or network multiplayer.

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Board shape | 2×2 grid (A–B, C–D; A–C, B–D edges) | Simple, symmetric, each territory has 2 neighbors. |
| Combat | 1 die each; higher wins; tie → defender | Simple, no extra rules. |
| Actions per turn | Exactly one: attack or skip | Keeps turns fast and clear. |
| Initial setup | Red: A,D or A,C; Blue: the other two | Symmetric; e.g. Red corners vs Blue corners. |
| Ownership model | Single owner per territory (no unit count) | Territory “flips” to winner’s color only. |

## Risks / Trade-offs

- Single attack per turn can make games longer; acceptable for v1.
- No undo/history in spec; can be added later if needed.
