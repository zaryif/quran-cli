
import sys
import os
from datetime import datetime, timedelta

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quran.core.prayer_times import get_prayer_times
from quran.core.notifier import dispatch_all

def test_prayer_calculation():
    print("Testing prayer calculation for Dhaka...")
    # Dhaka coordinates
    lat, lon = 23.8103, 90.4125
    tz = "Asia/Dhaka"
    
    pt = get_prayer_times(lat, lon, tz=tz)
    times = pt.as_dict()
    
    for name, dt in times.items():
        print(f"{name}: {dt.strftime('%I:%M %p')}")
    
    assert "Fajr" in times
    print("✓ Prayer calculation works.")

def test_notification_dispatch():
    print("\nTesting notification dispatch (Dry run/Local)...")
    # We'll just test if it runs without crashing
    try:
        dispatch_all("Test Title", "Test Message", topic="test-topic")
        print("✓ Notification dispatch executed without errors.")
    except Exception as e:
        print(f"✗ Notification dispatch failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_prayer_calculation()
    test_notification_dispatch()
    print("\nAll local tests passed!")
