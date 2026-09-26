from abc import ABC, abstractmethod

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile


class AIiCredentialProvider(ABC):
    """Resolves a complete credential profile from one runtime source."""

    @abstractmethod
    def resolve(self, profile: AIcCredentialProfile) -> AIcCredential | None:
        raise NotImplementedError
