#!/usr/bin/env bash
set -euo pipefail

# Standalone pub.lib.Security Maven + Python bootstrap. No Modustro Builder.
# Like the other Algites/Modustro bootstraps, one invocation builds, verifies and uploads
# unless MODUSTRO_BOOTSTRAP_PREPARE_ONLY=1 explicitly disables publication.
locRepo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
locHelper="$locRepo/devops/bootstrap/prepare.py"
locBuildRoot="$locRepo/build/run/security-bootstrap"
locJavaRepo="${MODUSTRO_SECURITY_BOOTSTRAP_CLOUDSMITH_REPO:-${MODUSTRO_SECURITY_BOOTSTRAP_JAVA_REPO:-algites/java-snapshots-pub}}"
locPythonRepo="${MODUSTRO_SECURITY_BOOTSTRAP_PYTHON_CLOUDSMITH_REPO:-${MODUSTRO_SECURITY_BOOTSTRAP_PYTHON_REPO:-algites/python-snapshots-pub}}"
locPython="${ALGITES_PYTHON_EXECUTABLE:-python3}"

locMode="${1:---upload}"
case "$locMode" in
    --plan-only|--prepare-only|--upload) ;;
    --help|-h)
        printf '%s\n' \
            'Usage: bash devops/bootstrap.sh [--plan-only|--prepare-only|--upload]' \
            'Default: build, verify and upload in one invocation.' \
            'Set MODUSTRO_BOOTSTRAP_PREPARE_ONLY=1 to build and verify without upload.'
        exit 0 ;;
    *) echo "Unknown bootstrap option: $locMode" >&2; exit 2 ;;
esac
if [[ $# -gt 1 ]]; then
    echo 'Only one optional bootstrap action is permitted' >&2
    exit 2
fi

locPrepareOnly="${MODUSTRO_BOOTSTRAP_PREPARE_ONLY:-0}"
case "$locPrepareOnly" in
    0|1) ;;
    *) echo "Invalid MODUSTRO_BOOTSTRAP_PREPARE_ONLY='$locPrepareOnly' (0|1)" >&2; exit 2 ;;
esac
if [[ "$locMode" == --prepare-only ]]; then
    locPrepareOnly=1
fi

# Dependency resolution follows the common bootstrap precedence policy.
# All This repository builds its own modules from checkout; source mode first
# prepares the required sibling-repository publications.
locDependencyMode="${MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE:-remote}"
case "$locDependencyMode" in
    remote|local|source) ;;
    *) echo "Invalid MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE='$locDependencyMode' (remote|local|source)" >&2; exit 2 ;;
esac
export MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE="$locDependencyMode"
locRefreshDependencies="${MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES:-}"
if [[ -z "$locRefreshDependencies" ]]; then
    if [[ "$locDependencyMode" == remote ]]; then
        locRefreshDependencies=1
    else
        locRefreshDependencies=0
    fi
fi
case "$locRefreshDependencies" in
    0|1) ;;
    *) echo "Invalid MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES='$locRefreshDependencies' (0|1)" >&2; exit 2 ;;
esac
export MODUSTRO_BOOTSTRAP_REFRESH_DEPENDENCIES="$locRefreshDependencies"
echo "Bootstrap dependency mode: $locDependencyMode; refresh published dependencies: $locRefreshDependencies"
if [[ "$locMode" == --plan-only ]]; then
    echo 'Bootstrap action: plan only (no build, no upload)'
elif [[ "$locPrepareOnly" == 1 ]]; then
    echo 'Bootstrap action: build and prepare only (no upload)'
else
    echo 'Bootstrap action: build, verify and upload to Cloudsmith'
fi

if ! command -v "$locPython" >/dev/null 2>&1; then
    echo "Missing Python interpreter: $locPython" >&2; exit 2
fi
if ! "$locPython" -c 'import yaml' >/dev/null 2>&1; then
    echo 'PyYAML is required to interpret modustro-artifact.yml (python -m pip install pyyaml)' >&2; exit 2
fi
locDetectedVersion="$("$locPython" - "$locRepo/modustro-source-repository.yml" <<'PY_VERSION'
import sys
import yaml
release = yaml.safe_load(open(sys.argv[1], encoding='utf-8'))['Version']
base = str(release['ReleaseLineVersion']) + '.' + str(release['Revision'])
kind = str(release.get('QualifierKind', 'release')).lower()
if kind not in ('snapshot', 'release'):
    raise SystemExit('Unsupported repository version qualifier: ' + kind)
