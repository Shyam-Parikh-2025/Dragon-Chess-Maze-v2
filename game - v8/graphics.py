import moderngl as mgl
import numpy as np, math
import pygame as pg
from pyrr import matrix44
from shaders.shaders_3D import VERTEX_SHADER_3D, FRAGMENT_SHADER_3D
from shaders.shaders_2D import VERTEX_SHADER_2D, FRAGMENT_SHADER_2D
import constants
from player import Player
import os
 
 
class Graphics3d:
    def __init__(self, screen):
        self.ctx = mgl.create_context()
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.disable(mgl.CULL_FACE)
        self.ctx.enable(mgl.BLEND)
 
        self.prog = self.ctx.program(
            vertex_shader=VERTEX_SHADER_3D,
            fragment_shader=FRAGMENT_SHADER_3D
        )
 
        self.vbo           = self.ctx.buffer(self._cube_data())
        self.elongated_vbo = self.ctx.buffer(self._laser_data())
 
        self.vao           = self.ctx.simple_vertex_array(self.prog, self.vbo, "in_pos")
        self.elongated_vao = self.ctx.simple_vertex_array(self.prog, self.elongated_vbo, 'in_pos')
 
        aspect_ratio_screen = screen.get_width() / screen.get_height()
        self.projection = matrix44.create_perspective_projection_matrix(
            90.0, aspect_ratio_screen, 0.1, 100.0)
        self.prog["m_proj"].write(self.projection.astype("float32"))
 
        self.prog_2d = self.ctx.program(
            vertex_shader=VERTEX_SHADER_2D,
            fragment_shader=FRAGMENT_SHADER_2D
        )
        self.prog_2d['u_texture'].value = 0
        self.quad_buffer = self.ctx.buffer(np.array([
           -1,  1,    0, 0,
           -1, -1,    0, 1,
            1,  1,    1, 0,
            1, -1,    1, 1,
        ], dtype='float32'))
        self.vao_2d = self.ctx.simple_vertex_array(
            self.prog_2d, self.quad_buffer, "in_pos", "in_texcoord")
 
    def _cube_data(self):
        return np.array([
            -0.5, -0.5, -0.5,  0.5, -0.5, -0.5,  0.5,  0.5, -0.5,
             0.5,  0.5, -0.5, -0.5,  0.5, -0.5, -0.5, -0.5, -0.5,
            -0.5, -0.5,  0.5,  0.5, -0.5,  0.5,  0.5,  0.5,  0.5,
             0.5,  0.5,  0.5, -0.5,  0.5,  0.5, -0.5, -0.5,  0.5,
            -0.5,  0.5,  0.5, -0.5,  0.5, -0.5, -0.5, -0.5, -0.5,
            -0.5, -0.5, -0.5, -0.5, -0.5,  0.5, -0.5,  0.5,  0.5,
             0.5,  0.5,  0.5,  0.5,  0.5, -0.5,  0.5, -0.5, -0.5,
             0.5, -0.5, -0.5,  0.5, -0.5,  0.5,  0.5,  0.5,  0.5,
            -0.5, -0.5, -0.5,  0.5, -0.5, -0.5,  0.5, -0.5,  0.5,
             0.5, -0.5,  0.5, -0.5, -0.5,  0.5, -0.5, -0.5, -0.5,
            -0.5,  0.5, -0.5,  0.5,  0.5, -0.5,  0.5,  0.5,  0.5,
             0.5,  0.5,  0.5, -0.5,  0.5,  0.5, -0.5,  0.5, -0.5,
        ], dtype="float32")
 
    def _elongated_cube_data(self):
        return np.array([
            -0.5, -0.5, -0.5,  0.5, -0.5, -0.5,  0.5,  1.5, -0.5,
             0.5,  1.5, -0.5, -0.5,  1.5, -0.5, -0.5, -0.5, -0.5,
            -0.5, -0.5,  0.5,  0.5, -0.5,  0.5,  0.5,  1.5,  0.5,
             0.5,  1.5,  0.5, -0.5,  1.5,  0.5, -0.5, -0.5,  0.5,
            -0.5,  1.5,  0.5, -0.5,  1.5, -0.5, -0.5, -0.5, -0.5,
            -0.5, -0.5, -0.5, -0.5, -0.5,  0.5, -0.5,  1.5,  0.5,
             0.5,  1.5,  0.5,  0.5,  1.5, -0.5,  0.5, -0.5, -0.5,
             0.5, -0.5, -0.5,  0.5, -0.5,  0.5,  0.5,  1.5,  0.5,
            -0.5, -0.5, -0.5,  0.5, -0.5, -0.5,  0.5, -0.5,  0.5,
             0.5, -0.5,  0.5, -0.5, -0.5,  0.5, -0.5, -0.5, -0.5,
            -0.5,  1.5, -0.5,  0.5,  1.5, -0.5,  0.5,  1.5,  0.5,
             0.5,  1.5,  0.5, -0.5,  1.5,  0.5, -0.5,  1.5, -0.5,
        ], dtype="float32")
    
    def _laser_data(self):
        vertices = np.array([
            -0.1, -0.5, -0.1,  0.1, -0.5, -0.1,  0.1,  8.5, -0.1,
             0.1,  8.5, -0.1, -0.1,  8.5, -0.1, -0.1, -0.5, -0.1,
            -0.1, -0.5,  0.1,  0.1, -0.5,  0.1,  0.1,  8.5,  0.1,
             0.1,  8.5,  0.1, -0.1,  8.5,  0.1, -0.1, -0.5,  0.1,
            -0.1,  8.5,  0.1, -0.1,  8.5, -0.1, -0.1, -0.5, -0.1,
            -0.1, -0.5, -0.1, -0.1, -0.5,  0.1, -0.1,  8.5,  0.1,
             0.1,  8.5,  0.1,  0.1,  8.5, -0.1,  0.1, -0.5, -0.1,
             0.1, -0.5, -0.1,  0.1, -0.5,  0.1,  0.1,  8.5,  0.1,
            -0.1, -0.5, -0.1,  0.1, -0.5, -0.1,  0.1, -0.5,  0.1,
             0.1, -0.5,  0.1, -0.1, -0.5,  0.1, -0.1, -0.5, -0.1,
            -0.1,  8.5, -0.1,  0.1,  8.5, -0.1,  0.1,  8.5,  0.1,
             0.1,  8.5,  0.1, -0.1,  8.5,  0.1, -0.1,  8.5, -0.1,
        ], dtype="float32")
        return vertices
    
    def update_view(self, player):
        cam     = np.array([player.pos[0], 0.5, player.pos[1]], dtype="float32")
        dir_cam = np.array([np.cos(player.angle_x), 0.0, np.sin(player.angle_x)], dtype="float32")
        up_vec  = np.array([0.0, 1.0, 0.0], dtype="float32")
        view    = matrix44.create_look_at(cam, cam + dir_cam, up_vec)
        self.prog["m_view"].write(view.astype("float32"))
 
    def update_projection(self, width, height):
        aspect = width / height
        self.projection = matrix44.create_perspective_projection_matrix(
            90.0, aspect, 0.1, 100.0)
        self.prog['m_proj'].write(self.projection.astype('float32'))
 
    def render_maze(self, grid, wall_color, portal_color, player: Player):
        self.ctx.clear(0.1, 0.1, 0.1)
        self.ctx.enable(mgl.DEPTH_TEST)
        self.ctx.disable(mgl.CULL_FACE)
        self.prog["m_proj"].write(self.projection.astype("float32"))
 
        clarity   = player.clarity
        portal_on = player.portal_tower
 
        # Adjust this to change fog intensity:
        #   1.5 = gentle (original)
        #   2.0 = noticeably darker at render edge
        #   2.5 = dramatic, very dark edges
        FOG_EXPONENT = 2.0
 
        max_dist = 15.0 if clarity else 12.0
 
        rows, cols = grid.shape
        for r in range(rows):
            for c in range(cols):
                val = grid[r, c]
                if val == 0 or val == 2:
                    continue
 
                dx   = player.pos[0] - (c + 0.5)
                dz   = player.pos[1] - (r + 0.5)
                dist = math.hypot(dx, dz)
 
                portal_enlarge = (portal_on and val == 3 and dist < 10.0)
 
                if dist >= max_dist and not portal_enlarge:
                    continue
 
                translation_vec = np.array([c + 0.5, 0.5, r + 0.5], dtype="float32")
                model = matrix44.create_from_translation(translation_vec)
                self.prog["m_model"].write(model.astype("float32"))
 
                dimer = max(0.0, 1.0 - (dist / max_dist)) ** FOG_EXPONENT
 
                if   val == 1: r_c, g_c, b_c = wall_color
                elif val == 3: r_c, g_c, b_c = portal_color
                elif val == 4: r_c, g_c, b_c = 1.0, 0.0, 0.0
                else:          r_c, g_c, b_c = 0.5, 0.5, 0.5
 
                self.prog["u_color"].value = (r_c * dimer, g_c * dimer, b_c * dimer)
 
                if portal_enlarge:
                    self.elongated_vao.render(mgl.TRIANGLES)
                    self.elongated_vao.render(mgl.LINE_LOOP)
                self.vao.render(mgl.TRIANGLES)
                self.vao.render(mgl.LINE_LOOP)
 
    def render_2d_surf(self, surface):
        rgba    = pg.image.tobytes(surface, 'RGBA', False)
        texture = self.ctx.texture(surface.get_size(), 4, data=rgba)
        self.ctx.enable(mgl.BLEND)
        self.ctx.disable(mgl.DEPTH_TEST)
        self.ctx.blend_func = mgl.SRC_ALPHA, mgl.ONE_MINUS_SRC_ALPHA
        texture.use(0)
        self.vao_2d.render(mgl.TRIANGLE_STRIP)
        self.ctx.disable(mgl.BLEND)
        self.ctx.enable(mgl.DEPTH_TEST)
        texture.release()
 
