import numpy as np


class Game:
    def __init__(self, no_players=6, init_money=1000, big_blind=50):
        self.no_players = 0
        self.player_nicks = [None] * no_players
        self.player_channels = []
        self.init_money = init_money
        self.big_blind = big_blind
        self.cur_players = 0
        self.no_players = no_players

        self.turn = 0
        self.is_playing = [True] * no_players
        self.money = [init_money] * no_players
        self.cards = []


    def joined_player(self, channel):
        self.cur_players += 1
        self.player_channels.append(channel)
        self.cards.append([None, None])


    def start_game(self):
        print('starting game')
        for i, ch in enumerate(self.player_channels):
            ch.Send({'action': 'startgame', 'init_money': self.init_money, 'big_blind': self.big_blind,
                     'players_nick': ['p1', 'p2', 'p3', 'p4', 'p5'], 'player_id': i})
            ch.Send({'action': 'getcards', 'cards': self.cards[i]})


    def fold(self, data):
        self.is_playing[data['player_id']] = False
        print('in game fold')
        for ch in self.player_channels:
            ch.Send(data)
        self.turn += 1
        self.turn = self.turn % self.no_players


    def check(self, data):
        for ch in self.player_channels:
            ch.Send(data)
        self.turn += 1
        self.turn = self.turn % self.no_players


    def call(self, data):
        self.money[data['player_id']] = data['money']
        for ch in self.player_channels:
            ch.Send(data)
        self.turn += 1
        self.turn = self.turn % self.no_players


    def raise_(self, data):
        self.money[data['player_id']] = data['money']
        for ch in self.player_channels:
            ch.Send(data)
        self.turn += 1
        self.turn = self.turn % self.no_players


    def deal_cards(self):
        get_color = {0: 'H', 1: 'D', 2: 'S', 3: 'C'}
        get_fig = {i: i+2 for i in range(9)}
        get_fig[9] = 'J'; get_fig[10] = 'Q'; get_fig[11] = 'K'; get_fig[12] = 'A'
        cards = np.random.choice(52, size=2*self.cur_players, replace=False)
        print(cards)

        for i in range(0, 2*self.cur_players, 2):
            c0, c1 = cards[i], cards[i+1]
            self.cards[i//2][0] = f'{get_fig[c0//4]}{get_color[c0%4]}'
            self.cards[i//2][1] = f'{get_fig[c1//4]}{get_color[c1%4]}'
