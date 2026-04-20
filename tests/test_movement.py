"""
Tests for movement.reachable_territories(tid, team, unit_type).

Rules:
  - Infantry can move to any friendly-owned territory within 1 hop.
  - Tanks can move up to 2 hops, passing through intermediate friendly territories.
    A tank that enters an enemy territory stops there and may not continue through it.
  - Source territory is never included in the result.
"""

import pytest

from src.movement import reachable_territories
from src.territory import ALL_TERRITORY_IDS, Team, TerritoryId, set_owner
from src.units import set_units, init_game


def _setup_owners(red_territories: list[TerritoryId], blue_territories: list[TerritoryId]) -> None:
    """Set ownership for a subset of territories; remaining get whatever they were."""
    for tid in red_territories:
        set_units(tid, "Red", {"infantry": 2, "tanks": 1})
        set_units(tid, "Blue", {"infantry": 0, "tanks": 0})
    for tid in blue_territories:
        set_units(tid, "Blue", {"infantry": 2, "tanks": 1})
        set_units(tid, "Red", {"infantry": 0, "tanks": 0})


# --------------------------------------------------------------------------- #
#  Infantry tests (1 hop only)                                                 #
# --------------------------------------------------------------------------- #

class TestInfantryReachable:
    def test_infantry_can_reach_adjacent_friendly_territory(self) -> None:
        # japan -> [minamitori, marianas]; make all Red
        _setup_owners(["japan", "minamitori", "marianas"], [])
        result = reachable_territories("japan", "Red", "infantry")
        assert "minamitori" in result
        assert "marianas" in result

    def test_infantry_cannot_reach_enemy_adjacent_territory(self) -> None:
        # japan neighbors: minamitori (friendly Red), marianas (enemy Blue)
        _setup_owners(["japan", "minamitori"], ["marianas"])
        result = reachable_territories("japan", "Red", "infantry")
        assert "marianas" not in result

    def test_infantry_cannot_reach_non_adjacent_friendly_territory(self) -> None:
        # japan's 1-hop neighbors are minamitori and marianas; micronesia is 2 hops away
        _setup_owners(["japan", "minamitori", "marianas", "micronesia"], [])
        result = reachable_territories("japan", "Red", "infantry")
        assert "micronesia" not in result

    def test_infantry_source_not_included(self) -> None:
        _setup_owners(["japan", "minamitori"], [])
        result = reachable_territories("japan", "Red", "infantry")
        assert "japan" not in result

    def test_infantry_empty_result_when_all_neighbors_are_enemy(self) -> None:
        # japan neighbors: minamitori, marianas — both Blue
        _setup_owners(["japan"], ["minamitori", "marianas"])
        result = reachable_territories("japan", "Red", "infantry")
        assert result == set()

    def test_infantry_single_friendly_neighbor(self) -> None:
        _setup_owners(["japan", "minamitori"], ["marianas"])
        result = reachable_territories("japan", "Red", "infantry")
        assert result == {"minamitori"}


# --------------------------------------------------------------------------- #
#  Tank tests (up to 2 hops, enemy territory stops movement)                   #
# --------------------------------------------------------------------------- #

