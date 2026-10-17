from dataclasses import dataclass

from eu.algites.lib.security.credentials.core.ain_credential_store_availability_status import AInCredentialStoreAvailabilityStatus


@dataclass(frozen=True)
class AIcCredentialStoreAvailability:
    """Diagnostic availability result for a persistent credential-store backend."""

    status: AInCredentialStoreAvailabilityStatus
    message: str
    remediation: tuple[str, ...] = ()

    @property
    def is_available(self) -> bool:
        return self.status is AInCredentialStoreAvailabilityStatus.AVAILABLE

    @classmethod
    def available(cls, message: str) -> "AIcCredentialStoreAvailability":
        return cls(AInCredentialStoreAvailabilityStatus.AVAILABLE, message, ())
