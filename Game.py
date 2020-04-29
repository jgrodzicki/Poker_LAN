import numpy as np
import time

import threading


class Game:
    def __init__(self, no_players=6, init_money=1000, big_blind=50):
        self.no_players = 0
        self.player_nicks = [None] * no_players
        self.player_channels = []
        self.init_money = init_money
        self.big_blind = big_blind
        self.cur_players = 0
        self.no_players = no_players

        self.init_money = init_money

        self.pot = [[0, [True] * no_players]]
        self.id_turn = 0
        self.id_big_blind = self.id_small_blind = None
        self.is_playing = [False] * no_players
        self.no_playing = 0
        self.money = []
        self.cards = []
        self.id_to_nick = {}

        self.is_flop = self.is_turn = self.is_river = False
    
    
    def next_round(self):
        self.id_big_blind, self.id_small_blind, self.id_turn = (self.id_big_blind+1)%self.cur_players, (self.id_small_blind+1)%self.cur_players, (self.id_turn+1)%self.cur_players
        self.deal_cards()
        self.is_flop = self.is_turn = self.is_river = False
        for i, ch in enumerate(self.player_channels):
            self.is_playing[i] = True
            ch.Send({'action': 'nextround'})
            ch.Send({'action': 'getcards', 'cards': self.cards[i]})
            ch.Send({'action': 'nextturn', 'player_id_turn': self.id_turn})

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
        for ch in self.player_channels:
            ch.Send({'action': 'addnick', 'player_id': id, 'nick': nick})


    def game_init(self):
        for i, ch in enumerate(self.player_channels):
            self.no_playing += 1
            self.is_playing[i] = True
            self.money.append(self.init_money)
            ch.Send({'action': 'init', 'init_money': self.init_money, 'big_blind': self.big_blind,
                     'player_id': i})
            ch.Send({'action': 'getcards', 'cards': self.cards[i]})

        for i, ch in enumerate(self.player_channels):  # notify about other players
            j = (i+1) % self.cur_players
            while j != i:
                ch.Send({'action': 'addplayer', 'player_id': j, 'money': self.init_money})
                j = (j+1) % self.cur_players


    def start_game(self):
        print('starting game')
        self.id_turn = 2%self.cur_players
        self.id_big_blind, self.id_small_blind = 1, 0
        self.its = 0

        for i, ch in enumerate(self.player_channels):
            ch.Send({'action': 'startgame'})
            ch.Send({'action': 'nextturn', 'player_id_turn': self.id_turn})


    def fold(self, data):
        self.is_playing[data['player_id']] = False
        self.pot[-1][1] = self.is_playing.copy()
        print(self.pot)
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()


    def check(self, data):
        for ch in self.player_channels:
            ch.Send(data)
        print(self.pot)
        self.next_turn()


    def call(self, data):
        self.money[data['player_id']] = data['money']
        self.pot[-1][0] += data['extra_to_pot']
        print(self.pot)
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()


    def raise_(self, data):
        self.its = 0
        self.money[data['player_id']] = data['money']
        self.pot.append([self.pot[-1][0], self.is_playing.copy()])
        self.pot[-1][0] += data['extra_to_pot']
        print(self.pot)
        for ch in self.player_channels:
            ch.Send(data)
        self.next_turn()

    def next_turn(self):
        print('next turn')
        self.id_turn += 1
        self.id_turn = self.id_turn % self.cur_players
        while not self.is_playing[self.id_turn]:
            self.id_turn = (self.id_turn + 1) % self.cur_players

        self.its += 1

        if self.its == self.no_playing:
            self.its = 0
            self.id_turn = self.id_small_blind
            self.no_playing = len(list(filter(lambda x: x, self.is_playing)))

            if not self.is_flop:
                self.flop()
            elif not self.is_turn:
                self.turn()
            elif not self.is_river:
                self.river()
            else:
                self.pot_to_winners()
                th = threading.Thread(target=lambda: time.sleep(5))
                th.start()
                th.join()
                self.next_round()
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

    def pot_to_winners(self):
        pl_hands = [None] * self.cur_players
        for i, pl_cards in enumerate(self.cards):
            c, f = self.get_colors_and_figs(pl_cards)
            pl_hands[i] = [self._is_straight_flush(c, f), self._is_four_of_kind(c, f), self._is_full_house(c, f),
                        self._is_flush(c, f), self._is_straight(c, f), self._is_three_of_kind(c, f),
                        self._is_two_pairs(c, f), self._is_pair(c, f), self._is_high_card(c, f)]

        # show cards of anyone who played till the end
        for id, is_p in enumerate(self.is_playing):
            if is_p:
                for ch in self.player_channels:
                    ch.Send({'action': 'showcards', 'player_id': id, 'cards': self.cards[id]})

        for p, played in self.pot:
            winners = self.get_winners(pl_hands)
            for w in winners:
                self.money[int(w)] += p/len(winners)

            for ch in self.player_channels:
                for w in winners:
                    ch.Send({'action': 'winner', 'player_id': int(w), 'won': p / len(winners)})


    def logout(self, id):
        for ch in self.player_channels:
            ch.Send({'action': 'logout', 'player_id': id})
        self.player_channels = self.player_channels[:id] + self.player_channels[id+1:]
        self.cur_players -= 1
        self.money = self.money[:id] + self.money[id+1:]
        self.cards = self.cards[:id] + self.cards[id+1:]


    def get_winners(self, pl_hands):
        for h in range(12):  # loop over possible hands
            who_has = []
            what = []
            for i, ph in enumerate(pl_hands):
                if ph[h] is not None:
                    who_has.append(i)
                    what.append(ph[h])

            if len(who_has):
                break

        who_has = np.array(who_has)
        what = np.array(what)

        for i in range(what.shape[1]):
            max_ = what[:, i].max()
            idxs = what[:, i] == max_
            what = what[idxs]
            who_has = who_has[idxs]

        return who_has



    def get_colors_and_figs(self, pl_cards):
        fig_to_no = {str(i): i-2 for i in range(2, 11)}
        fig_to_no['J'] = 9; fig_to_no['Q'] = 10; fig_to_no['K'] = 11; fig_to_no['A'] = 12
        col_to_no = {c: i for i, c in enumerate(['H', 'D', 'S', 'C'])}
        colors = [0] * 4
        figs = [0] * 13
        for c in pl_cards + self.flop_cards + [self.turn_card] + [self.river_card]:
            fg = fig_to_no[c[:-1]]
            cl = col_to_no[c[-1]]
            colors[cl] += 1
            figs[fg] += 1
        return colors, figs

    def _is_straight_flush(self, colors, figs):
        straight, flush = self._is_straight(colors, figs), self._is_flush(colors, figs)
        if straight is not None and flush is not None:
            return straight
        return None

    def _is_four_of_kind(self, colors, figs):
        for i, n in enumerate(figs):
            if n == 4:
                res = [i]
                res.extend(self._find_best_high(colors, figs, [i], 1))
                return res
        return None

    def _is_full_house(self, colors, figs):
        res = [None, None]
        for i, n in enumerate(figs):
            if n == 3:
                res[0] = i
            elif n == 2:
                res[1] = i

        if all(res):
            return res
        return None


    def _is_flush(self, colors, figs):
        if any(list(map(lambda x: x == 4, colors))):
            return self._find_best_high(colors, figs, [], 5)
        return None

    def _is_straight(self, colors, figs):
        res = [None]
        cnt = 0
        for i, n in enumerate(figs):
            if n > 1:
                return None
            if n == 1:
                cnt += 1
            if cnt == 5:
                return list(range(i, i-5, -1))
            if n == 0 and 0 < cnt < 5:
                return None


    def _is_three_of_kind(self, colors, figs):
        res = [None]
        for i, n in enumerate(figs):
            if n == 3:
                res[0] = i

        if res[0] is None:
            return None

        res.extend(self._find_best_high(colors, figs, res, 2))
        return res

    def _is_two_pairs(self, colors, figs):
        res = []
        for i, n in enumerate(figs):
            if n == 2:
                res.append(i)

        if len(res) < 2:
            return None

        res = res[::-1][:2]
        res.extend(self._find_best_high(colors, figs, res, 1))
        return res

    def _is_pair(self, colors, figs):  # pair, 3 best other
        res = [None]
        for i, n in enumerate(figs):
            if n == 2:
                res[0] = i

        if res[0] is None:
            return None

        res.extend(self._find_best_high(colors, figs, [res[0]], 3))
        return res

    def _is_high_card(self, colors, figs):  # 5 cards
        return self._find_best_high(colors, figs, [], 5)

    def _find_best_high(self, colors, figs, without, to_ret):
        res = []
        for i, n in enumerate(figs):
            if i in without:
                continue
            res.extend([i] * n)
        return res[::-1][:to_ret]
