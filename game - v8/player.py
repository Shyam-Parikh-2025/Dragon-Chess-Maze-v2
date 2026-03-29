import pygame as pg
import numpy as np
import math

class Waypoint:
    """A named map marker.  label is a single display char: 'H', 'P', '1', '2' …"""
    def __init__(self, label: str, grid_r: int, grid_c: int):
        self.label  = label
        self.grid_r = grid_r
        self.grid_c = grid_c

class Player:
    def __init__(self, start_pos, surface=None, radius=0.3):
        self.pos = np.array(start_pos, dtype=np.float32)
        self.playing_chess = False
        self.speed = 0.1
        self.radius = radius
        self.dragons_beaten = 0

        self.lives = 3
        self.score = 10000000
        
        self.can_move = True
        self.angle_x = 0.0
        self.angle_y = 0.0
        self.mouse_sensitivity = 0.002
        
        self.chance_of_chess = 0.5
        self.chess_difficulty, self.fps_difficulty = 0, 0
        self.time_limit_of_AI = 0 
        self.time_limit_of_fps = 0 
        self.fps_block_speed_multiplier = 1.0
        self.fps_block_size_multiplier = 1.0

        self.vision_range = 5
        self.minimap_radius_bonus = 1.0
        self.unlocked_skills = {"root"}
        # skill flags — checked by game logic when relevant
        # ── Sentinel (Chess) ──────────────────────────
        self.pawn_shield     = False   # +1 pawn at start
        self.royal_guard     = False   # pawn → Queen
        self.ai_fatigue      = False   # AI depth -2 per 5 moves
        self.dragons_blunder = False   # AI picks 3rd best move
        self.blitz_specialist= False   # win <20 moves = 2× pts
        self.berserker_king  = False   # King also moves as Knight
 
        # ── Guardian (Defense) ────────────────────────
        self.peace_treaty    = False   # stalemates safe
        self.soft_landing    = False   # lose → 5 tiles from portal
        self.second_wind     = False   # revive once at 0 lives
        self._second_wind_used = False # internal — resets each run
        self.kings_ransom    = False   # spend 500 pts to survive
 
        # ── Explorer (Utility) ────────────────────────
        self.speedster       = False   # Shift = 2× speed
        self.extra_spoils    = False   # +25% battle score
 
        # ── Seer (Navigation) ─────────────────────────
        self.beacon           = False   # unlocks waypoint system
        self.home_beacon      = False   # H key → home waypoint
        self.portal_beacon    = False   # P key → nearest portal waypoint
        self.multi_beacon     = False   # raises max_waypoints to 3
        self.boss_tracker     = False   # boss dot after 2 kills
        self.clarity          = False   # no fog
        self.gps              = False   # full maze on minimap
        self.warp             = False   # teleport to boss once
        self.teleport_to_end_available = True

        self.portal_tower = False
 
        # Waypoints dict: label → Waypoint  (e.g. 'H', 'P', '1', '2', '3')
        self.waypoints     = {}
        self.max_waypoints = 1      # raised by multi_beacon (→3)

    def set_named_waypoint(self, label: str, grid_r: int, grid_c: int):
        if label in self.waypoints:
            del self.waypoints[label]
        else:
            self.waypoints[label] = Waypoint(label, grid_r, grid_c)

    def place_custom_waypoint(self, grid_r: int, grid_c: int):
        labels = [str(i) for i in range(1, self.max_waypoints + 1)]
        for lbl in labels:
            if lbl in self.waypoints:
                wp = self.waypoints[lbl]
                if wp.grid_r == grid_r and wp.grid_c == grid_c:
                    del self.waypoints[lbl]
                    return
        
        for lbl in labels:
            if lbl not in self.waypoints:
                self.waypoints[lbl] = Waypoint(lbl, grid_r, grid_c)
                return
        
        del self.waypoints[labels[0]]
        self.waypoints[labels[0]] = Waypoint(labels[0], grid_r, grid_c)
    
    def nearest_portal(self, grid) -> tuple | None:
        portals = np.argwhere(grid == 3)
        if len(portals) == 0: return None

        px, py = float(self.pos[0]), float(self.pos[1])
        best_d, best_r, best_c  = float('inf'), None, None

        for pos in portals:
            r, c = int(pos[0]), int(pos[1])
            d = math.hypot(c - px, r - py)
            if d < best_d:
                best_d, best_r, best_c = d, r, c
        return(best_r, best_c) if best_r is not None else None


        
    def angle_mouse(self):
        x, y = pg.mouse.get_rel()
        self.angle_x += x * self.mouse_sensitivity
        self.angle_y -= y * self.mouse_sensitivity
        self.angle_y = np.clip(self.angle_y, -np.pi / 2, np.pi / 2)

    def update(self, keys, grid, delta_time = 0.016):
        self.angle_mouse()
        sin_a = np.sin(self.angle_x)
        cos_a = np.cos(self.angle_x)

        speed = self.speed
        if self.speedster and keys[pg.K_LSHIFT]:
            speed = speed * 2
        actual_speed = (speed * 60.0) * delta_time

        delta_x = 0.0
        delta_z = 0.0
        if self.can_move:
            if keys[pg.K_w] or keys[pg.K_UP]:
                delta_x += actual_speed * cos_a
                delta_z += actual_speed * sin_a
            if keys[pg.K_s] or keys[pg.K_DOWN]:
                delta_x -= actual_speed * cos_a
                delta_z -= actual_speed * sin_a
            if keys[pg.K_a] or keys[pg.K_LEFT]:
                delta_x += actual_speed * sin_a
                delta_z -= actual_speed * cos_a
            if keys[pg.K_d] or keys[pg.K_RIGHT]:
                delta_x -= actual_speed * sin_a
                delta_z += actual_speed * cos_a

            if delta_x != 0.0 and delta_z != 0.0:
                length = np.hypot(delta_x, delta_z)
                delta_x = delta_x / length
                delta_z = delta_z / length
                delta_x *= actual_speed
                delta_z *= actual_speed

        self.collision_checker(delta_x, delta_z, grid)

    def collision_checker(self, dx, dz, grid):
        """"""
        rows, cols = grid.shape

        to_be_x = self.pos[0] + dx
        n_x = int(np.clip(to_be_x + np.sign(dx) * self.radius, 0, cols - 1))
        n_y = int(np.clip(self.pos[1], 0, rows - 1))

        if grid[n_y, n_x] != 1:
            self.pos[0] = to_be_x

        to_be_z = self.pos[1] + dz
        n_x = int(np.clip(self.pos[0], 0, cols - 1))
        n_y = int(np.clip(to_be_z + np.sign(dz) * self.radius, 0, rows - 1))

        if grid[n_y, n_x] != 1:
            self.pos[1] = to_be_z

    def check_teleports(self, grid, portal_dict):
        rows, cols = grid.shape
        r = int(np.clip(self.pos[1], 0, rows - 1))
        c = int(np.clip(self.pos[0], 0, cols - 1))

        if grid[r, c] == 3:
            self.speed = 0
            self.playing_chess = True
            pg.mouse.get_rel()