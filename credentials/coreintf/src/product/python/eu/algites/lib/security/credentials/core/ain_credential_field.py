from enum import Enum


class AInCredentialField(Enum):
    """Canonical fields supported by Algites credential types."""

    USERNAME = "username"
    PASSWORD = "password"
    TOKEN = "token"
    API_KEY = "apiKey"
    CERTIFICATE = "certificate"
    PRIVATE_KEY = "privateKey"
    PRIVATE_KEY_PASSWORD = "privateKeyPassword"

    @property
    def id(self) -> str:
        return self.value

    @classmethod
    def from_id(cls, value: str) -> "AInCredentialField":
        if value is None:
            raise ValueError("Credential field id must not be null.")
        normalized = value.strip()
        for field in cls:
            if field.value == normalized or field.name == normalized.upper():
                return field
        raise ValueError(f"Unsupported credential field: {value}")
