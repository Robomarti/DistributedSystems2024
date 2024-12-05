import os
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from collections import OrderedDict

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        # Using ordered dict guarantees that the clients are added to the 
        # dict in the order they join the rendezvous server
        # this makes it much easier to manage turn order states
        self.clients = OrderedDict()

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        print(f"Received message: {datagram} from {addr}")

        if datagram == "ready":
            if addr not in self.clients:
                self.clients[addr] = None
                print("Client connected: ", addr)
                ordered_addresses = "!".join([f"{x[0]}:{x[1]}" for x in self.clients.keys()])
                player_order_number = len(self.clients)
                message = f"PLAYER_ORDER!{player_order_number}!{ordered_addresses}"
                self.transport.write(message.encode("utf-8"), addr)
                self.broadcast(f"NEW_CLIENT!{addr[0]}:{addr[1]}", exclude=addr)

    def broadcast(self, message, exclude=None):
        """Broadcast a message to all clients"""
        for peer_address in self.clients.keys():
            if peer_address != exclude:
                self.transport.write(message.encode("utf-8"), peer_address)

if __name__ == '__main__':
    os.system("clear")
    print("Starting server...")
    PORT = 9999
    reactor.listenUDP(PORT, Server())
    print(f"Server is running on UDP port {PORT}")
    reactor.run()
