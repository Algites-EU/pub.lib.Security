import re
from collections.abc import Mapping

from eu.algites.lib.security.credentials.core.aic_credential_value_reference import AIcCredentialValueReference
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType


class AIcCredentialDocument:
    """Parsed universal Algites credential document containing named profiles."""

    _PROFILE_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

    def __init__(
        self,
        profiles: Mapping[str, Mapping[AInCredentialType, Mapping[AInCredentialField, AIcCredentialValueReference]]],
    ) -> None:
        copied: dict[str, dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]]] = {}
        for profile_id, typed_credentials in profiles.items():
            if not self._PROFILE_ID_PATTERN.fullmatch(profile_id):
                raise ValueError(
                    f"Credential profile id must use canonical lowercase dash-separated form: {profile_id}"
                )
            copied_types: dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]] = {}
            for credential_type, fields in typed_credentials.items():
                copied_fields = dict(fields)
                for field in copied_fields:
                    if field not in credential_type.supported_fields:
                        raise ValueError(
                            f"Credential field '{field.id}' is not supported by credential type '{credential_type.id}'."
                        )
                for required_field in credential_type.required_fields:
                    if required_field not in copied_fields:
                        raise ValueError(
                            f"Credential profile '{profile_id}' type '{credential_type.id}' is missing required field "
                            f"'{required_field.id}'."
                        )
                copied_types[credential_type] = copied_fields
            if not copied_types:
                raise ValueError(f"Credential profile '{profile_id}' must define at least one type.")
            copied[profile_id] = copied_types
        self._profiles = copied

    @property
    def profile_ids(self) -> tuple[str, ...]:
        return tuple(self._profiles.keys())

    def contains_profile(self, profile_id: str) -> bool:
        return profile_id in self._profiles

    def get_credential_values(
        self,
        profile_id: str,
        credential_type: AInCredentialType,
    ) -> dict[AInCredentialField, AIcCredentialValueReference] | None:
        profile = self._profiles.get(profile_id)
        if profile is None:
            return None
        values = profile.get(credential_type)
        return None if values is None else dict(values)
