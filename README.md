# agent-3

Territory grid (2×2) — Python + Pygame.

## Setup

```bash
poetry install
```

## Run the game

```bash
poetry run python -m src.game
# or: poetry run game
```

Closes on window close or Escape.

## Tests

```bash
poetry run pytest tests/ -v
```

## Docker / Make

```bash
make docker-build    # build image
make docker-test     # run tests in container
make docker-run      # run game in container (headless)
make docker-shell   # shell in container
```

## API (territory module)

- `ALL_TERRITORY_IDS` — tuple `("A", "B", "C", "D")`
- `GRID_ROWS`, `GRID_COLS` — both `2`
- `get_territory_at(row, col)` — territory ID at position, or `None` if out of bounds
- `get_position_of(tid)` — `(row, col)` for a territory ID, or `None`
- `neighbors(tid)` — list of adjacent territory IDs (orthogonal only; each territory has exactly two neighbors)

Territories: A = top-left, B = top-right, C = bottom-left, D = bottom-right.
