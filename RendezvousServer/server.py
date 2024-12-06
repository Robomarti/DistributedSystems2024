import os
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from collections import OrderedDict

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        self.clients = OrderedDict()

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        print(f"Received message: {datagram} from {addr}")

        if datagram == "ready":
            self.client_connection(addr)
        elif datagram == "disconnect":
            self.client_disconnection(addr)

    def client_connection(self, addr):
        """Handle a new client connection"""
        if addr not in self.clients:
            self.clients[addr] = None
            print(f"Client connected: {addr}")
            self.player_order()
            self.send_all(f"NEW_CLIENT!{addr[0]}:{addr[1]}", exclude=addr)

    def client_disconnection(self, addr):
        """Handle a client disconnection"""
        if addr in self.clients:
            print(f"Client disconnected: {addr}")
            del self.clients[addr]
            self.player_order()

    def player_order(self):
        """Sends the current player order to clients"""
        addresses = "!".join([f"{x[0]}:{x[1]}" for x in self.clients.keys()])
        for index, client_addr in enumerate(self.clients.keys(), start=1):
            message = f"PLAYER_ORDER!{index}!{addresses}"
            self.transport.write(message.encode("utf-8"), client_addr)

    def send_all(self, message, exclude=None):
        """Send a message to all clients"""
        for peer_address in self.clients:
            if peer_address != exclude:
                self.transport.write(message.encode("utf-8"), peer_address)

if __name__ == '__main__':
    os.system("clear")
    print("Starting server...")
    PORT = 9999
    reactor.listenUDP(PORT, Server())
    print(f"Server is running on UDP port {PORT}")
    reactor.run()
