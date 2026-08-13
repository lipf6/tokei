import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_codex_limits import USAGE, _REAL_LEDGER_RECONCILE, _REAL_LEDGER_TOUCH


class LedgerReconcileTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old_file = USAGE._LEDGER_FILE
        USAGE._LEDGER_FILE = str(Path(self.temp.name) / "ledger.json")
        USAGE.ledger_reconcile = _REAL_LEDGER_RECONCILE
        USAGE.ledger_touch = _REAL_LEDGER_TOUCH

    def tearDown(self):
        USAGE._LEDGER_FILE = self.old_file
        USAGE.ledger_reconcile = lambda tool, live_days: live_days
        USAGE.ledger_touch = lambda tool: None
        self.temp.cleanup()

    def test_live_higher_updates_high_water(self):
        first = USAGE.ledger_reconcile("claude", {
            "2026-08-01": {"in": 100, "out": 10, "cost": 1.0},
        })
        self.assertEqual(first["2026-08-01"]["in"], 100)

        second = USAGE.ledger_reconcile("claude", {
            "2026-08-01": {"in": 180, "out": 20, "cost": 1.8},
        })
        self.assertEqual(second["2026-08-01"]["in"], 180)
        stored = json.loads(Path(USAGE._LEDGER_FILE).read_text(encoding="utf-8"))
        self.assertEqual(stored["tools"]["claude"]["2026-08-01"]["in"], 180)

    def test_live_lower_keeps_ledger_and_missing_days_are_restored(self):
        USAGE.ledger_reconcile("codex", {
            "2026-08-01": {"in": 200, "cached": 50, "out": 20, "reason": 5, "cost": 2.0},
            "2026-08-02": {"in": 80, "cached": 10, "out": 8, "reason": 1, "cost": 0.8},
        })

        merged = USAGE.ledger_reconcile("codex", {
            "2026-08-01": {"in": 30, "cached": 5, "out": 2, "reason": 0, "cost": 0.3},
        })
        self.assertEqual(merged["2026-08-01"]["in"], 200)
        self.assertEqual(merged["2026-08-02"]["in"], 80)

    def test_sets_are_not_persisted(self):
        USAGE.ledger_reconcile("gemini", {
            "2026-08-03": {"in": 10, "out": 2, "sessions": {"a", "b"}},
        })
        stored = json.loads(Path(USAGE._LEDGER_FILE).read_text(encoding="utf-8"))
        self.assertNotIn("sessions", stored["tools"]["gemini"]["2026-08-03"])

    def test_kimi_scan_falls_back_to_ledger_after_logs_disappear(self):
        now = "2026-08-10"
        live_days = {
            now: {
                "in": 140, "out": 28, "cr": 62, "cw": 10, "reason": 0,
                "cost": 0.0, "models": {"kimi-code/k3": {
                    "in": 140, "out": 28, "cr": 62, "cw": 10, "reason": 0, "cost": 0.0,
                }},
                "hours": [0] * 24,
            }
        }
        USAGE.ledger_reconcile("kimi", live_days)

        empty = USAGE.ledger_reconcile("kimi", {})
        self.assertEqual(empty[now]["in"], 140)
        self.assertEqual(empty[now]["out"], 28)
        self.assertEqual(empty[now]["cr"], 62)
        self.assertEqual(empty[now]["cw"], 10)

    def test_heal_from_sync_snapshot(self):
        ledger = {
            "v": 1,
            "tools": {"claude": {"2026-07-01": {"in": 999, "out": 1, "cost": 9.0}}},
        }
        Path(USAGE._LEDGER_FILE).write_text("{broken", encoding="utf-8")
        snapshot = Path(self.temp.name) / "macbook.json"
        snapshot.write_text(json.dumps({"_ledger": ledger}), encoding="utf-8")

        with mock.patch.object(USAGE, "_load_tokei_config", return_value={
            "device_id": "macbook",
            "sync_dir": self.temp.name,
        }):
            restored = USAGE._load_ledger()
        self.assertEqual(restored["tools"]["claude"]["2026-07-01"]["in"], 999)
        healed = json.loads(Path(USAGE._LEDGER_FILE).read_text(encoding="utf-8"))
        self.assertEqual(healed["tools"]["claude"]["2026-07-01"]["in"], 999)


if __name__ == "__main__":
    unittest.main()
