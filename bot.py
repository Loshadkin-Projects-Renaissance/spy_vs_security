# -*- coding: utf-8 -*-
import os
import random
import threading

from constants import *
from game import game_data
from lambdas import *
from config import *
from startup import bot, types


@bot.message_handler(commands=['gameinfo'])
def gameinfo_handler(m):
    game = game_data.get_game(m.chat.id)
    if not game:
        bot.send_message(m.chat.id, 'Игра еще не запущена!')
        return
    tts = ''
    tts += 'Инфо о игре:\n'
    tts += f'Ход: {game.turn}/25\n'
    tts += f'Игроков походило: {len(game.ready_players)}/{len(game.players)}'
    bot.send_message(m.chat.id, tts)

    


@bot.message_handler(commands=['creategame'], func=game_not_exists)
def creategame_handler(m):
    game = game_data.create_game(m.chat.id, 2)
    bot.send_message(m.chat.id, 'Игра в режиме 1х1 началась! Жмите /join, чтобы присоединиться! До отмены игры 5 минут.')
    t = threading.Timer(300,cancelgame,args=[m.chat.id])
    t.start()
    game.timer = t


@bot.message_handler(commands=['creategame2x2'], func=game_not_exists)
def creategame_2x2_handler(m):
    game = game_data.create_game(m.chat.id, 4)
    bot.send_message(m.chat.id, 'Игра в режиме 2х2 началась! Жмите /join, чтобы присоединиться! До отмены игры 5 минут.')
    t=threading.Timer(300,cancelgame,args=[m.chat.id])
    t.start()
    game.timer = t


@bot.message_handler(commands=['cancel'], func=game_exists)
def cancelgamee(m):
    game_data.get_game(m.chat.id).timer.cancel()
    del game_data.games[m.chat.id]
    bot.send_message(m.chat.id, 'Игра была удалена.')
       
 
@bot.message_handler(commands=['surrender'], func=game_exists)
def surrender_handler(m):
    game = game_data.get_game(m.chat.id)
    player=None
    for ids in game.players:
        if game.players[ids].id == m.from_user.id:
            player=game.players[ids]
    if not player:
        return
    player.disarmed = 1
    if player.role == 'spy':
        text='В шпионе '+player.name+' проснулась совесть, и он сдался.'
    else:
        text=player.name + ' сдался!'
    bot.send_message(m.chat.id, text)
     

@bot.message_handler(commands=['map'])
def map_handler(m):
    bot.send_photo(m.chat.id, map_file_id)


@bot.message_handler(commands=['startgame'], func=game_not_started)
def startgame_handler(m):
    game = game_data.get_game(m.chat.id)
    if game.check_readiness():
        game.begin()
    else:
        bot.send_message(m.chat.id, 'Недостаточно игроков!')
    

@bot.message_handler(commands=['join'], func=game_not_started)
def join_handler(m):
    game = game_data.get_game(m.chat.id)

    for player in game.players:
        if player.id == m.from_user.id:
            bot.send_message(m.chat.id, 'Вы уже в игре!')
            return

    if game.check_readiness():
        bot.send_message(m.chat.id, 'Достигнуто максимальное число игроков!')
        return

    try:
        bot.send_message(m.from_user.id, 'Вы успешно присоединились!')
    except:
        bot.send_message(m.chat.id, 'Для начала напишите боту @Spy_VS_Security_Bot что-нибудь!')
        return

    game.join_player(m.from_user.id, m.from_user.first_name, m.chat.id)
    bot.send_message(m.chat.id, m.from_user.first_name+' присоединился!')
               
              
def cancelgame(id):
    try:
        del game
        bot.send_message(id, 'Игра была отменена!')
    except:
        pass
    

def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode='Markdown'):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)


@bot.callback_query_handler(func=history_callback)
def history_callback_handler(c):
    history_id = c.data.split(' ')[1]
    yes=0
    for game in game_data.games:
        game = game_data.games[game]
        for player in game.players:
            if player.id == c.from_user.id:
                bot.send_message(c.message.chat.id, c.from_user.first_name+', нельзя смотреть историю, находясь в игре!')
                return

    if history_id not in history:
        medit('История этой игры больше недоступна!',c.message.chat.id,c.message.message_id)
        return

    try:
        bot.send_message(c.from_user.id, history[history_id])
    except:
        bot.send_message(c.message.chat.id, c.from_user.first_name+', напишите боту в личку, чтобы я мог отправлять вам историю боя!')


@bot.callback_query_handler(func=move_callback)
def move_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    kb = types.InlineKeyboardMarkup()
    for near_location in set(nearlocs[player.location]):
        if near_location == player.location:
            continue
        kb.add(types.InlineKeyboardButton(text=loctoname(near_location), callback_data='move '+near_location))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))    
    medit('Куда вы хотите направиться?',c.message.chat.id,c.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=items_callback)
def items_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    kb = types.InlineKeyboardMarkup()
    for item in player.items:
        item_name = itemtoname(item)
        if item_name:
            kb.add(types.InlineKeyboardButton(text=item_name, callback_data=item))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
    medit('Выберите предмет.', c.message.chat.id, c.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=camerainfo_callback)
