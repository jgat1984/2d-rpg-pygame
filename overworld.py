"""
Overworld scene with tile-based movement and tree obstacles.
"""

import pygame
import random
from config import MAP_W, MAP_H, TILE_SIZE, MIN_TILE_SIZE, MAX_TILE_SIZE, ZOOM_STEP, BLUE, RED, GRAY, BLACK, YELLOW, WHITE, DARK, SCREEN_HEIGHT
from entities import Unit, Tree
from rendering import draw_text, draw_tree
from assets import get_hero_sheet, get_goblin_sheet, get_dragon_image


class Overworld:
    def __init__(self, game):
        self.game = game
        # Pass sprite sheets to units
        self.player = Unit("Hero", 5, 5, 20, 5, 4, BLUE, get_hero_sheet())
        
        # Add multiple enemy types using YOUR sprite_mapper selections
        self.enemies = [
            Unit("Goblin", 10, 8, 10, 3, 0, RED, get_goblin_sheet()),
            Unit("Dragon", 15, 10, 18, 7, 0, (200, 100, 50), None),  # One dragon
        ]
        
        self.map = [[0 for _ in range(MAP_W)] for _ in range(MAP_H)]
        for i in range(3, 8):
            self.map[7][i] = 1
        
        # Add trees
        self.trees = []
        self._generate_trees(density=0.15)  # 15% of tiles will have trees
        
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = TILE_SIZE  # Current zoom level

    def _generate_trees(self, density=0.15):
        """Generate trees randomly across the map, avoiding walls and spawn points."""
        for y in range(MAP_H):
            for x in range(MAP_W):
                # Skip if it's a wall
                if self.map[y][x] == 1:
                    continue
                
                # Skip player and enemy spawn areas
                if (x, y) == (self.player.x, self.player.y):
                    continue
                if any((x, y) == (e.x, e.y) for e in self.enemies):
                    continue
                
                # Skip adjacent to player/enemies
                if abs(x - self.player.x) <= 1 and abs(y - self.player.y) <= 1:
                    continue
                if any(abs(x - e.x) <= 1 and abs(y - e.y) <= 1 for e in self.enemies):
                    continue
                
                # Random chance to place tree
                if random.random() < density:
                    self.trees.append(Tree(x, y))
        
        print(f"DEBUG: Generated {len(self.trees)} trees on the map")

    def _is_tree_at(self, x, y):
        """Check if there's a tree at the given position."""
        return any(tree.x == x and tree.y == y for tree in self.trees)

    def update(self, dt):
        # Update player animation
        self.player.update_animation(dt)
        # Update enemy animations
        for e in self.enemies:
            e.update_animation(dt)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            # Zoom controls
            if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                self.tile_size = min(MAX_TILE_SIZE, self.tile_size + ZOOM_STEP)
                print(f"Zoom in: tile_size = {self.tile_size}")
            elif event.key == pygame.K_MINUS:
                self.tile_size = max(MIN_TILE_SIZE, self.tile_size - ZOOM_STEP)
                print(f"Zoom out: tile_size = {self.tile_size}")
            
            # Movement with direction updates
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
                # Trigger animation on each press
                self.player.is_moving = True
                self.player.anim_frame = 0  # Start animation from frame 0
                
                dx, dy = 0, 0
                if event.key == pygame.K_LEFT:
                    dx = -1
                    self.player.facing = "left"
                elif event.key == pygame.K_RIGHT:
                    dx = 1
                    self.player.facing = "right"
                elif event.key == pygame.K_UP:
                    dy = -1
                    self.player.facing = "up"
                elif event.key == pygame.K_DOWN:
                    dy = 1
                    self.player.facing = "down"
                
                nx, ny = self.player.x + dx, self.player.y + dy
                
                # Check bounds, collision, and trees before moving
                if 0 <= nx < MAP_W and 0 <= ny < MAP_H and self.map[ny][nx] == 0 and not self._is_tree_at(nx, ny):
                    coll = next((e for e in self.enemies if e.x == nx and e.y == ny and e.is_alive()), None)
                    if coll:
                        self.game.start_battle(self.player, coll)
                        return
                    
                    self.player.x, self.player.y = nx, ny
                
            elif event.key == pygame.K_SPACE:
                for e in self.enemies:
                    if e.is_alive() and self.player.distance_to(e) == 1:
                        self.game.start_battle(self.player, e)
                        return

    def render(self, surface):
        surface.fill(DARK)
        # draw tiles with current zoom level
        for y in range(MAP_H):
            for x in range(MAP_W):
                rx = x * self.tile_size
                ry = y * self.tile_size
                rect = pygame.Rect(rx, ry, self.tile_size, self.tile_size)
                color = GRAY if self.map[y][x] == 1 else (60, 140, 60)
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)

        # draw trees
        for tree in self.trees:
            draw_tree(surface, tree.x, tree.y, self.tile_size)

        # draw enemies with current zoom
        for e in self.enemies:
            if not e.is_alive():
                continue
            # For dragons (units without sprite sheets), use the dragon image directly
            if "Dragon" in e.name:
                self._draw_dragon_sprite(surface, e, e.x, e.y, e.color)
            else:
                self._draw_sprite(surface, e, e.x, e.y, e.color)
            draw_text(surface, f"{e.hp}", e.x * self.tile_size + 6, e.y * self.tile_size + 4, WHITE)

        # player with current zoom and directional sprite
        self._draw_sprite(surface, self.player, self.player.x, self.player.y, self.player.color)
        draw_text(surface, f"{self.player.hp}", self.player.x * self.tile_size + 6, self.player.y * self.tile_size + 4, WHITE)

        # HUD
        draw_text(surface, "Overworld - Arrow keys: move | Space: battle | +/-: zoom", 8, SCREEN_HEIGHT - 26, YELLOW)
        draw_text(surface, f"Zoom: {self.tile_size}px | Facing: {self.player.facing} | Trees: {len(self.trees)}", 8, SCREEN_HEIGHT - 46, WHITE)

    def _draw_dragon_sprite(self, surface, unit, x, y, tint_color):
        """Draw dragon sprite (use first frame for static display)."""
        # Use first frame of dragon animation for overworld
        img = get_dragon_image(0)

        if img:
            # Scale the sprite to fit the tile
            sprite = pygame.transform.smoothscale(img, (self.tile_size, self.tile_size))
            
            # Calculate position to center the sprite in the tile
            sprite_x = x * self.tile_size
            sprite_y = y * self.tile_size
            
            surface.blit(sprite, (sprite_x, sprite_y))
        else:
            # Fallback to colored rect
            rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
            pygame.draw.rect(surface, tint_color, rect)

    def _draw_sprite(self, surface, unit_or_img, x, y, tint_color):
        """Draw sprite with current zoom level and correct facing direction."""
        # Check if we received a Unit object or just an image
        if hasattr(unit_or_img, 'get_current_sprite'):
            # It's a Unit object
            unit = unit_or_img
            img = unit.get_current_sprite()
            
            if img:
                # Check if we need to flip for left direction
                if unit.facing == "left":
                    img = pygame.transform.flip(img, True, False)
                
                sprite = pygame.transform.smoothscale(img, (self.tile_size, self.tile_size))
                surface.blit(sprite, (x * self.tile_size, y * self.tile_size))
            else:
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                pygame.draw.rect(surface, tint_color, rect)
        else:
            # It's just an image (backward compatibility)
            img = unit_or_img
            if img:
                sprite = pygame.transform.smoothscale(img, (self.tile_size, self.tile_size))
                surface.blit(sprite, (x * self.tile_size, y * self.tile_size))
            else:
                rect = pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size)
                pygame.draw.rect(surface, tint_color, rect)