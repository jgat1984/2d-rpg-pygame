class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D RPG Demo - Overworld + Tactical Battle")

        # Convert loaded sheets and extract single-frame sprites now that a video mode exists
        _convert_and_extract_frames()

        self.clock = pygame.time.Clock()
        ...