class Graphics2d:
    def __init__(self, surface, player, txt_size=36, big_txt_size=72):
        self.surface    = surface
        self.font       = pg.font.Font(None, txt_size)
        self.large_font = pg.font.Font(None, big_txt_size)
        self.player     = player
        self.images     = {}
        self.load_dragon_imgs()
        self.minimap_radius = 90
        self.wp_font = pg.font.Font(None, 17)
 
    def load_dragon_imgs(self):
        _, height = self.surface.get_size()
        sqsize = height // 8
        try:
            for drag in ['dragon_normal.png', 'dragon_thinking.png']:
                base_path    = os.path.dirname(__file__)
                image_folder = os.path.join(base_path, "images")
                full_path    = os.path.join(image_folder, drag)
                img = pg.image.load(full_path).convert()
                img.set_colorkey((255, 0, 255))
                img = pg.transform.smoothscale(img, (sqsize * 2, sqsize * 2))
                self.images[drag] = img
        except:
            print("Dragon images file not found, shifting to writing")
 
    def draw_chess_board(self, chess_engine, selected_sq=None,
                         hover_sq=None, valid_moves=None):
        width, height = self.surface.get_size()
        sqsize   = min(width - 200, height) // 8
        x_offset = ((width - 200) - (sqsize * 8)) // 2
        y_offset = (height - (sqsize * 8)) // 2
 
        if chess_engine is None or chess_engine.board is None:
            return
 
        board = chess_engine.board
        for sq in range(64):
            r, c     = sq // 8, sq % 8
            sq_color = constants.color["light"] if (r + c) % 2 == 0 else constants.color["dark"]
            pg.draw.rect(self.surface, sq_color,
                (x_offset + c * sqsize, y_offset + r * sqsize, sqsize, sqsize))
 
            if hover_sq == sq:
                surf = pg.Surface((sqsize, sqsize))
                surf.set_alpha(100)
                surf.fill((100, 200, 255))
                self.surface.blit(surf, (x_offset + c * sqsize, y_offset + r * sqsize))
 
            if selected_sq == sq:
                surf = pg.Surface((sqsize, sqsize))
                surf.set_alpha(100)
                surf.fill((255, 255, 0))
                self.surface.blit(surf, (x_offset + c * sqsize, y_offset + r * sqsize))
 
            if valid_moves and sq in valid_moves:
                center     = (x_offset + c * sqsize + sqsize // 2,
                              y_offset + r * sqsize + sqsize // 2)
                targ_piece = board[sq]
                rect       = pg.Rect(center[0] - sqsize // 2, center[1] - sqsize // 2,
                                     sqsize, sqsize)
                color      = (100, 100, 100) if targ_piece == 0 else (200, 50, 50)
                pg.draw.rect(self.surface, color, rect, 5)
 
            piece = chess_engine.board[sq]
            if piece != 0:
                piece_type_val = piece & 7
                type_names     = (None, 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king')
                type_piece     = type_names[piece_type_val]
                p_color        = 'black' if bool(piece & 8) else 'white'
                key            = f"{p_color}_{type_piece}"
                if key in chess_engine.org_imgs:
                    if key not in chess_engine.images or \
                            chess_engine.images[key].get_width() != sqsize:
                        chess_engine.images[key] = pg.transform.smoothscale(
                            chess_engine.org_imgs[key], (sqsize, sqsize))
                    img      = chess_engine.images[key]
                    img_rect = img.get_rect(
                        center=(x_offset + c * sqsize + sqsize // 2,
                                y_offset + r * sqsize + sqsize // 2))
                    self.surface.blit(img, img_rect)
                else:
                    rgb      = (255, 255, 255) if p_color == 'white' else (0, 0, 0)
                    bg       = (255, 255, 255) if p_color != 'white' else (0, 0, 0)
                    txt_surf = self.font.render(f"{type_piece}", True, rgb, bgcolor=bg)
                    txt_rect = txt_surf.get_rect(
                        center=(x_offset + c * sqsize + sqsize // 2,
                                y_offset + r * sqsize + sqsize // 2))
                    self.surface.blit(txt_surf, txt_rect)
 
    def draw_fps(self, ai_thinking=False, show_drag=False):
        width, height  = self.surface.get_size()
        player         = self.player
        sidebar_width  = 200
        sidebar_x      = width - sidebar_width
        pg.draw.rect(self.surface, (40, 40, 50), (sidebar_x, 0, sidebar_width, height))
        pg.draw.line(self.surface, (255, 255, 255), (sidebar_x, 0), (sidebar_x, height), 3)
        text_x     = sidebar_x + 30
        lives_txt  = self.font.render(f"Lives: {player.lives}",           True, (255, 50,  50))
        score_txt  = self.font.render(f"Score: {player.score}",           True, (255, 255, 255))
        dragon_txt = self.font.render(f"Dragons: {player.dragons_beaten}", True, (255, 215,  0))
        self.surface.blit(lives_txt,  (text_x, 50))
        self.surface.blit(score_txt,  (text_x, 100))
        self.surface.blit(dragon_txt, (text_x, 150))
        if show_drag:
            drag_mode = 'thinking' if ai_thinking else 'normal'
            key       = f'dragon_{drag_mode}.png'
            center_y  = height // 2
            if key in self.images:
                img      = self.images[key]
                img_rect = img.get_rect(center=(sidebar_x + sidebar_width // 2, center_y))
                self.surface.blit(img, img_rect)
            else:
                fallback = self.font.render(f'[{drag_mode.upper()}]', True, (255, 0, 255))
                self.surface.blit(fallback,
                    fallback.get_rect(center=(sidebar_x + sidebar_width // 2, center_y)))
 
    def start_2d(self):
        self.surface.fill((0, 0, 0, 0))
 
    def draw_minimap(self, grid, player, wall_color: tuple, portal_color: tuple):
        width, height = self.surface.get_size()
        padding       = 10
        radius_bonus  = player.minimap_radius_bonus
        effective_r   = int(self.minimap_radius * radius_bonus)
        center_x      = width - effective_r - padding
        center_y      = height // 2
        vision_range  = 15 if player.gps else player.vision_range
 
        pg.draw.circle(self.surface, (30, 30, 40, 200), (center_x, center_y), effective_r)
 
        surf_size    = int(effective_r * 3)
        minimap_surf = pg.Surface((surf_size, surf_size), pg.SRCALPHA)
        map_center   = surf_size // 2
        scale        = effective_r / vision_range
        px, py       = float(player.pos[0]), float(player.pos[1])
 
        start_r = max(0, int(py - vision_range - 1))
        end_r   = min(grid.shape[0], int(py + vision_range + 1))
        start_c = max(0, int(px - vision_range - 1))
        end_c   = min(grid.shape[1], int(px + vision_range + 1))
 
        wr_c, wg_c, wb_c = wall_color
        pr_c, pg_c, pb_c = portal_color
        WALL_COLOR    = (wr_c * 255, wg_c * 255, wb_c * 255, 255)
        PORTAL_COLOR  = (pr_c * 255, pg_c * 255, pb_c * 255, 255)
        EMPTY_COLOR   = (0,   0,   0,   255)
        START_COLOR   = (50,  255, 50,  255)
        BOSS_COLOR    = (150, 0,   150, 255)
        DEFAULT_COLOR = (40,  40,  50,  255)
 
        for r in range(start_r, end_r):
            for c in range(start_c, end_c):
                dx, dy = c - px, r - py
                if math.hypot(dx, dy) <= vision_range:
                    draw_x = int(map_center + dx * scale)
                    draw_y = int(map_center + dy * scale)
                    size   = int(scale + 1)
                    val    = grid[r, c]
                    if   val == 1: color = WALL_COLOR
                    elif val == 0: color = EMPTY_COLOR
                    elif val == 3: color = PORTAL_COLOR
                    elif val == 2: color = START_COLOR
                    elif val == 4: color = BOSS_COLOR
                    else:          color = DEFAULT_COLOR
                    pg.draw.rect(minimap_surf, color, pg.Rect(draw_x, draw_y, size, size))
 
        # waypoints: labeled dots inside map, arrows on edge when off-screen
        if player.beacon and player.waypoints:
            max_r_draw = effective_r - 8
            for wp in player.waypoints.values():
                dx_wp   = (wp.grid_c - px) * scale
                dy_wp   = (wp.grid_r - py) * scale
                dist_px = math.hypot(dx_wp, dy_wp)
                if dist_px <= max_r_draw:
                    draw_x = int(map_center + dx_wp)
                    draw_y = int(map_center + dy_wp)
                    pg.draw.circle(minimap_surf, (255, 215, 0, 230), (draw_x, draw_y), 7)
                    pg.draw.circle(minimap_surf, (0,   0,   0, 200), (draw_x, draw_y), 7, 1)
                    lbl = self.wp_font.render(wp.label, True, (10, 10, 10))
                    minimap_surf.blit(lbl, (draw_x - lbl.get_width()  // 2,
                                           draw_y - lbl.get_height() // 2))
                else:
                    if dist_px == 0:
                        continue
                    nx, ny  = dx_wp / dist_px, dy_wp / dist_px
                    tip_x   = int(map_center + nx * max_r_draw)
                    tip_y   = int(map_center + ny * max_r_draw)
                    px_p, py_p = -ny, nx
                    base_x  = int(tip_x - nx * 9)
                    base_y  = int(tip_y - ny * 9)
                    left_x  = int(base_x + px_p * 5)
                    left_y  = int(base_y + py_p * 5)
                    right_x = int(base_x - px_p * 5)
                    right_y = int(base_y - py_p * 5)
                    pg.draw.polygon(minimap_surf, (255, 215, 0, 220),
                                    [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)])
                    pg.draw.polygon(minimap_surf, (0, 0, 0, 160),
                                    [(tip_x, tip_y), (left_x, left_y), (right_x, right_y)], 1)
                    lbl = self.wp_font.render(wp.label, True, (255, 255, 255))
                    minimap_surf.blit(lbl, (int(tip_x - nx * 12) - lbl.get_width()  // 2,
                                           int(tip_y - ny * 12) - lbl.get_height() // 2))
 
        # boss tracker
        if player.boss_tracker and player.dragons_beaten >= 2:
            boss_positions = np.argwhere(grid == 4)
            for pos in boss_positions:
                br, bc = pos
                dx_b   = (bc - px) * scale
                dy_b   = (br - py) * scale
                if math.hypot(bc - px, br - py) <= vision_range * 2:
                    pg.draw.circle(minimap_surf, (200, 0,   200, 255),
                                   (int(map_center + dx_b), int(map_center + dy_b)), 6)
                    pg.draw.circle(minimap_surf, (255, 255, 255, 255),
                                   (int(map_center + dx_b), int(map_center + dy_b)), 3)
 
        angle_deg    = math.degrees(player.angle_x) + 90
        rotated_surf = pg.transform.rotate(minimap_surf, angle_deg)
        final_surf   = pg.Surface((effective_r * 2, effective_r * 2), pg.SRCALPHA)
        rotated_rect = rotated_surf.get_rect(center=(effective_r, effective_r))
        final_surf.blit(rotated_surf, rotated_rect.topleft)
 
        p_center = (effective_r, effective_r)
        pg.draw.circle(final_surf, (0, 255, 255), p_center, 4)
 
        mask_surf = pg.Surface((effective_r * 2, effective_r * 2), pg.SRCALPHA)
        pg.draw.circle(mask_surf, (255, 255, 255, 255), p_center, effective_r)
        final_surf.blit(mask_surf, (0, 0), special_flags=pg.BLEND_RGBA_MIN)
 
        self.surface.blit(final_surf, (center_x - effective_r, center_y - effective_r))
        pg.draw.circle(self.surface, (200, 200, 200), (center_x, center_y), effective_r, 3)