import chess
import pandas as pd


class StateAnalyzer:
    def __init__(self, square, board):
        self.square = square
        self.board = board
        self.friend = board.color_at(self.square)
        self.piece_name = chess.piece_name(board.piece_type_at(self.square))
        self.get_attacks()
    
    def get_pieces(self, squares, is_friend):
        return [
            chess.piece_name(self.board.piece_type_at(s)).upper() + ' ' + chess.SQUARE_NAMES[s]
            for s in squares
            if self.board.piece_type_at(s)
            and (
                self.board.color_at(s) == self.board.color_at(self.square) if is_friend
                else self.board.color_at(s) != self.board.color_at(self.square)
            )
        ]

    def get_attacks(self):
        self.protectors = self.get_pieces(
            squares = self.board.attackers(self.friend, self.square),
            is_friend = True
        )
        self.attackers = self.get_pieces(
            squares = self.board.attackers(not self.friend, self.square),
            is_friend = False
        )
        self.target_squares = self.board.attacks(self.square)
        self.attacked = self.get_pieces(
            squares = self.target_squares,
            is_friend = False
        )
        self.protected = self.get_pieces(
            squares = self.target_squares,
            is_friend = True
        )
    
    def __str__(self):
        return self.piece_name.upper() + ' ' + chess.SQUARE_NAMES[self.square] + '\n' +\
        '''protetores: ''' + str(list(self.protectors)) + '\n' +\
        '''atacantes: ''' + str(list(self.attackers)) + '\n' +\
        '''peças atacadas: ''' + str(list(self.attacked)) + '\n' +\
        '''peças protegidas: ''' + str(list(self.protected))


class MoveAnalyzer:
    def __init__(self, initial_state: StateAnalyzer, final_state: StateAnalyzer):
        self.initial_state = initial_state
        self.final_state = final_state
    
    def still(self, pieces1, pieces2):
        return list(
            set(pieces1).intersection(pieces2)
        )
    
    def no_more(self, pieces1, pieces2):
        return [
            piece for piece in pieces1 
            if piece not in pieces2
        ]
    
    def only_now(self, pieces1, pieces2):
        return [
            piece for piece in pieces2
            if piece not in pieces1
        ]
    
    def compare(self, pieces1, pieces2, function=''):
        return {
            'still': self.still(pieces1, pieces2),
            'no_more': self.no_more(pieces1, pieces2),
            'only_now': self.only_now(pieces1, pieces2),
            'function': function,
            'piece': self.final_state.piece_name,
            'square': self.final_state.square
        }
    
    def get_comparisons(self):
        comparisons = [
            {
                'name': 'protectors',
                'function': lambda a: a.protectors
            },
            {
                'name': 'protected',
                'function': lambda a: a.protected
            },
            {
                'name': 'attackers',
                'function': lambda a: a.attackers
            },
            {
                'name': 'attacked',
                'function': lambda a: a.attacked
            },
        ]

        resp = []
        for comparison in comparisons:
            resp.append(
                self.compare(
                    comparison['function'](self.initial_state),
                    comparison['function'](self.final_state),
                    function=comparison['name']
                )
            )
        resp = pd.DataFrame(resp)
        resp.index = resp['function']
        resp = resp.drop(columns=['function'])

        return resp.T
    
class MoveExplainer:
    def __init__(self, Move: MoveAnalyzer):
        self.Move = Move
        self.comparisons = self.Move.get_comparisons()

    def piece_name(self):
        return self.comparisons.protectors.loc['piece'].upper() +\
                ' (' + chess.SQUARE_NAMES[self.comparisons.protectors.loc['square']] + ') '

    def becomes_protected(self):
        protectors = self.comparisons.protectors
        return len(protectors.loc['only_now']) > 0 \
        and len(protectors.loc['still']) == 0
    
    def becomes_unprotected(self):
        protectors = self.comparisons.protectors
        return len(protectors.loc['still']) == 0 \
        and len(protectors.loc['only_now']) == 0
    
    def becomes_attacked(self):
        attackers = self.comparisons.attackers
        return len(attackers.loc['only_now']) > 0
    
    def becomes_unattacked(self):
        attackers = self.comparisons.attackers
        return len(attackers.loc['no_more']) > 0
    
    def becomes_attacker(self):
        attacked = self.comparisons.attacked
        return len(attacked.loc['only_now']) > 0
    
    def becomes_not_attacker(self):
        attacked = self.comparisons.attacked
        return len(attacked.loc['still']) == 0 \
        and len(attacked.loc['only_now']) == 0 \
        and len(attacked.loc['no_more']) > 0
    
    def becomes_protector(self):
        protected = self.comparisons.protected
        return len(protected.loc['only_now']) > 0
    
    def becomes_not_protector(self):
        protected = self.comparisons.protected
        return len(protected.loc['still']) == 0 \
        and len(protected.loc['only_now']) == 0 \
        and len(protected.loc['no_more']) > 0
    
    def explain(self):
        explanation = {
            'warning': [],
            'error': [],
            'success': []
        }
        if self.becomes_unprotected():
            explanation['error'].append(
                'Esta jogada deixa a peça ' + self.piece_name() + ' desprotegida.'
            )
        if self.becomes_attacked():
            explanation['error'].append(
                'Esta jogada deixa a peça ' + self.piece_name() + ' atacada por ' + str(self.comparisons['attackers'].loc['only_now'])
            )
        if self.becomes_not_attacker():
            explanation['warning'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' parar de atacar ' + str(self.comparisons['attacked'].loc['no_more'])
            )
        if self.becomes_not_protector():
            explanation['warning'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' parar de proteger ' + str(self.comparisons['protected'].loc['no_more'])
            )
        if self.becomes_protected():
            explanation['success'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' ser protegida por ' + str(self.comparisons['protectors'].loc['only_now'])
            )
        if self.becomes_protector():
            explanation['success'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' passa a proteger ' + str(self.comparisons['protected'].loc['only_now'])
            )
        if self.becomes_attacker():
            explanation['success'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' passa a atacar ' + str(self.comparisons['attacked'].loc['only_now'])
            )
        if self.becomes_unattacked():
            explanation['success'].append(
                'Esta jogada faz a peça ' + self.piece_name() + ' parar de ser atacada por ' + str(self.comparisons['attackers'].loc['no_more'])
            )
        return explanation


def analyze(move, board):
    past_board = board.copy()
    past_board.pop()

    past = move.from_square
    present = move.to_square

    past_analyzer = StateAnalyzer(past, past_board)
    present_analyzer = StateAnalyzer(present, board)

    move_analyzer = MoveAnalyzer(past_analyzer, present_analyzer)
    move_explainer = MoveExplainer(move_analyzer)

    return move_explainer.explain()