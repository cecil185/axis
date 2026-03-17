# Territory Game — Spec (Polynesian Map amendments)

## ADDED Requirements (this change)

### Requirement: Polynesian territory set
The board SHALL use the fixed Polynesian territory set of exactly eight territories with canonical ids: `hawaii`, `samoa`, `tonga`, `fiji`, `tahiti`, `marquesas`, `cook_islands`, `easter_island`. Each territory SHALL have metadata: `region` (string) and `display_name` (string). Adjacency SHALL be defined by an explicit graph (not a grid).

#### Scenario: Territory count and metadata
- **GIVEN** the game is started  
- **THEN** exactly eight territories exist  
- **AND** each territory has a unique id, a display_name, and a region

#### Scenario: Adjacency (Polynesian graph)
- **GIVEN** the game is started  
- **THEN** adjacency is: hawaii–marquesas; samoa–cook_islands, tonga, fiji; tonga–samoa, fiji; fiji–samoa, tonga; tahiti–marquesas, cook_islands; marquesas–hawaii, tahiti, easter_island; cook_islands–tahiti, samoa; easter_island–marquesas  
- **AND** each territory has at least one neighbor

### Requirement: Fixed initial ownership (thematic)
Initial ownership SHALL be fixed and identical every game. Red SHALL own: hawaii, samoa, tonga, fiji. Blue SHALL own: tahiti, marquesas, cook_islands, easter_island.

#### Scenario: Same start every game
- **WHEN** a new game is started  
- **THEN** Red owns exactly hawaii, samoa, tonga, fiji  
- **AND** Blue owns exactly tahiti, marquesas, cook_islands, easter_island  
- **AND** no randomness is used to determine initial ownership

### Requirement: Win condition (all territories)
The game SHALL end when one team owns all eight territories. That team SHALL be the winner.

#### Scenario: Victory
- **WHEN** after any change of ownership a team owns all eight territories  
- **THEN** the game ends and that team is the winner

## MODIFIED (from base spec)

- **Board and territories**: Replaced “four territories in a 2×2 grid” with “eight Polynesian territories and explicit adjacency graph.”
- **Initial ownership**: Replaced “two Red, two Blue (symmetric corners)” with fixed thematic west (Red) / east (Blue) as above.
- **Victory**: “All four” → “all eight” territories.
