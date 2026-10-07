#!/usr/bin/env bash
# Run this script in the repository checkout BEFORE synchronizing the migrated ZIP.
set -euo pipefail
locRepoRoot="$(git rev-parse --show-toplevel)"
cd -- "$locRepoRoot"
locExpectedRepo=pub.lib.Security
if [[ ! -f algites-source-repository.yml && ! -f modustro-source-repository.yml ]]; then
    printf '%s\n' "No repository descriptor found in $locRepoRoot" >&2
    exit 1
fi
locDescriptor=algites-source-repository.yml
[[ -f "$locDescriptor" ]] || locDescriptor=modustro-source-repository.yml
if ! grep -Eq "^[[:space:]]*Id:[[:space:]]*['\"]?${locExpectedRepo//./\.}['\"]?[[:space:]]*$" "$locDescriptor"; then
    printf '%s\n' "This script is for $locExpectedRepo; the repository identity does not match." >&2
    exit 1
fi
locOld=(
    algites-source-repository.yml
    credentials/algites-artifact-set.yml
    credentials/coreimpl/algites-artifact.yml
    credentials/coreintf/algites-artifact.yml
    credentials/macstore/algites-artifact.yml
    credentials/secretservicestore/algites-artifact.yml
    credentials/winstore/algites-artifact.yml
)
locNew=(
    modustro-source-repository.yml
    credentials/modustro-artifact-set.yml
    credentials/coreimpl/modustro-artifact.yml
    credentials/coreintf/modustro-artifact.yml
    credentials/macstore/modustro-artifact.yml
    credentials/secretservicestore/modustro-artifact.yml
    credentials/winstore/modustro-artifact.yml
)
for locIndex in "${!locOld[@]}"; do
    locSource="${locOld[$locIndex]}"
    locTarget="${locNew[$locIndex]}"
    if [[ -e "$locSource" ]]; then
        if [[ -e "$locTarget" ]]; then
            printf '%s\n' "Both paths exist: $locSource and $locTarget; resolve the collision first." >&2
            exit 1
        fi
        git ls-files --error-unmatch -- "$locSource" >/dev/null
    elif [[ ! -f "$locTarget" ]]; then
        printf '%s\n' "Neither path exists: $locSource or $locTarget" >&2
        exit 1
    else
        git ls-files --error-unmatch -- "$locTarget" >/dev/null
    fi
done
for locIndex in "${!locOld[@]}"; do
    locSource="${locOld[$locIndex]}"
    locTarget="${locNew[$locIndex]}"
    if [[ -e "$locSource" ]]; then
        git mv -- "$locSource" "$locTarget"
    fi
done
printf '%s\n' "Descriptor moves completed for $locExpectedRepo. Synchronize the migrated repository files next."
