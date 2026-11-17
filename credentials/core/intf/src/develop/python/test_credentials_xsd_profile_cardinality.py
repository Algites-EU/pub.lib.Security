"""XSD 1.0 validation of the JSON/YAML-equivalent credential profile value set."""

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest


XSD = (Path(__file__).resolve().parents[2] / 'product' / 'xmldefs'
       / 'eu' / 'algites' / 'lib' / 'security' / 'credentials' / 'core'
       / 'credentials_1.xsd')
XS = '{http://www.w3.org/2001/XMLSchema}'


def test_each_credential_type_is_optional_but_not_repeating():
    schema = ET.parse(XSD).getroot()
    typ = next(item for item in schema.findall(f'{XS}complexType')
               if item.get('name') == 'ProfileType')
    group = typ.find(f'{XS}all')
    assert group is not None
    fields = group.findall(f'{XS}element')
    assert [f.get('name') for f in fields] == ['Basic', 'Bearer', 'ApiKey', 'Certificate']
    assert all(field.get('minOccurs') == '0' and field.get('maxOccurs') == '1'
               for field in fields)
    assert typ.find(f'{XS}attribute').get('name') == 'Id'


def test_actual_xsd_accepts_distinct_types_and_rejects_duplicates():
    etree = pytest.importorskip('lxml.etree')
    validator = etree.XMLSchema(etree.parse(str(XSD)))
    basic = ('<Basic><Username><Source>direct_value</Source><Value>a</Value></Username>'
             '<Password><Source>direct_value</Source><Value>b</Value></Password></Basic>')
    bearer = ('<Bearer><Token><Source>direct_value</Source><Value>t</Value>'
              '</Token></Bearer>')
    def document(content):
        return etree.fromstring(('<CredentialDocument><Profile Id="main">'
                                 + content + '</Profile></CredentialDocument>').encode())
    assert validator.validate(document(basic))
    assert validator.validate(document(bearer + basic))
    assert validator.validate(document(basic + bearer))
    assert not validator.validate(document(basic + basic))


def test_profile_variants_match_json_and_yaml_contracts():
    """Ensure the three wire models keep the same four unique credential types."""
    import json
    source = next(parent for parent in XSD.parents if parent.name == 'product')
    def profile(kind, suffix):
        definition = next((source / kind).rglob(f'credentials_1.{suffix}.schema.json'))
        return json.loads(definition.read_text(encoding='utf-8'))['$defs']['profileValues']

    json_profile = profile('jsondefs', 'jsondef')
    yaml_profile = profile('yamldefs', 'yamldef')
    assert json_profile == yaml_profile
    assert json_profile['type'] == 'object'
    assert json_profile['additionalProperties'] is False
    assert json_profile['minProperties'] == 1
    xml_profile = next(node for node in ET.parse(XSD).getroot().findall(f'{XS}complexType')
                       if node.get('name') == 'ProfileType')
    xml_fields = xml_profile.find(f'{XS}all').findall(f'{XS}element')
    assert set(json_profile['properties']) == {node.get('name') for node in xml_fields}
    assert all(node.get('maxOccurs') == '1' and node.get('minOccurs') == '0'
               for node in xml_fields)
