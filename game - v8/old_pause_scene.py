import pygame as pg
from scene import Scene
from ui import UI_MANAGER, Button
from menu_scenes import StartScreen
from typing import Callable

from game import Game # To delete
from player import Player

class PauseScene(Scene):
    def __init__(self, game: Game, previous_scene):
        super().__init__(game)
        self.prev_scene = previous_scene
        self.manager = UI_MANAGER(game.graphic2d_surf)

        pg.event.set_grab(False)
        pg.mouse.set_visible(True)

        self.manager.add_element(Button, "Resume", on_click=self.resume,
                                 alignment='CENTER_BOTH', y_offset=-120)
        self.manager.add_element(Button, "SKILL TREE", on_click=self.open_skill_tree,
                                 alignment='CENTER_BOTH', y_offset=-40)
        self.manager.add_element(Button, "QUIT TO MENU", on_click=self.quit,
                                 alignment='CENTER_BOTH', y_offset=40, ACTIVE_COLOR=(255, 100, 100))
        self.font = pg.font.Font(None, 100)

    def resume(self):
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)
        self.game.change_scene(self.prev_scene)
    
    def open_skill_tree(self):
        self.game.change_scene(SkillTreeScene(self.game, self))
    
    def quit(self):
        self.game.change_scene(StartScreen(self.game))
    
    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.resume()
        self.manager.handle_event(event)

    def update(self):
        self.manager.update()
    
    def render(self):
        self.prev_scene.render()
        graphic2d_surf = self.game.graphic2d_surf
        width, height = graphic2d_surf.get_size()
        overlay = pg.Surface((width, height), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        graphic2d_surf.blit(overlay, (0, 0))
        txt = self.font.render("PAUSED", True, (255, 255, 255))
        rect = txt.get_rect(center=(width//2, 100))
        graphic2d_surf.blit(txt, rect)
        self.manager.draw()
        self.game.graphic3d.render_2d_surf(graphic2d_surf)
    
    def resize(self, width, height):
        self.prev_scene.resize(width, height)
        self.manager.handle_resize(width, height, self.game.graphic2d_surf)

class SkillTreeScene(Scene):
    def __init__(self, game: Game, pause_menu):
        super().__init__(game)
        self.pause_menu: PauseScene = pause_menu
        self.ui_manager = UI_MANAGER(game.graphic2d_surf)
        self.skill_manager = Skill_Manager({
            "root": Skill(
        name="root", description="Start", cost=0, prereqs=[],
        branches=[], branch_name="purple",
        effect=lambda p: None,
        pos=(400, 80), color=(160, 100, 220)
    ),
    "tough_scales": Skill(
        name="tough_scales", description="+1 life", cost=200, prereqs=["root"],
        branches=[], branch_name="coral",
        effect=lambda p: setattr(p, "lives", p.lives + 1),
        pos=(200, 220), color=(220, 90, 70)
    ),
    "chess_instinct": Skill(
        name="chess_instinct", description="AI -3s", cost=300, prereqs=["root"],
        branches=[], branch_name="blue",
        effect=lambda p: setattr(p, "time_limit_of_AI", p.time_limit_of_AI + 3),
        pos=(400, 220), color=(60, 130, 220)
    ),
    "hunters_eye": Skill(
        name="hunters_eye", description="Targets slower", cost=300, prereqs=["root"],
        branches=[], branch_name="teal",
        effect=lambda p: setattr(p, "fps_block_speed_multiplier", p.fps_block_speed_multiplier * 0.8),
        pos=(600, 220), color=(40, 180, 150)
    ),
    "iron_will": Skill(
        name="iron_will", description="+2 lives", cost=500, prereqs=["tough_scales"],
        branches=[], branch_name="coral",
        effect=lambda p: setattr(p, "lives", p.lives + 2),
        pos=(200, 380), color=(220, 90, 70)
    ),
    "grandmaster": Skill(
        name="grandmaster", description="AI -8s", cost=700, prereqs=["chess_instinct"],
        branches=[], branch_name="blue",
        effect=lambda p: setattr(p, "time_limit_of_AI", p.time_limit_of_AI + 8),
        pos=(400, 380), color=(60, 130, 220)
    ),
    "hawk_sight": Skill(
        name="hawk_sight", description="+10s FPS", cost=400, prereqs=["hunters_eye"],
        branches=[], branch_name="teal",
        effect=lambda p: setattr(p, "time_limit_of_fps", p.time_limit_of_fps + 10),
        pos=(600, 380), color=(40, 180, 150)
    ),

        }, self.game.graphic2d_surf)
        self.branches = []
        self.selected = None
        self.scroll_y = 0

        self.ui_manager.add_element(Button, "GO BACK", on_click=self.go_back,
                                 alignment='BOTTOM CENTER_X', y_offset=-40)
        
        self.node_rects = {}
    
    def go_back(self):
        self.game.change_scene(self.pause_menu)
    
    def handle_event(self, event):
        if event.type == pg.MOUSEMOTION:
            self.selected = None
            for name, rect in self.node_rects.items():
                rect: pg.Rect
                if rect.collidepoint(event.pos):
                    self.selected = self.skill_manager.get_by_name(name)
                    break
        if event.type == pg.MOUSEBUTTONDOWN and self.selected:
            self.skill_manager.try_buy(self.selected, self.game.player,
                                       self.game.player.unlocked_skills)
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                self.go_back()
        self.ui_manager.handle_event(event)
    
    def update(self):
        self.ui_manager.update()
        self.skill_manager.update_states(self.game.player.score,
                                         self.game.player.unlocked_skills)
    
    def render(self):
        graphic_2d_surf = self.game.graphic2d_surf
        graphic_2d_surf.fill((20, 25, 35))
        self.node_rects = self.skill_manager.draw_all(self.selected,
                                                      0, self.scroll_y)
        self.ui_manager.draw()

        self.game.graphic3d.render_2d_surf(graphic_2d_surf)

    def resize(self, width, height):
        self.ui_manager.handle_resize(width, height, self.game.graphic2d_surf)
        self.skill_manager.handle_resize(self.game.graphic2d_surf)

class Skill():
    _font_small = None
    _font_large = None
    def __init__(self, name: str, description: str, cost: int,
                 prereqs: list, branches: list, branch_name: str,
                 effect: Callable, pos: tuple, color: tuple, 
                 state: str = "locked", width: int = 150, 
                 height: int = 60,):

        self.name = name
        self.description = description
        self.cost = cost
        self.prereqs = prereqs
        self.branches = branches
        self.branch_name = branch_name
        self.effect = effect
        self.state = state # can be "locked", "unlocked", "available"
        self.org_pos = pos
        self.pos = list(pos)
        if Skill._font_small is None or Skill._font_large is None:
            Skill._font_small = pg.font.Font(None, 21)
            Skill._font_large = pg.font.Font(None, 30)
        self.font_small = Skill._font_small
        self.font_large = Skill._font_large 
        self.width, self.height = width, height
        self.color = color
    
    def is_available(self, player_balance, unlocked_set):
        if self.state == "unlocked": return False
        prereqs_met = all(p in unlocked_set for p in self.prereqs)
        return prereqs_met and self.cost <= player_balance
    
    def draw(self, surface, selected, scroll_x, scroll_y):
        cx, cy = self.pos
        cx += scroll_x
        cy += scroll_y
        width, height = self.width, self.height
        rect = pg.Rect(cx - width//2, cy - height//2, width, height)
        color = self.color
        state = self.state

        if state == "unlocked":
            bgc = (color[0]//2, color[1]//2, color[2]//2)  # dimmed
            fc = (180, 180, 180)
            border = color
        elif state == "available":
            bgc = color
            fc = (255, 255, 255)
            border = (255, 215, 0)  # gold border = buyable
        else:  # locked
            bgc = (30, 30, 38)
            fc = (80, 80, 90)
            border = (60, 60, 70)
        
        pg.draw.rect(surface, bgc, rect, border_radius=10)
        pg.draw.rect(surface, border, rect, 2, border_radius=10)
        if selected:
            pg.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=10)
        
        name_surf = self.font_large.render(self.name, True, fc)
        desc_color = (120, 120, 130) if state == "unlocked" else (fc[0]//2, fc[1]//2, fc[2]//2)
        desc_surf = self.font_small.render(self.description, True, desc_color)
        surface.blit(name_surf, name_surf.get_rect(centerx=rect.centerx, y=rect.y + 10))
        surface.blit(desc_surf, desc_surf.get_rect(centerx=rect.centerx, y=rect.y + 34))
        return rect

    def resize(self, width_diff, height_diff):
        self.pos[0] += width_diff
        self.pos[1] += height_diff

class Skill_Manager():
    def __init__(self, skills: dict, surface):
        self.skills = skills
        self.surface = surface
    
    def get_by_name(self, name):
        return self.skills.get(name, None)

    def update_states(self, player_balance, unlocked_set):
        for skill in self.skills.values():
            if skill.name in unlocked_set:
                skill.state = "unlocked"
            elif skill.is_available(player_balance, unlocked_set):
                skill.state = "available"
            else:
                skill.state = "locked"
    
    def try_buy(self, skill: Skill, player, unlocked_set):
        if not skill.is_available(player.score, unlocked_set):
            return False
        player.score -= skill.cost
        skill.effect(player)
        unlocked_set.add(skill.name)
        skill.state = "unlocked"
        return True
    
    def draw_connections(self, scroll_x, scroll_y):
        for skill in self.skills.values():
            cx_b = skill.pos[0] + scroll_x
            cy_b = skill.pos[1] + scroll_y
            for prereq_name in skill.prereqs:
                prereq = self.get_by_name(prereq_name)
                if prereq:
                    cx_a = prereq.pos[0] + scroll_x
                    cy_a = prereq.pos[1] + scroll_y
                    both_active = prereq.state == "unlocked" and skill.state != "locked"
                    color = (180, 180, 180) if both_active else (70, 70, 70)
                    pg.draw.line(self.surface, color, (cx_a, cy_a), (cx_b, cy_b), 3)
    
    def draw_all(self, selected_skill, scroll_x, scroll_y):
        self.draw_connections(scroll_x, scroll_y)
        rects = {}
        for name, skill in self.skills.items():
            rects[name] = skill.draw(self.surface, skill is selected_skill, scroll_x, scroll_y)
        return rects

    def change_surface(self, surface):
        self.surface = surface
    
    def handle_resize(self, surface):
        self.change_surface(surface)
        width, height = self.surface.get_size()
        for skill in self.skills.values():
            skill.resize(width, height)
