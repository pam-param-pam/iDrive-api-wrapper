from typing import Optional

from utils.networker import make_request


class Resource:
    def __init__(self, resource_id):
        self._id: str = resource_id
        self._fetched = False
        self._password: Optional[str] = None

    def _get_password_header(self):
        return {"x-resource-password": self._password} if self._password else {}

    def set_password(self, password: str) -> None:
        self._password = password

    async def check_password(self, password: str):
        await make_request("GET", f"resource/password/{self._id}", headers={"x-resource-password": password})
