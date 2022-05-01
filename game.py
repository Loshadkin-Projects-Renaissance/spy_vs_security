from constants import *
from startup import bot, types
import random
import threading

class Game:
    def __init__(self):
        self.games = {}

    def create_game(self, chat_id, player_count):
        game = GameSession(chat_id, player_count)
        self.games.update({
            chat_id: game
        })
        return game

    def get_game(self, chat_id):
        return self.games.get(chat_id)

    def is_player_playing(self, user_id):
        for game in self.games:
            game = self.games[game]
            for player in game.players:
                if player.id == user_id and not player.ready:
                    return player


class GameSession:
    def __init__(self, chat_id, player_count):
        self.id = chat_id
        self.players = []
        self.turn = 1
        self.spies = 0
        self.security = 0
        self.timer = None
        self.gametimer = None
        self.flashed = []
        self.treasurestealed = False
        self.started = False
        self.texttohistory = ''
        self.shockminelocs = []
        self.maxplayers = player_count

    def player_step(self):
        ready_players = [player for player in self.players if player.ready]
        if len(ready_players) == len(self.players):
            self.gametimer.cancel()
            self.end_turn()

    @property
    def ready_players(self):
        return [player for player in self.players if player.ready]


    def end_turn(self):
        texttohistory=''

        for player in self.players:
            g = 'шпиона' if player.role == 'spy' else 'охранника'
            self.texttohistory += f'Перемещение {g} {player.name}:\n{loctoname(player.lastloc)}\n |\nv\n{loctoname(player.location)}'

            if not player.ready:
                try:
                    medit('Время вышло!', player.messagetoedit.chat.id, player.messagetoedit.message_id)
                    self.texttohistory += player.name+' АФК!\n\n'
                except:
                    pass
                player.lastloc = player.location

        for player in self.players:
            if not player.moving:
                player.lastloc = player.location

        text=''        

        for player in self.players:
            if player.setupcamera:
                player.cameras.append(player.location)
                self.texttohistory+=f'Шпион {player.name} устанавливает камеру в локацию {loctoname(player.location)}!\n\n'
            if player.role == 'security' and player.location in self.flashed:
                if player.glasses <= 0:
                    player.flashed = True 
                    self.texttohistory += 'Охранник '+player.name+' был ослеплен флэшкой!\n\n'
                    bot.send_message(player.id, 'Вы были ослеплены флэшкой! В следующий ход вы не сможете действовать.')
                else:
                    self.texttohistory+='Охранник '+player.name+' избежал ослепления!\n\n'
                    bot.send_message(player.id, 'Очки спасли вас от флэшки!')
            if player.role == 'spy' and player.location in self.shockminelocs:
                if not player.removemine:
                    player.shocked = True
                    self.texttohistory+='Шпион '+player.name+' наступил на мину-шокер в локации '+loctoname(player.location)+'!\n\n'
                    bot.send_message(player.id,'Вы наступили на мину-шокер! В следующий ход вы не сможете действовать.')
                else:
                    self.texttohistory+='Шпион '+player.name+' обезвредил мину-шокер в локации '+loctoname(player.location)+'!\n\n'
                    bot.send_message(player.id,'Вы обезвредили мину-шокер!')
                try:
                    self.shockminelocs.remove(player.location)
                except:
                    pass
                
            if player.destroycamera:
                if not player.flashed:
                    for other_player in self.players:
                        if player.location in other_player.cameras:
                            other_player.cameras.remove(player.location)
                            text+='Охранник уничтожил камеру шпиона в локации: '+loctoname(player.location)+'!\n'
                            self.texttohistory+='Охранник '+player.name+' уничтожил камеру в локации '+loctoname(player.location)+'!\n\n'
                else:
                    bot.send_message(player.id,'Вы были ослеплены! Камеры шпионов обнаружить не удалось.')
                    self.texttohistory+='Охранник '+player.name+' был ослеплён! Ему не удалось обнаружить камеры.\n\n'
                                                                                                                            
                    
            if player.stealing and not player.treasure:
                player.treasure = True
                self.texttohistory+=f'Шпион {player.name} украл сокровище!\n\n'
                bot.send_message(player.id,'Вы успешно украли сокровище! Теперь выберитесь отсюда (Выход в той же локации, где вы начинали игру).')
            
            if player.role=='security':
                for other_player in self.players:
                    if player.location == other_player.location and other_player.role != 'security':
                        if not player.flashed and not other_player.disarmed:
                            other_player.disarmed = True
                            text+='Охранник нейтрализовал шпиона в локации: '+loctoname(player.location)+'!\n'
                            self.texttohistory+='Охранник '+player.name+' нейтрализовал шпиона в локации '+loctoname(player.location)+'!\n\n'
                            bot.send_message(player.id,'Вы нейтрализовали шпиона!')
                        else:
                            bot.send_message(other_player.id, 'В вашей текущей локации вы видите ослеплённого охранника! Поторопитесь уйти...') 
                        
            if player.role=='security' and player.flashed==0 and player.lastloc != player.location:
                for other_player in self.players: 
                    if other_player.lastloc==player.location and other_player.location==player.lastloc and \
                    other_player.disarmed==0:
                        text+='Шпион и охранник столкнулись в коридоре! Шпион нейтрализован!\n'
                        self.texttohistory+='Охранник '+player.name+' нейтрализовал шпиона по пути в локацию '+loctoname(player.location)+'!\n\n'
                        bot.send_message(player.id,'Вы нейтрализовали шпиона!')
                        other_player.disarmed=1
                
            locs = ''
            for near_location in player.nearby_locations:
                if near_location != player.location:
                    locs += loctoname(near_location)+'\n'
            hearinfo='Прослушиваемые вами локации в данный момент:\n'+locs+'\n' 
            for other_player in self.players:
                if player.can_hear(other_player):
                    if other_player.location != player.location:
                        hearinfo+='Вы слышите движение в локации: '+loctoname(other_player.location)+'!\n'
                    else:
                        hearinfo+='Вы слышите движение в вашей текущей локации!!\n'
            bot.send_message(player.id, hearinfo)

        for player in self.players:
            if player.treasure and not player.disarmed and player.location=='spystart':
                self.treasurestealed = True
                        
        if not text:
            text = 'Ничего необычного...'
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='История '+str(self.turn)+' хода', callback_data='history '+datagen(self.texttohistory)))
        bot.send_message(self.id, 'Ход '+str(self.turn)+'. Ситуация в здании:\n\n'+text, reply_markup=kb)
            
        endgame=0    
        spyalive=0    
        for player in self.players:
            if not player.disarmed and player.role=='spy':
                spyalive += 1
        if spyalive<=0:
            endgame = True
            winner='security'
        if self.turn>=25:
            endgame = True
            winner='security'
            self.texttohistory+='Победа охраны по причине: прошло 25 ходов!\n\n'
        if self.treasurestealed:
            endgame = True
            winner='spy'
        if not endgame:
            for player in self.players:
                if not player.flashed and not player.shocked:
                    if not player.disarmed:            
                        bot.send_photo(player.id, map_file_id)
                        player.send_acts()
                    else:
                        player.ready = True
                else:
                    player.lastloc = player.location
                    player.ready = True

            self.gametimer = threading.Timer(90, self.end_turn)
            self.gametimer.start()

            self.turn+=1
            self.flashed=[]
            self.texttohistory=''
            for player in self.players:
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
                bot.send_message(self.id, 'Победа охраны!')
            else:
                bot.send_message(self.id, 'Победа шпионов!')
            try:
                del game_data.games[self.id]
            except:
                pass


    def check_readiness(self):
        return self.maxplayers == len(self.players)

    def join_player(self, user_id, user_name, chat_id):
        player = Player(user_id, user_name, chat_id)
        self.players.append(player)
        return player

    def get_player(user_id):
        return [player for player in self.players if player.id == user_id][0]

    def begin(self):
        self.started = True
        self.timer.cancel()
        
        securityitems = ['glasses','pistol','tizer', 'glasses','shockmine']
        spyitems = ['camera','camera','camera','flash','costume', 'flash','mineremover']
        for player in self.players:
            if self.spies > self.security:
                player.role = 'security'
                self.security += 1
                bot.send_message(player.id, 'Вы - охранник! Ваша цель - не дать шпионам украсть сокровище!'+\
                                    'Если продержитесь 25 ходов - вам на помощь приедет спецназ, и вы победите!')
            elif self.spies < self.security:
                player.role = 'spy'
                self.spies += 1
                bot.send_message(player.id, 'Вы - шпион! Ваша цель - украсть сокровище!'+\
                                    'Не попадитесь на глаза охраннику и сделайте всё меньше, чем за 26 ходов, иначе проиграете!')
            elif self.spies == self.security:
                player.role = random.choice(['spy','security'])
                if player.role == 'spy':
                    self.spies += 1
                    bot.send_message(player.id, 'Вы - шпион! Ваша цель - украсть сокровище!'+\
                                    'Не попадитесь на глаза охраннику и сделайте всё меньше, чем за 26 ходов, иначе проиграете!')
                elif player.role == 'security':
                    self.security += 1
                    bot.send_message(player.id, 'Вы - охранник! Ваша цель - не дать шпионам украсть сокровище! '+\
                                    'Если продержитесь 25 ходов - вам на помощь приедет спецназ, и вы победите!')
                    
        for player in self.players:
            if player.role=='security':
                player.items=securityitems
                player.location='stock'
            elif player.role=='spy':
                player.items=spyitems
                player.location='spystart'
                
        for player in self.players:
            player.lastloc = player.location
            player.send_acts()
        bot.send_message(self.id, 'Игра начинается! Охранники, шпионы - по позициям!')
            
        t=threading.Timer(90, self.end_turn, args=[self.id])
        t.start()
        self.gametimer = t



