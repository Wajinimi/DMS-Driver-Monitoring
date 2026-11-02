# Phase 11 — I turn the weekly coaching report into an email the driver can read on their phone


class WeeklyReportFormatter:
    def __init__(self, driver_name="Driver", dashboard_url=None):
        self._driver_name = driver_name #i am storing the driver name for a personal greeting in the email
        self._dashboard_url = dashboard_url #i am adding a link to the full dashboard at the bottom

    def format_subject(self, coaching_report):
        """I build the email subject line from the week and score."""
        week_end = coaching_report.get("week_end", "")
        if not coaching_report.get("has_data"):
            return f"Your weekly driving report — week ending {week_end}"

        score = coaching_report.get("safety_score")
        band = coaching_report.get("band", "")
        return f"Weekly safety report: {score}/100 ({band}) — week ending {week_end}"

    def format_plain_text(self, coaching_report):
        """I build the full email body as plain text."""
        lines = []
        lines.append(f"Hi {self._driver_name},")
        lines.append("")
        lines.append("Here is your weekly driver safety summary.")
        lines.append("")

        week_start = coaching_report.get("week_start", "")
        week_end = coaching_report.get("week_end", "")
        lines.append(f"Week: {week_start} to {week_end}")
        lines.append("")

        if not coaching_report.get("has_data"):
            lines.append("No driving data was recorded this week.")
            lines.append("Take a trip with the DMS running to get a score next week.")
        else:
            score = coaching_report.get("safety_score")
            band = coaching_report.get("band", "")
            lines.append(f"Safety score: {score} / 100 — {band}")
            lines.append("")

            top = coaching_report.get("top_contributors") or []
            if top:
                lines.append("Top risk contributors:")
                for item in top:
                    behavior = item.get("behavior", "")
                    pct = item.get("pct_of_total_risk", "")
                    lines.append(f"  • {behavior} ({pct}% of total risk)")
                lines.append("")

            recs = coaching_report.get("recommendations") or []
            if recs:
                lines.append("Coaching tips:")
                for rec in recs:
                    lines.append(f"  • {rec['message']}")
                lines.append("")

        if self._dashboard_url:
            lines.append(f"View full dashboard: {self._dashboard_url}")

        lines.append("")
        lines.append("Drive safely,")
        lines.append("Your DMS Coach")

        return "\n".join(lines)
