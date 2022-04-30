from game import game_data

def game_exists(m):
    return m.chat.id in game_data.games

def game_not_exists(m):
    return not game_exists(m)