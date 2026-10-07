# Algites Security Libraries

Reusable, technology-neutral security libraries for the Algites ecosystem.

> Public Algites project.

---

## 📦 Overview

This repository contains reusable **security library artifacts** shared by Algites build tooling, frameworks, services, applications, and other products.

The repository is technology-neutral at repository level. Individual artifacts declare the TechnologyKinds they provide, and one artifact may provide multiple technology implementations while sharing the same business model and namespace.

Security integrations that are specific to a tool or build environment belong in `pub.tool.Security`; AAC adapters belong in the AAC framework. This repository owns the reusable security contracts and implementations underneath those integrations.

---

## 🧱 Modules & Structure

The repository is organized into security domains. Each domain may contain several independently distributed artifacts.

```text
.
├── README.md
└── credentials/
    ├── README.md
    ├── modustro-artifact-set.yml
    ├── coreintf/
    │   └── src/
    │       ├── product/
    │       │   ├── java/
    │       │   ├── python/
    │       │   └── jsondefs/
    │       └── develop/
    │           ├── java/
    │           └── python/
    ├── coreimpl/
    │   └── src/
    │       ├── product/
    │       │   ├── java/
    │       │   └── python/
    │       └── develop/
    │           ├── java/
    │           └── python/
    ├── winstore/
    ├── macstore/
    └── secretservicestore/
```

`coreintf` and `coreimpl` are separate distribution artifacts, but this separation is intentionally not exposed in the business namespace. Their Java and Python implementations share:

```text
eu.algites.lib.security.credentials.core
```

Technology-neutral definitions use semantic SourceKinds such as `jsondefs`, `yamldefs`, `xmldefs`, or `config`; a generic `schema` SourceKind or `schema` package layer is not used.

---

## 🚀 Build

The supported repository build entry point is the **Algites Gradle lifecycle**:

```bash
./gradlew algitesBuild
```

Gradle coordinates all TechnologyKinds, shared definitions, validation, testing, packaging, and publication rules. Direct technology-specific repository builds are not a supported build mode.

---

## 🔄 Continuous Integration (Algites CI)

This repository uses the **Algites unified GitHub Actions CI pipeline**; build, test, and publish rules are centralized.

For exact usage and naming of branches, see:
https://github.com/Algites-EU/pub.gov.Algites.specs/blob/main/ci/Algites-Github-CI-Policy.md

---

## 📥 Usage

Consumers should depend only on the security domain and artifacts required by their application. Tool-specific adapters are provided separately by `pub.tool.Security`.

### Credentials

The `credentials` module set provides the common credential model, resolution implementation, and optional operating-system secure-store backends.

- `credentials/coreintf` — Java + Python credential profile, value, provider, and store contracts together with shared JSON definitions.
- `credentials/coreimpl` — Java + Python credential document, environment, resolver, codec, and secure-store selection implementation.
- `credentials/winstore` — Java Windows Credential Manager backend.
- `credentials/macstore` — Java macOS Keychain backend.
- `credentials/secretservicestore` — Java Freedesktop Secret Service backend.

The core artifacts deliberately share the same business namespace even though they are distributed separately. Python uses PEP 420 namespace packages, so independently distributed artifacts must not collide on final module or resource paths.

The canonical credential JSON definitions are located under:

```text
credentials/coreintf/src/product/jsondefs/eu/algites/lib/security/credentials/core/
```

Build tools, CLI tools, AAC applications, catalog services, and other products may therefore use the same credential model without making the credential subsystem build-specific.

---

## 🛠 Development

Typical workflow:

```bash
git clone https://github.com/Algites-EU/pub.lib.Security.git
cd pub.lib.Security
./gradlew algitesBuild
```

Follow the Algites artifact, source-layout, technology, and naming conventions defined by `pub.gov.Algites`. In particular, distribution boundaries such as `coreintf` and `coreimpl` must not be copied mechanically into business package namespaces.

---

## 🤝 Contributing

Contributions are welcome.

Please:
- open an issue to discuss changes,
- follow the Algites coding, artifact, source-layout, and naming standards,
- keep reusable security functionality independent of particular tools and frameworks where possible,
- ensure CI passes before submitting a PR.

---

## 📜 License

This project is licensed under the terms of the license specified in the `LICENSE` file. Individual governed content may additionally reference applicable licenses through the repository licensing metadata.

---

## 🌍 About Algites

Algites develops platforms, tools, frameworks, libraries, and applications based on strong governance, modeling, and automation principles.

See:
- https://github.com/Algites-EU/pub.gov.Algites.specs

---

**© Algites**
