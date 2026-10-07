from __future__ import annotations

from eu.algites.lib.security.credentials.core.aiig_credential_value_source_fields_1 import AIigCredentialValueSourceFields_1
from eu.algites.lib.security.credentials.core.aiig_credentials_1 import AIigCredentials_1






import io
import json
from collections.abc import Mapping
from pathlib import Path
from typing import BinaryIO
from urllib.request import urlopen
from xml.etree import ElementTree

from eu.algites.lib.security.credentials.core.aic_credential_document import AIcCredentialDocument
from eu.algites.lib.security.credentials.core.aic_credential_value_reference import AIcCredentialValueReference
from eu.algites.lib.security.credentials.core.ain_credential_document_format import AInCredentialDocumentFormat
from eu.algites.lib.security.credentials.core.ain_credential_field import AInCredentialField
from eu.algites.lib.security.credentials.core.ain_credential_type import AInCredentialType
from eu.algites.lib.security.credentials.core.ain_credential_value_source import AInCredentialValueSource
from eu.algites.lib.security.credentials.core.aix_credential_exception import AIxCredentialException


class AIcCredentialDocumentReader:
    """Reads complete Algites credential documents from JSON, YAML, or XML."""

    _DETECTION_PREFIX_SIZE = 8192

    def read(self, source: str | bytes | Path | BinaryIO) -> AIcCredentialDocument:
        if isinstance(source, Path):
            with source.open("rb") as stream:
                return self.read(stream)
        if isinstance(source, bytes):
            return self.read(io.BytesIO(source))
        if isinstance(source, str):
            return self.read(io.BytesIO(source.encode("utf-8")))
        stream = self._buffered(source)
        credential_format = self._detect_format(stream.peek(self._DETECTION_PREFIX_SIZE))
        return self._read_stream(stream, credential_format)

    def read_url(self, url: str) -> AIcCredentialDocument:
        with urlopen(url) as stream:
            return self.read(stream)

    def read_json(self, source: str | bytes | Path | BinaryIO) -> AIcCredentialDocument:
        return self._read_explicit(source, AInCredentialDocumentFormat.JSON)

    def read_yaml(self, source: str | bytes | Path | BinaryIO) -> AIcCredentialDocument:
        return self._read_explicit(source, AInCredentialDocumentFormat.YAML)

    def read_xml(self, source: str | bytes | Path | BinaryIO) -> AIcCredentialDocument:
        return self._read_explicit(source, AInCredentialDocumentFormat.XML)

    def read_json_url(self, url: str) -> AIcCredentialDocument:
        return self._read_url_explicit(url, AInCredentialDocumentFormat.JSON)

    def read_yaml_url(self, url: str) -> AIcCredentialDocument:
        return self._read_url_explicit(url, AInCredentialDocumentFormat.YAML)

    def read_xml_url(self, url: str) -> AIcCredentialDocument:
        return self._read_url_explicit(url, AInCredentialDocumentFormat.XML)

    def _read_explicit(
        self,
        source: str | bytes | Path | BinaryIO,
        credential_format: AInCredentialDocumentFormat,
    ) -> AIcCredentialDocument:
        if isinstance(source, Path):
            with source.open("rb") as stream:
                return self._read_stream(stream, credential_format)
        if isinstance(source, bytes):
            return self._read_stream(io.BytesIO(source), credential_format)
        if isinstance(source, str):
            return self._read_stream(io.BytesIO(source.encode("utf-8")), credential_format)
        return self._read_stream(source, credential_format)

    def _read_url_explicit(
        self,
        url: str,
        credential_format: AInCredentialDocumentFormat,
    ) -> AIcCredentialDocument:
        with urlopen(url) as stream:
            return self._read_stream(stream, credential_format)

    def _read_stream(
        self,
        stream: BinaryIO,
        credential_format: AInCredentialDocumentFormat,
    ) -> AIcCredentialDocument:
        if credential_format is AInCredentialDocumentFormat.JSON:
            return self._parse_mapping(self._load_json(stream), "JSON")
        if credential_format is AInCredentialDocumentFormat.YAML:
            return self._parse_mapping(self._load_yaml(stream), "YAML")
        if credential_format is AInCredentialDocumentFormat.XML:
            return self._load_xml(stream)
        raise AIxCredentialException(f"Unsupported credential document format: {credential_format}")

    @staticmethod
    def _buffered(stream: BinaryIO) -> io.BufferedReader:
        if isinstance(stream, io.BufferedReader):
            return stream
        return io.BufferedReader(stream)

    @staticmethod
    def _load_json(stream: BinaryIO) -> object:
        try:
            return json.load(stream)
        except (json.JSONDecodeError, UnicodeDecodeError) as exception:
            raise AIxCredentialException("Credential document is not valid JSON.") from exception

    @staticmethod
    def _load_yaml(stream: BinaryIO) -> object:
        try:
            import yaml
        except ImportError as exception:
            raise AIxCredentialException("YAML credential documents require the PyYAML package.") from exception
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as exception:
            raise AIxCredentialException("Credential document is not valid YAML.") from exception

    def _parse_mapping(self, root: object, format_name: str) -> AIcCredentialDocument:
        if not isinstance(root, Mapping):
            raise AIxCredentialException(f"Credential document must contain a {format_name} object at its root.")
        profiles: dict[str, dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]]] = {}
        for profile_id, profile_node in root.items():
            if profile_id == AIigCredentials_1.SCHEMA_FIELD_NAME__SCHEMA:
                if not isinstance(profile_node, str):
                    raise AIxCredentialException("Credential document '$schema' must be a string.")
                continue
            if not isinstance(profile_id, str) or not isinstance(profile_node, Mapping):
                raise AIxCredentialException("Credential profiles must use string ids and object values.")
            typed_credentials: dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]] = {}
            for type_property, type_node in profile_node.items():
                credential_type = self._type_from_property_name(type_property)
                if not isinstance(type_node, Mapping):
                    raise AIxCredentialException(
                        f"Credential profile '{profile_id}' type '{credential_type.id}' must be an object."
                    )
                fields: dict[AInCredentialField, AIcCredentialValueReference] = {}
                for field_name, field_node in type_node.items():
                    try:
                        field = AInCredentialField.from_id(str(field_name))
                    except ValueError as exception:
                        raise AIxCredentialException(
                            f"Credential profile '{profile_id}' type '{credential_type.id}' contains unsupported field "
                            f"'{field_name}'."
                        ) from exception
                    if field not in credential_type.supported_fields:
                        raise AIxCredentialException(
                            f"Credential profile '{profile_id}' type '{credential_type.id}' does not support field "
                            f"'{field.id}'."
                        )
                    fields[field] = self._parse_value_reference(profile_id, credential_type, field, field_node)
                typed_credentials[credential_type] = fields
            profiles[profile_id] = typed_credentials
        try:
            return AIcCredentialDocument(profiles)
        except ValueError as exception:
            raise AIxCredentialException(str(exception)) from exception

    def _parse_value_reference(
        self,
        profile_id: str,
        credential_type: AInCredentialType,
        field: AInCredentialField,
        node: object,
    ) -> AIcCredentialValueReference:
        if not isinstance(node, Mapping):
            raise self._field_error(profile_id, credential_type, field, "must be an object containing Source and Value.")
        if set(node.keys()) != {AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__SOURCE, AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__VALUE}:
            raise self._field_error(profile_id, credential_type, field, "must contain exactly Source and Value.")
        source_value = node.get(AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__SOURCE)
        reference = node.get(AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__VALUE)
        if not isinstance(source_value, str):
            raise self._field_error(profile_id, credential_type, field, "is missing string property 'Source'.")
        if not isinstance(reference, str):
            raise self._field_error(profile_id, credential_type, field, "is missing string property 'Value'.")
        try:
            return AIcCredentialValueReference(AInCredentialValueSource.from_id(source_value), reference)
        except ValueError as exception:
            raise self._field_error(profile_id, credential_type, field, str(exception)) from exception

    def _load_xml(self, stream: BinaryIO) -> AIcCredentialDocument:
        try:
            root = ElementTree.parse(stream).getroot()
        except (ElementTree.ParseError, UnicodeDecodeError) as exception:
            raise AIxCredentialException("Credential document is not valid XML.") from exception
        if root.tag != "CredentialDocument":
            raise AIxCredentialException("XML credential document root element must be CredentialDocument.")
        profiles: dict[str, dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]]] = {}
        for profile_element in list(root):
            if profile_element.tag != "Profile":
                raise AIxCredentialException(
                    f"XML credential document contains unsupported element '{profile_element.tag}'."
                )
            profile_id = profile_element.attrib.get("Id", "")
            if not profile_id:
                raise AIxCredentialException("XML credential Profile element is missing required Id attribute.")
            typed_credentials: dict[AInCredentialType, dict[AInCredentialField, AIcCredentialValueReference]] = {}
            for type_element in list(profile_element):
                credential_type = self._type_from_property_name(type_element.tag)
                fields: dict[AInCredentialField, AIcCredentialValueReference] = {}
                for field_element in list(type_element):
                    try:
                        field = AInCredentialField.from_id(field_element.tag)
                    except ValueError as exception:
                        raise AIxCredentialException(
                            f"Credential profile '{profile_id}' type '{credential_type.id}' contains unsupported field "
                            f"'{field_element.tag}'."
                        ) from exception
                    if field not in credential_type.supported_fields:
                        raise AIxCredentialException(
                            f"Credential profile '{profile_id}' type '{credential_type.id}' does not support field "
                            f"'{field.id}'."
                        )
                    children = list(field_element)
                    if [child.tag for child in children] != [AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__SOURCE, AIigCredentialValueSourceFields_1.SCHEMA_FIELD_NAME__VALUE]:
                        raise self._field_error(
                            profile_id,
                            credential_type,
                            field,
                            "must contain Source and Value XML elements in that order.",
                        )
                    source_text = children[0].text or ""
                    value_text = children[1].text or ""
                    try:
                        fields[field] = AIcCredentialValueReference(
                            AInCredentialValueSource.from_id(source_text),
                            value_text,
                        )
                    except ValueError as exception:
                        raise self._field_error(profile_id, credential_type, field, str(exception)) from exception
                if credential_type in typed_credentials:
                    raise AIxCredentialException(
                        f"Credential profile '{profile_id}' contains duplicate type '{credential_type.property_name}'."
                    )
                typed_credentials[credential_type] = fields
            if profile_id in profiles:
                raise AIxCredentialException(f"Duplicate credential profile id '{profile_id}'.")
            profiles[profile_id] = typed_credentials
        try:
            return AIcCredentialDocument(profiles)
        except ValueError as exception:
            raise AIxCredentialException(str(exception)) from exception

    @staticmethod
    def _type_from_property_name(property_name: object) -> AInCredentialType:
        for credential_type in AInCredentialType:
            if credential_type.property_name == property_name:
                return credential_type
        raise AIxCredentialException(f"Unsupported credential type property '{property_name}'.")

    @staticmethod
    def _field_error(
        profile_id: str,
        credential_type: AInCredentialType,
        field: AInCredentialField,
        message: str,
    ) -> AIxCredentialException:
        return AIxCredentialException(f"Credential '{profile_id}/{credential_type.id}/{field.id}' {message}")

    @classmethod
    def _detect_format(cls, prefix: bytes) -> AInCredentialDocumentFormat:
        text = cls._decode_detection_prefix(prefix)
        first = next((character for character in text if not character.isspace()), "")
        if first in "{[":
            return AInCredentialDocumentFormat.JSON
        if first == "<":
            return AInCredentialDocumentFormat.XML
        return AInCredentialDocumentFormat.YAML

    @staticmethod
    def _decode_detection_prefix(prefix: bytes) -> str:
        encodings = (
            (b"\xef\xbb\xbf", "utf-8-sig"),
            (b"\x00\x00\xfe\xff", "utf-32-be"),
            (b"\xff\xfe\x00\x00", "utf-32-le"),
            (b"\xfe\xff", "utf-16-be"),
            (b"\xff\xfe", "utf-16-le"),
        )
        for marker, encoding in encodings:
            if prefix.startswith(marker):
                return prefix[len(marker):].decode(encoding, errors="ignore")
        return prefix.decode("utf-8", errors="ignore")
