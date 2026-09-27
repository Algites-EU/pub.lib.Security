# Credential core interfaces

Technology-neutral credential contracts shared by Algites credential providers, stores, tools, and build integrations.

The module defines named credential profiles and credential types, credential fields and value sources, and the parsed `CredentialDocument` model used for complete multi-profile documents.

The credential document model is serialization-neutral. JSON and YAML use the existing map-shaped profile representation; XML uses `CredentialDocument/Profile[@Id]` while mapping to the same logical model. Version-1 schema definitions are provided for JSON, YAML, and XML representations.
