"""
Configuration constants for the 2D RPG game.
"""

# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Tile settings
TILE_SIZE = 32  # Default, but will be adjustable
MAP_W = 20
MAP_H = 15

# Battle settings
BATTLE_GRID_W = 8
BATTLE_GRID_H = 6
BATTLE_TILE = 64

# Zoom settings
MIN_TILE_SIZE = 16
MAX_TILE_SIZE = 64
ZOOM_STEP = 8

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (120, 120, 120)
GREEN = (50, 200, 50)
RED = (200, 50, 50)
BLUE = (50, 100, 200)
YELLOW = (220, 220, 50)
DARK = (30, 30, 30)