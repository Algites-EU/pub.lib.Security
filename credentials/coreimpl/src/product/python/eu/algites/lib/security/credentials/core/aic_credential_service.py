import json

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_document_reader import AIcCredentialDocumentReader
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException
from eu.algites.lib.security.credentials.core.aic_credential_store_provider import AIcCredentialStoreProvider


class AIcCredentialService:
    """Persistent credential management facade shared by tools and applications."""

    def __init__(self, store_provider: AIcCredentialStoreProvider | None = None):
        self._store_provider = store_provider or AIcCredentialStoreProvider()

    @property
    def store_id(self) -> str:
        return self._store_provider.require_available_store().id

    def _read_document_object(self) -> dict:
        raw = self._store_provider.read_credential_document()
        if raw is None:
            return {}
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exception:
            raise AIxCredentialException("ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS does not contain valid JSON.") from exception
        if not isinstance(value, dict):
            raise AIxCredentialException("ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS must contain a JSON object.")
        return value

    def _write_document_object(self, value: dict) -> None:
        self._store_provider.write_credential_document(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        )

    def is_stored(self, profile: AIcCredentialProfile) -> bool:
        typed = self._read_document_object().get(profile.id, {}).get(profile.type.property_name, {})
        return isinstance(typed, dict) and all(field.id in typed for field in profile.type.required_fields)

    def store(self, profile: AIcCredentialProfile, credential: AIcCredential) -> None:
        if not credential.satisfies(profile):
            raise AIxCredentialException(f"Credential does not contain all fields required by profile '{profile.id}'.")
        root = self._read_document_object()
        profile_node = root.setdefault(profile.id, {})
        if not isinstance(profile_node, dict):
            raise AIxCredentialException(f"ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS entry '{profile.id}' must be a JSON object.")
        typed = {}
        for field in profile.type.supported_fields:
            value = credential.get_text(field)
            if value is not None:
                typed[field.id] = {"Source": AInCredentialValueSource.DIRECT_VALUE.id, "Value": value}
        profile_node[profile.type.property_name] = typed
        self._write_document_object(root)

    def remove(self, profile: AIcCredentialProfile) -> None:
        root = self._read_document_object()
        profile_node = root.get(profile.id)
        if not isinstance(profile_node, dict):
            return
        profile_node.pop(profile.type.property_name, None)
        if not profile_node:
            root.pop(profile.id, None)
        if root:
            self._write_document_object(root)
        else:
            self._store_provider.delete_credential_document()

    def read_credential_document(self) -> str | None:
        value = self._store_provider.read_credential_document()
        return None if value is None else value.decode("utf-8")

    def store_credential_document(self, document: str) -> None:
        parsed = AIcCredentialDocumentReader().read(document)
        normalized: dict = {}
        for profile_id in parsed.profile_ids:
            profile_node = {}
            for credential_type in AInCredentialType:
                values = parsed.get_credential_values(profile_id, credential_type)
                if values is None:
                    continue
                typed = {}
                for field, reference in values.items():
                    typed[field.id] = {"Source": reference.source.id, "Value": reference.value}
                profile_node[credential_type.property_name] = typed
            normalized[profile_id] = profile_node
        self._write_document_object(normalized)

    def remove_credential_document(self) -> None:
        self._store_provider.delete_credential_document()

    def read_named_secret(self, secret_id: str) -> str | None:
        value = self._store_provider.read_named_secret(secret_id)
        return None if value is None else value.decode("utf-8")

    def store_named_secret(self, secret_id: str, value: str) -> None:
        self._store_provider.write_named_secret(secret_id, value.encode("utf-8"))

    def remove_named_secret(self, secret_id: str) -> None:
        self._store_provider.delete_named_secret(secret_id)

    def store_diagnostics(self) -> str:
        return self._store_provider.build_unavailable_store_message()
