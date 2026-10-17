import os
from collections.abc import Mapping

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.aii_credential_provider import AIiCredentialProvider
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


class AIcEnvironmentCredentialProvider(AIiCredentialProvider):
    """Resolves credentials injected through process environment variables."""

    def __init__(self, environment: Mapping[str, str] | None = None):
        self._environment = dict(os.environ if environment is None else environment)

    def resolve(self, profile: AIcCredentialProfile) -> AIcCredential | None:
        values = {}
        missing_required: list[str] = []
        present_count = 0
        for field in profile.type.supported_fields:
            variable = profile.environment_variable(field)
            value = self._environment.get(variable)
            if value:
                values[field] = value
                present_count += 1
            elif field in profile.type.required_fields:
                missing_required.append(variable)
        if present_count == 0:
            return None
        if missing_required:
            raise AIxCredentialException(
                f"Credential profile '{profile.id}' is only partially defined in the environment. "
                f"Missing: {', '.join(missing_required)}."
            )
        return AIcCredential(values)

    @staticmethod
    def required_environment_variables(profile: AIcCredentialProfile) -> tuple[str, ...]:
        return tuple(profile.environment_variable(field) for field in profile.type.required_fields)

    @staticmethod
    def optional_environment_variables(profile: AIcCredentialProfile) -> tuple[str, ...]:
        return tuple(profile.environment_variable(field) for field in profile.type.optional_fields)
