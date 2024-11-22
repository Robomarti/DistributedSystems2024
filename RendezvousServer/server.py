"used this video: https://www.youtube.com/watch?v=1Fay1pjttLg"

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

class Server(DatagramProtocol):
    def __init__(self):
        self.clients = set()
    
    def datagramReceived(self, datagram: bytes, addr):
        datagram = datagram.decode("utf-8")
        if datagram == "ready":
            adresses = "\n".join([str(x) for x in self.clients])
            self.transport.write(adresses.encode("utf-8"), addr)
            self.clients.add(addr)

if __name__ == '__main__':
    port = 9999
    reactor.listenUDP(port, Server())
    reactor.run()
