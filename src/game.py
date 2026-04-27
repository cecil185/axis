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
    territory_at_point_polygon,
    territory_polygon,
    TerritoryId,
    winner,
)
from .state import current_team, end_turn
from .valid_actions import can_skip, valid_attack_targets
from .actions import attack, set_combat_hook, skip
from .combat_loop import CombatLoop, CombatState, CombatStatus
from .units import ALL_UNIT_TYPES, UnitType, set_units, units as territory_units, total_units
from .economy import (
    UNIT_COSTS,
    buy_unit,
    clear_pending,
    get_balance,
    get_pending,
    place_unit,
)
from .territory import ipc_value as territory_ipc_value
from .movement import reachable_territories
from .movement_phase import (
    _moved_from as _combat_moved_from,
    end_movement_phase,
    move_unit,
    pending_battles,
    reset_movement_phase,
    resolve_next_battle,
    skip_all_battles,
)
from .ncm_phase import (
    end_ncm_phase,
    ncm_move_unit,
    ncm_moved_from,
    reset_ncm_phase,
)

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
# (attacker_team, combat_state, defending_territory_id, attacking_territory_id | None)
# combat_state is the terminal CombatState snapshot from CombatLoop.
_last_combat: tuple[str, CombatState, TerritoryId, TerritoryId | None] | None = None

# Currently selected territory to attack FROM (green outline); None if none selected
_selected_territory: TerritoryId | None = None

# UI phase (CEC-12, CEC-18):
#   "movement" -> combat-movement: select an owned territory and click a
#                  reachable destination to move all its units. "Done Moving"
#                  advances to "main".
#   "main"     -> combat / attack flow.
#   "ncm"      -> non-combat movement (CEC-18).
# Toggled via the right-side sidebar button.
_ui_phase: str = "movement"

# Economy sub-phase (CEC-16) progressed by the End Turn button:
#   "purchase"  -> buy units (sidebar buttons); End Turn -> "action"
#   "action"    -> attack / ncm flow as before; End Turn -> "placement"
#   "placement" -> place pending units on owned territories; End Turn -> end
#                  turn, flush pending queue, advance to next team -> "purchase"
_eco_phase: str = "purchase"

# Currently selected pending unit type for placement (None = no selection).
_placement_unit: "UnitType | None" = None

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


def _movement_reachable(tid: TerritoryId) -> set[TerritoryId]:
    """Return all territories reachable from `tid` during the combat-movement phase.

    Combines reachable sets across the unit types present at `tid`. Combat
    movement may enter friendly, enemy, or neutral territories — the full
    result is returned without owner filtering.
    """
    team = current_team()
    if owner(tid) != team:
        return set()
    stack = territory_units(tid, team)
    has_tanks = stack.get("tanks", 0) > 0
    has_inf = stack.get("infantry", 0) > 0
    reach: set[TerritoryId] = set()
    if has_tanks:
        reach |= reachable_territories(tid, team, "tanks")
    if has_inf:
        reach |= reachable_territories(tid, team, "infantry")
    return reach


def _handle_movement_click(tid: TerritoryId | None) -> None:
    """Click handler for the combat-movement phase (CEC-12).

    - tid is None (clicked empty space) -> deselect.
    - tid is the currently selected territory -> deselect (toggle).
    - tid is owned by current team with units -> select.
    - tid is in the reachable set of the current selection -> move all units
      from the selection to tid via move_unit().
    - Otherwise -> deselect.
    """
    global _selected_territory
    if tid is None:
        _selected_territory = None
        return
    if tid == _selected_territory:
        _selected_territory = None
        return
    team = current_team()
    if (
        _selected_territory is not None
        and tid in _movement_reachable(_selected_territory)
    ):
        src = _selected_territory
        stack = territory_units(src, team)
        inf = stack.get("infantry", 0)
        tnk = stack.get("tanks", 0)
        try:
            if inf > 0:
                move_unit(src, tid, team, "infantry", inf)
            if tnk > 0:
                move_unit(src, tid, team, "tanks", tnk)
        except ValueError as e:
            logging.warning("Invalid move ignored: %s", e)
        _selected_territory = None
        return
    if owner(tid) == team and total_units(tid, team) > 0:
        _selected_territory = tid
        return
    _selected_territory = None


def _advance_movement_to_combat() -> None:
    """End combat-movement and switch the UI to the combat (main) flow."""
    global _ui_phase, _selected_territory
    end_movement_phase()
    _ui_phase = "main"
    _selected_territory = None


def _begin_movement_phase() -> None:
    """Reset combat-movement state for a fresh turn (CEC-12)."""
    global _ui_phase, _selected_territory
    reset_movement_phase()
    _ui_phase = "movement"
    _selected_territory = None




# --- Non-Combat Movement helpers (CEC-18) ---------------------------------
# NCM runs after the combat phase. Destinations must be friendly-owned (NCM
# may never start a battle); territories that already moved during the combat-
# movement phase this turn are also locked from NCM.


def _ncm_friendly_destinations(tid: TerritoryId) -> set[TerritoryId]:
    """Return friendly-owned NCM destinations reachable from `tid`.

    Range rules match combat movement (infantry 1, tanks 2). When the source
    has both unit types, both reach sets are unioned. The result is filtered
    to territories owned by the current team — NCM may never enter enemy or
    neutral territory.
    """
    team = current_team()
    if owner(tid) != team:
        return set()
    stack = territory_units(tid, team)
    has_tanks = stack.get("tanks", 0) > 0
    has_inf = stack.get("infantry", 0) > 0
    reach: set[TerritoryId] = set()
    if has_tanks:
        reach |= reachable_territories(tid, team, "tanks")
    if has_inf:
        reach |= reachable_territories(tid, team, "infantry")
    return {t for t in reach if owner(t) == team}


