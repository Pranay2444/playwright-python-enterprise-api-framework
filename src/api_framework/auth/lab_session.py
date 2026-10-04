"""Per-test MFA session, explicit refresh, fail-closed state, no business-request replay."""

from collections.abc import Callable
from dataclasses import dataclass, field
from time import monotonic

from api_framework.core.responses import json_object


class AuthFlowError(RuntimeError):
    pass


@dataclass(repr=False)
class LabSession:
    client: object
    clock: Callable[[], float] = monotonic
    state: str = field(default="anonymous", init=False)
    _access: str | None = field(default=None, init=False, repr=False)
    _refresh: str | None = field(default=None, init=False, repr=False)
    _expires_at: float = field(default=0, init=False)

    def __repr__(self):
        return f"LabSession(state={self.state!r})"

    def clear(self):
        self.state = "anonymous"
        self._access = self._refresh = None
        self._expires_at = 0

    def authenticate(self, email: str, password: str, code_provider: Callable[[str], str]):
        self.clear()
        try:
            challenge = json_object(self.client.login(email, password), 202)
            self.state = "challenge"
            code = code_provider(challenge["challenge_id"])
            self._accept(json_object(self.client.verify(challenge["challenge_id"], code)))
        except Exception:
            self.clear()
            raise AuthFlowError("MFA sign-in failed; session cleared") from None

    def _accept(self, body):
        access, refresh, lifetime = body["access_token"], body["refresh_token"], body["expires_in"]
        if (
            not isinstance(access, str)
            or not access
            or not isinstance(refresh, str)
            or not refresh
            or type(lifetime) is not int
            or lifetime <= 0
            or body["token_type"] != "bearer"
            or any(not 33 <= ord(char) <= 126 for char in access + refresh)
        ):
            raise ValueError("Invalid token response")
        self._access, self._refresh = access, refresh
        self._expires_at = self.clock() + lifetime
        self.state = "authenticated"

    def headers(self) -> dict[str, str]:
        if self._access is None:
            raise AuthFlowError("Authenticate before requesting a protected resource")
        if self.clock() >= self._expires_at:
            self.state = "expired"
            raise AuthFlowError(
                "Access lifetime elapsed; refresh explicitly before the next request"
            )
        return {"Authorization": f"Bearer {self._access}"}

    def refresh(self):
        if self._refresh is None:
            raise AuthFlowError("Authenticate before refreshing")
        try:
            self._accept(json_object(self.client.refresh(self._refresh)))
        except Exception:
            self.clear()
            raise AuthFlowError("Refresh failed; session cleared") from None

    def logout(self):
        try:
            response = self.client.logout(self.headers())
            if response.status != 204:
                raise AuthFlowError("Server logout failed")
        finally:
            self.clear()
