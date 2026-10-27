"""Offline regression tests for the Security bootstrap publication planner."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve()
REPOSITORY = HERE.parents[2]
SPEC = importlib.util.spec_from_file_location("security_bootstrap_prepare", HERE.parent / "prepare.py")
prepare = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(prepare)


class SecurityBootstrapTests(unittest.TestCase):
    def test_repository_release(self):
        version = prepare.read_yaml(REPOSITORY / "modustro-source-repository.yml")["Version"]
        self.assertEqual((str(version["ReleaseLineVersion"]), int(version["Revision"])), ("1", 1))

    def test_descriptor_driven_publications(self):
        records = prepare.module_records(REPOSITORY, "1.1-SNAPSHOT", "1.1.dev20261027000000000000")
        descriptors = list(REPOSITORY.rglob("modustro-artifact.yml"))
        self.assertEqual(len(records), len(descriptors))
        self.assertEqual(sum(r["java"] for r in records), EXPECTED_JAVA)
        self.assertEqual(sum(r["python"] for r in records), EXPECTED_PYTHON)
        self.assertTrue(all(r["artifactId"].startswith(REPOSITORY.name + "_") for r in records))
        for record in records:
            for dep in record["dependencies"]:
                if dep["kind"] == "external" and dep["coordinate"].startswith("eu.algites."):
                    self.assertNotIn(":1.0-SNAPSHOT", dep["coordinate"])

    def test_staged_gradle_plan_includes_real_java_tests(self):
        records = prepare.module_records(REPOSITORY, "1.1-SNAPSHOT", "1.1.dev20261027000000000000")
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            prepare.stage_gradle(REPOSITORY, work, records, "1.1-SNAPSHOT")
            manifest = json.loads((work / "gradle/modules.json").read_text())
            self.assertEqual(len(manifest), EXPECTED_JAVA)
            text = (work / "gradle/build.gradle").read_text()
            self.assertIn("src/develop/java", text)
            self.assertIn("useTestNG()", text)
            self.assertIn("maven-publish", text)

    def test_dynamic_discovery_not_hard_coded(self):
        records = prepare.module_records(REPOSITORY, "1.1-SNAPSHOT", "1.1.dev20261027000000000000")
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            # The packager stages exactly the selected products, irrespective of
            # repository totals. A hard-coded expected number would reject this.
            selection = [r for r in records if r["artifactId"].endswith("credentials.core.intf")]
            self.assertEqual(len(selection), 1)
            prepare.stage_gradle(REPOSITORY, work, selection, "1.1-SNAPSHOT")
            manifest = json.loads((work / "gradle/modules.json").read_text())
            self.assertEqual(len(manifest), 1)

    def test_help_and_plan_only(self):
        command = ["bash", str(REPOSITORY / "devops/bootstrap.sh"), "--help"]
        process = subprocess.run(command, text=True, capture_output=True)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertIn("--prepare-only", process.stdout)


EXPECTED_JAVA = 5
EXPECTED_PYTHON = 1
if __name__ == "__main__":
    unittest.main()
