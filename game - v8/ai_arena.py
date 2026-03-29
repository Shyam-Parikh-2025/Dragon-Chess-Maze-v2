import os
import sys
import time
import threading
import pygame as pg

# Change this to True to disable Numba's C-compilation.
DISABLE_JIT = False 
if DISABLE_JIT:
    os.environ['NUMBA_DISABLE_JIT'] = '1'
    print("WARNING: Numba JIT is DISABLED. Running in pure Python...")
else:
    print("Numba JIT is ENABLED. Running at maximum speed...")

from chess_engine import Chess, decode_move
from dragon import Dragon
import constants

class VisualArena:
    def __init__(self, ai_white, ai_black):
        pg.init()
        self.ai_white = ai_white
        self.ai_black = ai_black
        
        self.board_size = 800
        self.panel_width = 400
        self.screen = pg.display.set_mode((self.board_size + self.panel_width, self.board_size))
        pg.display.set_caption(f"AI Arena | JIT Enabled: {not DISABLE_JIT}")
        
        self.font = pg.font.Font(None, 36)
        self.large_font = pg.font.Font(None, 50)
        
        self.engine = Chess(load_graphic=True)
        self.engine.load_images()
        self.sq_size = self.board_size // 8
        
        self.move_history = []
        self.white_times = []
        self.black_times = []
        
        self.ai_thinking = False
        self.calculated_move = None
        self.game_over = False
        self.result_msg = ""

    def draw_board(self):
        colors = [(234, 251, 200), (119, 154, 88)] 
        for r in range(8):
            for c in range(8):
                color = colors[(r + c) % 2]
                rect = pg.Rect(c * self.sq_size, r * self.sq_size, self.sq_size, self.sq_size)
                pg.draw.rect(self.screen, color, rect)
                
                if self.move_history:
                    last_start, last_end, _ = decode_move(self.move_history[-1])
                    sq = r * 8 + c
                    if sq == last_start or sq == last_end:
                        highlight = pg.Surface((self.sq_size, self.sq_size))
                        highlight.set_alpha(100)
                        highlight.fill((255, 255, 0))
                        self.screen.blit(highlight, (c * self.sq_size, r * self.sq_size))

                piece = self.engine.board[r * 8 + c]
                if piece != 0:
                    p_type = piece & 7
                    is_black = bool(piece & 8)
                    color_str = 'black' if is_black else 'white'
                    type_names = (None, 'pawn', 'knight', 'bishop', 'rook', 'queen', 'king')
                    key = f"{color_str}_{type_names[p_type]}"
                    
                    if key in self.engine.org_imgs:
                        img = pg.transform.smoothscale(self.engine.org_imgs[key], (self.sq_size, self.sq_size))
                        self.screen.blit(img, rect)
                    else:
                        txt = self.font.render(type_names[p_type][0].upper(), True, (0,0,0) if not is_black else (255,255,255))
                        self.screen.blit(txt, txt.get_rect(center=rect.center))

    def draw_stats_panel(self):
        panel_rect = pg.Rect(self.board_size, 0, self.panel_width, self.board_size)
        pg.draw.rect(self.screen, (30, 30, 40), panel_rect)
        pg.draw.line(self.screen, (255, 255, 255), (self.board_size, 0), (self.board_size, self.board_size), 3)

        x_offset = self.board_size + 20
        
        jit_status = "DISABLED (Slow)" if DISABLE_JIT else "ENABLED (Fast)"
        color = (255, 50, 50) if DISABLE_JIT else (50, 255, 50)
        self.screen.blit(self.font.render(f"Numba JIT: {jit_status}", True, color), (x_offset, 20))
        
        current_move_num = (len(self.move_history) // 2) + 1
        
        self.screen.blit(self.large_font.render("Match Stats", True, (255, 215, 0)), (x_offset, 80))
        self.screen.blit(self.font.render(f"Current Move: {current_move_num}", True, (200, 200, 255)), (x_offset, 115))
        
        w_avg = sum(self.white_times) / len(self.white_times) if self.white_times else 0
        w_last = self.white_times[-1] if self.white_times else 0
        self.screen.blit(self.font.render(f"White: {self.ai_white.name}", True, (255, 255, 255)), (x_offset, 170))
        self.screen.blit(self.font.render(f"Last Move: {w_last:.3f}s", True, (200, 200, 200)), (x_offset, 210))
        self.screen.blit(self.font.render(f"Avg Time:  {w_avg:.3f}s", True, (200, 200, 200)), (x_offset, 250))

        b_avg = sum(self.black_times) / len(self.black_times) if self.black_times else 0
        b_last = self.black_times[-1] if self.black_times else 0
        self.screen.blit(self.font.render(f"Black: {self.ai_black.name}", True, (255, 255, 255)), (x_offset, 320))
        self.screen.blit(self.font.render(f"Last Move: {b_last:.3f}s", True, (200, 200, 200)), (x_offset, 360))
        self.screen.blit(self.font.render(f"Avg Time:  {b_avg:.3f}s", True, (200, 200, 200)), (x_offset, 400))

        if not self.game_over:
            turn_txt = "White is thinking..." if self.engine.white_turn else "Black is thinking..."
            self.screen.blit(self.large_font.render(turn_txt, True, (0, 255, 255)), (x_offset, 500))
        else:
            self.screen.blit(self.large_font.render(self.result_msg, True, (255, 50, 50)), (x_offset, 500))

    def _think_thread(self, current_ai):
        start_t = time.perf_counter()
        move = current_ai.get_move(self.engine, current_ai.dragon_level)
        time_taken = time.perf_counter() - start_t
        
        self.calculated_move = move
        if self.engine.white_turn:
            self.white_times.append(time_taken)
        else:
            self.black_times.append(time_taken)

    def run(self):
        clock = pg.time.Clock()
        running = True

        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False

            if not self.game_over and not self.ai_thinking:
                if self.engine.is_checkmate():
                    winner = "Black" if self.engine.white_turn else "White"
                    self.result_msg = f"CHECKMATE! {winner} wins."
                    self.game_over = True
                elif self.engine.is_stalemate():
                    self.result_msg = "STALEMATE! DRAW."
                    self.game_over = True
                
                # Check for the turn limit (150 moves = 75 turns)
                elif len(self.move_history) > 150:
                    score = self.engine.eval_board()
                    
                    if score > 0:
                        self.result_msg = "TIME LIMIT! White wins by points."
                    elif score < 0:
                        self.result_msg = "TIME LIMIT! Black wins by points."
                    else:
                        self.result_msg = "TIME LIMIT! Perfect Tie."
                        
                    self.game_over = True
                else:
                    self.ai_thinking = True
                    current_ai = self.ai_white if self.engine.white_turn else self.ai_black
                    threading.Thread(target=self._think_thread, args=(current_ai,), daemon=True).start()

            if self.ai_thinking and self.calculated_move is not None:
                self.engine.make_move(self.calculated_move)
                self.move_history.append(self.calculated_move)
                self.calculated_move = None
                self.ai_thinking = False

            self.screen.fill((0, 0, 0))
            self.draw_board()
            self.draw_stats_panel()
            pg.display.flip()
            clock.tick(60)

        pg.quit()

if __name__ == "__main__":
    
    # Changed drag_time_limit from 10 to 0 to speed up testing
    ai_1 = Dragon(name="White_Dragon", dragon_level=2, drag_time_limit=0)
    ai_2 = Dragon(name="Black_Dragon", dragon_level=2, drag_time_limit=0)
    
    arena = VisualArena(ai_1, ai_2)
    
    arena.engine = Chess(load_graphic=True) 
    arena.engine.load_images()
    
    arena.run()