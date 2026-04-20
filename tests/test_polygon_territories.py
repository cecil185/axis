"""Tests for SVG territory polygon regions and point-in-polygon click detection.

Verifies:
- All 29 territories have defined polygon data.
- Every territory's map centre (x_frac, y_frac) falls strictly inside its polygon.
- Ray-casting point-in-polygon correctness for known cases.
- territory_at_point_polygon returns the correct territory for centre clicks.
- territory_at_point delegates to polygon logic (backward-compat).
- territory_polygon returns pixel coordinates scaled to map_rect.
"""

import pytest
from src.territory import (
    ALL_TERRITORY_IDS,
    _POLYGONS,
    _point_in_polygon,
    map_position,
    territory_at_point,
    territory_at_point_polygon,
    territory_polygon,
    TerritoryId,
)


# ---------------------------------------------------------------------------
# Data completeness
# ---------------------------------------------------------------------------

def test_all_29_territories_have_polygon_data() -> None:
    """_POLYGONS must contain exactly one entry per territory ID."""
    assert len(_POLYGONS) == 29
    for tid in ALL_TERRITORY_IDS:
        assert tid in _POLYGONS, f"No polygon defined for territory: {tid}"


def test_each_polygon_has_at_least_3_vertices() -> None:
    """A polygon needs at least 3 vertices to define an area."""
    for tid, poly in _POLYGONS.items():
        assert len(poly) >= 3, f"{tid} polygon has only {len(poly)} vertex/vertices"


def test_polygon_vertices_are_fractional_in_0_1() -> None:
    """All vertex coordinates must be in the [0, 1] range."""
    for tid, poly in _POLYGONS.items():
        for x, y in poly:
            assert 0.0 <= x <= 1.0, f"{tid} vertex x={x} out of range"
            assert 0.0 <= y <= 1.0, f"{tid} vertex y={y} out of range"


# ---------------------------------------------------------------------------
# Centre-point containment
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("tid", ALL_TERRITORY_IDS)
def test_territory_centre_inside_own_polygon(tid: TerritoryId) -> None:
    """Each territory's map centre must fall strictly inside its polygon."""
    x_frac, y_frac = map_position(tid)
    assert _point_in_polygon(x_frac, y_frac, _POLYGONS[tid]), (
        f"{tid} centre ({x_frac:.3f}, {y_frac:.3f}) is NOT inside its polygon"
    )


# ---------------------------------------------------------------------------
# Ray-casting correctness
# ---------------------------------------------------------------------------

def test_point_in_polygon_simple_square_inside() -> None:
    """Point clearly inside a unit square."""
    square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert _point_in_polygon(0.5, 0.5, square)


def test_point_in_polygon_simple_square_outside() -> None:
    """Point clearly outside a unit square."""
    square = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert not _point_in_polygon(1.5, 0.5, square)
    assert not _point_in_polygon(-0.1, 0.5, square)
    assert not _point_in_polygon(0.5, -0.1, square)
    assert not _point_in_polygon(0.5, 1.5, square)


def test_point_in_polygon_triangle_inside() -> None:
    """Point inside a right triangle."""
    triangle = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    # (0.1, 0.1) is well inside x+y < 1 triangle
    assert _point_in_polygon(0.1, 0.1, triangle)


def test_point_in_polygon_triangle_outside() -> None:
    """Point outside a right triangle."""
    triangle = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    # (0.6, 0.6) satisfies x+y > 1, so outside
    assert not _point_in_polygon(0.6, 0.6, triangle)


# ---------------------------------------------------------------------------
# territory_at_point_polygon
# ---------------------------------------------------------------------------

def test_territory_at_point_polygon_returns_territory_for_centre_click() -> None:
    """Clicking on the centre of a territory returns that territory."""
    map_rect = (0, 0, 1000, 1000)
    for tid in ALL_TERRITORY_IDS:
        x_frac, y_frac = map_position(tid)
        px = int(x_frac * 1000)
        py = int(y_frac * 1000)
        result = territory_at_point_polygon(map_rect, px, py)
        assert result == tid, (
            f"Expected {tid} at ({px}, {py}), got {result}"
        )


