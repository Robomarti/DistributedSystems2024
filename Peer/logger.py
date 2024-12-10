class Logger():
    def __init__(self, own_address):
        self.own_address = own_address
        self.peer_number = -1

    def log_message(self, message, print_message=True):
        if print_message:
            print(message)

        peer_log_name = "logs.txt"

        if self.peer_number != -1:
            peer_log_name = str(self.peer_number) + peer_log_name
        
        with open(peer_log_name, "a", encoding="utf-8") as log_file:
            log_file.write(f"{self.own_address}: " + message + "\n")

    def clear_logs(self):
        peer_log_name = "logs.txt"

        if self.peer_number != -1:
            peer_log_name = str(self.peer_number) + peer_log_name

        open(peer_log_name, "w", encoding="utf-8").close()
