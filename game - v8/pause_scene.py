import pygame as pg
from scene import Scene
from ui import UI_MANAGER, Button
from menu_scenes import StartScreen
from typing import Callable
from game import Game

# ── LAYOUT ────────────────────────────────────────────────────────────────────
SX = 185
SY = 90
_T1, _T2      = -int(SY*1.6), -int(SY*3.2)
_B1, _B2, _B3 =  int(SY*1.6),  int(SY*3.2),  int(SY*4.8)
_B4           =  int(SY*6.4)   # extra row for warp

BRANCH_COLORS = {
    "crimson":  (190,  45,  45),
    "sapphire": ( 45,  95, 210),
    "emerald":  ( 35, 165,  75),
    "amber":    (205, 145,  20),
    "root":     (145,  85, 215),
}

SKILL_OFFSETS = {
    "root":            (      0,    0),

    # ── Sentinel (Chess) — top-left ──────────────────────────────────────────
    # Row _T1:  pawn_shield → royal_guard → ai_fatigue
    "pawn_shield":     (  -SX,  _T1),
    "royal_guard":     (-SX*2,  _T1),
    "ai_fatigue":      (-SX*3,  _T1),
    # Row _T2:  dragons_blunder (from royal_guard) | blitz_specialist (from ai_fatigue)
    #           both converge on berserker_king
    "dragons_blunder": (  -SX,  _T2),
    "blitz_specialist":(-SX*2,  _T2),
    "berserker_king":  (-SX*3,  _T2),

    # ── Guardian (Defense) — top-right ───────────────────────────────────────
    # Row _T1:  sturdy_mind → iron_will | peace_treaty
    "sturdy_mind":     (   SX,  _T1),
    "iron_will":       ( SX*2,  _T1),
    "peace_treaty":    ( SX*3,  _T1),
    # Row _T2:  second_wind (from iron_will) | soft_landing (from peace_treaty) → kings_ransom
    "second_wind":     (   SX,  _T2),
    "soft_landing":    ( SX*2,  _T2),
    "kings_ransom":    ( SX*3,  _T2),

    # ── Explorer (Utility) — bottom-left ─────────────────────────────────────
    # Row _B1:  swift_boots → speedster | steady_hand
    "swift_boots":     (  -SX,  _B1),
    "speedster":       (-SX*2,  _B1),
    "steady_hand":     (-SX*3,  _B1),
    # Row _B2:  sharp_eyes (from swift_boots) → eagle_vision | extra_spoils (from steady_hand)
    "sharp_eyes":      (  -SX,  _B2),
    "eagle_vision":    (-SX*2,  _B2),
    "extra_spoils":    (-SX*3,  _B2),

    # ── Seer (Navigation) — bottom-right ─────────────────────────────────────
    # Row _B1:  beacon → home_beacon | portal_beacon
    "beacon":          (   SX,  _B1),
    "home_beacon":     ( SX*2,  _B1),
    "portal_beacon":   ( SX*3,  _B1),
    # Row _B2:  boss_tracker (from beacon) | multi_beacon (from home_beacon) | portal_tower (from portal_beacon)
    "boss_tracker":    (   SX,  _B2),
    "multi_beacon":    ( SX*2,  _B2),
    "portal_tower":    ( SX*3,  _B2),
    # Row _B3:  clarity (from boss_tracker) | gps (from clarity, offset right)
    "clarity":         (   SX,  _B3),
    "gps":             ( SX*2,  _B3),
    # Row _B4:  warp (from gps)
    "warp":            ( SX*2,  _B4),
}
 
BRANCH_LABELS = [
    ("-- SENTINEL --", -SX*2, _T1 - 52, BRANCH_COLORS["crimson"]),
    ("-- GUARDIAN --",  SX*2, _T1 - 52, BRANCH_COLORS["sapphire"]),
    ("-- EXPLORER --", -SX*2, _B1 - 52, BRANCH_COLORS["emerald"]),
    ("-- SEER --",      SX*2, _B1 - 52, BRANCH_COLORS["amber"]),
]
 
