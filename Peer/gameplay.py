import random
from logger import Logger
from typing import List, Tuple, Optional

class Gameplay:
    """Handles all gameplay-related tasks."""

    def __init__(self, logger: Logger, addresses: List[Tuple[str, int]], player_id: Tuple[str, int]):
        self.deck: List[str] = []
        self.logger = logger
        self.addresses = addresses
        self.player_id = player_id
        self.turn_order: List[Tuple[str, int]] = []
        self.turn_index = 0
        self.points = 0
        self.deck_host_and_first_player = False

        self.supported_incoming_commands = [
            "CREATE_DECK", "DRAW_CARD", "START_GAME",
            "PASS_TURN", "END_GAME", "INVALID_ACTION",
            "SYNC_ERROR", "REQUEST_DECK", "TURN_ORDER"
        ]

        self.cards = [
            "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10", "C11", "C12", "C13", "C14",  # Clubs
            "D02", "D03", "D04", "D05", "D06", "D07", "D08", "D09", "D10", "D11", "D12", "D13", "D14",  # Diamonds
            "H02", "H03", "H04", "H05", "H06", "H07", "H08", "H09", "H10", "H11", "H12", "H13", "H14",  # Hearts
            "S02", "S03", "S04", "S05", "S06", "S07", "S08", "S09", "S10", "S11", "S12", "S13", "S14"   # Spades
        ]

    def create_deck(self, deck_values: Optional[List[str]] = None):
        """Handles creating or importing the deck"""
        if deck_values is None:
            self.logger.log_message("First connected player, creating a deck")
            self.deck = self.cards.copy()
            random.shuffle(self.deck)
        else:
            self.logger.log_message("Importing deck data from a peer")
            self.deck = deck_values

    def handle_input(self, user_input: str):
        """Handles input from the player."""
        # splitted_input splits the input message by question mark
        # e.g. DRAW_CARD!D2!11 -> ["DRAW_CARD", "D2", "11"]
        splitted_input = user_input.split("!")
        input = splitted_input[0].upper()

        if input == "CHAT":
            return self.chat_input(splitted_input)
        elif input == "DRAW_CARD":
            return self.draw_card_input()
        elif input == "PASS_TURN":
            return self.pass_turn_input()
        elif input == "INITIATE_GAME":
            return self.initiate_game_input()
        elif input == "SEND_DECK":
            return self.send_deck()
        elif input == "CLEAR_LOGS":
            self.logger.clear_logs()
            return "developer command"
        elif input == "PRINT_DECK":
            self.logger.log_message(str(self.deck))
            return "developer command"
        else:
            self.logger.log_message("Unsupported user input: " + user_input, print_message=False)
            return ""

    def chat_input(self, splitted_input: List[str]) -> str:
        """Processes CHAT! input."""
        return "!".join(splitted_input[1:])

    def draw_card_input(self) -> str:
        """Processes draw card input."""
        if not self.is_game_initiated():
            self.logger.log_message("The game has not been initiated yet!")
            return ""

        if not self.is_my_turn():
            self.logger.log_message("It's not your turn!")
            return "It's not your turn!"

        if not self.deck:
            self.logger.log_message("The deck is empty!")
            return "The deck is empty!"

        card_drawn = self.deck.pop(0)
        self.add_points(card_drawn)
        self.logger.log_message(f"Drew card: {card_drawn}")
        result_message = f"DRAW_CARD!{card_drawn}!{len(self.deck)}"
        self.advance_player_turn()
        return result_message

    def pass_turn_input(self) -> str:
        """Processes PASS_TURN! input."""
        if not self.is_game_initiated():
            self.logger.log_message("The game has not been initiated yet!", print_message=False)
            return ""

        if not self.is_my_turn():
            self.logger.log_message("It's not your turn!")
            return "It's not your turn!"

        self.logger.log_message("Passed")
        self.advance_player_turn()
        return "PASS_TURN!"

    def initiate_game_input(self) -> List[str]:
        """Processes initiate game input - this can only be done by the leading player."""
        if not self.deck_host_and_first_player:
            self.logger.log_message("You are not the first player; you cannot initiate the game")
            return []

        self.create_deck()
        self.logger.log_message(f"Deck host created deck: {self.deck}", print_message=False)
        self.turn_order = [self.player_id] + [addr for addr in self.addresses if addr != self.player_id]
        turn_order_message = self.send_turn_order()
        deck_message = self.send_deck()
        return [turn_order_message, deck_message]

    def handle_incoming_commands(self, datagram: str) -> List[str]:
        """Handles the commands sent to connected peers (players)."""
        resulting_commands = []
        splitted_command = datagram.split("!")
        command = splitted_command[0].upper()

        self.logger.log_message(f"Handling command from peer: {datagram}", print_message=False)

        if command == "CREATE_DECK":
            self.create_deck_command(splitted_command)
        elif command == "TURN_ORDER":
            self.turn_order_command(splitted_command)
        elif command == "DRAW_CARD":
            resulting_commands.extend(self.draw_card_command(splitted_command))
        elif command == "PASS_TURN":
            self.pass_turn_command()
        elif command == "START_GAME":
            self.logger.log_message("Game started")
        elif command == "END_GAME":
            self.logger.log_message("Game ended")
        elif command == "INVALID_ACTION":
            self.logger.log_message("Invalid action")
        elif command == "SYNC_ERROR":
            self.logger.log_message("Sync error detected")
            resulting_commands.append("REQUEST_DECK")
        elif command == "REQUEST_DECK":
            self.logger.log_message("Peer requests deck values", print_message=False)
            resulting_commands.append(self.send_deck())

        return resulting_commands

    def create_deck_command(self, splitted_command: List[str]):
        """Processes CREATE_DECK! command."""
        deck_values = splitted_command[1:]
        self.create_deck(deck_values)
        self.logger.log_message(f"Deck created: {self.deck}", print_message=False)

    def turn_order_command(self, splitted_command: List[str]):
        """Processes TURN_ORDER! command."""
        self.turn_order = [
            tuple(player_str.split(":")) for player_str in splitted_command[1:]
        ]
        self.turn_order = [(host, int(port)) for host, port in self.turn_order]
        self.logger.log_message(f"Updated turn order: {self.turn_order}")
        self.turn_index = 0

    def draw_card_command(self, splitted_command: List[str]) -> List[str]:
        """Processes DRAW_CARD! command."""
        resulting_commands = []
        card_drawn = splitted_command[1]
        deck_length = int(splitted_command[2])
        self.logger.log_message(f"Peer drew card: {card_drawn}")
        self.logger.log_message(f"Current length of peer's deck: {deck_length}", print_message=False)

        if card_drawn in self.deck:
            drawn_card_index = self.deck.index(card_drawn)
            self.deck = self.deck[drawn_card_index + 1:]
        else:
            self.logger.log_message("Card not found in deck; possible desynchronization")
            resulting_commands.extend(["SYNC_ERROR!", "REQUEST_DECK"])

        if deck_length != len(self.deck):
            resulting_commands.extend(["SYNC_ERROR!", "REQUEST_DECK"])

        self.advance_player_turn()
        return resulting_commands

    def pass_turn_command(self):
        """Processes PASS_TURN! command."""
        self.logger.log_message("Peer passed their turn")
        self.advance_player_turn()

    def is_my_turn(self) -> bool:
        """Checks if it's the player's turn"""
        if not self.turn_order:
            return False
        current_player = self.turn_order[self.turn_index]
        return current_player == self.player_id

    def is_game_initiated(self) -> bool:
        """Checks if the game has been initiated."""
        return bool(self.turn_order)

    def advance_player_turn(self):
        """Advances the player's turn - should be called locally and remotely"""
        self.turn_index = (self.turn_index + 1) % len(self.turn_order)
        next_player = self.turn_order[self.turn_index]
        if next_player == self.player_id:
            self.logger.log_message("It's now your turn!")

    def send_deck(self) -> str:
        """Creates a CREATE_DECK! request, send deck data to the peers."""
        deck_message = "CREATE_DECK!" + "!".join(self.deck)
        self.logger.log_message(f"Created a deck importation request: {deck_message}", print_message=False)
        return deck_message

    def send_turn_order(self) -> str:
        """Creates a TURN_ORDER! message to send to peers."""
        turn_order_str = "!".join(f"{player[0]}:{player[1]}" for player in self.turn_order)
        turn_order_message = f"TURN_ORDER!{turn_order_str}"
        self.logger.log_message(f"Created TURN_ORDER message: {turn_order_message}", print_message=False)
        return turn_order_message

    def add_points(self, card: str):
        """Adds points to player's total point value based on the value of the drawn card."""
        card_value = int(card[1:])
        self.points += card_value
        self.logger.log_message(f"Added {card_value} points for card: {card}. Your point total: {self.points}")

    def update_addresses(self, addresses: List[Tuple[str, int]]):
        """Updates the list of player addresses."""
        self.addresses = addresses
