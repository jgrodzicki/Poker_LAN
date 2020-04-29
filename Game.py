import numpy as np
import time

import threading

from itertools import cycle


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

        self.pot = []
        self.id_turn = self.id_big_blind = self.id_small_blind = None
        self.id_turn_cc = self.id_big_blind_cc = self.id_small_blind_cc = None  # cycles
        self.is_playing = {}
        self.no_playing = 0
        self.no_folds = 0
        self.money = {}
        self.cards = {}
        self.id_to_nick = {}
        self.ids = []

        self.its = 0

        self.is_flop = self.is_turn = self.is_river = False
        self.flop_cards = self.turn_card = self.river_card = None
    
    
    def next_round(self):
        self.id_turn, self.id_big_blind, self.id_small_blind = next(self.id_turn_cc), next(self.id_big_blind_cc), \
                                                               next(self.id_small_blind_cc)
        self.deal_cards()
        self.is_flop = self.is_turn = self.is_river = False
        self.is_playing = {id: True for id in self.ids}
        self.no_playing = self.cur_players
        self.pot = [[self.big_blind * 1.5, {id: True for id in self.ids}]]

        self.money[self.id_big_blind] -= self.big_blind
        self.money[self.id_small_blind] -= self.big_blind//2

        self.no_folds = 0

        print(self.id_big_blind, self.id_small_blind)

        for i, ch in enumerate(self.player_channels):
            id = self.ids[i]
            ch.Send({'action': 'nextround', 'id_big_blind': self.id_big_blind, 'id_small_blind': self.id_small_blind, 'pot': self.pot})
            ch.Send({'action': 'getcards', 'cards': self.cards[id]})
            ch.Send({'action': 'nextturn', 'player_id_turn': self.id_turn, 'pot': self.pot})

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
        id = self.cur_players
        self.cur_players += 1
        self.player_channels.append(channel)
        self.ids.append(id)


    def add_nick(self, id, nick):
        self.id_to_nick[id] = nick
        for ch in self.player_channels:
            ch.Send({'action': 'addnick', 'player_id': id, 'nick': nick})


    def game_init(self):
        print('game_init')
        self.id_turn_cc = cycle(self.ids[2:] + self.ids[:2])
        self.id_big_blind_cc = cycle(self.ids[1:] + self.ids[1:])
        self.id_small_blind_cc = cycle(self.ids)

        for i, ch in enumerate(self.player_channels):
            id = self.ids[i]
            self.no_playing += 1
            self.is_playing[id] = True
            self.money[id] = self.init_money

            ch.Send({'action': 'init', 'init_money': self.init_money, 'big_blind': self.big_blind,
                     'player_id': id})
            ch.Send({'action': 'getcards', 'cards': self.cards[id]})

        for i, ch in enumerate(self.player_channels):  # notify about other players
            j = (i+1) % self.cur_players
            while j != i:
                ch.Send({'action': 'addplayer', 'player_id': j, 'money': self.init_money})
                j = (j+1) % self.cur_players


    def start_game(self):
        print('starting game')

        for i, ch in enumerate(self.player_channels):
            ch.Send({'action': 'startgame'})


    def fold(self, data):
        self.is_playing[data['player_id']] = False
        self.no_folds += 1
        if self.cur_players - self.no_folds == 1:
            won_id = None
            for id, f in self.is_playing.items():
                if f:
                    won_id = id
                    break
            for p in self.pot:
                for ch in self.player_channels:
                    ch.Send({'action': 'winner', 'player_id': won_id, 'won': p[0]})
            time.sleep(3)
            self.next_round()
        else:
            self.pot[-1][1] = self.is_playing.copy()
            for ch in self.player_channels:
                ch.Send(data)
            threading.Thread(target=self.next_turn).start()


    def check(self, data):
        for ch in self.player_channels:
            ch.Send(data)
        threading.Thread(target=self.next_turn).start()


    def call(self, data):
        self.money[data['player_id']] = data['money']
        self.pot[-1][0] += data['extra_to_pot']
        for ch in self.player_channels:
            ch.Send(data)
        threading.Thread(target=self.next_turn).start()


    def raise_(self, data):
        self.its = 0
        self.money[data['player_id']] = data['money']
        self.pot[-1][0] += data['extra_to_pot']
        for ch in self.player_channels:
            ch.Send(data)
        threading.Thread(target=self.next_turn).start()

    def next_turn(self):
        print('next turn')
        self.id_turn = next(self.id_turn_cc)

        while not self.is_playing[self.id_turn]:
            self.id_turn = next(self.id_turn_cc)

        self.its += 1
        print(f'its: {self.its}\nturn: {self.id_turn}')

        if self.its == self.no_playing:
            self.id_turn_cc = cycle(self.ids[self.id_small_blind:] + self.ids[:self.id_small_blind])
            self.id_turn = next(self.id_turn_cc)
            while not self.is_playing[self.id_turn]:
                self.id_turn = next(self.id_turn_cc)

            self.its = 0
            self.no_playing = len(list(filter(lambda id_v: id_v[1], self.is_playing.items())))

            if not self.is_flop:
                self.flop()
            elif not self.is_turn:
                self.turn()
            elif not self.is_river:
                self.river()
            else:
                self.pot_to_winners()
                time.sleep(5)
                self.next_round()

        for ch in self.player_channels:
            ch.Send({'action': 'nextturn', 'player_id_turn': self.id_turn, 'pot': self.pot})


    def logout(self, id):
        for ch in self.player_channels:
            ch.Send({'action': 'logout', 'player_id': id})
        self.player_channels = self.player_channels[:id] + self.player_channels[id+1:]
        self.cur_players -= 1
        del self.money[id]
        del self.cards[id]
        del self.is_playing[id]


    def deal_cards(self):
        get_color = {0: 'H', 1: 'D', 2: 'S', 3: 'C'}
        get_fig = {i: i+2 for i in range(9)}
        get_fig[9] = 'J'; get_fig[10] = 'Q'; get_fig[11] = 'K'; get_fig[12] = 'A'
        cards = np.random.choice(52, size=2*self.cur_players + 5, replace=False)
        self.flop_cards = [f'{get_fig[c//4]}{get_color[c%4]}' for c in cards[-5:-2]]
        self.turn_card = f'{get_fig[cards[-2]//4]}{get_color[cards[-2]%4]}'
        self.river_card = f'{get_fig[cards[-1]//4]}{get_color[cards[-1]%4]}'

        for i, id in enumerate(self.ids):
            c0, c1 = cards[i], cards[i+1]
            self.cards[id] = [f'{get_fig[c0//4]}{get_color[c0%4]}',
                              f'{get_fig[c1//4]}{get_color[c1%4]}']

    def pot_to_winners(self):
        pl_hands = {}
        for id in self.ids:
            if self.is_playing[id]:
                pl_cards = self.cards[id]
                c, f = self.get_colors_and_figs(pl_cards)
                pl_hands[id] = [self._is_straight_flush(c, f), self._is_four_of_kind(c, f), self._is_full_house(c, f),
                                self._is_flush(c, f), self._is_straight(c, f), self._is_three_of_kind(c, f),
                                self._is_two_pairs(c, f), self._is_pair(c, f), self._is_high_card(c, f)]

        # show cards of anyone who played till the end
        for id, is_p in self.is_playing.items():
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


    def get_winners(self, pl_hands):  # pl_hands is a dict id -> hand
        for h in range(12):  # loop over possible hands
            who_has = []
            what = []
            for id, ph in pl_hands.items():
                if ph[h] is not None:
                    who_has.append(id)
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
