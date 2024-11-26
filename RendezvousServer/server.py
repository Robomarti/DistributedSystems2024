# used this video: https://www.youtube.com/watch?v=1Fay1pjttLg as basis

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Server(DatagramProtocol):
    """Handles peers finding each other"""
    def __init__(self):
        self.clients = set()

    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if datagram == "ready":
            # Send back list of addresses of every connected peer
            adresses = "!".join([str(x) for x in self.clients])
            self.transport.write(adresses.encode("utf-8"), addr)

            # send connections to connected peers about new connection
            for peer_adress in self.clients:
                self.transport.write(str(addr).encode("utf-8"), peer_adress)

            self.clients.add(addr)

if __name__ == '__main__':
    PORT = 9999
    # Dont worry about pylint errors such as "Module 'twisted.internet.reactor' has no 'listenUDP'
    # member", this code still works.
    reactor.listenUDP(PORT, Server())
    reactor.run()
