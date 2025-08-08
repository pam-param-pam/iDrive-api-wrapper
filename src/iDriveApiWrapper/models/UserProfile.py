from .namedTuples import User, Perms
from ..models.UserSettings import Settings
from ..utils.networker import make_request


class UserProfile:
    def __init__(self, user: dict, perms: dict, settings: dict):
        self.user = User(**user)
        self.perms = Perms(**perms)
        self.settings = Settings(**settings)

    @classmethod
    def fetch(cls):
        data = make_request("GET", "user/me")

        return cls(
            user=data["user"],
            perms=data["perms"],
            settings=data["settings"]
        )

    def __str__(self):
        return f"UserProfile({self.user.name})"