def _flag(attr):
    return lambda p: setattr(p, attr, True)
 
SKILL_EFFECTS = {
    "root":            lambda p: None,
    # Sentinel
    "pawn_shield":     _flag("pawn_shield"),
    "royal_guard":     _flag("royal_guard"),
    "ai_fatigue":      _flag("ai_fatigue"),
    "dragons_blunder": _flag("dragons_blunder"),
    "blitz_specialist":_flag("blitz_specialist"),
    "berserker_king":  _flag("berserker_king"),
    # Guardian
    "sturdy_mind":     lambda p: setattr(p, "lives", p.lives + 1),
    "iron_will":       lambda p: setattr(p, "lives", p.lives + 1),
    "peace_treaty":    _flag("peace_treaty"),
    "soft_landing":    _flag("soft_landing"),
    "second_wind":     _flag("second_wind"),
    "kings_ransom":    _flag("kings_ransom"),
    # Explorer
    "swift_boots":     lambda p: setattr(p, "speed", p.speed * 1.15),
    "speedster":       _flag("speedster"),
    "steady_hand":     lambda p: setattr(p, "time_limit_of_fps", p.time_limit_of_fps + 10),
    "sharp_eyes":      lambda p: setattr(p, "minimap_radius_bonus",
                                          getattr(p, "minimap_radius_bonus", 1.0) * 1.2),
    "eagle_vision":    lambda p: setattr(p, "minimap_radius_bonus", 1.5),
    "extra_spoils":    _flag("extra_spoils"),
    # Seer
    "beacon":          _flag("beacon"),
    "home_beacon":     _flag("home_beacon"),          # H key sets home waypoint
    "portal_beacon":   _flag("portal_beacon"),        # P key sets portal waypoint
    "multi_beacon":    lambda p: setattr(p, "max_waypoints", 3),  # 1 → 3 custom slots
    "boss_tracker":    _flag("boss_tracker"),
    "clarity":         _flag("clarity"),
    "gps":             _flag("gps"),
    "warp":            _flag("warp"),
    "portal_tower":    _flag("portal_tower"),
}
 
