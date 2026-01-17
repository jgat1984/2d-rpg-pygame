"""
Game entities: Unit and Tree classes.
"""

import pygame
from assets import detect_frame_size, get_frame


class Unit:
    def __init__(self, name, x, y, hp, atk, movement, color, sprite_sheet=None):
        self.name = name
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.atk = atk
        self.movement = movement
        self.color = color
        self.has_moved = False
        self.has_acted = False
        
        # Sprite direction tracking
        self.facing = "down"  # default: down, up, left, right
        self.sprite_sheet = sprite_sheet
        self.sprite_frames = {}
        
        # Animation tracking
        self.anim_frame = 0  # Current animation frame (0-3)
        self.anim_timer = 0  # Timer for animation
        self.anim_speed = 0.15  # Seconds per frame
        self.is_moving = False  # Track if unit is moving
        
        # Load directional sprites if sheet is provided
        if sprite_sheet:
            self._load_directional_sprites(sprite_sheet)
    
    def _load_directional_sprites(self, sheet):
        """Extract directional sprites from sheet with animation frames.
        Assumes standard RPG layout: down=row 0, left=row 1, right=row 2, up=row 3
        Each row has 4 animation frames.
        """
        frame_w, frame_h = detect_frame_size(sheet)
        if frame_w and frame_h:
            # Load all 4 animation frames for each direction
            self.sprite_frames["down"] = [get_frame(sheet, col, 0, frame_w, frame_h) for col in range(4)]
            self.sprite_frames["left"] = [get_frame(sheet, col, 1, frame_w, frame_h) for col in range(4)]
            self.sprite_frames["right"] = [get_frame(sheet, col, 2, frame_w, frame_h) for col in range(4)]
            self.sprite_frames["up"] = [get_frame(sheet, col, 3, frame_w, frame_h) for col in range(4)]
            
            print(f"DEBUG: {self.name} loaded animated sprites (4 frames per direction)")
    
    def update_animation(self, dt):
        """Update animation frame based on movement."""
        if self.is_moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                old_frame = self.anim_frame
                self.anim_frame = (self.anim_frame + 1) % 4  # Cycle through 0-3 (all 4 frames)
                print(f"DEBUG: {self.name} ANIMATION CYCLE - {old_frame} -> {self.anim_frame} (facing: {self.facing}, is_moving: {self.is_moving})")
                
                # After one animation cycle completes, stop moving
                if self.anim_frame == 0:  # Completed full cycle (went back to frame 0)
                    self.is_moving = False
        else:
            # Keep current frame when idle (don't reset to 1)
            self.anim_timer = 0
    
    def get_current_sprite(self):
        """Return the sprite for current facing direction and animation frame."""
        if not self.sprite_frames:
            return None

        frames = self.sprite_frames.get(self.facing)

        # Handle flipping for left direction
        if self.facing == "left":
            # Check if we need to flip from right frames
            if not frames or frames[0] is None:
                right_frames = self.sprite_frames.get("right")
                if right_frames and right_frames[0]:
                    # Get the right-facing frame
                    sprite = right_frames[self.anim_frame]
                    # Flip it horizontally (True, False) for left direction
                    return pygame.transform.flip(sprite, False, True)
            else:
                # We have dedicated left frames, return current animation frame
                return frames[self.anim_frame] if frames[self.anim_frame] else frames[0]

        # Return current animation frame for the direction
        if frames and self.anim_frame < len(frames) and frames[self.anim_frame]:
            return frames[self.anim_frame]

        # Fallback to first frame of down direction
        down_frames = self.sprite_frames.get("down")
        if down_frames and down_frames[0]:
            return down_frames[0]

        return None
    
    def is_alive(self):
        return self.hp > 0

    def distance_to(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)


class Tree:
    """Represents a tree obstacle on the map."""
    def __init__(self, x, y):
        self.x = x
        self.y = y