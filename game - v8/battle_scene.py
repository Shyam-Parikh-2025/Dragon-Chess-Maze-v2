from scene import Scene
from battle import Battle
import pygame as pg
from menu_scenes import EndScreen
from ui import Button
import constants

class BattleScene(Scene):
    def __init__(self, game, is_boss=False, super_mode=0): 
        super().__init__(game)
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

        drag_name = "King" if is_boss else "Dragon Minion"
        self.battle = Battle(
            surface=game.graphic2d_surf,
            dragon_level=constants.BOSS_DRAG_LEVEL if is_boss else constants.MINION_DRAG_LEVEL,
            dragon_name= drag_name,
            player=game.player,
            super_mode=super_mode
        )
        width, height = game.graphic2d_surf.get_size()
        self.quit_button = Button(width - 190, height - 60, 180, 50, game.graphic2d_surf, 
                               on_click=self.surrender, 
                               text="SURRENDER", ACTIVE_COLOR=(255, 80, 80))
        self.resolved = False

    def surrender(self):
        self.battle.player_lost()
        print("Player surrendered!")
        if self.game.player.lives <= 0:
            print("Game Over by Surrender")
            pg.event.set_grab(False)
            pg.mouse.set_visible(True)
            self.game.change_scene(EndScreen(self.game, victory=False))
            return
        self.game.player.playing_chess = False
        self.game.player.speed = 0.1
        self._respawn_player()
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)
        self.game.change_scene(self.game.maze_scene)

    def _respawn_player(self):
        if self.game.player.soft_landing:
            r, c = self.game.current_battle_pos
            grid = self.game.grid
            rows, cols = grid.shape
            for dist in [5, 4, 3, 2, 1]:
                nr = max(0, min(rows - 1, r + dist))
                nc = max(0, min(cols - 1, c))
                if grid[nr, nc] == 0:
                    self.game.player.pos[0] = float(nc)
                    self.game.player.pos[1] = float(nr)
                    return
        self.game.player.pos[0] = 2.0
        self.game.player.pos[1] = 2.0
        
    def handle_event(self, event):
        self.battle.handle_event(event)
        self.quit_button.handle_event(event) 
        
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_q:
                self.surrender()
    
    def update(self):
        self.battle.update()
        if self.battle.check_game_over(self.game.player):
            if self.resolved :
                return
            self.resolved = True
            
            if self.battle.chess_engine.is_checkmate() and not self.battle.chess_engine.white_turn:
                if self.battle.dragon_level == constants.BOSS_DRAG_LEVEL:
                    print("YOU WIN!!!")
                    pg.event.set_grab(False)
                    pg.mouse.set_visible(True)
                    self.game.change_scene(EndScreen(self.game, victory=True))
                    return

                r, c = self.game.current_battle_pos                
                self.game.grid[r, c] = 0
                print("One Battle cleared!")
            
            elif self.game.player.lives <= 0:
                print("Game Over")
                pg.event.set_grab(False)
                pg.mouse.set_visible(True)
                self.game.change_scene(EndScreen(self.game, victory=False))
                return
            else:
                print("Stalemate - respawing)")
                self._respawn_player()
            self.game.player.playing_chess = False
            self.game.player.speed = 0.1
            self.game.player.can_move = True

            pg.event.set_grab(True)
            pg.mouse.set_visible(False)
            
            self.game.change_scene(self.game.maze_scene)
            pg.time.wait(1)
            
    def render(self):
        game = self.game
        
        game.graphic3d.ctx.clear(0.05, 0.05, 0.1)
        game.graphic2d_surf.fill((0,0,0,0))
        game.graphic2d.draw_chess_board(
            self.battle.chess_engine,
            selected_sq=self.battle.selected_sq,
            hover_sq=self.battle.hover_sq,
            valid_moves= self.battle.hover_moves)
        game.graphic2d.draw_fps(self.battle.ai_thinking, True)
        self.quit_button.draw()
        game.graphic3d.render_2d_surf(game.graphic2d_surf)

    def resize(self, width, height):
        self.quit_button.surface = self.game.graphic2d_surf
        self.quit_button.rect.x = width - 190
        self.quit_button.rect.y = height - 60
        self.battle.surface = self.game.graphic2d_surf