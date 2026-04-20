"""
Pygame Pacific map (29 territories). Run with: python -m src.game
Uses src/img/map.jpg as background; territories are clickable markers.
"""

import logging
import math
import os

import pygame
import pygame_gui
from .territory import (
    ALL_TERRITORY_IDS,
    display_name,
    is_game_over,
    map_position,
    neighbors,
    owner,
    region,
    set_owner,
    territory_at_point,
    TerritoryId,
    winner,
)
from .state import current_team
from .valid_actions import can_skip, valid_attack_targets
from .actions import attack, set_combat_hook, skip
from .combat import roll_combat, resolve_combat, resolve_combat_with_units
from .units import units as territory_units

# Layout: map on top, bottom bar underneath (left area) | right sidebar
MARGIN = 16
GAP = 8
BOTTOM_BAR_HEIGHT = 72
SIDEBAR_RIGHT_WIDTH = 280
MAP_WIDTH = 1280
MAP_HEIGHT = 648  # leaves room for bottom bar
WIDTH = MAP_WIDTH + GAP + SIDEBAR_RIGHT_WIDTH
HEIGHT = MAP_HEIGHT + BOTTOM_BAR_HEIGHT
TITLE = "Pacific Map (29 territories)"

# Theme
BG_COLOR = (28, 32, 38)
TEAM_COLORS = {"Red": (200, 80, 80), "Blue": (80, 80, 200), "Neutral": (150, 150, 150)}
TEXT_COLOR = (230, 230, 240)
SIDEBAR_BG = (45, 48, 55)
SIDEBAR_BORDER = (70, 74, 90)
BTN_BG = (90, 95, 110)
MOVES_TITLE_COLOR = (190, 190, 210)
MARKER_RADIUS = 8  # 25% larger than original 6
MARKER_BORDER = 1

SIDEBAR_PAD = 16
BUTTON_HEIGHT = 44
FONT_SIZE_SMALL = 26
FONT_SIZE_BTN = 34
FONT_SIZE_UNIT_LABEL = 16  # tiny font for per-territory unit count labels on the map
FPS = 60
BORDER_RADIUS = 8
SIDEBAR_TURN_GAP = 20
SIDEBAR_SECTION_GAP = 6
SIDEBAR_LINE_GAP = 2
SIDEBAR_LINE_WIDTH = 2

# Last combat result for UI:
# (attacker_team, attacker_roll, defender_roll, winner, defending_territory_id, attacking_territory_id | None)
# winner is "attacker" | "defender" from resolve_combat
_last_combat: tuple[str, int, int, str, TerritoryId, TerritoryId | None] | None = None

# Currently selected territory to attack FROM (green outline); None if none selected
_selected_territory: TerritoryId | None = None

# Active tooltip panel managed by pygame-gui (None when no territory hovered)
_tooltip_panel: "pygame_gui.elements.UIPanel | None" = None
# The territory ID the active tooltip is for (to detect when mouse moves to new territory)
_tooltip_tid: "TerritoryId | None" = None

# Highlight color for valid attack cells on hover / pulse
HOVER_HIGHLIGHT_COLOR = (255, 255, 200)
HOVER_HIGHLIGHT_WIDTH = 4

# Pulse settings for valid attack target outlines (~1s cycle, smooth sine wave)
PULSE_PERIOD_MS = 1000  # milliseconds per full cycle
PULSE_ALPHA_MIN = 80    # minimum alpha (dim end of pulse)
PULSE_ALPHA_MAX = 255   # maximum alpha (bright end of pulse)


def _map_rect() -> pygame.Rect:
    return pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT)


def bottom_bar_rect() -> pygame.Rect:
    return pygame.Rect(0, MAP_HEIGHT, MAP_WIDTH, BOTTOM_BAR_HEIGHT)


def right_sidebar_rect() -> pygame.Rect:
    return pygame.Rect(MAP_WIDTH + GAP, 0, SIDEBAR_RIGHT_WIDTH, HEIGHT)


