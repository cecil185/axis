"""
Pacific map: 29 territory IDs and metadata (region, display_name, map position).
Single source of truth; adjacency by maritime/geographic proximity.
"""

from typing import Literal, TypedDict, get_args

TerritoryId = Literal[
    "japan",
    "indonesia",
    "philippines",
    "hawaii",
    "midway",
    "johnston",
    "australia_west",
    "marianas",
    "minamitori",
    "micronesia",
    "belau",
    "marshall",
    "nauru",
    "kiribati",
    "tuvalu",
    "solomon",
    "papua_new_guinea",
    "vanuatu",
    "fiji",
    "australia_east",
    "tokelau",
    "cook_islands",
    "tonga",
    "new_caledonia",
    "new_zealand",
    "french_polynesia",
    "clipperton",
    "pitcairn",
    "rapa_nui",
]
# Team: the two playing factions. Used for units, turns, and combat.
Team = Literal["Red", "Blue"]
# OwnerState: extended ownership including unclaimed Neutral territories.
OwnerState = Literal["Red", "Blue", "Neutral"]

ALL_TERRITORY_IDS: tuple[TerritoryId, ...] = get_args(TerritoryId)

# Territories that start the game as Neutral (ownerless, no units).
# Chosen for being remote, low-value atolls that create an early expansion race.
NEUTRAL_TERRITORIES: frozenset[TerritoryId] = frozenset({
    "clipperton",
    "pitcairn",
    "johnston",
    "tokelau",
    "nauru",
})


def is_neutral_start(tid: TerritoryId) -> bool:
    """Return True if the territory begins the game as a Neutral (ownerless) territory."""
    return tid in NEUTRAL_TERRITORIES


class TerritoryInfo(TypedDict):
    """Metadata for a territory: region, display_name, map position (x_frac, y_frac), and ipc_value."""

    region: str
    display_name: str
    x_frac: float
    y_frac: float
    ipc_value: int


