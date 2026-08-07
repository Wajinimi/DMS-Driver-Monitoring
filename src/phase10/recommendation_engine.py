# Phase 10 — I want a rule-based coaching engine from the weekly safety score report
import logging
import sqlite3
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RecommendationEngine:
    def __init__(
        self,
        behavior_tips=None,
        baseline_weeks=4,
        increase_threshold=1.30,
        improve_threshold=0.85,
        db_path=None,
    ):
        # I store behavior tips from config.yaml (eat, magazine, etc.)
        self._behavior_tips = behavior_tips or {}
        # I use this many past weeks to compute "what I normally do"
        self._baseline_weeks = baseline_weeks
        # If this week > baseline × 1.30, I flag the behavior as "increased"
        self._increase_threshold = increase_threshold
        # If this week < baseline × 0.85, I flag the behavior as "improved"
        self._improve_threshold = improve_threshold
        # I read activity history from the same SQLite file as Phase 7
        self._db_path = db_path
        logger.info(
            "I started the Recommendation Engine (baseline_weeks=%s)",
            baseline_weeks,
        )

    def _score_band_rules(self, report):
        """I return coaching messages based on the safety score band (Excellent, Fair, etc.)."""
        recommendations = []

        # I stop early if Phase 9 says there is no trip data this week
        if not report.get("has_data") or report.get("safety_score") is None:
            recommendations.append({
                "rule": "no_data",
                "message": "Not enough driving data this week to generate coaching.",
            })
            return recommendations

        # I pull the score and the #1 risk behavior from the weekly report
        score = report["safety_score"]
        band = report.get("band", "")
        top = report.get("top_contributors") or []
        top_behavior = top[0]["behavior"] if top else "distractions"

        # I match Phase 9 bands: below 70 = High risk, 70–79 Fair, 80–89 Good, 90+ Excellent
        if score < 70:
            recommendations.append({
                "rule": "high_risk_score",
                "message": (
                    f"Your safety score was high risk this week ({score}/100). "
                    f"Focus on reducing {top_behavior}."
                ),
            })
        elif score < 80:
            recommendations.append({
                "rule": "fair_score",
                "message": (
                    f"Your score was fair this week ({score}/100 — {band}). "
                    f"Try to cut down on {top_behavior}."
                ),
            })
        elif score < 90:
            recommendations.append({
                "rule": "good_score",
                "message": (
                    f"Good driving this week ({score}/100). "
                    f"Small improvements on {top_behavior} could push you to Excellent."
                ),
            })
        else:
            recommendations.append({
                "rule": "excellent_score",
                "message": f"Excellent concentration this week ({score}/100), keep it up.",
            })

        return recommendations

    def _behavior_tips_rules(self, report):
        """I add practical tips for the top 2 distraction behaviors this week."""
        recommendations = []

        # I skip tips when there is no weekly data
        if not report.get("has_data"):
            return recommendations

        top = report.get("top_contributors") or []
        # I only tip the top 2 contributors so I do not overwhelm the driver
        for item in top[:2]:
            behavior = item["behavior"]
            # I look up the tip text from config.yaml coaching.behavior_tips
            tip = self._behavior_tips.get(behavior)
            if tip:
                recommendations.append({
                    "rule": "behavior_tip_" + behavior,
                    "behavior": behavior,
                    "message": tip,
                })
        return recommendations

    def _get_week_bounds(self, end_date=None):
        """I compute a 7-day window ending on end_date (or today if None)."""
        if end_date is None:
            # I use today's date when the dashboard does not pass end_date
            end = datetime.now().date()
        else:
            # I parse strings like "2026-07-25" from the API query param
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        # I go back 6 days so start + 6 = 7 days total
        start = end - timedelta(days=6)
        # I convert to Unix timestamps so I can query SQLite start_time
        start_ts = datetime.combine(start, datetime.min.time()).timestamp()
        end_ts = datetime.combine(end, datetime.max.time()).timestamp()
        return start, end, start_ts, end_ts

    def _get_behavior_durations(self, start_ts, end_ts):
        """I sum distraction seconds per behavior between two timestamps."""
        if not self._db_path:
            raise ValueError("I need db_path to read baseline data")

        conn = sqlite3.connect(self._db_path)
        rows = conn.execute(
            """
            SELECT activity, COALESCE(SUM(duration_sec), 0) AS total_sec
            FROM activities
            WHERE start_time >= ? AND start_time <= ?
              AND activity IS NOT NULL
            GROUP BY activity
            """,
            (start_ts, end_ts),
        ).fetchall()
        conn.close()
        # I skip empty activity names and force float so math never sees None
        return {row[0]: float(row[1]) for row in rows if row[0]}

    def compute_personal_baseline(self, end_date=None):
        """I compute my average seconds/week per behavior over the prior N weeks."""
        current_start, current_end, _, _ = self._get_week_bounds(end_date)

        # I use the N full weeks BEFORE this week — I do not include this week in baseline
        baseline_end = current_start - timedelta(days=1)
        baseline_start = baseline_end - timedelta(days=7 * self._baseline_weeks - 1)

        start_ts = datetime.combine(baseline_start, datetime.min.time()).timestamp()
        end_ts = datetime.combine(baseline_end, datetime.max.time()).timestamp()

        totals = self._get_behavior_durations(start_ts, end_ts)
        # I divide total seconds by number of weeks to get "average per week"
        avg_per_week = {
            activity: round(total_sec / self._baseline_weeks, 1)
            for activity, total_sec in totals.items()
        }

        return {
            "baseline_start": baseline_start.isoformat(),
            "baseline_end": baseline_end.isoformat(),
            "weeks": self._baseline_weeks,
            "avg_seconds_per_week": avg_per_week,
        }

    def _compare_trends(self, this_week_sec, baseline_sec_per_week):
        """I compare this week's seconds to baseline and flag increased/improved."""
        trends = []
        # I union both dict keys so I check every behavior that appears in either week
        behaviors = set(this_week_sec) | set(baseline_sec_per_week)

        for behavior in behaviors:
            current = this_week_sec.get(behavior, 0.0)
            base = baseline_sec_per_week.get(behavior, 0.0)
            # I skip when baseline is 0 — I cannot say "increased vs usual" with no history
            if base <= 0:
                continue

            ratio = current / base
            if ratio >= self._increase_threshold:
                trends.append({
                    "behavior": behavior,
                    "trend": "increased",
                    "this_week_sec": round(current, 1),
                    "baseline_sec": round(base, 1),
                    "ratio": round(ratio, 2),
                })
            elif ratio <= self._improve_threshold:
                trends.append({
                    "behavior": behavior,
                    "trend": "improved",
                    "this_week_sec": round(current, 1),
                    "baseline_sec": round(base, 1),
                    "ratio": round(ratio, 2),
                })

        return trends

    def compute_trend_flags(self, end_date=None):
        """I load this week + baseline from SQLite, then run _compare_trends."""
        _, _, start_ts, end_ts = self._get_week_bounds(end_date)
        # I get how many seconds I spent in each behavior THIS week
        this_week = self._get_behavior_durations(start_ts, end_ts)
        # I get my rolling average from the prior baseline_weeks
        baseline = self.compute_personal_baseline(end_date)["avg_seconds_per_week"]
        return self._compare_trends(this_week, baseline)

    def _trend_rules(self, trends):
        """I turn trend flags into coaching messages the driver can read."""
        recommendations = []

        for item in trends:
            behavior = item["behavior"]
            if item["trend"] == "increased":
                # I warn when a behavior jumped above my usual pattern
                recommendations.append({
                    "rule": "trend_increased_" + behavior,
                    "behavior": behavior,
                    "message": (
                        f"{behavior} increased compared to your usual pattern "
                        f"({item['this_week_sec']}s this week vs "
                        f"{item['baseline_sec']}s/week baseline)."
                    ),
                })
            elif item["trend"] == "improved":
                # I praise when a behavior dropped below my usual pattern
                recommendations.append({
                    "rule": "trend_improved_" + behavior,
                    "behavior": behavior,
                    "message": (
                        f"{behavior} improved compared to your usual pattern, keep it up."
                    ),
                })

        return recommendations

    def generate_weekly_coaching(self, weekly_report, end_date=None):
        """I combine score rules, behavior tips, and trend messages into one report."""
        # I read trend flags from SQLite for the same week as the score report
        trends = self.compute_trend_flags(end_date)
        baseline = self.compute_personal_baseline(end_date)

        recommendations = []
        # I start with the overall score band message (Excellent, Fair, etc.)
        recommendations.extend(self._score_band_rules(weekly_report))
        # I add practical tips for the top 2 risk behaviors
        recommendations.extend(self._behavior_tips_rules(weekly_report))
        # I add personal trend messages (increased / improved vs baseline)
        recommendations.extend(self._trend_rules(trends))

        # I return one JSON object the dashboard can show in Step 10.7
        return {
            "week_start": weekly_report.get("week_start"),
            "week_end": weekly_report.get("week_end"),
            "has_data": weekly_report.get("has_data", False),
            "safety_score": weekly_report.get("safety_score"),
            "band": weekly_report.get("band"),
            "top_contributors": weekly_report.get("top_contributors", []),
            "baseline": baseline,
            "trends": trends,
            "recommendations": recommendations,
        }
