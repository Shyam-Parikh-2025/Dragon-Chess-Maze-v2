import pygame as pg
import numpy as np
import math
import time
import random
import moderngl as mgl
 
from pyrr import matrix44
from scene import Scene
import constants
from menu_scenes import EndScreen

class Net:
    def __init__(self, start_pos, direction, difficulty: float=0.0):
        self.start_pos = np.array(start_pos, dtype=np.float32)
        self.pos = np.array(start_pos, dtype=np.float32)
        self.direction = direction
        self.difficulty = (1-difficulty)
        self.speed = 1.0 + (difficulty * 1)
        self.velocity = np.array(self.direction, dtype=np.float32) * self.speed
        self.gravity = 0.01
        self.active = True
        self.life_time = 150
        self.radius = 0.3
 
    def update(self):
        if self.active:
            self.velocity[1] -= 0.01
            self.pos += self.velocity
            distance = abs(np.linalg.norm(self.pos - self.start_pos))
            if (distance > 2000) or (self.life_time <= 0) or (self.pos[1] < -15.0):
                self.active=False
            self.life_time -= 1
   
    def check_collision(self, targets):
        
        hit_idxs = []
        target_found = False
        for i, target in enumerate(targets):
            if target.captured: continue
            half_width = target.width / 2
            half_z_depth = target.z_depth / 2

            min_x, max_x = target.pos[0] + target.hitbox_min[0], target.pos[0] + target.hitbox_max[0]
            min_y, max_y = target.pos[1] + target.hitbox_min[1], target.pos[1] + target.hitbox_max[1]
            min_z, max_z = target.pos[2] + target.hitbox_min[2], target.pos[2] + target.hitbox_max[2]

            if (
                min_x - self.radius <= self.pos[0] <= max_x + self.radius and
                min_y - self.radius <= self.pos[1] <= max_y + self.radius and
                min_z - self.radius <= self.pos[2] <= max_z + self.radius
               ):
                hit_idxs.append(i)
                target_found = True
        if target_found:
            return True, None, hit_idxs
        return False, None, None
 
class Target:
    def __init__(self, ctx, program, name, pos, hitbox_mul, color, fmt='3f', size=1.0, attribute_names=['in_pos'],  vbo=None):
        self.name = name
        self.max_hp = 3 if self.name == 'King' else (2 if self.name == 'Queen' else 1)
        self.hp = self.max_hp
        self.pos = np.array(pos, dtype='float32')
        self.hitbox_mul = hitbox_mul
        self.color = color
        self.captured = False
        self.program = program
        self.size = size
        self.vbo = vbo
        self.hitbox_min = self.hitbox_max = 0
        if self.vbo is None:
            vertices = np.array([
            -self.size, -self.size,  self.size,  self.size, -self.size,  self.size,  self.size,  self.size,  self.size, # Front
            -self.size, -self.size,  self.size,  self.size,  self.size,  self.size, -self.size,  self.size,  self.size,
            self.size, -self.size,  self.size,  self.size, -self.size, -self.size,  self.size,  self.size, -self.size, # Right
            self.size, -self.size,  self.size,  self.size,  self.size, -self.size,  self.size,  self.size,  self.size,
            self.size, -self.size, -self.size, -self.size, -self.size, -self.size, -self.size,  self.size, -self.size, # Back
            self.size, -self.size, -self.size, -self.size,  self.size, -self.size,  self.size,  self.size, -self.size,
            -self.size, -self.size, -self.size, -self.size, -self.size,  self.size, -self.size,  self.size,  self.size, # Left
            -self.size, -self.size, -self.size, -self.size,  self.size,  self.size, -self.size,  self.size, -self.size,
            -self.size,  self.size,  self.size,  self.size,  self.size,  self.size,  self.size,  self.size, -self.size, # Top
            -self.size,  self.size,  self.size,  self.size,  self.size, -self.size, -self.size,  self.size, -self.size,
            -self.size, -self.size, -self.size,  self.size, -self.size, -self.size,  self.size, -self.size,  self.size, # Bottom
            -self.size, -self.size, -self.size,  self.size, -self.size,  self.size, -self.size, -self.size,  self.size,
            ], dtype='float32')
        else:
            vertices = vbo.astype('float32') * 10.0 # type: ignore
        self.vbo = ctx.buffer(vertices)
        self.vao = ctx.vertex_array(program, [(self.vbo, fmt, *attribute_names)])

        self.hitbox_builder(vertices)
   
    def render(self):
        if not self.captured:
            scale_mat = matrix44.create_from_scale(
                np.array([self.size, self.size, self.size], dtype='float32')
            )
            trans_mat = matrix44.create_from_translation(self.pos)
            model = matrix44.multiply(scale_mat, trans_mat)
            self.program["m_model"].write(model.astype("float32"))
            self.program["u_color"].value = self.color
            self.vao.render()
    
    def hitbox_builder(self, vertices):
        vbo = np.array(vertices)
        if vbo is not None:
            shaped_vbo: np.ndarray = vbo.reshape(-1, 3)
            self.vbo_min = np.min(shaped_vbo, axis=0)
            self.vbo_max = np.max(shaped_vbo, axis=0)

            self.width = (self.vbo_max[0] - self.vbo_min[0])  * self.size
            self.height = (self.vbo_max[1] - self.vbo_min[1]) * self.size
            self.z_depth = (self.vbo_max[2] - self.vbo_min[2])* self.size
            
            self.hitbox_min, self.hitbox_max = self.vbo_min * self.size, self.vbo_max * self.size
            self.hitbox_center = ((self.vbo_max + self.vbo_min)/2) * self.size

        else:
            self.width = self.height = self.depth = self.size * 2
            self.hitbox_min = np.array([-self.size, 0.0, -self.size])
            self.hitbox_max = np.array([self.size, self.size * 2, self.size])
            self.hitbox_center = np.array([0.0, self.size, 0.0])

