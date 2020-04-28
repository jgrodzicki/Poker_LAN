import pygame

from PodSixNet.Connection import ConnectionListener, connection

from collections import defaultdict
import itertools
from time import sleep


class Poker(ConnectionListener):

    def __init__(self, c1='JH', c2='10H', nickname='grodzik', players_nick=['p1', 'p2', 'p3', 'p4', 'p5']):
        # initialize shit
        pygame.init()
        width, height = 550, 450
        # card_w, card_h = 43, 62
        # 2
        # initialize the screen
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Poker')
        # 3
        # initialize pygame clock
        self.clock = pygame.time.Clock()

        # player
        self.card1 = pygame.image.load(f'images/{c1}.png')
        # self.card1 = pygame.transform.scale(self.card1, (card_w, card_h))
        self.card2 = pygame.image.load(f'images/{c2}.png')
        # self.card2 = pygame.transform.scale(self.card2, (card_w, card_h))

        self.back_card = pygame.image.load(f'images/back.png')

        font = pygame.font.Font('freesansbold.ttf', 16)
        self.nick = font.render(nickname, True, (0, 255, 0), None)

        # other players
        self.players_nick = [font.render(nick, True, (0, 255, 0), None) for nick in players_nick]
        self.players_pos = [(50, 250), (50, 100), (250, 50), (450, 100), (450, 250)]
        # self.connect()

    def update(self):
        # sleep to make the game 60 fps
        self.clock.tick(60)
        # clear the screen
        self.screen.fill(0)

        for event in pygame.event.get():
            # quit if the quit button was pressed
            if event.type == pygame.QUIT:
                exit()

        self.screen.blit(self.card1, (225, 350))
        self.screen.blit(self.card2, (275, 350))
        self.screen.blit(self.nick,  (240, 320))


        for i, nick in enumerate(self.players_nick):
            x, y = self.players_pos[i]
            self.screen.blit(self.back_card, (x-25, y))
            self.screen.blit(self.back_card, (x+25, y))
            self.screen.blit(nick, (x-10, y-25))


        # update the screen
        pygame.display.update()
        self.clock.tick(60)




poker = Poker()
while 1:
    poker.update()