def end_turn_button_rect(sidebar: pygame.Rect | None = None) -> pygame.Rect:
    s = sidebar if sidebar is not None else right_sidebar_rect()
    return pygame.Rect(
        s.x + SIDEBAR_PAD,
        HEIGHT - MARGIN - BUTTON_HEIGHT,
        SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD,
        BUTTON_HEIGHT,
    )


def _load_map_surface() -> pygame.Surface | None:
    """Load map image from src/img/map.jpg; scale to MAP_WIDTH x MAP_HEIGHT."""
    base = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base, "img", "map.jpg")
    if not os.path.isfile(path):
        return None
    img = pygame.image.load(path)
    return pygame.transform.smoothscale(img, (MAP_WIDTH, MAP_HEIGHT))


def _handle_events(
    sidebar: pygame.Rect,
    map_surf: pygame.Surface | None,
    map_rect: pygame.Rect,
    ui_manager: "pygame_gui.UIManager | None" = None,
    end_turn_btn: "pygame_gui.elements.UIButton | None" = None,
) -> bool:
    global _selected_territory
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False

        # Let pygame-gui process the event first so button states update
        if ui_manager is not None:
            ui_manager.process_events(event)

        # UIButton End Turn press (pygame-gui event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if end_turn_btn is not None and event.ui_element is end_turn_btn:
                if not is_game_over():
                    skip()
                    _selected_territory = None
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if is_game_over():
                # No actions allowed once the game has ended
                continue
            # If using raw button fallback (no ui_manager), handle it here
            if ui_manager is None and end_turn_button_rect(sidebar).collidepoint(event.pos):
                skip()
                _selected_territory = None
            else:
                r = map_rect
                mx, my, mw, mh = r.x, r.y, r.w, r.h
                tid = territory_at_point((mx, my, mw, mh), event.pos[0], event.pos[1], MARKER_RADIUS + 4)
                if tid is None:
                    # Clicked empty space: deselect
                    _selected_territory = None
                elif owner(tid) == current_team():
                    # Clicked own territory: select it as attack-from
                    _selected_territory = tid
                elif (
                    _selected_territory is not None
                    and tid in valid_attack_targets()
                    and tid in neighbors(_selected_territory)
                ):
                    # Clicked valid target adjacent to selected: execute attack
                    try:
                        attack(tid)
                    except ValueError as e:
                        logging.warning("Invalid attack ignored: %s", e)
                    _selected_territory = None
                else:
                    # Clicked elsewhere (non-owned, non-valid-target): deselect
                    _selected_territory = None
    return True


def _build_tooltip_lines(tid: TerritoryId) -> list[str]:
    """Build the list of text lines for a territory tooltip card."""
    owning_state = owner(tid)
    lines = [f"{display_name(tid)} ({region(tid)})"]
    if owning_state == "Neutral":
        lines.append("Neutral (unclaimed)")
    else:
        own_stack = territory_units(tid, owning_state)
        own_inf = own_stack.get("infantry", 0)
        own_tnk = own_stack.get("tanks", 0)
        enemy_team = "Blue" if owning_state == "Red" else "Red"
        enemy_stack = territory_units(tid, enemy_team)
        enemy_inf = enemy_stack.get("infantry", 0)
        enemy_tnk = enemy_stack.get("tanks", 0)
        lines.append(f"{owning_state}: {own_inf} inf {own_tnk} tnk")
        if enemy_inf > 0 or enemy_tnk > 0:
            lines.append(f"{enemy_team}: {enemy_inf} inf {enemy_tnk} tnk")
    return lines


def _compute_tooltip_rect(
    mouse_pos: tuple[int, int],
    box_w: int,
    box_h: int,
) -> pygame.Rect:
    """Compute tooltip card rect near cursor, clamped to window bounds."""
    px, py = mouse_pos
    # Prefer above-left of cursor
    popup_x = px - box_w - 12
    popup_y = py - box_h - 12
    # Clamp to window
    if popup_x < 0:
        popup_x = px + 12
    if popup_y < 0:
        popup_y = py + 12
    # Clamp right/bottom edges
    if popup_x + box_w > WIDTH:
        popup_x = WIDTH - box_w - 4
    if popup_y + box_h > HEIGHT:
        popup_y = HEIGHT - box_h - 4
    return pygame.Rect(popup_x, popup_y, box_w, box_h)