class TamingScene(Scene):
    def __init__(self, game, is_boss=False):
        WIDTH = constants.WIDTH
        HEIGHT = constants.HEIGHT
        super().__init__(game)
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)
        self.is_boss = is_boss
        
        self.time_limit = float(self.game.player.time_limit_of_fps) + 9.0 
        if not (self.time_limit > 0.0): self.time_limit = 20.0
       
        self.distance_extra_x = 1.0 if not is_boss else 2.0
        self.distance_extra_y = -1.0 if not is_boss else 2.0
        self.distance_extra_z = 1.0 if not is_boss else 2.0
 
        self.dragon_level = 1.0 if not is_boss else 1.5
        self.size = 0.90
        self.speed_mul = self.game.player.fps_block_speed_multiplier * self.dragon_level
       
        self.start_time = time.time()
        self.nets = []
        self.yaw = math.pi / 2.0
        self.pitch = 0.0
        self.camera_front = np.array([0.0, 0.0, 1.0], dtype='float32')
        self.mouse_sensitivity: float = 0.002
        self.targets: dict = {}
        self.over_processed: bool = False

        self.pieces_defeated: int = 0
 
        self.hitbox_show: bool = False
        self.hitbox_vbo = self.game.graphic3d.ctx.buffer(self.game.graphic3d._cube_data())
        self.hitbox_vao = self.game.graphic3d.ctx.simple_vertex_array(self.game.graphic3d.prog, self.hitbox_vbo, "in_pos")
 
        try:
            from vbo_folder.vbo import QUEEN_VBO, KING_VBO, ROOK_VBO
        except ImportError:
            print("VBOs not found.")
            ROOK_VBO, KING_VBO, QUEEN_VBO = None, None, None
 
        self.targets["Rook"]=Target(ctx=self.game.graphic3d.ctx,
                                program=self.game.graphic3d.prog,
                                name="Rook",
                                pos=[-5.0 + self.distance_extra_x, 0.0 + self.distance_extra_y, 20.0+self.distance_extra_z],
                                hitbox_mul=self.size,
                                color=(0.0, 0.5, 1.0),
                                fmt='3f',
                                size=self.size,
                                attribute_names=['in_pos'],
                                vbo=ROOK_VBO
                            )
 
        self.targets["Queen"] = Target(
                                ctx=self.game.graphic3d.ctx,
                                program=self.game.graphic3d.prog,
                                name="Queen",
                                pos=[5.0 + self.distance_extra_x, 2.0 + self.distance_extra_y, 25.0+self.distance_extra_z],
                                hitbox_mul=self.size,
                                color=(1.0, 0.0, 1.0),
                                fmt='3f',
                                size=self.size,
                                attribute_names=['in_pos'],
                                vbo=QUEEN_VBO
                            )
 
        self.targets["King"] = Target(
                                ctx=self.game.graphic3d.ctx,
                                program=self.game.graphic3d.prog,
                                name="King",
                                pos=[0.0 + self.distance_extra_x, 0.0 + self.distance_extra_y, 30.0+self.distance_extra_z],
                                hitbox_mul=self.size,
                                color=(1.0, 0.8, 0.0),
                                fmt='3f',
                                size=self.size,
                                attribute_names=['in_pos'],
                                vbo=KING_VBO
                            )
       
        self.update_cam()
        self.dir_target = 1

    def update_cam(self):
        x = math.cos(self.yaw) * math.cos(self.pitch)
        y = math.sin(self.pitch)
        z = math.sin(self.yaw) * math.cos(self.pitch)
        self.camera_front = np.array([x, y, z], dtype='float32')
        self.camera_front /= np.linalg.norm(self.camera_front)
        eye = np.array([0.0, 0.0, 0.0], dtype='float32')
        up = np.array([0.0, 1.0, 0.0], dtype='float32')
        self.view = matrix44.create_look_at(eye, eye + self.camera_front, up)
                                           
    def handle_event(self, event):
        if event.type == pg.MOUSEMOTION:
            dx, dy = event.rel
            self.yaw += dx * self.mouse_sensitivity
            self.pitch -= dy * self.mouse_sensitivity
            self.pitch = max(-math.pi/2 + 0.1, min(math.pi/2 - 0.1, self.pitch))

        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.shoot_net()
        elif event.type == pg.KEYDOWN:
            if event.key == pg.K_ESCAPE:
                pg.event.set_grab(not pg.event.get_grab())
                pg.mouse.set_visible(not pg.mouse.get_visible())
            if event.key == pg.K_q:
                self.finish_taming(victory=False, pieces_defeated=self.pieces_defeated)
            if (event.key == pg.K_F2) or (event.key == pg.K_h):
                self.hitbox_show = not self.hitbox_show
   
    def shoot_net(self):
        net = Net([0.0, 0.0, 0.0], self.camera_front.copy(), difficulty=self.game.player.fps_difficulty)
        self.nets.append(net)
   
    def update(self):
        self.update_cam()

        time_left = max(0, self.time_limit - (time.time() - self.start_time))
        theta = time.time() * (1 + self.dragon_level*self.speed_mul)
        if abs(time_left % 100.0) < 0.1:
            self.dir_target = random.choice([1,-1])*self.dir_target

        rook, queen, king = self.targets["Rook"], self.targets["Queen"], self.targets["King"]

        rook_radius = 12.0
        if not rook.captured:
            radius = rook_radius
            y_incr = random.choice([0, 0.1]) if random.random() < 0.1 else 0
            rook.pos = np.array([radius * math.cos(theta), # X
                                 -1.0 + (y_incr),           # Y
                                 radius * math.sin(theta)])# Z
        if not queen.captured:
            radius = rook_radius + 6.0
            queen.pos = np.array([radius * math.cos(theta * 1.5), # X
                                  1.0 + (0.3 * math.cos(theta * 1.8)),# Y
                                  radius * math.sin(theta)])      # Z
        if not king.captured:
            radius = rook_radius + 12.0
            king.pos = np.array([radius * math.cos(theta), # X
                                3.0 + (2.1 * math.cos(theta * 2.8)),# Y
                                radius * math.sin(theta)]) # Z
       
        for net in self.nets[:]:
            net.update()
            
            target_list = list(self.targets.values())
            hit_bool, hit_pos, hit_indices = net.check_collision(target_list)
 
            if hit_bool and net.active:
                net.active = False
                for idx in hit_indices:
                    target_obj = target_list[idx]
                    if not target_obj.captured:
                        target_obj.hp -= 1
                        self.pieces_defeated += 1
                        if target_obj.hp <= 0:
                            target_obj.captured = True
                            print(f"Captured the {target_obj.name}")
                        else:
                            health_percent = target_obj.hp / target_obj.max_hp
                            red = 0.19 + (health_percent * 0.81)
                            target_obj.color = (red, 0.0, 0.0)
                            target_obj.pos[1] += 1.0

            if not net.active or net.life_time <= 0:
                if net in self.nets:
                    self.nets.remove(net)
 
            all_captured = all(target.captured for target in self.targets.values())
            if all_captured:
                self.finish_taming(victory=True, pieces_defeated=self.pieces_defeated)
            elif time_left <= 0:
                self.finish_taming(victory=False, pieces_defeated=self.pieces_defeated)
 
    def finish_taming(self, victory, pieces_defeated):
        if self.over_processed: return
        for target in self.targets.values():
            target.vbo.release()
            target.vao.release()
        
        self.game.player.score += (pieces_defeated * (10*self.game.player.fps_difficulty))

        if victory:
            print("One Dragon Tamed!")
            self.game.player.dragons_beaten += 1
            self.game.player.score += (100 + (100 * self.game.player.fps_difficulty))
            if self.is_boss:
                    pg.event.set_grab(False)
                    pg.mouse.set_visible(True)
                    self.game.change_scene(EndScreen(self.game, victory=True))
                    return
            r, c = self.game.current_battle_pos                
            self.game.grid[r, c] = 0
        else:
            print("Time ran out! You lost a life.")
            self.game.player.lives -= 1
            if self.game.player.lives <= 0:
                pg.event.set_grab(False)
                pg.mouse.set_visible(True)
                self.game.change_scene(EndScreen(self.game, victory=False))
                return
            self.game.player.pos[0] = 2.0
            self.game.player.pos[1] = 2.0
        self.over_processed = True
        pg.event.set_grab(True)
        pg.mouse.set_visible(False)
        self.game.player.playing_chess = False
        if self.game.maze_scene is not None:
            self.game.change_scene(self.game.maze_scene)
 
    def render(self):
        game = self.game
        game.graphic3d.ctx.clear(0.05, 0.05, 0.1)
        game.graphic3d.ctx.enable(game.graphic3d.ctx.DEPTH_TEST)

        width, height = game.graphic2d_surf.get_size()
        aspect_ratio = width / max(1, height)
        projection = matrix44.create_perspective_projection_matrix(90.0, aspect_ratio, 0.1, 200.0)
        game.graphic3d.prog["m_proj"].write(projection.astype("float32"))
        game.graphic3d.prog["m_view"].write(self.view.astype("float32"))
        for name, target in self.targets.items():
            target.render()
       
        for net in self.nets[:]:
            model = matrix44.create_from_translation(net.pos)
            size = net.radius + abs((1 - self.game.player.fps_difficulty))
            scale = matrix44.create_from_scale(np.array([size, size, size], dtype=np.float32))
            final_model = matrix44.multiply(scale, model)
            game.graphic3d.prog["m_model"].write(final_model.astype("float32"))
            game.graphic3d.prog["u_color"].value = (0.0, 1.0, 1.0)
            game.graphic3d.vao.render()
        
        if self.hitbox_show:
            for target in self.targets.values():
                if target.captured: continue
                scale = matrix44.create_from_scale([
                 target.width,
                 target.height,
                 target.z_depth
                ])
                trans_mat = matrix44.create_from_translation(target.pos + target.hitbox_center)
                model = matrix44.multiply(scale, trans_mat)
                self.game.graphic3d.prog["m_model"].write(model.astype('float32'))
                self.game.graphic3d.prog["u_color"].value = (0.0, 1.0, 0.0)
                self.hitbox_vao.render(mode=mgl.LINE_LOOP)

        surf = game.graphic2d_surf
        surf.fill((0, 0, 0, 0))
        cx = width // 2
        cy = height // 2
        pg.draw.line(surf, (255, 50, 50), (cx - 15, cy), (cx + 15, cy), 2)
        pg.draw.line(surf, (255, 50, 50), (cx, cy - 15), (cx, cy + 15), 2)
       
        elapsed = time.time() - self.start_time
        time_left = max(0, self.time_limit - elapsed)
        font = pg.font.Font(None, 40)
        timer_txt = font.render(f"Time: {time_left:.1f}s", True, (255, 255, 255))
        surf.blit(timer_txt, (20, 20))
        y_offset = 70
 
        for name, target_obj in self.targets.items():
            color = (0, 255, 0) if target_obj.captured else (100, 100, 100)
            status_txt = font.render(name, True, color)
            surf.blit(status_txt, (20, y_offset))
            y_offset += 40
        game.graphic3d.render_2d_surf(surf)