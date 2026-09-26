from pathlib import Path

from eu.algites.lib.security.credentials.core.aic_credential_document_provider import AIcCredentialDocumentProvider
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType


def test_resolves_direct_and_secret_content():
    provider = AIcCredentialDocumentProvider({
        "ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS": '{"profile":{"Basic":{"Username":{"Source":"direct_value","Value":"user"},"Password":{"Source":"secret_content","Value":"PASSWORD_SECRET"}}}}',
        "_TMP_ALGITES_CREDENTIAL_SECRETS_JSON": '{"PASSWORD_SECRET":"secret"}',
    }, Path("."))
    profile = AIcCredentialProfile("profile", AInCredentialType.BASIC)
    credential = provider.resolve(profile)
    assert credential is not None
    with credential:
        assert credential.get_text(AInCredentialField.USERNAME) == "user"
        assert credential.get_text(AInCredentialField.PASSWORD) == "secret"
