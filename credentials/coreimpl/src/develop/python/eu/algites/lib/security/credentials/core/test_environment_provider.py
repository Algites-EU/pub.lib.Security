import pytest

from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.aic_environment_credential_provider import AIcEnvironmentCredentialProvider
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


def test_resolves_complete_basic_profile():
    provider = AIcEnvironmentCredentialProvider({
        "ALGITES_CREDENTIAL_REPSY_PRIVATE_BASIC_USERNAME": "user",
        "ALGITES_CREDENTIAL_REPSY_PRIVATE_BASIC_PASSWORD": "secret",
    })
    profile = AIcCredentialProfile("repsy-private", AInCredentialType.BASIC)
    credential = provider.resolve(profile)
    assert credential is not None
    with credential:
        assert credential.get_text(AInCredentialField.USERNAME) == "user"
        assert credential.get_text(AInCredentialField.PASSWORD) == "secret"


def test_rejects_partial_profile():
    provider = AIcEnvironmentCredentialProvider({"ALGITES_CREDENTIAL_REPSY_PRIVATE_BASIC_USERNAME": "user"})
    with pytest.raises(AIxCredentialException):
        provider.resolve(AIcCredentialProfile("repsy-private", AInCredentialType.BASIC))
