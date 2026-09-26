from abc import ABC, abstractmethod

from eu.algites.lib.security.credentials.core.aic_credential_store_availability import AIcCredentialStoreAvailability


class AIiCredentialStore(ABC):
    """Persistent secure-store service provider interface."""

    @property
    @abstractmethod
    def id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def priority(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def availability(self) -> AIcCredentialStoreAvailability:
        raise NotImplementedError

    @abstractmethod
    def read(self, storage_key: str) -> bytes | None:
        raise NotImplementedError

    @abstractmethod
    def write(self, storage_key: str, value: bytes) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        raise NotImplementedError
