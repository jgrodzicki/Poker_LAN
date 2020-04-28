import pygame

from PodSixNet.Connection import ConnectionListener, connection

from collections import defaultdict
import itertools
from time import sleep

from Button import Button
from TextField import TextField


class Poker(ConnectionListener):

    def __init__(self, c1='JH', c2='10H', nickname='grodzik', init_money=1000, players_nick=['p1', 'p2', 'p3', 'p4', 'p5'],
                 big_blind=50):
        # initialize shit
        pygame.init()
        self.width, self.height = 750, 500
        self.card_w, self.card_h = 43, 62
        nick_color, self.money_color = (100, 100, 100), (255, 255, 0)
        # 2
        # initialize the screen
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption('Poker')
        # 3
        # initialize pygame clock
        self.clock = pygame.time.Clock()

        self.is_turn = False
        self.big_blind = big_blind
        self.small_blind = big_blind//2

        # player
        self.card1 = pygame.image.load(f'images/{c1}.png')
        self.card2 = pygame.image.load(f'images/{c2}.png')
        self.money = init_money

        self.back_card = pygame.image.load(f'images/back.png')

        self.font = pygame.font.Font('freesansbold.ttf', 16)
        self.nick = self.font.render(nickname, True, nick_color, None)

        # other players
        self.players_nick = [self.font.render(nick, True, nick_color, None) if nick is not None else None
                             for nick in players_nick]
        self.players_money = [init_money] * len(players_nick)
        self.players_pos = [(self.width*0.75//5, self.height*3//5), (self.width*0.75//5, self.height*1.5//5),
                            (self.width//2, 50), (self.width*4.25//5, self.height*1.5//5),
                            (self.width*4.25//5, self.height*3//5)]

        # cards on the table
        self.on_table = [None] * 5
        # self.on_table = [pygame.image.load(f'images/{card}.png') for card in ['AS', 'AH', 'JH', '3D', 'JC']]

        self.bet = 0
        self.bet_on_table = 0

        self.fold_b = Button('fold', (self.width - 270, self.height-20), self.screen)
        self.check_b = Button('check', (self.width - 180, self.height-20), self.screen)
        self.raise_b = Button('raise', (self.width - 90, self.height-20), self.screen)

        self.raise_t = TextField((self.width - 90, self.height - 50), self.screen)


    def update(self):
        # sleep to make the game 60 fps
        self.clock.tick(60)
        # clear the screen
        self.screen.fill(0)

        for event in pygame.event.get():
            # quit if the quit button was pressed
            if event.type == pygame.QUIT:
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.fold_b.is_clicked():
                    print('fold')
                elif self.check_b.is_clicked():
                    print('check')
                elif self.raise_b.is_clicked():
                    print('raise')
                elif self.raise_t.is_clicked():
                    self.raise_t.click_action()

            elif event.type == pygame.KEYDOWN:
                self.raise_t.update(event.key)

        # draw player
        self.screen.blit(self.card1, (self.width//2 - self.card_w - 5, self.height-100))
        self.screen.blit(self.card2, (self.width//2 + 5, self.height-100))

        nick_rect = self.nick.get_rect(center=(self.width // 2, self.height-20))
        self.screen.blit(self.nick, nick_rect)

        money_label = self.font.render(str(self.money), True, self.money_color, None)
        money_rect = money_label.get_rect(center=(self.width//2, self.height-120))
        self.screen.blit(money_label, money_rect)

        self.fold_b.draw()
        self.check_b.draw()
        self.raise_b.draw()
        self.raise_t.draw()

        # draw others
        for i, nick in enumerate(self.players_nick):
            if nick is None:
                continue
            x, y = self.players_pos[i]
            self.screen.blit(self.back_card, (x-self.card_w-5, y))
            self.screen.blit(self.back_card, (x+5, y))

            nick_rect = nick.get_rect(center=(x, y+70))
            self.screen.blit(nick, nick_rect)

            money_label = self.font.render(str(self.players_money[i]), True, self.money_color, None)
            money_rect = money_label.get_rect(center=(x, y-20))
            self.screen.blit(money_label, money_rect)


        # draw table
        for i, card in enumerate(self.on_table):
            if card is None:
                break
            self.screen.blit(card, (self.width//2 - (self.card_w//2) - (i-2)*(self.card_w+5), self.height//2))

        # update the screen
        pygame.display.update()
        self.clock.tick(60)


    def _check(self):
        pass


    def _call(self):
        if self.bet_on_table - self.bet < self.money:
            self.money -= (self.bet_on_table - self.bet)
            self.bet = self.bet_on_table
        else:
            self.bet += self.money
            self.money = 0


    def _raise(self, amount):
        self.money -= (self.bet - amount)
        self.bet = self.bet_on_table = amount



poker = Poker()
while 1:
    poker.update()
