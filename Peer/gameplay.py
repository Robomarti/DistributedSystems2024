import random
from logger import Logger

class Gameplay():
    """Handles all gameplay related task"""
    def __init__(self, logger: Logger):
        self.deck = []
        self.logger = logger
        self.supported_incoming_commands = ["CREATE_DECK","DRAW_CARD", "PASS_TURN", "START_GAME",
                                            "END_GAME", "INVALID_ACTION", "SYNC_ERROR", "REQUEST_DECK"]
        self.cards = ["C02", "C03", "C04",
                      "D02", "D03", "D04",
                      "H02", "H03", "H04",
                      "S02", "S03", "S04"]
        self.points = 0
        self.deck_host_and_first_player = False

    def create_deck(self, deck_values=None):
        """Handles creating or importing the deck"""
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
        """Handles input from the user"""
        splitted_input = user_input.split("!")

        if splitted_input[0].upper() == "CHAT":
            # send everything as a chat message, except for the CHAT! command,
            # and replace original !-marks that were not used as a command marker
            result = "!".join(splitted_input[1::])
            return result

        if splitted_input[0].upper() == "DRAW_CARD":
            # todo: check if it's this player's turn
            result = self.deck.pop(0)
            self.add_points(result)
            self.logger.log_message("Drew card: " + result)
            result = "DRAW_CARD!"+result+"!"+str(len(self.deck))

            return result

        if splitted_input[0].upper() == "PASS_TURN":
            # implement logic
            self.logger.log_message("Passed")
            result = "Passed"
            return result

        if splitted_input[0].upper() == "INIATE_GAME":
            if self.deck_host_and_first_player:
                self.create_deck()
                self.logger.log_message("Deck host created deck: " + str(self.deck))
                result = self.send_deck()
                return result

            self.logger.log_message("You are not the first player, you cannot iniate the game")
            return ""

        if splitted_input[0].upper() == "SEND_DECK":
            # developer command
            return self.send_deck()

        if splitted_input[0].upper() == "CLEAR_LOGS":
            # developer command
            self.logger.clear_logs()
            result = "developer command"
            return result

        if splitted_input[0].upper() == "PRINT_DECK":
            # developer command
            self.logger.log_message(str(self.deck))
            result = "developer command"
            return result

        self.logger.log_message("Unsupported user_input: " + user_input, False)
        result = ""
        return result

    def handle_incoming_commands(self, datagram: str):
        """Handles input from the connected peers"""

        resulting_commands = []

        splitted_command = datagram.split("!")
        self.logger.log_message("Handling command from peer: " + datagram, False)

        if splitted_command[0].upper() == "CREATE_DECK":
            self.create_deck(splitted_command[1::])
            # todo in the final version: don't print the deck to the player
            self.logger.log_message("Deck created: " + str(self.deck))

        elif splitted_command[0].upper() == "DRAW_CARD":
            # todo: check if peer can draw a card
            self.logger.log_message("peer drew card: " + splitted_command[1])
            self.logger.log_message("current length of peer's deck: " + splitted_command[2], False)

            if int(splitted_command[2]) > len(self.deck):
                resulting_commands.append("SYNC_ERROR!")

            # finding the card that the peer drew and remove it and cards before it from the deck
            # this requires every card to be unique
            drawn_card_index = self.deck.index(splitted_command[1])
            self.deck = self.deck[drawn_card_index+1:]

            # if lengths of decks of peers are not the same size, something has gone wrong
            if not splitted_command[2] == len(self.deck):
                resulting_commands.append("SYNC_ERROR!")
                resulting_commands.append("REQUEST_DECK")

        elif splitted_command[0].upper() == "PASS_TURN":
            self.logger.log_message("peer passed")

        elif splitted_command[0].upper() == "START_GAME":
            self.logger.log_message("game started")

        elif splitted_command[0].upper() == "END_GAME":
            self.logger.log_message("game ended")

        elif splitted_command[0].upper() == "INVALID_ACTION":
            self.logger.log_message("INVALID_ACTION")

        elif splitted_command[0].upper() == "SYNC_ERROR":
            # todo, implement error messages
            self.logger.log_message("SYNC_ERROR")

        elif splitted_command[0].upper() == "REQUEST_DECK":
            self.logger.log_message("Peer requests deck values", False)
            resulting_commands.append(self.send_deck())

        return resulting_commands

    def send_deck(self):
        """Creates a deck-sending request"""
        result = "CREATE_DECK!"
        for card in self.deck:
            result += card + "!"

        # remove last ! -mark
        result = result[:-1]
        self.logger.log_message("Created a deck importation request: " + result, False)
        return result

    def add_points(self, card):
        self.logger.log_message("Adding points worth of card: " + card)
