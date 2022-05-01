# -*- coding: utf-8 -*-
import os
import random
import threading
from telebot import types, TeleBot
from pymongo import MongoClient
import constants
from game import game_data
from lambdas import *
from config import *

bot = TeleBot(token)

history={}

client=MongoClient(mongo_url)
db=client.spyvssecurity
stats=db.stats


symbollist=['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z',
           '1','2','3','4','5','6','7','8','9','0']


nearlocs={'spystart':['leftcorridor','rightcorridor','midcorridor'],
          'leftcorridor':['spystart','treasure','leftpass'],
          'rightcorridor':['spystart','treasure', 'rightpass'],
          'rightpass':['rightcorridor','stock'],
          'leftpass':['stock','leftcorridor'],
          'treasure':['leftcorridor','rightcorridor','stock','midcorridor'],
          'spystart':['leftcorridor','rightcorridor','midcorridor'],
          'midcorridor':['spystart','treasure'],
          'stock':['rightpass','leftpass','treasure']
}
nearlocs2={
'a1':['a2','b1'],
    'a2':['a1','a3','b2'],
    'a3':['a2','a4','b3'],
    'a4':['a3','b4'],
    'b1':['a1','b2','c1'],
    'b2':['b1','a2','b3','c2'],
    'b3':['b2','a3','b4','c3'],
    'b4':['b3','a4','c4'],
    'c1':['b1','c2','d1'],
    'c2':['c1','b2','c3','d2'],
    'c3':['c2','b3','c4','d3'],
    'c4':['c3','b4','d4'],
    'd1':['c1','d2','e1'],
    'd2':['d1','c2','d3','e2'],
    'd3':['d2','c3','d4','e3'],
    'd4':['d3','c4','e4'],
    'e1':['d1','e2'],
    'e2':['e1','d2','e3'],
    'e3':['e2','d3','e4'],
    'e4':['e3','d4']
}


@bot.message_handler(commands=['stats'])
def stats_handler(m):
    x=stats.find_one({})
    if x==None:
        bot.send_message(m.chat.id, 'Ошибка статистики.')
        return
    text='Общая статистика:\nШпионы выигрывали: '+str(x['spywins'])+' раз(а)\nОхранники выигрывали: '+str(x['securitywins'])+' раз(а)'
    bot.send_message(m.chat.id, text)


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
    bot.send_photo(m.chat.id, constants.map_file_id)

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
        
 
def testturn(chat_id):
    game = game_data.get_game(chat_id)
    ready_players = [player for player in game.players if player.ready]
    if len(ready_players) == len(game.players):
        game.gametimer.cancel()
        endturn(chat_id)
        
