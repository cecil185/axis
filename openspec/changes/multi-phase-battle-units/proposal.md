# Multi-Phase Battle Units — Proposal

## Why

Extend the territory game with distinct unit types (infantry, tanks) and phased combat so battles feel tactical: players see health/defense and can choose to retreat. UI must reflect each phase so decisions are clear.

## What Changes

- **Unit types**: Two types—infantry and tanks—each with health and defense values (Axis & Allies style). Territories hold stacks of units by type.
- **Game start**: At game start, each territory SHALL have a set number of units per type (e.g. fixed counts such as 2 infantry, 1 tank per territory), so initial state is deterministic and symmetric.
- **Combat**: Multi-phase. Each phase: both sides roll/apply damage; after a phase, attacker or defender may **retreat** (combat ends, no ownership change) or continue. Repeat until one side has no units or someone retreats.
- **UI**: Show unit counts and types per territory; during combat show phase, rolls, damage, remaining units; after each phase offer "Continue" / "Retreat" with clear state.

### Modified Capabilities

- `territory-game`: Add unit types (infantry, tanks) with health/defense; replace single-roll combat with multi-phase combat and retreat option; require UI to display units and combat phases/choices at each step.

## Non-goals

- No more than two unit types. No movement of units between territories (attack only). No persistence of battle history beyond current game state.

## Impact

Game state and combat logic change; all combat and turn flows touch UI. Existing territory-game code and any minimal UI must be updated for units and phased combat flows.
