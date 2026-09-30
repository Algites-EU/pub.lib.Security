#!/usr/bin/env bash
set -euo pipefail

# Run from the repository root before synchronizing the migrated tree.
git mv -- 'credentials/coreintf/src/product/yamldefs/eu/algites/lib/security/credentials/core/credentials_1.schema.json' 'credentials/coreintf/src/product/yamldefs/eu/algites/lib/security/credentials/core/credentials_1.yamldef.schema.json'
git mv -- 'credentials/coreintf/src/product/yamldefs/eu/algites/lib/security/credentials/core/credential-profiles_1.schema.json' 'credentials/coreintf/src/product/yamldefs/eu/algites/lib/security/credentials/core/credential-profiles_1.yamldef.schema.json'
git mv -- 'credentials/coreintf/src/product/jsondefs/eu/algites/lib/security/credentials/core/credentials_1.json' 'credentials/coreintf/src/product/jsondefs/eu/algites/lib/security/credentials/core/credentials_1.jsondef.schema.json'
git mv -- 'credentials/coreintf/src/product/jsondefs/eu/algites/lib/security/credentials/core/credential-profiles_1.json' 'credentials/coreintf/src/product/jsondefs/eu/algites/lib/security/credentials/core/credential-profiles_1.jsondef.schema.json'
