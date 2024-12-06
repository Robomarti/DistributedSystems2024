from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay
from logger import Logger
import random
import socket
import time
import os

class Peer(DatagramProtocol):
    """Handles message sending and receiving"""
    def __init__(self, host, own_port):
        if host == "localhost":
            host = "127.0.0.1"

        self.id = (host, own_port)
        self.addresses = []
        self.server = ("127.0.0.1", 9999)
        self.send_message_thread_active = False
        self.logger = Logger(self.id)
        self.gameplay = Gameplay(self.logger, self.id)

        self.logger.log_message("Own address: " + str(self.id), print_message=False)

    def startProtocol(self):
        """Send a message to the server to get connected to other peers"""
        self.send_message("ready", self.server)

    def send_message(self, message, target_addr):
        """send message to target_addr"""
        self.transport.write(message.encode('utf-8'), target_addr)

    def broadcast(self, message: str):
        """Broadcasts a message to all connected peers"""
        try:
            for peer_address in self.addresses:
                self.transport.write(message.encode("utf-8"), peer_address)
            self.logger.log_message(f"Broadcast message: {message}", print_message=True)
        except Exception as e:
            self.logger.log_message(f"Error broadcasting message: {e}", print_message=True)

    def handle_type_command(self):
        """Handles gathering user input and sending messages to connected peers"""
        while True:
            self.logger.log_message("Type a command: ")
            user_input = input()
            self.logger.log_message(user_input, False)

            # Decide what to send to peers
            message_to_send = self.gameplay.handle_input(user_input)

            if not message_to_send:
                self.logger.log_message("Unsupported command")
                continue
            elif message_to_send == "dont-send":
                continue

            # Ensure message_to_send is a list
            if not isinstance(message_to_send, list):
                message_to_send = [message_to_send]

            # Log and send each message
            self._log_and_send_messages(message_to_send)

    def _log_and_send_messages(self, messages):
        """Logs and sends messages to all connected peers with error tolerance"""
        for message in messages:
            self.logger.log_message("Supported command: " + message, False)
            for peer_address in self.addresses:
                try:
                    self.logger.log_message("Sending a message to: " + str(peer_address), False)
                    self.send_message(message, peer_address)
                except Exception as e:
                    self.logger.log_message(f"Error sending message to {peer_address}: {e}", print_message=True)


    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        print("Received datagram: ", datagram)
        if addr == self.server:
            self.handle_datagram_from_server(datagram)
        else:
            self.handle_datagram_from_peer(datagram, addr)

    def handle_datagram_from_peer(self, datagram: str, addr):
        """Handles messages from other peers"""
        try:
            splitted_command = datagram.split("!")

            if splitted_command[0].upper() in self.gameplay.supported_incoming_commands:
                self.logger.log_message(f"Command from {addr}: {splitted_command[0]}", False)

                messages_to_send = self.gameplay.handle_incoming_commands(datagram)
                if messages_to_send:
                    if not isinstance(messages_to_send, list):
                        messages_to_send = [messages_to_send]

                    for message in messages_to_send:
                        for peer_address in self.addresses:
                            self.transport.write(message.encode("utf-8"), peer_address)
            else:
                self.logger.log_message(f"Message from {addr}: {datagram}")
                self.logger.log_message("Type a command: ", print_message=True)

        except Exception as e:
            self.logger.log_message(f"Error handling datagram from {addr}: {e}", print_message=True)


    def handle_datagram_from_server(self, datagram: str):
        """Handles messages from the rendezvous server"""
        datagram_data = datagram.split("!")
        if datagram_data[0] == "PLAYER_ORDER":
            self.handle_player_order(datagram_data)

        if datagram_data[0] == "NEW_CLIENT":
            self.handle_new_client(datagram_data)
        
        # If this is called here, the first player can't issue commands
        # until at least 1 other peer is connected
        if not self.send_message_thread_active and self.addresses:
            reactor.callInThread(self.handle_type_command)
            self.send_message_thread_active = True

    def handle_player_order(self, datagram_data):
        """Handles the player order message from the server"""
        try:
            self.player_order_number = int(datagram_data[1]) 
            
            if self.player_order_number == 1:
                self.logger.log_message("You are the first player online, waiting for connections")
                self.gameplay.deck_host_and_first_player = True
                return
            
            self.gameplay.update_order_number(self.player_order_number)

            peer_list = datagram_data[2:]
            for peer in peer_list:
                try:
                    ip, port = peer.split(":")
                    peer_tuple = (ip, int(port))
                    self.add_peer_address(peer_tuple)
                except ValueError as e:
                    self.logger.log_message(f"Error parsing peer address {peer}: {e}", print_message=True)

            print(f"Connected peers: {self.addresses}")
        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing player order message: {e}", print_message=True)
            self.player_order_number = int(datagram_data[1])

    def handle_new_client(self, datagram_data):
        """Handles the new client message from the server"""
        try:
            new_client_address = datagram_data[1]
            self.logger.log_message("New client connected: " + new_client_address)
            
            ip, port = new_client_address.split(":")
            new_client_tuple = (ip, int(port))
            self.add_peer_address(new_client_tuple)
        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing new client message: {e}", print_message=True)


    def add_peer_address(self, peer_address):
        """Adds a peer address to the list of addresses"""
        if not isinstance(peer_address, tuple) or len(peer_address) != 2:
            self.logger.log_message(f"Invalid peer address format: {peer_address}", print_message=True)
            return False

        if peer_address not in self.addresses and peer_address != self.id:
            self.addresses.append(peer_address)
            self.gameplay.increment_connected_peers_count()
            self.logger.log_message(f"Peer {peer_address} added.", print_message=False)
            return True
        else:
            self.logger.log_message(f"Peer {peer_address} already exists or is self.", print_message=False)
            return False

def peer_start():
    """Finds an available port for the peer to use"""
    os.system('clear')
    print("Starting peer...")
    while True:
        port = random.randint(1024, 65535)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return port
            except OSError:
                continue
    
if __name__ == '__main__':
    port = peer_start()
    print(f"Using port number: {port}")
    reactor.listenUDP(port, Peer('localhost', port))
    reactor.run()
