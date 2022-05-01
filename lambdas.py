from game import game_data

def game_exists(m):
    return m.chat.id in game_data.games

def game_not_exists(m):
    return not game_exists(m)

def game_not_started(m):
    if game_not_exists(m):
        return
    game = game_data.get_game(m.chat.id)
    return not game.started

def history_callback(c):
    return 'history' in c.data

def move_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'move'

def move_to_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    if not c.data.count(' '):
        return
    location = c.data.split(' ')[1]
    if location not in player.nearby_locations:
        return
    return player and 'move' in c.data

def items_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'items'

def back_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'back'

def treasure_info_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'treasureinfo'

def camerainfo_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'camerainfo'

def wait_callback(c):
    return game_data.is_player_playing(c.from_user.id) and c.data == 'wait'

def mineremover_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'mineremover' and 'mineremover' in player.items

def glasses_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'glasses' and 'glasses' in player.items

def pistol_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'pistol' and 'pistol' in player.items

def camera_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'camera' and 'camera' in player.items

def costume_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'costume' and 'costume' in player.items

def flash_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'flash' and 'flash' in player.items

def shockmine_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    return c.data == 'shockmine' and 'shockmine' in player.items

def flash_to_callback(c):
    player = game_data.is_player_playing(c.from_user.id)
    if not player:
        return
    if not c.data.count(' '):
        return
    location = c.data.split(' ')[1]
    if location not in player.nearby_locations:
        return
    return player and 'flash' in c.data