SKILL_DEFS = {
    "root":            ("DRAGON TAMER",     "Begin your journey",          0, [],                                       "root"),
    # ── Sentinel ──────────────────────────────────────────────────────────────
    "pawn_shield":     ("PAWN SHIELD",      "+1 extra pawn at start",    150, ["root"],                                 "crimson"),
    "royal_guard":     ("ROYAL GUARD",      "One start pawn = Queen",    300, ["pawn_shield"],                          "crimson"),
    "ai_fatigue":      ("AI FATIGUE",       "AI loses 2 depth/10 moves", 250, ["pawn_shield"],                          "crimson"),
    "dragons_blunder": ("DRAGON'S BLUNDER", "AI plays its 3rd-best move",400, ["royal_guard"],                          "crimson"),
    "blitz_specialist":("BLITZ SPECIALIST", "Win ≤40 moves = 2x pts",    400, ["ai_fatigue"],                           "crimson"),
    "berserker_king":  ("BERSERKER KING",   "King jumps like Knight",     600, ["dragons_blunder", "blitz_specialist"], "crimson"),
    # ── Guardian ──────────────────────────────────────────────────────────────
    "sturdy_mind":     ("STURDY MIND",      "Additional life",           200, ["root"],                                 "sapphire"),
    "iron_will":       ("IRON WILL",        "Additional life",           400, ["sturdy_mind"],                          "sapphire"),
    "peace_treaty":    ("PEACE TREATY",     "Stalemates don't cost life",300, ["sturdy_mind"],                          "sapphire"),
    "soft_landing":    ("SOFT LANDING",     "Loss = respawn near portal",250, ["peace_treaty"],                         "sapphire"),
    "second_wind":     ("SECOND WIND",      "Survive death once per run",500, ["iron_will"],                            "sapphire"),
    "kings_ransom":    ("KING'S RANSOM",    "Pay 500 pts to survive",    600, ["second_wind"],                          "sapphire"),
    # ── Explorer ──────────────────────────────────────────────────────────────
    "swift_boots":     ("SWIFT BOOTS",      "Move speed +15%",           200, ["root"],                                 "emerald"),
    "speedster":       ("SPEEDSTER",        "Hold Shift = 2x speed",     300, ["swift_boots"],                          "emerald"),
    "steady_hand":     ("STEADY HAND",      "FPS time limit +10s",       300, ["swift_boots"],                          "emerald"),
    "sharp_eyes":      ("SHARP EYES",       "Minimap radius +20%",       200, ["swift_boots"],                          "emerald"),
    "eagle_vision":    ("EAGLE VISION",     "Minimap radius x1.5 total", 400, ["sharp_eyes"],                           "emerald"),
    "extra_spoils":    ("EXTRA SPOILS",     "+25% score per battle",     350, ["steady_hand"],                          "emerald"),
    # ── Seer ──────────────────────────────────────────────────────────────────
    "beacon":          ("BEACON",           "M = map mode, click=waypoint",200, ["root"],                               "amber"),
    "home_beacon":     ("HOME BEACON",      "H key = home waypoint",     250, ["beacon"],                               "amber"),
    "portal_beacon":   ("PORTAL BEACON",    "P key = nearest portal",    250, ["beacon"],                               "amber"),
    "boss_tracker":    ("BOSS TRACKER",     "Boss dot after 2 kills",    250, ["beacon", "portal_tower"],                               "amber"),
    "portal_tower": ("PORTAL TOWER", "Portals are tall pillars", 300, ["portal_beacon"], "amber"),
    "multi_beacon":    ("MULTI BEACON",     "Up to 3 custom waypoints",  350, ["home_beacon"],                          "amber"),
    "clarity":         ("CLARITY",          "No fog in the 3D maze",     500, ["boss_tracker"],                         "amber"),
    "gps":             ("GPS",              "Full maze on minimap",      700, ["clarity"],                              "amber"),
    "warp":            ("WARP",             "Teleport to boss once",     900, ["gps"],                                  "amber"),
}

