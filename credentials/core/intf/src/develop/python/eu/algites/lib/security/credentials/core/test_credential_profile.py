from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource


def test_canonical_environment_contract():
    profile = AIcCredentialProfile("repsy-private-download", AInCredentialType.BASIC)
    assert profile.environment_prefix == "ALGITES_CREDENTIAL_REPSY_PRIVATE_DOWNLOAD_BASIC"
    assert profile.environment_variable(AInCredentialField.USERNAME) == "ALGITES_CREDENTIAL_REPSY_PRIVATE_DOWNLOAD_BASIC_USERNAME"
    assert profile.storage_key == "repsy-private-download/basic"


def test_type_contract():
    assert AInCredentialType.BASIC.required_fields == (AInCredentialField.USERNAME, AInCredentialField.PASSWORD)
    assert AInCredentialType.API_KEY.required_fields == (AInCredentialField.API_KEY,)
    assert AInCredentialType.CERTIFICATE.optional_fields == (AInCredentialField.PRIVATE_KEY, AInCredentialField.PRIVATE_KEY_PASSWORD)
    assert AInCredentialType.API_KEY.id == "api_key"
    assert AInCredentialType.API_KEY.property_name == "ApiKey"
    assert AInCredentialField.PRIVATE_KEY.id == "PrivateKey"
    assert AInCredentialValueSource.SECRET_CONTENT.id == "secret_content"
