import re
from types import MappingProxyType
from typing import Mapping

from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType


class AIcCredentialProfile:
    """Stable, non-secret description of a named credential profile."""

    _ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def __init__(self, profile_id: str, credential_type: AInCredentialType, configuration: Mapping[str, str] | None = None):
        if profile_id is None:
            raise ValueError("Credential profile id must not be null.")
        if credential_type is None:
            raise ValueError("Credential profile type must not be null.")
        if not self._ID_PATTERN.fullmatch(profile_id):
            raise ValueError(f"Credential profile id must use canonical lowercase dash-separated form: {profile_id}")
        self._id = profile_id
        self._type = credential_type
        self._configuration = MappingProxyType(dict(configuration or {}))

    @property
    def id(self) -> str:
        return self._id

    @property
    def type(self) -> AInCredentialType:
        return self._type

    @property
    def configuration(self) -> Mapping[str, str]:
        return self._configuration

    @property
    def environment_prefix(self) -> str:
        return f"ALGITES_CREDENTIAL_{self._id.upper().replace('-', '_')}_{self._type.environment_segment}"

    def environment_variable(self, field: AInCredentialField) -> str:
        if field not in self._type.supported_fields:
            raise ValueError(f"Credential field {field} is not supported by credential type {self._type.id}.")
        return f"{self.environment_prefix}_{field.name}"

    @property
    def storage_key(self) -> str:
        return f"{self._id}/{self._type.id}"
