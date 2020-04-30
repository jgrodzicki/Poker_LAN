import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

from Game import Game

import sys


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

    def __init__(self, no_players=6, init_money=1000, big_blind=50, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)
        self.queue = Game(no_players=no_players)
        self.game = None
        self.no_players = no_players

    def Connected(self, channel, addr):
        print('new connection:', channel)
        self.queue.joined_player(channel)
        print(self.queue.cur_players)

        if self.queue.cur_players == self.no_players:
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


if __name__ == '__main__':
    print('STARTING SERVER ON LOCALHOST')
    if len(sys.argv) < 3:
        print('you have to provide server_address port')
        exit()

    no_players, init_money, big_blind = 6, 1000, 50
    addr, port = sys.argv[1:3]

    try:
        if len(sys.argv) > 3:
            no_players = int(sys.argv[3])
            if no_players > 6 or no_players < 2:
                print('number of players was to be at least 2 and not greater than 6')
                exit()
        if len(sys.argv) > 4:
            init_money = int(sys.argv[4])
            if init_money < 0:
                print('money has to be greater than 0 you dumbass')
                exit()
        if len(sys.argv) > 5:
            big_blind = int(sys.argv[5])
            if big_blind < init_money:
                print('seriously big blind greater than init money?')
                exit()
    except ValueError:
        print('cannot convert values to integers')
        exit()

    pokerServer = PokerServer(localaddr=(addr, int(port)), no_players=no_players,
                              init_money=init_money, big_blind=big_blind)
    try:
        while True:
            pokerServer.Pump()
            sleep(0.01)
    except KeyboardInterrupt:
        pokerServer.close()
