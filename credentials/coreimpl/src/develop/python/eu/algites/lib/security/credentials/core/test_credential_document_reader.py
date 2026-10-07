import io
import json
import pytest

from eu.algites.lib.security.credentials.core.aic_credential_document_reader import AIcCredentialDocumentReader
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


JSON_DOCUMENT = '''{
  "profile": {
    "Basic": {
      "Username": {"Source": "direct_value", "Value": "user"},
      "Password": {"Source": "direct_value", "Value": "password"}
    }
  }
}'''

YAML_DOCUMENT = '''
profile:
  Basic:
    Username:
      Source: direct_value
      Value: user
    Password:
      Source: direct_value
      Value: password
'''

XML_DOCUMENT = '''
<CredentialDocument>
  <Profile Id="profile">
    <Basic>
      <Username><Source>direct_value</Source><Value>user</Value></Username>
      <Password><Source>direct_value</Source><Value>password</Value></Password>
    </Basic>
  </Profile>
</CredentialDocument>
'''


def _assert_basic(document):
    values = document.get_credential_values("profile", AInCredentialType.BASIC)
    assert values is not None
    assert values[AInCredentialField.USERNAME].source is AInCredentialValueSource.DIRECT_VALUE
    assert values[AInCredentialField.USERNAME].value == "user"
    assert values[AInCredentialField.PASSWORD].value == "password"


def test_root_schema_hint_is_not_a_credential_profile():
    reader = AIcCredentialDocumentReader()
    schema_uri = "https://defs.dev.algites.eu/api/yamldefs/eu/algites/lib/security/credentials/core/credentials_1.yamldef.schema.json"
    json_document = reader.read_json(json.dumps({"$schema": schema_uri, **json.loads(JSON_DOCUMENT)}))
    yaml_document = reader.read_yaml("$schema: " + schema_uri + "\n" + YAML_DOCUMENT)
    _assert_basic(json_document)
    _assert_basic(yaml_document)
    assert not json_document.contains_profile("$schema")
    assert not yaml_document.contains_profile("$schema")
    with pytest.raises(AIxCredentialException):
        reader.read_json('{"$schema":4}')
    with pytest.raises(AIxCredentialException):
        reader.read_yaml("$schema: 4\n")


def test_detects_json_yaml_and_xml():
    reader = AIcCredentialDocumentReader()
    _assert_basic(reader.read(JSON_DOCUMENT))
    _assert_basic(reader.read(YAML_DOCUMENT))
    _assert_basic(reader.read(XML_DOCUMENT))


def test_detection_preserves_non_seekable_stream():
    class NonSeekable(io.RawIOBase):
        def __init__(self, data: bytes):
            self._stream = io.BytesIO(data)

        def readable(self):
            return True

        def readinto(self, buffer):
            data = self._stream.read(len(buffer))
            buffer[:len(data)] = data
            return len(data)

    _assert_basic(AIcCredentialDocumentReader().read(NonSeekable(JSON_DOCUMENT.encode("utf-8"))))


def test_explicit_readers():
    reader = AIcCredentialDocumentReader()
    _assert_basic(reader.read_json(JSON_DOCUMENT))
    _assert_basic(reader.read_yaml(YAML_DOCUMENT))
    _assert_basic(reader.read_xml(XML_DOCUMENT))