print(base + ('-SNAPSHOT' if kind == 'snapshot' else ''))
PY_VERSION
)"
locVersion="${MODUSTRO_SECURITY_BOOTSTRAP_VERSION:-$locDetectedVersion}"
# The old 1.0 binary products are incompatible with the new generators.
# Never publish a 1.0 override from this 1.1 checkout.
if [[ "$locVersion" == 1.0 || "$locVersion" == 1.0-SNAPSHOT ]]; then
    echo 'Security bootstrap refuses 1.0: that line belongs to the former generator output.' >&2
    exit 2
fi
# Source mode explicitly prepares the prerequisite checkout, keeping the
# normal remote/local modes independent of the neighboring Git worktree.
if [[ "$locDependencyMode" == source && "$locMode" != --plan-only && "${MODUSTRO_BOOTSTRAP_SOURCE_PREPARED:-0}" != 1 ]]; then
    locSibling="${MODUSTRO_SECURITY_BOOTSTRAP_SOURCE_DEPENDENCY_DIR:-$(dirname -- "$locRepo")/pub.lib.General}"
    [[ -f "$locSibling/devtools/bootstrap.sh" ]] || {
        echo "Missing source prerequisite $locSibling (set MODUSTRO_SECURITY_BOOTSTRAP_SOURCE_DEPENDENCY_DIR)" >&2
        exit 2
    }
    echo "Preparing source prerequisite: $locSibling"
    MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE=source MODUSTRO_BOOTSTRAP_PREPARE_ONLY=1 \
        bash "$locSibling/devtools/bootstrap.sh" --prepare-only
fi
if [[ "$locMode" != --plan-only ]] && ! "$locPython" -c 'import setuptools, wheel' >/dev/null 2>&1; then
    echo 'Python build backends are required (python -m pip install setuptools wheel)' >&2; exit 2
fi

# Never mix artifacts from different source snapshots or versions.
mkdir -p "$locRepo/build/run"
if [[ -e "$locBuildRoot" && ! -d "$locBuildRoot" ]]; then
    echo "Build output path is not a directory: $locBuildRoot" >&2; exit 2
fi
rm -rf -- "$locBuildRoot"
mkdir -p "$locBuildRoot"
locArgs=(--repository "$locRepo" --output "$locBuildRoot" --version "$locVersion")
if [[ -n "${MODUSTRO_SECURITY_BOOTSTRAP_PYTHON_VERSION:-}" ]]; then
    locArgs+=(--python-version "$MODUSTRO_SECURITY_BOOTSTRAP_PYTHON_VERSION")
fi
export PYTHONDONTWRITEBYTECODE=1
export PYTEST_ADDOPTS="${PYTEST_ADDOPTS:+${PYTEST_ADDOPTS} }-p no:cacheprovider"
"$locPython" "$locHelper" plan "${locArgs[@]}"
if [[ "$locMode" == --plan-only ]]; then
    echo "Bootstrap plan generated in $locBuildRoot; no build and no upload performed."
    exit 0
fi

locGradle=(bash "$locRepo/gradlew")
if [[ -n "${MODUSTRO_GRADLE_EXECUTABLE:-}" ]]; then
    locGradle=("${MODUSTRO_GRADLE_EXECUTABLE}")
fi
locGradleArgs=(--no-daemon --project-dir "$locBuildRoot/gradle")
if [[ "$locRefreshDependencies" == 1 ]]; then
    locGradleArgs+=(--refresh-dependencies)
fi
# The standalone build publishes only to local staging; never to Maven Local or
# Cloudsmith as a Gradle side effect.
MODUSTRO_SECURITY_BOOTSTRAP_OUTPUT="$locBuildRoot" MODUSTRO_SECURITY_BOOTSTRAP_VERSION="$locVersion" \
    "${locGradle[@]}" "${locGradleArgs[@]}" test publishAllPublicationsToBootstrapRepository

"$locPython" "$locHelper" verify-maven "${locArgs[@]}"
"$locPython" "$locHelper" package-python "${locArgs[@]}" --python-executable "$locPython"
"$locPython" "$locHelper" test-python "${locArgs[@]}" --python-executable "$locPython"
# The descriptor-driven verification helpers have checked every selected
# publication. Count the resulting manifests instead of comparing to constants.
locJavaCount="$(wc -l < "$locBuildRoot/packages.tsv")"
locPythonCount="$(wc -l < "$locBuildRoot/python-packages.tsv")"


