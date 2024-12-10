import os
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        self.clients = []
        self.last_recv = {}

    def startProtocol(self):
        """periodic cleanup start"""
        self.cleanup_task = LoopingCall(self.cleanup_inactive_clients)
        self.cleanup_task.start(60.0)

    def stopProtocol(self):
        """periodic cleanup stop"""
        if hasattr(self, "cleanup_task"):
            self.cleanup_task.stop()
        print("Server stopped")

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        print(f"Received message: {datagram} from {addr}")

        self.last_recv[addr] = reactor.seconds() # Timeout disconnection

        if datagram == "ready":
            self.client_connection(addr)
        elif datagram == "disconnect":
            self.client_disconnection(addr)

    def client_connection(self, addr):
        """Handle a new client connection"""
        if addr not in self.clients:
            self.clients.append(addr)
            print(f"Client connected: {addr}")
            self.player_order()

    def client_disconnection(self, addr):
        """Handle a client disconnection"""
        if addr in self.clients:
            print(f"Client disconnected: {addr}")
            if addr in self.clients:
                self.clients.remove(addr)
            del self.last_recv[addr] # Timeout disconnection
            self.player_order()

    def player_order(self):
        """Sends the current player order to clients"""
        addresses = "!".join([f"{x[0]}:{x[1]}" for x in self.clients])
        for index, client_addr in enumerate(self.clients):
            message = f"PLAYER_ORDER!{index}!{addresses}"
            self.transport.write(message.encode("utf-8"), client_addr)

    def send_all(self, message, exclude=None):
        """Send a message to all clients"""
        for peer_address in self.clients:
            if peer_address != exclude:
                self.transport.write(message.encode("utf-8"), peer_address)

    def cleanup_inactive_clients(self):
        """Timeout remove"""
        current_time = reactor.seconds()
        inactive_clients = [
            addr for addr, last_time in self.last_recv.items()
            if current_time - last_time > 300  # Timeout: 300 seconds
        ]
        for addr in inactive_clients:
            print(f"Remove inactive client: {addr}")
            del self.clients[addr]
            del self.last_recv[addr]
            self.player_order()

            disconnect_message = f"PEER_DISCONNECTED!{addr[0]}!{addr[1]}"
            self.send_all(disconnect_message)

if __name__ == '__main__':
    os.system("clear")
    print("Starting server...")
    PORT = 9999
    reactor.listenUDP(PORT, Server())
    print(f"Server is running on UDP port {PORT}")
    reactor.run()
