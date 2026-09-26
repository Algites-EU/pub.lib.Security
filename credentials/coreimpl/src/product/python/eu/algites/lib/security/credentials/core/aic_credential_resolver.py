from collections.abc import Iterable

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_document_provider import AIcCredentialDocumentProvider
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.aii_credential_provider import AIiCredentialProvider
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


class AIcCredentialResolver:
    """Ordered credential-provider chain used by applications and tools."""

    def __init__(self, providers: Iterable[AIiCredentialProvider]):
        self._providers = tuple(providers)

    @classmethod
    def standard(cls) -> "AIcCredentialResolver":
        return cls((AIcCredentialDocumentProvider(),))

    def resolve(self, profile: AIcCredentialProfile) -> AIcCredential | None:
        for provider in self._providers:
            credential = provider.resolve(profile)
            if credential is not None:
                return credential
        return None

    def require(self, profile: AIcCredentialProfile) -> AIcCredential:
        credential = self.resolve(profile)
        if credential is not None:
            return credential
        raise AIxCredentialException(
            f"Credential profile '{profile.id}' with type '{profile.type.id}' is not available.\n"
            "Provide the profile through the universal ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS document "
            "in the environment or in an available Algites OS credential store."
        )
