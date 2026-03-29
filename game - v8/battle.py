from chess_engine import Chess, decode_move
from dragon import Dragon
from player import Player
import pygame as pg
import threading
import numpy, random

class Battle:
    def __init__(self, surface, dragon_level, dragon_name, player=Player((2,2)), super_mode=0):
        self.surface = surface
        self.super_mode = super_mode
        self.chess_engine = Chess(super_mode=self.super_mode) 
        self.is_active = True

        self.selected_sq = None
        self.hover_sq = None
        self.hover_moves = []

        self.player = player
        self.time_limit_bonus = max(self.player.dragons_beaten, 0) + player.time_limit_of_AI
        self.player.can_move = False
        self.dragon = Dragon(dragon_name, dragon_level)
        self.dragon_level = dragon_level
        self.game_over_processed = False
        self.ai_thinking = False
        self.ai_thread = None
        self.calculated_move = None

        self._last_width, self._last_height = 0, 0
        self.sqsize = 1
        self.x_offset, self.y_offset = 0, 0
        self.resized = False

        self.chess_engine.berserker_king = player.berserker_king
        self._apply_board_skills()
    
    def _apply_board_skills(self):
        board = self.chess_engine.board
        if self.player.pawn_shield:
            i = 0
            while True:
                sq = random.choice(list(range(40, 48)))
                if board[sq] == 0:
                    board[sq] = 1
                    break
                i += 1
                if i > 10: break
        if self.player.royal_guard:
            i = 0
            while True:
                sq = random.choice(list(range(48, 56)))
                if board[sq] == 1:
                    board[sq] = 5
                    break
                i += 1
                if i > 10: break
        if self.player.pawn_shield or self.player.royal_guard:
            self.chess_engine.mid_game_score = 0
            self.chess_engine.end_game_score = 0
            self.chess_engine.phase = 0
            self.chess_engine.calc_board_score()
            self.chess_engine.max_phase = max(24, self.chess_engine.phase)

    def handle_event(self, event):
        self._update_layout()

        if event.type == pg.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            col = (mouse_x - self.x_offset) // self.sqsize
            row = (mouse_y - self.y_offset) // self.sqsize
            if 0<= row < 8 and 0 <= col < 8:
                sq = row * 8 + col
                self.click_process(sq)
        
        if event.type == pg.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            col = (mouse_x - self.x_offset) // self.sqsize
            row = (mouse_y - self.y_offset) // self.sqsize

            if 0 <= row < 8 and 0 <= col < 8:
                sq = row * 8 + col
                if self.hover_sq != sq:
                    self.hover_sq = sq
                    self.update_hover_moves()
            else:
                if self.hover_sq is not None:
                    self.hover_sq = None
                    self.hover_moves = []
        
    def update_hover_moves(self):
        self.hover_moves = []
        target_sq = self.selected_sq if self.selected_sq is not None else self.hover_sq
        if target_sq is not None:
            piece = self.chess_engine.board[target_sq]
            if piece != 0 and not (piece & 8) and self.chess_engine.white_turn:
                for move in self.chess_engine.get_valid_moves():
                    start, end, flag = decode_move(move)
                    if start == target_sq:
                        self.hover_moves.append(end)

    
    def click_process(self, sq):
        if self.selected_sq is None:
            piece = self.chess_engine.board[sq]
            if piece != 0:
                is_black = bool(piece  & 8)
                if self.chess_engine.white_turn and not is_black:
                    self.selected_sq = sq
    
        else:
            if self.selected_sq == sq:
                self.selected_sq = None
                return
            move_to_make = None
            for move in  self.chess_engine.get_valid_moves():
                start, end, flag = decode_move(move)
                if start == self.selected_sq and end == sq:
                    move_to_make = move
                    break
            if move_to_make is not None:
                self.chess_engine.make_move(move_to_make)
                self.selected_sq = None
                self.check_game_over(self.player)
            else:
                n_piece = self.chess_engine.board[sq]
                if self.chess_engine.white_turn and n_piece != 0 and not (n_piece & 8):
                    self.selected_sq = sq
                else:
                    self.selected_sq = None
        self.update_hover_moves()

    def update(self):
        if not self.chess_engine.white_turn and not self.game_over_processed:
            if not self.ai_thinking:
                self.trigger_dragon_move()
            elif self.calculated_move is not None:
                self.chess_engine.make_move(self.calculated_move)
                self.check_game_over(self.player)

                self.ai_thinking = False
                self.calculated_move = None
                self.ai_thread = None

    def trigger_dragon_move(self):
        self.ai_thinking = True
        self.calculated_move = None

        chess_engine_clone = self.chess_engine.clone()

        self.ai_thread = threading.Thread(target=self._calculate_move_thread,
                                          args=(chess_engine_clone,))
        self.ai_thread.start()

    def _calculate_move_thread(self, chess_engine_clone):
        self.calculated_move = self.dragon.get_move(chess_engine_clone, self.dragon_level)

    def player_won(self):
        if self.game_over_processed: return
        self.game_over_processed = True
        self.player.dragons_beaten += 1
        self.player.playing_chess = False
        self.player.can_move = True
        self.update_score(self.dragon_level)
    
    def player_lost(self):
        if self.game_over_processed: return
        self.game_over_processed = True

        if self.player.second_wind and not self.player._second_wind_used:
            self.player._second_wind_used = True
            print("Second Wind!")
            self.chess_engine = Chess(super_mode=self.super_mode)
            self.chess_engine.berserker_king = self.player.berserker_king
            self._apply_board_skills()
            self.game_over_processed = False
            return
        if self.player.kings_ransom and self.player.score >= 500:
            self.player.score -= 500
            print("King's Random paid - 500 pts spent to survive!")
            self.chess_engine = Chess(super_mode=self.super_mode)
            self.chess_engine.berserker_king = self.player.berserker_king
            self._apply_board_skills()
            self.game_over_processed = False
            return
        self.player.lives -= 1
        self.player.playing_chess = False
        self.player.can_move = True
        print("Lost a Life! You can do it!")

    def update_score(self, difficulty):
        score = (difficulty + 1)*100
        if self.player.blitz_specialist and len(self.chess_engine.move_log) <= 40:
            score *= 2
            print("Blitz Specialist! Double points!")
        if self.player.extra_spoils:
            score = int(score * 1.25)
        
        self.player.score += score
    
    def check_game_over(self, player):
        if self.chess_engine.is_checkmate():
            if self.chess_engine.white_turn:
                self.player_lost()
            else:
                self.player_won()
            return True
        elif self.chess_engine.is_stalemate():
            if player.peace_treaty:
                print("Peace Treaty - stalemate ignored!")
                return False
            print("Good Progress! Try again!")
            player.playing_chess = False
            return True
        return False
    
    def _update_layout(self):
        curr_w, curr_h = self.surface.get_size()

        if curr_w != self._last_width or curr_h != self._last_height:
            self._last_width, self._last_height = curr_w, curr_h

            avail_width = curr_w - 200
            self.sqsize = min(avail_width, curr_h) // 8
            if self.sqsize < 1: self.sqsize = 1
            self.x_offset = (avail_width - (self.sqsize * 8)) // 2
            self.y_offset = (curr_h - (self.sqsize * 8)) // 2