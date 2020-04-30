# Poker_LAN

Work in progress...
Maximum number of players: 6

## Setup
Clone the repo, run `./setup.sh`
#### Run as client
`python3 poker.py nickname host_address port`
#### Run as host
`python3 server.py address port number_of_players init_money big_blind`, where `number_of_players`, `init_money` 
and `big_blind` are optional, by default equal respectively `6`, `1000`, `50`.



#### TODO:
- when all-in create new pot
- when only 1 player with money
- graphics

#### Possible:
- implement logouts
- join running game
