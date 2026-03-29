import pygame as pg
import numpy as np
import os
from numba import njit
import constants
from piece_points import piece_square_mid_game, piece_square_end_game, PHASE_WEIGHTS
 
# ============ PIECE TYPES =================
w_p, w_k, w_b, w_r, w_q, w_K = 1, 2, 3, 4, 5, 6
b_p, b_k, b_b, b_r, b_q, b_K = 9, 10, 11, 12, 13, 14
empty = 0
 
# ============ OFFSETS =================
knight_offsets = np.array([-17, -15, -10, -6, 6, 10, 15, 17], dtype=np.int32)
diag_offsets = np.array([-9, -7, 7, 9], dtype=np.int32)
straight_offsets = np.array([-8, -1, 1, 8], dtype=np.int32)
king_offsets = np.array([-9, -8, -7, -1, 1, 7, 8, 9], dtype=np.int32)
berserker_king_offsets = np.array([-17, -15, -10, -6, 6, 10, 15, 17, -9,  -8,  -7, -1, 1,  7,  8,  9],
    dtype=np.int32)

@njit
def mop_up_eval(my_king_sq, enemy_king_sq, phase):
    if phase > 6:
        return 0
    
    score = 0

    ek_r, ek_c = enemy_king_sq // 8, enemy_king_sq % 8
    dist_r = max(3 - ek_r, ek_r - 4)
    dist_c = max(3 - ek_c, ek_c - 4)
    score += (dist_r + dist_c) * 10 

    mk_r, mk_c = my_king_sq // 8, my_king_sq % 8
    dist_between = abs(mk_r - ek_r) + abs(mk_c - ek_c)
    score += (14 - dist_between) * 5

    return score
 
