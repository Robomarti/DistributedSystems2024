class Logger():
    def __init__(self, own_address):
        self.own_address = own_address

    def log_message(self, message, print_message=True):
        if print_message:
            print(message)
        with open("logs.txt", "a", encoding="utf-8") as log_file:
            log_file.write(f"{self.own_address}: " + message + "\n")

    def clear_logs(self):
        open("logs.txt", "w", encoding="utf-8").close()
