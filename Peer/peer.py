"used this video: https://www.youtube.com/watch?v=1Fay1pjttLg"

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from gameplay import Gameplay

class Peer(DatagramProtocol):
    def __init__(self, host, port):
        if host == "localhost":
            host = "127.0.0.1"

        self.id = (host, port)
        self.addresses = []
        self.server = ("127.0.0.1",9999)
        self.send_message_thread_active = False
        self.gameplay = Gameplay()

        print("Working on id: ", self.id)

    def startProtocol(self):
        self.transport.write("ready".encode("utf-8"), self.server)

    def send_message(self):
        while True:
            message_to_send = input("Type a message: ")
            for peer_address in self.addresses:
                print("Sending a message to", peer_address)
                self.transport.write(message_to_send.encode('utf-8'), peer_address)

    def handle_datagram(self, datagram):
        datagram_data = datagram.split("!")
        if datagram_data[0] == "CREATE_DECK":
            deck = []
            for index in range(1, len(datagram_data)):
                deck.append(datagram_data[index])
            self.gameplay.create_deck(deck)
        else:
            print("Peers you are being connected to:")

            peer_addresses = datagram_data
            for address in peer_addresses:
                # remove parentheses, spaces and quotes for editing
                address = address.replace("(", "").replace(")", "").replace(" ", "").replace("'", "").replace('"', "")
                address_port = address.split(",")
                print(address_port)
                self.addresses.append((address_port[0], int(address_port[1])))

            if not self.send_message_thread_active:
                reactor.callInThread(self.send_message)
                self.send_message_thread_active = True

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if addr == self.server:
            if datagram == "":
                print("No other connections yet.")
                self.gameplay.create_deck()
            else:
                self.handle_datagram(datagram)
        else:
            print("Message from: ", addr, ":", datagram)

if __name__ == '__main__':
    port = int(input("enter a unique port number: "))
    # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'listenUDP'
    # member", this code still works.
    reactor.listenUDP(port, Peer('localhost', port))
    reactor.run()
