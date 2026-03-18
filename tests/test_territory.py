from src.state import TEAMS
from src.territory import (
    ALL_TERRITORY_IDS,
    display_name,
    ipc_value,
    map_position,
    territory_at_point,
    neighbors,
    owner,
    OwnerState,
    region,
    set_owner,
    territory_info,
    TerritoryId,
    winner,
    is_game_over,
)
from src.units import set_units

RED, BLUE = TEAMS[0], TEAMS[1]


def test_exposes_thirty_territory_ids() -> None:
    assert len(ALL_TERRITORY_IDS) == 29
    assert "hawaii" in ALL_TERRITORY_IDS
    assert "japan" in ALL_TERRITORY_IDS
    assert "rapa_nui" in ALL_TERRITORY_IDS
    assert "french_polynesia" in ALL_TERRITORY_IDS


def test_region_returns_region_for_each_territory() -> None:
    assert region("hawaii") == "North Pacific"
    assert region("fiji") == "South Pacific"
    assert region("rapa_nui") == "Eastern Pacific"


def test_display_name_returns_display_name_for_each_territory() -> None:
    assert display_name("hawaii") == "Hawaii"
    assert display_name("cook_islands") == "Cook Islands"
    assert display_name("papua_new_guinea") == "Papua New Guinea"


def test_territory_info_includes_region_display_name_and_position() -> None:
    info = territory_info("fiji")
    assert info["region"] == "South Pacific"
    assert info["display_name"] == "Fiji"
    assert "x_frac" in info and "y_frac" in info
    assert 0 <= info["x_frac"] <= 1 and 0 <= info["y_frac"] <= 1


def test_map_position_returns_fractions_in_range() -> None:
    for tid in ALL_TERRITORY_IDS:
        x, y = map_position(tid)
        assert 0 <= x <= 1 and 0 <= y <= 1


def test_territory_at_point_returns_territory_when_click_in_marker() -> None:
    # Map rect (x, y, w, h); marker for hawaii at (0.56, 0.31) per territory metadata
    map_rect = (0, 0, 1000, 500)
    cx = int(0 + 0.56 * 1000)
    cy = int(0 + 0.31 * 500)
    assert territory_at_point(map_rect, cx, cy, radius_px=20) == "hawaii"


def test_territory_at_point_returns_none_when_far_from_markers() -> None:
    map_rect = (0, 0, 1000, 500)
    assert territory_at_point(map_rect, 10, 10, radius_px=18) is None


def test_neighbors_returns_adjacent_territories_symmetric() -> None:
    """Each territory has a list of neighbors; adjacency is symmetric (if A borders B, B borders A)."""
    for tid in ALL_TERRITORY_IDS:
        adj = neighbors(tid)
        assert isinstance(adj, list)
        for n in adj:
            assert n in ALL_TERRITORY_IDS, f"{tid} neighbor {n} not in ALL_TERRITORY_IDS"
            assert tid in neighbors(n), f"adjacency not symmetric: {tid} -> {n} but {n} -/-> {tid}"


def test_initial_ownership_red_owns_first_fifteen() -> None:
    for i, tid in enumerate(ALL_TERRITORY_IDS[:15]):
        assert owner(tid) == RED, f"{tid} should be Red"


def test_initial_ownership_blue_owns_last_fourteen() -> None:
    for tid in ALL_TERRITORY_IDS[15:]:
        assert owner(tid) == BLUE, f"{tid} should be Blue"


def test_set_owner_updates_ownership() -> None:
    set_owner("hawaii", BLUE)
    assert owner("hawaii") == BLUE
    set_owner("hawaii", RED)
    assert owner("hawaii") == RED


def test_is_game_over_false_when_split() -> None:
    assert not is_game_over()


def test_is_game_over_true_when_one_team_owns_all() -> None:
    for tid in ALL_TERRITORY_IDS:
        set_owner(tid, RED)
    try:
        assert is_game_over()
    finally:
        for i, tid in enumerate(ALL_TERRITORY_IDS):
            set_owner(tid, RED if i < 15 else BLUE)


def test_winner_returns_none_when_not_game_over() -> None:
    assert winner() is None


def test_winner_returns_team_when_owns_all() -> None:
    for tid in ALL_TERRITORY_IDS:
        set_owner(tid, RED)
    try:
        assert winner() == RED
        for tid in ALL_TERRITORY_IDS:
            set_owner(tid, BLUE)
        assert winner() == BLUE
    finally:
        for i, tid in enumerate(ALL_TERRITORY_IDS):
            set_owner(tid, RED if i < 15 else BLUE)


# --- Neutral ownership tests ---


def test_set_owner_neutral_clears_units_and_sets_neutral() -> None:
    """Setting a territory to Neutral clears all units and owner() returns 'Neutral'."""
    set_owner("hawaii", "Neutral")
    try:
        assert owner("hawaii") == "Neutral"
    finally:
        set_owner("hawaii", RED)


def test_owner_returns_neutral_when_no_units_and_fallback_neutral() -> None:
    """When both teams have 0 units and fallback is Neutral, owner() returns 'Neutral'."""
    set_units("hawaii", "Red", {"infantry": 0, "tanks": 0})
    set_units("hawaii", "Blue", {"infantry": 0, "tanks": 0})
    set_owner("hawaii", "Neutral")
    try:
        assert owner("hawaii") == "Neutral"
    finally:
        set_owner("hawaii", RED)


# --- IPC value tests ---


def test_ipc_value_strategic_territories_worth_3() -> None:
    """Strategic territories (japan, hawaii, australia_east, australia_west) are worth 3 IPCs."""
    for tid in ("japan", "hawaii", "australia_east", "australia_west"):
        assert ipc_value(tid) == 3, f"{tid} should be worth 3 IPCs"


def test_ipc_value_all_territories_in_range_1_to_3() -> None:
    """Every territory has an IPC value between 1 and 3."""
    for tid in ALL_TERRITORY_IDS:
        v = ipc_value(tid)
        assert 1 <= v <= 3, f"{tid} ipc_value={v} out of range 1–3"


def test_ipc_value_remote_atolls_worth_1() -> None:
    """Remote atolls and minor islands are worth 1 IPC."""
    for tid in ("johnston", "minamitori", "belau", "nauru", "tuvalu", "tokelau",
                "clipperton", "pitcairn", "rapa_nui"):
        assert ipc_value(tid) == 1, f"{tid} should be worth 1 IPC"


def test_ipc_value_mid_tier_worth_2() -> None:
    """Mid-tier territories are worth 2 IPCs."""
    for tid in ("indonesia", "philippines", "midway", "marshall", "fiji", "new_zealand"):
        assert ipc_value(tid) == 2, f"{tid} should be worth 2 IPCs"


def test_territory_info_includes_ipc_value() -> None:
    """territory_info() includes ipc_value in the returned dict."""
    info = territory_info("japan")
    assert "ipc_value" in info
    assert info["ipc_value"] == 3


def test_winner_none_when_neutral_territory_exists() -> None:
    """Game cannot be won if any territory is Neutral."""
    set_owner("rapa_nui", "Neutral")
    try:
        # Even if all others are Red, Neutral prevents a winner
        for tid in ALL_TERRITORY_IDS:
            if tid != "rapa_nui":
                set_owner(tid, RED)
        assert winner() is None
        assert not is_game_over()
    finally:
        for i, tid in enumerate(ALL_TERRITORY_IDS):
            set_owner(tid, RED if i < 15 else BLUE)
