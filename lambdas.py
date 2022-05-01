from game import game_data

def game_exists(m):
    return m.chat.id in game_data.games

def game_not_exists(m):
    return not game_exists(m)

def game_not_started(m):
    if game_not_exists(m):
        return
    return not game_data.get_game(m.chat.id).started

def history_callback(c):
    return 'history' in c.data

def move_callback(c):
    return game.is_player_playing(c.from_user.id) and c.data == 'move'

def items_callback(c):
    return game.is_player_playing(c.from_user.id) and c.data == 'items'

def camerainfo_callback(c):
    return game.is_player_playing(c.from_user.id) and c.data == 'camerainfo'

def wait_callback(c):
    return game.is_player_playing(c.from_user.id) and c.data == 'wait'

def mineremover_callback(c):
    player = game.is_player_playing(c.from_user.id)
    return player and c.data == 'wait' and 'mineremover' in player.items