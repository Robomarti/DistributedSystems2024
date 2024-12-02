import random
from typing import List, Tuple, Optional
from logger import Logger

class Gameplay:
    """Handles all gameplay-related tasks."""

    def __init__(self, logger: Logger, player_id: Tuple[str, int]):
        self.logger = logger
        self.player_id = player_id
        self.connected_peers = 0
        self.deck: List[str] = []
        self.current_turn = -1 # current_turn is -1 to mark that the game is not active yet
        self.own_turn_identifier = -1
        self.points = 0
        self.passed = False

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

    def reset_gameplay_variables(self):
        """Reset variables for next game"""
        self.deck: List[str] = []
        self.current_turn = -1
        self.points = 0
        self.passed = False

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
        upper_input = splitted_input[0].upper()

        if upper_input == "CHAT":
            return self.chat_input(splitted_input)
        elif upper_input == "DRAW_CARD":
            return self.draw_card_input()
        elif upper_input == "PASS_TURN":
            return self.pass_turn_input()
        elif upper_input == "INITIATE_GAME":
            return self.initiate_game_input()
        elif upper_input == "SEND_DECK":
            # This is a developer command as well, players should not
            # need this and thus should not have access this in the final build
            return self.send_deck()
        elif upper_input == "CLEAR_LOGS":
            self.logger.clear_logs()
            return "developer command"
        elif upper_input == "PRINT_DECK":
            self.logger.log_message(str(self.deck))
            return "developer command"
        else:
            self.logger.log_message("Unsupported user input: " + user_input, print_message=False)
            return ""

    def chat_input(self, splitted_input: List[str]) -> str:
        """Processes CHAT! input."""
        return "!".join(splitted_input[1:])

    def draw_card_input(self) -> str:
        """Processes DRAW_CARD! input."""
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
        self.passed = True
        self.advance_player_turn()
        return "PASS_TURN!"

    def initiate_game_input(self) -> List[str]:
        """Processes INITIATE_GAME! input - this can only be done by the leading player."""
        if self.own_turn_identifier != 0:
            self.logger.log_message("You are not the first player; you cannot initiate the game")
            return []

        self.current_turn = 0
        self.create_deck()
        self.logger.log_message(f"Deck host created deck: {self.deck}", print_message=False)
        deck_message = self.send_deck()
        return [deck_message]

    def handle_incoming_commands(self, datagram: str) -> List[str]:
        """Handles the commands sent to connected peers (players)."""
        resulting_commands = []
        splitted_command = datagram.split("!")
        command = splitted_command[0].upper()

        self.logger.log_message(f"Handling command from peer: {datagram}", print_message=False)

        if command == "CREATE_DECK":
            self.create_deck_command(splitted_command)
        elif command == "DRAW_CARD":
            resulting_commands.extend(self.draw_card_command(splitted_command))
        elif command == "PASS_TURN":
            self.pass_turn_command()
        elif command == "START_GAME":
            self.logger.log_message("Game started")
        elif command == "END_GAME":
            self.end_game()
        elif command == "INVALID_ACTION":
            self.logger.log_message("Invalid action")
        elif command == "SYNC_ERROR":
            self.logger.log_message("Sync error detected")
            resulting_commands.append("REQUEST_DECK")
        elif command == "REQUEST_DECK":
            self.logger.log_message("Peer requests deck values", print_message=False)
            resulting_commands.append(self.send_deck())

        if self.is_my_turn() and self.passed:
            self.logger.log_message("Automatically passed.")
            resulting_commands.append("PASS_TURN!")

        return resulting_commands

    def create_deck_command(self, splitted_command: List[str]):
        """Processes CREATE_DECK! command. \n
        Also initializes the game if game has not been started yet"""
        deck_values = splitted_command[1:]
        self.create_deck(deck_values)
        self.logger.log_message(f"Deck created: {self.deck}", print_message=False)
        if self.current_turn == -1:
            self.current_turn = 0

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
        return self.current_turn == self.own_turn_identifier

    def is_game_initiated(self) -> bool:
        """Checks if the game has been initiated."""
        return bool(self.current_turn > -1)

    def advance_player_turn(self):
        """Advances the player's turn - should be called locally and remotely"""
        self.current_turn += 1
        if self.current_turn > self.connected_peers:
            self.current_turn = 0
        if self.is_my_turn():
            self.logger.log_message("It's now your turn!")

    def send_deck(self) -> str:
        """Creates a CREATE_DECK! request, send deck data to the peers."""
        deck_message = "CREATE_DECK!" + "!".join(self.deck)
        self.logger.log_message(f"Created a deck importation request: {deck_message}", print_message=False)
        return deck_message

    def add_points(self, card: str):
        """Adds points to player's total point value based on the value of the drawn card."""
        card_value = int(card[1:])
        self.points += card_value
        self.logger.log_message(f"Added {card_value} points for card: {card}. Your point total: {self.points}")
        if self.points > 21:
            self.passed = True
            self.logger.log_message("Points went over 21, you lost this game and automatically passed for the rest of the game.")

    def update_order_number(self, order_number: str):
        """Update own turn identifier"""
        self.own_turn_identifier = int(order_number)
        self.logger.log_message("own_turn_identifier: " + order_number, False)

    def increment_connected_peers_count(self):
        """Increment value to know which player is the last"""
        self.connected_peers += 1
        self.logger.log_message("connected_peers: " + str(self.connected_peers), False)

    def end_game(self):
        """Ends the game"""
        self.logger.log_message("Ending the game, calculating winner...")
        # todo: add functionality
        self.logger.log_message("Game ended, ready for a new game.")
        self.reset_gameplay_variables()
