"""
Tests — lock module: PIN hashing, config save/load, fallback behavior.
Run: pytest tests/test_lock.py -v
"""
import pytest
import hashlib


class TestLockPIN:
    def test_pin_hash_sha256(self):
        """PIN should be hashed with SHA-256."""
        from quran.commands.lock import _hash
        pin = "1234"
        expected = hashlib.sha256(pin.encode()).hexdigest()
        assert _hash(pin) == expected

    def test_pin_hash_different_pins(self):
        """Different PINs should produce different hashes."""
        from quran.commands.lock import _hash
        assert _hash("1234") != _hash("5678")
        assert _hash("0000") != _hash("9999")

    def test_pin_hash_consistency(self):
        """Same PIN should always produce the same hash."""
        from quran.commands.lock import _hash
        pin = "mypin123"
        h1 = _hash(pin)
        h2 = _hash(pin)
        assert h1 == h2

    def test_pin_save_and_get(self, tmp_path, monkeypatch):
        """PIN should be saved to config and retrievable."""
        monkeypatch.setenv("HOME", str(tmp_path))
        from quran.config import settings
        import importlib
        importlib.reload(settings)

        from quran.commands.lock import _save_pin, _get_pin_hash, _hash
        _save_pin("4321")

        cfg = settings.load()
        assert cfg["lock"]["pin_hash"] == _hash("4321")
        assert cfg["lock"]["enabled"] is True

    def test_pin_remove(self, tmp_path, monkeypatch):
        """Removing PIN should clear hash and disable lock."""
        monkeypatch.setenv("HOME", str(tmp_path))
        from quran.config import settings
        import importlib
        importlib.reload(settings)

        from quran.commands.lock import _save_pin
        _save_pin("1111")
        _save_pin(None)

        cfg = settings.load()
        assert cfg["lock"]["pin_hash"] == ""
        assert cfg["lock"]["enabled"] is False


class TestLockDefaults:
    def test_config_defaults_include_lock(self, tmp_path, monkeypatch):
        """Config defaults should include lock section."""
        monkeypatch.setenv("HOME", str(tmp_path))
        from quran.config import settings
        import importlib
        importlib.reload(settings)

        cfg = settings.load()
        assert "lock" in cfg
        assert cfg["lock"]["pin_hash"] == ""
        assert cfg["lock"]["enabled"] is False


class TestClockModule:
    def test_clock_module_imports(self):
        """Clock module should import without errors."""
        from quran.commands.clock import _get_prayer_data, _fmt_countdown, _build_display
        assert callable(_get_prayer_data)
        assert callable(_fmt_countdown)
        assert callable(_build_display)

    def test_fmt_countdown(self):
        """Countdown formatter should produce readable strings."""
        from quran.commands.clock import _fmt_countdown
        from datetime import datetime, timedelta

        now = datetime(2026, 4, 20, 12, 0, 0)
        future = now + timedelta(hours=2, minutes=30, seconds=15)
        result = _fmt_countdown(future, now)
        assert "2h" in result
        assert "30m" in result

    def test_fmt_countdown_minutes_only(self):
        """Countdown under 1 hour should not show hours."""
        from quran.commands.clock import _fmt_countdown
        from datetime import datetime, timedelta

        now = datetime(2026, 4, 20, 12, 0, 0)
        future = now + timedelta(minutes=15, seconds=30)
        result = _fmt_countdown(future, now)
        assert "h" not in result
        assert "15m" in result
