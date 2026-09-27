import json
import os
from collections.abc import Mapping
from pathlib import Path

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_document_reader import AIcCredentialDocumentReader
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.aii_credential_provider import AIiCredentialProvider
from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException
from eu.algites.lib.security.credentials.core.aic_credential_store_provider import AIcCredentialStoreProvider


class AIcCredentialDocumentProvider(AIiCredentialProvider):
    """Resolves the universal Algites credential document."""

    CREDENTIALS_VARIABLE = "ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS"
    SECRET_CONTEXT_VARIABLE = "_TMP_ALGITES_CREDENTIAL_SECRETS_JSON"

    def __init__(
        self,
        environment: Mapping[str, str] | None = None,
        base_directory: Path | str | None = None,
        store_provider: AIcCredentialStoreProvider | None = None,
    ):
        self._environment = dict(os.environ if environment is None else environment)
        self._base_directory = Path.cwd() if base_directory is None else Path(base_directory).resolve()
        self._store_provider = store_provider or AIcCredentialStoreProvider()

    @staticmethod
    def _parse_object(raw: str, label: str) -> dict:
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exception:
            raise AIxCredentialException(f"{label} does not contain valid JSON.") from exception
        if not isinstance(value, dict):
            raise AIxCredentialException(f"{label} must contain a JSON object.")
        return value

    def _load_document(self) -> str | None:
        raw = self._environment.get(self.CREDENTIALS_VARIABLE)
        if raw and raw.strip():
            return raw
        stored = self._store_provider.read_credential_document()
        return None if stored is None else stored.decode("utf-8")

    def _secret_context(self) -> dict:
        raw = self._environment.get(self.SECRET_CONTEXT_VARIABLE)
        return {} if not raw or not raw.strip() else self._parse_object(raw, self.SECRET_CONTEXT_VARIABLE)

    def _field_error(self, profile: AIcCredentialProfile, field, message: str) -> AIxCredentialException:
        return AIxCredentialException(f"Credential '{profile.id}/{profile.type.id}/{field.id}' {message}")

    def _resolve_reference(self, profile: AIcCredentialProfile, field, reference, secrets: dict) -> str:
        source = reference.source
        value = reference.value
        if source is AInCredentialValueSource.DIRECT_VALUE:
            return value
        if source is AInCredentialValueSource.FILE_CONTENT:
            path = Path(value)
            if not path.is_absolute():
                path = self._base_directory / path
            path = path.resolve()
            if not path.is_file():
                raise self._field_error(profile, field, f"references missing file '{path}'.")
            return path.read_text(encoding="utf-8")
        if source is AInCredentialValueSource.SECRET_CONTENT:
            if value in secrets:
                return str(secrets[value])
            stored = self._store_provider.read_named_secret(value)
            if stored is None:
                raise self._field_error(profile, field, f"references unavailable secret '{value}'.")
            return stored.decode("utf-8")
        if source is AInCredentialValueSource.ENVIRONMENT_VARIABLE_CONTENT:
            if value not in self._environment:
                raise self._field_error(profile, field, f"references unavailable environment variable '{value}'.")
            return self._environment[value]
        raise self._field_error(profile, field, f"uses unsupported source '{source.id}'.")

    def resolve_field(self, document, profile: AIcCredentialProfile, field):
        typed = document.get_credential_values(profile.id, profile.type)
        if typed is None or field not in typed:
            return None
        if field not in profile.type.supported_fields:
            raise AIxCredentialException(
                f"Credential field '{field.id}' is not supported by credential type '{profile.type.id}'."
            )
        return self._resolve_reference(profile, field, typed[field], self._secret_context())

    def resolve(self, profile: AIcCredentialProfile) -> AIcCredential | None:
        raw = self._load_document()
        if not raw or not raw.strip():
            return None
        document = AIcCredentialDocumentReader().read(raw)
        typed = document.get_credential_values(profile.id, profile.type)
        if typed is None:
            return None
        secrets = self._secret_context()
        values = {}
        for field, reference in typed.items():
            values[field] = self._resolve_reference(profile, field, reference, secrets)
        credential = AIcCredential(values)
        if not credential.satisfies(profile):
            credential.close()
            raise AIxCredentialException(
                f"Credential profile '{profile.id}' type '{profile.type.id}' is incomplete."
            )
        return credential
