import random
import socket
import os
from collections import OrderedDict
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay
from logger import Logger
from heartbeat import HeartbeatManager

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
        self.heartbeat_manager = HeartbeatManager(self)
        self.player_order_number = -1
        self.lamport_clock: int = 0

        self.logger.log_message("Own address: " + str(self.id), print_message=False)

    def startProtocol(self):
        """Send a message to the server to get connected to other peers"""
        self.send_message("ready", self.server)

    def stopProtocol(self):
        """Notify the server about disconnection and stop heartbeat."""
        try:
            self.send_message("disconnect", self.server)
            self.logger.log_message("Sent disconnect message to server.", print_message=False)
        except Exception as e:
            self.logger.log_message(f"Error notifying server about disconnection: {e}", print_message=False)
        self.heartbeat_manager.stop()

    def send_message(self, message, target_addr):
        """send message to target_addr"""
        self.transport.write(message.encode('utf-8'), target_addr)

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
        # increment logical clock
        self.lamport_clock += 1

        for message in messages:
            self.logger.log_message("Supported command: " + message, False)
            for peer_address in self.addresses:
                try:
                    self.logger.log_message("Sending a message to: " + str(peer_address), False)
                    
                    # attach local timestamp
                    message += f"!{self.lamport_clock}"
                    self.send_message(message, peer_address)
                except Exception as e:
                    self.logger.log_message(f"Error sending message to {peer_address}: {e}", print_message=False)


    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if "HEARTBEAT" not in datagram:
            self.logger.log_message(f"Received datagram: {datagram}", False)
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
                    self.logger.log_message(f"Error processing PEER_DISCONNECTED: {str(e)}", False)
                return

            if splitted_command[0].upper() in self.gameplay.supported_incoming_commands:
                self.logger.log_message(f"Command from {addr}: {splitted_command[0]}", False)

                # check message logical clock value
                if int(splitted_command[-1]) <= self.lamport_clock:
                    self.logger.log_message(f"Received old data: {datagram}", False)
                    return
                else:
                    self.lamport_clock = int(splitted_command[-1])
                
                # remove logical clock from the received message
                splitted_command.pop()
                datagram = "!".join(splitted_command)

                messages_to_send = self.gameplay.handle_incoming_commands(datagram)
                if messages_to_send:
                    if not isinstance(messages_to_send, list):
                        messages_to_send = [messages_to_send]

                    self._log_and_send_messages(messages_to_send)
            else:
                self.logger.log_message(f"Message from {addr}: {datagram}")
                self.logger.log_message("Type a command: ", print_message=True)

        except Exception as e:
            self.logger.log_message(f"Error handling datagram from {addr}: {e}", print_message=False)

    def handle_datagram_from_server(self, datagram: str):
        """Handles messages from the rendezvous server"""
        datagram_data = datagram.split("!")
        if datagram_data[0] == "PLAYER_ORDER":
            self.handle_player_order(datagram_data)

        if datagram_data[0] == "NEW_CLIENT":
            self.handle_new_client(datagram_data)

        # new
        elif datagram_data[0] == "PEER_DISCONNECTED":
            self.handle_server_disconnection(datagram_data)
        # If this is called here, the first player can't issue commands
        # until at least 1 other peer is connected
        if not self.send_message_thread_active and self.addresses:
            reactor.callInThread(self.handle_type_command)
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

            peer_list = datagram_data[2:]
            for peer in peer_list:
                try:
                    ip, peer_port = peer.split(":")
                    peer_tuple = (ip, int(peer_port))
                    self.add_peer_address(peer_tuple)
                except ValueError as e:
                    self.logger.log_message(f"Error parsing peer address {peer}: {e}", print_message=False)

        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing player order message: {e}", print_message=False)

    def handle_new_client(self, datagram_data):
        """Handles the new client message from the server"""
        try:
            new_client_address = datagram_data[1]
            self.logger.log_message("New client connected: " + new_client_address, False)
            
            ip, port = new_client_address.split(":")
            new_client_tuple = (ip, int(port))
            self.add_peer_address(new_client_tuple)
        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing new client message: {e}", print_message=False)

    def add_peer_address(self, peer_address):
        """Adds a peer address to both OrderedDicts"""
        if not isinstance(peer_address, tuple) or len(peer_address) != 2:
            self.logger.log_message(f"Invalid peer address format: {peer_address}", print_message=False)
            return False

        if peer_address not in self.addresses and peer_address != self.id:
            self.addresses.append(peer_address)
            self.gameplay.increment_connected_peers_count()
            self.logger.log_message(
                f"Peer {peer_address} added to addresses. Current addresses: {self.addresses}",
            False)
            return True
        else:
            self.logger.log_message(
                f"Peer {peer_address} already exists in addresses or is self.", print_message=False
            )
            return False

    def handle_peer_disconnection(self, disconnected_peer):
        """Handles logic when a peer disconnects"""
        try:
            disconnected_peer_index = None
            try:
                self.logger.log_message(f"Disconnected peer: {disconnected_peer}", True)
                disconnected_peer_index = self.addresses.index(disconnected_peer)
            except ValueError as _: # sometimes peers also can try to access the same value
                pass

            if disconnected_peer_index != None:
                self.gameplay.synchronize_turn_orders(disconnected_peer_index, self.addresses)
                self.gameplay.synchronize_passes(disconnected_peer_index)
                self.gameplay.synchronize_points(disconnected_peer_index)

            self.addresses.remove(disconnected_peer)
        except KeyError as _:
            pass # all peers will try to access the key, which may not exist, so this is passed
        except Exception as e:
            self.logger.log_message(f"Error handling PEER_DISCONNECTED: {str(e)}")

    def handle_server_disconnection(self, datagram_data):
        """Handle disconnection messages from the server."""
        try:
            disconnected_peer_ip = datagram_data[1]
            disconnected_peer_port = int(datagram_data[2])
            disconnected_peer = (disconnected_peer_ip, disconnected_peer_port)
            self.handle_peer_disconnection(disconnected_peer)
            self.logger.log_message(f"Peer {disconnected_peer} disconnected (by server).", print_message=False)
        except (IndexError, ValueError) as e:
            self.logger.log_message(f"Error processing server disconnection message: {e}", False)

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