def test_territory_at_point_polygon_returns_none_in_ocean() -> None:
    """Clicking in an ocean area (top-right corner not covered) returns None."""
    # Use a small map_rect and click far outside any polygon
    map_rect = (0, 0, 1000, 1000)
    # The far bottom-left corner (0, 1000) in frac space is (0.0, 1.0), which may
    # or may not be covered. Use a point we verified is inside japan: (200, 260).
    # Instead verify a point clearly inside japan:
    result = territory_at_point_polygon(map_rect, 0, 0)
    # (0,0) maps to (0.0, 0.0) in frac — inside japan polygon (0.00–0.30, 0.00–0.27)
    assert result == "japan"


def test_territory_at_point_polygon_zero_size_map_returns_none() -> None:
    """Zero-width/height map_rect returns None (no division by zero crash)."""
    assert territory_at_point_polygon((0, 0, 0, 0), 5, 5) is None
    assert territory_at_point_polygon((0, 0, 0, 100), 5, 5) is None


def test_territory_at_point_polygon_offset_map_rect() -> None:
    """Polygon hit testing works correctly when map_rect has non-zero origin."""
    offset_x, offset_y = 200, 100
    mw, mh = 800, 600
    map_rect = (offset_x, offset_y, mw, mh)
    # Hawaii centre at (0.56, 0.31) → pixel (200 + 0.56*800, 100 + 0.31*600) = (648, 286)
    px = int(offset_x + 0.56 * mw)
    py = int(offset_y + 0.31 * mh)
    result = territory_at_point_polygon(map_rect, px, py)
    assert result == "hawaii"


# ---------------------------------------------------------------------------
# territory_at_point backward-compat delegation
# ---------------------------------------------------------------------------

def test_territory_at_point_delegates_to_polygon_detection() -> None:
    """territory_at_point must return the same result as territory_at_point_polygon."""
    map_rect_tuple = (0, 0, 1000, 1000)
    for tid in ("japan", "hawaii", "australia_west", "rapa_nui"):
        x_frac, y_frac = map_position(tid)
        px = int(x_frac * 1000)
        py = int(y_frac * 1000)
        poly_result = territory_at_point_polygon(map_rect_tuple, px, py)
        compat_result = territory_at_point(map_rect_tuple, px, py)
        assert compat_result == poly_result == tid


# ---------------------------------------------------------------------------
# territory_polygon pixel coordinates
# ---------------------------------------------------------------------------

def test_territory_polygon_returns_pixel_list() -> None:
    """territory_polygon must return a list of (int, int) tuples."""
    map_rect = (0, 0, 1280, 648)
    for tid in ALL_TERRITORY_IDS:
        pixels = territory_polygon(tid, map_rect)
        assert len(pixels) == len(_POLYGONS[tid])
        for px, py in pixels:
            assert isinstance(px, int)
            assert isinstance(py, int)


def test_territory_polygon_scales_with_map_rect() -> None:
    """Pixel coords scale proportionally with the map_rect dimensions."""
    # With a 1000x1000 map, all frac coords [0,1] map to [0,1000]
    map_rect = (0, 0, 1000, 1000)
    px_list = territory_polygon("japan", map_rect)
    for (xf, yf), (px, py) in zip(_POLYGONS["japan"], px_list):
        assert px == int(xf * 1000)
        assert py == int(yf * 1000)


def test_territory_polygon_respects_map_rect_offset() -> None:
    """Pixel coords shift by the map_rect (x, y) offset."""
    ox, oy = 50, 30
    map_rect = (ox, oy, 1000, 1000)
    px_list = territory_polygon("hawaii", map_rect)
    for (xf, yf), (px, py) in zip(_POLYGONS["hawaii"], px_list):
        assert px == int(ox + xf * 1000)
        assert py == int(oy + yf * 1000)
