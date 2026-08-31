import json
import os
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from test_codex_limits import USAGE


class KimiQuotaTests(unittest.TestCase):
    def test_live_quota_can_be_disabled_in_tokei_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config.json").write_text(
                json.dumps({"kimi_live_quota_enabled": False}), encoding="utf-8")
            ensure = mock.Mock()
            with mock.patch.object(USAGE, "_USER_DIR", str(root)), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", ensure):
                quota = USAGE.fetch_kimi_quota()

        self.assertIsNone(quota)
        ensure.assert_not_called()

    def test_parse_weekly_five_hour_and_extra_usage(self):
        payload = {
            "usage": {"used": "40", "limit": "1000", "resetTime": "2026-08-10T00:00:00Z"},
            "limits": [{
                "name": "rolling",
                "window": {"duration": "300", "timeUnit": "TIME_UNIT_MINUTE"},
                "detail": {"used": "25", "limit": "100", "resetTime": "2026-08-04T08:00:00Z"},
            }],
            "boosterWallet": {
                "balance": {"type": "BOOSTER", "amount": "250000000", "amountLeft": "125000000"},
                "monthlyChargeLimitEnabled": True,
                "monthlyChargeLimit": {"priceInCents": "1000", "currency": "USD"},
                "monthlyUsed": {"priceInCents": "125", "currency": "USD"},
            },
        }

        quota = USAGE._parse_kimi_usage(payload)

        self.assertEqual(quota["weekly"]["used"], 40)
        self.assertEqual(quota["weekly"]["duration"], 1)
        self.assertEqual(quota["weekly"]["unit"], "week")
        self.assertEqual(quota["limits"][0]["duration"], 5)
        self.assertEqual(quota["limits"][0]["unit"], "hour")
        self.assertEqual(quota["extra_usage"]["balance_cents"], 125)
        self.assertEqual(quota["extra_usage"]["monthly_limit_cents"], 1000)

    def test_refresh_rotates_credentials_atomically_with_private_permissions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            credentials = root / "credentials" / "kimi-code.json"
            credentials.parent.mkdir(parents=True)
            credentials.write_text(json.dumps({
                "access_token": "expired",
                "refresh_token": "refresh-old",
                "expires_at": 1,
                "expires_in": 3600,
            }), encoding="utf-8")
            refreshed = {
                "access_token": "fresh",
                "refresh_token": "refresh-new",
                "expires_at": 4_000_000_000,
                "expires_in": 3600,
                "scope": "",
                "token_type": "Bearer",
            }
            with mock.patch.object(USAGE, "KIMI_CREDENTIALS", str(credentials)), \
                    mock.patch.object(USAGE, "KIMI_OAUTH_LOCK_TARGET", str(root / "oauth" / "kimi-code")), \
                    mock.patch.object(USAGE, "_kimi_refresh_access_token", return_value=refreshed):
                token = USAGE._kimi_ensure_access_token()

            stored = json.loads(credentials.read_text(encoding="utf-8"))
            self.assertEqual(token, "fresh")
            self.assertEqual(stored["refresh_token"], "refresh-new")
            self.assertEqual(os.stat(credentials).st_mode & 0o777, 0o600)
            self.assertFalse((root / "oauth" / "kimi-code.lock").exists())

    def test_fallback_cache_is_marked_stale(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "kimi-quota.json"
            cache.write_text(json.dumps({
                "fetched_at": int(datetime.now().timestamp()),
                "quota": {"weekly": {"used": 1, "limit": 10}, "limits": []},
            }), encoding="utf-8")
            with mock.patch.object(USAGE, "KIMI_QUOTA_CACHE", str(cache)), \
                    mock.patch.object(USAGE, "_KIMI_QUOTA_TTL", 0), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", side_effect=PermissionError("not_authenticated")):
                quota = USAGE.fetch_kimi_quota()

        self.assertEqual(quota["source"], "cache")
        self.assertTrue(quota["stale"])
        self.assertEqual(quota["error"], "not_authenticated")

    def test_cache_expires_when_quota_reset_time_is_reached(self):
        payload = {
            "usage": {"used": "0", "limit": "100", "resetTime": "2026-08-14T08:00:00Z"},
            "limits": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "kimi-quota.json"
            now = int(datetime.now().timestamp())
            cache.write_text(json.dumps({
                "fetched_at": now,
                "quota": {
                    "weekly": {"used": 31, "limit": 100, "reset_at": now - 1},
                    "limits": [],
                },
            }), encoding="utf-8")
            with mock.patch.object(USAGE, "KIMI_QUOTA_CACHE", str(cache)), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", return_value="token") as ensure, \
                    mock.patch.object(USAGE, "_kimi_fetch_usage_payload", return_value=payload):
                quota = USAGE.fetch_kimi_quota()

        self.assertEqual(quota["source"], "live")
        self.assertEqual(quota["weekly"]["used"], 0)
        ensure.assert_called_once_with()

    def test_forced_refresh_bypasses_fresh_quota_cache(self):
        payload = {
            "usage": {"used": "0", "limit": "100", "resetTime": "2026-08-14T08:00:00Z"},
            "limits": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "kimi-quota.json"
            cache.write_text(json.dumps({
                "fetched_at": int(datetime.now().timestamp()),
                "quota": {
                    "weekly": {"used": 31, "limit": 100, "reset_at": 4_000_000_000},
                    "limits": [],
                },
            }), encoding="utf-8")
            with mock.patch.object(USAGE, "KIMI_QUOTA_CACHE", str(cache)), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", return_value="token") as ensure, \
                    mock.patch.object(USAGE, "_kimi_fetch_usage_payload", return_value=payload):
                quota = USAGE.fetch_kimi_quota(force=True)

        self.assertEqual(quota["source"], "live")
        self.assertEqual(quota["weekly"]["used"], 0)
        ensure.assert_called_once_with()

    def test_manual_refresh_passes_force_quota_flag_to_collector(self):
        root = Path(__file__).resolve().parents[1]
        panel = (root / "Tokei" / "Sources" / "Tokei" / "PanelView.swift").read_text()
        loader = (root / "Tokei" / "Sources" / "Tokei" / "DataLoader.swift").read_text()
        collector = (root / "usage.30s.py").read_text()

        self.assertIn("store.refresh(forceKimiQuota: true)", panel)
        self.assertIn('args.append("--force-kimi-quota")', loader)
        self.assertIn('force_kimi_quota = "--force-kimi-quota" in sys.argv', collector)

    def test_missing_login_returns_actionable_error_without_cache(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "missing.json"
            with mock.patch.object(USAGE, "KIMI_QUOTA_CACHE", str(cache)), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", side_effect=PermissionError("not_authenticated")):
                quota = USAGE.fetch_kimi_quota()

        self.assertEqual(quota, {"stale": True, "error": "not_authenticated"})

    def test_live_quota_cache_never_contains_oauth_tokens(self):
        payload = {
            "usage": {"used": "2", "limit": "10", "resetTime": "2026-08-10T00:00:00Z"},
            "limits": [],
        }
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "kimi-quota.json"
            with mock.patch.object(USAGE, "KIMI_QUOTA_CACHE", str(cache)), \
                    mock.patch.object(USAGE, "_kimi_ensure_access_token", return_value="secret-token"), \
                    mock.patch.object(USAGE, "_kimi_fetch_usage_payload", return_value=payload):
                quota = USAGE.fetch_kimi_quota()
            raw = cache.read_text(encoding="utf-8")

        self.assertEqual(quota["source"], "live")
        self.assertFalse(quota["stale"])
        self.assertNotIn("secret-token", raw)
        self.assertNotIn("access_token", raw)


if __name__ == "__main__":
    unittest.main()
