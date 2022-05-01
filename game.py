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
        self.locs = ['treasure','spystart','leftcorridor','rightcorridor','leftpass','rightpass','antiflashroom','midcorridor','stock']
        self.flashed: []
        self.treasurestealed = False
        self.started = False
        self.texttohistory = ''
        self.shockminelocs = []
        self.maxplayers = player_count

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
            sendacts(player)
        bot.send_message(self.id, 'Игра начинается! Охранники, шпионы - по позициям!')
            
        t=threading.Timer(90, endturn, args=[self.id])
        t.start()
        self.gametimer = t



class Player:
    def __init__(self, user_id, user_name, chat_id):
        self.game = game_data.get_game(chat_id)

        self.id = user_id
        self.name = user_id
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
        return nearby_locations

    @property
    def nearby_locations(self):
        return self.get_nearby_locations()

    def can_hear(self, player):
        return player.location in self.nearby_locations and \
               player.location!=player.lastloc and \
               not player.silent and self.role!=player.role


game_data = Game()