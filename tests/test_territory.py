from src.state import TEAMS
from src.territory import (
    ALL_TERRITORY_IDS,
    display_name,
    ipc_value,
    map_position,
    territory_at_point,
    neighbors,
    owner,
    region,
    set_owner,
    territory_info,
    TerritoryId,
    winner,
    is_game_over,
)

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


def test_territory_at_point_returns_none_when_in_uncovered_ocean() -> None:
    # (0.20, 0.80) in fractional space falls in no territory polygon (open ocean).
    map_rect = (0, 0, 1000, 1000)
    assert territory_at_point(map_rect, 200, 800) is None


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


def test_ipc_value_strategic_territories_worth_3() -> None:
    """Strategic territories (japan, hawaii, australia_east, australia_west) are worth 3 IPCs."""
    assert ipc_value("japan") == 3
    assert ipc_value("hawaii") == 3
    assert ipc_value("australia_east") == 3
    assert ipc_value("australia_west") == 3


def test_ipc_value_all_territories_in_range_1_to_3() -> None:
    """Every territory must have an IPC value of 1, 2, or 3."""
    for tid in ALL_TERRITORY_IDS:
        val = ipc_value(tid)
        assert val in (1, 2, 3), f"{tid} has ipc_value={val}, expected 1–3"


def test_ipc_value_remote_atolls_worth_1() -> None:
    """Remote atolls and minor islands are worth 1 IPC."""
    assert ipc_value("johnston") == 1
    assert ipc_value("midway") == 1
    assert ipc_value("clipperton") == 1
    assert ipc_value("pitcairn") == 1
    assert ipc_value("rapa_nui") == 1


def test_ipc_value_returned_in_territory_info() -> None:
    """territory_info dict includes the ipc_value field."""
    info = territory_info("japan")
    assert "ipc_value" in info
    assert info["ipc_value"] == 3