# Promote the entire verified staging publication set to Maven Local only after
# Python distributions are also ready. The upload reads Maven Local bytes.
locStagedManifest="$locBuildRoot/packages.tsv"
locStagedJson="$locBuildRoot/staged-publications.json"
"$locPython" "$locRepo/devops/bootstrap-maven-stage.py" collect-tsv --tsv "$locStagedManifest" --output "$locStagedJson"
"$locPython" "$locRepo/devops/bootstrap-maven-stage.py" promote --manifest "$locStagedJson" --output "$locBuildRoot/local-packages.tsv"
locVerifyGradle="${MODUSTRO_GRADLE_EXECUTABLE:-$locRepo/gradlew}"
"$locPython" "$locRepo/devops/bootstrap-maven-stage.py" verify-gradle --manifest "$locBuildRoot/local-packages.tsv" --gradle "$locVerifyGradle" --work "$locBuildRoot/local-gradle-verification"
# Publish verified Python distributions to the shared Modustro local Simple index.
"${ALGITES_PYTHON_EXECUTABLE:-python3}" "$locRepo/devops/modustro-local-python-repo.py" publish --manifest "$locBuildRoot/python-packages.tsv"
locCloudsmithManifest="$locBuildRoot/local-packages.tsv"

# Same manifest-output override as the other Modustro bootstraps; do not move
# the real staging area or rebuild for a later --upload invocation.
locManifestOutput="${MODUSTRO_BOOTSTRAP_OUTPUT_DIR:-$locBuildRoot}"
mkdir -p "$locManifestOutput"
if [[ "$locManifestOutput/packages.tsv" != "$locCloudsmithManifest" ]]; then
    cp "$locCloudsmithManifest" "$locManifestOutput/packages.tsv"
fi
if [[ "$locManifestOutput/python-packages.tsv" != "$locBuildRoot/python-packages.tsv" ]]; then
    cp "$locBuildRoot/python-packages.tsv" "$locManifestOutput/python-packages.tsv"
fi
if [[ "$locManifestOutput/python-release.txt" != "$locBuildRoot/python-release.txt" ]]; then
    cp "$locBuildRoot/python-release.txt" "$locManifestOutput/python-release.txt"
fi

echo "Prepared $locJavaCount Maven artifacts and $locPythonCount Python wheels with their sdists (discovered from product descriptors)."
echo "Java manifest: $locManifestOutput/packages.tsv"
echo "Python manifest: $locManifestOutput/python-packages.tsv"
if [[ "$locPrepareOnly" == 1 ]]; then
    echo 'Preparation complete. No Cloudsmith upload performed.'
    exit 0
fi

command -v algites-cloudsmith >/dev/null || { echo 'algites-cloudsmith is required for upload' >&2; exit 2; }
# Resolve the credential once for the whole upload batch.
algites-cloudsmith --session -- bash -c '
    set -euo pipefail
    locJavaRepo="$1"; locJavaManifest="$2"; locPythonRepo="$3"; locPythonManifest="$4"
    while IFS=$'"'"'\t'"'"' read -r locJar locPom locModule locSources; do
        [[ -s "$locJar" && -s "$locPom" && -s "$locModule" && -s "$locSources" ]] || {
            echo "Maven artifact is missing: $locJar" >&2; exit 1;
        }
        cloudsmith push maven "$locJavaRepo" "$locJar" \
            --pom-file "$locPom" --extra-files "$locModule" --sources-file "$locSources"
    done < "$locJavaManifest"
    while IFS=$'"'"'\t'"'"' read -r locWheel locSdist; do
        [[ -s "$locWheel" && -s "$locSdist" ]] || {
            echo "Python artifact is missing: $locWheel" >&2; exit 1;
        }
        cloudsmith push python "$locPythonRepo" "$locWheel"
        cloudsmith push python "$locPythonRepo" "$locSdist"
    done < "$locPythonManifest"
' _ "$locJavaRepo" "$locCloudsmithManifest" "$locPythonRepo" "$locBuildRoot/python-packages.tsv"

echo 'Cloudsmith upload finished.'
