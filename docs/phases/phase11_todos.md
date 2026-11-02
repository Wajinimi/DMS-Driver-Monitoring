# Phase 11 — Weekly insights to driver (email first)

**Goal:** Send the same weekly score + coaching the dashboard shows, to the driver's **email**.

**Input:** Output of `RecommendationEngine.generate_weekly_coaching()`.

**Output:** Plain-text (and later HTML) email body ready to send.

---

## TODO checklist

| Step | What we build | Status |
|------|---------------|--------|
| 1 | `WeeklyReportFormatter` — coaching JSON → email text | ⬜ |
| 2 | `ResendSender` — send via Resend API (no SMTP) | ✅ |
| 3 | `send_weekly_report.py` — CLI + test | ✅ |
| 4 | `weekly_delivery` in `config.yaml` | ⬜ |
| 5 | Optional: schedule (cron / launchd) | ⬜ |
| 6 | SMS via Twilio (later) | ⬜ |

---

## Success criteria

1. Given a week with trip data, driver receives one email with score, band, and coaching tips.
2. No secrets in git (SMTP password via environment variable).
3. Driver has opted in (documented in consent flow).
