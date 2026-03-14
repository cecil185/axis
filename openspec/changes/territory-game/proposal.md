# Territory Game — Proposal

## Why

Introduce a minimal 2D board game: two teams fight over four territories; turn-based, dice-based combat, territory ownership flips to the winner. Good scope for learning game loop, state, and UI.

## What Changes

- New game: 4 territories (2×2 grid), 2 teams (e.g. Red vs Blue).
- Turn-based: each turn a player chooses **attack** (adjacent enemy) or **skip**.
- Combat: 1v1 dice; higher roll wins; defender wins ties. Winning team takes the territory (color change).
- Win: one team controls all 4 territories.

## Capabilities

### New Capabilities
- `territory-game`: Core game loop (board, teams, turns, attack/skip, dice combat, win condition).

### Modified Capabilities
- (none)

## Non-goals

- No unit counts or reinforcements; one ownership per territory.
- No persistence, AI, or multiplayer beyond local turn-taking.
- No diagonal attacks; only orthogonally adjacent territories.

## Impact

New Python game module; optional simple 2D UI (e.g. terminal or minimal graphics). No existing code modified.
