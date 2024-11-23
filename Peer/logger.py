class Logger():
    def __init__(self, own_address):
        self.own_address = own_address

    def log_message(self, message, print_message=True):
        if print_message:
            print(message)
        f = open("logs.txt", "a")
        f.write(f"{self.own_address}: " + message + "\n")
        f.close()