def _ncm_selectable_sources() -> set[TerritoryId]:
    """Return owned territories that may move FROM during NCM.

    Selectable iff owned by the current team, has at least one unit, and has
    not already been moved-from this turn (combat movement OR NCM).
    """
    team = current_team()
    locked = _combat_moved_from | ncm_moved_from()
    return {
        tid for tid in ALL_TERRITORY_IDS
        if owner(tid) == team
        and total_units(tid, team) > 0
        and tid not in locked
    }


def _handle_ncm_click(tid: TerritoryId | None) -> None:
    """Click handler for the Non-Combat Movement phase (CEC-18).

    - tid is None or a non-friendly territory -> deselect.
    - tid is the currently selected source -> deselect (toggle).
    - tid is a friendly destination of the current selection -> move ALL
      units (both infantry and tanks) from the source to tid.
    - Otherwise, if tid is a still-selectable owned territory -> select it.
    """
    global _selected_territory
    team = current_team()

    if tid is None:
        _selected_territory = None
        return
    if tid == _selected_territory:
        _selected_territory = None
        return

    if _selected_territory is not None:
        destinations = _ncm_friendly_destinations(_selected_territory)
        if tid in destinations:
            src = _selected_territory
            stack = territory_units(src, team)
            inf = stack.get("infantry", 0)
            tnk = stack.get("tanks", 0)
            try:
                if inf > 0:
                    ncm_move_unit(src, tid, team, "infantry", inf)
                    if tnk > 0:
                        from_stack = territory_units(src, team)
                        to_stack = territory_units(tid, team)
                        new_from = dict(from_stack)
                        new_from["tanks"] = from_stack.get("tanks", 0) - tnk
                        new_to = dict(to_stack)
                        new_to["tanks"] = to_stack.get("tanks", 0) + tnk
                        set_units(src, team, new_from)
                        set_units(tid, team, new_to)
                elif tnk > 0:
                    ncm_move_unit(src, tid, team, "tanks", tnk)
            except ValueError as e:
                logging.warning("Invalid NCM move ignored: %s", e)
            _selected_territory = None
            return

    if tid in _ncm_selectable_sources():
        _selected_territory = tid
    else:
        _selected_territory = None


def _begin_ncm_phase() -> None:
    """Enter the Non-Combat Movement phase from the combat (main) phase."""
    global _ui_phase, _selected_territory
    reset_ncm_phase()
    _ui_phase = "ncm"
    _selected_territory = None


def _advance_ncm_to_end_turn() -> None:
    """Finalise NCM, advance the turn, reset to movement phase for next team."""
    global _ui_phase, _selected_territory, _placement_unit
    # CEC-16: any unplaced reinforcements are forfeited at end of turn.
    clear_pending(current_team())
    _placement_unit = None
    end_ncm_phase()
    end_turn()
    reset_ncm_phase()
    reset_movement_phase()
    _ui_phase = "movement"
    _selected_territory = None

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


# --- Economy UI rect helpers (CEC-16) -------------------------------------
ECO_ROW_HEIGHT = 32
ECO_PANEL_HEIGHT = 32 + ECO_ROW_HEIGHT * 2 + 12  # header + 2 unit rows + padding


def economy_panel_rect(sidebar: pygame.Rect | None = None) -> pygame.Rect:
    """Rect of the economy purchase / placement panel inside the sidebar.

    Positioned just above the battle-queue / End Turn button stack so it does
    not overlap with the multi-battle UI (CEC-17).
    """
    s = sidebar if sidebar is not None else right_sidebar_rect()
    end_btn = end_turn_button_rect(s)
    panel_bottom = end_btn.y - 12 - 2 * (BUTTON_HEIGHT + 8)
    return pygame.Rect(
        s.x + SIDEBAR_PAD,
        panel_bottom - ECO_PANEL_HEIGHT,
        SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD,
        ECO_PANEL_HEIGHT,
    )


def unit_row_rect(
    unit_type: UnitType, sidebar: pygame.Rect | None = None
) -> pygame.Rect:
    """Rect of a single unit-type row inside the economy panel."""
    panel = economy_panel_rect(sidebar)
    idx = ALL_UNIT_TYPES.index(unit_type)
    return pygame.Rect(
        panel.x + 4,
        panel.y + 32 + idx * ECO_ROW_HEIGHT,
        panel.width - 8,
        ECO_ROW_HEIGHT - 4,
    )


def income_for(team) -> int:
    """Sum of ipc_value over territories currently owned by *team*."""
    return sum(territory_ipc_value(tid) for tid in ALL_TERRITORY_IDS if owner(tid) == team)


def territory_count(team) -> int:
    """Number of territories owned by *team*."""
    return sum(1 for tid in ALL_TERRITORY_IDS if owner(tid) == team)


# --- Multi-battle UI rect helpers (CEC-17) --------------------------------
# When the pending-battle queue is non-empty (battles registered during the
# movement phase), the sidebar shows a counter ("N battles remaining") and
# two stacked buttons: "Next Battle" (resolve the next one) and "Skip All"
# (discard the rest of the queue without rolling). Buttons sit just above
# the End Turn button.

BATTLE_BUTTON_GAP = 8


def battle_queue_label_text(count: int | None = None) -> str:
    """Return the sidebar label for the pending-battle counter.

    When `count` is None, queries `pending_battles()` for the live count.
    Returns an empty string when no battles are pending.
    Pluralises: "1 battle remaining" vs. "N battles remaining".
    """
    if count is None:
        count = len(pending_battles())
    if count <= 0:
        return ""
    noun = "battle" if count == 1 else "battles"
    return f"{count} {noun} remaining"


