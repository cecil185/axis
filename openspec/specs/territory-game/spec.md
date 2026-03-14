# Territory Game — Spec

## ADDED Requirements

### Requirement: Board and territories
The game SHALL have exactly four territories in a 2×2 grid. Each territory MUST have a unique id (e.g. A, B, C, D). Adjacency SHALL be orthogonal only: A–B, A–C, B–D, C–D (no diagonals).

#### Scenario: Board layout
- **WHEN** the game starts
- **THEN** four territories exist with correct adjacency (each has 2 neighbors)

### Requirement: Team ownership
Each territory MUST be owned by exactly one of two teams (e.g. Red, Blue). Ownership SHALL be represented (e.g. by color or team id).

#### Scenario: Initial ownership
- **WHEN** the game starts
- **THEN** two territories are Red and two are Blue (one team per pair of opposite corners or similar symmetric split)

### Requirement: Turn order
Play SHALL be turn-based. One team MUST be the current player; after a turn, the other team SHALL become current.

#### Scenario: Turn alternation
- **WHEN** the current player ends their turn (attack or skip)
- **THEN** the other team becomes the current player

### Requirement: Turn actions
On their turn, the current player MUST choose exactly one action: **attack** or **skip**. Skip SHALL end the turn with no other effect. Attack MUST target one adjacent territory owned by the opponent.

#### Scenario: Skip
- **WHEN** the current player chooses skip
- **THEN** no combat occurs and the turn ends (other team’s turn)

#### Scenario: Attack target validity
- **WHEN** the current player chooses attack
- **THEN** they must select a territory that is (1) adjacent to at least one territory they own and (2) owned by the opponent; otherwise the choice is invalid

### Requirement: Combat resolution
Combat SHALL be resolved by each side rolling one die (1–6). Higher roll MUST win. If tied, the defender MUST win. The winner gains ownership of the contested territory (it changes to the winner’s team). The turn then ends.

#### Scenario: Attacker wins
- **WHEN** attacker rolls higher than defender
- **THEN** the attacked territory becomes owned by the attacker’s team and the turn ends

#### Scenario: Defender wins or tie
- **WHEN** defender rolls higher or equal
- **THEN** ownership does not change and the turn ends

### Requirement: Win condition
The game SHALL end when one team owns all four territories. That team MUST be the winner.

#### Scenario: Victory
- **WHEN** after any change of ownership a team owns all four territories
- **THEN** the game ends and that team is the winner