class Chess:
    def __init__(self, super_mode: int=0, load_graphic: bool=True):
        pawn_row = np.array([w_p] * 8)
        if super_mode > 0:
            cnt = min(super_mode, 8)
            idxs = np.random.choice(len(pawn_row), cnt, replace=False)
            pawn_row[idxs] = w_q
        
        self.board = np.zeros(64, dtype=np.int8)
        self.board[0: 8]   = [b_r, b_k, b_b, b_q, b_K, b_b, b_k, b_r]
        self.board[8: 16]  = [b_p, b_p, b_p, b_p, b_p, b_p, b_p, b_p]
        self.board[48: 56] = pawn_row
        self.board[56: 64] = [w_r, w_k, w_b, w_q, w_K, w_b, w_k, w_r]
 
        self.white_turn = True
        self.move_log   = []
        self.board_history = []
        self.org_imgs   = {}
        self.images     = {}
        if load_graphic:
            self.load_images()
        
        self.phase = 0
        self.mid_game_score = 0
        self.end_game_score = 0
        self.calc_board_score()
        self.max_phase = max(24, self.phase)
        self.white_king_sq, self.black_king_sq = 60, 4
        self.board_history.append(self.board.tobytes())

        self.berserker_king = False
        self.dragons_blunder = False
        self.ai_fatigue = False
        self.move_count = 0
 
    def calc_board_score(self):
        for sq in range(64):
                piece = self.board[sq]
                if piece != 0:
                    self.mid_game_score += piece_square_mid_game[piece][sq]
                    self.end_game_score += piece_square_end_game[piece][sq]
                    self.phase += PHASE_WEIGHTS[piece]
    
    def eval_board(self):
        phase = min(max(self.phase, 0), self.max_phase)
        base_score = (self.mid_game_score * phase + self.end_game_score * (self.max_phase - phase)) // self.max_phase
        
        if base_score > 0:
            base_score += mop_up_eval(self.white_king_sq, self.black_king_sq, phase)
        elif base_score < 0:
            base_score -= mop_up_eval(self.black_king_sq, self.white_king_sq, phase)
            
        return base_score
 
    def load_images(self):
        try:
            base_path = os.path.dirname(__file__)
            image_folder = os.path.join(base_path, "images")
            
            pieces = ['pawn', 'knight', 'bishop', 'rook', 'queen', 'king']
            colors = ['white', 'black']
            for c in colors:
                for p in pieces:
                    key = f"{c}_{p}"
                    full_path = os.path.join(image_folder, f"{key}.png")
                    img = pg.image.load(full_path).convert_alpha()
                    self.org_imgs[key] = img
        except Exception as e:
            print(f"ERROR: {e}")
            print("Piece files not found, shifting to text if possible.")
 
    def make_move(self, move):
        start, end, flag = decode_move(move)
        piece = self.board[start]
        captured_piece = self.board[end]
 
        self.move_log.append((move, captured_piece, self.white_king_sq, self.black_king_sq,
                              self.white_turn, self.phase, self.mid_game_score, self.end_game_score))
        self.mid_game_score -= piece_square_mid_game[piece][start]
        self.end_game_score -= piece_square_end_game[piece][end]
        
        if (piece & 7) == 6:
            if piece & 8:
                self.black_king_sq = end
            else:
                self.white_king_sq = end
        
        if captured_piece != 0:
            self.mid_game_score -= piece_square_mid_game[captured_piece][end]
            self.end_game_score -= piece_square_end_game[captured_piece][end]
            self.phase -= PHASE_WEIGHTS[captured_piece]
        
        if flag == 1: 
            promote_queen_val = 13 if (piece & 8) else 5
            self.board[end] = promote_queen_val
            self.mid_game_score += piece_square_mid_game[promote_queen_val][end]
            self.end_game_score += piece_square_end_game[promote_queen_val][end]
            self.phase += PHASE_WEIGHTS[promote_queen_val]
        else:
            self.board[end] = piece
            self.mid_game_score += piece_square_mid_game[piece][end]
            self.end_game_score += piece_square_end_game[piece][end]
        
        self.board[start] = 0
        self.white_turn = not self.white_turn
        self.board_history.append(self.board.tobytes())
 
    def undo_move(self):
        if not self.move_log:
            return
        move, captured_piece,  prev_w_K, prev_b_K, prev_turn, prev_phase, prev_mid_game, prev_end_game = self.move_log.pop()
        self.mid_game_score, self.end_game_score = prev_mid_game, prev_end_game
        self.phase = prev_phase
        self.white_turn = prev_turn
        self.white_king_sq = prev_w_K
        self.black_king_sq = prev_b_K
        
        start, end, flag = decode_move(move)
        curr_piece = self.board[end]
 
        if flag == 1:
            pawn_val = 9 if (curr_piece & 8) else 1
            self.board[start] = pawn_val
        else:
            self.board[start] = curr_piece
        
        self.board[end] = captured_piece
        if self.board_history:
            self.board_history.pop()
    
    def get_valid_moves(self):
        return self.validate_moves(self.get_all_pos_moves())  # validates pseudo-valid moves
 
    def get_all_pos_moves(self):
        berserker_king: bool = bool(self.berserker_king and self.white_turn and (self.phase <= 12))
        return get_pos_moves(self.white_turn, self.board, berserker_king)
 
    def validate_moves(self, pseudo_moves):
        valid_moves=[]
        for move in pseudo_moves:
            self.make_move(move)
            if not self.is_in_check(not self.white_turn):
                valid_moves.append(move)
            self.undo_move()
        return valid_moves
 
    def is_in_check(self, is_white_king):
        king_sq= self.white_king_sq if is_white_king else self.black_king_sq
        attacker_is_white = not is_white_king
        berserker_king = bool(self.berserker_king and attacker_is_white and (self.phase <= 12))
        return is_square_attacked(self.board, king_sq, attacker_is_white, berserker_king)
    
    def is_checkmate(self):
        if self.is_in_check(self.white_turn):
            if len(self.get_valid_moves()) == 0:
                return True
        return False
    
    def is_stalemate(self):
        curr_board = self.board.tobytes()
        if self.board_history.count(curr_board) >= 3:
            return True
        if not self.is_in_check(self.white_turn):
            if len(self.get_valid_moves()) == 0:
                return True
        return False
    
    def clone(self):
        c = Chess(super_mode=0, load_graphic=False)
        c.board = self.board.copy()
        c.white_turn = self.white_turn
        c.white_king_sq = self.white_king_sq
        c.black_king_sq = self.black_king_sq
        c.mid_game_score = self.mid_game_score
        c.end_game_score = self.end_game_score
        c.phase = self.phase
        c.max_phase = self.max_phase
        c.move_log = list(self.move_log)
        c.board_history = list(self.board_history)
        # skill flags
        c.dragons_blunder = self.dragons_blunder
        c.ai_fatigue = self.ai_fatigue
        c.move_count = self.move_count
        c.berserker_king = False  # AI never gets this
        return c

