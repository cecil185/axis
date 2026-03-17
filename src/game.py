"""
Pygame Pacific map (29 territories). Run with: python -m src.game
Uses src/img/map.jpg as background; territories are clickable markers.
"""

import logging
import os

import pygame
from .territory import (
    ALL_TERRITORY_IDS,
    display_name,
    is_game_over,
    map_position,
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
from .combat import roll_combat, resolve_combat

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
TEAM_COLORS = {"Red": (200, 80, 80), "Blue": (80, 80, 200)}
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
FPS = 60
BORDER_RADIUS = 8
SIDEBAR_TURN_GAP = 20
SIDEBAR_SECTION_GAP = 6
SIDEBAR_LINE_GAP = 2
SIDEBAR_LINE_WIDTH = 2

# Last combat result for UI: (attacker_team, attacker_roll, defender_roll, winner, defending_territory_id) or None
# winner is "attacker" | "defender" from resolve_combat
_last_combat: tuple[str, int, int, str, TerritoryId] | None = None

# Highlight color for valid attack cells on hover
HOVER_HIGHLIGHT_COLOR = (255, 255, 200)
HOVER_HIGHLIGHT_WIDTH = 4


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


def _handle_events(sidebar: pygame.Rect, map_surf: pygame.Surface | None) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if end_turn_button_rect(sidebar).collidepoint(event.pos):
                skip()
            else:
                mx, my, mw, mh = _map_rect().x, _map_rect().y, _map_rect().w, _map_rect().h
                tid = territory_at_point((mx, my, mw, mh), event.pos[0], event.pos[1], MARKER_RADIUS + 4)
                if tid is not None and tid in valid_attack_targets():
                    try:
                        attack(tid)
                    except ValueError as e:
                        logging.warning("Invalid attack ignored: %s", e)
    return True


def _draw_coord_tooltip(
    screen: pygame.Surface,
    map_rect: pygame.Rect,
    mouse_pos: tuple[int, int],
    font: pygame.font.Font,
) -> None:
    """Draw a hover popup: territory name+region when over a marker, else x,y fractions."""
    if not map_rect.collidepoint(mouse_pos):
        return
    mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
    px, py = mouse_pos[0], mouse_pos[1]
    tid = territory_at_point((mx, my, mw, mh), px, py, MARKER_RADIUS + 4)
    if tid is not None:
        text = f"{display_name(tid)} ({region(tid)})"
    else:
        x_frac = (px - mx) / mw
        y_frac = (py - my) / mh
        x_frac = max(0.0, min(1.0, x_frac))
        y_frac = max(0.0, min(1.0, y_frac))
        text = f"x: {x_frac:.3f}  y: {y_frac:.3f}"
    label = font.render(text, True, TEXT_COLOR)
    pad = 8
    tw, th = label.get_size()
    box_w, box_h = tw + 2 * pad, th + 2 * pad
    # Place popup above and left of cursor so it doesn't cover the point
    popup_x = px - box_w - 12
    popup_y = py - box_h - 12
    if popup_x < map_rect.x:
        popup_x = px + 12
    if popup_y < map_rect.y:
        popup_y = py + 12
    popup_rect = pygame.Rect(popup_x, popup_y, box_w, box_h)
    pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 1, border_radius=BORDER_RADIUS)
    screen.blit(label, (popup_rect.x + pad, popup_rect.y + pad))


def _draw_map(
    screen: pygame.Surface,
    map_rect: pygame.Rect,
    map_surf: pygame.Surface | None,
    mouse_pos: tuple[int, int] | None = None,
) -> None:
    """Draw map image and territory markers; highlight valid attack target under mouse."""
    if map_surf is not None:
        screen.blit(map_surf, map_rect.topleft)
    mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
    targets = set(valid_attack_targets())
    for tid in ALL_TERRITORY_IDS:
        x_frac, y_frac = map_position(tid)
        tx = int(mx + x_frac * mw)
        ty = int(my + y_frac * mh)
        pygame.draw.circle(screen, TEAM_COLORS[owner(tid)], (tx, ty), MARKER_RADIUS)
        pygame.draw.circle(screen, SIDEBAR_BORDER, (tx, ty), MARKER_RADIUS, MARKER_BORDER)
        is_hover = (
            mouse_pos is not None
            and (mouse_pos[0] - tx) ** 2 + (mouse_pos[1] - ty) ** 2 <= (MARKER_RADIUS + 4) ** 2
            and tid in targets
        )
        if is_hover:
            pygame.draw.circle(
                screen,
                HOVER_HIGHLIGHT_COLOR,
                (tx, ty),
                MARKER_RADIUS + HOVER_HIGHLIGHT_WIDTH,
                width=HOVER_HIGHLIGHT_WIDTH,
            )