def camerainfo_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game
    if player.role=='spy':
        text=''
        for camera in player.cameras:
            text+=loctoname(camera)+':\n'
            for other_player in game.players:
                if other_player.location == camera and other_player.id!=player.id:
                    text+=other_player.name+' был замечен на камерах!\n'
        if text=='':
            text='У вас не установлено ни одной камеры!'
        bot.answer_callback_query(c.id,text, show_alert=True)


@bot.callback_query_handler(func=wait_callback)
def wait_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    player.ready = True
    medit('Вы пропускаете ход. Ожидайте следующего хода...',c.message.chat.id, c.message.message_id)
    player.lastloc = player.location
    game.player_step()


@bot.callback_query_handler(func=mineremover_callback)
def mineremover_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    
    player.items.remove('mineremover')
    player.removemine = True            
    game.texttohistory+='Шпион '+player.name+' готовится обезвреживать мину-шокер.\n\n'
    medit('Вы готовитесь обезвредить мину-шокер в своей следующей локации.', c.message.chat.id, c.message.message_id)

    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    msg = bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
    player.currentmessage = msg
    player.messagetoedit = msg 


@bot.callback_query_handler(func=move_to_callback)
def move_to_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    location = c.data.split(' ')[1]
    player.lastloc=player.location
    medit('Вы перемещаетесь в локацию: '+loctoname(location)+'.',c.message.chat.id, c.message.message_id)
    player.location = location
    player.ready = True
    player.moving = True
    if player.role=='spy' and player.location=='treasure':
        player.stealing = True
    game.player_step()


@bot.callback_query_handler(func=glasses_callback)
def glasses_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    player.items.remove('glasses')
    player.glasses = 1
    game.texttohistory+='Охранник '+player.name+' надел очко!\n\n'
    medit('Вы успешно надели очки! На этот ход вы защищены от флэшек.', c.message.chat.id, c.message.message_id)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    msg = bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
    player.currentmessage = msg
    player.messagetoedit = msg   


@bot.callback_query_handler(func=pistol_callback)
def pistol_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    player.destroycamera = True            
    player.ready = True
    player.lastloc = player.location
    medit('Выбрано действие: уничтожение вражеских камер.', c.message.chat.id, c.message.message_id)
    game.player_step()


@bot.callback_query_handler(func=camera_callback)
def camera_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    player.items.remove('camera')
    player.cameras.append(player.location)
    game.texttohistory+='Шпион '+player.name+' устанавливает камеру в локацию '+loctoname(player.location)+'!\n\n'
    medit('Вы установили камеру в вашей текущей локации ('+loctoname(player.location)+')!', c.message.chat.id, c.message.message_id)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    msg = bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
    player.currentmessage = msg
    player.messagetoedit = msg   


@bot.callback_query_handler(func=flash_callback)
def flash_callback_handler(c):
    kb=types.InlineKeyboardMarkup()
    player = game_data.is_player_playing(c.from_user.id)
    for location in player.nearby_locations:
        if location != player.location:
            kb.add(types.InlineKeyboardButton(text=loctoname(location), callback_data='flash '+location))
        else:
            kb.add(types.InlineKeyboardButton(text='Эта локация', callback_data='flash '+location))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
    medit('Выберите, куда будете кидать флэшку.', c.message.chat.id, c.message.message_id, reply_markup=kb)
    

@bot.callback_query_handler(func=flash_to_callback)
def flash_to_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    location=c.data.split(' ')[1]
    player.items.remove('flash')
    game.flashed.append(location)

    medit('Вы бросили флэшку в локацию: '+loctoname(location)+'.', c.message.chat.id, c.message.message_id)
    game.texttohistory+='Шпион '+player.name+' бросил флэшку в локацию '+loctoname(location)+'!\n\n'
    
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
    player.currentmessage = msg
    player.messagetoedit = msg


@bot.callback_query_handler(func=costume_callback)
def costume_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    kb=types.InlineKeyboardMarkup()
    player.items.remove('costume')
    player.silent = True
    game.texttohistory+='Шпион '+player.name+' надел сапоги ниндзя!\n\n'
    medit('Вы надели сапоги ниндзя! На этом ходу ваши передвижения не будут услышаны.', c.message.chat.id, c.message.message_id)
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
    player.currentmessage = msg
    player.messagetoedit = msg


@bot.callback_query_handler(func=shockmine_callback)
def shockmine_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    kb=types.InlineKeyboardMarkup()
    player.items.remove('shockmine')
    game.texttohistory += 'Охранник '+player.name+' установил мину-шокер в локации '+loctoname(player.location)+'!\n\n'
    medit('Вы устанавливаете мину-шокер.', c.message.chat.id, c.message.message_id)
    player.ready = True
    player.lastloc = player.location
    game.player_step()
    game.shockminelocs.append(player.location)


@bot.callback_query_handler(func=back_callback)
def back_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    medit('Выберите действие.', c.message.chat.id, c.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=treasure_info_callback)
def treasure_info_callback_handler(c):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    stealed = False
    text='Сокровищница:\n'
    for other_player in game.players:
        if other_player.treasure:
            stealed = True
        if other_player.location=='treasure' and other_player.id != player.id:
            text += other_player.name+' был замечен на камере!\n'
    text += 'В комнате нет сокровища!!!' if stealed else 'Сокровище на месте.'              
    bot.answer_callback_query(c.id,text, show_alert=True)               
        
print('7777')
bot.polling(none_stop=True,timeout=600)
