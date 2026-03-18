"""Tests for movement range: reachable_territories(tid, team, unit_type)."""

from src.movement import reachable_territories
from src.territory import TerritoryId, neighbors, owner, set_owner
from src.units import init_game, set_units


def _reset_ownership() -> None:
    """Reset to default ownership: Red first 15, Blue last 14."""
    from src.territory import ALL_TERRITORY_IDS
    for i, tid in enumerate(ALL_TERRITORY_IDS):
        set_owner(tid, "Red" if i < 15 else "Blue")


class TestInfantryMovement:
    """Infantry can move 1 hop to any friendly-owned adjacent territory."""

    def setup_method(self) -> None:
        init_game()
        _reset_ownership()

    def test_infantry_can_reach_friendly_neighbor(self) -> None:
        # Japan is Red, adjacent to marianas (Red) and minamitori (Red)
        result = reachable_territories("japan", "Red", "infantry")
        assert "marianas" in result
        assert "minamitori" in result

    def test_infantry_cannot_reach_enemy_territory(self) -> None:
        # Japan is Red; make minamitori Blue
        set_owner("minamitori", "Blue")
        result = reachable_territories("japan", "Red", "infantry")
        assert "minamitori" not in result
        assert "marianas" in result

    def test_infantry_cannot_reach_non_adjacent(self) -> None:
        # Japan is not adjacent to hawaii
        result = reachable_territories("japan", "Red", "infantry")
        assert "hawaii" not in result

    def test_infantry_returns_set(self) -> None:
        result = reachable_territories("japan", "Red", "infantry")
        assert isinstance(result, set)

    def test_infantry_no_friendly_neighbors(self) -> None:
        # Make all neighbors of japan enemy-owned
        for n in neighbors("japan"):
            set_owner(n, "Blue")
        result = reachable_territories("japan", "Red", "infantry")
        assert result == set()

    def test_infantry_does_not_include_source(self) -> None:
        result = reachable_territories("japan", "Red", "infantry")
        assert "japan" not in result


class TestTankMovement:
    """Tanks can move up to 2 hops through friendly territories, but stop on enemy."""

    def setup_method(self) -> None:
        init_game()
        _reset_ownership()

    def test_tank_reaches_1_hop_friendly(self) -> None:
        # Japan -> marianas (friendly, 1 hop)
        result = reachable_territories("japan", "Red", "tanks")
        assert "marianas" in result

    def test_tank_reaches_2_hops_through_friendly(self) -> None:
        # Japan -> marianas (friendly) -> micronesia (friendly, if Red)
        # marianas neighbors: micronesia, minamitori, japan, philippines
        # micronesia is index 9 in ALL_TERRITORY_IDS, so it's Red (first 15)
        result = reachable_territories("japan", "Red", "tanks")
        # 2-hop: japan -> marianas -> micronesia
        assert "micronesia" in result
        # 2-hop: japan -> marianas -> philippines (index 2, Red)
        assert "philippines" in result

    def test_tank_stops_on_enemy_territory(self) -> None:
        # Make marianas enemy (Blue). Tank can reach marianas (1 hop enemy = stops)
        # but cannot continue through it to micronesia.
        set_owner("marianas", "Blue")
        result = reachable_territories("japan", "Red", "tanks")
        # Can reach the enemy territory at 1 hop
        assert "marianas" in result
        # Cannot continue through enemy territory
        # micronesia is only reachable through marianas from japan
        # (minamitori doesn't connect to micronesia)
        assert "micronesia" not in result

    def test_tank_cannot_exceed_2_hops(self) -> None:
        # Ensure 3-hop territories are not reachable
        # japan -> marianas -> micronesia -> belau (3 hops)
        result = reachable_territories("japan", "Red", "tanks")
        assert "belau" not in result

    def test_tank_does_not_include_source(self) -> None:
        result = reachable_territories("japan", "Red", "tanks")
        assert "japan" not in result

    def test_tank_returns_set(self) -> None:
        result = reachable_territories("japan", "Red", "tanks")
        assert isinstance(result, set)

    def test_tank_enemy_at_hop1_is_reachable(self) -> None:
        # Even if the neighbor is enemy, tank can reach it (stops there)
        set_owner("marianas", "Blue")
        result = reachable_territories("japan", "Red", "tanks")
        assert "marianas" in result

    def test_tank_2hop_through_friendly_to_enemy(self) -> None:
        # japan -> minamitori (friendly) -> marianas (already in 1-hop)
        # japan -> marianas (friendly) -> micronesia (friendly)
        # Make micronesia Blue — tank should still reach it at hop 2
        set_owner("micronesia", "Blue")
        result = reachable_territories("japan", "Red", "tanks")
        assert "micronesia" in result

    def test_tank_no_moves_when_all_neighbors_enemy_only_1hop(self) -> None:
        # If all neighbors are enemy, tank can still reach them (stops at 1 hop)
        for n in neighbors("japan"):
            set_owner(n, "Blue")
        result = reachable_territories("japan", "Red", "tanks")
        # Tank CAN move into enemy territory (stops there)
        assert "marianas" in result
        assert "minamitori" in result
        # But cannot continue through enemy
        assert "micronesia" not in result


class TestEdgeCases:
    """Edge cases for reachable_territories."""

    def setup_method(self) -> None:
        init_game()
        _reset_ownership()

    def test_infantry_enemy_can_reach_own_territories(self) -> None:
        # Blue infantry from tokelau (Blue territory, index 19)
        # tokelau neighbors: kiribati (Red, idx 13), tuvalu (Blue, idx 14), cook_islands (Blue, idx 20)
        result = reachable_territories("tokelau", "Blue", "infantry")
        # tuvalu is index 14 -> Blue (last 14 = indices 15..28)
        # Wait, tuvalu is index 14 which is the last Red territory (indices 0-14 = 15 territories)
        # Actually: first 15 = indices 0..14, last 14 = indices 15..28
        # tuvalu is at index 14 -> Red
        # Let me check: tokelau neighbors are kiribati, tuvalu, cook_islands
        # cook_islands is index 20 -> Blue
        assert "cook_islands" in result

    def test_reachable_from_isolated_friendly_island(self) -> None:
        # clipperton neighbors: pitcairn only
        # clipperton is index 24 (Blue), pitcairn is index 25 (Blue)
        result = reachable_territories("clipperton", "Blue", "infantry")
        assert "pitcairn" in result

    def test_tank_2hop_reaches_multiple_paths(self) -> None:
        # Verify that tank movement explores all paths correctly
        # hawaii (Red, idx 3) -> midway (Red, idx 4) -> australia_west (Red, idx 6)
        # hawaii -> johnston (Red, idx 5) -> marshall (Red, idx 11)
        result = reachable_territories("hawaii", "Red", "tanks")
        assert "midway" in result
        assert "johnston" in result
        assert "australia_west" in result  # 2 hops: hawaii->midway->australia_west
        assert "marshall" in result  # 2 hops: hawaii->johnston->marshall