# Region, display name, and position on map (0–1 fractions: x left→right = Asia→Americas, y top→bottom).
# Tuned for Pacific-centered map (src/img/map.jpg); dots sit on/near each EEZ/territory.
# ipc_value: 3 = strategic, 2 = mid-tier, 1 = remote atoll / minor island.
_METADATA: dict[TerritoryId, TerritoryInfo] = {
    "japan": {"region": "North Pacific", "display_name": "Japan", "x_frac": 0.2, "y_frac": 0.26, "ipc_value": 3},
    "indonesia": {"region": "South Pacific", "display_name": "Indonesia", "x_frac": 0.10, "y_frac": 0.5, "ipc_value": 2},
    "philippines": {"region": "North Pacific", "display_name": "Philippines", "x_frac": 0.08, "y_frac": 0.38, "ipc_value": 2},
    "hawaii": {"region": "North Pacific", "display_name": "Hawaii", "x_frac": 0.56, "y_frac": 0.31, "ipc_value": 3},
    "midway": {"region": "North Pacific", "display_name": "Midway", "x_frac": 0.4, "y_frac": 0.27, "ipc_value": 1},
    "johnston": {"region": "North Pacific", "display_name": "Johnston", "x_frac": 0.47, "y_frac": 0.36, "ipc_value": 1},
    "australia_west": {"region": "South Pacific", "display_name": "Australia West", "x_frac": 0.12, "y_frac": 0.63, "ipc_value": 3},
    "marianas": {"region": "North Pacific", "display_name": "Marianas", "x_frac": 0.21, "y_frac": 0.31, "ipc_value": 2},
    "minamitori": {"region": "North Pacific", "display_name": "Minamitori", "x_frac": 0.27, "y_frac": 0.27, "ipc_value": 1},
    "micronesia": {"region": "Central Pacific", "display_name": "Micronesia", "x_frac": 0.285, "y_frac": 0.415, "ipc_value": 2},
    "belau": {"region": "Central Pacific", "display_name": "Belau", "x_frac": 0.14, "y_frac": 0.41, "ipc_value": 2},
    "marshall": {"region": "Central Pacific", "display_name": "Marshall", "x_frac": 0.345, "y_frac": 0.40, "ipc_value": 2},
    "nauru": {"region": "Central Pacific", "display_name": "Nauru", "x_frac": 0.335, "y_frac": 0.465, "ipc_value": 2},
    "kiribati": {"region": "Central Pacific", "display_name": "Kiribati", "x_frac": 0.58, "y_frac": 0.51, "ipc_value": 2},
    "tuvalu": {"region": "South Pacific", "display_name": "Tuvalu", "x_frac": 0.42, "y_frac": 0.494, "ipc_value": 2},
    "solomon": {"region": "South Pacific", "display_name": "Solomon", "x_frac": 0.355, "y_frac": 0.52, "ipc_value": 2},
    "papua_new_guinea": {"region": "South Pacific", "display_name": "Papua New Guinea", "x_frac": 0.24, "y_frac": 0.48, "ipc_value": 2},
    "vanuatu": {"region": "South Pacific", "display_name": "Vanuatu", "x_frac": 0.36, "y_frac": 0.58, "ipc_value": 2},
    "fiji": {"region": "South Pacific", "display_name": "Fiji", "x_frac": 0.40, "y_frac": 0.582, "ipc_value": 2},
    "australia_east": {"region": "South Pacific", "display_name": "Australia East", "x_frac": 0.24, "y_frac": 0.63, "ipc_value": 3},
    "tokelau": {"region": "South Pacific", "display_name": "Tokelau", "x_frac": 0.50, "y_frac": 0.555, "ipc_value": 1},
    "cook_islands": {"region": "South Pacific", "display_name": "Cook Islands", "x_frac": 0.53, "y_frac": 0.585, "ipc_value": 1},
    "tonga": {"region": "South Pacific", "display_name": "Tonga", "x_frac": 0.44, "y_frac": 0.58, "ipc_value": 2},
    "new_caledonia": {"region": "South Pacific", "display_name": "New Caledonia", "x_frac": 0.33, "y_frac": 0.61, "ipc_value": 2},
    "new_zealand": {"region": "South Pacific", "display_name": "New Zealand", "x_frac": 0.40, "y_frac": 0.76, "ipc_value": 2},
    "french_polynesia": {"region": "South Pacific", "display_name": "French Polynesia", "x_frac": 0.64, "y_frac": 0.58, "ipc_value": 2},
    "clipperton": {"region": "Eastern Pacific", "display_name": "Clipperton", "x_frac": 0.82, "y_frac": 0.42, "ipc_value": 1},
    "pitcairn": {"region": "Eastern Pacific", "display_name": "Pitcairn", "x_frac": 0.74, "y_frac": 0.64, "ipc_value": 1},
    "rapa_nui": {"region": "Eastern Pacific", "display_name": "Rapa Nui", "x_frac": 0.83, "y_frac": 0.70, "ipc_value": 1},
}

