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
    game_data.games.update(creategame(m.chat.id, 2))
    bot.send_message(m.chat.id, 'Игра в режиме 1х1 началась! Жмите /join, чтобы присоединиться! До отмены игры 5 минут.')
    t=threading.Timer(300,cancelgame,args=[m.chat.id])
    t.start()
    game_data.games[m.chat.id]['timer']=t


@bot.message_handler(commands=['creategame2x2'], func=game_not_exists)
def creategame_2x2_handler(m):
    game_data.games.update(creategame(m.chat.id, 4))
    bot.send_message(m.chat.id, 'Игра в режиме 2х2 началась! Жмите /join, чтобы присоединиться! До отмены игры 5 минут.')
    t=threading.Timer(300,cancelgame,args=[m.chat.id])
    t.start()
    game_data.games[m.chat.id]['timer']=t


@bot.message_handler(commands=['cancel'], func=game_exists)
def cancelgamee(m):
    game_data.games[m.chat.id]['timer'].cancel()
    del game_data.games[m.chat.id]
    bot.send_message(m.chat.id, 'Игра была удалена.')
       
 
@bot.message_handler(commands=['surrender'], func=game_exists)
def surrender_handler(m):
    player=None
    for ids in game_data.games[m.chat.id]['players']:
        if game_data.games[m.chat.id]['players'][ids]['id']==m.from_user.id:
            player=game_data.games[m.chat.id]['players'][ids]
    if player!=None:
        player['disarmed']=1
        if player['role']=='spy':
            text='В шпионе '+player['name']+' проснулась совесть, и он сдался.'
        else:
            text=player['name']+' сдался!'
        bot.send_message(m.chat.id, text)
     
@bot.message_handler(commands=['map'])
def map_handler(m):
    bot.send_photo(m.chat.id, constants.map_file_id)

@bot.message_handler(commands=['startgame'])
def startgame_handler(m):
    if m.chat.id in game_data.games:
      if game_data.games[m.chat.id]['started']==0:
        if len(game_data.games[m.chat.id]['players'])==game_data.games[m.chat.id]['maxplayers']:
            game_data.games[m.chat.id]['started']=1
            game_data.games[m.chat.id]['timer'].cancel()
            begin(m.chat.id)
        else:
            bot.send_message(m.chat.id, 'Недостаточно игроков!')
    
@bot.message_handler(commands=['join'])
def join_handler(m):
  try:
    no=0
    if m.chat.id in game_data.games:
      if game_data.games[m.chat.id]['started']==0:
        for ids in game_data.games[m.chat.id]['players']:
            if game_data.games[m.chat.id]['players'][ids]['id']==m.from_user.id:
                no=1
    if len(game_data.games[m.chat.id]['players'])<game_data.games[m.chat.id]['maxplayers']:
      if no==0:
        try:
            bot.send_message(m.from_user.id, 'Вы успешно присоединились!')
            game_data.games[m.chat.id]['players'].update(createplayer(m.from_user.id, m.from_user.first_name, m.chat.id))
            bot.send_message(m.chat.id, m.from_user.first_name+' присоединился!')
        except:
            bot.send_message(m.chat.id, 'Для начала напишите боту @Spy_VS_Security_Bot что-нибудь!')
      else:
           bot.send_message(m.chat.id, 'Вы уже в игре!')
    else:
        bot.send_message(m.chat.id, 'Достигнуто максимальное число игроков!')
  except:
    pass
 
def testturn(id):
    i=0
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['ready']==1:
           i+=1
    if i==len(game_data.games[id]['players']):
           game_data.games[id]['gametimer'].cancel()
           endturn(id)
            
