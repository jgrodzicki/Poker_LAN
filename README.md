# Poker_LAN

Work (probably not) in progress...

Quickly writen python code to play poker with homies using Hamachi (minecraft vibes) using `pygame`, `PodSixNet` and `numpy`.
Maximum number of players: 6

#### Run as client
`python3 poker.py nickname host_address port`
#### Run as host
`python3 server.py address port number_of_players init_money big_blind`

where `number_of_players`, `init_money` and `big_blind` are optional, by default equal `2`, `1000`, `50` respectively.
`number_of_players` describes minimal number of players to start the game.


#### TODO:
- when all-in create new pot
- graphics lol
- logging out before taking action makes 1 player make action twice during that round and last player can't log out
