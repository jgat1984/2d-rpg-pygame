"""
Rendering utilities for drawing sprites and UI elements.
"""

import pygame
from config import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, BATTLE_GRID_W, BATTLE_GRID_H, BATTLE_TILE, WHITE
from assets import get_font, get_tree_image


def draw_text(surface, text, x, y, color=WHITE):
    """Draw text on the surface."""
    font = get_font()
    surf = font.render(text, True, color)
    surface.blit(surf, (x, y))


def draw_tree(surface, x, y, tile_size):
    """Draw a tree using the tree.png sprite, or fallback to shapes."""
    tree_img = get_tree_image()
    if tree_img:
        # Scale and draw the tree image
        tree_sprite = pygame.transform.smoothscale(tree_img, (tile_size, tile_size))
        surface.blit(tree_sprite, (x * tile_size, y * tile_size))
    else:
        # Fallback to drawing tree with shapes if image not found
        # Tree trunk
        trunk_w = tile_size // 4
        trunk_h = tile_size // 2
        trunk_x = x * tile_size + (tile_size - trunk_w) // 2
        trunk_y = y * tile_size + tile_size // 2
        pygame.draw.rect(surface, (101, 67, 33), (trunk_x, trunk_y, trunk_w, trunk_h))
        
        # Tree foliage (green circle)
        foliage_radius = tile_size // 3
        foliage_x = x * tile_size + tile_size // 2
        foliage_y = y * tile_size + tile_size // 3
        pygame.draw.circle(surface, (34, 139, 34), (foliage_x, foliage_y), foliage_radius)
        # Highlight
        pygame.draw.circle(surface, (50, 205, 50), (foliage_x - foliage_radius // 3, foliage_y - foliage_radius // 3), foliage_radius // 3)


def draw_overworld_sprite(surface, img, x, y, tint_color):
    """Draw a sprite in the overworld."""
    if img:
        sprite = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
        surface.blit(sprite, (x * TILE_SIZE, y * TILE_SIZE))
    else:
        rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surface, tint_color, rect)


def draw_battle_sprite(surface, img, grid_x, grid_y, tint_color, offset_x=0, offset_y=0):
    """Draw a sprite in the battle scene with optional centering offset."""
    start_x = (SCREEN_WIDTH - (BATTLE_GRID_W * BATTLE_TILE)) // 2
    start_y = (SCREEN_HEIGHT - (BATTLE_GRID_H * BATTLE_TILE)) // 2
    if img:
        # Scale sprite to 80% of tile size to leave room for centering
        sprite_size = int(BATTLE_TILE * 0.8)
        sprite = pygame.transform.smoothscale(img, (sprite_size, sprite_size))
        
        # Center the sprite in the tile
        sprite_x = start_x + grid_x * BATTLE_TILE
        sprite_y = start_y + grid_y * BATTLE_TILE
        
        # Calculate centering offset
        center_offset_x = (BATTLE_TILE - sprite.get_width()) // 2
        center_offset_y = (BATTLE_TILE - sprite.get_height()) // 2
        
        surface.blit(sprite, (sprite_x + center_offset_x + offset_x, sprite_y + center_offset_y + offset_y))
    else:
        rect = pygame.Rect(start_x + grid_x * BATTLE_TILE + 4, start_y + grid_y * BATTLE_TILE + 4, BATTLE_TILE - 8, BATTLE_TILE - 8)
        pygame.draw.rect(surface, tint_color, rect)