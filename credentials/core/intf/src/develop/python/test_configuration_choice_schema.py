"""Validate cross-format tagged Configuration values in the schema-only prototype.

The physical XML and JSON/YAML envelopes must expose the same Choice branch.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip('jsonschema')
etree = pytest.importorskip('lxml.etree')

PRODUCT = Path(__file__).resolve().parents[2] / 'product'
NAMESPACE = 'https://defs.dev.algites.eu/api/xmldefs/eu/algites/lib/security/credentials/core/credential-profiles_1.xsd'
VARIANTS = {'StringVariant': ('StringValue', 'string'),
            'IntegerVariant': ('IntegerValue', 'integer'),
            'BooleanVariant': ('BooleanValue', 'boolean')}


def _schema(kind: str):
    extension = 'jsondef' if kind == 'jsondefs' else 'yamldef'
    path = next((PRODUCT / kind).rglob(f'credential-profiles_1.{extension}.schema.json'))
    return json.loads(path.read_text(encoding='utf-8'))


@pytest.mark.parametrize('kind', ['jsondefs', 'yamldefs'])
def test_choice_definitions_and_validation(kind: str):
    """Both JSON-schema dialects select exactly one named scalar value."""
    schema = _schema(kind)
    jsonschema.Draft202012Validator.check_schema(schema)
    choice = schema['$defs']['ConfigurationValueType']
    assert choice['x-algites-defscodegen-choice'] is True
    assert choice['type'] == 'object'
    assert choice['minProperties'] == choice['maxProperties'] == 1
    assert choice['additionalProperties'] is False
    assert set(choice['properties']) == {field for field, _ in VARIANTS.values()}
    for name, (field, typ) in VARIANTS.items():
        assert choice['properties'][field]['type'] == typ
    valid = {'Profile': [{'Id': 'development', 'Configuration': {'Entry': [
        {'Name': 'server', 'Choice': {'StringValue': 'localhost'}},
        {'Name': 'timeout', 'Choice': {'IntegerValue': 30}},
        {'Name': 'enabled', 'Choice': {'BooleanValue': True}},
    ]}}]}
    validator = jsonschema.Draft202012Validator(schema)
    assert validator.is_valid(valid)
    for value in (
        {'Profile': [{'Id': 'development', 'Configuration': {'Entry': [{'Name': 'timeout'}]}}]},
        {'Profile': [{'Id': 'development', 'Configuration': {'Entry': [{'Name': 'timeout', 'Choice': {'IntegerValue': '30'}}]}}]},
        {'Profile': [{'Id': 'development', 'Configuration': {'Entry': [{'Name': 'timeout',
            'Choice': {'IntegerValue': 30, 'BooleanValue': True}}]}}]},
        {'Profile': [{'Id': 'development', 'Configuration': {'Entry': [{'Choice': {'IntegerValue': 30}}]}}]},
    ):
        assert not validator.is_valid(value)


def test_xml_choice_and_key_validation():
    """XSD uses the same variant names and forbids duplicate map keys."""
    source = next((PRODUCT / 'xmldefs').rglob('credential-profiles_1.xsd'))
    schema = etree.XMLSchema(etree.parse(str(source)))
    tree = etree.parse(str(source))
    ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}
    values = tree.xpath('//xs:complexType[@name="ConfigurationValueType"]/xs:choice/xs:element', namespaces=ns)
    assert [(element.get('name'), element.get('type')) for element in values] == [
        ('StringValue', 'xs:string'), ('IntegerValue', 'xs:integer'), ('BooleanValue', 'xs:boolean')]
    keys = tree.xpath('//xs:key[@name="ConfigurationEntryByName"]', namespaces=ns)
    assert len(keys) == 1
    assert keys[0].find('{http://www.w3.org/2001/XMLSchema}field').get('xpath') == '@Name'

    def document(entries: str):
        return etree.fromstring((
            f'<CredentialProfiles xmlns="{NAMESPACE}">'
            '<Profile Id="development"><Configuration>'
            f'{entries}'
            '</Configuration></Profile></CredentialProfiles>').encode())

    assert schema.validate(document(
        '<Entry Name="server"><Choice><StringValue>localhost</StringValue></Choice></Entry>'
        '<Entry Name="timeout"><Choice><IntegerValue>30</IntegerValue></Choice></Entry>'
        '<Entry Name="enabled"><Choice><BooleanValue>true</BooleanValue></Choice></Entry>'))
    assert not schema.validate(document(
        '<Entry Name="server"><Choice><StringValue>localhost</StringValue></Choice></Entry>'
        '<Entry Name="server"><Choice><BooleanValue>true</BooleanValue></Choice></Entry>'))
    assert not schema.validate(document(
        '<Entry Name="timeout"><Choice><IntegerValue>not-a-number</IntegerValue></Choice></Entry>'))
    assert not schema.validate(document(
        '<Entry Name="timeout"><Choice><StringValue>a</StringValue><BooleanValue>true</BooleanValue></Choice></Entry>'))