def _show_combat_popup(
    screen: pygame.Surface,
    att_team: str,
    att_roll: int,
    def_roll: int,
    combat_winner: str,
    def_territory_id: TerritoryId,
    clock: pygame.time.Clock,
) -> None:
    """Show battle stats and outcome in a modal popup; wait for any key to close."""
    def_team = "Blue" if att_team == "Red" else "Red"
    attacker_wins = att_roll > def_roll
    outcome = f"{att_team} wins!" if attacker_wins else "Defender holds!"
    outcome_color = TEAM_COLORS[att_team] if attacker_wins else TEAM_COLORS[def_team]
    def_name = display_name(def_territory_id)

    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill((0, 0, 0))
    screen.blit(overlay, (0, 0))

    popup_w, popup_h = 320, 190
    popup_x = (WIDTH - popup_w) // 2
    popup_y = (HEIGHT - popup_h) // 2
    popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
    pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 2, border_radius=BORDER_RADIUS)
    font = pygame.font.Font(None, 48)
    small_font = pygame.font.Font(None, 24)
    title = font.render("Combat", True, MOVES_TITLE_COLOR)
    screen.blit(title, title.get_rect(centerx=popup_rect.centerx, top=popup_y + 16))
    msg = font.render(f"{att_team} {att_roll}  vs  {def_team} {def_roll}", True, TEXT_COLOR)
    screen.blit(msg, msg.get_rect(centerx=popup_rect.centerx, top=popup_y + 52))
    defending_label = small_font.render(f"Defending: {def_name}", True, MOVES_TITLE_COLOR)
    screen.blit(defending_label, defending_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 88))
    outcome_surf = font.render(outcome, True, outcome_color)
    screen.blit(outcome_surf, outcome_surf.get_rect(centerx=popup_rect.centerx, top=popup_y + 112))
    hint = pygame.font.Font(None, 24).render("Press any key to close", True, MOVES_TITLE_COLOR)
    screen.blit(hint, hint.get_rect(centerx=popup_rect.centerx, top=popup_y + 152))
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


def _draw_bottom_bar(screen: pygame.Surface, bar: pygame.Rect) -> None:
    """Draw empty bottom bar under the map (reserved for future content)."""
    pygame.draw.rect(screen, SIDEBAR_BG, bar)
    pygame.draw.line(screen, SIDEBAR_BORDER, (0, bar.top), (bar.width, bar.top), SIDEBAR_LINE_WIDTH)


def _draw_right_sidebar(
    screen: pygame.Surface,
    sidebar: pygame.Rect,
    small_font: pygame.font.Font,
    btn_font: pygame.font.Font,
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
    btn = end_turn_button_rect(sidebar)
    pygame.draw.rect(screen, BTN_BG, btn, border_radius=BORDER_RADIUS)
    btn_text = btn_font.render("End turn", True, TEXT_COLOR)
    screen.blit(btn_text, btn_text.get_rect(center=btn.center))


def main() -> None:
    global _last_combat
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    map_surf = _load_map_surface()
    small_font = pygame.font.Font(None, FONT_SIZE_SMALL)
    btn_font = pygame.font.Font(None, FONT_SIZE_BTN)

    def on_combat(target_id: TerritoryId) -> None:
        global _last_combat
        att = current_team()
        def_team = owner(target_id)
        att_roll, def_roll = roll_combat(att, def_team, target_id)
        combat_winner = resolve_combat(att_roll, def_roll)
        _last_combat = (att, att_roll, def_roll, combat_winner, target_id)
        if combat_winner == "attacker":
            set_owner(target_id, att)

    set_combat_hook(on_combat)
    clock = pygame.time.Clock()
    running = True
    while running:
        running = _handle_events(right_sidebar_rect(), map_surf)
        if not running:
            break
        screen.fill(BG_COLOR)
        sidebar = right_sidebar_rect()
        mouse_pos = pygame.mouse.get_pos()
        _draw_map(screen, _map_rect(), map_surf, mouse_pos)
        _draw_coord_tooltip(screen, _map_rect(), mouse_pos, small_font)
        _draw_bottom_bar(screen, bottom_bar_rect())
        _draw_right_sidebar(screen, sidebar, small_font, btn_font)
        pygame.display.flip()
        if _last_combat is not None:
            att_team, att_roll, def_roll, combat_winner, def_tid = _last_combat
            _show_combat_popup(screen, att_team, att_roll, def_roll, combat_winner, def_tid, clock)
            _last_combat = None
            continue
        if is_game_over():
            w = winner()
            if w is not None:
                _show_winner_popup(screen, w, clock)
            break
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()
