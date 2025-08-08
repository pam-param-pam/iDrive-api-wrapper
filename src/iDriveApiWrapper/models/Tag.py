from typing import Optional

from ..models.Resource import Resource
from ..utils.networker import make_request


class Tag(Resource):
    def __init__(self, id: str, name: str):
        super().__init__(id)
        self.name: str = name
        self.file_id: Optional[str] = None

    def remove(self):
        if not self.file_id:
            raise KeyError("file_id is missing in tag.")

        make_request("DELETE", f"files/{self.file_id}/tags/{self._id}", headers=self._get_password_header())

    def __str__(self):
        return f"Tag({self.name})"

    def __repr__(self):
        return self.__str__()