def next_battle_button_rect(sidebar: pygame.Rect | None = None) -> pygame.Rect:
    """Rect of the 'Next Battle' button, two rows above the End Turn button."""
    s = sidebar if sidebar is not None else right_sidebar_rect()
    end_btn = end_turn_button_rect(s)
    skip_top = end_btn.y - BATTLE_BUTTON_GAP - BUTTON_HEIGHT
    next_top = skip_top - BATTLE_BUTTON_GAP - BUTTON_HEIGHT
    return pygame.Rect(
        s.x + SIDEBAR_PAD,
        next_top,
        SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD,
        BUTTON_HEIGHT,
    )


def skip_all_battles_button_rect(sidebar: pygame.Rect | None = None) -> pygame.Rect:
    """Rect of the 'Skip All' button, sitting directly above the End Turn button."""
    s = sidebar if sidebar is not None else right_sidebar_rect()
    end_btn = end_turn_button_rect(s)
    return pygame.Rect(
        s.x + SIDEBAR_PAD,
        end_btn.y - BATTLE_BUTTON_GAP - BUTTON_HEIGHT,
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


def _handle_economy_click(pos: tuple[int, int], sidebar: pygame.Rect) -> bool:
    """Handle a left-click on the economy panel (CEC-16).

    Returns True if the click was inside the economy panel (consumed).
    During non-NCM phases, clicks buy a unit (if affordable).
    During NCM, clicks select the pending unit type for placement.
    """
    global _placement_unit
    panel = economy_panel_rect(sidebar)
    if not panel.collidepoint(pos):
        return False
    team = current_team()
    placement = (_ui_phase == "ncm")
    for ut in ALL_UNIT_TYPES:
        if unit_row_rect(ut, sidebar).collidepoint(pos):
            if placement:
                if get_pending(team).get(ut, 0) > 0:
                    _placement_unit = ut
                else:
                    _placement_unit = None
            else:
                try:
                    buy_unit(team, ut)
                except ValueError as e:
                    logging.info("Cannot buy %s: %s", ut, e)
            return True
    return True


def _handle_placement_map_click(tid: TerritoryId | None) -> None:
    """Place a pending unit of `_placement_unit` on `tid` (CEC-16)."""
    global _placement_unit
    if tid is None or _placement_unit is None:
        return
    team = current_team()
    if owner(tid) != team:
        return
    try:
        place_unit(team, tid, _placement_unit)
    except ValueError as e:
        logging.info("Cannot place %s on %s: %s", _placement_unit, tid, e)
    if get_pending(team).get(_placement_unit, 0) <= 0:
        _placement_unit = None


def _handle_events(
    sidebar: pygame.Rect,
    map_surf: pygame.Surface | None,
    map_rect: pygame.Rect,
    ui_manager: "pygame_gui.UIManager | None" = None,
    end_turn_btn: "pygame_gui.elements.UIButton | None" = None,
    done_moving_btn: "pygame_gui.elements.UIButton | None" = None,
    next_battle_btn: "pygame_gui.elements.UIButton | None" = None,
    skip_all_btn: "pygame_gui.elements.UIButton | None" = None,
    on_battle_resolved: "callable | None" = None,
) -> bool:
    global _selected_territory, _placement_unit
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return False

        # Let pygame-gui process the event first so button states update
        if ui_manager is not None:
            ui_manager.process_events(event)

        # UIButton press (pygame-gui event)
        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if (
                done_moving_btn is not None
                and event.ui_element is done_moving_btn
                and _ui_phase == "movement"
            ):
                if not is_game_over():
                    _advance_movement_to_combat()
                continue
            # Multi-battle UI (CEC-17): Next Battle -> resolve next pending battle.
            if next_battle_btn is not None and event.ui_element is next_battle_btn:
                if not is_game_over() and pending_battles():
                    result = resolve_next_battle(current_team())
                    if on_battle_resolved is not None:
                        on_battle_resolved(result)
                continue
            # Multi-battle UI (CEC-17): Skip All -> discard the rest of the queue.
            if skip_all_btn is not None and event.ui_element is skip_all_btn:
                if not is_game_over():
                    skip_all_battles(current_team())
                continue
            if end_turn_btn is not None and event.ui_element is end_turn_btn:
                if not is_game_over():
                    if _ui_phase == "main":
                        _begin_ncm_phase()
                    elif _ui_phase == "ncm":
                        _advance_ncm_to_end_turn()
                    else:
                        skip()
                        _begin_movement_phase()
            continue

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if is_game_over():
                # No actions allowed once the game has ended
                continue
            # Multi-battle UI fallback (no ui_manager): handle Next/Skip All by rect.
            if ui_manager is None and pending_battles():
                if next_battle_button_rect(sidebar).collidepoint(event.pos):
                    result = resolve_next_battle(current_team())
                    if on_battle_resolved is not None:
                        on_battle_resolved(result)
                    continue
                if skip_all_battles_button_rect(sidebar).collidepoint(event.pos):
                    skip_all_battles(current_team())
                    continue
            # If using raw button fallback (no ui_manager), handle it here
            if ui_manager is None and end_turn_button_rect(sidebar).collidepoint(event.pos):
                if _ui_phase == "movement":
                    _advance_movement_to_combat()
                elif _ui_phase == "main":
                    _begin_ncm_phase()
                elif _ui_phase == "ncm":
                    _advance_ncm_to_end_turn()
                else:
                    skip()
                    _begin_movement_phase()
                continue

            # Economy panel click (CEC-16): consume purchase / placement-row clicks.
            if _handle_economy_click(event.pos, sidebar):
                continue

            r = map_rect
            mx, my, mw, mh = r.x, r.y, r.w, r.h
            tid = territory_at_point((mx, my, mw, mh), event.pos[0], event.pos[1], MARKER_RADIUS + 4)

            # Placement (NCM) map click: place selected unit on owned territory.
            if _ui_phase == "ncm" and _placement_unit is not None:
                _handle_placement_map_click(tid)
                continue

            if _ui_phase == "movement":
                _handle_movement_click(tid)
                continue
            if _ui_phase == "ncm":
                _handle_ncm_click(tid)
                continue

            # Combat (main) phase: existing attack flow.
            if tid is None:
                _selected_territory = None
            elif owner(tid) == current_team():
                _selected_territory = tid
            elif (
                _selected_territory is not None
                and tid in valid_attack_targets()
                and tid in neighbors(_selected_territory)
            ):
                try:
                    attack(tid)
                except ValueError as e:
                    logging.warning("Invalid attack ignored: %s", e)
                _selected_territory = None
            else:
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
    highlight_targets: set[TerritoryId] | None = None,
) -> None:
    """Draw map image and filled polygon territory regions.

    Each territory is drawn as a semi-transparent filled polygon colored by owner
    (red / blue / neutral-grey).  The selected territory gets a green polygon
    outline; valid targets (attack targets in combat phase, reachable
    destinations in combat-movement phase) get a pulsing yellow outline.

    Unit icons and text labels are still centred on the territory's x_frac/y_frac
    centre point so they remain readable regardless of polygon shape.

    When `highlight_targets` is provided it overrides the default attack-targets
    set entirely (used by the combat-movement phase / NCM).
    """
    if map_surf is not None:
        screen.blit(map_surf, map_rect.topleft)
    mx, my, mw, mh = map_rect.x, map_rect.y, map_rect.w, map_rect.h
    map_tuple = (mx, my, mw, mh)
    if highlight_targets is not None:
        selected_targets = set(highlight_targets)
    else:
        all_targets = set(valid_attack_targets())
        # When a territory is selected, pulse outlines only on its attackable neighbours
        if selected is not None:
            selected_targets = {t for t in neighbors(selected) if t in all_targets}
        else:
            selected_targets = all_targets

    # Determine whether the mouse is over a polygon territory (for pulse boost)
    hovered_tid: TerritoryId | None = None
    if mouse_pos is not None and map_rect.collidepoint(mouse_pos):
        hovered_tid = territory_at_point_polygon(map_tuple, mouse_pos[0], mouse_pos[1])

    for tid in ALL_TERRITORY_IDS:
        poly_px = territory_polygon(tid, map_tuple)
        team_color = TEAM_COLORS[owner(tid)]

        # --- Filled polygon (semi-transparent) ---------------------------------
        fill_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
        # Shift polygon coords to fill_surf space (which starts at mx, my)
        local_poly = [(px - mx, py - my) for px, py in poly_px]
        r, g, b = team_color
        pygame.draw.polygon(fill_surf, (r, g, b, 80), local_poly)
        screen.blit(fill_surf, (mx, my))

        # --- Polygon border (solid, thin) --------------------------------------
        pygame.draw.polygon(screen, SIDEBAR_BORDER, poly_px, 1)

        # --- Green outline for selected territory ------------------------------
        if tid == selected:
            pygame.draw.polygon(screen, (80, 200, 80), poly_px, 3)

        # --- Pulsing yellow outline on valid attack targets --------------------
        if tid in selected_targets:
            alpha = 255 if tid == hovered_tid else pulse_alpha
            r2, g2, b2 = HOVER_HIGHLIGHT_COLOR
            pulse_surf = pygame.Surface((mw, mh), pygame.SRCALPHA)
            pygame.draw.polygon(
                pulse_surf,
                (r2, g2, b2, alpha),
                local_poly,
                HOVER_HIGHLIGHT_WIDTH,
            )
            screen.blit(pulse_surf, (mx, my))

        # --- Unit icons centred on the territory's map centre point -----------
        x_frac, y_frac = map_position(tid)
        tx = int(mx + x_frac * mw)
        ty = int(my + y_frac * mh)
        icon_data = _unit_icon_data(tid)
        if icon_data["team"] != "Neutral":
            icon_color = TEAM_COLORS[icon_data["team"]]  # type: ignore[index]
            icon_positions = _icon_positions_for_territory(tx, ty, MARKER_RADIUS)
            if icon_data["infantry"]:  # type: ignore[truthy-bool]
                inf_x, inf_y = icon_positions["infantry"]
                _draw_infantry_icon(screen, inf_x, inf_y, icon_color, _ICON_SIZE)
            if icon_data["tanks"]:  # type: ignore[truthy-bool]
                tnk_x, tnk_y = icon_positions["tanks"]
                _draw_tank_icon(screen, tnk_x, tnk_y, icon_color, _ICON_SIZE)

        # --- Unit count label below territory centre --------------------------
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
            label_x = tx - label_surf.get_width() // 2
            label_y = ty + MARKER_RADIUS + 2
            shadow_surf = unit_label_font.render(label_text, True, (0, 0, 0))
            screen.blit(shadow_surf, (label_x + 1, label_y + 1))
            screen.blit(label_surf, (label_x, label_y))


