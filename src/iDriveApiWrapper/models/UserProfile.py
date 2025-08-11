from .namedTuples import User, Perms, Device
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

    def get_active_devices(self) -> list[Device]:
        data = make_request("GET", "user/devices")
        devices = []
        for element in data:
            devices.append(Device(**element))
        return devices

    def __str__(self):
        return f"UserProfile({self.user.name})"
