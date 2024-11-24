from logger import Logger

class Gameplay():
    def __init__(self, logger: Logger):
        self.deck = None
        self.logger = logger

    def create_deck(self, deck=None):
        if deck is None:
            # create a deck
            self.logger.log_message("First connected player, creating a deck")
        else:
            self.logger.log_message("Importing deck data from a peer")
            self.deck = deck

    def handle_input(self, user_input: str):
        result = ""
        splitted_input = user_input.split("!")

        if splitted_input[0].lower() == "chat":
            result = splitted_input[1]
        elif splitted_input[0].lower() == "draw":
            # implement logic
            self.logger.log_message("Drew card: ")
        else:
            self.logger.log_message("Unsupported user_input: " + user_input, False)
            result = ""

        return result
