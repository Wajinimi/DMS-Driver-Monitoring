"""Phase 9 Step 6 — full simulation test for SafetyScoreEngine."""

import os
import sqlite3
import sys
import tempfile

import yaml

from src.phase9.safety_score_engine import SafetyScoreEngine

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


def load_engine(db_path=None):
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    cfg = config["safety_score"]
    return SafetyScoreEngine(
        weights=cfg["weights"],
        scale_factor=cfg["scale_factor"],
        bands=cfg["bands"],
        exposure_unit=cfg["exposure_unit"],
        db_path=db_path,
    )


def test_score_math(engine):
    print("\n1) Score math (fake activity durations, no database)")

    baseline = {
        "eat": 90.0,
        "magazine": 120.0,
        "sunglasses": 30.0,
    }
    result = engine.score_from_durations(baseline)
    check("baseline total_risk", result["total_risk"] == 15.5, f"got {result['total_risk']}")
    check("baseline safety_score", result["safety_score"] == 97.7, f"got {result['safety_score']}")
    check("baseline band", result["band"] == "Excellent", f"got {result['band']}")

    perfect = engine.score_from_durations({})
    check("perfect driver score", perfect["safety_score"] == 100.0)
    check("perfect driver band", perfect["band"] == "Excellent")

    high_risk = engine.score_from_durations({"magazine": 2800.0})
    check("high risk band", high_risk["band"] == "High risk", f"score={high_risk['safety_score']}")
    check("high risk score below 70", high_risk["safety_score"] < 70)

    good = engine.score_from_durations({"magazine": 1200.0})
    check("good band", good["band"] == "Good", f"score={good['safety_score']}")

    fair = engine.score_from_durations({"magazine": 2000.0})
    check("fair band", fair["band"] == "Fair", f"score={fair['safety_score']}")


def test_top_contributors(engine):
    print("\n2) Top contributors")

    contributions = {"eat": 10.52, "magazine": 32.58, "sunglasses": 1.0}
    top = engine.get_top_contributors(contributions, n=2, total_risk=44.1)

    check("top count", len(top) == 2)
    check("top behavior order", top[0]["behavior"] == "magazine" and top[1]["behavior"] == "eat")
    check(
        "top pct sums roughly to covered share",
        abs(top[0]["pct_of_total_risk"] + top[1]["pct_of_total_risk"] - 97.7) < 1.0,
        f"got {top[0]['pct_of_total_risk']} + {top[1]['pct_of_total_risk']}",
    )


def test_percentages(engine):
    print("\n3) Safe / behavior percentages")

    durations = {"eat": 60.0, "magazine": 90.0}
    safe_pct, behavior_pct = engine._compute_percentage(durations, total_driving_sec=600.0)

    check("safe + behavior totals 100", abs(safe_pct + sum(behavior_pct.values()) - 100.0) < 0.1)
    check("eat pct", behavior_pct["eat"] == 10.0, f"got {behavior_pct['eat']}")
    check("magazine pct", behavior_pct["magazine"] == 15.0, f"got {behavior_pct['magazine']}")

    safe_pct2, behavior_pct2 = engine._compute_percentage(durations, total_driving_sec=0.0)
    check("handles zero trip time", abs(safe_pct2 + sum(behavior_pct2.values()) - 100.0) < 0.1)


def create_sim_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE trips (
            trip_id TEXT PRIMARY KEY,
            start_time REAL NOT NULL,
            end_time REAL,
            total_distraction_sec REAL DEFAULT 0,
            alert_count INTEGER DEFAULT 0
        );
        CREATE TABLE activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id TEXT NOT NULL,
            activity TEXT NOT NULL,
            start_time REAL NOT NULL,
            end_time REAL NOT NULL,
            duration_sec REAL NOT NULL,
            max_confidence REAL
        );
        """
    )

    # Simulated week: Jul 20–22, 2026
    trips = [
        ("trip_sim_mon", 1784582400.0, 1784584200.0),  # 30 min
        ("trip_sim_wed", 1784755200.0, 1784756400.0),  # 20 min
    ]
    conn.executemany(
        "INSERT INTO trips (trip_id, start_time, end_time) VALUES (?, ?, ?)",
        trips,
    )
    activities = [
        ("trip_sim_mon", "eat", 1784582500.0, 1784582560.0, 60.0),
        ("trip_sim_mon", "magazine", 1784583000.0, 1784583090.0, 90.0),
        ("trip_sim_wed", "sunglasses", 1784755300.0, 1784755345.0, 45.0),
    ]
    conn.executemany(
        """
        INSERT INTO activities (trip_id, activity, start_time, end_time, duration_sec)
        VALUES (?, ?, ?, ?, ?)
        """,
        activities,
    )
    conn.commit()
    conn.close()


def test_sqlite_simulation():
    print("\n4) SQLite simulation (fake trips + activities)")

    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        create_sim_db(db_path)
        engine = load_engine(db_path=db_path)

        trip = engine.compute_trip_score("trip_sim_mon")
        check("trip score computed", trip["safety_score"] is not None)
        check("trip top contributor", trip["top_contributors"][0]["behavior"] == "magazine")
        check("trip has eat + magazine", set(trip["activity_durations_sec"]) == {"eat", "magazine"})

        week = engine.compute_weekly_score(end_date="2026-07-25")
        check("weekly has_data", week["has_data"] is True)
        check("weekly score computed", week["safety_score"] is not None)
        check("weekly top contributor", week["top_contributors"][0]["behavior"] == "magazine")
        check(
            "weekly behavior pct includes all distractions",
            set(week["behavior_pct"]) == {"eat", "magazine", "sunglasses"},
        )
        check(
            "weekly safe + behavior pct = 100",
            abs(week["safe_driving_pct"] + sum(week["behavior_pct"].values()) - 100.0) < 0.2,
        )

        empty_week = engine.compute_weekly_score(end_date="2026-06-01")
        check("empty week has_data false", empty_week["has_data"] is False)
        check("empty week band", empty_week["band"] == "No data")
        check("empty week score null", empty_week["safety_score"] is None)

        print(f"\n  Sample trip score: {trip['safety_score']} /100 — {trip['band']}")
        print(f"  Sample week score: {week['safety_score']} /100 — {week['band']}")
        print(f"  Week top contributors: {week['top_contributors']}")
    finally:
        os.remove(db_path)


def main():
    print("Phase 9 — Safety Score Engine (full simulation)")
    engine = load_engine()
    test_score_math(engine)
    test_top_contributors(engine)
    test_percentages(engine)
    test_sqlite_simulation()

    print(f"\n{'=' * 50}")
    print(f"Results: {PASS} passed, {FAIL} failed")
    if FAIL:
        sys.exit(1)
    print("All simulations passed.")


if __name__ == "__main__":
    main()