def begin(id):
    securityitems=['glasses','pistol','tizer', 'glasses','shockmine']
    spyitems=['camera','camera','camera','flash','costume', 'flash','mineremover']
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['spies']>game_data.games[id]['security']:
            game_data.games[id]['players'][ids]['role']='security'
            game_data.games[id]['security']+=1
            bot.send_message(game_data.games[id]['players'][ids]['id'], 'Вы - охранник! Ваша цель - не дать шпионам украсть сокровище!'+\
                             'Если продержитесь 25 ходов - вам на помощь приедет спецназ, и вы победите!')
        elif game_data.games[id]['spies']<game_data.games[id]['security']:
            game_data.games[id]['players'][ids]['role']='spy'
            game_data.games[id]['spies']+=1
            bot.send_message(game_data.games[id]['players'][ids]['id'], 'Вы - шпион! Ваша цель - украсть сокровище!'+\
                             'Не попадитесь на глаза охраннику и сделайте всё меньше, чем за 26 ходов, иначе проиграете!')
        elif game_data.games[id]['spies']==game_data.games[id]['security']:
            x=random.choice(['spy','security'])
            game_data.games[id]['players'][ids]['role']=x
            if x=='spy':
                game_data.games[id]['spies']+=1
                bot.send_message(game_data.games[id]['players'][ids]['id'], 'Вы - шпион! Ваша цель - украсть сокровище!'+\
                             'Не попадитесь на глаза охраннику и сделайте всё меньше, чем за 26 ходов, иначе проиграете!')
            elif x=='security':
                game_data.games[id]['security']+=1
                bot.send_message(game_data.games[id]['players'][ids]['id'], 'Вы - охранник! Ваша цель - не дать шпионам украсть сокровище! '+\
                             'Если продержитесь 25 ходов - вам на помощь приедет спецназ, и вы победите!')
                
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['role']=='security':
            game_data.games[id]['players'][ids]['items']=securityitems
            game_data.games[id]['players'][ids]['location']='stock'
        elif game_data.games[id]['players'][ids]['role']=='spy':
            game_data.games[id]['players'][ids]['items']=spyitems
            game_data.games[id]['players'][ids]['location']='spystart'
            
    for ids in game_data.games[id]['players']:
        game_data.games[id]['players'][ids]['lastloc']=game_data.games[id]['players'][ids]['location']
        sendacts(game_data.games[id]['players'][ids])
    bot.send_message(id, 'Игра начинается! Охранники, шпионы - по позициям!')
        
    t=threading.Timer(90, endturn, args=[id])
    t.start()
    game_data.games[id]['gametimer']=t
        
