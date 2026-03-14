"""
Pygame 2×2 territory grid. Run with: python -m src.game
"""

import pygame
from .territory import (
    GRID_ROWS,
    GRID_COLS,
    get_territory_at,
    owner,
    set_owner,
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


def cell_rect(row: int, col: int) -> pygame.Rect:
    """Rect for a grid cell (left side only)."""
    x = MARGIN + col * (CELL_SIZE + MARGIN)
    y = MARGIN + row * (CELL_SIZE + MARGIN)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def sidebar_rect() -> pygame.Rect:
    """Rect for the right-hand sidebar."""
    return pygame.Rect(GRID_WIDTH + MARGIN, 0, SIDEBAR_WIDTH, HEIGHT)


def end_turn_button_rect() -> pygame.Rect:
    """Rect for the End turn button inside the sidebar."""
    sx = sidebar_rect().x + SIDEBAR_PAD
    sy = HEIGHT - MARGIN - BUTTON_HEIGHT
    return pygame.Rect(sx, sy, SIDEBAR_WIDTH - 2 * SIDEBAR_PAD, BUTTON_HEIGHT)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    font = pygame.font.Font(None, 72)
    bg = (30, 30, 40)
    team_colors = {"Red": (180, 70, 70), "Blue": (70, 70, 180)}
    text_color = (220, 220, 230)

    # Clicking an enemy adjacent square attacks it and it switches to current team
    def on_combat(target_id: str) -> None:
        set_owner(target_id, current_team())

    set_combat_hook(on_combat)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if end_turn_button_rect().collidepoint(event.pos):
                    skip()
                else:
                    # Click on grid cell: attack if it's a valid target
                    for row in range(GRID_ROWS):
                        for col in range(GRID_COLS):
                            if cell_rect(row, col).collidepoint(event.pos):
                                tid = get_territory_at(row, col)
                                if tid is not None and tid in valid_attack_targets():
                                    try:
                                        attack(tid)
                                    except ValueError:
                                        pass
                                break

        screen.fill(bg)

        # Left: 2×2 grid only
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                tid = get_territory_at(row, col)
                if tid is None:
                    continue
                r = cell_rect(row, col)
                cell_color = team_colors[owner(tid)]
                pygame.draw.rect(screen, cell_color, r, border_radius=8)
                text = font.render(tid, True, text_color)
                tr = text.get_rect(center=r.center)
                screen.blit(text, tr)

        # Right: sidebar (turn, possible moves, End turn)
        sidebar = sidebar_rect()
        pygame.draw.rect(screen, (45, 45, 55), sidebar)
        pygame.draw.line(screen, (70, 70, 85), (sidebar.left, 0), (sidebar.left, HEIGHT), 2)

        small_font = pygame.font.Font(None, 28)
        btn_font = pygame.font.Font(None, 36)
        y = MARGIN

        # Who's turn
        turn_label = f"{current_team()}'s turn"
        turn_surf = btn_font.render(turn_label, True, team_colors[current_team()])
        turn_rect = turn_surf.get_rect(x=sidebar.x + SIDEBAR_PAD, y=y)
        screen.blit(turn_surf, turn_rect)
        y = turn_rect.bottom + 20

        # Possible moves
        targets = valid_attack_targets()
        skip_ok = can_skip()
        moves_title = small_font.render("Possible moves", True, (180, 180, 200))
        screen.blit(moves_title, (sidebar.x + SIDEBAR_PAD, y))
        y += moves_title.get_height() + 6
        attack_txt = small_font.render(f"Attack: {targets if targets else 'none'}", True, text_color)
        screen.blit(attack_txt, (sidebar.x + SIDEBAR_PAD, y))
        y += attack_txt.get_height() + 2
        skip_txt = small_font.render(f"Skip: {'yes' if skip_ok else 'no'}", True, text_color)
        screen.blit(skip_txt, (sidebar.x + SIDEBAR_PAD, y))

        # End turn button at bottom of sidebar
        btn = end_turn_button_rect()
        pygame.draw.rect(screen, (90, 90, 110), btn, border_radius=8)
        btn_text = btn_font.render("End turn", True, text_color)
        screen.blit(btn_text, btn_text.get_rect(center=btn.center))

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