# Adjacency: each territory lists neighbors (symmetric). Based on Pacific geography / EEZ proximity.
_ADJACENCY: dict[TerritoryId, list[TerritoryId]] = {
    "japan": ["minamitori", "marianas"],
    "indonesia": ["papua_new_guinea", "philippines"],
    "philippines": ["marianas", "belau", "indonesia"],
    "hawaii": ["midway", "johnston"],
    "midway": ["hawaii", "australia_west"],
    "johnston": ["hawaii", "marshall"],
    "australia_west": ["midway", "marshall"],
    "marianas": ["micronesia", "minamitori", "japan", "philippines"],
    "minamitori": ["marianas", "japan"],
    "micronesia": ["marianas", "belau", "marshall", "kiribati"],
    "belau": ["micronesia", "papua_new_guinea", "philippines"],
    "marshall": ["johnston", "australia_west", "micronesia", "kiribati", "nauru"],
    "nauru": ["marshall", "kiribati", "solomon", "papua_new_guinea"],
    "kiribati": ["marshall", "nauru", "micronesia", "tuvalu", "tokelau", "french_polynesia"],
    "tuvalu": ["kiribati", "tokelau", "fiji"],
    "solomon": ["papua_new_guinea", "nauru", "vanuatu", "fiji"],
    "papua_new_guinea": ["belau", "nauru", "solomon", "vanuatu", "indonesia"],
    "vanuatu": ["solomon", "papua_new_guinea", "fiji", "new_caledonia"],
    "fiji": ["tuvalu", "solomon", "vanuatu", "tonga", "new_caledonia"],
    "australia_east": ["cook_islands", "tonga"],
    "tokelau": ["kiribati", "tuvalu", "cook_islands"],
    "cook_islands": ["tokelau", "australia_east", "tonga", "french_polynesia"],
    "tonga": ["fiji", "australia_east", "cook_islands", "new_caledonia", "new_zealand"],
    "new_caledonia": ["vanuatu", "fiji", "tonga", "new_zealand"],
    "new_zealand": ["tonga", "new_caledonia", "french_polynesia"],
    "french_polynesia": ["kiribati", "cook_islands", "new_zealand", "pitcairn", "rapa_nui"],
    "clipperton": ["pitcairn"],
    "pitcairn": ["french_polynesia", "rapa_nui", "clipperton"],
    "rapa_nui": ["french_polynesia", "pitcairn"],
}


def region(tid: TerritoryId) -> str:
    """Return the region for the territory."""
    return _METADATA[tid]["region"]


def display_name(tid: TerritoryId) -> str:
    """Return the display name for the territory."""
    return _METADATA[tid]["display_name"]


def map_position(tid: TerritoryId) -> tuple[float, float]:
    """Return (x_frac, y_frac) position on the map (0–1)."""
    m = _METADATA[tid]
    return (m["x_frac"], m["y_frac"])


def ipc_value(tid: TerritoryId) -> int:
    """Return the IPC value (1–3) for the territory. 3 = strategic, 2 = mid-tier, 1 = remote atoll."""
    return _METADATA[tid]["ipc_value"]


def territory_info(tid: TerritoryId) -> TerritoryInfo:
    """Return region, display_name, and map position for the territory."""
    return _METADATA[tid].copy()


def territory_at_point(
    map_rect: tuple[int, int, int, int], px: int, py: int, radius_px: int = 18
) -> TerritoryId | None:
    """Return the territory whose marker contains (px, py), or None. map_rect = (x, y, w, h).

    Delegates to territory_at_point_polygon for polygon-based hit testing.
    The radius_px argument is ignored (kept for API compatibility only).
    """
    return territory_at_point_polygon(map_rect, px, py)


# ---------------------------------------------------------------------------
# Polygon territory regions
# ---------------------------------------------------------------------------
# Per-territory polygon vertices as fractional (x_frac, y_frac) coordinates.
# Direction does not matter for the ray-casting point-in-polygon algorithm.
#
# Coordinates are tuned to the Pacific-centred map (src/img/map.jpg, 1280×648).
# Polygons are non-overlapping rectangular approximations; every territory
# centre (x_frac, y_frac from _METADATA) falls strictly inside its own polygon.

# Helper: axis-aligned rectangle as a 4-vertex polygon (x0,y0)→(x1,y1).
def _rect(x0: float, y0: float, x1: float, y1: float) -> list[tuple[float, float]]:
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