@njit
def get_pos_moves(white_turn, board, berseker_king=False):
    moves = np.zeros(256, dtype=np.int32)
    cnt = 0
    for sq in range(64):
            piece = board[sq]
            if piece == 0: continue
 
            piece_is_black = bool(piece & 8)
            if white_turn and piece_is_black: continue
            if not white_turn and not piece_is_black: continue
 
            color = -1 if not piece_is_black else 1
            piece_type = piece & 7
 
            if piece_type == 1:
                cnt = pawn_moves(board, sq, color, moves, cnt)
            elif piece_type == 2:
                cnt = knight_moves(board, sq, moves, cnt)
            elif piece_type == 3:
                cnt = bishop_moves(board, sq, moves, cnt)
            elif piece_type == 4:
                cnt = rook_moves(board, sq, moves, cnt)
            elif piece_type == 5:
                cnt = queen_moves(board, sq, moves, cnt)
            elif piece_type == 6:
                use_berserker_king = berseker_king and not piece_is_black
                cnt = king_moves(board, sq, moves, cnt, use_berserker_king)
 
    return moves[:cnt]

@njit
def pawn_moves(board, sq, color, moves, cnt):
    is_black = (color == 1)
    dir_offset = 8 if is_black else -8
    start_row = 1 if is_black else 6
    promote_row = 7 if is_black else 0
    
    target = sq + dir_offset
    if 0 <= target < 64 and board[target] == 0:
        if target // 8 == promote_row:
            moves[cnt] = sq | (target << 6) | (1 << 12)
        else:
            moves[cnt] = sq | (target << 6)
        cnt  +=1
 
        if sq // 8 == start_row:
            target_2_ahead = sq + (2 * dir_offset)
            if board[target_2_ahead] == 0:
                moves[cnt] = sq | (target_2_ahead << 6)
                cnt += 1
        
    for diag_offset in (dir_offset - 1, dir_offset + 1):
        target = sq + diag_offset
        if 0 <= target < 64 and abs((sq % 8) - (target % 8)) == 1:
                target_piece = board[target]
                if target_piece != 0:
                    if ((board[sq] & 8) != (target_piece & 8)): 
                        if target // 8 == promote_row:
                            moves[cnt] = sq | (target << 6) | (1 << 12)
                        else:
                            moves[cnt] = sq | (target << 6)
                        cnt += 1
    return cnt 
 
@njit
def knight_moves(board, sq, moves, cnt):
    for jump in knight_offsets:
        target_sq = sq + jump
        if 0 <= target_sq < 64:
            if abs((sq % 8) - (target_sq % 8)) <= 2: 
                target_piece = board[target_sq]
                if target_piece == 0 or ((board[sq] & 8) != (target_piece & 8)):
                    moves[cnt] = sq | (target_sq << 6)
                    cnt += 1
    return cnt
 
@njit
def bishop_moves(board, sq, moves, cnt):
    return sliding_piece_move_finder(board, sq, diag_offsets, moves, cnt)
@njit
def rook_moves(board, sq, moves, cnt):
    return sliding_piece_move_finder(board, sq, straight_offsets, moves, cnt)
@njit
def queen_moves(board, sq, moves, cnt):
    cnt = sliding_piece_move_finder(board, sq, diag_offsets, moves, cnt)
    cnt = sliding_piece_move_finder(board, sq, straight_offsets, moves, cnt)
    return cnt
@njit
def king_moves(board, sq, moves, cnt, use_berserker_king=False):
    offsets = berserker_king_offsets if use_berserker_king else king_offsets
    col_limit = 2 if use_berserker_king else 1
    for jump in offsets: 
        target = sq + jump
        if 0 <= target < 64:
            if abs((sq % 8) - (target % 8)) <= col_limit:
                target_piece = board[target]
                if target_piece == 0 or (board[sq] & 8) != (target_piece & 8):
                    moves[cnt] = sq | (target << 6)
                    cnt += 1
    return cnt
 
