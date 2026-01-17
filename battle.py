"""
Tactical battle scene with grid-based combat.
SHINING FORCE STYLE: Full party system with multiple units!
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
    STATE_PLAYER_ACTION_MENU = 2  # NEW: Attack/Magic/Item menu
    STATE_PLAYER_ATTACK = 3
    STATE_ENEMY_TURN = 4
    STATE_VICTORY = 5
    STATE_DEFEAT = 6

    def __init__(self, game, player_unit, enemy_unit):
        self.game = game
        
        # Determine which sprite sheet and image to use based on enemy name
        if "Dragon" in enemy_unit.name:
            enemy_sheet = get_dragon_sheet()
            self.enemy_battle_image = get_dragon_image()
        else:
            enemy_sheet = get_goblin_sheet()
            self.enemy_battle_image = get_goblin_image()
        
        # CREATE PARTY: Multiple player units (Shining Force style!)
        hero_sheet = get_hero_sheet()
        self.player_units = [
            # Main hero in front
            Unit(player_unit.name, 1, BATTLE_GRID_H // 2, player_unit.hp, player_unit.atk, 4, BLUE, hero_sheet),
            # Party members behind/adjacent
            Unit("Knight", 1, BATTLE_GRID_H // 2 - 1, 25, 6, 3, (100, 150, 255), hero_sheet),
            Unit("Archer", 0, BATTLE_GRID_H // 2, 15, 5, 4, (150, 255, 150), hero_sheet),
            Unit("Mage", 0, BATTLE_GRID_H // 2 + 1, 12, 7, 3, (255, 150, 255), hero_sheet),
        ]
        
        # Set attack ranges for each unit type
        self.player_units[0].attack_range = 1  # Hero - melee
        self.player_units[1].attack_range = 1  # Knight - melee
        self.player_units[2].attack_range = 3  # Archer - ranged (2-3 tiles)
        self.player_units[2].min_range = 2     # Archer can't attack adjacent
        self.player_units[3].attack_range = 2  # Mage - magic (1-2 tiles)
        self.player_units[3].min_range = 1     # Mage can attack adjacent and 1 tile away
        
        # CREATE ENEMY PARTY: Multiple enemies
        self.enemy_units = [
            Unit(enemy_unit.name, BATTLE_GRID_W - 2, BATTLE_GRID_H // 2, 
                 enemy_unit.hp, enemy_unit.atk, 3, enemy_unit.color, enemy_sheet),
            # Add minion enemies
            Unit("Goblin", BATTLE_GRID_W - 2, BATTLE_GRID_H // 2 - 1, 
                 8, 3, 3, RED, get_goblin_sheet()),
            Unit("Goblin", BATTLE_GRID_W - 3, BATTLE_GRID_H // 2 + 1, 
                 8, 3, 3, RED, get_goblin_sheet()),
        ]
        
        # Set enemy attack ranges (all melee by default)
        for e in self.enemy_units:
            e.attack_range = 1
            e.min_range = 1
        
        # Copy facing direction from overworld
        self.player_units[0].facing = player_unit.facing
        
        self.state = Battle.STATE_PLAYER_SELECT
        self.selected_unit = None  # No unit selected initially
        self.cursor_x = BATTLE_GRID_W // 2
        self.cursor_y = BATTLE_GRID_H // 2
        self.valid_moves = set()
        self.valid_attacks = set()  # NEW: valid attack targets
        self.turn_queue = deque(["player", "enemy"])
        self.message = "Select a unit to move"
        
        # Store original position for move cancellation
        self.original_pos = None

    def _in_bounds(self, x, y):
        return 0 <= x < BATTLE_GRID_W and 0 <= y < BATTLE_GRID_H

    def _compute_valid_moves(self):
        """Calculate valid movement tiles for selected unit."""
        if not self.selected_unit:
            self.valid_moves = set()
            return
            
        self.valid_moves = set()
        start = (self.selected_unit.x, self.selected_unit.y)
        maxdist = self.selected_unit.movement
        visited = {start: 0}
        q = deque([start])
        
        while q:
            cx, cy = q.popleft()
            dist = visited[(cx, cy)]
            
            # Check if we can END movement here
            can_stop_here = True
            for u in self.player_units + self.enemy_units:
                if u == self.selected_unit:
                    continue
                if u.x == cx and u.y == cy and u.is_alive():
                    can_stop_here = False
                    break
            
            if can_stop_here:
                self.valid_moves.add((cx, cy))
            
            if dist >= maxdist:
                continue
            
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if not self._in_bounds(nx, ny):
                    continue
                if (nx, ny) in visited:
                    continue
                
                # Allow movement THROUGH friendly units, but not enemies
                blocked = False
                for e in self.enemy_units:
                    if e.x == nx and e.y == ny and e.is_alive():
                        blocked = True
                        break
                
                if blocked:
                    continue
                
                visited[(nx, ny)] = dist + 1
                q.append((nx, ny))

    def _compute_valid_attacks(self):
        """Calculate valid attack targets for selected unit."""
        if not self.selected_unit:
            self.valid_attacks = set()
            return
        
        self.valid_attacks = set()
        attack_range = getattr(self.selected_unit, 'attack_range', 1)
        min_range = getattr(self.selected_unit, 'min_range', 1)
        
        # Find all enemies within attack range
        for e in self.enemy_units:
            if not e.is_alive():
                continue
            dist = self.selected_unit.distance_to(e)
            if min_range <= dist <= attack_range:
                self.valid_attacks.add((e.x, e.y))

    def _get_player_unit_at(self, x, y):
        """Get player unit at position that hasn't acted yet."""
        return next((p for p in self.player_units if p.x == x and p.y == y and p.is_alive() and not p.has_acted), None)

    def _enemy_at(self, x, y):
        """Get enemy unit at position."""
        return next((e for e in self.enemy_units if e.x == x and e.y == y and e.is_alive()), None)

    def handle_event(self, event):
        if self.state in (Battle.STATE_VICTORY, Battle.STATE_DEFEAT):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                self.game.end_battle(self.state == Battle.STATE_VICTORY, self.player_units[0])
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Cancel current action
                if self.state == Battle.STATE_PLAYER_MOVE and self.selected_unit and self.original_pos:
                    # Return unit to original position
                    self.selected_unit.x, self.selected_unit.y = self.original_pos
                    self.state = Battle.STATE_PLAYER_SELECT
                    self.selected_unit = None
                    self.message = "Action cancelled - Select a unit"
                elif self.state == Battle.STATE_PLAYER_ATTACK and self.selected_unit and self.original_pos:
                    # Return unit to original position
                    self.selected_unit.x, self.selected_unit.y = self.original_pos
                    self.state = Battle.STATE_PLAYER_SELECT
                    self.selected_unit = None
                    self.message = "Action cancelled - Select a unit"
                else:
                    # Forfeit battle
                    self.state = Battle.STATE_DEFEAT
                return

            if self.state in (Battle.STATE_PLAYER_SELECT, Battle.STATE_PLAYER_MOVE, Battle.STATE_PLAYER_ATTACK):
                # Cursor movement
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
                        # Select a unit to move
                        unit = self._get_player_unit_at(self.cursor_x, self.cursor_y)
                        if unit:
                            self.selected_unit = unit
                            self.original_pos = (unit.x, unit.y)
                            self.state = Battle.STATE_PLAYER_MOVE
                            self._compute_valid_moves()
                            self.message = f"{unit.name} selected - Choose destination"
                        else:
                            self.message = "No unit here or already acted"
                    
                    elif self.state == Battle.STATE_PLAYER_MOVE:
                        # Move unit to selected tile
                        if (self.cursor_x, self.cursor_y) in self.valid_moves:
                            self.selected_unit.x, self.selected_unit.y = self.cursor_x, self.cursor_y
                            self.state = Battle.STATE_PLAYER_ATTACK
                            self._compute_valid_attacks()
                            
                            # Show attack range info
                            attack_range = getattr(self.selected_unit, 'attack_range', 1)
                            min_range = getattr(self.selected_unit, 'min_range', 1)
                            if attack_range > 1:
                                self.message = f"{self.selected_unit.name} - Select target (range {min_range}-{attack_range}) or Space to skip"
                            else:
                                self.message = f"{self.selected_unit.name} - Select target or Space to skip"
                        else:
                            self.message = "Cannot move there"
                    
                    elif self.state == Battle.STATE_PLAYER_ATTACK:
                        # Attack enemy
                        enemy = self._enemy_at(self.cursor_x, self.cursor_y)
                        if enemy and (self.cursor_x, self.cursor_y) in self.valid_attacks:
                            self._attack(self.selected_unit, enemy)
                            self.selected_unit.has_acted = True
                            self._after_player_action()
                        else:
                            if enemy:
                                self.message = "Target out of range - Press Space to skip"
                            else:
                                self.message = "No target - Press Space to skip"
                
                # Space bar to skip attack phase
                elif event.key == pygame.K_SPACE and self.state == Battle.STATE_PLAYER_ATTACK:
                    # End turn without attacking
                    self.selected_unit.has_acted = True
                    self.message = f"{self.selected_unit.name} ended turn"
                    self._after_player_action()

            # Add code here to handle action menu selection (Attack/Magic/Item)

    def _attack(self, attacker, defender):
        """Execute attack."""
        defender.hp -= attacker.atk
        attack_range = getattr(attacker, 'attack_range', 1)
        weapon = "bow" if "Archer" in attacker.name else "magic" if "Mage" in attacker.name else "sword"
        
        if attack_range > 1:
            self.message = f"{attacker.name} attacks with {weapon} for {attacker.atk}!"
        else:
            self.message = f"{attacker.name} hits {defender.name} for {attacker.atk}!"
        
        if defender.hp <= 0:
            defender.hp = 0
            self.message += f" {defender.name} defeated!"

    def _after_player_action(self):
        """Check victory/defeat and transition turns."""
        if not any(e.is_alive() for e in self.enemy_units):
            self.state = Battle.STATE_VICTORY
            self.message = "Victory!"
            return
        
        # Check if all player units have acted
        if all(p.has_acted or not p.is_alive() for p in self.player_units):
            self.state = Battle.STATE_ENEMY_TURN
            self.message = "Enemy turn..."
            self.selected_unit = None  # Clear selection
            self.valid_attacks = set()
            pygame.time.set_timer(pygame.USEREVENT + 1, 800)  # Increased delay for visibility
        else:
            # More units to move
            self.state = Battle.STATE_PLAYER_SELECT
            self.selected_unit = None
            self.valid_attacks = set()
            self.message = "Select next unit"

    def update(self, dt):
        pass

    def enemy_turn(self):
        """AI turn for all enemies."""
        for e in self.enemy_units:
            if not e.is_alive():
                continue
            
            living_players = [p for p in self.player_units if p.is_alive()]
            if not living_players:
                self.state = Battle.STATE_DEFEAT
                self.message = "Defeat..."
                return
            
            target = min(living_players, key=lambda p: e.distance_to(p))
            
            # Attack if adjacent
            if e.distance_to(target) == 1:
                target.hp -= e.atk
                self.message = f"{e.name} hits {target.name} for {e.atk}!"
                if target.hp <= 0:
                    target.hp = 0
                    self.message += f" {target.name} defeated!"
            else:
                # Move towards target
                dx = 1 if target.x > e.x else -1 if target.x < e.x else 0
                dy = 1 if target.y > e.y else -1 if target.y < e.y else 0
                moved = False
                
                # Try diagonal and cardinal moves
                for nx, ny in [(e.x + dx, e.y + dy), (e.x + dx, e.y), (e.x, e.y + dy)]:
                    if 0 <= nx < BATTLE_GRID_W and 0 <= ny < BATTLE_GRID_H:
                        if not any(u.x == nx and u.y == ny and u.is_alive() for u in self.player_units + self.enemy_units):
                            e.x, e.y = nx, ny
                            moved = True
                            self.message = f"{e.name} moved"
                            break
                
                # If still can't move, try any adjacent tile
                if not moved:
                    for dx2, dy2 in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx, ny = e.x + dx2, e.y + dy2
                        if 0 <= nx < BATTLE_GRID_W and 0 <= ny < BATTLE_GRID_H:
                            if not any(u.x == nx and u.y == ny and u.is_alive() for u in self.player_units + self.enemy_units):
                                e.x, e.y = nx, ny
                                self.message = f"{e.name} moved"
                                break
        
        if not any(p.is_alive() for p in self.player_units):
            self.state = Battle.STATE_DEFEAT
            self.message = "Defeat..."
            return
        
        # Reset player units for next turn
        for p in self.player_units:
            p.has_acted = False
        
        self.state = Battle.STATE_PLAYER_SELECT
        # Position cursor on first available unit
        for p in self.player_units:
            if p.is_alive() and not p.has_acted:
                self.cursor_x, self.cursor_y = p.x, p.y
                break
        self.message = "Your turn - Select a unit"

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

        # highlight valid attack targets when in attack state
        if self.state == Battle.STATE_PLAYER_ATTACK:
            for (ax, ay) in self.valid_attacks:
                rx = start_x + ax * BATTLE_TILE
                ry = start_y + ay * BATTLE_TILE
                s = pygame.Surface((BATTLE_TILE - 4, BATTLE_TILE - 4), pygame.SRCALPHA)
                s.fill((200, 80, 80, 100))  # Red highlight for attackable enemies
                surface.blit(s, (rx + 2, ry + 2))

        # draw units with status indicators
        for p in self.player_units:
            if not p.is_alive():
                continue
            draw_battle_sprite(surface, get_hero_image(), p.x, p.y, p.color)
            
            # Visual indicator: dimmed if already acted
            if p.has_acted:
                rx = start_x + p.x * BATTLE_TILE
                ry = start_y + p.y * BATTLE_TILE
                s = pygame.Surface((BATTLE_TILE - 4, BATTLE_TILE - 4), pygame.SRCALPHA)
                s.fill((0, 0, 0, 120))
                surface.blit(s, (rx + 2, ry + 2))
            
            # Selected unit highlight
            if p == self.selected_unit:
                rx = start_x + p.x * BATTLE_TILE
                ry = start_y + p.y * BATTLE_TILE
                pygame.draw.rect(surface, (255, 255, 0), (rx, ry, BATTLE_TILE, BATTLE_TILE), 4)

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

        # ===== HUD PANEL - Boxed bottom display =====
        hud_height = 120
        hud_y = SCREEN_HEIGHT - hud_height
        
        # Draw HUD background box
        hud_bg = pygame.Surface((SCREEN_WIDTH, hud_height))
        hud_bg.fill((20, 20, 50))
        surface.blit(hud_bg, (0, hud_y))
        
        # Draw border
        pygame.draw.rect(surface, YELLOW, (0, hud_y, SCREEN_WIDTH, hud_height), 2)
        
        # Draw divider lines
        pygame.draw.line(surface, (100, 100, 150), (0, hud_y + 25), (SCREEN_WIDTH, hud_y + 25), 1)
        pygame.draw.line(surface, (100, 100, 150), (0, hud_y + 50), (SCREEN_WIDTH, hud_y + 50), 1)
        pygame.draw.line(surface, (100, 100, 150), (0, hud_y + 75), (SCREEN_WIDTH, hud_y + 75), 1)
        
        # Line 1: Enemy HP
        enemy_hp_text = "ENEMIES: "
        for e in self.enemy_units:
            if e.is_alive():
                enemy_hp_text += f"{e.name}: {e.hp}/{e.max_hp}  "
        draw_text(surface, enemy_hp_text.strip(), 10, hud_y + 5, RED)
        
        # Line 2: Player HP (shortened format)
        hp_text = "PARTY: "
        for p in self.player_units:
            if p.is_alive():
                # Shortened format: use ✓ for DONE, ● for READY
                status = "✓" if p.has_acted else "●"
                hp_text += f"{p.name}:{p.hp}/{p.max_hp}{status} "
        draw_text(surface, hp_text.strip(), 10, hud_y + 30, WHITE)
        
        # Line 3: Controls
        draw_text(surface, "Arrows: cursor | Enter: select/attack | Space: skip attack | ESC: cancel/forfeit", 10, hud_y + 55, (180, 180, 200))
        
        # Line 4: Main message
        draw_text(surface, f"Battle - {self.message}", 10, hud_y + 80, YELLOW)