# Tooltip card dimensions
_TOOLTIP_LINE_HEIGHT = 22
_TOOLTIP_PAD = 10
_TOOLTIP_MIN_W = 200


def _update_territory_tooltip(
    map_rect: pygame.Rect,
    mouse_pos: tuple[int, int],
    ui_manager: "pygame_gui.UIManager",
) -> None:
    """Create, update, or destroy the styled territory tooltip panel based on mouse position.

    Uses module-level _tooltip_panel and _tooltip_tid to track state between frames.
    When mouse moves to a new territory, old panel is destroyed and a new one created.
    When mouse leaves all territories, panel is destroyed.
    """
    global _tooltip_panel, _tooltip_tid

    # Determine which territory (if any) the mouse is over
    current_tid: TerritoryId | None = None
    if map_rect.collidepoint(mouse_pos):
        mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
        px, py = mouse_pos
        current_tid = territory_at_point((mx, my, mw, mh), px, py, MARKER_RADIUS + 4)

    # Destroy stale tooltip when tid changes or mouse leaves map
    if _tooltip_tid != current_tid:
        if _tooltip_panel is not None:
            _tooltip_panel.kill()
            _tooltip_panel = None
        _tooltip_tid = current_tid

    # Nothing to show
    if current_tid is None:
        return

    # If tooltip already exists for this tid, reposition to follow cursor
    lines = _build_tooltip_lines(current_tid)
    box_w = max(_TOOLTIP_MIN_W, max(len(ln) * 8 for ln in lines) + 2 * _TOOLTIP_PAD)
    box_h = len(lines) * _TOOLTIP_LINE_HEIGHT + 2 * _TOOLTIP_PAD
    card_rect = _compute_tooltip_rect(mouse_pos, box_w, box_h)

    if _tooltip_panel is not None:
        # Move existing panel to follow cursor
        _tooltip_panel.set_relative_position(card_rect.topleft)
        return

    # Create a new styled panel card
    _tooltip_panel = pygame_gui.elements.UIPanel(
        relative_rect=card_rect,
        starting_height=10,  # render above most other elements
        manager=ui_manager,
        object_id=pygame_gui.core.ObjectID(class_id="@tooltip_panel"),
    )

    # Lay out one UILabel per line inside the panel
    label_y = _TOOLTIP_PAD
    for line in lines:
        label_rect = pygame.Rect(
            _TOOLTIP_PAD,
            label_y,
            box_w - 2 * _TOOLTIP_PAD,
            _TOOLTIP_LINE_HEIGHT,
        )
        pygame_gui.elements.UILabel(
            relative_rect=label_rect,
            text=line,
            manager=ui_manager,
            container=_tooltip_panel,
        )
        label_y += _TOOLTIP_LINE_HEIGHT


