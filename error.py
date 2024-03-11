class CommandError(Exception):
    def __init__(self, message: str, ephemeral: bool = False) -> None:
        self.message = message
        self.ephemeral = ephemeral
