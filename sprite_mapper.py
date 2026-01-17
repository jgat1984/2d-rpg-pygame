"""
Interactive sprite sheet mapper tool.
Shows a grid overlay on your sprite sheet and lets you click to select sprites.
NOW WITH DYNAMIC FRAME SIZE ADJUSTMENT!
"""

import pygame
import sys
import os

# Configuration
SPRITE_SHEET_PATH = "dragons.png"  # Change this to your sprite sheet
INITIAL_FRAME_SIZE = 64  # Starting frame size
GRID_COLOR = (255, 255, 0)  # Yellow grid lines
SELECTED_COLOR = (0, 255, 0)  # Green for selected frame
HOVER_COLOR = (255, 0, 0)  # Red for hovered frame
BG_COLOR = (40, 40, 40)  # Dark gray background

class SpriteMapper:
    def __init__(self, sprite_path, initial_frame_size=64):
        pygame.init()
        
        # Load sprite sheet
        self.sprite_sheet = pygame.image.load(sprite_path)
        self.sheet_width, self.sheet_height = self.sprite_sheet.get_size()
        self.frame_size = initial_frame_size
        
        # Calculate grid dimensions
        self.update_grid()
        
        # Create window (add padding for info panel)
        self.info_panel_width = 350
        self.window_width = self.sheet_width + self.info_panel_width
        self.window_height = max(self.sheet_height, 600)
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Dragon Sprite Mapper - Dynamic Frame Size")
        
        # State
        self.selected_frames = []  # List of (col, row) tuples
        self.hover_frame = None
        self.running = True
        self.font = pygame.font.SysFont("Consolas", 12)
        self.title_font = pygame.font.SysFont("Consolas", 16, bold=True)
        
        # Multi-cell selection
        self.cell_width = 1  # How many cells wide
        self.cell_height = 1  # How many cells tall
        
        self.print_info()
    
    def update_grid(self):
        """Recalculate grid based on current frame size."""
        self.cols = max(1, self.sheet_width // self.frame_size)
        self.rows = max(1, self.sheet_height // self.frame_size)
    
    def print_info(self):
        """Print current configuration."""
        print(f"\n{'='*60}")
        print(f"Sprite sheet: {self.sheet_width}x{self.sheet_height}")
        print(f"Frame size: {self.frame_size}x{self.frame_size}")
        print(f"Grid: {self.cols} columns × {self.rows} rows")
        print(f"Multi-cell: {self.cell_width}x{self.cell_height}")
        print(f"{'='*60}\n")
    
    def get_frame_at_pos(self, mouse_x, mouse_y):
        """Convert mouse position to grid coordinates."""
        if mouse_x >= self.sheet_width or mouse_y >= self.sheet_height:
            return None
        
        col = mouse_x // self.frame_size
        row = mouse_y // self.frame_size
        
        if 0 <= col < self.cols and 0 <= row < self.rows:
            return (col, row)
        return None
    
    def handle_events(self):
        """Handle mouse and keyboard events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEMOTION:
                self.hover_frame = self.get_frame_at_pos(*event.pos)
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click - select frame
                    frame = self.get_frame_at_pos(*event.pos)
                    if frame:
                        frame_data = (frame[0], frame[1], self.cell_width, self.cell_height)
                        if frame_data in self.selected_frames:
                            self.selected_frames.remove(frame_data)
                            print(f"Deselected: col={frame[0]}, row={frame[1]}, size={self.cell_width}x{self.cell_height}")
                        else:
                            self.selected_frames.append(frame_data)
                            print(f"Selected: col={frame[0]}, row={frame[1]}, size={self.cell_width}x{self.cell_height}")
                            self.print_code_snippet(frame_data)
                
                elif event.button == 4:  # Mouse wheel up - increase frame size
                    self.frame_size = min(512, self.frame_size + 16)
                    self.update_grid()
                    self.print_info()
                
                elif event.button == 5:  # Mouse wheel down - decrease frame size
                    self.frame_size = max(16, self.frame_size - 16)
                    self.update_grid()
                    self.print_info()
            
            elif event.type == pygame.KEYDOWN:
                # Frame size adjustment with +/- keys
                if event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.frame_size = min(512, self.frame_size + 8)
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_MINUS:
                    self.frame_size = max(8, self.frame_size - 8)
                    self.update_grid()
                    self.print_info()
                
                # Multi-cell size adjustment with Shift+Arrows
                elif event.key == pygame.K_RIGHT and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.cell_width = min(5, self.cell_width + 1)
                    print(f"Multi-cell size: {self.cell_width}x{self.cell_height}")
                elif event.key == pygame.K_LEFT and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.cell_width = max(1, self.cell_width - 1)
                    print(f"Multi-cell size: {self.cell_width}x{self.cell_height}")
                elif event.key == pygame.K_DOWN and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.cell_height = min(5, self.cell_height + 1)
                    print(f"Multi-cell size: {self.cell_width}x{self.cell_height}")
                elif event.key == pygame.K_UP and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                    self.cell_height = max(1, self.cell_height - 1)
                    print(f"Multi-cell size: {self.cell_width}x{self.cell_height}")
                
                # Preset frame sizes with number keys
                elif event.key == pygame.K_1:
                    self.frame_size = 32
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_2:
                    self.frame_size = 64
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_3:
                    self.frame_size = 96
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_4:
                    self.frame_size = 128
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_5:
                    self.frame_size = 192
                    self.update_grid()
                    self.print_info()
                elif event.key == pygame.K_6:
                    self.frame_size = 256
                    self.update_grid()
                    self.print_info()
                
                # Copy code
                elif event.key == pygame.K_c:
                    self.copy_to_clipboard()
                
                # Clear selections
                elif event.key == pygame.K_x:
                    self.selected_frames.clear()
                    print("Cleared all selections")
                
                # Quit
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def print_code_snippet(self, frame_data):
        """Print code snippet for the selected frame."""
        col, row, w, h = frame_data
        pixel_x = col * self.frame_size
        pixel_y = row * self.frame_size
        pixel_w = w * self.frame_size
        pixel_h = h * self.frame_size
        
        print(f"\n--- Code Snippet ---")
        if w == 1 and h == 1:
            print(f'"dragon_{col}_{row}": ({col}, {row}),  # → ({pixel_x}, {pixel_y}) pixels, size {pixel_w}x{pixel_h}')
            print(f'get_frame(_DRAGON_SHEET, col={col}, row={row}, frame_w={self.frame_size}, frame_h={self.frame_size})')
        else:
            print(f'"dragon_{col}_{row}": ({col}, {row}, {w}, {h}),  # Multi-cell: {w}x{h}')
            print(f'# Extract {pixel_w}x{pixel_h} sprite at pixel position ({pixel_x}, {pixel_y})')
            print(f'dragon_rect = pygame.Rect({pixel_x}, {pixel_y}, {pixel_w}, {pixel_h})')
            print(f'dragon_img = _DRAGON_SHEET.subsurface(dragon_rect).copy()')
        print("-------------------\n")
    
    def copy_to_clipboard(self):
        """Generate Python code for all selected frames."""
        if not self.selected_frames:
            print("No frames selected!")
            return
        
        print("\n" + "="*60)
        print("COPY THIS CODE:")
        print("="*60)
        
        for i, frame_data in enumerate(self.selected_frames):
            col, row, w, h = frame_data
            pixel_x = col * self.frame_size
            pixel_y = row * self.frame_size
            pixel_w = w * self.frame_size
            pixel_h = h * self.frame_size
            
            print(f"\n# Dragon {i}: col={col}, row={row}, cells={w}x{h}")
            if w == 1 and h == 1:
                print(f'DRAGON_{i} = get_frame(_DRAGON_SHEET, col={col}, row={row}, frame_w={self.frame_size}, frame_h={self.frame_size})')
            else:
                print(f'dragon_{i}_rect = pygame.Rect({pixel_x}, {pixel_y}, {pixel_w}, {pixel_h})')
                print(f'DRAGON_{i} = _DRAGON_SHEET.subsurface(dragon_{i}_rect).copy()')
        
        print("\n" + "="*60 + "\n")
    
    def draw_grid(self):
        """Draw grid overlay on sprite sheet."""
        # Draw vertical lines
        for col in range(self.cols + 1):
            x = col * self.frame_size
            if x <= self.sheet_width:
                pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, self.sheet_height), 1)
        
        # Draw horizontal lines
        for row in range(self.rows + 1):
            y = row * self.frame_size
            if y <= self.sheet_height:
                pygame.draw.line(self.screen, GRID_COLOR, (0, y), (self.sheet_width, y), 1)
    
    def draw_selections(self):
        """Highlight selected and hovered frames."""
        # Draw selected frames
        for col, row, w, h in self.selected_frames:
            rect = pygame.Rect(col * self.frame_size, row * self.frame_size, 
                             w * self.frame_size, h * self.frame_size)
            pygame.draw.rect(self.screen, SELECTED_COLOR, rect, 3)
            # Draw size label
            label = self.font.render(f"{w}x{h}", True, SELECTED_COLOR)
            self.screen.blit(label, (rect.x + 5, rect.y + 5))
        
        # Draw hovered frame with multi-cell preview
        if self.hover_frame:
            col, row = self.hover_frame
            rect = pygame.Rect(col * self.frame_size, row * self.frame_size, 
                             self.cell_width * self.frame_size, 
                             self.cell_height * self.frame_size)
            pygame.draw.rect(self.screen, HOVER_COLOR, rect, 2)
            # Draw size label
            if self.cell_width > 1 or self.cell_height > 1:
                label = self.font.render(f"{self.cell_width}x{self.cell_height}", True, HOVER_COLOR)
                self.screen.blit(label, (rect.x + 5, rect.y + 5))
    
    def draw_info_panel(self):
        """Draw information panel on the right side."""
        panel_x = self.sheet_width
        
        # Fill panel background
        pygame.draw.rect(self.screen, (30, 30, 30), 
                        (panel_x, 0, self.info_panel_width, self.window_height))
        
        y_offset = 10
        
        # Title
        title = self.title_font.render("Sprite Mapper PRO", True, (255, 255, 255))
        self.screen.blit(title, (panel_x + 10, y_offset))
        y_offset += 30
        
        # Sheet info
        info_lines = [
            f"Sheet: {self.sheet_width}×{self.sheet_height}",
            f"Frame: {self.frame_size}×{self.frame_size}",
            f"Grid: {self.cols}×{self.rows}",
            f"Multi: {self.cell_width}×{self.cell_height}",
            "",
            "CONTROLS:",
            "+/- : Frame size ±8",
            "Scroll: Frame size ±16",
            "1-6: Presets (32-256)",
            "",
            "Shift+Arrows: Multi-cell",
            "Click: Select frame",
            "C: Copy code",
            "X: Clear all",
            "ESC: Quit",
            "",
            f"Selected: {len(self.selected_frames)}",
        ]
        
        for line in info_lines:
            text = self.font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 16
        
        # Show hover info
        if self.hover_frame:
            col, row = self.hover_frame
            pixel_x = col * self.frame_size
            pixel_y = row * self.frame_size
            
            y_offset += 10
            hover_lines = [
                "HOVER INFO:",
                f"Grid: ({col}, {row})",
                f"Pixel: ({pixel_x}, {pixel_y})",
                f"Size: {self.cell_width * self.frame_size}×{self.cell_height * self.frame_size}",
            ]
            
            for line in hover_lines:
                text = self.font.render(line, True, (255, 255, 100))
                self.screen.blit(text, (panel_x + 10, y_offset))
                y_offset += 16
        
        # Show selected frames list
        if self.selected_frames:
            y_offset += 10
            selected_title = self.font.render("SELECTED:", True, (100, 255, 100))
            self.screen.blit(selected_title, (panel_x + 10, y_offset))
            y_offset += 18
            
            for col, row, w, h in self.selected_frames[-15:]:  # Show last 15
                text = self.font.render(f"({col},{row}) {w}×{h}", True, (150, 255, 150))
                self.screen.blit(text, (panel_x + 15, y_offset))
                y_offset += 14
    
    def draw_preview(self):
        """Draw preview of hovered frame."""
        if not self.hover_frame:
            return
        
        col, row = self.hover_frame
        
        # Extract preview frame (multi-cell aware)
        rect = pygame.Rect(col * self.frame_size, row * self.frame_size, 
                          self.cell_width * self.frame_size, 
                          self.cell_height * self.frame_size)
        
        try:
            preview = self.sprite_sheet.subsurface(rect).copy()
            
            # Scale to fit preview area (max 256x256)
            max_preview = 200
            scale_factor = min(max_preview / preview.get_width(), 
                             max_preview / preview.get_height())
            new_w = int(preview.get_width() * scale_factor)
            new_h = int(preview.get_height() * scale_factor)
            preview = pygame.transform.scale(preview, (new_w, new_h))
            
            # Draw preview in bottom of info panel
            preview_x = self.sheet_width + (self.info_panel_width - new_w) // 2
            preview_y = self.window_height - new_h - 20
            
            # Draw border
            pygame.draw.rect(self.screen, (255, 255, 255), 
                           (preview_x - 2, preview_y - 2, new_w + 4, new_h + 4), 2)
            
            self.screen.blit(preview, (preview_x, preview_y))
            
            # Draw size label
            size_label = self.font.render(f"{rect.width}×{rect.height}px", True, (255, 255, 255))
            self.screen.blit(size_label, (preview_x, preview_y - 16))
            
        except Exception as e:
            pass
    
    def run(self):
        """Main loop."""
        clock = pygame.time.Clock()
        
        while self.running:
            self.handle_events()
            
            # Draw
            self.screen.fill(BG_COLOR)
            self.screen.blit(self.sprite_sheet, (0, 0))
            self.draw_grid()
            self.draw_selections()
            self.draw_info_panel()
            self.draw_preview()
            
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    # Check if sprite sheet exists
    if not os.path.exists(SPRITE_SHEET_PATH):
        print(f"Error: Could not find '{SPRITE_SHEET_PATH}'")
        print("Please update SPRITE_SHEET_PATH in the script.")
        sys.exit(1)
    
    print("=" * 60)
    print("DRAGON SPRITE SHEET MAPPER PRO")
    print("=" * 60)
    print("Instructions:")
    print("1. Adjust frame size with +/- or mouse wheel")
    print("2. Use number keys 1-6 for preset sizes")
    print("3. Use Shift+Arrows to select multi-cell sprites")
    print("4. Click frames to select them")
    print("5. Press 'C' to generate code")
    print("6. Press 'X' to clear selections")
    print("=" * 60)
    
    mapper = SpriteMapper(SPRITE_SHEET_PATH, initial_frame_size=INITIAL_FRAME_SIZE)
    mapper.run()