"""Canonical tagged credential ValueSource serialization and legacy migration tests."""
from __future__ import annotations

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from eu.algites.lib.security.credentials.core.impl.standard.aic_credential_document_reader import AIcCredentialDocumentReader
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException

SCHEMA_ROOT = Path(__file__).resolve().parents[12] / 'intf/src/product/jsondefs'


def test_external_validator_and_reader_accept_canonical_profile_list():
    """Both JSON Schema and reader accept explicit Profile Id and Source/Value."""
    schema = json.loads(next(SCHEMA_ROOT.rglob('credential-document_1.jsondef.schema.json')).read_text())
    instance = {'Profile': [{'Id': 'example', 'Bearer': {'Token': {
        'Source': 'secret_content', 'Value': 'EXAMPLE_REFERENCE'
    }}}]}
    assert Draft202012Validator(schema).is_valid(instance)
    reference = AIcCredentialDocumentReader().read_json(json.dumps(instance)).get_credential_values(
        'example', AInCredentialType.BEARER)[AInCredentialField.TOKEN]
    assert reference.source.choice_variant == 'SecretContent'
    assert reference.value == 'EXAMPLE_REFERENCE'


def test_choice_tag_must_agree_with_source_discriminator():
    """Never accept a Source discriminator inconsistent with the named variant."""
    payload = {'example': {'Bearer': {'Token': {
        'DirectValue': {'Source': 'secret_content', 'Value': 'EXAMPLE_REFERENCE'}
    }}}}
    with pytest.raises(AIxCredentialException, match='conflicts'):
        AIcCredentialDocumentReader().read_json(json.dumps(payload))


def test_legacy_source_value_remains_readable():
    """Existing remotely stored credentials can still be read during migration."""
    legacy = {'example': {'Bearer': {'Token': {'Source': 'direct_value', 'Value': 'x'}}}}
    parsed = AIcCredentialDocumentReader().read_json(json.dumps(legacy))
    ref = parsed.get_credential_values('example', AInCredentialType.BEARER)[AInCredentialField.TOKEN]
    assert ref.source.choice_variant == 'DirectValue'
