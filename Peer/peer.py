from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay
from logger import Logger

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
        self.transport.write("ready".encode("utf-8"), self.server)

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
            elif message_to_send == "developer command":
                continue

            if not isinstance(message_to_send, list):
                message_to_send = [message_to_send]

            for message in message_to_send:
                self.logger.log_message("Supported command: " + message, False)

                for peer_address in self.addresses:
                    self.logger.log_message("Sending a message to: " + str(peer_address), False)
                    self.transport.write(message.encode('utf-8'), peer_address)

    def handle_datagram_from_server(self, datagram: str):
        """Handles messages from the rendezvous server"""
        datagram_data = datagram.split("!")
        if datagram_data[0] == "PLAYER_ORDER":
            # This peer has joined, and peer_addresses contains addresses of all peers

            player_order_number = datagram_data[1]
            self.gameplay.update_order_number(player_order_number)
            peer_addresses = datagram_data[2:]
        else:
            # A new peer has joined, and this peer receives only the new peer's address in peer_addresses
            peer_addresses = datagram_data

        if not peer_addresses[0]:
            # peer_addresses[0] is '' and peer_addresses[1] does not exist
            # for first connected peer, which would break
            # peer_address = (address_port[0], int(address_port[1])) in the for loop
            return
            
        self.logger.log_message("You are being connected to peers.")
        for address in peer_addresses:
            # remove parentheses, spaces and quotes for editing
            address = address.replace("(", "").replace(")", "").replace(" ", "").replace("'", "").replace('"', "")
            address_port = address.split(",")
            peer_address = (address_port[0], int(address_port[1]))
            self.logger.log_message("Connecting to " + str(peer_address), print_message=False)
            if peer_address not in self.addresses and peer_address != self.id:
                self.addresses.append(peer_address)
                self.gameplay.increment_connected_peers_count()
        
        # If this is called here, the first player can't issue commands
        # until at least 1 other peer is connected
        if not self.send_message_thread_active:
            reactor.callInThread(self.send_message)
            self.send_message_thread_active = True

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if addr == self.server:
            # renderzvous server has sent something
            if datagram == "":
                self.logger.log_message("You are the first player online, waiting for connections")
                self.gameplay.deck_host_and_first_player = True
            else:
                self.handle_datagram_from_server(datagram)
        else:
            # a peer has sent something
            splitted_command = datagram.split("!")
            if splitted_command[0].upper() in self.gameplay.supported_incoming_commands:
                self.logger.log_message("Command from: "
                                        + str(addr) + ": " + splitted_command[0], False)
                messages_to_send = self.gameplay.handle_incoming_commands(datagram)
                if messages_to_send:
                    if not isinstance(messages_to_send, list):
                        messages_to_send = [messages_to_send]
                    for message in messages_to_send:
                        for peer_address in self.addresses:
                            self.transport.write(message.encode('utf-8'), peer_address)
            else:
                self.logger.log_message("Message from: " + str(addr) + ": " + datagram)
                self.logger.log_message("Type a command: ")

if __name__ == '__main__':
    port = int(input("Enter a unique port number: "))
    reactor.listenUDP(port, Peer('localhost', port))
    reactor.run()
