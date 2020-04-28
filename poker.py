import pygame

from PodSixNet.Connection import ConnectionListener, connection

from collections import defaultdict
import itertools
from time import sleep


class Poker(ConnectionListener):

    def __init__(self, c1='JH', c2='10H', nickname='grodzik'):
        # initialize shit
        pygame.init()
        width, height = 550, 450
        card_w, card_h = 43, 62
        # 2
        # initialize the screen
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption('Poker')
        # 3
        # initialize pygame clock
        self.clock = pygame.time.Clock()

        self.card1 = pygame.image.load(f'images/{c1}.png')
        self.card1 = pygame.transform.scale(self.card1, (card_w, card_h))
        self.card2 = pygame.image.load(f'images/{c2}.png')
        self.card2 = pygame.transform.scale(self.card2, (card_w, card_h))

        font = pygame.font.Font('freesansbold.ttf', 16)
        self.nick = font.render(nickname, True, (0, 255, 0), None)

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

        # update the screen
        pygame.display.update()
        self.clock.tick(60)




poker = Poker()
while 1:
    poker.update()
