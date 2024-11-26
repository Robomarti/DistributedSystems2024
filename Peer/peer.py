# used this video: https://www.youtube.com/watch?v=1Fay1pjttLg as the basis

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
        self.server = ("127.0.0.1",9999)
        self.send_message_thread_active = False
        self.logger = Logger(self.id)
        self.gameplay = Gameplay(self.logger)

        self.logger.log_message("Own address: " + str(self.id), False)

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

            if message_to_send == "":
                # user input was not valid
                self.logger.log_message("Unsupported command")
            elif message_to_send != "developer command":
                # send a valid command to peers
                self.logger.log_message("Supported command: " + message_to_send, False)

                for peer_address in self.addresses:
                    self.logger.log_message("Sending a message to: " + str(peer_address), False)
                    self.transport.write(message_to_send.encode('utf-8'), peer_address)

    def handle_datagram_from_server(self, datagram: str):
        """Handles messages from the rendezvous server"""
        datagram_data = datagram.split("!")
        self.logger.log_message("You are being connected to peers.")

        peer_addresses = datagram_data
        for address in peer_addresses:
            # remove parentheses, spaces and quotes for editing
            address = address.replace("(", "").replace(")", "").replace(" ", "").replace("'", "").replace('"', "")
            address_port = address.split(",")
            self.logger.log_message("Connecting to " + str(address_port), False)
            self.addresses.append((address_port[0], int(address_port[1])))

        if not self.send_message_thread_active:
            # Dont worry about pylint errors such as "Module 'twisted.internet.reactor'
            # has no 'callInThread' member", this code still works.
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
                # todo: send all messages in messages_to_send
            else:
                self.logger.log_message("Message from: " + str(addr) + ": " + datagram)
                self.logger.log_message("Type a command: ")

if __name__ == '__main__':
    port = int(input("enter a unique port number: "))
    # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'listenUDP'
    # member", this code still works.
    reactor.listenUDP(port, Peer('localhost', port))
    reactor.run()