class Player:
    def __init__(self, user_id, user_name, chat_id):
        self.game = game_data.get_game(chat_id)

        self.id = user_id
        self.name = user_name
        self.location = None
        self.team = None
        self.items = []
        self.ready = 0
        self.messagetoedit = None
        self.cameras = []
        self.chatid = chat_id
        self.stealing = 0
        self.glasses = 0
        self.setupcamera = 0
        self.destroycamera = 0
        self.currentmessage = 0
        self.silent = 0
        self.flashed = 0
        self.lastloc = None
        self.treasure = 0
        self.disarmed = 0
        self.moving = 0
        self.shocked = 0
        self.removemine = 0

    def get_nearby_locations(self):
        nearby_locations = nearlocs[self.location]
        nearby_locations.append(self.location)
        return set(nearby_locations)

    @property
    def nearby_locations(self):
        return self.get_nearby_locations()

    def can_hear(self, player):
        return player.location in self.nearby_locations and \
               player.location!=player.lastloc and \
               not player.silent and self.role!=player.role

    def send_acts(self):  
        kb=types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(text='Перемещение', callback_data='move'),types.InlineKeyboardButton(text='Предметы', callback_data='items'))
        if self.role=='spy':
            kb.add(types.InlineKeyboardButton(text='Инфо с камер', callback_data='camerainfo'))
        if self.role=='security':
            kb.add(types.InlineKeyboardButton(text='Камера в сокровищнице', callback_data='treasureinfo'))
        kb.add(types.InlineKeyboardButton(text='Ожидать', callback_data='wait'))
        if not self.flashed:
            self.messagetoedit = bot.send_message(self.id,'Выберите действие.',reply_markup=kb)
        else:
            self.ready = True


game_data = Game()