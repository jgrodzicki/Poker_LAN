import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

from Game import Game


class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)


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
            for i, ch in enumerate(self.game.player_channels):
                ch.Send({'action': 'startgame', 'init_money': 1000, 'big_blind': 50, 'players_nick': ['p1', 'p2', 'p3', 'p4', 'p5']})
                ch.Send({'action': 'getcards', 'cards': self.game.cards[i]})


    def fold(self, data):
        self.game.fold(data)


print("STARTING SERVER ON LOCALHOST")
pokerServer = PokerServer(localaddr=('0.0.0.0', 8000))
try:
    while True:
        pokerServer.Pump()
        sleep(0.01)
except KeyboardInterrupt:
    pokerServer.close()