from enum import Enum


class AInCredentialValueSource(Enum):
    """Algorithms for resolving a credential field value."""

    DIRECT_VALUE = "direct_value"
    FILE_CONTENT = "file_content"
    SECRET_CONTENT = "secret_content"
    ENVIRONMENT_VARIABLE_CONTENT = "environment_variable_content"

    @property
    def id(self) -> str:
        return self.value

    @classmethod
    def from_id(cls, value: str) -> "AInCredentialValueSource":
        if value is None:
            raise ValueError("Credential value source must not be null.")
        normalized = value.strip()
        for source in cls:
            if source.value == normalized:
                return source
        raise ValueError(f"Unsupported credential value source: {value}")
