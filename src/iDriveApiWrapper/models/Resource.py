from abc import ABC
from typing import Optional, Union

from overrides import EnforceOverrides

from ..utils.networker import make_request


class Resource(ABC, EnforceOverrides):
    def __init__(self, resource_id):
        self._id: str = resource_id
        self._password: Optional[str] = None

    def _get_password_header(self):
        return {"x-resource-password": self._password} if self._password else {}

    def set_password(self, password: Union[str, None]) -> None:
        self._password = password

    def get_password(self) -> str:
        return self._password

    def check_password(self, password: str):
        make_request("GET", f"resource/password/{self._id}", headers={"x-resource-password": password})

    def refresh(self):
        setattr(self, '__refresh', True)
