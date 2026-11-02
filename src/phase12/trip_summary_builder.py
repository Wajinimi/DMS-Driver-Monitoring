# Phase 12 I am building the end-of-trip report used by the terminal printout and on-screen overlay
from src.phase9.safety_score_engine import SafetyScoreEngine
from src.phase10.recommendation_engine import RecommendationEngine


def build_trip_report(config, trip_summary, max_tips=2):
    """
     turninng a saved trip row into score + coaching messages

    Returns one dict so print and overlay show the same facts
    """
    trip_id = trip_summary.get("trip_id")
    score_cfg = config["safety_score"]
    coach_cfg = config["coaching"]

    score_engine = SafetyScoreEngine(
        weights=score_cfg["weights"],
        scale_factor=score_cfg["scale_factor"],
        bands=score_cfg["bands"],
        exposure_unit=score_cfg["exposure_unit"],
        db_path=config["analytics"]["db_path"],
    )
    coach_engine = RecommendationEngine(
        behavior_tips=coach_cfg["behavior_tips"],
        baseline_weeks=coach_cfg["baseline_weeks"],
        increase_threshold=coach_cfg["increase_threshold"],
        improve_threshold=coach_cfg["improve_threshold"],
        db_path=config["analytics"]["db_path"],
    )

    trip_score = score_engine.compute_trip_score(trip_id) if trip_id else {}
    trip_report = {
        "has_data": trip_score.get("safety_score") is not None,
        "safety_score": trip_score.get("safety_score"),
        "band": trip_score.get("band"),
        "top_contributors": trip_score.get("top_contributors", []),
    }
    coaching = coach_engine.generate_trip_coaching(trip_report)
    tips = coaching.get("recommendations", [])[:max_tips]

    return {
        "trip_summary": trip_summary,
        "trip_score": trip_score,
        "trip_report": trip_report,
        "coaching": coaching,
        "tips": tips,
    }


def format_terminal_report(report_bundle):
    """i am formatting the same report as plain text for the terminal"""
    trip_summary = report_bundle["trip_summary"]
    trip_report = report_bundle["trip_report"]
    tips = report_bundle["tips"]
    trip_id = trip_summary.get("trip_id")

    lines = []
    lines.append("=" * 60)
    lines.append("TRIP SAVED")
    lines.append(f"  trip_id: {trip_id}")
    lines.append(f"  duration_sec: {round(trip_summary.get('duration_sec', 0), 1)}")
    lines.append(
        f"  distraction_sec: {round(trip_summary.get('total_distraction_sec', 0), 1)}"
    )
    lines.append(f"  alerts: {trip_summary.get('alert_count', 0)}")
    lines.append("")
    lines.append("TRIP SCORE (monitoring time only)")

    if trip_report["has_data"]:
        lines.append(
            f"  score: {trip_report['safety_score']} /100 — {trip_report['band']}"
        )
        lines.append(f"  top contributors: {trip_report.get('top_contributors', [])}")
    else:
        lines.append(
            "  no score (monitoring never activated — press + until speed >= 15 km/h)"
        )

    lines.append("")
    lines.append("COACHING")
    for rec in tips:
        lines.append(f"  {rec['rule']} → {rec['message']}")

    lines.append("")
    lines.append("Next: python3 run_dashboard.py → refresh browser to see charts")
    lines.append("=" * 60)
    return "\n".join(lines)
