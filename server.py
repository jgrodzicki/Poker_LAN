import PodSixNet.Channel
import PodSixNet.Server
from time import sleep

from Game import Game


class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)

    def Network_startgame(self, data):
        pass

    def Network_init(self, data):
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

        if self.queue.cur_players == 2:
            self.game = self.queue
            self.queue = None

            self.game.deal_cards()
            self.game.game_init()

            # self.game.add_nicks()
            # self.game.start_game()


    def fold(self, data):
        print('in server fold')
        self.game.fold(data)

    def info(self, data):
        print('info server -- adding nicks')
        self.game.add_nick(data['player_id'], data['nick'])

        if len(self.game.id_to_nick.keys()) == self.game.cur_players:
            self.game.add_nicks()
            self.game.start_game()


print("STARTING SERVER ON LOCALHOST")
pokerServer = PokerServer(localaddr=('0.0.0.0', 8000))
try:
    while True:
        pokerServer.Pump()
        sleep(0.01)
except KeyboardInterrupt:
    pokerServer.close()