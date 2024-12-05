from typing import Tuple, Dict
from time import time
from twisted.internet import reactor

class HeartbeatManager:
    """Manages heartbeat by constantly checking peers to detect any faults within the system"""

    def __init__(self, peer, heartbeat_interval: float = 1.0, timeout: float = 2.0):
        """
        Initialize the heartbeat manager

        Args:
            peer: Reference to the Peer instance
            heartbeat_interval: How often to send heartbeats (seconds). Default: 1s.
            timeout: How long to wait before considering a peer disconnected (seconds). Default: 2s.
        """
        self.peer = peer
        self.heartbeat_interval = heartbeat_interval
        self.timeout = timeout
        self.last_heartbeats: Dict[Tuple[str, int], float] = {}
        self.check_loop = None
        self.send_loop = None

    def start(self):
        """Start the heartbeat checking and sending loops"""
        self.send_loop = reactor.callLater(0, self.send_heartbeats)
        self.check_loop = reactor.callLater(0, self.check_connections)

    def stop(self):
        """Stop the heartbeat checking and sending loops"""
        if self.check_loop and self.check_loop.active():
            self.check_loop.cancel()
        if self.send_loop and self.send_loop.active():
            self.send_loop.cancel()

    def send_heartbeats(self):
        """Send heartbeat messages to all connected peers"""
        for peer_address in self.peer.addresses:
            self.peer.transport.write("HEARTBEAT!".encode("utf-8"), peer_address)
        self.send_loop = reactor.callLater(self.heartbeat_interval, self.send_heartbeats)

    def check_connections(self):
        """Check for peers that haven't sent heartbeats recently"""
        current_time = time()
        disconnected_peers = []

        for peer_address in self.peer.addresses:
            if peer_address not in self.last_heartbeats:
                self.last_heartbeats[peer_address] = current_time
            elif current_time - self.last_heartbeats[peer_address] > self.timeout:
                disconnected_peers.append(peer_address)
    
        for peer_address in disconnected_peers:
            self.notify_disconnection_to_peers(peer_address)

        self.check_loop = reactor.callLater(self.heartbeat_interval, self.check_connections)

    def notify_disconnection_to_peers(self, peer_address: Tuple[str, int]):
        """Notify peers about a disconnect."""
        if peer_address in self.peer.addresses:
            self.peer.addresses.remove(peer_address)
        if peer_address in self.last_heartbeats:
            del self.last_heartbeats[peer_address]

        self.peer.logger.log_message(f"Peer {peer_address} disconnected due to heartbeat timeout.", print_message=True)

        message = f"PEER_DISCONNECTED!{peer_address[0]}!{peer_address[1]}"
        for addr in self.peer.addresses:
            self.peer.transport.write(message.encode("utf-8"), addr)

    def record_heartbeat(self, peer_address: Tuple[str, int]):
        """Record that we received a heartbeat from a peer"""
        self.last_heartbeats[peer_address] = time()
