"""
Simple 2D RPG demo with an overworld and a graphical tactical battle scene.
- Overworld: tile-based movement, walk with arrow keys, press Space to interact/start battle.
- Battle: grid-based, turn-based movement and attacks. Player moves then enemy AI moves.
This is a compact demo (no external assets) suitable for iteration in Visual Studio.
"""

import pygame
import sys
import os

# Initialize pygame FIRST before importing other modules
pygame.init()

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from audio import init_audio, play_music, stop_music
from assets import BASE_DIR, OVERWORLD_MUSIC_PATH, BATTLE_MUSIC_PATH, load_assets
from overworld import Overworld
from battle import Battle


class Game:
    SCENE_OVERWORLD = 0
    SCENE_BATTLE = 1

    def __init__(self):
        # Initialize audio
        init_audio()
        
        # Load assets (this will also initialize the font)
        load_assets()
        
        # Create display
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("2D RPG Demo - Overworld + Tactical Battle")

        self.clock = pygame.time.Clock()
        self.scene = Game.SCENE_OVERWORLD
        self.overworld = Overworld(self)
        self.battle = None
        self.running = True
        
        # Start overworld music
        if os.path.isfile(OVERWORLD_MUSIC_PATH):
            play_music(OVERWORLD_MUSIC_PATH, loop=-1, volume=0.4)

    def start_battle(self, player_unit, enemy_unit):
        # stop overworld music and play battle music (if available)
        stop_music()
        if os.path.isfile(BATTLE_MUSIC_PATH):
            play_music(BATTLE_MUSIC_PATH, loop=-1, volume=0.5)

        self.battle = Battle(self, player_unit, enemy_unit)
        self.scene = Game.SCENE_BATTLE

    def end_battle(self, player_won, player_unit_copy):
        # stop battle music and resume overworld music (if available)
        stop_music()
        if os.path.isfile(OVERWORLD_MUSIC_PATH):
            play_music(OVERWORLD_MUSIC_PATH, loop=-1, volume=0.4)

        if player_won:
            for e in self.overworld.enemies:
                if e.is_alive():
                    e.hp = 0
                    break
        self.overworld.player.hp = player_unit_copy.hp
        self.scene = Game.SCENE_OVERWORLD
        self.battle = None

    def main_loop(self):
        # Debug: print the asset folder + listing
        print("DEBUG: BASE_DIR =", BASE_DIR)
        try:
            print("DEBUG: directory listing:", os.listdir(BASE_DIR))
        except Exception as ex:
            print("DEBUG: listdir failed:", ex)

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.USEREVENT + 1:
                    if self.scene == Game.SCENE_BATTLE and self.battle:
                        self.battle.enemy_turn()
                    pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                else:
                    if self.scene == Game.SCENE_OVERWORLD:
                        self.overworld.handle_event(event)
                    elif self.scene == Game.SCENE_BATTLE:
                        self.battle.handle_event(event)

            if self.scene == Game.SCENE_OVERWORLD:
                self.overworld.update(dt)
            elif self.scene == Game.SCENE_BATTLE:
                self.battle.update(dt)

            if self.scene == Game.SCENE_OVERWORLD:
                self.overworld.render(self.screen)
            elif self.scene == Game.SCENE_BATTLE:
                self.battle.render(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().main_loop()