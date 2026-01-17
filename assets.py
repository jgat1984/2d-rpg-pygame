"""
Asset loading and management for sprites, music, and fonts.
"""

import pygame
import os
import math
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Asset paths
HERO_SRC = os.path.join(BASE_DIR, "hero.png")
GOBLIN_SRC = os.path.join(BASE_DIR, "goblin.png")
DRAGON_SRC = os.path.join(BASE_DIR, "dragons.png")
TREE_SRC = os.path.join(BASE_DIR, "tree.png")
OVERWORLD_MUSIC_PATH = os.path.join(BASE_DIR, "overworld.mp3")
BATTLE_MUSIC_PATH = os.path.join(BASE_DIR, "battle.wav")

# Font - will be initialized during load_assets()
FONT = None


def get_font():
    """Get the initialized font."""
    global FONT
    if FONT is None:
        pygame.font.init()
        FONT = pygame.font.SysFont("Consolas", 18)
        print("DEBUG: Font initialized")
    return FONT


def _safe_load_image(path):
    """Load an image safely with error handling."""
    try:
        if os.path.isfile(path):
            img = pygame.image.load(path)
            print(f"DEBUG: loaded image {path} size={img.get_size()}")
            return img
        else:
            print(f"DEBUG: image file not found: {path}")
    except Exception as ex:
        print(f"DEBUG: failed loading image {path}: {ex}")
        traceback.print_exc()
    return None


def detect_frame_size(sheet, manual_size=None):
    """Return a (w,h) guess for single-frame size in a spritesheet.
    Prefers common frame sizes and falls back to gcd(width,height).
    """
    if sheet is None:
        return None, None
    
    if manual_size:
        print(f"DEBUG: detect_frame_size using manual override: {manual_size}x{manual_size}")
        return manual_size, manual_size
    
    sw, sh = sheet.get_size()
    print(f"DEBUG: detect_frame_size input: sheet size = {sw}x{sh}")
    # Common frame sizes to try (largest first)
    for s in (64, 48, 32, 24, 16, 8):
        if sw % s == 0 and sh % s == 0:
            print(f"DEBUG: detect_frame_size -> chosen {s}x{s} (divides {sw}x{sh})")
            return s, s
    # fallback: use gcd of dimensions (useful for irregular sheets)
    g = math.gcd(sw, sh)
    if g > 0 and g >= 8:  # Only use GCD if it's reasonable (at least 8 pixels)
        print(f"DEBUG: detect_frame_size -> gcd fallback {g} (sheet {sw}x{sh})")
        return g, g
    # ultimate fallback: use full size
    print(f"DEBUG: detect_frame_size -> fallback full size {sw}x{sh}")
    return sw, sh


def get_frame(sheet, col, row, frame_w, frame_h):
    """Return a copy of one frame from a spritesheet (safe even before convert_alpha)."""
    if sheet is None or frame_w is None or frame_h is None:
        print(f"DEBUG: get_frame - sheet or frame size is None")
        return None
    rect = pygame.Rect(col * frame_w, row * frame_h, frame_w, frame_h)
    # ensure rect inside sheet
    sw, sh = sheet.get_size()
    if rect.right > sw or rect.bottom > sh:
        print(f"DEBUG: get_frame rect {rect} out of bounds for sheet size {(sw,sh)}")
        return None
    return sheet.subsurface(rect).copy()


def get_sprite_bounds(img):
    """Get the bounding box of non-transparent pixels in an image.
    Returns (left, top, width, height) of the actual sprite content.
    """
    if img is None:
        return None
    
    # Get the bounding box of non-transparent pixels
    # Convert to a format where we can check alpha channel
    width, height = img.get_size()
    min_x, min_y = width, height
    max_x, max_y = 0, 0
    
    # Lock the surface for pixel access
    img_locked = pygame.surfarray.pixels_alpha(img)
    
    # Find bounds of non-transparent pixels
    for y in range(height):
        for x in range(width):
            if img_locked[x, y] > 10:  # Threshold for non-transparent (alpha > 10)
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    
    del img_locked  # Unlock the surface
    
    if max_x >= min_x and max_y >= min_y:
        return (min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)
    return None


def crop_to_content(img):
    """Crop an image to its non-transparent content."""
    if img is None:
        return None
    
    bounds = get_sprite_bounds(img)
    if bounds:
        left, top, width, height = bounds
        rect = pygame.Rect(left, top, width, height)
        return img.subsurface(rect).copy()
    return img


# Load sprite sheets
_HERO_SHEET = None
_GOBLIN_SHEET = None
_DRAGON_SHEET = None
_TREE_IMG = None
HERO_IMG = None
GOBLIN_IMG = None
DRAGON_IMG = None

# Dragon animation frames
DRAGON_ANIMATION_FRAMES = []

# Dragon images dictionary
DRAGON_IMAGES = {}