def endturn(id):
    game = game_data.get_game(chat_id)
    texttohistory=''

    for player in game.players:
        if player.role == 'spy':
            g='шпиона'
        else:
            g='охранника'
        game.texttohistory += f'Перемещение {g} {player.name}:\n{loctoname(player.lastloc)}\n |\nv\n{loctoname(player.location)}'

        if not player.ready:
            try:
              medit('Время вышло!', player.messagetoedit.chat.id, player.messagetoedit.message_id)
              game.texttohistory += player.name+' АФК!\n\n'
            except:
                 pass
            player.lastloc = player.location

    for player in game.players:
        if not player.moving:
            player.lastloc = player.location

    text=''        

    for player in game.players:
        if player.setupcamera:
            player.cameras.append(player.location)
            game.texttohistory+=f'Шпион {player.name} устанавливает камеру в локацию {loctoname(player.location)}!\n\n'
        if player.role == 'security' and player.location in game.flashed:
            if player.glasses <= 0:
               player.flashed = True 
               game.texttohistory += 'Охранник '+player.name+' был ослеплен флэшкой!\n\n'
               bot.send_message(player.id, 'Вы были ослеплены флэшкой! В следующий ход вы не сможете действовать.')
            else:
               game.texttohistory+='Охранник '+player.name+' избежал ослепления!\n\n'
               bot.send_message(player.id, 'Очки спасли вас от флэшки!')
        if player.role == 'spy' and player.location in game.shockminelocs:
            if not player.removemine:
                player.shocked = True
                game.texttohistory+='Шпион '+player.name+' наступил на мину-шокер в локации '+loctoname(player.location)+'!\n\n'
                bot.send_message(player.id,'Вы наступили на мину-шокер! В следующий ход вы не сможете действовать.')
            else:
                game.texttohistory+='Шпион '+player.name+' обезвредил мину-шокер в локации '+loctoname(player.location)+'!\n\n'
                bot.send_message(player.id,'Вы обезвредили мину-шокер!')
            try:
                game.shockminelocs.remove(player.location)
            except:
                pass
            
        if player.destroycamera:
            if not player.flashed:
                for other_player in game.players:
                    if player.location in other_player.cameras:
                        other_player.cameras.remove(player.location)
                        text+='Охранник уничтожил камеру шпиона в локации: '+loctoname(player.location)+'!\n'
                        game.texttohistory+='Охранник '+player.name+' уничтожил камеру в локации '+loctoname(player.location)+'!\n\n'
            else:
                bot.send_message(player.id,'Вы были ослеплены! Камеры шпионов обнаружить не удалось.')
                game.texttohistory+='Охранник '+player.name+' был ослеплён! Ему не удалось обнаружить камеры.\n\n'
                                                                                                                        
                
        if player.stealing and not player.treasure:
            player.treasure = True
            game.texttohistory+='Шпион '+player.name+' украл сокровище!\n\n'
            bot.send_message(player.id,'Вы успешно украли сокровище! Теперь выберитесь отсюда (Выход в той же локации, где вы начинали игру).')
        
        if player.role=='security':
            for other_player in game.players:
                if player.location == other_player.location and other_player.role != 'security':
                    if not player.flashed and not other_player.disarmed:
                        other_player.disarmed = True
                        text+='Охранник нейтрализовал шпиона в локации: '+loctoname(player.location)+'!\n'
                        game.texttohistory+='Охранник '+player.name+' нейтрализовал шпиона в локации '+loctoname(player.location)+'!\n\n'
                        bot.send_message(player.id,'Вы нейтрализовали шпиона!')
                    else:
                        bot.send_message(other_player.id, 'В вашей текущей локации вы видите ослеплённого охранника! Поторопитесь уйти...') 
                     
        if player.role=='security' and player.flashed==0 and player.lastloc != player.location:
            for other_player in game.players: 
                if other_player.lastloc==player.location and other_player.location==player.lastloc and \
                other_player.disarmed==0:
                    text+='Шпион и охранник столкнулись в коридоре! Шпион нейтрализован!\n'
                    game.texttohistory+='Охранник '+player.name+' нейтрализовал шпиона по пути в локацию '+loctoname(player.location)+'!\n\n'
                    bot.send_message(player.id,'Вы нейтрализовали шпиона!')
                    other_player.disarmed=1
            
        locs = ''
        for near_location in player.nearby_locations:
            if near_location != player.location:
                locs += loctoname(near_location)+'\n'
        hearinfo='Прослушиваемые вами локации в данный момент:\n'+locs+'\n' 
        for other_player in game.players:
            if player.can_hear(other_player):
                if other_playerlocation != player.location:
                    hearinfo+='Вы слышите движение в локации: '+loctoname(other_player.location)+'!\n'
                else:
                    hearinfo+='Вы слышите движение в вашей текущей локации!!\n'
        bot.send_message(player.id, hearinfo)

    for player in game.players:
        if player.treasure and not player.disarmed and player.location=='spystart':
            game.treasurestealed = True
                    
    if not text:
        text = 'Ничего необычного...'
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='История '+str(game.turn)+' хода', callback_data='history '+datagen(game.texttohistory)))
    bot.send_message(id, 'Ход '+str(game.turn)+'. Ситуация в здании:\n\n'+text, reply_markup=kb)
        
    endgame=0    
    spyalive=0    
    for player in game.players:
        if not player.disarmed and player.role=='spy':
            spyalive += 1
    if spyalive<=0:
        endgame = True
        winner='security'
    if game.turn>=25:
        endgame = True
        winner='security'
        game.texttohistory+='Победа охраны по причине: прошло 25 ходов!\n\n'
    if game.treasurestealed:
        endgame = True
        winner='spy'
    if not endgame:
        for player in game.players:
            if not player.flashed and not player.shocked:
                if not player.disarmed:            
                    bot.send_photo(player.id, map_file_id)
                    sendacts(player)
                else:
                    player.ready = True
            else:
                player.lastloc = player.location
                player.ready = True

        game.gametimer = threading.Timer(90, endturn, args=[id])
        game.gametimer.start()

        game.turn+=1
        game.flashed=[]
        game.texttohistory=''
        for player in game.players:
            if not player.flashed and not player.shocked:
                player.ready = False
            player.stealing = False
            if player.glasses>0:
                player.glasses-=1
            player.setupcamera            
            player.moving = False
            player.destroycamera            
            player.silent = False
            if player.flashed>0:
                player.flashed-=1
            if player.shocked>0:
                player.shocked-=1
            player.removemine    
    else:
        if winner=='security':
            bot.send_message(game.id, 'Победа охраны!')
            stats.update_one({},{'$inc':{'securitywins':1}})
        else:
            bot.send_message(game.id, 'Победа шпионов!')
            stats.update_one({},{'$inc':{'spywins':1}})
        try:
            del game
        except:
            pass

                   
