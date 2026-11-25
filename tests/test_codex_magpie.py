import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from test_codex_limits import USAGE


class CodexMagpieTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.rollout = self.root / "rollout-session.jsonl"
        self.gateway = self.root / "usage.jsonl"
        self.cache = {"v": USAGE._SCAN_CACHE_VERSION}
        self.records = [
            self.record("session_meta", {"id": "session"}),
            self.record("turn_context", {"model": "group/smart-split"}),
        ]
        for attribute, value in (
            ("CODEX_DIR", str(self.root)),
            ("CODEX_ARCHIVED_DIR", str(self.root / "archive")),
            ("_SCAN_CACHE_FILE", str(self.root / "scan-cache.json")),
            ("_LEDGER_FILE", str(self.root / "ledger.json")),
            ("_MAGPIE_USAGE_FILE", str(self.gateway)),
        ):
            patcher = mock.patch.object(USAGE, attribute, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def record(self, kind, payload):
        return {"timestamp": "2026-11-07T01:00:00Z", "type": kind, "payload": payload}

    def response(self, response_id, total=100):
        usage = {"input_tokens": 100, "cached_input_tokens": 80,
                 "output_tokens": 10, "reasoning_output_tokens": 2}
        cumulative = {key: value * (total // 100) for key, value in usage.items()}
        return self.record("token_usage_record", {
            "thread_id": "session", "response_id": response_id,
            "usage": usage, "thread_token_usage": cumulative,
        })

    def mirror(self, response):
        payload = response["payload"]
        return self.record("event_msg", {"type": "token_count", "info": {
            "last_token_usage": payload["usage"],
            "total_token_usage": payload["thread_token_usage"],
        }})

    def write_rollout(self):
        self.rollout.write_text("".join(json.dumps(row) + "\n" for row in self.records))

    def gateway_record(self, response_id, model="gpt-6-astra", session="session"):
        return {"agent": "codex", "req": "group/smart-split",
                "response_id": response_id, "native_session": session,
                "model": model, "served": model, "in": 20, "cache_read": 80, "out": 10}

    def write_gateway(self, *records):
        self.gateway.write_text("".join(json.dumps(row) + "\n" for row in records))

    def scan(self):
        return USAGE.scan_codex(USAGE.range_bounds(), self.cache, local_only=True)["ranges"]["all"]

    def assert_tokens(self, result, count):
        self.assertEqual(tuple(result[key] for key in ("in", "cached", "out", "reason")),
                         (100 * count, 80 * count, 10 * count, 2 * count))

    def test_routes_each_response_and_deduplicates_mirrors_and_warm_scans(self):
        first, second = self.response("first"), self.response("second", 200)
        self.records.extend([first, self.mirror(first), second, self.mirror(second)])
        self.write_rollout()
        self.write_gateway(self.gateway_record("first"),
                           self.gateway_record("second", "gpt-6.1-terra"))
        result = self.scan()
        self.assert_tokens(result, 2)
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra", "openai/gpt-6.1-terra"})
        expected_cost = sum(USAGE._codex_estimated_cost(model, 100, 80, 10)
                            for model in result["models"])
        self.assertAlmostEqual(result["cost"], expected_cost)
        self.assertEqual(result, self.scan())

    def test_old_cache_backfill_replaces_ledger_without_recounting(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        before = copy.deepcopy(self.scan())
        entry = self.cache["codex"][str(self.rollout)]
        entry.pop("routing_v")
        entry.pop("has_routes")
        events = list(USAGE._iter_codex_cached_events(str(self.rollout)))
        entry["event_cache_size"] = USAGE._codex_write_event_cache(
            str(self.rollout), [event[:15] for event in events])
        USAGE.ledger_flush()
        USAGE._LEDGER_CACHE["data"] = None
        self.write_gateway(self.gateway_record("first"))
        result = self.scan()
        self.assert_tokens(result, 1)
        self.assertEqual(set(before["models"]), {"group/smart-split"})
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra"})
        self.assertEqual(result, self.scan())

    def test_late_gateway_record_updates_unchanged_rollout_without_reparsing(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        self.scan()
        self.write_gateway(self.gateway_record("first"))
        with mock.patch.object(USAGE, "_iter_codex_usage_records",
                               side_effect=AssertionError("unchanged rollout must stay cached")):
            result = self.scan()
        self.assert_tokens(result, 1)
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra"})
        self.assertEqual(result, self.scan())

    def test_incremental_append_keeps_previous_attribution(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        self.write_gateway(self.gateway_record("first"))
        self.scan()
        self.records.append(self.response("second", 200))
        self.write_rollout()
        self.write_gateway(self.gateway_record("second", "deepseek-v4-flash"))
        result = self.scan()
        self.assert_tokens(result, 2)
        self.assertEqual(set(result["models"]),
                         {USAGE._model_identity_id(model)
                          for model in ("gpt-6-astra", "deepseek-v4-flash")})
        self.assertEqual(result, self.scan())

    def test_missing_rotated_log_preserves_confirmed_model(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        self.write_gateway(self.gateway_record("first"))
        result = self.scan()
        self.gateway.unlink()
        self.assertEqual(result, self.scan())
        self.gateway.write_text("")
        self.assertEqual(result, self.scan())
        self.cache["codex"][str(self.rollout)]["parser_version"] = -1
        self.assertEqual(result, self.scan())

    def test_legacy_mirror_in_another_segment_keeps_real_model(self):
        first, second = self.response("first"), self.response("second", 200)
        self.records.append(first)
        self.write_rollout()
        continuation = self.root / "rollout-continuation.jsonl"
        continuation.write_text("".join(json.dumps(record) + "\n" for record in [
            *self.records[:2], self.mirror(first), second,
        ]))
        self.write_gateway(self.gateway_record("first"),
                           self.gateway_record("second", "gpt-6.1-terra"))
        result = self.scan()
        self.assert_tokens(result, 2)
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra", "openai/gpt-6.1-terra"})
        self.assertEqual(result, self.scan())

    def test_unknown_old_route_followed_by_direct_model_is_backfilled(self):
        self.records.extend([
            self.response("first"),
            self.record("turn_context", {"model": "gpt-6.1-terra"}),
            self.response("second", 200),
        ])
        self.write_rollout()
        self.scan()
        self.cache["codex"][str(self.rollout)].pop("routing_v")
        self.write_gateway(self.gateway_record("first"))
        result = self.scan()
        self.assert_tokens(result, 2)
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra", "openai/gpt-6.1-terra"})

    def test_served_model_overrides_requested_upstream_and_accepts_sessionless_id(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        gateway = self.gateway_record("first", session=None)
        gateway["model"] = "gpt-6.1-terra"
        self.write_gateway(gateway)
        result = self.scan()
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra"})

    def test_unknown_routing_is_not_guessed_from_other_sessions_or_classifier(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        classifier = self.gateway_record("first")
        classifier["agent"] = "magpie"
        self.write_gateway(self.gateway_record("first", session="another-session"), classifier)
        result = self.scan()
        self.assert_tokens(result, 1)
        self.assertEqual(set(result["models"]), {"group/smart-split"})
        self.assertEqual(USAGE.nice_model("group/smart-split"), "路由模型未识别")

    def test_legacy_first_dual_write_resolves_once_even_across_scans(self):
        response = self.response("first")
        self.records.append(self.mirror(response))
        self.write_rollout()
        self.scan()
        self.records.append(response)
        self.write_rollout()
        self.write_gateway(self.gateway_record("first"))
        result = self.scan()
        self.assert_tokens(result, 1)
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra"})
        self.assertEqual(result, self.scan())

    def test_duplicate_files_and_gateway_records_count_once(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        archive = self.root / "archive"
        archive.mkdir()
        (archive / "rollout-copy.jsonl").write_bytes(self.rollout.read_bytes())
        self.write_gateway(self.gateway_record("first"), self.gateway_record("first"))
        result = self.scan()
        self.assert_tokens(result, 1)
        self.assertEqual(result, self.scan())

    def test_non_routed_requests_keep_their_model(self):
        self.records[1]["payload"]["model"] = "gpt-6.1-terra"
        self.records.append(self.response("first"))
        self.write_rollout()
        self.write_gateway(self.gateway_record("first"))
        result = self.scan()
        self.assertEqual(set(result["models"]), {"openai/gpt-6.1-terra"})
        self.assert_tokens(result, 1)

    def test_incomplete_gateway_line_is_retried_after_completion(self):
        self.records.append(self.response("first"))
        self.write_rollout()
        record = json.dumps(self.gateway_record("first"))
        self.gateway.write_text("null\n" + record[:30])
        self.assertIn("group/smart-split", self.scan()["models"])
        with self.gateway.open("a") as handle:
            handle.write(record[30:] + "\n")
        result = self.scan()
        self.assertEqual(set(result["models"]), {"openai/gpt-6-astra"})
        self.assert_tokens(result, 1)