class TestTankReachable:
    def test_tank_can_reach_1hop_friendly(self) -> None:
        _setup_owners(["japan", "minamitori", "marianas"], [])
        result = reachable_territories("japan", "Red", "tanks")
        assert "minamitori" in result
        assert "marianas" in result

    def test_tank_can_reach_2hop_friendly_via_friendly_intermediate(self) -> None:
        # japan -> marianas -> micronesia (all Red); tank should reach micronesia
        _setup_owners(["japan", "minamitori", "marianas", "micronesia"], [])
        result = reachable_territories("japan", "Red", "tanks")
        assert "micronesia" in result

    def test_tank_can_enter_enemy_territory_at_1hop(self) -> None:
        # enemy territory is reachable at hop 1 — tank stops there
        _setup_owners(["japan", "minamitori"], ["marianas"])
        result = reachable_territories("japan", "Red", "tanks")
        assert "marianas" in result

    def test_tank_cannot_pass_through_enemy_territory(self) -> None:
        # japan -> marianas (Blue) -> micronesia (Red)
        # tank stops at marianas; cannot pass through to micronesia
        _setup_owners(["japan", "minamitori", "micronesia"], ["marianas"])
        result = reachable_territories("japan", "Red", "tanks")
        assert "marianas" in result      # enemy at 1-hop: reachable
        assert "micronesia" not in result  # blocked by enemy intermediate

    def test_tank_cannot_continue_beyond_enemy_at_hop1(self) -> None:
        # Both neighbors of japan are enemy; tank can reach them but not go further
        _setup_owners(["japan"], ["minamitori", "marianas"])
        # minamitori neighbors: marianas, japan — marianas is also enemy
        # marianas neighbors: micronesia, minamitori, japan, philippines — set all Blue
        _setup_owners(["japan"], ["minamitori", "marianas", "micronesia", "philippines"])
        result = reachable_territories("japan", "Red", "tanks")
        # Can reach 1-hop enemies
        assert "minamitori" in result
        assert "marianas" in result
        # Cannot reach 2-hop territories through enemy
        assert "micronesia" not in result
        assert "philippines" not in result

    def test_tank_source_not_included(self) -> None:
        _setup_owners(["japan", "minamitori", "marianas"], [])
        result = reachable_territories("japan", "Red", "tanks")
        assert "japan" not in result

    def test_tank_2hop_friendly_not_reachable_via_enemy_intermediate(self) -> None:
        # japan -> marianas (Blue) -> micronesia (Red): can't reach micronesia via marianas
        # japan -> minamitori (Red) -> marianas (Blue): can enter marianas but stop
        _setup_owners(["japan", "minamitori", "micronesia"], ["marianas"])
        result = reachable_territories("japan", "Red", "tanks")
        assert "marianas" in result
        assert "micronesia" not in result

    def test_tank_reaches_enemy_at_2hop_if_intermediate_is_friendly(self) -> None:
        # japan -> marianas (Red) -> micronesia (Blue): tank can enter micronesia at hop 2
        _setup_owners(["japan", "minamitori", "marianas"], ["micronesia"])
        result = reachable_territories("japan", "Red", "tanks")
        assert "micronesia" in result

    def test_tank_returns_set(self) -> None:
        _setup_owners(["japan", "minamitori", "marianas"], [])
        result = reachable_territories("japan", "Red", "tanks")
        assert isinstance(result, set)

    def test_tank_no_duplicates_in_result(self) -> None:
        # A territory reachable via multiple paths should appear only once
        # marianas is adjacent to both japan directly AND via minamitori -> marianas path
        # but japan is not adjacent to marianas via minamitori in one hop; marianas IS a direct neighbor
        _setup_owners(["japan", "minamitori", "marianas", "micronesia", "philippines"], [])
        result = reachable_territories("japan", "Red", "tanks")
        # result is a set so duplicates are impossible — just verify it's a set
        assert isinstance(result, set)


# --------------------------------------------------------------------------- #
#  Blue team tests (symmetry)                                                  #
# --------------------------------------------------------------------------- #

class TestBlueTeamReachable:
    def test_blue_infantry_can_reach_adjacent_blue_territory(self) -> None:
        _setup_owners([], ["rapa_nui", "french_polynesia", "pitcairn"])
        result = reachable_territories("rapa_nui", "Blue", "infantry")
        # rapa_nui neighbors: french_polynesia, pitcairn
        assert "french_polynesia" in result
        assert "pitcairn" in result

    def test_blue_infantry_cannot_reach_red_adjacent_territory(self) -> None:
        _setup_owners(["french_polynesia"], ["rapa_nui", "pitcairn"])
        result = reachable_territories("rapa_nui", "Blue", "infantry")
        assert "french_polynesia" not in result

    def test_blue_tank_2hop(self) -> None:
        # rapa_nui -> french_polynesia (Blue) -> cook_islands (Blue): reachable
        _setup_owners([], ["rapa_nui", "french_polynesia", "pitcairn", "cook_islands"])
        result = reachable_territories("rapa_nui", "Blue", "tanks")
        assert "cook_islands" in result
