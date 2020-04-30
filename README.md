# Poker_LAN

Work (maybe) in progress...

Quickly writen python code to play poker with homies using Hamachi (minecraft vibes).
Maximum number of players: 6

## Setup
Clone the repo `git clone https://github.com/jgrodzicki/Poker_LAN.git` and run `./setup.sh`
#### Run as client
`python3 poker.py nickname host_address port`
#### Run as host
`python3 server.py address port number_of_players init_money big_blind`

where `number_of_players`, `init_money` and `big_blind` are optional, by default equal `6`, `1000`, `50` respectively.


#### TODO:
- when all-in create new pot
- when only 1 player with money
- graphics lol
- logging out before taking action makes 1 player make action twice during that round and last player can't log out

#### Possible:
- join running game
