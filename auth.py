import requests

class AuthManager:
    def __init__(self, client_id: str, client_secret: str, auth_url: str = "https://example.com/oauth/token"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.auth_url = auth_url
        self.token = None

    def get_access_token(self):
        if not self.token or self.is_token_expired():
            self.token = self.fetch_token()
        return self.token["access_token"]

    def fetch_token(self):
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = requests.post(self.auth_url, data=payload)
            response.raise_for_status()
            token_data = response.json()
            return token_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching token: {e}")
            return None

    def is_token_expired(self):
        # Simplified logic for demo purposes.
        # You can expand this method to check token expiration time.
        return False
