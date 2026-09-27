from dataclasses import dataclass

from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource


@dataclass(frozen=True)
class AIcCredentialValueReference:
    """Immutable credential-document value reference."""

    source: AInCredentialValueSource
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.source, AInCredentialValueSource):
            raise TypeError("Credential value source must be an AInCredentialValueSource.")
        if not isinstance(self.value, str) or not self.value:
            raise ValueError("Credential value reference must not be empty.")
