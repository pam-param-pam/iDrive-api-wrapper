from .Webhook import Webhook
from ..models.Bot import Bot
from ..utils.networker import make_request


class DiscordSettings:
    def __init__(self, bots, webhooks, guild_id, channels, attachment_name, can_add_bots_or_webhooks, auto_setup_complete):
        self.bots = [Bot(**bot) for bot in bots]
        self.webhooks = [Webhook(**hook) for hook in webhooks]
        self.guild_id = guild_id
        self.channels = {channel['id']: channel['name'] for channel in channels}
        self.attachment_name = attachment_name
        self.can_add_bots_or_webhooks = can_add_bots_or_webhooks
        self.auto_setup_complete = auto_setup_complete

    @classmethod
    def fetch(cls) -> "DiscordSettings":
        data = make_request("GET", "user/discordSettings")
        return cls(**data)

    def reset(self) -> None:
        make_request("DELETE", "user/discordSettings")

    def auto_setup(self) -> None:
        make_request("POST", "user/discordSettings/autoSetup")

    def set_guild_id(self, guild_id: str) -> None:
        make_request("PATCH", "user/discordSettings", data={"guild_id": guild_id})

    def set_attachment_name(self, name: str) -> None:
        make_request("PATCH", "user/discordSettings", data={"attachment_name": name})

    def add_webhook(self, webhook_url: str) -> Webhook:
        data = make_request("POST", "user/discordSettings/webhooks", data={"webhook_url": webhook_url})
        return Webhook(**data)

    def add_bot(self, bot_token: str) -> Bot:
        data = make_request("POST", "user/discordSettings/bots", data={"token": bot_token})
        return Bot(**data)

    def __str__(self):
        return "DiscordSettings()"
