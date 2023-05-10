from requests import head
import streamlit as st
import chess
import chess.svg
from chess_utils import read_games, headers_df
from analyzer import analyze

partidas = read_games()
headers = headers_df(partidas)

st.title('Perfil de xadrez - ' + headers['username'][0])
st.dataframe(headers)

p_id = st.selectbox(
    'Escolha uma partida para rever', 
    options = range(len(partidas)),
    format_func=lambda a: headers['id'][a]
)
partida = partidas[p_id]
color = chess.BLACK if headers.loc[p_id]['Black'] == headers.loc[p_id]['username'] else chess.WHITE

moves = [move for move in partida.mainline_moves()]
move_index = st.select_slider(
    label='Lance',
    options=list(range(len(moves)+1))
)
last = moves[move_index - 1] if move_index > 0 else None

board = chess.Board()

tipos = [
    chess.PAWN,
    chess.KNIGHT,
    chess.BISHOP,
    chess.ROOK,
    chess.QUEEN,
    chess.KING
]
friend_pieces = [item for sublist in [list(board.pieces(tipo, color)) for tipo in tipos] for item in sublist]
enemy_pieces = [item for sublist in [list(board.pieces(tipo, not color)) for tipo in tipos] for item in sublist]

friend_dict = dict.fromkeys(
            [item for sublist in [list(board.attacks(i)) for i in friend_pieces] for item in sublist], "#00cc00cc"
        )
enemy_dict = dict.fromkeys(
            [item for sublist in [list(board.attacks(i)) for i in enemy_pieces] for item in sublist], "#cc0000cc"
        )
intersec_dict = {a: '#ffff00' for a in list(
        set(friend_dict.keys()).intersection(
        set(enemy_dict.keys())
    ))}

svg_board = chess.svg.board(
        board,
        orientation=color,
        fill=friend_dict | enemy_dict | intersec_dict,
        arrows=[chess.svg.Arrow(
            last.from_square,
            last.to_square, color="#0000cccc"
        )] if last else [],
        size=300
    )

for m in moves[:move_index]:
    board.push(m)

    friend_pieces = [item for sublist in [list(board.pieces(tipo, color)) for tipo in tipos] for item in sublist]
    enemy_pieces = [item for sublist in [list(board.pieces(tipo, not color)) for tipo in tipos] for item in sublist]

    friend_dict = dict.fromkeys(
            [item for sublist in [list(board.attacks(i)) for i in friend_pieces] for item in sublist], "#00cc00cc"
        )
    enemy_dict = dict.fromkeys(
                [item for sublist in [list(board.attacks(i)) for i in enemy_pieces] for item in sublist], "#cc0000cc"
            )
    
    intersec_dict = {a: '#ffff00cc' for a in list(
        set(friend_dict.keys()).intersection(
        set(enemy_dict.keys())
    ))}
    
    analise = analyze(m, board)

    svg_board = chess.svg.board(
        board,
        orientation=color,
        fill=friend_dict | enemy_dict | intersec_dict,
        arrows=[chess.svg.Arrow(
            last.from_square,
            last.to_square, color="#0000cccc"
        )] if last else [],
        size=300
    )

col1, col2 = st.columns(2)
col1.write(svg_board, unsafe_allow_html = True)

if last:
    board2 = board.copy()
    board2.pop()
    col2.text(board2.san(last))
    
    for error in analise['error']:
        col2.error(error)
    for warning in analise['warning']:
        col2.warning(warning)
    for success in analise['success']:
        col2.success(success)
    
if move_index == len(moves):
    col2.write(headers['Termination'][p_id])