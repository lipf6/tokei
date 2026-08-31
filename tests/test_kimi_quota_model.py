import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOKEI_SRC = ROOT / "Tokei" / "Sources" / "Tokei"


class KimiQuotaModelTests(unittest.TestCase):
    def test_kimi_stat_decodes_quota_and_legacy_payloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / "kimi-quota-model-check"
            subprocess.run(
                [
                    "swiftc",
                    "-parse-as-library",
                    "-module-name",
                    "KimiQuotaModelCheck",
                    str(TOKEI_SRC / "Model.swift"),
                    str(ROOT / "tests/swift/KimiQuotaModelCheck.swift"),
                    "-o",
                    str(binary),
                ],
                check=True,
                cwd=ROOT,
            )
            result = subprocess.run(
                [str(binary)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Kimi quota model checks passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
