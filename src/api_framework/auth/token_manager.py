"""Cache tokens for one test. Refresh proactively; never replay a failed business request."""

from collections.abc import Callable
from dataclasses import dataclass
from time import monotonic
from typing import Protocol


@dataclass(frozen=True, repr=False)
class TokenPair:
    access_token: str
    refresh_token: str
    expires_in_seconds: int


class TokenSource(Protocol):
    """A future service adapter can implement these same two methods."""

    def obtain_tokens(self) -> TokenPair: ...

    def renew_tokens(self, refresh_token: str) -> TokenPair: ...


class TokenManager:
    def __init__(
        self,
        source: TokenSource,
        *,
        refresh_margin_seconds: int = 30,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if refresh_margin_seconds < 0:
            raise ValueError("refresh_margin_seconds must not be negative")
        self._source = source
        self._clock = clock
        self._refresh_margin = refresh_margin_seconds
        self._tokens: TokenPair | None = None
        self._expires_at = 0.0

    def access_token(self) -> str:
        if self._tokens is None:
            self._store(self._source.obtain_tokens())
        elif self._clock() >= self._expires_at - self._refresh_margin:
            self.refresh()
        assert self._tokens is not None
        return self._tokens.access_token

    def authorization_header(self) -> str:
        return f"Bearer {self.access_token()}"

    def refresh(self) -> None:
        if self._tokens is None:
            self._store(self._source.obtain_tokens())
            return
        refresh_token = self._tokens.refresh_token
        # A failed refresh must not leave stale credentials cached.
        self.invalidate()
        self._store(self._source.renew_tokens(refresh_token))

    def invalidate(self) -> None:
        self._tokens = None
        self._expires_at = 0.0

    def _store(self, tokens: TokenPair) -> None:
        if not tokens.access_token or not tokens.refresh_token:
            raise ValueError("Auth response must include non-empty access and refresh tokens")
        if tokens.expires_in_seconds <= self._refresh_margin:
            raise ValueError("Token lifetime must exceed the refresh margin")
        self._tokens = tokens
        self._expires_at = self._clock() + tokens.expires_in_seconds
