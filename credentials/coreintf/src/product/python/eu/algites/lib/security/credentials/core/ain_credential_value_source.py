from enum import Enum


class AInCredentialValueSource(Enum):
    """Algorithms for resolving a credential field value."""

    DIRECT_VALUE = "DIRECT_VALUE"
    FILE_CONTENT = "FILE_CONTENT"
    SECRET_CONTENT = "SECRET_CONTENT"
    ENVIRONMENT_VARIABLE_CONTENT = "ENVIRONMENT_VARIABLE_CONTENT"

    @classmethod
    def from_id(cls, value: str) -> "AInCredentialValueSource":
        if value is None:
            raise ValueError("Credential value source must not be null.")
        try:
            return cls[value.strip()]
        except KeyError as exception:
            raise ValueError(f"Unsupported credential value source: {value}") from exception
