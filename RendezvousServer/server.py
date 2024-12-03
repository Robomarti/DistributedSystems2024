# used this video: https://www.youtube.com/watch?v=1Fay1pjttLg as basis

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import os

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        self.clients = set()

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        print(f"Received message: {datagram} from {addr}")

        if datagram == "ready":
            # Add the client to the set of clients
            self.clients.add(addr)
            print("Client connected: ", addr)

            # Send the client the order number and the addresses of all other clients
            adresses = "!".join([f"{x[0]}:{x[1]}" for x in self.clients])
            player_order_number = len(self.clients)
            message = f"PLAYER_ORDER!{player_order_number}!{adresses}"
            self.transport.write(message.encode("utf-8"), addr)

            # Broadcast to all other clients that a new client has connected
            self.broadcast(f"NEW_CLIENT!{addr[0]}:{addr[1]}", exclude=addr)

    def broadcast(self, message, exclude=None):
        """Broadcast a message to all clients"""
        for peer_address in self.clients:
            if peer_address != exclude:
                self.transport.write(message.encode("utf-8"), peer_address)

if __name__ == '__main__':
    os.system("clear")
    print("Starting server...")
    PORT = 9999
    # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'listenUDP'
    # member", this code still works.
    reactor.listenUDP(PORT, Server())
    print(f"Server is running on UDP port {PORT}")
    reactor.run()
