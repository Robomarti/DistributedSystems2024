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
        self.max_send_retries = 3
        self.retry_delay = 0.5

    def start(self):
        """Start the heartbeat checking and sending loops"""
        try:
            self.send_loop = reactor.callLater(0, self.send_heartbeats)
            self.check_loop = reactor.callLater(0, self.check_connections)
        except Exception as e:
            self.peer.logger.log_message(f"Error starting heartbeat manager: {e}", print_message=True)

    def stop(self):
        """Stop the heartbeat checking and sending loops"""
        try:
            if self.check_loop and self.check_loop.active():
                self.check_loop.cancel()
            if self.send_loop and self.send_loop.active():
                self.send_loop.cancel()
        except Exception as e:
            self.peer.logger.log_message(f"Error stopping heartbeat manager: {e}", print_message=True)

    def send_heartbeats(self, retry_count: int = 0):
        """Send heartbeat messages to all connected peers with retry logic"""
        try:
            for peer_address in self.peer.addresses[:]:
                try:
                    self.peer.transport.write("HEARTBEAT!".encode("utf-8"), peer_address)
                except PermissionError:
                    if retry_count < self.max_send_retries:
                        reactor.callLater(
                            self.retry_delay,
                            self.send_heartbeats,
                            retry_count + 1
                        )
                        return
                    else:
                        self.peer.logger.log_message(
                            f"Failed to send heartbeat to {peer_address} after {self.max_send_retries} retries",
                            print_message=True
                        )
                        self.handle_send_failure(peer_address)
                except Exception as e:
                    self.peer.logger.log_message(
                        f"Error sending heartbeat to {peer_address}: {e}",
                        print_message=True
                    )
                    self.handle_send_failure(peer_address)
            self.send_loop = reactor.callLater(self.heartbeat_interval, self.send_heartbeats, 0)
        except Exception as e:
            self.peer.logger.log_message(f"Error in send_heartbeats: {e}", print_message=True)
            self.send_loop = reactor.callLater(self.heartbeat_interval, self.send_heartbeats, 0)

    def handle_send_failure(self, peer_address: Tuple[str, int]):
        """Handle cases where sending heartbeat consistently fails"""
        self.notify_disconnection_to_peers(peer_address)

    def check_connections(self):
        """Check for peers that haven't sent heartbeats recently"""
        try:
            current_time = time()
            disconnected_peers = []

            for peer_address in self.peer.addresses[:]:
                if peer_address not in self.last_heartbeats:
                    self.last_heartbeats[peer_address] = current_time
                elif current_time - self.last_heartbeats[peer_address] > self.timeout:
                    disconnected_peers.append(peer_address)
        
            for peer_address in disconnected_peers:
                self.notify_disconnection_to_peers(peer_address)

            self.check_loop = reactor.callLater(self.heartbeat_interval, self.check_connections)
        except Exception as e:
            self.peer.logger.log_message(f"Error in check_connections: {e}", print_message=True)
            self.check_loop = reactor.callLater(self.heartbeat_interval, self.check_connections)

    def notify_disconnection_to_peers(self, peer_address: Tuple[str, int]):
        """Notify peers about a disconnect."""
        try:
            if peer_address in self.peer.addresses:
                self.peer.player_manager.remove_player(peer_address)
            if peer_address in self.last_heartbeats:
                del self.last_heartbeats[peer_address]

            self.peer.logger.log_message(
                f"Peer {peer_address} disconnected due to heartbeat timeout.",
                print_message=True
            )

            message = f"PEER_DISCONNECTED!{peer_address[0]}!{peer_address[1]}"
            remaining_peers = [addr for addr in self.peer.addresses if addr != peer_address]
            
            for addr in remaining_peers:
                try:
                    self.peer.transport.write(message.encode("utf-8"), addr)
                except Exception as e:
                    self.peer.logger.log_message(
                        f"Error notifying {addr} about disconnect: {e}",
                        print_message=True
                    )
        except Exception as e:
            self.peer.logger.log_message(
                f"Error in notify_disconnection_to_peers: {e}",
                print_message=True
            )

    def record_heartbeat(self, peer_address: Tuple[str, int]):
        """Record that we received a heartbeat from a peer"""
        try:
            self.last_heartbeats[peer_address] = time()
        except Exception as e:
            self.peer.logger.log_message(
                f"Error recording heartbeat from {peer_address}: {e}",
                print_message=True
            )
