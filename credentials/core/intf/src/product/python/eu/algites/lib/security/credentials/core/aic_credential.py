from collections.abc import Mapping

from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField


class AIcCredential:
    """In-memory credential values with best-effort explicit wiping support."""

    def __init__(self, values: Mapping[AInCredentialField, str | bytes | bytearray]):
        if values is None:
            raise ValueError("Credential values must not be null.")
        self._values: dict[AInCredentialField, bytearray] = {}
        for field, value in values.items():
            if field is None or value is None:
                raise ValueError("Credential fields and values must not be null.")
            if isinstance(value, str):
                encoded = value.encode("utf-8")
            else:
                encoded = bytes(value)
            self._values[field] = bytearray(encoded)

    def contains(self, field: AInCredentialField) -> bool:
        return field in self._values

    def get_value(self, field: AInCredentialField) -> bytearray | None:
        value = self._values.get(field)
        return None if value is None else bytearray(value)

    def get_text(self, field: AInCredentialField) -> str | None:
        value = self._values.get(field)
        return None if value is None else bytes(value).decode("utf-8")

    def satisfies(self, profile: AIcCredentialProfile) -> bool:
        return all(field in self._values for field in profile.type.required_fields)

    def close(self) -> None:
        for value in self._values.values():
            value[:] = b"\x00" * len(value)
        self._values.clear()

    def __enter__(self) -> "AIcCredential":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