def _show_combat_popup(
    screen: pygame.Surface,
    att_team: str,
    combat_state: CombatState,
    def_territory_id: TerritoryId,
    clock: pygame.time.Clock,
    att_territory_id: TerritoryId | None = None,
) -> tuple[bool, bool] | None:
    """Show the multi-phase combat popup.

    Returns:
      - None for terminal status (ATTACKER_WINS / DEFENDER_WINS /
        RETREAT_NO_CHANGE) -- the user dismisses with any key.
      - (attacker_continues, defender_continues) for AWAITING_DECISION -- the
        user picks Continue/Retreat for each side via on-screen buttons; the
        popup blocks until both sides have chosen. The caller passes these
        into CombatLoop.submit_decision().
    """
    def_team: str = "Blue" if att_team == "Red" else "Red"
    status = combat_state["status"]
    is_terminal = status in (
        CombatStatus.ATTACKER_WINS,
        CombatStatus.DEFENDER_WINS,
        CombatStatus.RETREAT_NO_CHANGE,
    )
    if status == CombatStatus.ATTACKER_WINS:
        outcome = f"{att_team} wins!"
        outcome_color = TEAM_COLORS[att_team]
    elif status == CombatStatus.DEFENDER_WINS:
        outcome = "Defender holds!"
        outcome_color = TEAM_COLORS[def_team]
    elif status == CombatStatus.RETREAT_NO_CHANGE:
        outcome = "Combat ended -- retreat"
        outcome_color = TEXT_COLOR
    else:  # AWAITING_DECISION (mid-battle, more phases coming)
        outcome = "Phase complete"
        outcome_color = TEXT_COLOR
    def_name = display_name(def_territory_id)
    att_rolls = combat_state["last_att_rolls"]
    def_rolls = combat_state["last_def_rolls"]
    rem_att = combat_state["remaining_attackers"]
    rem_def = combat_state["remaining_defenders"]

    # AWAITING_DECISION needs two extra rows of Continue/Retreat per side.
    popup_w = 380
    popup_h = 270 if is_terminal else 360
    popup_x = (WIDTH - popup_w) // 2
    popup_y = (HEIGHT - popup_h) // 2

    btn_w, btn_h = 130, 32
    btn_gap_x = 16
    row_y_att = popup_y + 218
    row_y_def = popup_y + 270
    att_continue_rect = pygame.Rect(
        popup_x + (popup_w - 2 * btn_w - btn_gap_x) // 2, row_y_att, btn_w, btn_h
    )
    att_retreat_rect = pygame.Rect(
        att_continue_rect.right + btn_gap_x, row_y_att, btn_w, btn_h
    )
    def_continue_rect = pygame.Rect(att_continue_rect.x, row_y_def, btn_w, btn_h)
    def_retreat_rect = pygame.Rect(att_retreat_rect.x, row_y_def, btn_w, btn_h)

    att_choice: bool | None = None  # True=Continue, False=Retreat, None=unchosen
    def_choice: bool | None = None

    def _render() -> None:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        popup_rect = pygame.Rect(popup_x, popup_y, popup_w, popup_h)
        pygame.draw.rect(screen, SIDEBAR_BG, popup_rect, border_radius=BORDER_RADIUS)
        pygame.draw.rect(screen, SIDEBAR_BORDER, popup_rect, 2, border_radius=BORDER_RADIUS)
        font = pygame.font.Font(None, 48)
        small_font = pygame.font.Font(None, 24)
        title = font.render("Combat", True, MOVES_TITLE_COLOR)
        screen.blit(title, title.get_rect(centerx=popup_rect.centerx, top=popup_y + 10))
        phase_label = small_font.render(
            f"Phase {combat_state['phase_index']}: {att_team} {att_rolls} vs {def_team} {def_rolls}",
            True,
            TEXT_COLOR,
        )
        screen.blit(phase_label, phase_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 56))
        dmg_label = small_font.render(
            f"Damage: att {combat_state['last_att_damage']}  def {combat_state['last_def_damage']}",
            True,
            MOVES_TITLE_COLOR,
        )
        screen.blit(dmg_label, dmg_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 82))
        rem_label = small_font.render(
            f"Remaining: {att_team} {rem_att.get('infantry', 0)}i {rem_att.get('tanks', 0)}t  |  "
            f"{def_team} {rem_def.get('infantry', 0)}i {rem_def.get('tanks', 0)}t",
            True,
            TEXT_COLOR,
        )
        screen.blit(rem_label, rem_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 108))
        defending_label = small_font.render(f"Defending: {def_name}", True, MOVES_TITLE_COLOR)
        screen.blit(defending_label, defending_label.get_rect(centerx=popup_rect.centerx, top=popup_y + 134))
        outcome_surf = font.render(outcome, True, outcome_color)
        screen.blit(outcome_surf, outcome_surf.get_rect(centerx=popup_rect.centerx, top=popup_y + 162))

        if is_terminal:
            hint = pygame.font.Font(None, 24).render(
                "Press any key to close", True, MOVES_TITLE_COLOR
            )
            screen.blit(hint, hint.get_rect(centerx=popup_rect.centerx, top=popup_y + 222))
            return

        # AWAITING_DECISION: per-side Continue / Retreat button rows.
        def _draw_choice_button(
            rect: pygame.Rect, label: str, chosen: bool | None, this_choice: bool
        ) -> None:
            bg = (110, 160, 110) if (chosen is not None and chosen is this_choice) else BTN_BG
            pygame.draw.rect(screen, bg, rect, border_radius=BORDER_RADIUS)
            pygame.draw.rect(screen, SIDEBAR_BORDER, rect, 1, border_radius=BORDER_RADIUS)
            txt = small_font.render(label, True, TEXT_COLOR)
            screen.blit(txt, txt.get_rect(center=rect.center))

        att_row_label = small_font.render(f"{att_team} (attacker)", True, TEAM_COLORS[att_team])
        screen.blit(att_row_label, att_row_label.get_rect(x=popup_x + 16, top=row_y_att - 22))
        _draw_choice_button(att_continue_rect, "Continue", att_choice, True)
        _draw_choice_button(att_retreat_rect, "Retreat", att_choice, False)

        def_row_label = small_font.render(f"{def_team} (defender)", True, TEAM_COLORS[def_team])
        screen.blit(def_row_label, def_row_label.get_rect(x=popup_x + 16, top=row_y_def - 22))
        _draw_choice_button(def_continue_rect, "Continue", def_choice, True)
        _draw_choice_button(def_retreat_rect, "Retreat", def_choice, False)

    _render()
    pygame.display.flip()

    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                waiting = False
                if is_terminal:
                    return None
                # Treat window-close mid-battle as a mutual retreat.
                return (False, False)
            if is_terminal:
                if event.type == pygame.KEYDOWN:
                    waiting = False
                continue
            # AWAITING_DECISION: clicks on the four buttons set each side's choice.
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if att_continue_rect.collidepoint(event.pos):
                    att_choice = True
                elif att_retreat_rect.collidepoint(event.pos):
                    att_choice = False
                elif def_continue_rect.collidepoint(event.pos):
                    def_choice = True
                elif def_retreat_rect.collidepoint(event.pos):
                    def_choice = False
                if att_choice is not None and def_choice is not None:
                    waiting = False
        if waiting:
            _render()
            pygame.display.flip()
        clock.tick(FPS)

    if is_terminal:
        return None
    return (bool(att_choice), bool(def_choice))


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


