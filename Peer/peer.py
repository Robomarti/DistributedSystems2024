"used this video: https://www.youtube.com/watch?v=1Fay1pjttLg"

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay
from logger import Logger

class Peer(DatagramProtocol):
    def __init__(self, host, port):
        if host == "localhost":
            host = "127.0.0.1"

        self.id = (host, port)
        self.addresses = []
        self.server = ("127.0.0.1",9999)
        self.send_message_thread_active = False
        self.gameplay = Gameplay()
        self.logger = Logger(self.id)

        self.logger.log_message("Own address: " + str(self.id), False)

    def startProtocol(self):
        self.transport.write("ready".encode("utf-8"), self.server)

    def send_message(self):
        while True:
            self.logger.log_message("\n"+"Type a message: ")
            message_to_send = input()
            self.logger.log_message(message_to_send, False)
            for peer_address in self.addresses:
                self.logger.log_message("Sending a message to: " + str(peer_address), False)
                self.transport.write(message_to_send.encode('utf-8'), peer_address)

    def handle_datagram(self, datagram):
        datagram_data = datagram.split("!")
        if datagram_data[0] == "CREATE_DECK":
            deck = []
            for index in range(1, len(datagram_data)):
                deck.append(datagram_data[index])
            self.gameplay.create_deck(deck)
        else:
            self.logger.log_message("You are being connected to peers.")

            peer_addresses = datagram_data
            for address in peer_addresses:
                # remove parentheses, spaces and quotes for editing
                address = address.replace("(", "").replace(")", "").replace(" ", "").replace("'", "").replace('"', "")
                address_port = address.split(",")
                self.logger.log_message("Connecting to " + str(address_port), False)
                self.addresses.append((address_port[0], int(address_port[1])))

            if not self.send_message_thread_active:
                # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'callInThread'
                # member", this code still works.
                reactor.callInThread(self.send_message)
                self.send_message_thread_active = True

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if addr == self.server:
            if datagram == "":
                self.logger.log_message("Waiting for connections")
                self.gameplay.create_deck()
            else:
                self.handle_datagram(datagram)
        else:
            self.logger.log_message("Message from: " + str(addr) + ": " + datagram)
            self.logger.log_message("Type a message: ")

if __name__ == '__main__':
    port = int(input("enter a unique port number: "))
    # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'listenUDP'
    # member", this code still works.
    reactor.listenUDP(port, Peer('localhost', port))
    reactor.run()