def datagen(text):
    word=''
    for i in range(4):
        word+=random.choice(symbollist)
    if word in history:
        return datagen(text)
    else:
        history.update({word:text})
        return word
  
                                                                
def sendacts(player):  
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player.role=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player.role=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    if not player.flashed:
        player.messagetoedit = bot.send_message(player.id,'Выберите действие.',reply_markup=kb)
    else:
        player.ready = True
               
              
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
def history_callback_handler(call):
    history_id = call.data.split(' ')[1]
    yes=0
    for game in game_data.games:
        for player in game.players:
            if player.id == call.from_user.id:
                bot.send_message(call.message.chat.id, call.from_user.first_name+', нельзя смотреть историю, находясь в игре!')
                return

    if history_id not in history:
        medit('История этой игры больше недоступна!',call.message.chat.id,call.message.message_id)
        return

    try:
        bot.send_message(call.from_user.id, history[history_id])
    except:
        bot.send_message(call.message.chat.id, call.from_user.first_name+', напишите боту в личку, чтобы я мог отправлять вам историю боя!')


@bot.callback_query_handler(func=move_callback)
def move_callback_handler(call):
    kb = types.InlineKeyboardMarkup()
    for near_location in nearlocs[player.location]:
            kb.add(types.InlineKeyboardButton(text=loctoname(near_location), callback_data='move '+near_location))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))    
    medit('Куда вы хотите направиться?',call.message.chat.id,call.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=items_callback)
def items_callback_handler(call):
    kb = types.InlineKeyboardMarkup()
    for item in player.items:
        item_name = itemtoname(item)
        if item_name:
            kb.add(types.InlineKeyboardButton(text=item_name, callback_data=item))
    kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
    medit('Выберите предмет.', call.message.chat.id, call.message.message_id, reply_markup=kb)


@bot.callback_query_handler(func=camerainfo_callback)
def camerainfo_callback_handler(call):
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
        bot.answer_callback_query(call.id,text, show_alert=True)


@bot.callback_query_handler(func=wait_callback)
def wait_callback_handler(call):
    player = game_data.is_player_playing(c.from_user.id)
    player.ready = True
    medit('Вы пропускаете ход. Ожидайте следующего хода...',call.message.chat.id, call.message.message_id)
    player.lastloc = player.location
    testturn(player.chatid)


