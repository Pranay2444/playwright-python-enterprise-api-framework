"""Read environment variables once, when pytest creates its settings fixture."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


def validate_origin(base_url: str) -> None:
    url = urlsplit(base_url)
    if (
        url.scheme not in {"http", "https"}
        or not url.hostname
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
        or url.path not in {"", "/"}
    ):
        raise ValueError("base_url must be an HTTP(S) origin without credentials or a path")


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://dummyjson.com"
    username: str = field(default="emilys", repr=False)
    password: str = field(default="emilyspass", repr=False)
    timeout_ms: int = 15_000
    token_expires_in_mins: int = 5

    def __post_init__(self) -> None:
        validate_origin(self.base_url)
        if self.timeout_ms <= 0 or self.token_expires_in_mins <= 0:
            raise ValueError("timeout_ms and token_expires_in_mins must be positive")
        if not self.username.strip() or not self.password:
            raise ValueError("DummyJSON username and password must not be empty")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "Settings":
        # Explicit path: do not accidentally load a .env from another project.
        if env_file is not None:
            load_dotenv(env_file, override=False)
        return cls(
            base_url=os.getenv("DUMMYJSON_BASE_URL", "https://dummyjson.com").rstrip("/"),
            username=os.getenv("DUMMYJSON_USERNAME", "emilys"),
            password=os.getenv("DUMMYJSON_PASSWORD", "emilyspass"),
            timeout_ms=int(os.getenv("API_TIMEOUT_MS", "15000")),
            token_expires_in_mins=int(os.getenv("TOKEN_EXPIRES_IN_MINS", "5")),
        )


@dataclass(frozen=True)
class BookerSettings:
    base_url: str = "https://restful-booker.herokuapp.com"
    username: str = field(default="admin", repr=False)
    password: str = field(default="password123", repr=False)
    timeout_ms: int = 15_000

    def __post_init__(self) -> None:
        validate_origin(self.base_url)
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        if not self.username.strip() or not self.password:
            raise ValueError("Booker username and password must not be empty")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "BookerSettings":
        if env_file is not None:
            load_dotenv(env_file, override=False)
        return cls(
            base_url=os.getenv("BOOKER_BASE_URL", "https://restful-booker.herokuapp.com").rstrip(
                "/"
            ),
            username=os.getenv("BOOKER_USERNAME", "admin"),
            password=os.getenv("BOOKER_PASSWORD", "password123"),
            timeout_ms=int(os.getenv("API_TIMEOUT_MS", "15000")),
        )


@dataclass(frozen=True)
class ReqResSettings:
    base_url: str = "https://reqres.in"
    api_key: str = field(default="", repr=False)
    project_id: str = ""
    collection: str = "products"
    environment: str = "prod"
    timeout_ms: int = 15_000

    def __post_init__(self) -> None:
        validate_origin(self.base_url)
        if self.timeout_ms <= 0:
            raise ValueError("timeout_ms must be positive")
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.collection):
            raise ValueError("ReqRes collection must be a safe slug")
        if self.environment not in {"prod", "dev"}:
            raise ValueError("ReqRes environment must be prod or dev")

    def require_project(self) -> None:
        if not self.api_key or not self.project_id.strip():
            raise ValueError("Set REQRES_API_KEY and REQRES_PROJECT_ID for project tests")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> "ReqResSettings":
        if env_file is not None:
            load_dotenv(env_file, override=False)
        return cls(
            base_url=os.getenv("REQRES_BASE_URL", "https://reqres.in").rstrip("/"),
            api_key=os.getenv("REQRES_API_KEY", ""),
            project_id=os.getenv("REQRES_PROJECT_ID", ""),
            collection=os.getenv("REQRES_COLLECTION", "products"),
            environment=os.getenv("REQRES_ENV", "prod"),
            timeout_ms=int(os.getenv("API_TIMEOUT_MS", "15000")),
        )
