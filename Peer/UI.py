import random
import pygame
from pygame.locals import *
from peer import Peer
from twisted.internet import reactor

pygame.init()

# screnn
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FONT = pygame.font.Font(None, 30)
BIG_FONT = pygame.font.Font(None, 50)

class BlackjackUI:
    def __init__(self, peer: Peer):
        self.peer = peer
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Peer-to-Peer Blackjack")
        self.clock = pygame.time.Clock()
        self.running = True
        self.log_messages = []
        self.status_message = "Waiting for players..."
        self.state = "waiting"

        # register
        self.peer.register_ui_callback(self.update_ui_state)

        # button
        button_width, button_height = 200, 50
        button_spacing = 20
        total_button_width = 2 * button_width + button_spacing
        start_x = (SCREEN_WIDTH - total_button_width) // 2

        self.buttons = {
            "initiate_game": pygame.Rect((SCREEN_WIDTH // 2 - button_width // 2, 500), (button_width, button_height)),
            "draw_card": pygame.Rect((start_x, 500), (button_width, button_height)),
            "pass_turn": pygame.Rect((start_x + button_width + button_spacing, 500), (button_width, button_height)),
        }

    def update_ui_state(self, command: str):
        if command == "INITIATE_GAME":
            if self.state != "game":
                self.status_message = "Game started!"
                self.state = "game"
                self.log_messages.append("Game initialized!")
        elif command.startswith("DRAW_CARD"):
            _, card_value = command.split("!")
            self.log_messages.append(f"A player drew a card: {card_value}")
        elif command == "PASS_TURN":
            self.log_messages.append("A player passed their turn.")

    def draw_ui(self):
        self.screen.fill((30, 30, 30))

        # title
        title = BIG_FONT.render("Peer-to-Peer Blackjack", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # status info
        status_text = FONT.render(self.status_message, True, (200, 200, 200))
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 100))

        # player info
        player_count = len(self.peer.addresses)
        player_count_text = FONT.render(f"Connected Players: {player_count}", True, (255, 255, 255))
        self.screen.blit(player_count_text, (50, 150))

        # player list
        y_offset = 200
        self.screen.blit(FONT.render("Player List:", True, (255, 255, 255)), (50, y_offset))
        y_offset += 30
        for idx, addr in enumerate(self.peer.addresses, start=1):
            player_text = FONT.render(f"Player {idx}: {addr[0]}:{addr[1]}", True, (200, 200, 200))
            self.screen.blit(player_text, (50, y_offset))
            y_offset += 30

        # button
        for key, rect in self.buttons.items():
            if key == "initiate_game" and not self.peer.is_first_player():
                continue
            pygame.draw.rect(self.screen, (50, 150, 50), rect)
            text = FONT.render(key.replace("_", " ").title(), True, (255, 255, 255))
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))

        # log
        y_offset = 300
        for message in self.log_messages[-5:]:
            log_text = FONT.render(message, True, (200, 200, 200))
            self.screen.blit(log_text, (SCREEN_WIDTH // 2 - log_text.get_width() // 2, y_offset))
            y_offset += 30



    def handle_event(self, event):
        if event.type == QUIT:
            self.running = False
        elif event.type == MOUSEBUTTONDOWN:
            if self.state == "waiting":
                if self.buttons["initiate_game"].collidepoint(event.pos):
                    if len(self.peer.addresses) <= 1:
                        self.status_message = "Waiting for other players to join..."
                        self.log_messages.append("Cannot start the game: no other players connected.")
                    else:
                        if self.state != "game":
                            key = "initiate_game"
                            message = self.peer.gameplay.handle_input(key.upper())
                            if message == "dont-send":
                                self.log_messages.append(
                                    f"Cannot execute: {key.upper()}. Check game status or permissions.")
                            elif message:
                                self.send_message_to_peers("INITIATE_GAME")
                                self.log_messages.append("Game initialized! Broadcasting INITIATE_GAME.")
                                self.status_message = "Game started!"
                                self.state = "game"

            elif self.state == "game":
                for key, rect in self.buttons.items():
                    if rect.collidepoint(event.pos):
                        message = self.peer.gameplay.handle_input(key.upper())
                        if message == "dont-send":
                            self.log_messages.append(f"Cannot execute: {key.upper()}. Check game status or permissions.")
                        elif message:
                            self.send_message_to_peers(message)
                            self.log_messages.append(f"Command executed: {key.upper()}")

    def send_message_to_peers(self, message_to_send):
        if not message_to_send or message_to_send == "dont-send":
            return
        if not isinstance(message_to_send, list):
            message_to_send = [message_to_send]
        self.peer._log_and_send_messages(message_to_send)

    def run(self):
        while self.running:
            for event in pygame.event.get():
                self.handle_event(event)

            if self.state == "waiting":
                self.draw_waiting_screen()
            elif self.state == "game":
                self.draw_game_screen()

            pygame.display.flip()
            self.clock.tick(30)

        reactor.stop()

    def draw_waiting_screen(self):
        self.screen.fill((30, 30, 30))

        title = BIG_FONT.render("Waiting Room", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        status_text = FONT.render(self.status_message, True, (200, 200, 200))
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 100))

        player_count = len(self.peer.addresses)
        player_count_text = FONT.render(f"Connected Players: {player_count}", True, (255, 255, 255))
        self.screen.blit(player_count_text, (50, 150))

        y_offset = 200
        self.screen.blit(FONT.render("Player List:", True, (255, 255, 255)), (50, y_offset))
        y_offset += 30
        for idx, addr in enumerate(self.peer.addresses, start=1):
            player_text = FONT.render(f"Player {idx}: {addr[0]}:{addr[1]}", True, (200, 200, 200))
            self.screen.blit(player_text, (50, y_offset))
            y_offset += 30

        if self.peer.is_first_player():
            if player_count > 0:
                button_color = (50, 150, 50)
                button_text = "Init Game"
            else:
                button_color = (100, 100, 100)
                button_text = "Waiting for players"

            pygame.draw.rect(self.screen, button_color, self.buttons["initiate_game"])
            text = FONT.render(button_text, True, (255, 255, 255))
            self.screen.blit(text, (self.buttons["initiate_game"].centerx - text.get_width() // 2,
                                    self.buttons["initiate_game"].centery - text.get_height() // 2))

    def draw_game_screen(self):
        self.screen.fill((30, 30, 30))

        # title
        title = BIG_FONT.render("Peer-to-Peer Blackjack", True, (255, 255, 255))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        # status info
        status_text = FONT.render(self.status_message, True, (200, 200, 200))
        self.screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 100))

        # log
        y_offset = 200
        self.screen.blit(FONT.render("Recent Logs:", True, (255, 255, 255)), (50, y_offset))
        y_offset += 30
        for message in self.log_messages[-5:]:  # 限制显示最近的5条日志
            log_text = FONT.render(message, True, (200, 200, 200))
            self.screen.blit(log_text, (50, y_offset))
            y_offset += 30

        # button
        for key, rect in self.buttons.items():
            if key == "initiate_game":
                continue

            # button background
            pygame.draw.rect(self.screen, (50, 150, 50), rect)

            # button text
            text = FONT.render(key.replace("_", " ").title(), True, (255, 255, 255))
            self.screen.blit(text, (rect.centerx - text.get_width() // 2, rect.centery - text.get_height() // 2))


def start_reactor():
    """Twisted Reactor"""
    reactor.run(installSignalHandlers=False)

def main():
    from threading import Thread
    port = random.randint(1024, 65535)
    peer = Peer('localhost', port)
    reactor.listenUDP(port, peer)

    ui = BlackjackUI(peer)

    reactor_thread = Thread(target=reactor.run, daemon=True)
    reactor_thread.start()

    ui.run()

if __name__ == "__main__":
    main()
