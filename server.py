import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

from Game import Game


class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)

    def Network_fold(self, data):
        self._server.fold(data)

    def Network_check(self, data):
        self._server.check(data)

    def Network_call(self, data):
        self._server.call(data)

    def Network_raise(self, data):
        self._server.raise_(data)

    def Network_logout(self, data):
        self._server.logout(data)

    def Network_info(self, data):
        self._server.info(data)


class PokerServer(PodSixNet.Server.Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.queue = Game()
        self.game = None

    def Connected(self, channel, addr):
        print('new connection:', channel)
        self.queue.joined_player(channel)
        print(self.queue.cur_players)

        if self.queue.cur_players == 3:
            self.game = self.queue
            self.queue = None

            self.game.deal_cards()
            self.game.game_init()

    def fold(self, data):
        self.game.fold(data)

    def check(self, data):
        self.game.check(data)

    def call(self, data):
        self.game.call(data)

    def raise_(self, data):
        self.game.raise_(data)

    def logout(self, data):
        self.game.logout(data['player_id'])

    def info(self, data):
        self.game.add_nick(data['player_id'], data['nick'])

        if len(self.game.id_to_nick.keys()) == self.game.cur_players:
            self.game.start_game()
            self.game.next_round()


print("STARTING SERVER ON LOCALHOST")
pokerServer = PokerServer(localaddr=('0.0.0.0', 8000))
try:
    while True:
        pokerServer.Pump()
        sleep(0.01)
except KeyboardInterrupt:
    pokerServer.close()
