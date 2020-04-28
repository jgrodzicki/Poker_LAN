import PodSixNet.Channel
import PodSixNet.Server
from time import sleep


class ClientChannel(PodSixNet.Channel.Channel):
    def Network(self, data):
        print(data)


class PokerServer(PodSixNet.Server.Server):
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        PodSixNet.Server.Server.__init__(self, *args, **kwargs)

    def Connected(self, channel, addr):
        print('new connection:', channel)



print("STARTING SERVER ON LOCALHOST")
pokerServer = PokerServer(localaddr=('0.0.0.0', 8000))
while True:
    pokerServer.Pump()
    sleep(0.01)
