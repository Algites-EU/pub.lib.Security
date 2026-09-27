# Credential core implementation

Reusable implementation of Algites credential resolution, complete credential-document parsing, secure-store discovery, and credential persistence.

## Credential documents

`AIcCredentialDocumentReader` reads complete multi-profile credential documents in JSON, YAML, or XML form.

Automatic `read(...)` entry points detect the serialization from content. They do not infer it from a file extension. Format-specific `readJson(...)`, `readYaml(...)`, and `readXml(...)` entry points are available when the caller already knows the format and wants to skip detection.

Inputs include in-memory text, streams, paths, and URLs. Stream autodetection buffers the inspected prefix and passes the complete stream to the selected parser; callers do not need to provide a resettable or re-entrant stream.

The persistent credential service normalizes stored complete documents to the existing canonical JSON representation so profile-level set/remove operations remain deterministic regardless of the input serialization.

The Python YAML reader uses PyYAML when YAML input is consumed. JSON and XML use the Python standard library.