def _draw_bottom_bar(
    screen: pygame.Surface,
    bar: pygame.Rect,
    small_font: pygame.font.Font,
    team_labels: "dict[str, pygame_gui.elements.UILabel] | None" = None,
) -> None:
    """Draw bottom bar under the map with a team legend showing territory counts.

    When team_labels is provided, uses pygame-gui UILabel widgets for the count
    text (updated each frame via set_text) so labels participate in the GUI theme.
    The colored dot markers are still drawn with pygame (no UIImage equivalent).
    """
    pygame.draw.rect(screen, SIDEBAR_BG, bar)
    pygame.draw.line(screen, SIDEBAR_BORDER, (0, bar.top), (bar.width, bar.top), SIDEBAR_LINE_WIDTH)

    dot_radius = 10
    x = bar.x + MARGIN
    cy = bar.centery

    for team in ("Red", "Blue"):
        count = sum(1 for tid in ALL_TERRITORY_IDS if owner(tid) == team)
        color = TEAM_COLORS[team]
        pygame.draw.circle(screen, color, (x + dot_radius, cy), dot_radius)
        if team_labels is not None and team in team_labels:
            # Update the UILabel text each frame; pygame-gui draws it via draw_ui
            team_labels[team].set_text(f"{team}: {count}")
            # Advance x by the label widget's width so dots don't overlap
            x += dot_radius * 2 + GAP + team_labels[team].rect.width + MARGIN
        else:
            label = small_font.render(f"{team}: {count}", True, TEXT_COLOR)
            screen.blit(label, (x + dot_radius * 2 + GAP, cy - label.get_height() // 2))
            x += dot_radius * 2 + GAP + label.get_width() + MARGIN


def _draw_right_sidebar(
    screen: pygame.Surface,
    sidebar: pygame.Rect,
    small_font: pygame.font.Font,
    btn_font: pygame.font.Font,
    use_gui_button: bool = False,
    sidebar_panel: "pygame_gui.elements.UIPanel | None" = None,
) -> None:
    """Draw the right sidebar.

    When sidebar_panel is provided the background rect is rendered by the
    pygame-gui UIPanel widget (draw_ui handles it); only the dividing line
    and text content are drawn here. When sidebar_panel is None, falls back
    to raw pygame.draw.rect for the background (headless / test mode).
    """
    if sidebar_panel is None:
        # Fallback: raw background (no UIPanel available)
        pygame.draw.rect(screen, SIDEBAR_BG, sidebar)
    # Always draw the left border line over the panel
    pygame.draw.line(screen, SIDEBAR_BORDER, (sidebar.left, 0), (sidebar.left, HEIGHT), SIDEBAR_LINE_WIDTH)
    y = MARGIN
    turn_label = f"{current_team()}'s turn"
    turn_surf = btn_font.render(turn_label, True, TEAM_COLORS[current_team()])
    turn_rect = turn_surf.get_rect(x=sidebar.x + SIDEBAR_PAD, y=y)
    screen.blit(turn_surf, turn_rect)
    y = turn_rect.bottom + SIDEBAR_LINE_GAP
    if _ui_phase == "movement":
        phase_surf = small_font.render("Combat Movement", True, MOVES_TITLE_COLOR)
        phase_rect = phase_surf.get_rect(x=sidebar.x + SIDEBAR_PAD, y=y)
        screen.blit(phase_surf, phase_rect)
        y = phase_rect.bottom + SIDEBAR_TURN_GAP
    elif _ui_phase == "ncm":
        phase_surf = small_font.render("Non-Combat Movement", True, MOVES_TITLE_COLOR)
        phase_rect = phase_surf.get_rect(x=sidebar.x + SIDEBAR_PAD, y=y)
        screen.blit(phase_surf, phase_rect)
        y = phase_rect.bottom + SIDEBAR_TURN_GAP
    else:
        y += SIDEBAR_TURN_GAP
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
    y += skip_txt.get_height() + SIDEBAR_SECTION_GAP

    # --- Economy summary (always visible): both teams' balance + income (CEC-16) ---
    eco_title = small_font.render("Economy", True, MOVES_TITLE_COLOR)
    screen.blit(eco_title, (sidebar.x + SIDEBAR_PAD, y))
    y += eco_title.get_height() + SIDEBAR_LINE_GAP
    for tm in ("Red", "Blue"):
        bal = get_balance(tm)
        inc = income_for(tm)
        cnt = territory_count(tm)
        line = f"{tm}: {bal} IPC ({cnt}T->{inc})"
        line_surf = small_font.render(line, True, TEAM_COLORS[tm])
        screen.blit(line_surf, (sidebar.x + SIDEBAR_PAD, y))
        y += line_surf.get_height() + SIDEBAR_LINE_GAP

    _draw_economy_panel(screen, sidebar, small_font)

    # Draw the raw fallback button only when not using the pygame-gui UIButton
    if not use_gui_button:
        btn = end_turn_button_rect(sidebar)
        pygame.draw.rect(screen, BTN_BG, btn, border_radius=BORDER_RADIUS)
        btn_text = btn_font.render("End turn", True, TEXT_COLOR)
        screen.blit(btn_text, btn_text.get_rect(center=btn.center))


def _draw_economy_panel(
    screen: pygame.Surface,
    sidebar: pygame.Rect,
    small_font: pygame.font.Font,
) -> None:
    """Draw the purchase / placement panel inside the sidebar (CEC-16)."""
    panel = economy_panel_rect(sidebar)
    pygame.draw.rect(screen, (35, 38, 45), panel, border_radius=BORDER_RADIUS)
    pygame.draw.rect(screen, SIDEBAR_BORDER, panel, 1, border_radius=BORDER_RADIUS)
    placement = (_ui_phase == "ncm")
    header = "Place units" if placement else "Purchase units"
    header_surf = small_font.render(header, True, MOVES_TITLE_COLOR)
    screen.blit(header_surf, (panel.x + 8, panel.y + 4))
    team = current_team()
    pending = get_pending(team)
    balance = get_balance(team)
    for ut in ALL_UNIT_TYPES:
        rect = unit_row_rect(ut, sidebar)
        cost = UNIT_COSTS[ut]
        if placement:
            count = pending.get(ut, 0)
            bg = BTN_BG
            text_color = TEXT_COLOR if count > 0 else (140, 140, 140)
            row_text = f"{ut}: {count} ready"
        else:
            affordable = balance >= cost
            bg = BTN_BG if affordable else (60, 60, 60)
            text_color = TEXT_COLOR if affordable else (140, 140, 140)
            row_text = f"{ut}: {cost} IPCs"
        pygame.draw.rect(screen, bg, rect, border_radius=BORDER_RADIUS)
        if placement and _placement_unit == ut:
            pygame.draw.rect(screen, (80, 200, 80), rect, 2, border_radius=BORDER_RADIUS)
        row_surf = small_font.render(row_text, True, text_color)
        screen.blit(row_surf, row_surf.get_rect(midleft=(rect.x + 8, rect.centery)))


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
    # Combat-movement "Done Moving" button (CEC-12): occupies the same rect as
    # End Turn but is only visible during the movement phase. End Turn and
    # Done Moving are mutually exclusive — show / hide each frame based on
    # _ui_phase.
    done_moving_btn = pygame_gui.elements.UIButton(
        relative_rect=btn_rect,
        text="Done Moving",
        manager=ui_manager,
    )
    # Multi-battle UI (CEC-17): Next Battle + Skip All sit just above End Turn
    # and are only visible while the pending-battle queue is non-empty. They
    # let the player resolve battles one at a time or discard the rest.
    next_battle_btn = pygame_gui.elements.UIButton(
        relative_rect=next_battle_button_rect(sidebar),
        text="Next Battle",
        manager=ui_manager,
    )
    skip_all_btn = pygame_gui.elements.UIButton(
        relative_rect=skip_all_battles_button_rect(sidebar),
        text="Skip All",
        manager=ui_manager,
    )
    battle_queue_label = pygame_gui.elements.UILabel(
        relative_rect=pygame.Rect(
            next_battle_button_rect(sidebar).x,
            next_battle_button_rect(sidebar).y - 32,
            SIDEBAR_RIGHT_WIDTH - 2 * SIDEBAR_PAD,
            28,
        ),
        text="",
        manager=ui_manager,
    )
    # sidebar_panel is None; the sidebar background is drawn with raw pygame.draw.rect
    # in _draw_right_sidebar so that text labels rendered before ui_manager.draw_ui()
    # are not covered. The primary "styled widget container" for the sidebar is the
    # UIButton (End Turn), which replaces the previous raw pygame.draw.rect button.
    sidebar_panel = None

    # Bottom bar: styled UILabel widgets for team territory counts
    # Positioned to the right of each colored dot marker
    bar = bottom_bar_rect()
    dot_radius = 10
    label_h = 28
    label_w = 120
    label_y = bar.centery - label_h // 2
    red_label_x = bar.x + MARGIN + dot_radius * 2 + GAP
    blue_label_x = red_label_x + label_w + MARGIN + dot_radius * 2 + GAP + MARGIN
    team_labels: dict[str, pygame_gui.elements.UILabel] = {}
    for team, lx in (("Red", red_label_x), ("Blue", blue_label_x)):
        count = sum(1 for tid in ALL_TERRITORY_IDS if owner(tid) == team)
        team_labels[team] = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(lx, label_y, label_w, label_h),
            text=f"{team}: {count}",
            manager=ui_manager,
        )

    def on_combat(target_id: TerritoryId) -> None:
        global _last_combat
        att = current_team()
        defender: str = "Blue" if att == "Red" else "Red"
        att_tid = _selected_territory
        # Pull starting unit stacks from the territories.  When no attacker source
        # is selected (legacy hook usage), default to a single infantry attacker.
        if att_tid is not None:
            attackers = territory_units(att_tid, att)  # type: ignore[arg-type]
        else:
            attackers = {"infantry": 1, "tanks": 0}
        defenders = territory_units(target_id, defender)  # type: ignore[arg-type]

        loop = CombatLoop(attackers=attackers, defenders=defenders)
        # Run phases interactively. After each phase the popup refreshes with the
        # latest CombatState (CEC-9). At AWAITING_DECISION the popup returns the
        # user's Continue/Retreat choices for both sides (CEC-10) and the loop
        # advances accordingly; if either side retreats, RETREAT_NO_CHANGE ends
        # the battle with no ownership change.
        loop.run_phase()
        while True:
            state = loop.get_combat_state()
            decision = _show_combat_popup(screen, att, state, target_id, clock, att_tid)
            if state["status"] in (
                CombatStatus.ATTACKER_WINS,
                CombatStatus.DEFENDER_WINS,
                CombatStatus.RETREAT_NO_CHANGE,
            ):
                break
            # AWAITING_DECISION: feed user's per-side Continue/Retreat back into
            # the loop. submit_decision runs the next phase if both continue;
            # otherwise it sets RETREAT_NO_CHANGE and the next iteration breaks.
            att_cont, def_cont = decision if decision is not None else (True, True)
            loop.submit_decision(attacker_continues=att_cont, defender_continues=def_cont)

        # Sync surviving units back into the territories.
        if att_tid is not None:
            set_units(att_tid, att, state["remaining_attackers"])  # type: ignore[arg-type]
        set_units(target_id, defender, state["remaining_defenders"])  # type: ignore[arg-type]

        # Skip the post-combat popup in main(): all phases already shown above.
        _last_combat = None
        # ATTACKER_WINS: transfer ownership and advance survivors into the defender's tile.
        # DEFENDER_WINS / RETREAT_NO_CHANGE: ownership unchanged.
        if state["status"] == CombatStatus.ATTACKER_WINS:
            set_owner(target_id, att)  # type: ignore[arg-type]
            set_units(target_id, att, state["remaining_attackers"])  # type: ignore[arg-type]
            if att_tid is not None:
                set_units(att_tid, att, {"infantry": 0, "tanks": 0})  # type: ignore[arg-type]

    set_combat_hook(on_combat)
    clock = pygame.time.Clock()
    running = True
    while running:
        time_delta = clock.tick(FPS) / 1000.0
        map_rect = _map_rect()
        prev_team = current_team()
        # Toggle button visibility based on UI phase: only one of End Turn /
        # Done Moving is shown at a time. In NCM the End Turn button reads
        # "Done" — it finalises NCM and advances the turn (CEC-18).
        if _ui_phase == "movement":
            end_turn_btn.hide()
            done_moving_btn.show()
        else:
            done_moving_btn.hide()
            if _ui_phase == "ncm":
                end_turn_btn.set_text("Done")
            else:
                end_turn_btn.set_text("End Turn")
            end_turn_btn.show()
        # Multi-battle UI (CEC-17): show queue counter + Next/Skip All buttons
        # whenever there are pending battles outside of the movement phase.
        battles_remaining = len(pending_battles())
        if battles_remaining > 0 and _ui_phase != "movement":
            battle_queue_label.set_text(battle_queue_label_text(battles_remaining))
            battle_queue_label.show()
            next_battle_btn.show()
            skip_all_btn.show()
        else:
            battle_queue_label.set_text("")
            battle_queue_label.hide()
            next_battle_btn.hide()
            skip_all_btn.hide()

        def _on_battle_resolved(result) -> None:
            """Set _last_combat so the existing popup runs after a queue battle."""
            global _last_combat
            _last_combat = (
                result["attacker"],
                result["att_roll"],
                result["def_roll"],
                result["winner"],
                result["territory"],
                None,
            )

        running = _handle_events(
            right_sidebar_rect(),
            map_surf,
            map_rect,
            ui_manager,
            end_turn_btn,
            done_moving_btn,
            next_battle_btn,
            skip_all_btn,
            _on_battle_resolved,
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
        if _ui_phase == "movement":
            highlights = _movement_reachable(_selected_territory) if _selected_territory else set()
        elif _ui_phase == "ncm":
            highlights = (
                _ncm_friendly_destinations(_selected_territory)
                if _selected_territory
                else set()
            )
        else:
            highlights = None
        _draw_map(
            screen,
            map_rect,
            map_surf,
            mouse_pos,
            _selected_territory,
            pulse_alpha,
            unit_label_font,
            highlight_targets=highlights,
        )
        # Tooltip: managed by pygame-gui (created/destroyed in _draw_coord_tooltip)
        _draw_coord_tooltip(screen, map_rect, mouse_pos, small_font, ui_manager)
        # Bottom bar: draw background + dots; UILabels updated inside (via team_labels)
        _draw_bottom_bar(screen, bottom_bar_rect(), small_font, team_labels)
        # Sidebar: UIPanel provides background; text content drawn on top
        _draw_right_sidebar(screen, sidebar, small_font, btn_font, use_gui_button=True, sidebar_panel=sidebar_panel)
        # Update and draw pygame-gui widgets on top of everything else
        ui_manager.update(time_delta)
        ui_manager.draw_ui(screen)
        pygame.display.flip()
        if _last_combat is not None:
            att_team, combat_state, def_tid, att_tid = _last_combat
            _show_combat_popup(screen, att_team, combat_state, def_tid, clock, att_tid)
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
