class Gameplay():
    def __init__(self):
        self.deck = []
 
    def create_deck(self, deck=None):
        if deck is None:
            print("first connected player, creating a deck")
            # create a deck
        else:
            print("importing deck data from a peer")
            self.deck = deck
