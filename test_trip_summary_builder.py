# Phase 12 — I test trip summary text building without the webcam
import yaml

from src.phase12.trip_summary_builder import build_trip_report, format_terminal_report


def test_build_from_latest_trip():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)

    import sqlite3

    conn = sqlite3.connect(config["analytics"]["db_path"])
    row = conn.execute(
        "SELECT trip_id FROM trips ORDER BY start_time DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if row is None:
        print("SKIP — no trips in database yet")
        return

    trip_id = row[0]
    fake_summary = {
        "trip_id": trip_id,
        "duration_sec": 120.0,
        "total_distraction_sec": 8.0,
        "alert_count": 1,
    }

    bundle = build_trip_report(config, fake_summary, max_tips=2)
    assert "trip_report" in bundle
    assert "tips" in bundle
    assert len(bundle["tips"]) <= 2

    text = format_terminal_report(bundle)
    assert "TRIP SAVED" in text
    assert trip_id in text
    print(text)


if __name__ == "__main__":
    test_build_from_latest_trip()
    print("Trip summary builder test passed.")