def _draw_coord_tooltip(
    screen: pygame.Surface,
    map_rect: pygame.Rect,
    mouse_pos: tuple[int, int],
    font: pygame.font.Font,
    ui_manager: "pygame_gui.UIManager | None" = None,
) -> None:
    """Draw a hover popup: territory name+region+unit counts when over a marker.

    When ui_manager is provided, delegates to pygame-gui styled panel cards.
    Falls back to raw pygame drawing when ui_manager is None (e.g. tests).
    """
    if ui_manager is not None:
        _update_territory_tooltip(map_rect, mouse_pos, ui_manager)
        return

    # --- Fallback: raw pygame drawing (no ui_manager) ---
    if not map_rect.collidepoint(mouse_pos):
        return
    mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
    px, py = mouse_pos[0], mouse_pos[1]
    tid = territory_at_point((mx, my, mw, mh), px, py, MARKER_RADIUS + 4)
    if tid is not None:
        lines = _build_tooltip_lines(tid)
    else:
        x_frac = max(0.0, min(1.0, (px - mx) / mw))
        y_frac = max(0.0, min(1.0, (py - my) / mh))
        lines = [f"x: {x_frac:.3f}  y: {y_frac:.3f}"]
    labels = [font.render(line, True, TEXT_COLOR) for line in lines]
    pad = 8
    line_gap = 4
    box_w = max(lbl.get_width() for lbl in labels) + 2 * pad
    box_h = sum(lbl.get_height() for lbl in labels) + 2 * pad + line_gap * (len(labels) - 1)
    popup_x = px - box_w - 12
    popup_y = py - box_h - 12
    if popup_x < map_rect.x:
        popup_x = px + 12
    if popup_y < map_rect.y:
        popup_y = py + 12
    popup_rect = pygame.Rect(popup_x, popup_y, box_w, box_h)
    pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 1, border_radius=BORDER_RADIUS)
    y_off = popup_rect.y + pad
    for lbl in labels:
        screen.blit(lbl, (popup_rect.x + pad, y_off))
        y_off += lbl.get_height() + line_gap


def _icon_positions_for_territory(
    cx: int, cy: int, radius: int
) -> dict[str, tuple[int, int]]:
    """Return pixel positions for infantry and tank icons relative to territory circle center.

    Infantry is placed to the lower-left of the circle; tank to the lower-right.
    Offsets scale with the marker radius so icons clear the circle at any size.

    Returns:
        {"infantry": (x, y), "tanks": (x, y)}
    """
    offset_x = radius + 4
    offset_y = radius + 4
    return {
        "infantry": (cx - offset_x, cy + offset_y),
        "tanks": (cx + offset_x, cy + offset_y),
    }


def _unit_icon_data(tid: TerritoryId) -> dict[str, object]:
    """Return the icon data (team, unit counts) for a territory.

    Returns:
        {"team": str, "infantry": int, "tanks": int}
    For Neutral territories, infantry and tanks are 0.
    """
    owning_state = owner(tid)
    if owning_state == "Neutral":
        return {"team": "Neutral", "infantry": 0, "tanks": 0}
    stack = territory_units(tid, owning_state)  # type: ignore[arg-type]
    return {
        "team": owning_state,
        "infantry": stack.get("infantry", 0),
        "tanks": stack.get("tanks", 0),
    }


# Icon rendering sizes relative to MARKER_RADIUS
_ICON_SIZE = 5  # pixel radius/half-width of each icon glyph