@bot.callback_query_handler(func=mineremover_callback)
def mineremover_callback_handler(call):
    player = game_data.is_player_playing(c.from_user.id)
    game = player.game

    
    player.items.remove('mineremover')
    player.removemine = True            
    game.texttohistory+='Шпион '+player.name+' готовится обезвреживать мину-шокер.\n\n'
    medit('Вы готовитесь обезвредить мину-шокер в своей следующей локации.', call.message.chat.id, call.message.message_id)

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


@bot.callback_query_handler(func=lambda call:True)
def inline(call):
 try:
  if True:
    kb=types.InlineKeyboardMarkup()
               
        
    elif 'move' in call.data:
        x=call.data.split(' ')
        x=x[1]
        if x in nearlocs[player.location]:
            player.lastloc=player.location
            medit('Вы перемещаетесь в локацию: '+loctoname(x)+'.',call.message.chat.id, call.message.message_id)
            player.location=x
            player.ready=1
            player.moving=1
            if player.role=='spy' and player.location=='treasure':
                player['stealing']=1
            testturn(player['chatid'])
            
            
    elif call.data=='glasses':
        if 'glasses' in player['items']:
            player['items'].remove('glasses')
            player.glasses=1
            game_data.games[player['chatid']].texttohistory+='Охранник '+player.name+' надел очко!\n\n'
            medit('Вы успешно надели очки! На этот ход вы защищены от флэшек.', call.message.chat.id, call.message.message_id)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player.role=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player.role=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player.messagetoedit=msg     
            
    elif call.data=='pistol':
        if 'pistol' in player['items']:
            player.destroycamera            player.ready=1
            player.lastloc=player.location
            testturn(player['chatid'])
            medit('Выбрано действие: уничтожение вражеских камер.', call.message.chat.id, call.message.message_id)
            
    elif call.data=='camera':
        if 'camera' in player['items']:
            player['items'].remove('camera')
            player.cameras.append(player.location)
            game_data.games[player['chatid']].texttohistory+='Шпион '+player.name+' устанавливает камеру в локацию '+loctoname(player.location)+'!\n\n'
            medit('Вы установили камеру в вашей текущей локации ('+loctoname(player.location)+')!', call.message.chat.id, call.message.message_id)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player.role=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player.role=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player.messagetoedit=msg   
            
            
    elif call.data=='flash':
        if 'flash' in player['items']:
            locs=[]
            for ids in nearlocs[player.location]:
                locs.append(ids)
            locs.append(player.location)
            for ids in locs:
                if ids!=player.location:
                    kb.add(types.InlineKeyboardButton(text=loctoname(ids), callback_data='flash '+ids))
                else:
                    kb.add(types.InlineKeyboardButton(text='Эта локация', callback_data='flash '+ids))
            kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
            medit('Выберите, куда будете кидать флэшку.', call.message.chat.id, call.message.message_id, reply_markup=kb)
            
    elif 'flash' in call.data:
      print (call.data)
      if 'flash' in player['items']:
        kb=types.InlineKeyboardMarkup()
        x=call.data.split(' ')
        location=x[1]
        print(location)
        player['items'].remove('flash')
        game_data.games[player['chatid']].flashed.append(location)
        medit('Вы бросили флэшку в локацию: '+loctoname(location)+'.', call.message.chat.id, call.message.message_id)
        game_data.games[player['chatid']].texttohistory+='Шпион '+player.name+' бросил флэшку в локацию '+loctoname(location)+'!\n\n'
        kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
        if player.role=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
        if player.role=='security':
            kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
        kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
        msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
        player['currentmessage']=msg
        player.messagetoedit=msg
        
    elif call.data=='costume':
        if 'costume' in player['items']:
            kb=types.InlineKeyboardMarkup()
            player['items'].remove('costume')
            player['silent']=1
            game_data.games[player['chatid']].texttohistory+='Шпион '+player.name+' надел сапоги ниндзя!\n\n'
            medit('Вы надели сапоги ниндзя! На этом ходу ваши передвижения не будут услышаны.', call.message.chat.id, call.message.message_id)
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player.role=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player.role=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player.id,'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player.messagetoedit=msg
        
    elif call.data=='shockmine':
        if 'shockmine' in player['items']:
            kb=types.InlineKeyboardMarkup()
            player['items'].remove('shockmine')
            game_data.games[player['chatid']].texttohistory+='Охранник '+player.name+' установил мину-шокер в локации '+loctoname(player.location)+'!\n\n'
            medit('Вы устанавливаете мину-шокер.', call.message.chat.id, call.message.message_id)
            player.ready=1
            player.lastloc=player.location
            testturn(player['chatid'])
            game_data.games[player['chatid']].shockminelocs.append(player.location)
            
    elif call.data=='back':
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
        if player.role=='spy':
            kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
        if player.role=='security':
            kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
        kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
        medit('Выберите действие.', call.message.chat.id, call.message.message_id, reply_markup=kb)
        
    elif call.data=='treasureinfo':
        stealed=0
        text='Сокровищница:\n'
        for idss in game_data.games[player['chatid']]['players']:
            if game_data.games[player['chatid']]['players'][idss]['treasure']==1:
                stealed=1
            if game_data.games[player['chatid']]['players'][idss].location=='treasure' and game_data.games[player['chatid']]['players'][idss]['id']!=player.id:
                text+=game_data.games[player['chatid']]['players'][idss].name+' был замечен на камере!\n'
        if stealed==1:
            text+='В комнате нет сокровища!!!'
        else:
            text+='Сокровище на месте.'
        bot.answer_callback_query(call.id,text, show_alert=True)         
 except:
    pass
            
            
