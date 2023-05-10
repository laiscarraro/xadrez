import chess.pgn
import pandas as pd
import os

def read_games():
    pgn = open('partidas/'+os.listdir('partidas')[0], encoding='utf-8')
    offsets = []
    partidas = []

    while True:
        offset = pgn.tell()

        headers = chess.pgn.read_headers(pgn)
        if headers is None:
            break

        offsets.append(offset)
        
    for offset in offsets:
        pgn.seek(offset)
        partidas.append(chess.pgn.read_game(pgn))
    
    return partidas


def headers_df(partidas):
    headers = pd.DataFrame([partida.headers for partida in partidas]).fillna('')
    username = headers['Black'].append(headers['White']).value_counts().index[0]
    headers['username'] = username

    headers['vs'] = headers['White'].apply(lambda a: a if a != username else '') +\
                headers['Black'].apply(lambda a: a if a != username else '')
    headers['id'] = 'vs ' + headers['vs'] + ' ' + headers['Date'] + ' ' + headers['EndTime'] + ' ' + headers['Termination']
    return headers