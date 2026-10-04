"""Public request/response contracts; role/tenant cannot be assigned by signup."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, hide_input_in_errors=True)


class Registration(StrictInput):
    email: str = Field(pattern=r"^[a-z0-9][a-z0-9_.+-]{0,90}@example\.test$")
    password: SecretStr = Field(min_length=12, max_length=128)
    mfa_method: Literal["email", "totp", "sms"] = "email"


class Login(StrictInput):
    email: str = Field(min_length=1, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class Verification(StrictInput):
    challenge_id: str = Field(pattern=r"^[a-f0-9-]{36}$")
    code: SecretStr = Field(min_length=6, max_length=6)

    @field_validator("code")
    @classmethod
    def six_ascii_digits(cls, code: SecretStr) -> SecretStr:
        value = code.get_secret_value()
        if not value.isascii() or not value.isdigit():
            raise ValueError("OTP must contain six ASCII digits")
        return code


class Refresh(StrictInput):
    refresh_token: SecretStr = Field(min_length=20, max_length=256)


class UserView(BaseModel):
    id: str
    tenant_id: str
    role: Literal["member", "admin"]
    mfa_method: Literal["email", "totp", "sms"]


class Registered(UserView):
    totp_secret: str | None = None


class ChallengeView(BaseModel):
    challenge_id: str
    method: str
    expires_in: int


class Tokens(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int


class DocumentView(BaseModel):
    id: str
    owner_id: str
    tenant_id: str
    filename: str
    content_type: str
    sha256: str
    size: int


class ErrorView(BaseModel):
    error: str
    correlation_id: str
