import numpy as np
import time

import threading

from itertools import cycle


class Game:
    def __init__(self, no_players, init_money, big_blind):
        self.no_players = 0
        self.player_channels = {}
        self.init_money = init_money
        self.big_blind = big_blind
        self.cur_players = 0
        self.no_players = no_players

        self.init_money = init_money

        self.pot = []
        self.id_turn = self.id_big_blind = self.id_small_blind = None
        self.id_turn_cc = self.id_big_blind_cc = self.id_small_blind_cc = None  # cycles
        self.is_playing = {}
        self.is_allin = {}
        self.no_playing = 0
        self.no_folds = 0
        self.money = {}
        self.cards = {}
        self.id_to_nick = {}
        self.ids = []
        self.id_gen = (i for i in range(10000))

        self.queue = []
        self.is_game_on = False

        self.its = 0

        self.is_flop = self.is_turn = self.is_river = False
        self.flop_cards = self.turn_card = self.river_card = None
    
    
    def next_round(self):
        while len(self.queue) and self.cur_players < 6:
            id = next(self.id_gen)
            channel = self.queue[0]
            self.queue = self.queue[1:]

            # update vars
            self.cur_players += 1
            self.player_channels[id] = channel
            self.ids.append(id)
            self.is_playing[id] = self.is_allin[id] = self.cards[id] = None
            self.money[id] = self.init_money

            channel.Send({'action': 'init', 'init_money': self.init_money, 'player_id': id, 'big_blind': self.big_blind})

            # notify others
            for id1 in self.ids:
                if id1 == id:
                    continue
                self.player_channels[id1].Send({'action': 'addplayer', 'player_id': id, 'money': self.money[id]})
                self.player_channels[id].Send({'action': 'addplayer', 'player_id': id1, 'money': self.money[id1]})
                self.player_channels[id].Send({'action': 'addnick', 'player_id': id1, 'nick': self.id_to_nick[id1]})

            channel.Send({'action': 'startgame'})

            # update cycles
            id_turns = []
            t = next(self.id_turn_cc)
            while t not in id_turns:
                id_turns.append(t)
                t = next(self.id_turn_cc)
            id_turns.append(id)
            self.id_turn_cc = cycle(id_turns)

            id_bblind = []
            t = next(self.id_big_blind_cc)
            while t not in id_bblind:
                id_bblind.append(t)
                t = next(self.id_big_blind_cc)
            id_bblind.append(id)
            self.id_big_blind_cc = cycle(id_bblind)

            id_sblind = []
            t = next(self.id_small_blind_cc)
            while t not in id_sblind:
                id_sblind.append(t)
                t = next(self.id_small_blind_cc)
            id_sblind.append(id)
            self.id_small_blind_cc = cycle(id_sblind)


        self.id_turn, self.id_big_blind, self.id_small_blind = next(self.id_turn_cc), next(self.id_big_blind_cc), \
                                                               next(self.id_small_blind_cc)

        self.deal_cards()
        self.is_flop = self.is_turn = self.is_river = False
        self.is_playing = {id: self.money[id] > 0 for id in self.ids}
        self.no_playing = len(list(filter(lambda id: self.money[id] > 0, self.ids)))

        if self.no_playing < 2:
            return

        self.pot = [[self.big_blind * 1.5, {id: True for id in self.ids}]]

        self.money[self.id_big_blind] -= self.big_blind
        self.money[self.id_small_blind] -= self.big_blind//2

        self.is_allin = {id: False for id in self.ids}

        while not self.is_playing[self.id_turn]:
            self.id_turn = next(self.id_turn_cc)

        while not self.is_playing[self.id_big_blind]:
            self.id_big_blind = next(self.id_big_blind_cc)

        while not self.is_playing[self.id_small_blind]:
            self.id_small_blind = next(self.id_big_blind_cc)

        print(f'id bb: {self.id_big_blind}, id sm: {self.id_small_blind}')

        self.its = 0

        self.no_folds = 0

        print(self.id_big_blind, self.id_small_blind)

        for id in self.ids:
            self.player_channels[id].Send({'action': 'nextround', 'id_big_blind': self.id_big_blind, 'id_small_blind': self.id_small_blind, 'pot': self.pot})
            self.player_channels[id].Send({'action': 'getcards', 'cards': self.cards[id]})
            self.player_channels[id].Send({'action': 'nextturn', 'player_id_turn': self.id_turn, 'pot': self.pot})

    def flop(self):
        self.is_flop = True
        for id in self.ids:
            self.player_channels[id].Send({'action': 'flop', 'cards': self.flop_cards})

    def turn(self):
        self.is_turn = True
        for id in self.ids:
            self.player_channels[id].Send({'action': 'turn', 'card': self.turn_card})

    def river(self):
        self.is_river = True
        for id in self.ids:
            self.player_channels[id].Send({'action': 'river', 'card': self.river_card})


    def joined_player(self, channel):
        if not self.is_game_on:
            id = next(self.id_gen)
            self.cur_players += 1
            self.player_channels[id] = channel
            self.ids.append(id)
        else:
            self.queue.append(channel)
            if self.no_playing < 2:
                self.next_round()


    def add_nick(self, id, nick):
        self.id_to_nick[id] = nick
        for id1 in self.ids:
            self.player_channels[id1].Send({'action': 'addnick', 'player_id': id, 'nick': nick})


    def game_init(self):
        print('game_init')
        self.id_turn_cc = cycle(self.ids[2:] + self.ids[:2])
        self.id_big_blind_cc = cycle(self.ids[1:] + self.ids[:1])
        self.id_small_blind_cc = cycle(self.ids)

        for id in self.ids:
            self.no_playing += 1
            self.is_playing[id] = True
            self.money[id] = self.init_money

            self.player_channels[id].Send({'action': 'init', 'init_money': self.init_money, 'big_blind': self.big_blind,
                     'player_id': id})

        for id1 in self.ids:  # notify about other players
            for id2 in self.ids:
                if id1 == id2:
                    continue
                print(f'sending to {id1} about {id2}')
                self.player_channels[id1].Send({'action': 'addplayer', 'player_id': id2, 'money': self.init_money})


    def start_game(self):
        print('starting game')
        self.is_game_on = True

        for id in self.ids:
            self.player_channels[id].Send({'action': 'startgame'})


    def fold(self, data):
        self.is_playing[data['player_id']] = False
        self.no_folds += 1

        for id in self.ids:
            self.player_channels[id].Send(data)

        if self.cur_players - self.no_folds == 1:
            won_id = None
            for id, f in self.is_playing.items():
                if f:
                    won_id = id
                    break
            for p in self.pot:
                for id in self.ids:
                    self.player_channels[id].Send({'action': 'winner', 'player_id': won_id, 'won': p[0]})

            time.sleep(4)
            self.next_round()
        else:
            self.pot[-1][1] = self.is_playing.copy()
            threading.Thread(target=self.next_turn).start()


    def check(self, data):
        for id in self.ids:
            self.player_channels[id].Send(data)
        threading.Thread(target=self.next_turn).start()


    def call(self, data):
        id = data['player_id']
        self.money[id] = data['money']
        self.is_allin[id] = data['allin']
        self.pot[-1][0] += data['extra_to_pot']

        for id in self.ids:
            self.player_channels[id].Send(data)
            self.player_channels[id].Send({'action': 'updatepot', 'pot_val': self.pot[-1][0]})
        threading.Thread(target=self.next_turn).start()


    def raise_(self, data):
        self.its = 0
        id = data['player_id']
        self.money[id] = data['money']
        self.is_allin[id] = data['allin']
        self.pot[-1][0] += data['extra_to_pot']
        for id in self.ids:
            self.player_channels[id].Send(data)
            self.player_channels[id].Send({'action': 'updatepot', 'pot_val': self.pot[-1][0]})
        threading.Thread(target=self.next_turn).start()

    def next_turn(self):
        self.its += 1

        print(f'its: {self.its}, no_playing: {self.no_playing}')
        if self.its == self.no_playing:
            self.id_turn_cc = cycle(self.ids[self.id_small_blind:] + self.ids[:self.id_small_blind])

            self.its = 0
            self.no_playing = len(list(filter(lambda id: self.is_playing[id] and not self.is_allin[id], self.ids)))

            if self.no_playing == 0:
                if not self.is_flop:
                    self.flop()
                    time.sleep(4)
                if not self.is_turn:
                    self.turn()
                    time.sleep(4)
                if not self.is_river:
                    self.river()
                    time.sleep(4)

                self.pot_to_winners()
                time.sleep(8)
                self.next_round()
                return

            if not self.is_flop:
                self.flop()
            elif not self.is_turn:
                self.turn()
            elif not self.is_river:
                self.river()
            else:
                self.pot_to_winners()
                time.sleep(8)
                self.next_round()
                return

        self.id_turn = next(self.id_turn_cc)
        while not self.is_playing[self.id_turn] or self.is_allin[self.id_turn]:
            self.id_turn = next(self.id_turn_cc)

        for id in self.ids:
            self.player_channels[id].Send({'action': 'nextturn', 'player_id_turn': self.id_turn, 'pot': self.pot})


    def logout(self, id):
        print(f'player {self.id_to_nick[id]}, id:{id} logged out')
        for id1 in self.ids:
            print(f'send logout to {id1}')
            self.player_channels[id1].Send({'action': 'logout', 'player_id': id})
        self.cur_players -= 1

        del self.money[id]
        del self.cards[id]
        del self.is_playing[id]
        del self.id_to_nick[id]
        del self.player_channels[id]
        self.ids.remove(id)

        id_turns = []
        nid = next(self.id_turn_cc)
        while nid not in id_turns:
            if nid != id:
                id_turns.append(nid)
            nid = next(self.id_turn_cc)
        self.id_turn_cc = cycle(id_turns)

        id_bblinds = []
        nid = next(self.id_big_blind_cc)
        while nid not in id_bblinds:
            if nid != id:
                id_bblinds.append(nid)
            nid = next(self.id_big_blind_cc)
        self.id_big_blind_cc = cycle(id_bblinds)

        id_sblinds = []
        nid = next(self.id_small_blind_cc)
        while nid not in id_sblinds:
            if nid != id:
                id_sblinds.append(nid)
            nid = next(self.id_small_blind_cc)
        self.id_small_blind_cc = cycle(id_sblinds)

        print(f'players left: {self.id_to_nick.items()}')

        if id == self.id_turn:
            self.next_turn()


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
        for id in self.ids:
            self.player_channels[id].Send({'action': 'clearmsg'})

        pl_hands = {}
        for id in self.ids:
            if self.is_playing[id]:
                pl_cards = self.cards[id]
                c, f, cards = self.get_colors_figs_cards(pl_cards)
                pl_hands[id] = [self._is_straight_flush(c, f, cards), self._is_four_of_kind(c, f, cards), self._is_full_house(c, f, cards),
                                self._is_flush(c, f, cards), self._is_straight(c, f, cards), self._is_three_of_kind(c, f, cards),
                                self._is_two_pairs(c, f, cards), self._is_pair(c, f, cards), self._is_high_card(c, f, cards)]

                for i, h in enumerate(pl_hands[id]):
                    if h is not None:
                        desc = self.get_desc(i, h, self.id_to_nick[id])
                        for id in self.ids:
                            self.player_channels[id].Send({'action': 'addmsg', 'msg': desc})
                        # print(f'{self.id_to_nick[id]} has {name[i]}: {pl_hands[id][i]}')
                        break

        # show cards of anyone who played till the end
        for id, is_p in self.is_playing.items():
            if is_p:
                for id1 in self.ids:
                    self.player_channels[id1].Send({'action': 'showcards', 'player_id': id, 'cards': self.cards[id]})

        for p, played in self.pot:
            hands_round = {}
            for id, val in played.items():
                if val:
                    hands_round[id] = pl_hands[id]
            winners = self.get_winners(hands_round)
            for w in winners:
                self.money[int(w)] += p/len(winners)

            print(f'pot: {self.pot}')

            for id in self.ids:
                for w in winners:
                    self.player_channels[id].Send({'action': 'winner', 'player_id': int(w), 'won': p / len(winners)})

    def get_desc(self, i, pl_hand, nick):
        name = ['straight flush', 'four of the kind', 'full house', 'flush', 'straight',
                'three of the kind', 'two pairs', 'pair', 'high card']
        int_to_fig = {i: str(i+2) for i in range(9)}
        int_to_fig[9] = 'J'; int_to_fig[10] = 'Q'; int_to_fig[11] = 'K'; int_to_fig[12] = 'A'

        desc = f'{nick} has {name[i]}'
        if i == 0:
            desc += f' from {int_to_fig[pl_hand[0]]}'
        elif i == 1:
            desc += f' {int_to_fig[pl_hand[0]]} with kicker {int_to_fig[pl_hand[1]]}'
        elif i == 2:
            desc += f' {int_to_fig[pl_hand[0]]} and {int_to_fig[pl_hand[1]]}'
        elif i == 3:
            desc += f' {", ".join([int_to_fig[c] for c in pl_hand])}'
        elif i == 4:
            desc += f' from {int_to_fig[pl_hand[0]]}'
        elif i == 5:
            desc += f' {int_to_fig[pl_hand[0]]} and {int_to_fig[pl_hand[1]]}'
        elif i == 6:
            desc += f' {int_to_fig[pl_hand[0]]} and {int_to_fig[pl_hand[1]]} with kicker {int_to_fig[pl_hand[2]]}'
        elif i == 7 or i == 8:
            desc += f' {int_to_fig[pl_hand[0]]} with kickers {", ".join([int_to_fig[c] for c in pl_hand[1:]])}'

        return desc


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



    def get_colors_figs_cards(self, pl_cards):
        fig_to_no = {str(i): i-2 for i in range(2, 11)}
        fig_to_no['J'] = 9; fig_to_no['Q'] = 10; fig_to_no['K'] = 11; fig_to_no['A'] = 12
        col_to_no = {c: i for i, c in enumerate(['H', 'D', 'S', 'C'])}
        colors = [0] * 4
        figs = [0] * 13
        cards = []

        for c in pl_cards + self.flop_cards + [self.turn_card] + [self.river_card]:
            fg = fig_to_no[c[:-1]]
            cl = col_to_no[c[-1]]
            colors[cl] += 1
            figs[fg] += 1
            cards.append([cl, fg])

        return colors, figs, cards

    def _is_straight_flush(self, colors, figs, cards):
        straight, flush = self._is_straight(colors, figs, cards), self._is_flush(colors, figs, cards)
        cnt = [0]*4  # count continuous of each color

        if straight is not None and flush is not None:
            for i in range(13):
                occured = [0] * 4
                for c in cards:
                    if c[1] != i:
                        continue
                    occured[c[0]] = 1
                for j in range(4):
                    cnt[j] = occured[j]*cnt[j] + occured[j]
                    if cnt[j] == 5:
                        return list(range(i, i-5, -1))
        return None

    def _is_four_of_kind(self, colors, figs, cards):
        for i, n in enumerate(figs):
            if n == 4:
                res = [i]
                res.extend(self._find_best_high(colors, figs, [i], 1))
                return res
        return None

    def _is_full_house(self, colors, figs, cards):
        res = [None, None]
        for i, n in enumerate(figs):
            if n == 3:
                res[0] = i
            elif n == 2:
                res[1] = i

        if all(res):
            return res
        return None


    def _is_flush(self, colors, figs, cards):
        if any(list(map(lambda x: x == 5, colors))):
            color = colors.index(5)
            res = []
            for c in cards:
                if c[0] == color:
                    res.append(c[1])
            return sorted(res, reverse=True)
        return None

    def _is_straight(self, colors, figs, cards):
        cnt = 0
        for i, n in enumerate(figs):
            if n >= 1:
                cnt += 1
            if cnt == 5:
                return list(range(i, i-5, -1))
            if n == 0 and 0 < cnt < 5:
                return None


    def _is_three_of_kind(self, colors, figs, cards):
        res = [None]
        for i, n in enumerate(figs):
            if n == 3:
                res[0] = i

        if res[0] is None:
            return None

        res.extend(self._find_best_high(colors, figs, res, 2))
        return res

    def _is_two_pairs(self, colors, figs, cards):
        res = []
        for i, n in enumerate(figs):
            if n == 2:
                res.append(i)

        if len(res) < 2:
            return None

        res = res[::-1][:2]
        res.extend(self._find_best_high(colors, figs, res, 1))
        return res

    def _is_pair(self, colors, figs, cards):  # pair, 3 best other
        res = [None]
        for i, n in enumerate(figs):
            if n == 2:
                res[0] = i

        if res[0] is None:
            return None

        res.extend(self._find_best_high(colors, figs, [res[0]], 3))
        return res

    def _is_high_card(self, colors, figs, cards):  # 5 cards
        return self._find_best_high(colors, figs, [], 5)

    def _find_best_high(self, colors, figs, without, to_ret):
        res = []
        for i, n in enumerate(figs):
            if i in without:
                continue
            res.extend([i] * n)
        return res[::-1][:to_ret]