@njit
def sliding_piece_move_finder(board, sq, offsets, moves, cnt):
    for jump in offsets:
        target = sq
        for _ in range(1, 8):
            col = target % 8
            target += jump
 
            if target < 0 or target >= 64: break
            if abs(col - (target % 8)) > 1: break
 
            target_piece = board[target]
            if target_piece == 0:
                moves[cnt] = sq | (target << 6)
                cnt += 1
            else:
                if (board[sq] & 8) != (target_piece & 8):
                    moves[cnt] = sq | (target << 6)
                    cnt += 1
                break
    return cnt
 
@njit
def is_square_attacked(board, sq, attacker_is_white, berserker_king: bool=False):
    attacker_color_bit = 0 if attacker_is_white else 8
 
    pawn_dir = 8 if attacker_is_white else -8
    for shift in (pawn_dir -1, pawn_dir+1):
        target = sq + shift
        if 0 <= target < 64 and abs((sq % 8) - (target % 8)) == 1:
            if board[target] == (1 | attacker_color_bit):
                return True
    
    knight_val = 2 | attacker_color_bit
    for jump in knight_offsets:
        target = sq + jump
        if 0 <= target < 64 and abs((sq % 8) - (target % 8)) <= 2:
            if board[target] == knight_val: return True
    
    king_val = 6 | attacker_color_bit
    for jump in king_offsets:
        target = sq + jump
        if 0 <= target < 64 and abs((sq % 8) - (target % 8)) <= 1:
            if board[target] == king_val: return True
    
    if berserker_king:
        for jump in knight_offsets:
            target = sq + jump
            if 0<=target<64 and abs((sq % 8) - (target % 8)) <= 2:
                if board[target] == king_val:
                    return True

    bishop_val = 3 | attacker_color_bit
    rook_val = 4 | attacker_color_bit
    queen_val = 5 | attacker_color_bit
 
    for jump in diag_offsets:
        target = sq
        for _ in range(1, 8):
            col = target % 8
            target += jump
            if target < 0 or target >= 64 or abs(col - (target % 8)) > 1: break
            target_val = board[target]
            if target_val != 0:
                if target_val == bishop_val or target_val == queen_val:
                    return True
                break
    
    for jump in straight_offsets:
        target = sq
        for _ in range(1, 8):
            col = target % 8
            target += jump
            if target < 0 or target >= 64 or abs(col - (target % 8)) > 1: break
            target_val = board[target]
            if target_val != 0:
                if target_val == rook_val or target_val == queen_val:
                    return True
                break
    return False
             
@njit
def score_move(move, board):
    m = move
    start = m & 63
    end = (m >> 6) & 63
    flag = m >> 12

    score = np.int32(0)
    captured_piece = np.int32(board[end])
    moving_piece   = np.int32(board[start])

    if captured_piece != 0:
        victim_val   = (captured_piece & 7) * 100
        attacker_val = (moving_piece   & 7) * 10
        score += np.int32(1000 + (victim_val - attacker_val))
        
    if flag == 1:
        score += np.int32(900)
    return score
 
@njit
def sort_moves(moves, board):
    # Optimized Insertion Sort
    n = len(moves)
    scores = np.zeros(n, dtype=np.int32)
    for i in range(n):
        scores[i] = score_move(moves[i], board)
    
    for i in range(1, n):
        curr_score = scores[i]
        curr_move = moves[i]
        j = i - 1

        while j >= 0 and scores[j] < curr_score:
            scores[j + 1] = scores[j]
            moves[ j + 1] = moves[j]
            j -= 1
        
        scores[j + 1] = curr_score
        moves[j + 1] = curr_move
    return moves

@njit
def encode_move(start, end, flag):
    return start | (end << 6) | (flag << 12)
 
@njit
def decode_move(move):
    start = move & 63
    end = (move >> 6) & 63
    flag = move >> 12
    return start, end, flag