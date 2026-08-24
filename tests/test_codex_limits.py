import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "usage.30s.py"
SPEC = importlib.util.spec_from_file_location("tokei_usage", SCRIPT)
USAGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(USAGE)

# 测试不得读写本机 ~/.tokei/ledger.json
_LEDGER_DIR = tempfile.TemporaryDirectory(prefix="tokei-ledger-")
USAGE._LEDGER_FILE = str(Path(_LEDGER_DIR.name) / "ledger.json")
Path(USAGE._LEDGER_FILE).write_text('{"v":1,"tools":{}}', encoding="utf-8")
_REAL_LEDGER_RECONCILE = USAGE.ledger_reconcile
_REAL_LEDGER_TOUCH = USAGE.ledger_touch
# 默认测试走实时日志,避免共享账本把“今天”的高水位串到其他用例
USAGE.ledger_reconcile = lambda tool, live_days: live_days
USAGE.ledger_touch = lambda tool: None
USAGE._LEDGER_CACHE = {"data": None, "dirty": False}


class _Response:
    def __init__(self, payload, url=None):
        self.payload = json.dumps(payload).encode()
        self.url = url or USAGE._CODEX_USAGE_URL

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.payload[:limit]


class CodexQuotaValuesTests(unittest.TestCase):
    def test_legacy_primary_5h_secondary_week(self):
        limits = {
            "primary": {"used_percent": 25.0, "window_minutes": 300, "resets_at": 200},
            "secondary": {"used_percent": 40.0, "window_minutes": 10080, "resets_at": 300},
        }

        self.assertEqual(
            USAGE._codex_quota_values(limits, now_epoch=100),
            {"p5": 25.0, "pw": 40.0, "r5": 200, "rw": 300,
             "p5_stale": False, "pw_stale": False},
        )

    def test_week_only_primary(self):
        limits = {
            "primary": {"used_percent": 1.0, "window_minutes": 10080, "resets_at": 300},
            "secondary": None,
        }

        self.assertEqual(
            USAGE._codex_quota_values(limits, now_epoch=100),
            {"p5": None, "pw": 1.0, "r5": None, "rw": 300,
             "p5_stale": False, "pw_stale": False},
        )

    def test_expired_window_without_usage_is_reset(self):
        limits = {
            "primary": {"used_percent": 90.0, "window_minutes": 10080, "resets_at": 99},
        }

        self.assertEqual(
            USAGE._codex_quota_values(limits, now_epoch=100, consumed={"pw": 0}),
            {"p5": None, "pw": 0.0, "r5": None, "rw": None,
             "p5_stale": False, "pw_stale": False},
        )

    def test_expired_window_with_usage_is_stale(self):
        limits = {
            "primary": {"used_percent": 90.0, "window_minutes": 10080, "resets_at": 99},
        }

        self.assertEqual(
            USAGE._codex_quota_values(limits, now_epoch=100, consumed={"pw": 12345}),
            {"p5": None, "pw": 90.0, "r5": None, "rw": 99,
             "p5_stale": False, "pw_stale": True},
        )

    def test_expired_window_without_consumption_data_is_stale(self):
        limits = {
            "primary": {"used_percent": 90.0, "window_minutes": 10080, "resets_at": 99},
        }

        self.assertEqual(
            USAGE._codex_quota_values(limits, now_epoch=100, consumed=None),
            {"p5": None, "pw": 90.0, "r5": None, "rw": 99,
             "p5_stale": False, "pw_stale": True},
        )

    def test_keep_log_week_when_live_is_empty_seven_day_window(self):
        now = 1_000_000
        log = {
            "primary": {
                "used_percent": 18.0,
                "window_minutes": 10080,
                "resets_at": now + 76 * 3600,
            },
        }
        live = {
            "primary": {
                "used_percent": 0.0,
                "window_minutes": 10080,
                "resets_at": now + 7 * 24 * 3600,
            },
        }
        self.assertTrue(USAGE._codex_keep_log_week(log, live, now))

    def test_take_live_week_when_live_has_real_usage(self):
        now = 1_000_000
        log = {
            "primary": {
                "used_percent": 18.0,
                "window_minutes": 10080,
                "resets_at": now + 76 * 3600,
            },
        }
        live = {
            "primary": {
                "used_percent": 19.0,
                "window_minutes": 10080,
                "resets_at": now + 76 * 3600,
            },
        }
        self.assertFalse(USAGE._codex_keep_log_week(log, live, now))

    def test_take_live_week_when_log_window_already_ended(self):
        now = 1_000_000
        log = {
            "primary": {
                "used_percent": 90.0,
                "window_minutes": 10080,
                "resets_at": now - 10,
            },
        }
        live = {
            "primary": {
                "used_percent": 0.0,
                "window_minutes": 10080,
                "resets_at": now + 7 * 24 * 3600,
            },
        }
        self.assertFalse(USAGE._codex_keep_log_week(log, live, now))

    def test_live_quota_rejects_cross_origin_redirect(self):
        payload = {
            "rate_limit": {
                "primary_window": {
                    "used_percent": 25,
                    "limit_window_seconds": 604800,
                    "reset_at": 200,
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            auth_path = Path(temp_dir) / "auth.json"
            cache_path = Path(temp_dir) / "cache.json"
            auth_path.write_text(json.dumps({
                "tokens": {
                    "access_token": "test-token",
                    "account_id": "test-account",
                },
            }))
            response = _Response(payload, url="https://example.com/usage")
            with mock.patch.object(USAGE, "CODEX_AUTH", str(auth_path)), \
                    mock.patch.object(USAGE, "CODEX_QUOTA_CACHE", str(cache_path)), \
                    mock.patch("urllib.request.urlopen", return_value=response):
                self.assertIsNone(USAGE.fetch_codex_live_limits())

    def test_live_quota_uses_initial_request_only_credentials(self):
        payload = {
            "rate_limit": {
                "primary_window": {
                    "used_percent": 25,
                    "limit_window_seconds": 604800,
                    "reset_at": 200,
                },
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            auth_path = Path(temp_dir) / "auth.json"
            cache_path = Path(temp_dir) / "cache.json"
            auth_path.write_text(json.dumps({
                "tokens": {
                    "access_token": "test-token",
                    "account_id": "test-account",
                },
            }))
            opener = mock.Mock(return_value=_Response(payload))
            with mock.patch.object(USAGE, "CODEX_AUTH", str(auth_path)), \
                    mock.patch.object(USAGE, "CODEX_QUOTA_CACHE", str(cache_path)), \
                    mock.patch("urllib.request.urlopen", opener):
                limits, _, _ = USAGE.fetch_codex_live_limits()

        request = opener.call_args.args[0]
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(
            request.unredirected_hdrs["Authorization"],
            "Bearer test-token",
        )
        self.assertEqual(limits["primary"]["used_percent"], 25.0)

    def test_recent_failure_uses_active_official_cache(self):
        now = USAGE.datetime.now().timestamp()
        auth = {
            "tokens": {
                "access_token": "test-token",
                "account_id": "test-account",
            },
        }
        account_key = USAGE._codex_auth_context(auth)["account_key"]
        limits = {
            "primary": {
                "used_percent": 69.0,
                "window_minutes": 10080,
                "resets_at": int(now + 3 * 24 * 3600),
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            auth_path = Path(temp_dir) / "auth.json"
            auth_path.write_text(json.dumps(auth))
            cache_path.write_text(json.dumps({
                "fetched_at": now - 3600,
                "last_failure_at": now,
                "limits": limits,
                "plan": "pro",
                "account_key": account_key,
            }))
            with mock.patch.object(USAGE, "CODEX_AUTH", str(auth_path)), \
                    mock.patch.object(USAGE, "CODEX_QUOTA_CACHE", str(cache_path)), \
                    mock.patch("urllib.request.urlopen") as opener:
                cached_limits, plan, fetched_at = USAGE.fetch_codex_live_limits()

        opener.assert_not_called()
        self.assertEqual(cached_limits["primary"]["used_percent"], 69.0)
        self.assertEqual(plan, "pro")
        self.assertEqual(fetched_at, now - 3600)

    def test_recent_failure_rejects_cache_after_window_reset(self):
        now = USAGE.datetime.now().timestamp()
        auth = {
            "tokens": {
                "access_token": "test-token",
                "account_id": "test-account",
            },
        }
        account_key = USAGE._codex_auth_context(auth)["account_key"]
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            auth_path = Path(temp_dir) / "auth.json"
            auth_path.write_text(json.dumps(auth))
            cache_path.write_text(json.dumps({
                "fetched_at": now - 3600,
                "last_failure_at": now,
                "limits": {
                    "primary": {
                        "used_percent": 69.0,
                        "window_minutes": 10080,
                        "resets_at": int(now - 1),
                    },
                },
                "plan": "pro",
                "account_key": account_key,
            }))
            with mock.patch.object(USAGE, "CODEX_AUTH", str(auth_path)), \
                    mock.patch.object(USAGE, "CODEX_QUOTA_CACHE", str(cache_path)):
                self.assertIsNone(USAGE.fetch_codex_live_limits())

    def test_official_cache_is_scoped_to_codex_account(self):
        now = USAGE.datetime.now().timestamp()
        auth = {
            "tokens": {
                "access_token": "test-token",
                "account_id": "current-account",
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            auth_path = Path(temp_dir) / "auth.json"
            auth_path.write_text(json.dumps(auth))
            cache_path.write_text(json.dumps({
                "fetched_at": now - 3600,
                "last_failure_at": now,
                "limits": {
                    "primary": {
                        "used_percent": 69.0,
                        "window_minutes": 10080,
                        "resets_at": int(now + 3600),
                    },
                },
                "account_key": "different-account",
            }))
            with mock.patch.object(USAGE, "CODEX_AUTH", str(auth_path)), \
                    mock.patch.object(USAGE, "CODEX_QUOTA_CACHE", str(cache_path)), \
                    mock.patch("urllib.request.urlopen", side_effect=OSError("offline")):
                self.assertIsNone(USAGE.fetch_codex_live_limits())

    def test_newer_local_snapshot_wins_over_stale_official_cache(self):
        self.assertFalse(USAGE._codex_live_snapshot_is_current(
            1_700_000_000, "2023-11-14T22:13:21+00:00"))
        self.assertTrue(USAGE._codex_live_snapshot_is_current(
            1_700_000_002, "2023-11-14T22:13:21+00:00"))


def _epoch(year, month, day, hour=0, minute=0):
    return int(datetime(year, month, day, hour, minute).timestamp())


class CodexUsedSinceTests(unittest.TestCase):
    def days(self):
        boundary = [0] * 24
        boundary[3] = 40
        boundary[9] = 80
        later = [0] * 24
        later[1] = 230
        return {
            "2026-08-09": {"in": 500, "out": 50, "hours": [0] * 24},
            "2026-08-10": {"in": 100, "out": 20, "hours": boundary},
            "2026-08-11": {"in": 200, "out": 30, "hours": later},
        }

    def test_boundary_day_is_sliced_from_the_reset_hour(self):
        self.assertEqual(
            USAGE._codex_used_since(self.days(), _epoch(2026, 8, 10, 6)), 310)

    def test_reset_at_midnight_keeps_the_whole_boundary_day(self):
        self.assertEqual(
            USAGE._codex_used_since(self.days(), _epoch(2026, 8, 10)), 350)

    def test_reset_in_the_future_reports_no_usage(self):
        self.assertEqual(
            USAGE._codex_used_since(self.days(), _epoch(2026, 8, 12)), 0)

    def test_boundary_day_without_hours_counts_the_whole_day(self):
        days = self.days()
        days["2026-08-10"].pop("hours")

        self.assertEqual(
            USAGE._codex_used_since(days, _epoch(2026, 8, 10, 6)), 350)

    def test_missing_reset_time_is_unknown_not_zero(self):
        self.assertIsNone(USAGE._codex_used_since(self.days(), None))


class CodexScanFreshnessTests(unittest.TestCase):
    RESET = _epoch(2024, 1, 8, 2)

    def token_count(self, hour, minute, total, last, rate_limits=None):
        payload = {
            "type": "token_count",
            "info": {
                "total_token_usage": {
                    "input_tokens": total[0],
                    "cached_input_tokens": total[1],
                    "output_tokens": total[2],
                    "reasoning_output_tokens": total[3],
                },
                "last_token_usage": {
                    "input_tokens": last[0],
                    "cached_input_tokens": last[1],
                    "output_tokens": last[2],
                    "reasoning_output_tokens": last[3],
                },
            },
        }
        if rate_limits:
            payload["rate_limits"] = rate_limits
        return json.dumps({
            "timestamp": datetime(2024, 1, 8, hour, minute).astimezone().isoformat(),
            "type": "event_msg",
            "payload": payload,
        })

    def bounds(self):
        day = datetime(2024, 1, 8, tzinfo=timezone.utc)
        return {
            "today": day,
            "yesterday": day - timedelta(days=1),
            "week": day,
            "last_week": day - timedelta(days=7),
            "last_week_end": day,
            "month": day.replace(day=1),
            "year": day.replace(month=1, day=1),
        }

    def scan(self, tmp):
        limits = {
            "limit_id": "codex",
            "plan_type": "pro",
            "primary": {"used_percent": 90.0, "window_minutes": 10080,
                        "resets_at": self.RESET},
            "secondary": None,
        }
        path = Path(tmp) / "rollout-freshness.jsonl"
        path.write_text("\n".join([
            json.dumps({
                "timestamp": "2024-01-08T00:00:00Z",
                "type": "session_meta",
                "payload": {"id": "freshness", "cwd": "/tmp/project"},
            }),
            self.token_count(0, 30, (100, 80, 10, 4), (100, 80, 10, 4),
                             rate_limits=limits),
            self.token_count(5, 0, (150, 120, 15, 6), (50, 40, 5, 2)),
        ]) + "\n", encoding="utf-8")

        with mock.patch.object(USAGE, "CODEX_DIR", tmp), \
                mock.patch.object(USAGE, "CODEX_ARCHIVED_DIR",
                                  str(Path(tmp) / "archived_sessions")), \
                mock.patch.object(USAGE, "fetch_codex_live_limits", return_value=None):
            return USAGE.scan_codex(self.bounds(), {"v": USAGE._SCAN_CACHE_VERSION})

    def test_scan_reports_reading_time_and_usage_since_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scan(tmp)

        self.assertEqual(result["limits_updated"], _epoch(2024, 1, 8, 0, 30))
        self.assertEqual(result["limits_consumed"], {"p5": None, "pw": 55})

    def test_expired_reading_with_usage_is_reported_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.scan(tmp)

        values = USAGE._codex_quota_values(
            result["limits"], now_epoch=self.RESET + 3600,
            consumed=result["limits_consumed"])

        self.assertTrue(values["pw_stale"])
        self.assertEqual(values["pw"], 90.0)
        self.assertEqual(values["rw"], self.RESET)


if __name__ == "__main__":
    unittest.main()