# ── SKILL CLASS ───────────────────────────────────────────────────────────────
class Skill:
    _font_name = None
    _font_desc = None

    def __init__(self, name, display_name, description, cost, prereqs,
                 branch_name, effect, pos, color,
                 state="locked", width=162, height=58):
        self.name         = name
        self.display_name = display_name
        self.description  = description
        self.cost         = cost
        self.prereqs      = prereqs
        self.branch_name  = branch_name
        self.effect       = effect
        self.state        = state
        self.pos          = pos
        self.width        = width
        self.height       = height
        self.color        = color
        if Skill._font_name is None:
            Skill._font_name = pg.font.Font(None, 21)
            Skill._font_desc = pg.font.Font(None, 19)

    def is_available(self, player_score, unlocked_set):
        if self.state == "unlocked":
            return False
        return all(p in unlocked_set for p in self.prereqs) and self.cost <= player_score

    def draw(self, surface, selected, scroll_x, scroll_y):
        cx = self.pos[0] + scroll_x
        cy = self.pos[1] + scroll_y
        rect = pg.Rect(cx - self.width//2, cy - self.height//2, self.width, self.height)
        c = self.color
        if self.state == "unlocked":
            bgc = (c[0]//4, c[1]//4, c[2]//4)
            fc  = (130, 130, 140)
            border = (c[0]//2, c[1]//2, c[2]//2)
            dc  = (90, 90, 100)
        elif self.state == "available":
            bgc = (c[0]//3+10, c[1]//3+10, c[2]//3+10)
            fc  = (255, 255, 255)
            border = (255, 215, 0)
            dc  = (200, 200, 210)
        else:
            bgc = (24, 24, 32); fc = (60, 60, 72)
            border = (44, 44, 56); dc = (48, 48, 60)
        pg.draw.rect(surface, bgc, rect, border_radius=8)
        pg.draw.rect(surface, border, rect, 2, border_radius=8)
        if selected:
            pg.draw.rect(surface, (255, 255, 255), rect, 3, border_radius=8)
        ns = Skill._font_name.render(self.display_name, True, fc)
        ds = Skill._font_desc.render(self.description,  True, dc)
        surface.blit(ns, ns.get_rect(centerx=rect.centerx, y=rect.y + 9))
        surface.blit(ds, ds.get_rect(centerx=rect.centerx, y=rect.y + 34))
        return rect


# ── SKILL MANAGER ─────────────────────────────────────────────────────────────
class Skill_Manager:
    def __init__(self, skills, surface):
        self.skills  = skills
        self.surface = surface

    def get_by_name(self, name):
        return self.skills.get(name)

    def update_states(self, player_score, unlocked_set):
        for skill in self.skills.values():
            if skill.name in unlocked_set:
                skill.state = "unlocked"
            elif skill.is_available(player_score, unlocked_set):
                skill.state = "available"
            else:
                skill.state = "locked"

    def try_buy(self, skill, player, unlocked_set):
        if not skill.is_available(player.score, unlocked_set):
            return False
        player.score -= skill.cost
        skill.effect(player)
        unlocked_set.add(skill.name)
        skill.state = "unlocked"
        return True

    def update_positions(self, cx, cy):
        for key, skill in self.skills.items():
            ox, oy = SKILL_OFFSETS.get(key, (0, 0))
            skill.pos = (cx + ox, cy + oy)

    def draw_connections(self, scroll_x, scroll_y):
        for skill in self.skills.values():
            bx = skill.pos[0] + scroll_x
            by = skill.pos[1] + scroll_y
            for pname in skill.prereqs:
                pre = self.get_by_name(pname)
                if pre:
                    ax = pre.pos[0] + scroll_x
                    ay = pre.pos[1] + scroll_y
                    active = pre.state == "unlocked" and skill.state != "locked"
                    pg.draw.line(self.surface,
                                 (140, 140, 140) if active else (48, 48, 58),
                                 (ax, ay), (bx, by), 2)

    def draw_all(self, selected_skill, scroll_x, scroll_y):
        self.draw_connections(scroll_x, scroll_y)
        rects = {}
        for name, skill in self.skills.items():
            rects[name] = skill.draw(self.surface, skill is selected_skill,
                                     scroll_x, scroll_y)
        return rects

    def change_surface(self, surface):
        self.surface = surface


# ── BUILDER ───────────────────────────────────────────────────────────────────
def build_skill_tree(cx, cy, surface):
    skills = {}
    for key, (display_name, desc, cost, prereqs, branch) in SKILL_DEFS.items():
        ox, oy = SKILL_OFFSETS[key]
        skills[key] = Skill(
            name=key, display_name=display_name, description=desc,
            cost=cost, prereqs=prereqs, branch_name=branch,
            effect=SKILL_EFFECTS.get(key, lambda p: None),
            pos=(cx + ox, cy + oy),
            color=BRANCH_COLORS[branch],
        )
    return Skill_Manager(skills, surface)


# ── PAUSE SCENE ───────────────────────────────────────────────────────────────
class PauseScene(Scene):
    def __init__(self, game: Game, previous_scene):
        super().__init__(game)
        self.prev_scene = previous_scene
        self.manager    = UI_MANAGER(game.graphic2d_surf)
        pg.event.set_grab(False)
        pg.mouse.set_visible(True)
        self.manager.add_element(Button, "RESUME",       on_click=self.resume,
                                 alignment='CENTER_BOTH', y_offset=-120)
        self.manager.add_element(Button, "SKILL TREE",   on_click=self.open_skill_tree,
                                 alignment='CENTER_BOTH', y_offset=-40)
        self.manager.add_element(Button, "QUIT TO MENU", on_click=self.quit,
                                 alignment='CENTER_BOTH', y_offset=40,
                                 ACTIVE_COLOR=(255, 100, 100))
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
        if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
            self.resume()
        self.manager.handle_event(event)

    def update(self):
        self.manager.update()

    def render(self):
        self.prev_scene.render()
        surf = self.game.graphic2d_surf
        w, h = surf.get_size()
        overlay = pg.Surface((w, h), pg.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))
        txt = self.font.render("PAUSED", True, (255, 255, 255))
        surf.blit(txt, txt.get_rect(center=(w//2, 100)))
        self.manager.draw()
        self.game.graphic3d.render_2d_surf(surf)

    def resize(self, width, height):
        self.prev_scene.resize(width, height)
        self.manager.handle_resize(width, height, self.game.graphic2d_surf)


# ── SKILL TREE SCENE ──────────────────────────────────────────────────────────
class SkillTreeScene(Scene):
    SCROLL_SPEED = 20
    MAX_SCROLL_X = SX * 3 + 130
    MAX_SCROLL_Y = int(SY * 6.4) + 90

    def __init__(self, game: Game, pause_menu):
        super().__init__(game)
        self.pause_menu = pause_menu
        if not hasattr(game.player, "unlocked_skills"):
            game.player.unlocked_skills = {"root"}

        self._btn_font = pg.font.Font(None, 28)
        w, h = game.graphic2d_surf.get_size()
        self.cx, self.cy   = w // 2, h // 2
        self.skill_manager = build_skill_tree(self.cx, self.cy, game.graphic2d_surf)
        self.selected   = None
        self.node_rects = {}
        self.scroll_x   = 0
        self.scroll_y   = 0
        self._drag_origin       = None
        self._drag_scroll_start = None
        self._font_hud     = pg.font.Font(None, 26)
        self._font_label   = pg.font.Font(None, 30)
        self._font_tooltip = pg.font.Font(None, 23)
        self._btn_back   = pg.Rect(0, 0, 160, 44)
        self._btn_center = pg.Rect(0, 0, 160, 44)
        self._reposition_buttons(w, h)

    def _reposition_buttons(self, w, h):
        self._btn_back.center   = (w // 2 - 100, h - 38)
        self._btn_center.center = (w // 2 + 100, h - 38)

    def _draw_buttons(self, surf):
        mouse = pg.mouse.get_pos()
        for rect, label in ((self._btn_back, "GO BACK"), (self._btn_center, "CENTER VIEW")):
            hovered = rect.collidepoint(mouse)
            pg.draw.rect(surf, (80, 80, 95) if hovered else (45, 45, 58), rect, border_radius=8)
            pg.draw.rect(surf, (160, 160, 180), rect, 2, border_radius=8)
            txt = self._btn_font.render(label, True, (220, 220, 230))
            surf.blit(txt, txt.get_rect(center=rect.center))

    def go_back(self):
        self.game.change_scene(self.pause_menu)

    def center_view(self):
        self.scroll_x = self.scroll_y = 0

    def _clamp(self):
        self.scroll_x = max(-self.MAX_SCROLL_X, min(self.MAX_SCROLL_X, self.scroll_x))
        self.scroll_y = max(-self.MAX_SCROLL_Y, min(self.MAX_SCROLL_Y, self.scroll_y))

    def handle_event(self, event):
        if event.type == pg.KEYDOWN:
            k = event.key
            if   k == pg.K_ESCAPE: self.go_back()
            elif k == pg.K_r:      self.center_view()
            self._clamp()

        elif event.type == pg.MOUSEWHEEL:
            if pg.key.get_mods() & pg.KMOD_SHIFT:
                self.scroll_x += event.y * self.SCROLL_SPEED
            else:
                self.scroll_y += event.y * self.SCROLL_SPEED
            self._clamp()

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._btn_back.collidepoint(event.pos):
                    self.go_back()
                elif self._btn_center.collidepoint(event.pos):
                    self.center_view()
                elif self.selected:
                    self.skill_manager.try_buy(self.selected, self.game.player,
                                               self.game.player.unlocked_skills)
            elif event.button == 2:
                self._drag_origin       = event.pos
                self._drag_scroll_start = (self.scroll_x, self.scroll_y)

        elif event.type == pg.MOUSEBUTTONUP:
            if event.button == 2:
                self._drag_origin = None

        elif event.type == pg.MOUSEMOTION:
            if self._drag_origin:
                dx = event.pos[0] - self._drag_origin[0]
                dy = event.pos[1] - self._drag_origin[1]
                if self._drag_scroll_start is not None:
                    self.scroll_x = self._drag_scroll_start[0] + dx
                    self.scroll_y = self._drag_scroll_start[1] + dy
                self._clamp()
            self.selected = None
            for name, rect in self.node_rects.items():
                if rect.collidepoint(event.pos):
                    self.selected = self.skill_manager.get_by_name(name)
                    break

    def update(self):
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:  self.scroll_x += self.SCROLL_SPEED
        if keys[pg.K_RIGHT]: self.scroll_x -= self.SCROLL_SPEED
        if keys[pg.K_UP]:    self.scroll_y += self.SCROLL_SPEED
        if keys[pg.K_DOWN]:  self.scroll_y -= self.SCROLL_SPEED
        self._clamp()
        self.skill_manager.update_states(self.game.player.score,
                                         self.game.player.unlocked_skills)

    def _draw_labels(self, surf):
        for text, ox, oy, color in BRANCH_LABELS:
            x = self.cx + ox + self.scroll_x
            y = self.cy + oy + self.scroll_y
            s = self._font_label.render(text, True, color)
            surf.blit(s, s.get_rect(center=(x, y)))

    def _draw_tooltip(self, surf):
        sk = self.selected
        if sk is None:
            return
        lines = [
            (sk.display_name,           BRANCH_COLORS[sk.branch_name]),
            (sk.description,            (200, 200, 210)),
            (f"Cost: {sk.cost} pts",    (180, 180, 190)),
            (f"Status: {sk.state.upper()}", (160, 160, 170)),
        ]
        if sk.prereqs:
            lines.append((f"Needs: {', '.join(sk.prereqs)}", (140, 140, 150)))
        pad, lh, bw = 10, 22, 270
        bh = len(lines) * lh + pad * 2
        mx, my = pg.mouse.get_pos()
        bx = min(mx + 16, surf.get_width()  - bw - 4)
        by = min(my + 16, surf.get_height() - bh - 4)
        bg = pg.Surface((bw, bh), pg.SRCALPHA)
        bg.fill((12, 12, 22, 225))
        surf.blit(bg, (bx, by))
        pg.draw.rect(surf, BRANCH_COLORS[sk.branch_name], (bx, by, bw, bh), 1, border_radius=6)
        for i, (line, color) in enumerate(lines):
            surf.blit(self._font_tooltip.render(line, True, color),
                      (bx + pad, by + pad + i * lh))

    def _draw_hud(self, surf):
        hints = [
            f"Score: {self.game.player.score} pts",
            "Gold border = buyable  |  Click to unlock",
            "Scroll: Wheel / Arrows  |  MMB drag  |  R = recenter",
        ]
        for i, h in enumerate(hints):
            surf.blit(self._font_hud.render(h, True, (150, 150, 170)), (12, 10 + i * 22))

    def render(self):
        surf = self.game.graphic2d_surf
        surf.fill((16, 18, 28))
        self._draw_labels(surf)
        self.node_rects = self.skill_manager.draw_all(self.selected,
                                                      self.scroll_x, self.scroll_y)
        self._draw_tooltip(surf)
        self._draw_hud(surf)
        self._draw_buttons(surf)
        self.game.graphic3d.render_2d_surf(surf)

    def resize(self, width, height):
        self.pause_menu.resize(width, height)
        self.cx, self.cy = width // 2, height // 2
        self.skill_manager.update_positions(self.cx, self.cy)
        self.skill_manager.change_surface(self.game.graphic2d_surf)
        self._reposition_buttons(width, height)