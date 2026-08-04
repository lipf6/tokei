import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from test_codex_limits import USAGE


MODEL = "kimi-code/k3"


def usage_record(timestamp, inp=0, out=0, cache_read=0, cache_creation=0):
    return {
        "type": "usage.record",
        "time": int(timestamp.timestamp() * 1000),
        "model": MODEL,
        "usageScope": "turn",
        "usage": {
            "inputOther": inp,
            "output": out,
            "inputCacheRead": cache_read,
            "inputCacheCreation": cache_creation,
        },
    }


class KimiScanTests(unittest.TestCase):
    def scan(self, root, agent_records, trailing_text="", cache=None):
        root = Path(root)
        session_dir = root / "sessions" / "wd_test" / "session_123"
        project = root / "project"
        rows = [{
            "sessionDir": str(session_dir),
            "sessionId": "session_123",
            "workDir": str(project),
        }]
        (root / "session_index.jsonl").write_text(
            "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        for agent, records in agent_records.items():
            wire = session_dir / "agents" / agent / "wire.jsonl"
            wire.parent.mkdir(parents=True, exist_ok=True)
            wire.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n" + trailing_text,
                encoding="utf-8",
            )

        scan_cache = cache if cache is not None else {"v": USAGE._SCAN_CACHE_VERSION}
        with mock.patch.object(USAGE, "KIMI_CODE_HOME", str(root)), \
                mock.patch.object(USAGE, "KIMI_SESSION_INDEX", str(root / "session_index.jsonl")):
            result = USAGE.scan_kimi(USAGE.range_bounds(), scan_cache)
        return result, scan_cache, project

    def test_scans_main_and_subagents_without_double_counting_session(self):
        now = datetime.now().astimezone().replace(hour=10, minute=0, second=0, microsecond=0)
        main = usage_record(now, inp=100, out=20, cache_read=50, cache_creation=10)
        nested = {
            "type": "context.append_loop_event",
            "event": {"usage": main["usage"]},
        }
        subagent = usage_record(now.replace(hour=11), inp=40, out=8, cache_read=12)

        with tempfile.TemporaryDirectory() as tmp:
            result, cache, project = self.scan(
                tmp, {"main": [main, nested], "agent-1": [subagent]}, trailing_text="{partial")

        usage = result["ranges"]["all"]
        self.assertEqual(usage["in"], 140)
        self.assertEqual(usage["out"], 28)
        self.assertEqual(usage["cr"], 62)
        self.assertEqual(usage["cw"], 10)
        self.assertEqual(USAGE.token_total(usage), 240)
        self.assertEqual(len(usage["sessions"]), 1)
        self.assertEqual(usage["cost"], 0)
        self.assertEqual(usage["models"][MODEL]["in"], 140)
        self.assertEqual({entry["proj"] for entry in cache["kimi"].values()}, {str(project)})

    def test_cache_drops_removed_wire_file(self):
        now = datetime.now().astimezone()
        stale = {
            "v": USAGE._SCAN_CACHE_VERSION,
            "kimi": {"/missing/wire.jsonl": {"sig": "old", "days": {}}},
        }
        with tempfile.TemporaryDirectory() as tmp:
            result, cache, _ = self.scan(tmp, {"main": [usage_record(now, inp=10)]}, cache=stale)

        self.assertNotIn("/missing/wire.jsonl", cache["kimi"])
        self.assertEqual(result["ranges"]["all"]["in"], 10)
        self.assertTrue(cache["_dirty"])

    def test_daily_wrapped_and_projects_include_kimi(self):
        now = datetime.now().astimezone().replace(hour=7, minute=0, second=0, microsecond=0)
        with tempfile.TemporaryDirectory() as tmp:
            result, cache, project = self.scan(
                tmp, {"main": [usage_record(now, inp=20, out=5, cache_read=10)]})
            self.assertEqual(USAGE.token_total(result["ranges"]["all"]), 35)

            daily = USAGE.build_daily_costs("30d", refresh=False, _cache=cache)
            wrapped = USAGE.build_wrapped("30d", refresh=False, _cache=cache)

            cache_path = Path(tmp) / "scan-cache.json"
            cache_path.write_text(json.dumps(cache), encoding="utf-8")
            output = io.StringIO()
            with mock.patch.object(USAGE, "compute", return_value={}), \
                    mock.patch.object(USAGE, "_SCAN_CACHE_FILE", str(cache_path)), \
                    contextlib.redirect_stdout(output):
                USAGE.projects()
            projects = json.loads(output.getvalue())

        self.assertEqual(daily["daily"][0]["tokens"], 35)
        self.assertEqual(daily["models"][0]["tool"], "kimi")
        self.assertEqual(daily["models"][0]["cost"], 0)
        self.assertEqual(wrapped["total_tokens"], 35)
        self.assertEqual(wrapped["hours"][7], 35)
        self.assertEqual(wrapped["projects"][0]["name"], project.name)
        self.assertEqual(projects[0]["path"], str(project))
        self.assertEqual(projects[0]["sessions"], 1)
        self.assertEqual(projects[0]["tools"], ["kimi"])


if __name__ == "__main__":
    unittest.main()