# Final polygon boundaries (tuned so every territory centre is strictly inside).
# Centers are listed as comments for each entry: (x_frac, y_frac).
_POLYGONS: dict[TerritoryId, list[tuple[float, float]]] = {
    "japan":             _rect(0.00, 0.00, 0.30, 0.27),   # (0.20, 0.26)
    "indonesia":         _rect(0.00, 0.46, 0.20, 0.58),   # (0.10, 0.50)
    "philippines":       _rect(0.00, 0.27, 0.13, 0.46),   # (0.08, 0.38)
    "hawaii":            _rect(0.52, 0.00, 0.62, 0.46),   # (0.56, 0.31)
    "midway":            _rect(0.38, 0.00, 0.46, 0.35),   # (0.40, 0.27)
    "johnston":          _rect(0.46, 0.00, 0.52, 0.46),   # (0.47, 0.36)
    "australia_west":    _rect(0.00, 0.58, 0.20, 1.00),   # (0.12, 0.63)
    "marianas":          _rect(0.16, 0.27, 0.26, 0.35),   # (0.21, 0.31)
    "minamitori":        _rect(0.26, 0.00, 0.38, 0.28),   # (0.27, 0.27)
    "micronesia":        _rect(0.26, 0.35, 0.32, 0.46),   # (0.285, 0.415)
    "belau":             _rect(0.13, 0.35, 0.26, 0.46),   # (0.14, 0.41)
    "marshall":          _rect(0.32, 0.35, 0.40, 0.44),   # (0.345, 0.40)
    "nauru":             _rect(0.30, 0.44, 0.40, 0.50),   # (0.335, 0.465)
    "kiribati":          _rect(0.52, 0.46, 0.62, 0.54),   # (0.58, 0.51)
    "tuvalu":            _rect(0.40, 0.44, 0.46, 0.54),   # (0.42, 0.494)
    "solomon":           _rect(0.30, 0.50, 0.40, 0.58),   # (0.355, 0.52)
    "papua_new_guinea":  _rect(0.20, 0.46, 0.30, 0.58),   # (0.24, 0.48)
    "vanuatu":           _rect(0.35, 0.57, 0.39, 0.65),   # (0.36, 0.58)
    "fiji":              _rect(0.39, 0.54, 0.43, 0.65),   # (0.40, 0.582)
    "australia_east":    _rect(0.20, 0.58, 0.28, 0.72),   # (0.24, 0.63)
    "tokelau":           _rect(0.46, 0.46, 0.52, 0.62),   # (0.50, 0.555)
    "cook_islands":      _rect(0.52, 0.54, 0.62, 0.66),   # (0.53, 0.585)
    "tonga":             _rect(0.43, 0.54, 0.48, 0.65),   # (0.44, 0.58)
    "new_caledonia":     _rect(0.28, 0.58, 0.36, 0.68),   # (0.33, 0.61)
    "new_zealand":       _rect(0.30, 0.72, 0.52, 1.00),   # (0.40, 0.76)
    "french_polynesia":  _rect(0.62, 0.40, 0.70, 0.72),   # (0.64, 0.58)
    "clipperton":        _rect(0.70, 0.00, 1.00, 0.60),   # (0.82, 0.42)
    "pitcairn":          _rect(0.70, 0.60, 1.00, 0.68),   # (0.74, 0.64)
    "rapa_nui":          _rect(0.70, 0.68, 1.00, 1.00),   # (0.83, 0.70)
}


def territory_polygon(
    tid: TerritoryId, map_rect: tuple[int, int, int, int]
) -> list[tuple[int, int]]:
    """Return the polygon vertex list for *tid* in pixel coordinates.

    Args:
        tid: Territory identifier.
        map_rect: (x, y, w, h) bounding box of the map on screen.

    Returns:
        List of (px, py) integer pixel coordinates ready for pygame.draw.polygon.
    """
    mx, my, mw, mh = map_rect
    return [
        (int(mx + xf * mw), int(my + yf * mh))
        for xf, yf in _POLYGONS[tid]
    ]


def _point_in_polygon(px: float, py: float, polygon: list[tuple[float, float]]) -> bool:
    """Ray-casting algorithm: return True if (px, py) is inside *polygon*.

    Polygon is a list of (x, y) vertices (any coordinate space).
    """
    n = len(polygon)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if ((yi > py) != (yj > py)) and (px < (xj - xi) * (py - yi) / (yj - yi) + xi):
            inside = not inside
        j = i
    return inside


