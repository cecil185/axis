# Territory Game — Spec

## ADDED Requirements

### Requirement: Unit types
The game SHALL have exactly two unit types: **infantry** and **tanks**. Each type SHALL have a numeric **health** and **defense** value (Axis & Allies style). Territories SHALL hold stacks of units per type (e.g. counts of infantry and tanks).

#### Scenario: Unit type stats
- **WHEN** the game defines unit types
- **THEN** infantry and tanks each have defined health and defense values used in combat

#### Scenario: Territory unit stacks
- **WHEN** a territory is queried
- **THEN** it SHALL expose unit counts per type (infantry count, tank count) and owner is the team that has units there

### Requirement: Game start conditions
At game start, each territory SHALL be assigned a set number of units per type (e.g. 2 infantry, 1 tank). The counts SHALL be fixed and identical for every territory so the initial board is deterministic and symmetric.

#### Scenario: Initial unit counts
- **WHEN** the game starts
- **THEN** each territory SHALL have the defined initial unit counts per type (e.g. 2 infantry, 1 tank on each), with two territories owned by each team

### Requirement: Combat retreat
During combat, after each phase the attacker and the defender SHALL each have the option to **retreat**. If either chooses retreat, combat SHALL end immediately with no ownership change; surviving units remain in place and the turn SHALL end.

#### Scenario: Attacker retreats
- **WHEN** after a combat phase the attacker chooses retreat
- **THEN** combat ends, contested territory ownership unchanged, attacker’s surviving units remain in source territory, turn ends

#### Scenario: Defender retreats
- **WHEN** after a combat phase the defender chooses retreat
- **THEN** combat ends, contested territory ownership unchanged, defender’s surviving units remain in contested territory, turn ends

### Requirement: UI — units and combat phases
The runner or UI SHALL display unit counts and types per territory. During combat the UI SHALL show the current phase, rolls, damage applied, and remaining units for each side. After each phase the UI SHALL offer the choices "Continue" and "Retreat" with clear resulting state.

#### Scenario: Board shows units
- **WHEN** the board is displayed
- **THEN** each territory SHALL show owner and unit counts by type (e.g. infantry, tanks)

#### Scenario: Combat phase display
- **WHEN** a combat phase is in progress or just resolved
- **THEN** the UI SHALL show phase number, rolls, damage, and remaining units for attacker and defender

#### Scenario: Retreat/Continue choice
- **WHEN** a combat phase has ended and combat is not resolved (both sides have units)
- **THEN** the UI SHALL present "Continue" and "Retreat" (or equivalent) so the player(s) can choose; the choice SHALL be reflected in the next state shown

## MODIFIED Requirements

### Requirement: Team ownership
Each territory MUST be owned by exactly one of two teams (e.g. Red, Blue). Ownership SHALL be determined by which team has units in the territory; a territory with no units SHALL have no owner or a neutral state. Ownership SHALL be represented (e.g. by color or team id). Each territory SHALL also expose unit counts per type (infantry, tanks).

#### Scenario: Initial ownership
- **WHEN** the game starts
- **THEN** two territories are Red and two are Blue (one team per pair of opposite corners or similar symmetric split), each with the same set number of units per type as defined by game start conditions

#### Scenario: Ownership and units
- **WHEN** a territory is queried
- **THEN** owner and unit counts by type (infantry, tanks) are exposed

### Requirement: Turn actions
On their turn, the current player MUST choose exactly one action: **attack** or **skip**. Skip SHALL end the turn with no other effect. Attack MUST target one adjacent territory owned by the opponent; combat SHALL use the attacker’s units in the attacking territory and the defender’s units in the target territory.

#### Scenario: Skip
- **WHEN** the current player chooses skip
- **THEN** no combat occurs and the turn ends (other team’s turn)

#### Scenario: Attack target validity
- **WHEN** the current player chooses attack
- **THEN** they must select a territory that is (1) adjacent to at least one territory they own and (2) owned by the opponent; otherwise the choice is invalid

### Requirement: Combat resolution
Combat SHALL be multi-phase. Each phase: both sides roll (e.g. dice); damage SHALL be applied to units according to unit type health/defense; units reduced to zero SHALL be removed. After each phase, if both sides still have units, attacker and defender SHALL each choose to continue or retreat. If either retreats, combat ends with no ownership change and turn ends. If both continue, another phase runs. If one side has no units remaining, the other side SHALL gain ownership of the contested territory and the turn SHALL end.

#### Scenario: Attacker eliminates defender
- **WHEN** after a combat phase the defender has no units remaining
- **THEN** the contested territory becomes owned by the attacker’s team (attacker’s surviving units move or are placed there as designed), and the turn ends

#### Scenario: Defender eliminates attacker
- **WHEN** after a combat phase the attacker has no units remaining (e.g. all lost in combat)
- **THEN** ownership of the contested territory does not change, and the turn ends

#### Scenario: Retreat ends combat
- **WHEN** after a combat phase either side chooses retreat
- **THEN** combat ends, no ownership change, surviving units remain, turn ends

#### Scenario: Continue to next phase
- **WHEN** after a combat phase both sides have units and both choose continue
- **THEN** another combat phase runs (roll, apply damage, then again offer continue/retreat or resolve elimination)