def endturn(id):
    texttohistory=''
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['role']=='spy':
            g='шпиона'
        else:
            g='охранника'
        game_data.games[id]['texttohistory']+='Перемещение '+g+' '+game_data.games[id]['players'][ids]['name']+':\n'+loctoname(game_data.games[id]['players'][ids]['lastloc'])+\
        '\n |\n'+'v\n'+loctoname(game_data.games[id]['players'][ids]['location'])+'\n\n'
        if game_data.games[id]['players'][ids]['ready']==0:
            try:
              medit('Время вышло!',game_data.games[id]['players'][ids]['messagetoedit'].chat.id, game_data.games[id]['players'][ids]['messagetoedit'].message_id)
              game_data.games[id]['texttohistory']+=game_data.games[id]['players'][ids]['name']+' АФК!\n\n'
            except:
                 pass
            game_data.games[id]['players'][ids]['lastloc']=game_data.games[id]['players'][ids]['location']
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['moving']==0:
            game_data.games[id]['players'][ids]['lastloc']=game_data.games[id]['players'][ids]['location']
    text=''        
    for ids in game_data.games[id]['players']:
        player=game_data.games[id]['players'][ids]
        if player['setupcamera']==1:
            player['cameras'].append(player['location'])
            game_data.games[id]['texttohistory']+='Шпион '+player['name']+' устанавливает камеру в локацию '+loctoname(player['location'])+'!\n\n'
        if player['role']=='security' and player['location'] in game_data.games[id]['flashed']:
          if player['glasses']<=0:
            player['flashed']=1  
            game_data.games[id]['texttohistory']+='Охранник '+player['name']+' был ослеплен флэшкой!\n\n'
            bot.send_message(player['id'],'Вы были ослеплены флэшкой! В следующий ход вы не сможете действовать.')
          else:
            game_data.games[id]['texttohistory']+='Охранник '+player['name']+' избежал ослепления!\n\n'
            bot.send_message(player['id'],'Очки спасли вас от флэшки!')
        if player['role']=='spy' and player['location'] in game_data.games[id]['shockminelocs']:
          if player['removemine']==0:
            player['shocked']=1
            game_data.games[id]['texttohistory']+='Шпион '+player['name']+' наступил на мину-шокер в локации '+loctoname(player['location'])+'!\n\n'
            bot.send_message(player['id'],'Вы наступили на мину-шокер! В следующий ход вы не сможете действовать.')
          else:
            game_data.games[id]['texttohistory']+='Шпион '+player['name']+' обезвредил мину-шокер в локации '+loctoname(player['location'])+'!\n\n'
            bot.send_message(player['id'],'Вы обезвредили мину-шокер!')
          try:
              game_data.games[id]['shockminelocs'].remove(player['location'])
          except:
              pass
            
        if player['destroycamera']==1:
            if player['flashed']!=1:
                for idss in game_data.games[id]['players']:
                    if player['location'] in game_data.games[id]['players'][idss]['cameras']:
                        game_data.games[id]['players'][idss]['cameras'].remove(player['location'])
                        text+='Охранник уничтожил камеру шпиона в локации: '+loctoname(player['location'])+'!\n'
                        game_data.games[id]['texttohistory']+='Охранник '+player['name']+' уничтожил камеру в локации '+loctoname(player['location'])+'!\n\n'
            else:
                bot.send_message(player['id'],'Вы были ослеплены! Камеры шпионов обнаружить не удалось.')
                game_data.games[id]['texttohistory']+='Охранник '+player['name']+' был ослеплён! Ему не удалось обнаружить камеры.\n\n'
                                                                                                                        
                
        if player['stealing']==1 and player['treasure']==0:
            player['treasure']=1
            game_data.games[id]['texttohistory']+='Шпион '+player['name']+' украл сокровище!\n\n'
            bot.send_message(player['id'],'Вы успешно украли сокровище! Теперь выберитесь отсюда (Выход в той же локации, где вы начинали игру).')
        
        if player['role']=='security':
            for idss in game_data.games[id]['players']:
                if player['location']==game_data.games[id]['players'][idss]['location'] and game_data.games[id]['players'][idss]['role']!='security':
                  if player['flashed']==0 and game_data.games[id]['players'][idss]['disarmed']==0:
                    game_data.games[id]['players'][idss]['disarmed']=1
                    text+='Охранник нейтрализовал шпиона в локации: '+loctoname(player['location'])+'!\n'
                    game_data.games[id]['texttohistory']+='Охранник '+player['name']+' нейтрализовал шпиона в локации '+loctoname(player['location'])+'!\n\n'
                    bot.send_message(player['id'],'Вы нейтрализовали шпиона!')
                  else:
                    bot.send_message(game_data.games[id]['players'][idss]['id'], 'В вашей текущей локации вы видите ослеплённого охранника! Поторопитесь уйти...') 
                     
        if player['role']=='security' and player['flashed']==0 and player['lastloc']!=player['location']:
            for idss in game_data.games[id]['players']: 
                if game_data.games[id]['players'][idss]['lastloc']==player['location'] and game_data.games[id]['players'][idss]['location']==player['lastloc'] and \
                game_data.games[id]['players'][idss]['disarmed']==0:
                    text+='Шпион и охранник столкнулись в коридоре! Шпион нейтрализован!\n'
                    game_data.games[id]['texttohistory']+='Охранник '+player['name']+' нейтрализовал шпиона по пути в локацию '+loctoname(player['location'])+'!\n\n'
                    bot.send_message(player['id'],'Вы нейтрализовали шпиона!')
                    game_data.games[id]['players'][idss]['disarmed']=1
        
        loclist=[]
        for idss in nearlocs[player['location']]:
            loclist.append(idss)
        loclist.append(player['location'])
            
        locs=''
        for idss in loclist:
            if idss!=player['location']:
                locs+=loctoname(idss)+'\n'
        hearinfo='Прослушиваемые вами локации в данный момент:\n'+locs+'\n' 
        for idss in game_data.games[id]['players']:
            if game_data.games[id]['players'][idss]['location'] in loclist and \
            game_data.games[id]['players'][idss]['location']!=game_data.games[id]['players'][idss]['lastloc'] and \
            game_data.games[id]['players'][idss]['silent']!=1 and player['role']!=game_data.games[id]['players'][idss]['role']:
                if game_data.games[id]['players'][idss]['location']!=player['location']:
                    hearinfo+='Вы слышите движение в локации: '+loctoname(game_data.games[id]['players'][idss]['location'])+'!\n'
                else:
                    hearinfo+='Вы слышите движение в вашей текущей локации!!\n'
                    
        bot.send_message(player['id'],hearinfo)
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['treasure']==1 and \
        game_data.games[id]['players'][ids]['disarmed']==0 and \
        game_data.games[id]['players'][ids]['location']=='spystart':
            game_data.games[id]['treasurestealed']=1
                    
    if text=='':
        text='Ничего необычного...'
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='История '+str(game_data.games[id]['turn'])+' хода', callback_data='history '+datagen(game_data.games[id],game_data.games[id]['texttohistory'])))
    bot.send_message(id, 'Ход '+str(game_data.games[id]['turn'])+'. Ситуация в здании:\n\n'+text, reply_markup=kb)
        
    endgame=0    
    spyalive=0    
    for ids in game_data.games[id]['players']:
        if game_data.games[id]['players'][ids]['disarmed']==0 and game_data.games[id]['players'][ids]['role']=='spy':
            spyalive+=1
    if spyalive<=0:
        endgame=1
        winner='security'
    if game_data.games[id]['turn']>=25:
        endgame=1
        winner='security'
        game_data.games[id]['texttohistory']+='Победа охраны по причине: прошло 25 ходов!\n\n'
    if game_data.games[id]['treasurestealed']==1:
        endgame=1
        winner='spy'
    if endgame==0:
        for ids in game_data.games[id]['players']:
            if game_data.games[id]['players'][ids]['flashed']==0 and game_data.games[id]['players'][ids]['shocked']==0:
              if game_data.games[id]['players'][ids]['disarmed']==0:            
                bot.send_photo(game_data.games[id]['players'][ids]['id'], 'AgADAgAD06sxG7wwGEqukXmiDU8iF5zPtw4ABCn0Y60xUVfWDfgEAAEC')
                sendacts(game_data.games[id]['players'][ids])
              else:
                game_data.games[id]['players'][ids]['ready']=1
            else:
                game_data.games[id]['players'][ids]['lastloc']=game_data.games[id]['players'][ids]['location']
                game_data.games[id]['players'][ids]['ready']=1
        t=threading.Timer(90, endturn, args=[id])
        t.start()
        game_data.games[id]['gametimer']=t
        game_data.games[id]['turn']+=1
        game_data.games[id]['flashed']=[]
        game_data.games[id]['texttohistory']=''
        for ids in game_data.games[id]['players']:
            if game_data.games[id]['players'][ids]['flashed']==0 and game_data.games[id]['players'][ids]['shocked']==0:
              game_data.games[id]['players'][ids]['ready']=0
            game_data.games[id]['players'][ids]['stealing']=0
            if game_data.games[id]['players'][ids]['glasses']>0:
                game_data.games[id]['players'][ids]['glasses']-=1
            game_data.games[id]['players'][ids]['setupcamera']=0
            game_data.games[id]['players'][ids]['moving']=0
            game_data.games[id]['players'][ids]['destroycamera']=0
            game_data.games[id]['players'][ids]['silent']=0
            if game_data.games[id]['players'][ids]['flashed']>0:
                game_data.games[id]['players'][ids]['flashed']-=1
            if game_data.games[id]['players'][ids]['shocked']>0:
                game_data.games[id]['players'][ids]['shocked']-=1
            game_data.games[id]['players'][ids]['removemine']=0
    else:
        if winner=='security':
            bot.send_message(id, 'Победа охраны!')
            stats.update_one({},{'$inc':{'securitywins':1}})
        else:
            bot.send_message(id, 'Победа шпионов!')
            stats.update_one({},{'$inc':{'spywins':1}})
        try:
            del game_data.games[id]
        except:
            pass

                   
