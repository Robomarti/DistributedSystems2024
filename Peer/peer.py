import random
import socket
import os
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay
from logger import Logger
from heartbeat import HeartbeatManager
from collections import OrderedDict

class Peer(DatagramProtocol):
    """Handles message sending and receiving"""
    def __init__(self, host, own_port):
        if host == "localhost":
            host = "127.0.0.1"

        self.id = (host, own_port)
        self.addresses = OrderedDict()
        self.all_addresses = OrderedDict()
        self.server = ("127.0.0.1", 9999)
        self.send_message_thread_active = False
        self.logger = Logger(self.id)
        self.gameplay = Gameplay(self.logger, self.id)
        self.heartbeat_manager = HeartbeatManager(self)

        self.logger.log_message("Own address: " + str(self.id), print_message=False)

    def startProtocol(self):
        """Send a message to the server to get connected to other peers"""
        self.send_message1("ready", self.server)

    def stopProtocol(self):
        """Notify the server about disconnection and stop heartbeat."""
        try:
            self.send_message1("disconnect", self.server)
            self.logger.log_message("Sent disconnect message to server.", print_message=True)
        except Exception as e:
            self.logger.log_message(f"Error notifying server about disconnection: {e}", print_message=True)
        self.heartbeat_manager.stop()

    def send_message1(self, message, target_addr):
        """send message to target_addr"""
        self.transport.write(message.encode('utf-8'), target_addr)

    def broadcast(self, message: str):
        """Broadcasts a message to all connected peers"""
        try:
            for peer_address in self.addresses.keys():
                self.transport.write(message.encode("utf-8"), peer_address)
            self.logger.log_message(f"Broadcast message: {message}", print_message=True)
        except Exception as e:
            self.logger.log_message(f"Error broadcasting message: {e}", print_message=True)

    def send_message(self):
        """Handles gathering user input and sending messages to connected peers"""
        while True:
            self.logger.log_message("Type a command: ")
            user_input = input()
            self.logger.log_message(user_input, False)

            # decide what to send to peers
            message_to_send = self.gameplay.handle_input(user_input)

            if not message_to_send:
                self.logger.log_message("Unsupported command")
                continue
            elif message_to_send == "dont-send":
                continue

            if not isinstance(message_to_send, list):
                message_to_send = [message_to_send]

            for message in message_to_send:
                self.logger.log_message("Supported command: " + message, False)

                for peer_address in self.addresses:
                    self.logger.log_message("Sending a message to: " + str(peer_address), False)
                    self.transport.write(message.encode('utf-8'), peer_address)

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if "HEARTBEAT" not in datagram:
            print("Received datagram: ", datagram)
        if addr == self.server:
            self.handle_datagram_from_server(datagram)
        else:
            self.handle_other_datagrams(datagram, addr)

    def handle_other_datagrams(self, datagram: str, addr):
        """Handles messages from other peers and heartbeat manager"""
        try:
            splitted_command = datagram.split("!")

            if splitted_command[0] == "HEARTBEAT":
                self.heartbeat_manager.record_heartbeat(addr)
                return

            if splitted_command[0] == "PEER_DISCONNECTED":
                try:
                    disconnected_peer = (splitted_command[1], int(splitted_command[2]))
                    self.handle_peer_disconnection(disconnected_peer)
                except Exception as e:
                    self.logger.log_message(f"Error processing PEER_DISCONNECTED: {str(e)}", True)
                return

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
            reactor.callInThread(self.send_message)
            self.send_message_thread_active = True
            self.heartbeat_manager.start()

    def handle_player_order(self, datagram_data):
        """Handles the player order message from the server"""
        try:
            self.player_order_number = int(datagram_data[1])

            if self.player_order_number == 1:
                self.logger.log_message("You are the first player online, waiting for connections")

            if self.gameplay.own_turn_identifier == -1:
                self.gameplay.update_order_number(self.player_order_number - 1)

            self.logger.log_message(f"PLAYER ORDER NUMBER {self.player_order_number}")

            peer_list = datagram_data[2:]
            for peer in peer_list:
                try:
                    ip, port = peer.split(":")
                    peer_tuple = (ip, int(port))
                    self.add_peer_address(peer_tuple)
                except ValueError as e:
                    self.logger.log_message(f"Error parsing peer address {peer}: {e}", print_message=True)

            if self.id not in self.all_addresses:
                self.all_addresses[self.id] = None

            print(f"Connected peers: {list(self.addresses.keys())}")
            print(f"All peers: {list(self.all_addresses.keys())}")
        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing player order message: {e}", print_message=True)

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
        """Adds a peer address to both OrderedDicts"""
        self.logger.log_message(f"Trying to add peer address: {peer_address}, self.id: {self.id}")
        if not isinstance(peer_address, tuple) or len(peer_address) != 2:
            self.logger.log_message(f"Invalid peer address format: {peer_address}", print_message=True)
            return False

        if peer_address not in self.all_addresses:
            self.all_addresses[peer_address] = None

        if peer_address not in self.addresses and peer_address != self.id:
            self.addresses[peer_address] = None
            self.gameplay.increment_connected_peers_count()
            self.logger.log_message(
                f"Peer {peer_address} added to addresses. Current addresses: {list(self.addresses.keys())}"
            )
            return True
        else:
            self.logger.log_message(
                f"Peer {peer_address} already exists in addresses or is self.", print_message=False
            )
            return False

    def handle_peer_disconnection(self, disconnected_peer):
        """Handles logic when a peer disconnects"""
        try:
            try:
                disconnected_peer_index = list(self.all_addresses.keys()).index(disconnected_peer)
            except ValueError:
                self.logger.log_message(f"Disconnected peer {disconnected_peer} not found in all_addresses!", True)
                return

            self.gameplay.synchronize_turn_orders(disconnected_peer_index, self.all_addresses)
            self.gameplay.synchronize_passes(disconnected_peer_index)
            self.gameplay.synchronize_points(disconnected_peer_index)

            del self.all_addresses[disconnected_peer]
            del self.addresses[disconnected_peer]
        except Exception as e:
            self.logger.log_message(f"Error handling PEER_DISCONNECTED: {str(e)}")

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
