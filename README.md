# agent-3

Pacific map (30 territories) — Python + Pygame. Uses `src/img/map.jpg` as background; territories are clickable markers.

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

## Make

```bash
make install   # install deps (via poetry)
make test      # run tests
make run       # run the game
make shell     # bash in poetry env
make clean     # remove build artifacts
```

## API (territory module)

- `ALL_TERRITORY_IDS` — tuple of 30 territory IDs
- `map_position(tid)` — `(x_frac, y_frac)` position on the map (0–1)
- `territory_at_point(map_rect, px, py, radius_px)` — territory whose marker contains the point, or `None`
- `neighbors(tid)` — list of adjacent territory IDs (adjacency data as defined in territory data)
- `owner(tid)`, `set_owner(tid, team)` — ownership; `region(tid)`, `display_name(tid)` — metadata
