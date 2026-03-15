"""
Pygame 2×2 territory grid. Run with: python -m src.game
"""

import logging

import pygame
from .territory import (
    GRID_ROWS,
    GRID_COLS,
    get_territory_at,
    is_game_over,
    owner,
    set_owner,
    TerritoryId,
    winner,
)
from .state import current_team
from .valid_actions import can_skip, valid_attack_targets
from .actions import attack, set_combat_hook, skip

# Window: grid on left, sidebar on right
CELL_SIZE = 120
MARGIN = 20
SIDEBAR_WIDTH = 200
SIDEBAR_PAD = 16
BUTTON_HEIGHT = 44
GRID_WIDTH = GRID_COLS * CELL_SIZE + (GRID_COLS + 1) * MARGIN
GRID_HEIGHT = GRID_ROWS * CELL_SIZE + (GRID_ROWS + 1) * MARGIN
WIDTH = GRID_WIDTH + MARGIN + SIDEBAR_WIDTH
HEIGHT = GRID_HEIGHT
TITLE = "Territory Grid (2×2)"

# Theme
BG_COLOR = (30, 30, 40)
TEAM_COLORS = {"Red": (180, 70, 70), "Blue": (70, 70, 180)}
TEXT_COLOR = (220, 220, 230)
SIDEBAR_BG = (45, 45, 55)
SIDEBAR_BORDER = (70, 70, 85)
BTN_BG = (90, 90, 110)
MOVES_TITLE_COLOR = (180, 180, 200)

# Font sizes (pygame "None" default font)
FONT_SIZE_CELL = 72
FONT_SIZE_SMALL = 28
FONT_SIZE_BTN = 36
FPS = 60

# Layout details
BORDER_RADIUS = 8
SIDEBAR_TURN_GAP = 20
SIDEBAR_SECTION_GAP = 6
SIDEBAR_LINE_GAP = 2
SIDEBAR_LINE_WIDTH = 2


def cell_rect(row: int, col: int) -> pygame.Rect:
    """Rect for a grid cell (left side only)."""
    x = MARGIN + col * (CELL_SIZE + MARGIN)
    y = MARGIN + row * (CELL_SIZE + MARGIN)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def sidebar_rect() -> pygame.Rect:
    """Rect for the right-hand sidebar."""
    return pygame.Rect(GRID_WIDTH + MARGIN, 0, SIDEBAR_WIDTH, HEIGHT)


def end_turn_button_rect(sidebar: pygame.Rect | None = None) -> pygame.Rect:
    """Rect for the End turn button inside the sidebar."""
    s = sidebar if sidebar is not None else sidebar_rect()
    sx = s.x + SIDEBAR_PAD
    sy = HEIGHT - MARGIN - BUTTON_HEIGHT
    return pygame.Rect(sx, sy, SIDEBAR_WIDTH - 2 * SIDEBAR_PAD, BUTTON_HEIGHT)


def cell_at_point(pos: tuple[int, int]) -> tuple[int, int] | None:
    """Return (row, col) of the cell containing pos, or None if outside grid."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            if cell_rect(row, col).collidepoint(pos):
                return (row, col)
    return None


def _handle_events(sidebar: pygame.Rect) -> bool:
    """Process pygame events. Return False to quit."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if end_turn_button_rect(sidebar).collidepoint(event.pos):
                skip()
            else:
                cell = cell_at_point(event.pos)
                if cell is not None:
                    row, col = cell
                    tid = get_territory_at(row, col)
                    if tid is not None and tid in valid_attack_targets():
                        try:
                            attack(tid)
                        except ValueError as e:
                            logging.warning("Invalid attack ignored: %s", e)
    return True


def _draw_grid(screen: pygame.Surface, font: pygame.font.Font) -> None:
    """Draw the 2×2 territory grid on the left."""
    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            tid = get_territory_at(row, col)
            if tid is None:
                continue
            r = cell_rect(row, col)
            pygame.draw.rect(screen, TEAM_COLORS[owner(tid)], r, border_radius=BORDER_RADIUS)
            text = font.render(tid, True, TEXT_COLOR)
            tr = text.get_rect(center=r.center)
            screen.blit(text, tr)


def _show_winner_popup(
    screen: pygame.Surface, winning_team: str, clock: pygame.time.Clock
) -> None:
    """Show a modal popup with the winning team; wait for click or key to close."""
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
            if event.type == pygame.QUIT:
                waiting = False
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                waiting = False
        clock.tick(FPS)


def _draw_sidebar(
    screen: pygame.Surface,
    sidebar: pygame.Rect,
    small_font: pygame.font.Font,
    btn_font: pygame.font.Font,
) -> None:
    """Draw turn info, possible moves, and End turn button."""
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
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    font = pygame.font.Font(None, FONT_SIZE_CELL)
    small_font = pygame.font.Font(None, FONT_SIZE_SMALL)
    btn_font = pygame.font.Font(None, FONT_SIZE_BTN)

    def on_combat(target_id: TerritoryId) -> None:
        set_owner(target_id, current_team())

    set_combat_hook(on_combat)

    clock = pygame.time.Clock()
    running = True
    while running:
        sidebar = sidebar_rect()
        running = _handle_events(sidebar)
        if not running:
            break

        screen.fill(BG_COLOR)
        _draw_grid(screen, font)
        _draw_sidebar(screen, sidebar, small_font, btn_font)
        pygame.display.flip()
        if is_game_over():
            w = winner()
            if w is not None:
                _show_winner_popup(screen, w, clock)
            break
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
