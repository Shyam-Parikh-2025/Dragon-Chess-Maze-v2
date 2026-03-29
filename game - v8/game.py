import pygame as pg
from pathlib import Path
import constants
from player import Player
from graphics import Graphics2d, Graphics3d
from map_gen import MapGen

base_path = Path(__file__).resolve().parent

class Game:
    def __init__(self):
        pg.init()
        self.is_fullscreen = False
        self.screen = pg.display.set_mode((constants.WIDTH, constants.HEIGHT), pg.OPENGL | pg.DOUBLEBUF | pg.RESIZABLE)

        self.clock = pg.time.Clock()
        icon_path = base_path / 'images' / 'white_queen.png'
        try:
            game_icon = pg.image.load(icon_path) 
            pg.display.set_icon(game_icon)
        except FileNotFoundError:
            print("Icon file not found.")
        pg.display.set_caption("Dragon Chess Maze")

        self.player = Player(start_pos=(2, 2))
        self.graphic3d = Graphics3d(self.screen)
        self.graphic2d_surf = pg.Surface((constants.WIDTH, constants.HEIGHT), pg.SRCALPHA).convert_alpha()
        self.graphic2d = Graphics2d(self.graphic2d_surf, self.player)

        self.map_gen = MapGen(numBattles=81, maze_size=(45,45)) 
        self.grid, self.portals = self.map_gen.generate_full()

        self.current_battle_pos = (0,0)
        self.current_scene = None
        self.running = True
        self.wall_color = (0.3, 0.3, 0.3)
        self.portal_color = (0.6, 0.6, 0.6)
        self.maze_scene = None
        self.player.time_limit_of_AI = 0
        self.retry = False    
    
    def change_scene(self, new_scene):
        self.current_scene = new_scene
    
    def run(self):
        self.running = True
        while self.running:
            self.delta_time = self.clock.tick(60) / 1000.0

            for event in pg.event.get():
                if event.type == pg.QUIT:
                    self.running = False
                # Resizing Fix
                if event.type == pg.VIDEORESIZE:
                    width, height = event.size
                    self.graphic3d.ctx.viewport = (0, 0, width, height)
                    self.graphic3d.update_projection(width=width, height=height)
                    self.graphic2d_surf = pg.Surface((width, height), pg.SRCALPHA).convert_alpha()
                    self.graphic2d.surface = self.graphic2d_surf
                    if hasattr(self.current_scene, 'resize'):
                        self.current_scene.resize(width, height) 
                if self.current_scene:
                    self.current_scene.handle_event(event)
            
            if self.current_scene:
                self.current_scene.update()
                self.current_scene.render()
            
            pg.display.flip()
            if self.retry:
                return True
        return False