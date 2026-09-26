from eu.algites.lib.security.credentials.core.aic_credential_store_availability import AIcCredentialStoreAvailability
from eu.algites.lib.security.credentials.core.aic_credential_store_provider import AIcCredentialStoreProvider
from eu.algites.lib.security.credentials.core.aii_credential_store import AIiCredentialStore


class _MemoryStore(AIiCredentialStore):
    def __init__(self, store_id: str, priority: int):
        self._id = store_id
        self._priority = priority
        self.values = {}

    @property
    def id(self):
        return self._id

    @property
    def priority(self):
        return self._priority

    def availability(self):
        return AIcCredentialStoreAvailability.available("available")

    def read(self, storage_key):
        value = self.values.get(storage_key)
        return None if value is None else bytes(value)

    def write(self, storage_key, value):
        self.values[storage_key] = bytes(value)

    def delete(self, storage_key):
        self.values.pop(storage_key, None)


def test_uses_highest_priority_store():
    low = _MemoryStore("low", 10)
    high = _MemoryStore("high", 20)
    provider = AIcCredentialStoreProvider((low, high))
    provider.write_credential_document(b'{"profile":{}}')
    assert AIcCredentialStoreProvider.CREDENTIAL_DOCUMENT_STORAGE_KEY not in low.values
    assert provider.read_credential_document() == b'{"profile":{}}'