def datagen(game,text):
    i=0
    word=''
    while i<4:
        word+=random.choice(symbollist)
        i+=1
    if word in history:
        return datagen(game,text)
    else:
        history.update({word:text})
        return word
  
                                                                
def sendacts(player):  
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
    if player['role']=='spy':
        kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
    if player['role']=='security':
        kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
    kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
    if player['flashed']==0:
      msg=bot.send_message(player['id'],'Выберите действие.',reply_markup=kb)
      player['messagetoedit']=msg
    else:
      player['ready']=1
               
     
               
def cancelgame(id):
    try:
        del game_data.games[id]
        bot.send_message(id, 'Игра была отменена!')
    except:
        pass
    

def medit(message_text,chat_id, message_id,reply_markup=None,parse_mode='Markdown'):
    return bot.edit_message_text(chat_id=chat_id,message_id=message_id,text=message_text,reply_markup=reply_markup,
                                 parse_mode=parse_mode)


@bot.callback_query_handler(func=lambda call:True)
def inline(call):
 try:
  if 'history' in call.data:
    x=call.data.split(' ')
    x=x[1]
    yes=0
    for ids in game_data.games:
        for idss in game_data.games[ids]['players']:
            if game_data.games[ids]['players'][idss]['id']==call.from_user.id:
                yes=1
    if yes==0:
      try:
         print(history)
         print(x)
         aa=history[x]
         try:
             bot.send_message(call.from_user.id,history[x])
         except:
             bot.send_message(call.message.chat.id, call.from_user.first_name+', напишите боту в личку, чтобы я мог отправлять вам историю боя!')
      except:
         medit('История этой игры больше недоступна!',call.message.chat.id,call.message.message_id)
    else:
        bot.send_message(call.message.chat.id, call.from_user.first_name+', нельзя смотреть историю, находясь в игре!')
        
  yes=0
  for ids in game_data.games:
    for idss in game_data.games[ids]['players']:
        if game_data.games[ids]['players'][idss]['id']==call.from_user.id and game_data.games[ids]['players'][idss]['ready']==0:
            yes=1
            player=game_data.games[ids]['players'][idss]
  if yes==1:
    kb=types.InlineKeyboardMarkup()
    if call.data=='move':
        for ids in nearlocs[player['location']]:
            kb.add(types.InlineKeyboardButton(text=loctoname(ids), callback_data='move '+ids))
        kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))    
        medit('Куда вы хотите направиться?',call.message.chat.id,call.message.message_id, reply_markup=kb)
        
    elif call.data=='items':
        kb=types.InlineKeyboardMarkup()
        for ids in player['items']:
            x=itemtoname(ids)
            if x!=None:
                kb.add(types.InlineKeyboardButton(text=x, callback_data=ids))
        kb.add(types.InlineKeyboardButton(text='Назад', callback_data='back'))
        medit('Выберите предмет.', call.message.chat.id, call.message.message_id, reply_markup=kb)
        
    elif call.data=='camerainfo':
        if player['role']=='spy':
            text=''
            for ids in player['cameras']:
                text+=loctoname(ids)+':\n'
                for idss in game_data.games[player['chatid']]['players']:
                    if game_data.games[player['chatid']]['players'][idss]['location']==ids and game_data.games[player['chatid']]['players'][idss]['id']!=player['id']:
                        text+=game_data.games[player['chatid']]['players'][idss]['name']+' был замечен на камерах!\n'
            if text=='':
                text='У вас не установлено ни одной камеры!'
            bot.answer_callback_query(call.id,text, show_alert=True)
            
    elif call.data=='wait':
        player['ready']=1
        medit('Вы пропускаете ход. Ожидайте следующего хода...',call.message.chat.id, call.message.message_id)
        player['lastloc']=player['location']
        testturn(player['chatid'])
        
    elif call.data=='mineremover':
        if 'mineremover' in player['items']:
            kb=types.InlineKeyboardMarkup()
            player['items'].remove('mineremover')
            player['removemine']=1
            game_data.games[player['chatid']]['texttohistory']+='Шпион '+player['name']+' готовится обезвреживать мину-шокер.\n\n'
            medit('Вы готовитесь обезвредить мину-шокер в своей следующей локации.', call.message.chat.id, call.message.message_id)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player['role']=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player['role']=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player['id'],'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player['messagetoedit']=msg     
        
        
    elif 'move' in call.data:
        x=call.data.split(' ')
        x=x[1]
        if x in nearlocs[player['location']]:
            player['lastloc']=player['location']
            medit('Вы перемещаетесь в локацию: '+loctoname(x)+'.',call.message.chat.id, call.message.message_id)
            player['location']=x
            player['ready']=1
            player['moving']=1
            if player['role']=='spy' and player['location']=='treasure':
                player['stealing']=1
            testturn(player['chatid'])
            
            
    elif call.data=='glasses':
        if 'glasses' in player['items']:
            player['items'].remove('glasses')
            player['glasses']=1
            game_data.games[player['chatid']]['texttohistory']+='Охранник '+player['name']+' надел очко!\n\n'
            medit('Вы успешно надели очки! На этот ход вы защищены от флэшек.', call.message.chat.id, call.message.message_id)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player['role']=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player['role']=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player['id'],'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player['messagetoedit']=msg     
            
    elif call.data=='pistol':
        if 'pistol' in player['items']:
            player['destroycamera']=1
            player['ready']=1
            player['lastloc']=player['location']
            testturn(player['chatid'])
            medit('Выбрано действие: уничтожение вражеских камер.', call.message.chat.id, call.message.message_id)
            
    elif call.data=='camera':
        if 'camera' in player['items']:
            player['items'].remove('camera')
            player['cameras'].append(player['location'])
            game_data.games[player['chatid']]['texttohistory']+='Шпион '+player['name']+' устанавливает камеру в локацию '+loctoname(player['location'])+'!\n\n'
            medit('Вы установили камеру в вашей текущей локации ('+loctoname(player['location'])+')!', call.message.chat.id, call.message.message_id)
            kb=types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player['role']=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player['role']=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player['id'],'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player['messagetoedit']=msg   
            
            
    elif call.data=='flash':
        if 'flash' in player['items']:
            locs=[]
            for ids in nearlocs[player['location']]:
                locs.append(ids)
            locs.append(player['location'])
            for ids in locs:
                if ids!=player['location']:
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
        game_data.games[player['chatid']]['flashed'].append(location)
        medit('Вы бросили флэшку в локацию: '+loctoname(location)+'.', call.message.chat.id, call.message.message_id)
        game_data.games[player['chatid']]['texttohistory']+='Шпион '+player['name']+' бросил флэшку в локацию '+loctoname(location)+'!\n\n'
        kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
        if player['role']=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
        if player['role']=='security':
            kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
        kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
        msg=bot.send_message(player['id'],'Выберите действие.', reply_markup=kb)
        player['currentmessage']=msg
        player['messagetoedit']=msg
        
    elif call.data=='costume':
        if 'costume' in player['items']:
            kb=types.InlineKeyboardMarkup()
            player['items'].remove('costume')
            player['silent']=1
            game_data.games[player['chatid']]['texttohistory']+='Шпион '+player['name']+' надел сапоги ниндзя!\n\n'
            medit('Вы надели сапоги ниндзя! На этом ходу ваши передвижения не будут услышаны.', call.message.chat.id, call.message.message_id)
            kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
            if player['role']=='spy':
                kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
            if player['role']=='security':
                kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
            kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
            msg=bot.send_message(player['id'],'Выберите действие.', reply_markup=kb)
            player['currentmessage']=msg
            player['messagetoedit']=msg
        
    elif call.data=='shockmine':
        if 'shockmine' in player['items']:
            kb=types.InlineKeyboardMarkup()
            player['items'].remove('shockmine')
            game_data.games[player['chatid']]['texttohistory']+='Охранник '+player['name']+' установил мину-шокер в локации '+loctoname(player['location'])+'!\n\n'
            medit('Вы устанавливаете мину-шокер.', call.message.chat.id, call.message.message_id)
            player['ready']=1
            player['lastloc']=player['location']
            testturn(player['chatid'])
            game_data.games[player['chatid']]['shockminelocs'].append(player['location'])
            
    elif call.data=='back':
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
        if player['role']=='spy':
            kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
        if player['role']=='security':
            kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
        kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
        medit('Выберите действие.', call.message.chat.id, call.message.message_id, reply_markup=kb)
        
    elif call.data=='treasureinfo':
        stealed=0
        text='Сокровищница:\n'
        for idss in game_data.games[player['chatid']]['players']:
            if game_data.games[player['chatid']]['players'][idss]['treasure']==1:
                stealed=1
            if game_data.games[player['chatid']]['players'][idss]['location']=='treasure' and game_data.games[player['chatid']]['players'][idss]['id']!=player['id']:
                text+=game_data.games[player['chatid']]['players'][idss]['name']+' был замечен на камере!\n'
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