def load_assets():
    """Load all game assets including font."""
    global _HERO_SHEET, _GOBLIN_SHEET, _DRAGON_SHEET, _TREE_IMG, HERO_IMG, GOBLIN_IMG, DRAGON_IMG, FONT, DRAGON_ANIMATION_FRAMES, DRAGON_IMAGES
    
    # Initialize font first
    FONT = get_font()
    
    # Load sheets
    _HERO_SHEET = _safe_load_image(HERO_SRC)
    _GOBLIN_SHEET = _safe_load_image(GOBLIN_SRC)
    _DRAGON_SHEET = _safe_load_image(DRAGON_SRC)
    _TREE_IMG = _safe_load_image(TREE_SRC)
    
    # Detect frame sizes per sheet
    hero_frame_w, hero_frame_h = detect_frame_size(_HERO_SHEET)
    goblin_frame_w, goblin_frame_h = detect_frame_size(_GOBLIN_SHEET)
    
    # Extract top-left frames (col=0,row=0)
    HERO_IMG = get_frame(_HERO_SHEET, col=0, row=0, frame_w=hero_frame_w, frame_h=hero_frame_h)
    GOBLIN_IMG = get_frame(_GOBLIN_SHEET, col=0, row=0, frame_w=goblin_frame_w, frame_h=goblin_frame_h)
    
    # Dragons: Use exact pixel coordinates from sprite_mapper.py
    # Sheet is 428x377, Grid is 3x3 with 120x120 frames
    if _DRAGON_SHEET:
        sheet_w, sheet_h = _DRAGON_SHEET.get_size()
        print(f"DEBUG: Dragon sheet actual size: {sheet_w}x{sheet_h}")
        
        # Define precise extraction rectangles for each dragon
        # Row 0 (top row)
        dragon_rects = {
            "green": pygame.Rect(0, 0, 120, 120),      # Grid (0,0)
            "orange": pygame.Rect(120, 0, 120, 120),   # Grid (1,0)
            "red": pygame.Rect(240, 0, 120, 120),      # Grid (2,0)
            # Row 1 (middle row)
            "frame_1_0": pygame.Rect(0, 120, 120, 120),    # Grid (0,1)
            "frame_1_1": pygame.Rect(120, 120, 120, 120),  # Grid (1,1)
            "frame_1_2": pygame.Rect(240, 120, 120, 120),  # Grid (2,1)
        }
        
        # Extract each dragon and print bounds
        extracted = {}
        for name, rect in dragon_rects.items():
            print(f"DEBUG: Extracting {name} from rect {rect}")
            raw = _DRAGON_SHEET.subsurface(rect).copy()
            cropped = crop_to_content(raw)
            extracted[name] = cropped
            if cropped:
                print(f"DEBUG: {name} - raw: {raw.get_size()}, cropped: {cropped.get_size()}")
        
        # Set the main dragon image (green)
        DRAGON_IMG = extracted["green"]
        
        # Load dragon color variants
        DRAGON_IMAGES = {
            "green": extracted["green"],
            "orange": extracted["orange"],
            "red": extracted["red"],
        }
        
        # Animation frames - use variety from the sheet
        DRAGON_ANIMATION_FRAMES = [
            extracted["green"],
            extracted["orange"],
            extracted["frame_1_0"],
            extracted["frame_1_1"],
        ]
    
    print("DEBUG: extracted HERO frame size ->", HERO_IMG.get_size() if HERO_IMG else None)
    print("DEBUG: extracted GOBLIN frame size ->", GOBLIN_IMG.get_size() if GOBLIN_IMG else None)
    print("DEBUG: extracted DRAGON frame size ->", DRAGON_IMG.get_size() if DRAGON_IMG else None)
    print("DEBUG: loaded TREE image ->", _TREE_IMG.get_size() if _TREE_IMG else None)
    print(f"DEBUG: Total dragon animation frames: {len(DRAGON_ANIMATION_FRAMES)}")
    
    return _HERO_SHEET, _GOBLIN_SHEET, _DRAGON_SHEET, _TREE_IMG


def get_hero_sheet():
    """Get the hero sprite sheet."""
    return _HERO_SHEET


def get_goblin_sheet():
    """Get the goblin sprite sheet."""
    return _GOBLIN_SHEET


def get_dragon_sheet():
    """Get the dragon sprite sheet."""
    return _DRAGON_SHEET


def get_tree_image():
    """Get the tree image."""
    return _TREE_IMG


def get_hero_image():
    """Get the hero battle image (single frame)."""
    return HERO_IMG


def get_goblin_image():
    """Get the goblin battle image (single frame)."""
    return GOBLIN_IMG


def get_dragon_image(frame_index=0):
    """Get a specific frame of the dragon animation.
    
    Args:
        frame_index: Which animation frame to get (0-3)
    """
    if 0 <= frame_index < len(DRAGON_ANIMATION_FRAMES):
        return DRAGON_ANIMATION_FRAMES[frame_index]
    return DRAGON_IMG


def get_dragon_animation_frames():
    """Get all dragon animation frames."""
    return DRAGON_ANIMATION_FRAMES