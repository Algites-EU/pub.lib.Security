#!/usr/bin/env python3
"""Stage all Modustro native modules for a standalone pub.lib.General publication.

This helper does not invoke the Modustro Builder and never contacts Cloudsmith.
It reads the repository's native artifact descriptors and generates a separate
Gradle Maven publishing project and independent Python distribution workspaces.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import email
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import xml.etree.ElementTree as ET
import zipfile

import yaml

SOURCES = ('src/product/python', 'src/product/python.gen', 'src/product/config', 'src/product/resources',
           'src/product/xmldefs', 'src/product/yamldefs', 'src/product/jsondefs')
IGNORED = {'__pycache__', '.pytest_cache', 'build', 'node_modules', '.mypy_cache'}
JAVA_FIXED_VERSIONS = {
    'com.fasterxml.jackson.core:jackson-databind': '2.18.3',
    'com.fasterxml.jackson.dataformat:jackson-dataformat-yaml': '2.18.3',
    'com.fasterxml.jackson.core:jackson-annotations': '2.18.3',
}


def artifact_id(path: Path) -> str:
    return 'pub.lib.Security_' + '.'.join(path.parts)


def python_name(identifier: str) -> str:
    return 'eu-algites-' + re.sub('[^a-z0-9]+', '-', identifier.lower()).strip('-')


def python_version(java_version: str, override: str | None) -> str:
    if override:
        value = override
    elif java_version.endswith('-SNAPSHOT'):
        # Cloudsmith snapshots must not reuse the previous wheel's immutable name.
        value = java_version.removesuffix('-SNAPSHOT') + '.dev' + datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')
    else:
        value = java_version
    if not re.fullmatch(r'\d+(?:\.\d+)*(?:\.dev\d+)?', value):
        raise ValueError(f'Invalid Python package version {value!r}')
    return value


def read_yaml(path: Path) -> dict:
    with path.open(encoding='utf-8') as stream:
        return yaml.safe_load(stream) or {}


def inferred_group(repository: Path, module: Path) -> str:
    # Modustro artifact-set group IDs override the nearest enclosing ancestor.
    root = module
    while root != repository:
        descriptor = root / 'modustro-artifact-set.yml'
        if descriptor.is_file():
            group = read_yaml(descriptor).get('GroupId')
            if group:
                return str(group)
        root = root.parent
    return str(read_yaml(repository / 'modustro-source-repository.yml')['GroupId'])


def spec(requirement: dict | None, version: str) -> str:
    requirement = requirement or {}
    if 'Exact' in requirement:
        exact = str(requirement['Exact'])
        if exact.endswith('-SNAPSHOT'):
            prefix = exact.removesuffix('-SNAPSHOT')
            return f'>={prefix}.dev0,<{prefix}a0'
        return f'=={exact}'
    result = []
    for key, comparator in (('Minimum', '>='), ('Maximum', '<=')):
        if key not in requirement:
            continue
        raw = str(requirement[key])
        if raw.startswith(('>=', '<=', '==', '>', '<')):
            result.append(raw)
        else:
            op = '<' if key == 'Maximum' and requirement.get('MaximumStrict') else comparator
            result.append(op + raw)
    if result:
        return ','.join(result)
    return spec({'Exact': version}, version)


def java_version(name: str, requirement: dict | None) -> str:
    req = requirement or {}
    if 'Exact' in req:
        return str(req['Exact'])
    if name in JAVA_FIXED_VERSIONS:
        return JAVA_FIXED_VERSIONS[name]
    if 'Minimum' in req:
        return str(req['Minimum']).removeprefix('>=')
    raise ValueError(f'Cannot select a concrete Java dependency version for {name}: {req}')


def module_records(repository: Path, release: str, py_release: str) -> list[dict]:
    records = []
    for path in sorted(repository.rglob('modustro-artifact.yml')):
        # No build output or virtual environment may become a source artifact.
        relative = path.parent.relative_to(repository)
        if any(part in IGNORED or part.startswith('.') for part in relative.parts):
            continue
        doc = read_yaml(path)
        kinds = doc.get('Artifact', {}).get('TechnologyKinds', [])
        if 'java' not in kinds and 'python' not in kinds:
            continue
        identifier = artifact_id(relative)
        dependencies = []
        python_deps = []
        for dep_group in doc.get('Dependencies') or []:
            kind = dep_group.get('DependencyKind')
            for item in dep_group.get('Items') or []:
                usages = item.get('Usages') or []
                if not any(str(u).startswith('product_') for u in usages):
                    continue
                dep_id = str(item['ArtifactId'])
                if kind == 'modustro':
                    configuration = ('api' if 'product_api' in usages else
                                     'runtimeOnly' if 'product_runtime_only' in usages else
                                     'compileOnly' if 'product_compile_only_implementation' in usages else
                                     'implementation')
                    required = item.get('VersionRequirement')
                    # Products within this repository are staged as Gradle project dependencies.
                    # Cross-repository dependencies are published Maven/Python artifacts.
                    dependencies.append({'kind': 'modustro', 'artifactId': dep_id,
                                         'configuration': configuration, 'groupId': str(item.get('GroupId') or ''),
                                         'requirement': required})
                    if 'python' in kinds and ('product_api' in usages or 'product_implementation' in usages):
                        python_deps.append({'artifactId': dep_id, 'requirement': required})
                elif kind == 'java' and 'java' in kinds:
                    name = str(item['GroupId']) + ':' + dep_id
                    config = ('compileOnlyApi' if 'product_compile_only_api' in usages else
                              'compileOnly' if 'product_compile_only_implementation' in usages else
                              'api' if 'product_api' in usages else 'implementation')
                    dependencies.append({'kind': 'external', 'coordinate': name + ':' + java_version(name, item.get('VersionRequirement')),
                                         'configuration': config})
                elif kind == 'python' and 'python' in kinds:
                    python_deps.append(dep_id.replace('_', '-') + spec(item.get('VersionRequirement'), py_release))
        records.append({
            'path': relative.as_posix(), 'artifactId': identifier, 'groupId': inferred_group(repository, path.parent),
            'name': str(doc['Artifact'].get('Name', identifier)),
            'description': str(doc['Artifact'].get('Description', identifier)),
            'java': 'java' in kinds, 'python': 'python' in kinds,
            'dependencies': dependencies, 'pythonDependencies': python_deps,
        })
    if not records:
        raise ValueError('No native Java or Python products declared in modustro-artifact.yml')
    # Resolve internal modules from the current build. External modules keep the
    # exact or bounded version requirement declared in their product descriptor.
    lookup = {v['artifactId']: v for v in records}
    for record in records:
        for dep in record['dependencies']:
            if dep['kind'] != 'modustro':
                continue
            other = lookup.get(dep['artifactId'])
            if other is not None:
                if not other['java']:
                    raise ValueError(f'Internal non-Java dependency: {dep["artifactId"]}')
                if dep['groupId'] != other['groupId']:
                    raise ValueError(f'Group ID mismatch for {dep["artifactId"]}: '
                                     f'{dep["groupId"]} != {other["groupId"]}')
                dep['kind'] = 'project'
            else:
                if not dep['groupId']:
                    raise ValueError(f'Missing group ID for external dependency: {dep["artifactId"]}')
                # Only an explicit exact version or the accepted General 1.1 line
                # can be selected unambiguously for the current migration.
                requirement = dep['requirement'] or {}
                if 'Exact' in requirement:
                    selected = str(requirement['Exact'])
                elif dep['artifactId'].startswith('pub.lib.General_') and str(requirement.get('Minimum')) == '>1.0':
                    selected = '1.1-SNAPSHOT'
                else:
                    raise ValueError(f'Unpinned cross-repository Maven dependency of '
                                     f'{record["artifactId"]}: {dep}')
                dep['kind'] = 'external'
                dep['coordinate'] = dep['groupId'] + ':' + dep['artifactId'] + ':' + selected
        resolved_python = []
        for dep in record['pythonDependencies']:
            if isinstance(dep, str):
                resolved_python.append(dep)
                continue
            other = lookup.get(dep['artifactId'])
            if other is not None:
                if not other['python']:
                    raise ValueError(f'Internal dependency has no Python distribution: {dep["artifactId"]}')
                resolved_python.append(python_name(dep['artifactId']) + '==' + py_release)
            else:
                requirement = dep['requirement'] or {}
                # A published General snapshot has its own Python dev timestamp.
                # Selecting the 1.1 release line avoids erroneously pinning it to
                # the Security invocation's independent timestamp.
                exact = str(requirement.get('Exact', ''))
                if exact.endswith('-SNAPSHOT'):
                    prefix = exact.removesuffix('-SNAPSHOT')
                elif dep['artifactId'].startswith('pub.lib.General_') and str(requirement.get('Minimum')) == '>1.0':
                    prefix = '1.1'
                else:
                    raise ValueError(f'Cannot map external Python Modustro requirement: {dep}')
                resolved_python.append(python_name(dep['artifactId']) + f'>={prefix}.dev0,<{prefix}a0')
        record['pythonDependencies'] = list(dict.fromkeys(resolved_python))
    return records


def stage_gradle(repository: Path, work: Path, records: list[dict], version: str) -> None:
    stage = work / 'gradle'
    stage.mkdir(parents=True, exist_ok=True)
    java_modules = [r for r in records if r['java']]
    for number, record in enumerate(java_modules, 1):
        record['gradleProject'] = 'native%03d' % number
    ids = {r['artifactId']: r['gradleProject'] for r in java_modules}
    modules = [{'project': r['gradleProject'], 'groupId': r['groupId'], 'artifactId': r['artifactId'],
                'hasTests': (repository / r['path'] / 'src/develop/java').is_dir(),
                'dependencies': [{'kind': d['kind'], 'configuration': d['configuration'],
                                  'target': ids[d['artifactId']] if d['kind'] == 'project' else d['coordinate']}
                                 for d in r['dependencies']]}
               for r in java_modules]
    (stage / 'modules.json').write_text(json.dumps(modules, indent=2), encoding='utf-8')
    lines = ["rootProject.name = 'algites-pub-lib-security-native-bootstrap'"]
    for r in java_modules:
        # JSON encoded paths are valid Groovy double-quoted string literals.
        lines.append('include(' + json.dumps(':' + r['gradleProject']) + ')')
        lines.append('project(' + json.dumps(':' + r['gradleProject']) + ').projectDir = file(' +
                     json.dumps(str(repository / r['path'])) + ')')
    (stage / 'settings.gradle').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    build = '''import groovy.json.JsonSlurper\n\ndef manifest = new JsonSlurper().parse(new File(rootProject.projectDir, 'modules.json'))\ndef configByProject = manifest.collectEntries { [(it.project): it] }\ndef outputRoot = new File(System.getenv('MODUSTRO_SECURITY_BOOTSTRAP_OUTPUT') ?: rootProject.projectDir)\nlayout.buildDirectory.set(new File(outputRoot, 'gradle-build/root'))\nsubprojects { project ->\n    def config = configByProject[project.name]\n    if (config == null) throw new GradleException("Missing bootstrap configuration: ${project.name}")\n    project.layout.buildDirectory.set(new File(outputRoot, 'gradle-build/modules/' + project.name))\n    apply plugin: 'java-library'\n    apply plugin: 'maven-publish'\n    group = config.groupId\n    version = System.getenv('MODUSTRO_SECURITY_BOOTSTRAP_VERSION') ?: '1.1-SNAPSHOT'\n    repositories {\n        def bootstrapMode = System.getenv('MODUSTRO_BOOTSTRAP_DEPENDENCY_MODE') ?: 'remote'\n        if (bootstrapMode != 'remote') maven { name = 'modustro-local'; url = uri(System.getenv('MODUSTRO_LOCAL_MAVEN_REPOSITORY') ?: new File(System.getenv('MODUSTRO_HOME') ?: new File(System.getProperty('user.home'), '.modustro').path, 'artifact-repos/java/maven')) }\n        if (bootstrapMode == 'remote') maven {\n            url = uri('https://dl.cloudsmith.io/public/algites/java-snapshots-pub/maven/')\n            content { includeGroupByRegex('eu\\\\.algites\\\\..*') }\n        }\n        mavenCentral()\n    }\n    java { withSourcesJar() }\n    tasks.withType(JavaCompile).configureEach { options.release = 17 }\n    sourceSets {\n        main {\n            java.srcDirs = ['src/product/java', 'src/product/java.gen']\n            resources.srcDirs = ['src/product/config', 'src/product/resources',\n                                 'src/product/jsondefs', 'src/product/yamldefs', 'src/product/xmldefs']\n        }\n        test {\n            java.srcDirs = ['src/develop/java']\n            resources.srcDirs = ['src/develop/resources', 'src/develop/config']\n        }\n    }\n    tasks.withType(Test).configureEach { useTestNG() }\n    dependencies {\n        if (config.hasTests) testImplementation 'org.testng:testng:7.11.0'\n        config.dependencies.each { d ->\n            if (d.kind == 'project') {\n                add(d.configuration, rootProject.project(':' + d.target))\n            } else {\n                add(d.configuration, d.target)\n            }\n        }\n    }\n    publishing {\n        publications {\n            mavenJava(MavenPublication) {\n                from components.java\n                artifactId = config.artifactId\n            }\n        }\n        repositories {\n            maven { name = 'Bootstrap'; url = uri(new File(outputRoot, 'maven-repository')) }\n        }\n    }\n}\n'''
    (stage / 'build.gradle').write_text(build, encoding='utf-8')
    (stage / 'release-version.txt').write_text(version + '\n', encoding='utf-8')


def stage_one_python(repository: Path, work: Path, record: dict, release: str) -> Path:
    package = work / 'python-projects' / record['artifactId'].replace('.', '-')
    source_target = package / 'src'
    source_target.mkdir(parents=True, exist_ok=True)
    native_source = repository / record['path']
    for subdir in SOURCES:
        source = native_source / subdir
        if not source.is_dir():
            continue
        for file in sorted(source.rglob('*')):
            if not file.is_file() or file.suffix in ('.pyc', '.pyo') or any(p in IGNORED for p in file.parts):
                continue
            dst = source_target / file.relative_to(source)
            if dst.exists():
                if dst.read_bytes() != file.read_bytes():
                    raise ValueError(f'Conflicting resource {dst}')
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file, dst)
    if not list(source_target.rglob('*.py')):
        raise ValueError(f'Empty Python product for {record["artifactId"]}')
    license_file = repository / 'LICENSE'
    if license_file.is_file():
        shutil.copy2(license_file, package / 'LICENSE')
    toml = ('[build-system]\nrequires = ["setuptools>=69", "wheel"]\n'
            'build-backend = "setuptools.build_meta"\n\n'
            '[project]\nname = ' + json.dumps(python_name(record['artifactId'])) + '\n'
            'version = ' + json.dumps(release) + '\n'
            'description = ' + json.dumps(record['description']) + '\n'
            'requires-python = ">=3.11"\n'
            'dependencies = ' + json.dumps(record['pythonDependencies']) + '\n\n'
            '[tool.setuptools.packages.find]\nwhere = ["src"]\nnamespaces = true\n\n'
            '[tool.setuptools.package-data]\n"*" = ["*.settings", "*.yml", "*.yaml", "*.json", "*.xsd", "*.xml", "*.py"]\n')
    (package / 'pyproject.toml').write_text(toml, encoding='utf-8')
    (package / 'MANIFEST.in').write_text('recursive-include src *.py *.settings *.yml *.yaml *.json *.xsd *.xml\n', encoding='utf-8')
    return package


def package_python(repository: Path, work: Path, records: list[dict], release: str, python_command: str) -> None:
    dist = work / 'python-dist'
    dist.mkdir(parents=True, exist_ok=True)
    manifest = []
    for record in records:
        if not record['python']:
            continue
        package = stage_one_python(repository, work, record, release)
        # PEP 517 hooks produce both sdist and wheel without installing Modustro.
        # setuptools/wheel are the only build backend dependencies.
        command = ('import setuptools.build_meta as m; from pathlib import Path; '
                   'd = ' + repr(str(dist)) + '; '
                   'print("SDIST:", m.build_sdist(d)); print("WHEEL:", m.build_wheel(d))')
        output = subprocess.run([python_command, '-c', command], cwd=package,
                                text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if output.returncode:
            raise RuntimeError(f'Python build failed for {record["artifactId"]}:\n{output.stdout[-10000:]}')
        sdists = [dist / name.strip() for name in re.findall(r'^SDIST:\s*(.+)$', output.stdout, re.M)]
        wheels = [dist / name.strip() for name in re.findall(r'^WHEEL:\s*(.+)$', output.stdout, re.M)]
        if len(sdists) != 1 or len(wheels) != 1:
            raise RuntimeError(f'Unexpected Python build output for {record["artifactId"]}:\n{output.stdout[-3000:]}')
        sdist, wheel = sdists[0], wheels[0]
        verify_python_distribution(record, release, wheel, sdist)
        manifest.append((str(wheel), str(sdist)))
        print(f'Python package verified: {record["artifactId"]}', flush=True)
    (work / 'python-packages.tsv').write_text(''.join('\t'.join(row)+'\n' for row in manifest), encoding='utf-8')


def verify_python_distribution(record: dict, release: str, wheel: Path, sdist: Path) -> None:
    if not wheel.is_file() or not sdist.is_file():
        raise FileNotFoundError(f'Missing distribution: {wheel}, {sdist}')
    with zipfile.ZipFile(wheel) as archive:
        paths = archive.namelist()
        meta_files = [name for name in paths if name.endswith('.dist-info/METADATA')]
        if len(meta_files) != 1 or not any(p.endswith('.py') and p.startswith('eu/algites/') for p in paths):
            raise ValueError(f'Incomplete wheel: {wheel}')
        metadata = email.message_from_bytes(archive.read(meta_files[0]))
        norm = lambda name: re.sub('[-_.]+', '-', name).lower()
        if norm(metadata['Name']) != norm(python_name(record['artifactId'])) or metadata['Version'] != release:
            raise ValueError(f'Incorrect Python distribution identity/version in {wheel}')
    with tarfile.open(sdist, 'r:gz') as archive:
        if not any(path.endswith('/PKG-INFO') for path in archive.getnames()):
            raise ValueError(f'Source distribution missing PKG-INFO: {sdist}')


def maven_publication_files(directory: Path, artifact_id: str, release: str) -> tuple[Path, Path, Path, Path]:
    """Locate Gradle-published artifacts, including uniquely timestamped Maven snapshots.

    Maven repository publications of a *-SNAPSHOT version usually write timestamped
    files inside a directory still named *-SNAPSHOT. Their actual file versions are
    recorded per extension/classifier in that directory's maven-metadata.xml.
    Maven-local or older publications can instead use literal *-SNAPSHOT filenames.
    """
    def paths_for(version: str) -> tuple[Path, Path, Path, Path]:
        stem = artifact_id + '-' + version
        return (directory / (stem + '.jar'), directory / (stem + '.pom'),
                directory / (stem + '.module'), directory / (stem + '-sources.jar'))

    ordinary = paths_for(release)
    if all(path.is_file() and path.stat().st_size > 0 for path in ordinary):
        return ordinary

    metadata_path = directory / 'maven-metadata.xml'
    if not release.endswith('-SNAPSHOT') or not metadata_path.is_file():
        existing = sorted(path.name for path in directory.iterdir()) if directory.is_dir() else []
        raise FileNotFoundError(
            f'Incomplete Maven publication of {artifact_id} at {directory}; '
            f'expected {tuple(path.name for path in ordinary)}; existing files: {existing}'
        )

    metadata = ET.parse(metadata_path).getroot()
    coordinates = {
        child.tag.rsplit('}', 1)[-1]: child.text
        for child in metadata
        if child.tag.rsplit('}', 1)[-1] in ('groupId', 'artifactId', 'version')
    }
    expected_coordinates = {'artifactId': artifact_id, 'version': release}
    if any(coordinates.get(key) != value for key, value in expected_coordinates.items()):
        raise ValueError(f'Incorrect Maven snapshot metadata identity at {metadata_path}: {coordinates}')

    def child_named(element: ET.Element, name: str) -> ET.Element | None:
        return next((child for child in element if child.tag.rsplit('}', 1)[-1] == name), None)

    def child_text(element: ET.Element, name: str) -> str | None:
        child = child_named(element, name)
        return child.text if child is not None else None

    versioning = child_named(metadata, 'versioning')
    snapshot_versions = child_named(versioning, 'snapshotVersions') if versioning is not None else None
    resolved: dict[tuple[str, str], str] = {}
    if snapshot_versions is not None:
        for item in snapshot_versions:
            if item.tag.rsplit('}', 1)[-1] != 'snapshotVersion':
                continue
            extension = child_text(item, 'extension')
            classifier = child_text(item, 'classifier') or ''
            value = child_text(item, 'value')
            if extension and value:
                key = (extension, classifier)
                if key in resolved and resolved[key] != value:
                    raise ValueError(f'Ambiguous Maven snapshot metadata for {key} at {metadata_path}')
                resolved[key] = value

    # The snapshotVersion list is canonical, but some repository metadata
    # versions list only the timestamp and build number. Support both formats.
    snapshot = child_named(versioning, 'snapshot') if versioning is not None else None
    timestamp = child_text(snapshot, 'timestamp') if snapshot is not None else None
    build_number = child_text(snapshot, 'buildNumber') if snapshot is not None else None
    fallback = (release.removesuffix('-SNAPSHOT') + '-' + timestamp + '-' + build_number
                if timestamp and build_number else None)
    versions = [resolved.get(key, fallback) for key in
                (('jar', ''), ('pom', ''), ('module', ''), ('jar', 'sources'))]
    if any(not version for version in versions):
        raise ValueError(f'Incomplete Maven snapshot version metadata at {metadata_path}: {resolved}')
    if len(set(versions)) != 1:
        raise ValueError(f'Inconsistent Maven snapshot file versions at {metadata_path}: {versions}')
    actual = paths_for(versions[0])
    if not all(path.is_file() and path.stat().st_size > 0 for path in actual):
        existing = sorted(path.name for path in directory.iterdir())
        raise FileNotFoundError(f'Incomplete timestamped Maven publication of {artifact_id} at {directory}; '
                                f'expected {[path.name for path in actual]}; existing files: {existing}')
    return actual


def verify_maven(work: Path, records: list[dict], release: str) -> None:
    maven = work / 'maven-repository'
    rows = []
    for record in records:
        if not record['java']:
            continue
        directory = maven / record['groupId'].replace('.', '/') / record['artifactId'] / release
        jar, pom, module, sources = maven_publication_files(directory, record['artifactId'], release)
        root = ET.parse(pom).getroot()
        names = {node.tag.rsplit('}', 1)[-1]: node.text for node in root
                 if node.tag.rsplit('}', 1)[-1] in ('groupId', 'artifactId', 'version')}
        if any(names.get(k) != value for k, value in [('groupId', record['groupId']),
                                                       ('artifactId', record['artifactId']),
                                                       ('version', release)]):
            raise ValueError(f'Incorrect Maven POM coordinates for {record["artifactId"]}: {names}')
        with zipfile.ZipFile(jar) as archive:
            if not any(n.endswith('.class') for n in archive.namelist()):
                if not any(n.endswith(('.yml', '.yaml', '.gradle.kts', '.xml', '.xsd')) for n in archive.namelist()):
                    raise ValueError(f'JAR has neither compiled classes nor profile resources: {jar}')
        rows.append((str(jar), str(pom), str(module), str(sources)))
    (work / 'packages.tsv').write_text(''.join('\t'.join(row) + '\n' for row in rows), encoding='utf-8')
    print(f'Maven publications verified: {len(rows)}', flush=True)


def test_python(repository: Path, records: list[dict], python_command: str) -> None:
    """Test declared Python products without attempting to test disabled technologies."""
    import os
    passed = 0
    for record in records:
        if not record['python']:
            continue
        module = repository / record['path']
        root = module / 'src/develop/python'
        if not root.is_dir():
            continue
        test_files = [file for file in root.rglob('test_*.py') if file.is_file()]
        if not test_files:
            continue
        search_path = [str(module / src) for src in ('src/product/python', 'src/product/python.gen')
                       if (module / src).is_dir()]
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join(search_path + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else []))
        env['PYTHONDONTWRITEBYTECODE'] = '1'
        env['PYTEST_ADDOPTS'] = (env.get('PYTEST_ADDOPTS', '') + ' -p no:cacheprovider').strip()
        proc = subprocess.run([python_command, '-m', 'pytest', '-q', str(root)],
                              env=env, cwd=repository, check=False)
        if proc.returncode:
            raise RuntimeError(f'Python development tests failed: {record["artifactId"]}')
        passed += 1
    print(f'Python tested artifact groups: {passed}', flush=True)


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('plan','package-python','verify-maven','test-python'))
    parser.add_argument('--repository',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--version',required=True)
    parser.add_argument('--python-version')
    parser.add_argument('--python-executable',default=sys.executable)
    args=parser.parse_args()
    repository=args.repository.resolve(strict=True)
    output=args.output.absolute()
    output.mkdir(parents=True,exist_ok=True)
    # Preserve one immutable version for all Python wheels during this invocation.
    version_file=output / 'python-release.txt'
    if args.action == 'plan':
        release=python_version(args.version,args.python_version)
        version_file.write_text(release+'\n',encoding='utf-8')
    else:
        release=version_file.read_text(encoding='utf-8').strip()
        if args.python_version and args.python_version != release:
            raise ValueError('Python version changed during bootstrap')
    records=module_records(repository,args.version,release)
    (output/'artifacts.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
    if args.action == 'plan':
        stage_gradle(repository,output,records,args.version)
        print(f'Bootstrap plan: {sum(r["java"] for r in records)} Java Maven and '
              f'{sum(r["python"] for r in records)} Python distributions; release {args.version} / {release}',flush=True)
    elif args.action=='package-python':
        package_python(repository,output,records,release,args.python_executable)
    elif args.action=='verify-maven':
        verify_maven(output,records,args.version)
    elif args.action=='test-python':
        test_python(repository,records,args.python_executable)

if __name__ == '__main__':
    main()
