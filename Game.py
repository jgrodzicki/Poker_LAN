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
        self.when_end = None

        self.id_turn = 0
        self.id_big_blind = self.id_small_blind = None
        self.is_playing = [True] * no_players
        self.money = [init_money] * no_players
        self.cards = []
        self.id_to_nick = {}

        self.is_flop = self.is_turn = self.is_river = False
    
    
    def next_round(self):
        self.id_big_blind, self.id_small_blind, self.id_turn = (self.id_big_blind+1)%self.cur_players, (self.id_small_blind+1)%self.cur_players, (self.id_turn+1)%self.cur_players


    def flop(self):
        self.is_flop = True
        for ch in self.player_channels:
            ch.Send({'action': 'flop', 'cards': self.flop_cards})

    def turn(self):
        self.is_turn = True
        for ch in self.player_channels:
            ch.Send({'action': 'turn', 'card': self.turn_card})

    def river(self):
        self.is_river = True
        for ch in self.player_channels:
            ch.Send({'action': 'river', 'card': self.river_card})


    def joined_player(self, channel):
        self.cur_players += 1
        self.player_channels.append(channel)
        self.cards.append([None, None])


    def add_nick(self, id, nick):
        self.id_to_nick[id] = nick


    def game_init(self):
        for i, ch in enumerate(self.player_channels):
            ids = [i for i in range(i+1, self.cur_players)] + [i for i in range(i)]
            ch.Send({'action': 'init', 'init_money': self.init_money, 'big_blind': self.big_blind,
                     'player_id': i, 'opp_ids': ids})
            ch.Send({'action': 'getcards', 'cards': self.cards[i]})

    def start_game(self):
        print('starting game')
        self.id_turn = 2%self.cur_players
        self.id_big_blind, self.id_small_blind = 1, 0
        self.when_end = self.id_big_blind
        self.its = 0

        for i, ch in enumerate(self.player_channels):
            ch.Send({'action': 'startgame'})

    def add_nicks(self):
        for i, ch in enumerate(self.player_channels):
            ids = [i for i in range(i + 1, self.cur_players)] + [i for i in range(i)]
            ch.Send({'action': 'addnicks', 'nicks': [self.id_to_nick[id_] for id_ in ids]})


    def fold(self, data):
        self.is_playing[data['player_id']] = False
        print('in game fold')
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()


    def check(self, data):
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()


    def call(self, data):
        self.money[data['player_id']] = data['money']
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()


    def raise_(self, data):
        self.when_end = data['player_id']
        self.money[data['player_id']] = data['money']
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()

    def next_turn(self):
        print('next turn')
        self.id_turn += 1
        self.id_turn = self.id_turn % self.cur_players
        self.its += 1

        if self.id_turn == self.when_end and self.its > 0:
            self.when_end, self.its = (self.id_big_blind+1)%self.cur_players, 0
            if not self.is_flop:
                self.flop()
            elif not self.is_turn:
                self.turn()
            elif not self.is_river:
                self.river()
            else:
                pass
        for ch in self.player_channels:
            ch.Send({'action': 'nextturn', 'player_id_turn': self.id_turn})


    def deal_cards(self):
        get_color = {0: 'H', 1: 'D', 2: 'S', 3: 'C'}
        get_fig = {i: i+2 for i in range(9)}
        get_fig[9] = 'J'; get_fig[10] = 'Q'; get_fig[11] = 'K'; get_fig[12] = 'A'
        cards = np.random.choice(52, size=2*self.cur_players + 5, replace=False)
        self.flop_cards = [f'{get_fig[c//4]}{get_color[c%4]}' for c in cards[-5:-2]]
        self.turn_card = f'{get_fig[cards[-2]//4]}{get_color[cards[-2]%4]}'
        self.river_card = f'{get_fig[cards[-1]//4]}{get_color[cards[-1]%4]}'

        for i in range(0, 2*self.cur_players, 2):
            c0, c1 = cards[i], cards[i+1]
            self.cards[i//2][0] = f'{get_fig[c0//4]}{get_color[c0%4]}'
            self.cards[i//2][1] = f'{get_fig[c1//4]}{get_color[c1%4]}'
