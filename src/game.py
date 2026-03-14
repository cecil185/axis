"""
Pygame 2×2 territory grid. Run with: python -m src.game
"""

import pygame
from .territory import (
    ALL_TERRITORY_IDS,
    GRID_ROWS,
    GRID_COLS,
    get_territory_at,
)

# Window
CELL_SIZE = 120
MARGIN = 20
WIDTH = GRID_COLS * CELL_SIZE + (GRID_COLS + 1) * MARGIN
HEIGHT = GRID_ROWS * CELL_SIZE + (GRID_ROWS + 1) * MARGIN
TITLE = "Territory Grid (2×2)"


def cell_rect(row: int, col: int) -> pygame.Rect:
    x = MARGIN + col * (CELL_SIZE + MARGIN)
    y = MARGIN + row * (CELL_SIZE + MARGIN)
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    font = pygame.font.Font(None, 72)
    bg = (30, 30, 40)
    cell_color = (70, 80, 100)
    text_color = (220, 220, 230)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(bg)
        for row in range(GRID_ROWS):
            for col in range(GRID_COLS):
                tid = get_territory_at(row, col)
                if tid is None:
                    continue
                r = cell_rect(row, col)
                pygame.draw.rect(screen, cell_color, r, border_radius=8)
                text = font.render(tid, True, text_color)
                tr = text.get_rect(center=r.center)
                screen.blit(text, tr)

        pygame.display.flip()
        pygame.time.Clock().tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
