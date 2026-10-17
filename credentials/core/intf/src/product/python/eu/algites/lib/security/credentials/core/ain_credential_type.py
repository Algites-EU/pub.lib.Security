from enum import Enum

from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField


class AInCredentialType(Enum):
    """Authentication mechanisms supported by the Algites credential model."""

    BASIC = (
        "basic",
        "Basic",
        (AInCredentialField.USERNAME, AInCredentialField.PASSWORD),
        (),
    )
    BEARER = (
        "bearer",
        "Bearer",
        (AInCredentialField.TOKEN,),
        (),
    )
    API_KEY = (
        "api_key",
        "ApiKey",
        (AInCredentialField.API_KEY,),
        (),
    )
    CERTIFICATE = (
        "certificate",
        "Certificate",
        (AInCredentialField.CERTIFICATE,),
        (AInCredentialField.PRIVATE_KEY, AInCredentialField.PRIVATE_KEY_PASSWORD),
    )

    def __init__(self, type_id: str, property_name: str, required_fields: tuple[AInCredentialField, ...], optional_fields: tuple[AInCredentialField, ...]):
        self._type_id = type_id
        self._property_name = property_name
        self._required_fields = required_fields
        self._optional_fields = optional_fields

    @property
    def id(self) -> str:
        return self._type_id

    @property
    def property_name(self) -> str:
        return self._property_name

    @property
    def environment_segment(self) -> str:
        return self._type_id.upper()

    @property
    def required_fields(self) -> tuple[AInCredentialField, ...]:
        return self._required_fields

    @property
    def optional_fields(self) -> tuple[AInCredentialField, ...]:
        return self._optional_fields

    @property
    def supported_fields(self) -> tuple[AInCredentialField, ...]:
        return self._required_fields + self._optional_fields

    @classmethod
    def from_id(cls, value: str) -> "AInCredentialType":
        if value is None:
            raise ValueError("Credential type id must not be null.")
        normalized = value.strip().lower()
        for credential_type in cls:
            if credential_type.id == normalized:
                return credential_type
        raise ValueError(f"Unsupported credential type: {value}")
