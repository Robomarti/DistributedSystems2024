# Peer-To-Peer Blackjack

Peer-To-Peer Blackjack is a Python-based, dealerless Blackjack game designed to operate in a peer-to-peer (P2P) network. The game is played through a command-line interface (CLI), and players can automatically join a game instance by connecting to the Rendezvous Server. Right now, it is required to manually input the IP Address of the Rendezvous Server.
 
## Set up guide

Install requirements

```bash
pip install -r requirements.txt
```

Start Rendezvous Server

```bash
python3 RendezvousServer/server.py
```

Connect a Peer to the Rendezvous Server

```bash
python3 Peer/peer.py 
```

It is assumed that you are running the commands from the root directory of the project.

## Basic game commands

Starting the game

```bash
INITIATE_GAME
```

Drawing a card

```bash
DRAW_CARD
```

Passing

```bash
PASS_TURN
```

Chating with other players

```bash
CHAT <your message here>
```
