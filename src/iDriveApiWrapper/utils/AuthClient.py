import os
import json

from ..utils.networker import make_request


class AuthClient:
    TOKEN_FILE = "auth_token.json"

    @staticmethod
    def _load_auth():
        if os.path.exists(AuthClient.TOKEN_FILE):
            try:
                with open(AuthClient.TOKEN_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("auth_token"), data.get("device_id")
            except Exception:
                return None, None
        return None, None

    @staticmethod
    def _save_auth(token: str, device_id: str):
        with open(AuthClient.TOKEN_FILE, "w") as f:
            json.dump({"auth_token": token, "device_id": device_id}, f)

    @staticmethod
    def login(username: str, password: str, force_login: bool = False) -> tuple[str, str]:
        if not force_login:
            token, device_id = AuthClient._load_auth()
            if token and device_id:
                return token, device_id

        data = make_request("POST", "auth/token/login", data={'username': username, 'password': password})
        token = data['auth_token']
        device_id = data['device_id']
        AuthClient._save_auth(token, device_id)
        return token, device_id
