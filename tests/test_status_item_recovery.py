import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class StatusItemRecoveryTests(unittest.TestCase):
    def test_recovery_replaces_the_item_and_defers_while_panel_is_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "StatusItemRecoveryCheck"
            subprocess.run([
                "swiftc", "-parse-as-library", "-module-name", "StatusItemRecoveryCheck",
                str(ROOT / "Tokei/Sources/Tokei/StatusItemController.swift"),
                str(ROOT / "tests/swift/StatusItemRecoveryCheck.swift"),
                "-o", str(binary),
            ], check=True, cwd=ROOT)
            result = subprocess.run([str(binary)], check=True, capture_output=True,
                                    text=True, timeout=30)
            self.assertIn("status item recovery checks passed", result.stdout)
