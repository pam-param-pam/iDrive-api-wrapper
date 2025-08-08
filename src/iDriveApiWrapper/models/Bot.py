from ..utils.networker import make_request


class Bot:
    def __init__(self, name, created_at, discord_id, disabled, primary):
        self.name = name
        self.created_at = created_at
        self.discord_id = discord_id
        self.disabled = disabled
        self.primary = primary

    def __str__(self):
        return f"Bot({self.name})"

    def __repr__(self):
        return self.__str__()

    def delete(self) -> None:
        make_request("DELETE", f"user/discordSettings/bots/{self.discord_id}")
