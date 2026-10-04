from dataclasses import dataclass, field


@dataclass(frozen=True)
class ApiKeyAuth:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        # Visible ASCII only: reject whitespace/header injection without echoing a key.
        if not self.value or any(not 33 <= ord(char) <= 126 for char in self.value):
            raise ValueError("API key must contain nonempty visible ASCII without whitespace")

    def headers(self) -> dict[str, str]:
        return {"x-api-key": self.value}
