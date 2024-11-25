import random
from logger import Logger

class Gameplay():
    def __init__(self, logger: Logger):
        self.deck = []
        self.logger = logger
        self.supported_incoming_commands = ["CREATE_DECK","DRAW_CARD", "PASS_TURN", "START_GAME",
                                            "END_GAME", "INVALID_ACTION", "SYNC_ERROR"]
        self.cards = ["C02", "C03", "C04",
                      "D02", "D03", "D04",
                      "H02", "H03", "H04",
                      "S02", "S03", "S04"]
        self.points = 0

    def create_deck(self, deck_values=None):
        if deck_values is None:
            # create a deck
            self.logger.log_message("First connected player, creating a deck")
            self.deck = self.cards
            random.shuffle(self.deck)
        else:
            # import deck values
            self.logger.log_message("Importing deck data from a peer")
            for card in deck_values:
                self.deck.append(card)

    def handle_input(self, user_input: str):
        result = ""
        splitted_input = user_input.split("!")

        if splitted_input[0].upper() == "CHAT":
            result = splitted_input[1]
        elif splitted_input[0].upper() == "DRAW_CARD":
            # implement logic
            self.logger.log_message("Drew card: ")
            result = "card"
        elif splitted_input[0].upper() == "PASS_TURN":
            # implement logic
            self.logger.log_message("Passed")
            result = "Passed"
        elif splitted_input[0].upper() == "SEND_DECK":
            # implement logic
            self.logger.log_message("Sending deck creation request")
            result = "CREATE_DECK!" # + cards
        elif splitted_input[0].upper() == "CLEAR_LOGS":
            # developer command
            self.logger.clear_logs()
            result = "developer command"
        elif splitted_input[0].upper() == "PRINT_DECK":
            # developer command
            self.logger.log_message(str(self.deck))
            result = "developer command"
        else:
            self.logger.log_message("Unsupported user_input: " + user_input, False)

        return result

    def handle_incoming_commands(self, incoming_command: str):
        self.logger.log_message("Received command from peer: " + incoming_command, False)

        if incoming_command[0].upper() == "CREATE_DECK":
            for card in incoming_command[1::]:
                self.deck.append(card)
            self.logger.log_message("Deck created")
        elif incoming_command[0].upper() == "DRAW_CARD":
            self.logger.log_message("peer drew card")
        elif incoming_command[0].upper() == "PASS_TURN":
            self.logger.log_message("peer passed")
        elif incoming_command[0].upper() == "START_GAME":
            self.logger.log_message("game started")
        elif incoming_command[0].upper() == "END_GAME":
            self.logger.log_message("game ended")
        elif incoming_command[0].upper() == "INVALID_ACTION":
            self.logger.log_message("INVALID_ACTION")
        elif incoming_command[0].upper() == "SYNC_ERROR":
            self.logger.log_message("SYNC_ERROR")
