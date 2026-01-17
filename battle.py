"""
Tactical battle scene with grid-based combat.
"""

import pygame
from collections import deque
from config import BATTLE_GRID_W, BATTLE_GRID_H, BATTLE_TILE, SCREEN_WIDTH, SCREEN_HEIGHT, BLUE, RED, BLACK, YELLOW, WHITE
from entities import Unit
from rendering import draw_text, draw_battle_sprite
from assets import get_hero_sheet, get_goblin_sheet, get_dragon_sheet, get_hero_image, get_goblin_image, get_dragon_image


class Battle:
    STATE_PLAYER_SELECT = 0
    STATE_PLAYER_MOVE = 1
    STATE_PLAYER_ATTACK = 2
    STATE_ENEMY_TURN = 3
    STATE_VICTORY = 4
    STATE_DEFEAT = 5

    def __init__(self, game, player_unit, enemy_unit):
        self.game = game
        
        # Determine which sprite sheet and image to use based on enemy name
        if "Dragon" in enemy_unit.name:
            enemy_sheet = get_dragon_sheet()
            self.enemy_battle_image = get_dragon_image()
        else:
            enemy_sheet = get_goblin_sheet()
            self.enemy_battle_image = get_goblin_image()
        
        # create local tactical units with sprite sheets
        self.player_units = [Unit(player_unit.name, 1, BATTLE_GRID_H // 2, player_unit.hp, 
                                  player_unit.atk, 4, BLUE, get_hero_sheet())]
        self.enemy_units = [Unit(enemy_unit.name, BATTLE_GRID_W - 2, BATTLE_GRID_H // 2, 
                                 enemy_unit.hp, enemy_unit.atk, 3, enemy_unit.color, enemy_sheet)]
        # Copy facing direction from overworld
        self.player_units[0].facing = player_unit.facing
        
        self.state = Battle.STATE_PLAYER_SELECT
        self.selected_unit = self.player_units[0]
        self.cursor_x = self.selected_unit.x
        self.cursor_y = self.selected_unit.y
        self.valid_moves = set()
        self.turn_queue = deque(["player", "enemy"])
        self.message = ""
        self._compute_valid_moves()

    def _in_bounds(self, x, y):
        return 0 <= x < BATTLE_GRID_W and 0 <= y < BATTLE_GRID_H

    def _compute_valid_moves(self):
        self.valid_moves = set()
        start = (self.selected_unit.x, self.selected_unit.y)
        maxdist = self.selected_unit.movement
        visited = {start: 0}
        q = deque([start])
        while q:
            cx, cy = q.popleft()
            dist = visited[(cx, cy)]
            self.valid_moves.add((cx, cy))
            if dist >= maxdist:
                continue
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                if any(u.x == nx and u.y == ny and u.is_alive() for u in self.player_units + self.enemy_units):
                    continue
                visited[(nx, ny)] = dist + 1
                q.append((nx, ny))

    def handle_event(self, event):
        if self.state in (Battle.STATE_VICTORY, Battle.STATE_DEFEAT):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.game.end_battle(self.state == Battle.STATE_VICTORY, self.player_units[0])
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = Battle.STATE_DEFEAT
                return

            if self.state in (Battle.STATE_PLAYER_SELECT, Battle.STATE_PLAYER_MOVE, Battle.STATE_PLAYER_ATTACK):
                if event.key == pygame.K_LEFT:
                    self.cursor_x = max(0, self.cursor_x - 1)
                elif event.key == pygame.K_RIGHT:
                    self.cursor_x = min(BATTLE_GRID_W - 1, self.cursor_x + 1)
                elif event.key == pygame.K_UP:
                    self.cursor_y = max(0, self.cursor_y - 1)
                elif event.key == pygame.K_DOWN:
                    self.cursor_y = min(BATTLE_GRID_H - 1, self.cursor_y + 1)
                elif event.key == pygame.K_RETURN:
                    if self.state == Battle.STATE_PLAYER_SELECT:
                        if (self.cursor_x, self.cursor_y) == (self.selected_unit.x, self.selected_unit.y):
                            self.state = Battle.STATE_PLAYER_MOVE
                            self._compute_valid_moves()
                        else:
                            enemy = self._enemy_at(self.cursor_x, self.cursor_y)
                            if enemy and self.selected_unit.distance_to(enemy) == 1:
                                self._attack(self.selected_unit, enemy)
                                self._after_player_action()
                    elif self.state == Battle.STATE_PLAYER_MOVE:
                        if (self.cursor_x, self.cursor_y) in self.valid_moves:
                            self.selected_unit.x, self.selected_unit.y = self.cursor_x, self.cursor_y
                            self.state = Battle.STATE_PLAYER_ATTACK
                        else:
                            self.message = "Cannot move there."
                    elif self.state == Battle.STATE_PLAYER_ATTACK:
                        enemy = self._enemy_at(self.cursor_x, self.cursor_y)
                        if enemy and self.selected_unit.distance_to(enemy) == 1:
                            self._attack(self.selected_unit, enemy)
                            self._after_player_action()
                        else:
                            self._after_player_action()

    def _enemy_at(self, x, y):
        return next((e for e in self.enemy_units if e.x == x and e.y == y and e.is_alive()), None)

    def _attack(self, attacker, defender):
        defender.hp -= attacker.atk
        self.message = f"{attacker.name} hits {defender.name} for {attacker.atk}!"
        if defender.hp <= 0:
            defender.hp = 0
            self.message += f" {defender.name} defeated!"

    def _after_player_action(self):
        if not any(e.is_alive() for e in self.enemy_units):
            self.state = Battle.STATE_VICTORY
            self.message = "Victory!"
            return
        self.state = Battle.STATE_ENEMY_TURN
        pygame.time.set_timer(pygame.USEREVENT + 1, 400)

    def update(self, dt):
        pass

    def enemy_turn(self):
        for e in self.enemy_units:
            if not e.is_alive():
                continue
            living_players = [p for p in self.player_units if p.is_alive()]
            if not living_players:
                self.state = Battle.STATE_DEFEAT
                self.message = "Defeat..."
                return
            target = min(living_players, key=lambda p: e.distance_to(p))
            if e.distance_to(target) == 1:
                target.hp -= e.atk
                self.message = f"{e.name} hits {target.name} for {e.atk}!"
                if target.hp <= 0:
                    target.hp = 0
                    self.message += f" {target.name} defeated!"
            else:
                dx = 1 if target.x > e.x else -1 if target.x < e.x else 0
                dy = 1 if target.y > e.y else -1 if target.y < e.y else 0
                moved = False
                for nx, ny in [(e.x + dx, e.y), (e.x, e.y + dy), (e.x + dx, e.y + dy)]:
                    if 0 <= nx < BATTLE_GRID_W and 0 <= ny < BATTLE_GRID_H:
                        if not any(u.x == nx and u.y == ny and u.is_alive() for u in self.player_units + self.enemy_units):
                            e.x, e.y = nx, ny
                            moved = True
                            break
                if not moved:
                    for dx2, dy2 in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx, ny = e.x + dx2, e.y + dy2
                        if 0 <= nx < BATTLE_GRID_W and 0 <= ny < BATTLE_GRID_H and not any(u.x == nx and u.y == ny and u.is_alive() for u in self.player_units + self.enemy_units):
                            e.x, e.y = nx, ny
                            break
        if not any(p.is_alive() for p in self.player_units):
            self.state = Battle.STATE_DEFEAT
            self.message = "Defeat..."
            return
        self.state = Battle.STATE_PLAYER_SELECT
        self.cursor_x, self.cursor_y = self.selected_unit.x, self.selected_unit.y
        self._compute_valid_moves()

    def render(self, surface):
        surface.fill((10, 10, 40))
        # center the battle grid
        start_x = (SCREEN_WIDTH - (BATTLE_GRID_W * BATTLE_TILE)) // 2
        start_y = (SCREEN_HEIGHT - (BATTLE_GRID_H * BATTLE_TILE)) // 2

        # draw grid
        for y in range(BATTLE_GRID_H):
            for x in range(BATTLE_GRID_W):
                rx = start_x + x * BATTLE_TILE
                ry = start_y + y * BATTLE_TILE
                rect = pygame.Rect(rx, ry, BATTLE_TILE, BATTLE_TILE)
                pygame.draw.rect(surface, (40, 60, 40), rect)
                pygame.draw.rect(surface, BLACK, rect, 2)

        # highlight valid moves when in move state
        if self.state == Battle.STATE_PLAYER_MOVE:
            for (mx, my) in self.valid_moves:
                rx = start_x + mx * BATTLE_TILE
                ry = start_y + my * BATTLE_TILE
                s = pygame.Surface((BATTLE_TILE - 4, BATTLE_TILE - 4), pygame.SRCALPHA)
                s.fill((80, 200, 80, 100))
                surface.blit(s, (rx + 2, ry + 2))

        # draw units (no HP text here)
        for p in self.player_units:
            if not p.is_alive():
                continue
            draw_battle_sprite(surface, get_hero_image(), p.x, p.y, p.color)

        for e in self.enemy_units:
            if not e.is_alive():
                continue
            # Dragons are now properly cropped, minimal offset needed
            offset_x = 0 if "Dragon" in e.name else 0
            offset_y = 0 if "Dragon" in e.name else 0
            draw_battle_sprite(surface, self.enemy_battle_image, e.x, e.y, e.color, offset_x, offset_y)

        # cursor
        cx = start_x + self.cursor_x * BATTLE_TILE
        cy = start_y + self.cursor_y * BATTLE_TILE
        pygame.draw.rect(surface, YELLOW, (cx + 2, cy + 2, BATTLE_TILE - 4, BATTLE_TILE - 4), 3)

        # HUD / messages with HP display at bottom
        draw_text(surface, f"Battle - {self.message}", 8, SCREEN_HEIGHT - 26, YELLOW)
        
        # Display HP for all units at the bottom
        hp_text = ""
        for p in self.player_units:
            if p.is_alive():
                hp_text += f"{p.name}: {p.hp}/{p.max_hp} HP  "
        for e in self.enemy_units:
            if e.is_alive():
                hp_text += f"{e.name}: {e.hp}/{e.max_hp} HP"
        draw_text(surface, hp_text, 8, SCREEN_HEIGHT - 66, WHITE)
        
        draw_text(surface, "Use arrow keys to move cursor, Enter to confirm, Esc to concede", 8, SCREEN_HEIGHT - 46, WHITE)