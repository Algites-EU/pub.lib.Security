import json

from eu.algites.lib.security.credentials.core.aic_credential import AIcCredential
from eu.algites.lib.security.credentials.core.aic_credential_profile import AIcCredentialProfile
from eu.algites.lib.security.credentials.core.aic_credential_service import AIcCredentialService
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType


class MemoryDocumentStore:
    document = None

    def read_credential_document(self):
        return self.document

    def write_credential_document(self, value):
        self.document = value


def test_storing_credential_preserves_canonical_field_ids():
    store = MemoryDocumentStore()
    service = AIcCredentialService(store)
    profile = AIcCredentialProfile("example", AInCredentialType.BASIC)
    with AIcCredential({AInCredentialField.USERNAME: "u", AInCredentialField.PASSWORD: "p"}) as credential:
        service.store(profile, credential)
    assert json.loads(store.document) == {"example": {"Basic": {
        "Username": {"Source": "direct_value", "Value": "u"},
        "Password": {"Source": "direct_value", "Value": "p"},
    }}}


def test_storing_document_preserves_value_source_ids():
    store = MemoryDocumentStore()
    service = AIcCredentialService(store)
    document = {"example": {"Bearer": {"Token": {"Source": "secret_content", "Value": "TOKEN_SECRET"}}}}
    service.store_credential_document(json.dumps(document))
    assert json.loads(store.document) == document