def loctoname(x):
    if x=='leftcorridor':
        return 'Левый коридор'
    if x=='rightcorridor':
        return 'Правый коридор'
    if x=='spystart':
        return 'Старт шпионов'
    if x=='treasure':
        return 'Комната с сокровищем'
    if x=='leftcorridor':
        return 'Левый коридор'
    if x=='leftpass':
        return 'Левый обход'
    if x=='rightpass':
        return 'Правый обход'
    if x=='antiflashroom':
        return 'Светозащитная комната'
    if x=='midcorridor':
        return 'Центральный корридор'
    if x=='stock':
        return 'Склад'
            
def itemtoname(x):
    if x=='flash':
        return 'Флэшка'
    elif x=='costume':
        return 'Сапоги ниндзя'
    elif x=='glasses':
        return 'Защитные очки'
    elif x=='pistol':
        return 'Пистолет'
    elif x=='camera':
        return 'Камера'
    elif x=='shockmine':
        return 'Мина-шокер'
    elif x=='mineremover':
        return 'Водяная бомба'
    else:
        return None
        
        

            
            
def creategame(id, x):
    return{id:{
        'chatid':id,
        'players':{},
        'turn':1,
        'spies':0,
        'security':0,
        'timer':None,
        'locs':['treasure','spystart','leftcorridor','rightcorridor','leftpass','rightpass','antiflashroom','midcorridor','stock'],
        'flashed':[],
        'treasurestealed':0,
        'gametimer':None,
        'started':0,
        'texttohistory':'',
        'shockminelocs':[],
        'maxplayers':x
          }
     }
    

def createplayer(id,name,chatid):
    return{id:{
        'id':id,
        'name':name,
        'location':None,
        'team':None,
        'items':[],
        'ready':0,
        'messagetoedit':None,
        'cameras':[],
        'chatid':chatid,
        'stealing':0,
        'glasses':0,
        'setupcamera':0,
        'destroycamera':0,
        'currentmessage':None,
        'silent':0,
        'flashed':0,
        'lastloc':None,
        'treasure':0,
        'disarmed':0,
        'moving':0,
        'shocked':0,
        'removemine':0
          }
    }


@bot.message_handler(content_types=['photo'])
def jjhgh(m):
    print(m.chat.id)
    print(m)



if True:
   print('7777')
   bot.polling(none_stop=True,timeout=600)

