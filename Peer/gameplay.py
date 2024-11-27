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

        USER_INPUT = splitted_input[0].upper()

        if USER_INPUT == "CHAT":
            result = splitted_input[1]
        elif USER_INPUT == "DRAW_CARD":
            drawn_card = self.deck.pop(0)
            deck_size = len(self.deck)
            self.logger.log_message(f"Drew card: {drawn_card}")
            result = f"DRAW_CARD![{drawn_card}, {deck_size}]"
        elif USER_INPUT == "PASS_TURN":
            # implement logic
            self.logger.log_message("Passed")
            result = "Passed"
        elif USER_INPUT == "SEND_DECK":
            # implement logic
            self.logger.log_message("Sending deck creation request")
            result = "CREATE_DECK!" # + cards
        elif USER_INPUT == "CLEAR_LOGS":
            # developer command
            self.logger.clear_logs()
            result = "developer command"
        elif USER_INPUT == "PRINT_DECK":
            # developer command
            self.logger.log_message(str(self.deck))
            result = "developer command"
        else:
            self.logger.log_message("Unsupported user_input: " + user_input, False)

        return result

    def handle_incoming_commands(self, incoming_command: str, addr: str):
        self.logger.log_message("Received command from peer: " + incoming_command, False)

        split_incoming_message = incoming_command.split("!")

        COMMAND = split_incoming_message[0].upper()
        PAYLOAD = split_incoming_message[1].upper()

        if COMMAND == "CREATE_DECK":
            for card in PAYLOAD[1::]:
                self.deck.append(card)
            self.logger.log_message("Deck created")
        elif COMMAND == "DRAW_CARD":
            self.logger.log_message(f"Message from: " + str(addr) + ": " + "Player drew a card: " + PAYLOAD)
        elif COMMAND == "PASS_TURN":
            self.logger.log_message("peer passed")
        elif COMMAND == "START_GAME":
            self.logger.log_message("game started")
        elif COMMAND == "END_GAME":
            self.logger.log_message("game ended")
        elif COMMAND== "INVALID_ACTION":
            self.logger.log_message("INVALID_ACTION")
        elif COMMAND == "SYNC_ERROR":
            self.logger.log_message("SYNC_ERROR")
