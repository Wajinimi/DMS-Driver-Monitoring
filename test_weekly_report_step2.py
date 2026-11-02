# Phase 11 Step 2 — I test Resend delivery (dry-run by default)
import os
import sys

import yaml

END_DATE = None
if "--end-date" in sys.argv:
    idx = sys.argv.index("--end-date")
    if idx + 1 >= len(sys.argv):
        print("ERROR: --end-date requires YYYY-MM-DD (e.g. 2026-07-25 for old test data).")
        sys.exit(1)
    END_DATE = sys.argv[idx + 1]

from src.phase9.safety_score_engine import SafetyScoreEngine
from src.phase10.recommendation_engine import RecommendationEngine
from src.phase11.resend_sender import ResendSender
from src.phase11.weekly_report_formatter import WeeklyReportFormatter

with open("config.yaml") as f:
    config = yaml.safe_load(f)

delivery = config["weekly_delivery"]
resend_cfg = delivery["resend"]
driver = delivery["driver"]

score_engine = SafetyScoreEngine(
    weights=config["safety_score"]["weights"],
    scale_factor=config["safety_score"]["scale_factor"],
    bands=config["safety_score"]["bands"],
    exposure_unit=config["safety_score"]["exposure_unit"],
    db_path=config["analytics"]["db_path"],
)
coach_engine = RecommendationEngine(
    behavior_tips=config["coaching"]["behavior_tips"],
    baseline_weeks=config["coaching"]["baseline_weeks"],
    increase_threshold=config["coaching"]["increase_threshold"],
    improve_threshold=config["coaching"]["improve_threshold"],
    db_path=config["analytics"]["db_path"],
)

weekly = score_engine.compute_weekly_score(end_date=END_DATE)
coaching = coach_engine.generate_weekly_coaching(weekly, end_date=END_DATE)

formatter = WeeklyReportFormatter(
    driver_name=driver["name"],
    dashboard_url=delivery.get("dashboard_url"),
)
subject = formatter.format_subject(coaching)
body = formatter.format_plain_text(coaching)

print("Week:", coaching.get("week_start"), "to", coaching.get("week_end"))
print("From:", resend_cfg.get("from_name"), resend_cfg["from_address"])
print("To:", driver["email"])
print("Subject:", subject)
print()
print(body)
print()

if "--send" not in sys.argv:
    print("Dry run only. To send for real:")
    print("  export DMS_RESEND_API_KEY='re_...'")
    print("  python3 test_weekly_report_step2.py --send")
    print("Optional (old SQLite test week only):")
    print("  python3 test_weekly_report_step2.py --end-date 2026-07-25 --send")
    sys.exit(0)

if not os.environ.get("DMS_RESEND_API_KEY"):
    print("ERROR: Set DMS_RESEND_API_KEY first (your Resend API key).")
    sys.exit(1)

sender = ResendSender(
    from_address=resend_cfg["from_address"],
    from_name=resend_cfg.get("from_name"),
    api_key_env=resend_cfg.get("api_key_env", "DMS_RESEND_API_KEY"),
)
result = sender.send(driver["email"], subject, body)
print("Email sent. Resend id:", result.get("id"))
