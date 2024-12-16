class Logger():
    """Handles logging of the messages. Includes an optional to print the message to the console.

    Args:
        own_address: The address of the peer
        peer_number: An identifier of the peer
    """
    def __init__(self, own_address):
        self.own_address = own_address
        self.peer_number = -1

    def log_message(self, message, print_message=True):
        """Log a message to the log file and optionally print it to the console.

        Args:
            message: The message to be logged.
            print_message: Whether to print the message to the console. Default: True.
        """
        if print_message:
            print(message)

        peer_log_name = "logs.txt"

        if self.peer_number != -1:
            peer_log_name = str(self.peer_number) + peer_log_name
        
        with open(peer_log_name, "a", encoding="utf-8") as log_file:
            log_file.write(f"{self.own_address}: " + message + "\n")

    def clear_logs(self):
        """Clears the contents of the log file(s)."""
        peer_log_name = "logs.txt"

        if self.peer_number != -1:
            peer_log_name = str(self.peer_number) + peer_log_name

        open(peer_log_name, "w", encoding="utf-8").close()