def _draw_infantry_icon(
    screen: pygame.Surface,
    x: int,
    y: int,
    color: tuple[int, int, int],
    size: int = _ICON_SIZE,
) -> None:
    """Draw a minimal stick-soldier infantry icon centered at (x, y).

    Shape: circular head atop a triangular torso (helmet silhouette).
    """
    head_r = max(1, size // 2)
    # Head circle
    pygame.draw.circle(screen, color, (x, y - size // 2), head_r)
    # Body: small downward triangle
    half = max(1, size // 2)
    body_top = y - size // 2 + head_r
    pts = [
        (x - half, body_top + size),
        (x + half, body_top + size),
        (x, body_top),
    ]
    pygame.draw.polygon(screen, color, pts)


def _draw_tank_icon(
    screen: pygame.Surface,
    x: int,
    y: int,
    color: tuple[int, int, int],
    size: int = _ICON_SIZE,
) -> None:
    """Draw a minimal tank icon centered at (x, y).

    Shape: wide rectangular hull with a small gun barrel protruding to the right.
    """
    half_w = max(2, size)
    half_h = max(1, size // 2)
    # Hull rectangle
    hull = pygame.Rect(x - half_w, y - half_h, half_w * 2, half_h * 2)
    pygame.draw.rect(screen, color, hull, border_radius=1)
    # Turret: smaller square on top-center
    turret_size = max(1, size // 2)
    turret_rect = pygame.Rect(
        x - turret_size // 2,
        y - half_h - turret_size,
        turret_size,
        turret_size,
    )
    pygame.draw.rect(screen, color, turret_rect)
    # Gun barrel: short horizontal line to the right of turret
    barrel_x_start = x + turret_size // 2
    barrel_y = y - half_h - turret_size // 2
    barrel_x_end = barrel_x_start + max(2, size // 2)
    pygame.draw.line(screen, color, (barrel_x_start, barrel_y), (barrel_x_end, barrel_y), 1)


def _draw_map(
    screen: pygame.Surface,
    map_rect: pygame.Rect,
    map_surf: pygame.Surface | None,
    mouse_pos: tuple[int, int] | None = None,
    selected: TerritoryId | None = None,
    pulse_alpha: int = 255,
    unit_label_font: pygame.font.Font | None = None,
) -> None:
    """Draw map image and territory markers; pulse yellow outlines on valid attack targets.

    When unit_label_font is provided, renders a small label (e.g. '2i 1t') below each
    territory marker so unit counts are visible at a glance without hovering.
    """
    if map_surf is not None:
        screen.blit(map_surf, map_rect.topleft)
    mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
    all_targets = set(valid_attack_targets())
    # When a territory is selected, yellow outlines only on its enemy neighbors
    if selected is not None:
        selected_targets = {t for t in neighbors(selected) if t in all_targets}
    else:
        selected_targets = all_targets
    for tid in ALL_TERRITORY_IDS:
        x_frac, y_frac = map_position(tid)
        tx = int(mx + x_frac * mw)
        ty = int(my + y_frac * mh)
        pygame.draw.circle(screen, TEAM_COLORS[owner(tid)], (tx, ty), MARKER_RADIUS)
        pygame.draw.circle(screen, SIDEBAR_BORDER, (tx, ty), MARKER_RADIUS, MARKER_BORDER)
        # Green outline ring on selected territory
        if tid == selected:
            pygame.draw.circle(
                screen,
                (80, 200, 80),
                (tx, ty),
                MARKER_RADIUS + 5,
                width=3,
            )
        # Pulsing yellow outline on valid attack targets; brighter on hover
        if tid in selected_targets:
            is_hover = (
                mouse_pos is not None
                and (mouse_pos[0] - tx) ** 2 + (mouse_pos[1] - ty) ** 2 <= (MARKER_RADIUS + 4) ** 2
            )
            alpha = 255 if is_hover else pulse_alpha
            r, g, b = HOVER_HIGHLIGHT_COLOR
            pulse_surf = pygame.Surface(
                (2 * (MARKER_RADIUS + HOVER_HIGHLIGHT_WIDTH + 1),) * 2, pygame.SRCALPHA
            )
            center = MARKER_RADIUS + HOVER_HIGHLIGHT_WIDTH + 1
            pygame.draw.circle(
                pulse_surf,
                (r, g, b, alpha),
                (center, center),
                MARKER_RADIUS + HOVER_HIGHLIGHT_WIDTH,
                HOVER_HIGHLIGHT_WIDTH,
            )
            screen.blit(pulse_surf, (tx - center, ty - center))
        # Draw soldier and tank icons positioned relative to the territory circle.
        # Only draw each icon type when that unit type is actually present (count > 0).
        icon_data = _unit_icon_data(tid)
        if icon_data["team"] != "Neutral":
            icon_color = TEAM_COLORS[icon_data["team"]]  # type: ignore[index]
            icon_positions = _icon_positions_for_territory(tx, ty, MARKER_RADIUS)
            # Infantry icon (lower-left of circle) — only when infantry are present
            if icon_data["infantry"]:  # type: ignore[truthy-bool]
                inf_x, inf_y = icon_positions["infantry"]
                _draw_infantry_icon(screen, inf_x, inf_y, icon_color, _ICON_SIZE)
            # Tank icon (lower-right of circle) — only when tanks are present
            if icon_data["tanks"]:  # type: ignore[truthy-bool]
                tnk_x, tnk_y = icon_positions["tanks"]
                _draw_tank_icon(screen, tnk_x, tnk_y, icon_color, _ICON_SIZE)
        # Render a small unit count label below the marker when a font is provided
        if unit_label_font is not None:
            owning_state = owner(tid)
            label_color = TEAM_COLORS[owning_state]
            if owning_state == "Neutral":
                label_text = "N"
            else:
                stack = territory_units(tid, owning_state)
                inf_count = stack.get("infantry", 0)
                tnk_count = stack.get("tanks", 0)
                label_text = f"{inf_count}i {tnk_count}t"
            label_surf = unit_label_font.render(label_text, True, label_color)
            # Centered horizontally, just below the marker circle
            label_x = tx - label_surf.get_width() // 2
            label_y = ty + MARKER_RADIUS + 2
            # Dark shadow for readability against the map image
            shadow_surf = unit_label_font.render(label_text, True, (0, 0, 0))
            screen.blit(shadow_surf, (label_x + 1, label_y + 1))
            screen.blit(label_surf, (label_x, label_y))


def _show_combat_popup(
    screen: pygame.Surface,
    att_team: str,
    att_roll: int,
    def_roll: int,
    combat_winner: str,
    def_territory_id: TerritoryId,
    clock: pygame.time.Clock,
    att_territory_id: TerritoryId | None = None,
) -> None:
    """Show battle stats and outcome in a modal popup; wait for any key to close."""
    from .combat import _effective_attack_bonus, _effective_defense_bonus  # noqa: PLC0415
    def_team: str = "Blue" if att_team == "Red" else "Red"
    attacker_wins = combat_winner == "attacker"
    outcome = f"{att_team} wins!" if attacker_wins else "Defender holds!"
    outcome_color = TEAM_COLORS[att_team] if attacker_wins else TEAM_COLORS[def_team]
    def_name = display_name(def_territory_id)

    # Compute unit stat bonuses for display
    att_bonus = _effective_attack_bonus(att_team, att_territory_id) if att_territory_id else 0  # type: ignore[arg-type]
    def_bonus = _effective_defense_bonus(def_team, def_territory_id)  # type: ignore[arg-type]
    bonus_text = f"Att +{att_bonus}  Def +{def_bonus}" if (att_bonus or def_bonus) else ""

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    popup_w, popup_h = 320, 210
    popup_x = (WIDTH - popup_w) // 2
    popup_y = (HEIGHT - popup_h) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
    pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 2, border_radius=BORDER_RADIUS)
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    title = font.render("Combat", True, MOVES_TITLE_COLOR)
    screen.blit(title, title.get_rect(centerx=popup_rect.centerx, top=popup_y + 14))
    msg = font.render(f"{att_team} {att_roll}  vs  {def_team} {def_roll}", True, TEXT_COLOR)
    screen.blit(msg, msg.get_rect(centerx=popup_rect.centerx, top=popup_y + 50))
    if bonus_text:
        bonus_surf = small_font.render(bonus_text, True, MOVES_TITLE_COLOR)
        screen.blit(bonus_surf, bonus_surf.get_rect(centerx=popup_rect.centerx, top=popup_y + 86))
    defending_label = small_font.render(f"Defending: {def_name}", True, MOVES_TITLE_COLOR)
    screen.blit(defending_label, defending_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 104))
    outcome_surf = font.render(outcome, True, outcome_color)
    screen.blit(outcome_surf, outcome_surf.get_rect(centerx=popup_rect.centerx, top=popup_y + 128))
    hint = pygame.font.Font(None, 24).render("Press any key to close", True, MOVES_TITLE_COLOR)
    screen.blit(hint, hint.get_rect(centerx=popup_rect.centerx, top=popup_y + 172))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.KEYDOWN):
                waiting = False
        clock.tick(FPS)


def _show_winner_popup(
    screen: pygame.Surface, winning_team: str, clock: pygame.time.Clock
) -> None:
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))
    popup_w, popup_h = 320, 120
    popup_x = (WIDTH - popup_w) // 2
    popup_y = (HEIGHT - popup_h) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
    pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 2, border_radius=BORDER_RADIUS)
    font = pygame.font.Font(None, 48)
    title = font.render("Game Over", True, MOVES_TITLE_COLOR)
    screen.blit(title, title.get_rect(centerx=popup_rect.centerx, top=popup_y + 20))
    msg = font.render(f"{winning_team} wins!", True, TEAM_COLORS.get(winning_team, TEXT_COLOR))
    screen.blit(msg, msg.get_rect(centerx=popup_rect.centerx, top=popup_y + 55))
    hint = pygame.font.Font(None, 24).render("Click or press any key to close", True, MOVES_TITLE_COLOR)
    screen.blit(hint, hint.get_rect(centerx=popup_rect.centerx, top=popup_y + 90))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type in (pygame.QUIT, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                waiting = False
        clock.tick(FPS)


def _draw_bottom_bar(screen: pygame.Surface, bar: pygame.Rect, small_font: pygame.font.Font) -> None:
    """Draw bottom bar under the map with a team legend showing territory counts."""
    pygame.draw.rect(screen, SIDEBAR_BG, bar)
    pygame.draw.line(screen, SIDEBAR_BORDER, (0, bar.top), (bar.width, bar.top), SIDEBAR_LINE_WIDTH)

    dot_radius = 10
    x = bar.x + MARGIN
    cy = bar.centery

    for team in ("Red", "Blue"):
        count = sum(1 for tid in ALL_TERRITORY_IDS if owner(tid) == team)
        color = TEAM_COLORS[team]
        pygame.draw.circle(screen, color, (x + dot_radius, cy), dot_radius)
        label = small_font.render(f"{team}: {count}", True, TEXT_COLOR)
        screen.blit(label, (x + dot_radius * 2 + GAP, cy - label.get_height() // 2))
        x += dot_radius * 2 + GAP + label.get_width() + MARGIN


def _draw_right_sidebar(
    screen: pygame.Surface,
    sidebar: pygame.Rect,
    small_font: pygame.font.Font,
    btn_font: pygame.font.Font,
    use_gui_button: bool = False,
) -> None:
    pygame.draw.rect(screen, SIDEBAR_BG, sidebar)
    pygame.draw.line(screen, SIDEBAR_BORDER, (sidebar.left, 0), (sidebar.left, HEIGHT), SIDEBAR_LINE_WIDTH)
    y = MARGIN
    turn_label = f"{current_team()}'s turn"
    turn_surf = btn_font.render(turn_label, True, TEAM_COLORS[current_team()])
    turn_rect = turn_surf.get_rect(x=sidebar.x + SIDEBAR_PAD, y=y)
    screen.blit(turn_surf, turn_rect)
    y = turn_rect.bottom + SIDEBAR_TURN_GAP
    targets = valid_attack_targets()
    skip_ok = can_skip()
    moves_title = small_font.render("Possible moves", True, MOVES_TITLE_COLOR)
    screen.blit(moves_title, (sidebar.x + SIDEBAR_PAD, y))
    y += moves_title.get_height() + SIDEBAR_SECTION_GAP
    attack_txt = small_font.render(f"Attack: {targets if targets else 'none'}", True, TEXT_COLOR)
    screen.blit(attack_txt, (sidebar.x + SIDEBAR_PAD, y))
    y += attack_txt.get_height() + SIDEBAR_LINE_GAP
    skip_txt = small_font.render(f"Skip: {'yes' if skip_ok else 'no'}", True, TEXT_COLOR)
    screen.blit(skip_txt, (sidebar.x + SIDEBAR_PAD, y))
    # Draw the raw fallback button only when not using the pygame-gui UIButton
    if not use_gui_button:
        btn = end_turn_button_rect(sidebar)
        pygame.draw.rect(screen, BTN_BG, btn, border_radius=BORDER_RADIUS)
        btn_text = btn_font.render("End turn", True, TEXT_COLOR)
        screen.blit(btn_text, btn_text.get_rect(center=btn.center))


def main() -> None:
    global _last_combat, _selected_territory, _tooltip_panel, _tooltip_tid
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    map_surf = _load_map_surface()
    small_font = pygame.font.Font(None, FONT_SIZE_SMALL)
    btn_font = pygame.font.Font(None, FONT_SIZE_BTN)
    unit_label_font = pygame.font.Font(None, FONT_SIZE_UNIT_LABEL)

    # --- pygame-gui setup ---
    ui_manager = pygame_gui.UIManager((WIDTH, HEIGHT))

    # Create the styled End Turn button via pygame-gui
    sidebar = right_sidebar_rect()
    btn_rect = end_turn_button_rect(sidebar)
    end_turn_btn = pygame_gui.elements.UIButton(
        relative_rect=btn_rect,
        text="End Turn",
        manager=ui_manager,
    )

    def on_combat(target_id: TerritoryId) -> None:
        global _last_combat
        att = current_team()
        att_roll, def_roll = roll_combat()
        att_tid = _selected_territory
        # Apply unit stats if an attacking territory is selected
        if att_tid is not None:
            combat_winner = resolve_combat_with_units(att_roll, def_roll, att, att_tid, target_id)
        else:
            combat_winner = resolve_combat(att_roll, def_roll)
        _last_combat = (att, att_roll, def_roll, combat_winner, target_id, att_tid)
        if combat_winner == "attacker":
            set_owner(target_id, att)

    set_combat_hook(on_combat)
    clock = pygame.time.Clock()
    running = True
    while running:
        time_delta = clock.tick(FPS) / 1000.0
        map_rect = _map_rect()
        prev_team = current_team()
        running = _handle_events(
            right_sidebar_rect(), map_surf, map_rect, ui_manager, end_turn_btn
        )
        if not running:
            break
        # Clear selection after end_turn (team changed)
        if current_team() != prev_team:
            _selected_territory = None
        screen.fill(BG_COLOR)
        sidebar = right_sidebar_rect()
        mouse_pos = pygame.mouse.get_pos()
        # Compute smooth pulsing alpha for valid target outlines (~1s sine cycle)
        t_ms = pygame.time.get_ticks()
        phase = (t_ms % PULSE_PERIOD_MS) / PULSE_PERIOD_MS  # 0.0 to 1.0
        sine_val = (1.0 + math.sin(2 * math.pi * phase - math.pi / 2)) / 2  # 0.0 to 1.0
        pulse_alpha = int(PULSE_ALPHA_MIN + (PULSE_ALPHA_MAX - PULSE_ALPHA_MIN) * sine_val)
        _draw_map(screen, map_rect, map_surf, mouse_pos, _selected_territory, pulse_alpha, unit_label_font)
        # Tooltip: managed by pygame-gui (created/destroyed in _draw_coord_tooltip)
        _draw_coord_tooltip(screen, map_rect, mouse_pos, small_font, ui_manager)
        _draw_bottom_bar(screen, bottom_bar_rect(), small_font)
        _draw_right_sidebar(screen, sidebar, small_font, btn_font, use_gui_button=True)
        # Update and draw pygame-gui widgets on top of everything else
        ui_manager.update(time_delta)
        ui_manager.draw_ui(screen)
        pygame.display.flip()
        if _last_combat is not None:
            att_team, att_roll, def_roll, combat_winner, def_tid, att_tid = _last_combat
            _show_combat_popup(screen, att_team, att_roll, def_roll, combat_winner, def_tid, clock, att_tid)
            _last_combat = None
            continue
        if is_game_over():
            w = winner()
            if w is not None:
                _show_winner_popup(screen, w, clock)
            break
    # Clean up tooltip panel on exit
    if _tooltip_panel is not None:
        _tooltip_panel.kill()
        _tooltip_panel = None
    _tooltip_tid = None
    pygame.quit()


if __name__ == "__main__":
    main()
