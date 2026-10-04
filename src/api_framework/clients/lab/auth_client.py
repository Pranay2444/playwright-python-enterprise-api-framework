from api_framework.core.api_client import ApiClient


class LabAuthClient:
    def __init__(self, api: ApiClient):
        self.api = api

    def register(self, email: str, password: str, mfa_method: str = "email"):
        return self.api.post(
            "/auth/register", data={"email": email, "password": password, "mfa_method": mfa_method}
        )

    def login(self, email: str, password: str):
        return self.api.post("/auth/login", data={"email": email, "password": password})

    def verify(self, challenge_id: str, code: str):
        return self.api.post("/auth/verify", data={"challenge_id": challenge_id, "code": code})

    def refresh(self, refresh_token: str):
        return self.api.post("/auth/refresh", data={"refresh_token": refresh_token})

    def me(self, headers=None):
        return self.api.request("GET", "/auth/me", headers=headers)

    def logout(self, headers):
        return self.api.request("POST", "/auth/logout", headers=headers)
