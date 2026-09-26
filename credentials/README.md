# Credentials library subsystem

The credential library is a reusable security subsystem. It defines non-secret credential profiles, typed credential values, provider chains, a provider-independent credential document, persistent secure-store contracts, and OS-specific secure-store backends.

Supported credential types are `basic`, `bearer`, `api_key`, and `certificate`. Supported value sources are `direct_value`, `file_content`, `secret_content`, and `environment_variable_content`.

The universal credential document is carried through `ALGITES_DEVOPS_BUILD_REPOSITORY_CREDENTIALS`. `_TMP_ALGITES_CREDENTIAL_SECRETS_JSON` is an optional provider context for exact-name `secret_content` materialization; it is not a second credential format.

Credential enum values and document properties are intentionally distinct. Type/source enum values use lower snake case (`api_key`, `secret_content`), while Algites document properties use UpperCamelCase (`ApiKey`, `Username`, `Source`, `Value`).

`coreintf` and `coreimpl` are the first Algites artifacts in this repository to publish both Java and Python implementations. Both technologies use the same business namespace `eu.algites.lib.security.credentials.core`.

The OS stores are currently Java-only. This is intentional: multi-TechnologyKind support is declared per artifact, not per repository, and additional Python store implementations can be added when a runtime use case requires them.
