import os
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from twisted.internet.task import LoopingCall

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        self.clients = [] # List of connected clients addresses
        self.last_recv = {} # Last receive time for each client
        self.cleanup_loop_time = 15.0 # Cleanup every 15 seconds
        self.inactive_client_timeout = 30.0 # Disconnect inactive clients after 30 seconds

    def startProtocol(self):
        """periodic cleanup start"""
        self.cleanup_task = LoopingCall(self.cleanup_inactive_clients)
        self.cleanup_task.start(self.cleanup_loop_time) # Clean inactive clients every 15 seconds

    def stopProtocol(self):
        """periodic cleanup stop"""
        if hasattr(self, "cleanup_task"):
            self.cleanup_task.stop()
        print("Server stopped")

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        # print(f"Received message: {datagram} from {addr}")
        self.update_last_recv(addr)
        if datagram == "ready":
            self.client_connection(addr)
        elif datagram == "disconnect":
            self.client_disconnection(addr)

    def update_last_recv(self, addr):
        """Update the last receive time for a client"""
        self.last_recv[addr] = reactor.seconds() # Timeout disconnection

    def client_connection(self, addr):
        """Handle a new client connection"""
        if addr not in self.clients:
            self.clients.append(addr)
            self.last_recv[addr] = reactor.seconds()
            print(f"Client connected: {addr}")
            self.player_order()
        else:
            print(f"Client reconnected: {addr}")

    def client_disconnection(self, addr):
        """Handle a client disconnection"""
        if addr in self.clients:
            print(f"Client disconnected: {addr}")
            self.clients.remove(addr)  # Remove the client from the list
            if addr in self.last_recv:
                del self.last_recv[addr]  # Remove the client from the last receive list
            disconnect_message = f"PEER_DISCONNECTED!{addr[0]}!{addr[1]}"
            self.send_all(disconnect_message)
            self.player_order()  # Send the updated player order to clients
        else:
            print(f"Client already disconnected: {addr}")

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
            if current_time - last_time > self.inactive_client_timeout
        ]
        for addr in inactive_clients:
            print(f"Inactive client: {addr}")
            self.client_disconnection(addr)

if __name__ == '__main__':
    os.system("clear")
    print("Starting server...")
    PORT = 9999
    reactor.listenUDP(PORT, Server())
    print(f"Server is running on UDP port {PORT}")
    reactor.run()