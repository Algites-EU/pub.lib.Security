from enum import Enum


class AInCredentialStoreAvailabilityStatus(Enum):
    """Availability status reported by a persistent credential-store backend."""

    AVAILABLE = "AVAILABLE"
    UNSUPPORTED_PLATFORM = "UNSUPPORTED_PLATFORM"
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    SERVICE_LOCKED = "SERVICE_LOCKED"
    ERROR = "ERROR"
