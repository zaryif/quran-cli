"""
Tests — prayer times accuracy, config, ramadan detection.
Run: pytest tests/
"""
import pytest
from datetime import date, datetime
from quran.core.prayer_times import get_prayer_times, METHODS
from quran.core.ramadan import gregorian_to_hijri, is_ramadan, ramadan_day


class TestPrayerTimes:
    def test_dhaka_times(self):
        """Dhaka, Bangladesh — 23.8103N, 90.4125E"""
        pt = get_prayer_times(23.8103, 90.4125, for_date=date(2026, 3, 21))
        # Fajr should be early morning
        assert pt.fajr.hour in (4, 5)
        # Maghrib should be evening
        assert pt.maghrib.hour in (17, 18, 19)
        # Order: fajr < sunrise < dhuhr < asr < maghrib < isha
        assert pt.fajr < pt.sunrise < pt.dhuhr < pt.asr < pt.maghrib < pt.isha

    def test_london_times(self):
        pt = get_prayer_times(51.5074, -0.1278, for_date=date(2026, 6, 21))
        assert pt.fajr < pt.sunrise < pt.dhuhr < pt.asr < pt.maghrib < pt.isha

    def test_all_methods(self):
        for method in METHODS:
            pt = get_prayer_times(23.8, 90.4, for_date=date(2026, 3, 21), method=method)
            assert pt.fajr < pt.isha

    def test_next_prayer(self):
        pt = get_prayer_times(23.8103, 90.4125, for_date=date(2026, 3, 21))
        # Simulate being at 3 AM
        now = datetime(2026, 3, 21, 3, 0, 0)
        name, dt = pt.next_prayer(now)
        assert name == "Fajr"

    def test_hanafi_asr_later(self):
        """Hanafi asr should be later than Standard."""
        std  = get_prayer_times(23.8103, 90.4125, asr_method="Standard")
        han  = get_prayer_times(23.8103, 90.4125, asr_method="Hanafi")
        assert han.asr > std.asr


class TestHijriCalendar:
    def test_known_date(self):
        """Test a known Gregorian → Hijri conversion."""
        hy, hm, hd = gregorian_to_hijri(date(2025, 3, 1))
        assert hm == 9  # Should be Ramadan 1446

    def test_ramadan_detection(self):
        assert is_ramadan(date(2025, 3, 15))  # Known Ramadan 1446
        assert not is_ramadan(date(2025, 5, 1))

    def test_ramadan_day(self):
        rd = ramadan_day(date(2025, 3, 15))
        assert rd is not None and rd > 0


class TestConfig:
    def test_load_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        from quran.config import settings
        # Reset module state
        import importlib
        importlib.reload(settings)
        cfg = settings.load()
        assert cfg["lang"] == "en"
        assert "location" in cfg
        assert "remind" in cfg

    def test_set_and_get(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        from quran.config import settings
        import importlib
        importlib.reload(settings)
        settings.set_key("lang", "bn")
        assert settings.get("lang") == "bn"
