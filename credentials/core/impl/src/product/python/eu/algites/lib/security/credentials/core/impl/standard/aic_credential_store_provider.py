import re
from collections.abc import Iterable

from eu.algites.lib.security.credentials.core.aic_credential_store_availability import AIcCredentialStoreAvailability
from eu.algites.lib.security.credentials.core.aii_credential_store import AIiCredentialStore
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


class AIcCredentialStoreProvider:
    """Access facade for the highest-priority available credential-store backend."""

    CREDENTIAL_DOCUMENT_STORAGE_KEY = "document/ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS"
    _NAMED_SECRET_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

    def __init__(self, stores: Iterable[AIiCredentialStore] = ()):
        self._stores = sorted(stores, key=lambda store: (-store.priority, store.id))

    def available_store(self) -> AIiCredentialStore | None:
        return next((store for store in self._stores if store.availability().is_available), None)

    def store_availabilities(self) -> tuple[AIcCredentialStoreAvailability, ...]:
        return tuple(store.availability() for store in self._stores)

    def require_available_store(self) -> AIiCredentialStore:
        store = self.available_store()
        if store is None:
            raise AIxCredentialException(self.build_unavailable_store_message())
        return store

    def read_credential_document(self) -> bytes | None:
        store = self.available_store()
        return None if store is None else store.read(self.CREDENTIAL_DOCUMENT_STORAGE_KEY)

    def write_credential_document(self, value: bytes) -> None:
        self.require_available_store().write(self.CREDENTIAL_DOCUMENT_STORAGE_KEY, value)

    def delete_credential_document(self) -> None:
        self.require_available_store().delete(self.CREDENTIAL_DOCUMENT_STORAGE_KEY)

    @classmethod
    def _named_secret_storage_key(cls, secret_id: str) -> str:
        normalized = secret_id.strip()
        if not cls._NAMED_SECRET_ID_PATTERN.fullmatch(normalized):
            raise AIxCredentialException(
                "Secret id must use only letters, digits, dot, underscore, or dash and must start with a letter or digit: "
                + secret_id
            )
        return f"secret/{normalized}"

    def read_named_secret(self, secret_id: str) -> bytes | None:
        store = self.available_store()
        return None if store is None else store.read(self._named_secret_storage_key(secret_id))

    def write_named_secret(self, secret_id: str, value: bytes) -> None:
        self.require_available_store().write(self._named_secret_storage_key(secret_id), value)

    def delete_named_secret(self, secret_id: str) -> None:
        self.require_available_store().delete(self._named_secret_storage_key(secret_id))

    def build_unavailable_store_message(self) -> str:
        if not self._stores:
            return (
                "No supported Algites persistent credential store is available.\n"
                " - no AIiCredentialStore provider was configured\n"
                "   Ensure a platform credential-store implementation is available."
            )
        lines = ["No supported Algites persistent credential store is available."]
        for store in self._stores:
            availability = store.availability()
            lines.append(f" - {store.id}: {availability.status.name.lower().replace('_', '-')} - {availability.message}")
            lines.extend(f"   {item}" for item in availability.remediation)
        return "\n".join(lines)
