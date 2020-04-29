import sys

import pygame

from PodSixNet.Connection import ConnectionListener, connection

import time

from Button import Button
from TextField import TextField


class Poker(ConnectionListener):

    def __init__(self, nick, addr, port):

        self.width, self.height = 750, 500
        self.card_w, self.card_h = 43, 62

        # initialize pygame shit
        pygame.init()
        # 2
        # initialize the screen
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Poker')
        # 3
        # initialize pygame clock
        self.clock = pygame.time.Clock()

        self.nick_color, self.money_color = (100, 100, 100), (255, 255, 0)

        self.is_turn = False
        self.is_playing = True
        self.is_waiting_to_start = True
        self.player_id = None

        self.money = None
        self.big_blind = self.small_blind = None
        self.id_big_blind = self.id_small_blind = None

        self.card1 = self.card2 = None

        self.back_card = pygame.image.load(f'images/back.png')

        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.nick = nick
        # self.nick = self.font.render(nick, True, nick_color, None)

        self.error_font = pygame.font.Font('freesansbold.ttf', 12)
        self.error_raise_msg = self.error_font.render('INVALID VALUE', True, (255, 0, 0), (255, 255, 255))
        self.error_time = 0

        # other players
        self.is_opp_playing = {}
        self.id_turn = None
        self.opp_bet = {}
        self.players_nick = {}
        self.opp_ids = []
        self.opp_money = {}
        self.players_pos = [(self.width*0.75//5, self.height*3//5), (self.width*0.75//5, self.height*1.5//5),
                            (self.width//2, 50), (self.width*4.25//5, self.height*1.5//5),
                            (self.width*4.25//5, self.height*3//5)]

        # cards on the table
        self.on_table = [None] * 5

        self.bet = 0
        self.bet_on_table = 0

        self.fold_b = Button('fold', (self.width - 270, self.height-20), self.screen)
        self.check_b = Button('check', (self.width - 180, self.height-20), self.screen)
        self.raise_b = Button('raise', (self.width - 90, self.height-20), self.screen)
        self.raise_t = TextField((self.width - 90, self.height - 50), self.screen)

        self.Connect((addr, int(port)))


    def update(self):
        connection.Pump()
        self.Pump()
        if self.is_waiting_to_start:

            for event in pygame.event.get():
                # quit if the quit button was pressed
                if event.type == pygame.QUIT:
                    exit()
            return

        # sleep to make the game 60 fps
        self.clock.tick(60)
        # clear the screen
        self.screen.fill(0)

        self._handle_actions()

        self._draw_player()

        if self.is_turn:
            self._draw_buttons()

        if time.time() - self.error_time < 8:
            self.screen.blit(self.error_raise_msg, (self.width-135, self.height-80))

        self._draw_others()

        self._draw_table()

        # update the screen
        pygame.display.update()


    def Network_init(self, data):
        self.money = data['init_money']
        self.big_blind = data['big_blind']
        self.small_blind = self.big_blind//2
        self.player_id = data['player_id']
        self.money = data['init_money']

        # send nickname
        self.Send({'action': 'info', 'player_id': self.player_id, 'nick': self.nick})

    def Network_getcards(self, data):
        self.card1 = pygame.image.load(f'images/{data["cards"][0]}.png')
        self.card2 = pygame.image.load(f'images/{data["cards"][1]}.png')

    def Network_addplayer(self, data):
        id = data['player_id']
        self.opp_ids.append(id)
        self.opp_money[id] = data['money']
        self.opp_bet[id] = 0
        self.is_opp_playing[id] = True

    def Network_addnick(self, data):
        self.players_nick[data['player_id']] = data['nick']

    def Network_startgame(self, data):
        self.is_waiting_to_start = False

    def Network_nextround(self, data):
        self.id_big_blind = data['id_big_blind']
        self.id_small_blind = data['id_small_blind']

        self.bet = 0
        self.bet_on_table = self.big_blind

        self.is_opp_playing = {id: True for id in self.opp_ids}
        self.on_table = [None] * 5
        self.bet_on_table = self.big_blind

        self.check_b.change_txt(f'call {self.big_blind}')

        if self.id_big_blind == self.player_id:
            self.money -= self.big_blind
            self.bet = self.big_blind
            self.check_b.change_txt('check')
        else:
            self.opp_money[self.id_big_blind] -= self.big_blind
            self.opp_bet[self.id_big_blind] = self.big_blind

        if self.id_small_blind == self.player_id:
            self.money -= self.small_blind
            self.bet = self.small_blind
        else:
            self.opp_money[self.id_small_blind] -= self.small_blind
            self.opp_bet[self.id_small_blind] = self.small_blind

    def Network_nextturn(self, data):
        if self.player_id == data['player_id_turn']:
            self.is_turn = True
            self.id_turn = None
        else:
            self.id_turn = data['player_id_turn']

    def Network_flop(self, data):
        self.bet = self.bet_on_table = 0
        self.opp_bet = {id: 0 for id in self.opp_ids}
        self.on_table[:3] = list(map(lambda c: pygame.image.load(f'images/{c}.png'), data['cards']))

    def Network_turn(self, data):
        self.bet = self.bet_on_table = 0
        self.opp_bet = {id: 0 for id in self.opp_ids}
        self.on_table[3] = pygame.image.load(f'images/{data["card"]}.png')

    def Network_river(self, data):
        self.bet = self.bet_on_table = 0
        self.opp_bet = {id: 0 for id in self.opp_ids}
        self.on_table[4] = pygame.image.load(f'images/{data["card"]}.png')

    def Network_fold(self, data):
        id = data['player_id']
        if id == self.player_id:
            self.is_playing = False
        else:
            self.is_opp_playing[id] = False

    def Network_check(self, data):
        pass

    def Network_call(self, data):
        id = data['player_id']
        if id != self.player_id:
            self.opp_money[id] = data['money']

    def Network_raise(self, data):
        id = data['player_id']
        if id != self.player_id:
            self.opp_money[id] = data['money']
            self.bet_on_table = data['amount']
            self.check_b.change_txt(f'call {self.bet_on_table}')

    def Network_winner(self, data):
        id = data['player_id']
        if id == self.player_id:
            self.money += data['won']
        else:
            self.opp_money[id] += data['won']

    def Network_logout(self, data):
        pass


    def _fold(self):
        self.is_turn = False
        self.Send({'action': 'fold', 'player_id': self.player_id})


    def _check(self):
        self.is_turn = False
        self.Send({'action': 'check', 'player_id': self.player_id})


    def _call(self):
        self.is_turn = False
        extra_to_pot = self.bet_on_table - self.bet
        if self.bet_on_table - self.bet < self.money:
            self.money -= (self.bet_on_table - self.bet)
            self.bet = self.bet_on_table
            self.Send({'action': 'call', 'player_id': self.player_id, 'money': self.money, 'allin': False,
                       'extra_to_pot': extra_to_pot})
        else:
            self.bet += self.money
            self.money = 0
            self.Send({'action': 'call', 'player_id': self.player_id, 'money': self.money, 'allin': True,
                       'extra_to_pot': extra_to_pot})

        self.check_b.to_check()


    def _raise(self, amount):
        self.is_turn = False
        extra_to_pot = amount - self.bet
        self.money -= (amount - self.bet)
        self.bet = self.bet_on_table = amount
        self.Send(({'action': 'raise', 'player_id': self.player_id, 'money': self.money, 'allin': self.money == 0,
                    'amount': self.bet, 'extra_to_pot': extra_to_pot}))

        self.check_b.to_check()


    def _handle_actions(self):
        for event in pygame.event.get():
            # quit if the quit button was pressed
            if event.type == pygame.QUIT:
                exit()

            if self.is_turn:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.fold_b.is_clicked():
                        self._fold()
                    elif self.check_b.is_clicked() and self.bet_on_table == 0:
                        self._check()
                    elif self.check_b.is_clicked():
                        self._call()
                    elif self.raise_b.is_clicked():
                        val = self.raise_t.get_value()
                        if val < self.bet_on_table+self.big_blind or val > self.money:
                            self.error_time = time.time()
                        else:
                            self._raise(val)
                    elif self.raise_t.is_clicked():
                        self.raise_t.click_action()

                elif event.type == pygame.KEYDOWN:
                    self.raise_t.update(event.key)

    def _draw_player(self):
        self.screen.blit(self.card1, (self.width // 2 - self.card_w - 5, self.height - 100))
        self.screen.blit(self.card2, (self.width // 2 + 5, self.height - 100))

        if self.player_id == self.id_big_blind:
            self.screen.blit(self.font.render('BB', True, (150, 150, 150), None), (self.width // 2 + 50, self.height - 90))

        if self.player_id == self.id_small_blind:
            self.screen.blit(self.font.render('SB', True, (150, 150, 150), None), (self.width // 2 + 50, self.height - 90))

        nick_label = self.font.render(self.nick, True, self.nick_color, None)
        nick_rect = nick_label.get_rect(center=(self.width // 2, self.height - 20))
        self.screen.blit(nick_label, nick_rect)

        bet_label = self.font.render(str(self.bet), True, self.money_color, None)
        self.screen.blit(bet_label, (self.width//2 + 50, self.height - 105))

        money_label = self.font.render(str(self.money), True, self.money_color, None)
        money_rect = money_label.get_rect(center=(self.width // 2, self.height - 120))
        self.screen.blit(money_label, money_rect)


    def _draw_others(self):
        for i, id in enumerate(self.opp_ids):
            nick = self.players_nick[id]
            if nick is None:
                continue

            x, y = self.players_pos[i]

            if self.is_opp_playing[id]:
                self.screen.blit(self.back_card, (x-self.card_w-5, y))
                self.screen.blit(self.back_card, (x+5, y))

            if id == self.id_big_blind:
                self.screen.blit(self.font.render('BB', True, (150, 150, 150), None), (x+50, y+10))
            if id == self.id_small_blind:
                self.screen.blit(self.font.render('SB', True, (150, 150, 150), None), (x+50, y+10))

            if self.id_turn == id:
                self.screen.blit(self.font.render('turn', True, (100, 100, 100), None), (x, y+90))

            nick_label = self.font.render(nick, True, self.nick_color, None)
            nick_rect = nick_label.get_rect(center=(x, y+70))
            self.screen.blit(nick_label, nick_rect)

            bet_label = self.font.render(str(self.opp_bet[id]), True, self.money_color, None)
            self.screen.blit(bet_label, (x+50, y-5))

            money_label = self.font.render(str(self.opp_money[id]), True, self.money_color, None)
            money_rect = money_label.get_rect(center=(x, y-20))
            self.screen.blit(money_label, money_rect)


    def _draw_buttons(self):
        self.fold_b.draw()
        self.check_b.draw()
        self.raise_b.draw()
        self.raise_t.draw()


    def _draw_table(self):
        self.screen.blit(self.font.render(f'big blind: {self.big_blind}', True, (150, 150, 150), None),
                         (0, 0))

        for i, card in enumerate(self.on_table):
            if card is None:
                break
            self.screen.blit(card, (self.width//2 - (self.card_w//2) - (2-i)*(self.card_w+5), self.height//2))


if __name__=='__main__':
    if len(sys.argv) != 4:
        print('After "python3 poker.py" you have to specify your_nickname server_address server_port')
        exit()

    nick, addr, port = sys.argv[1:]
    poker = Poker(nick, addr, port)
    while 1:
        poker.update()
