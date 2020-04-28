import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

from Game import Game


class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)

    def Network_startgame(self, data):
        pass
        # print('start')
        # self.is_waiting_to_start = False
        # self.start(data['init_money'], data['big_blind'], data['players_nick'])
        # self.is_opp_playing = [True] * len(data['players_nick'])
        # self.player_id = data['player_id']
        # if self.player_id == 0:
        #     self.is_turn = True


    def Network_getcards(self, data):
        pass
        # c1, c2 = data['cards']
        # self.card1 = pygame.image.load(f'images/{c1}.png')
        # self.card2 = pygame.image.load(f'images/{c2}.png')


    def Network_fold(self, data):
        print('server fold')
        self._server.fold(data)


class PokerServer(PodSixNet.Server.Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.queue = Game()
        self.game = None

    def Connected(self, channel, addr):
        print('new connection:', channel)
        self.queue.joined_player(channel)
        print(self.queue.no_players)

        if self.queue.cur_players == 2:
            self.game = self.queue
            self.queue = None

            self.game.deal_cards()
            self.game.start_game()
            # print('starting game')
            # for i, ch in enumerate(self.game.player_channels):
            #     ch.Send({'action': 'startgame', 'init_money': self.game.init_money, 'big_blind': self.game.big_blind,
            #              'players_nick': ['p1', 'p2', 'p3', 'p4', 'p5'], 'player_id': i})
            #     # ch.Send({'action': 'getcards', 'cards': self.game.cards[i]})


    def fold(self, data):
        print('in server fold')
        self.game.fold(data)


print("STARTING SERVER ON LOCALHOST")
pokerServer = PokerServer(localaddr=('0.0.0.0', 8000))
try:
    while True:
        pokerServer.Pump()
        sleep(0.01)
except KeyboardInterrupt:
    pokerServer.close()