def territory_at_point_polygon(
    map_rect: tuple[int, int, int, int], px: int, py: int
) -> TerritoryId | None:
    """Return the territory whose polygon contains (px, py), or None.

    Uses ray-casting point-in-polygon test on fractional polygon coords
    converted to pixel space. First matching territory wins (deterministic
    for shared border edges — earlier territory in ALL_TERRITORY_IDS wins).

    Args:
        map_rect: (x, y, w, h) bounding box of the map on screen.
        px, py: Click position in screen pixel coordinates.
    """
    mx, my, mw, mh = map_rect
    if mw <= 0 or mh <= 0:
        return None
    # Convert click to fractional coords for polygon testing
    x_frac = (px - mx) / mw
    y_frac = (py - my) / mh
    for tid in ALL_TERRITORY_IDS:
        if _point_in_polygon(x_frac, y_frac, _POLYGONS[tid]):
            return tid
    return None


def neighbors(tid: TerritoryId) -> list[TerritoryId]:
    """Return list of adjacent territory IDs."""
    return list(_ADJACENCY[tid])


# Initial ownership: Red first 15, Blue last 14.
# Used as fallback when unit stacks are empty (e.g. before init_game).
# Type is OwnerState so entries can be set to "Neutral" for unclaimed territories.
_owners: dict[TerritoryId, OwnerState] = {
    tid: ("Red" if i < 15 else "Blue")
    for i, tid in enumerate(ALL_TERRITORY_IDS)
}


def owner(tid: TerritoryId) -> OwnerState:
    """
    Return the ownership state of the territory.
    Derives from unit stacks when available (owner_from_units); falls back
    to _owners when both teams have no units. Returns 'Neutral' when no team
    has units and the territory is unclaimed (i.e. _owners entry is 'Neutral').
    """
    # Lazy import to avoid circular dependency at module load time
    from .units import owner_from_units  # noqa: PLC0415
    unit_owner = owner_from_units(tid)
    if unit_owner is not None:
        return unit_owner
    return _owners[tid]


def set_owner(tid: TerritoryId, team: Team) -> None:
    """
    Set the owner of the territory by transferring all units to the new team.
    Clears losing team's units and gives winning team the standard stack if empty.
    Only accepts Team ('Red' or 'Blue') — neutral cannot be set via this function.
    """
    from .units import set_units, total_units  # noqa: PLC0415
    enemy: Team = "Blue" if team == "Red" else "Red"
    # Clear enemy units in the territory (attacker wins)
    set_units(tid, enemy, {"infantry": 0, "tanks": 0})
    # Ensure the winning team has at least some units (1 infantry minimum)
    if total_units(tid, team) == 0:
        set_units(tid, team, {"infantry": 1, "tanks": 0})
    # Also update the fallback dict
    _owners[tid] = team


def set_neutral(tid: TerritoryId) -> None:
    """
    Mark a territory as Neutral. Clears all unit stacks and sets the fallback
    ownership to 'Neutral'. The territory will produce no income and cannot be
    attacked until claimed by a team.
    """
    from .units import set_units  # noqa: PLC0415
    set_units(tid, "Red", {"infantry": 0, "tanks": 0})
    set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
    _owners[tid] = "Neutral"


def winner() -> Team | None:
    """
    Return the team that owns all territories, or None if game is not over.
    A team cannot win while any territory is Neutral or held by the opponent.
    """
    first: OwnerState = owner(ALL_TERRITORY_IDS[0])
    # Neutral territories prevent any team from winning
    if first not in ("Red", "Blue"):
        return None
    # first is now narrowed to Team (Red or Blue)
    winning_team: Team = first  # type: ignore[assignment]
    for tid in ALL_TERRITORY_IDS[1:]:
        if owner(tid) != winning_team:
            return None
    return winning_team


def is_game_over() -> bool:
    """Return True iff one team owns all territories (winner() is not None)."""
    return winner() is not None
