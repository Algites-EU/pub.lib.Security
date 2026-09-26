import json
import os
from collections.abc import Mapping
from pathlib import Path

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
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

    def _resolve_value(self, profile: AIcCredentialProfile, field, node: object, secrets: dict) -> str:
        if not isinstance(node, dict):
            raise self._field_error(profile, field, "must be an object containing source and value.")
        source_value = node.get("source")
        reference = node.get("value")
        if not isinstance(source_value, str):
            raise self._field_error(profile, field, "is missing string property 'source'.")
        if not isinstance(reference, str):
            raise self._field_error(profile, field, "is missing string property 'value'.")
        try:
            source = AInCredentialValueSource.from_id(source_value)
        except ValueError as exception:
            raise self._field_error(profile, field, str(exception)) from exception
        if source is AInCredentialValueSource.DIRECT_VALUE:
            return reference
        if source is AInCredentialValueSource.FILE_CONTENT:
            path = Path(reference)
            if not path.is_absolute():
                path = self._base_directory / path
            path = path.resolve()
            if not path.is_file():
                raise self._field_error(profile, field, f"references missing file '{path}'.")
            return path.read_text(encoding="utf-8")
        if source is AInCredentialValueSource.SECRET_CONTENT:
            if reference in secrets:
                return str(secrets[reference])
            stored = self._store_provider.read_named_secret(reference)
            if stored is None:
                raise self._field_error(profile, field, f"references unavailable secret '{reference}'.")
            return stored.decode("utf-8")
        if source is AInCredentialValueSource.ENVIRONMENT_VARIABLE_CONTENT:
            if reference not in self._environment:
                raise self._field_error(profile, field, f"references unavailable environment variable '{reference}'.")
            return self._environment[reference]
        raise self._field_error(profile, field, f"uses unsupported source '{source_value}'.")

    def resolve(self, profile: AIcCredentialProfile) -> AIcCredential | None:
        raw = self._load_document()
        if not raw or not raw.strip():
            return None
        root = self._parse_object(raw, self.CREDENTIALS_VARIABLE)
        profile_node = root.get(profile.id)
        if profile_node is None:
            return None
        if not isinstance(profile_node, dict):
            raise AIxCredentialException(f"Credential profile '{profile.id}' must be a JSON object.")
        typed = profile_node.get(profile.type.id)
        if typed is None:
            return None
        if not isinstance(typed, dict):
            raise AIxCredentialException(
                f"Credential profile '{profile.id}' type '{profile.type.id}' must be a JSON object."
            )
        secrets = self._secret_context()
        values = {}
        for field in profile.type.supported_fields:
            node = typed.get(field.id)
            if node is None:
                if field in profile.type.required_fields:
                    raise AIxCredentialException(
                        f"Credential profile '{profile.id}' type '{profile.type.id}' is missing required field '{field.id}'."
                    )
                continue
            values[field] = self._resolve_value(profile, field, node, secrets)
        credential = AIcCredential(values)
        if not credential.satisfies(profile):
            credential.close()
            raise AIxCredentialException(
                f"Credential profile '{profile.id}' type '{profile.type.id}' is incomplete."
            )
        return credential
