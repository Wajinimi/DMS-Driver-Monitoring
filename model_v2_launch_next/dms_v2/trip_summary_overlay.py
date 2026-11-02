# Phase 12 — I draw the end-of-trip summary on the webcam window
import time

import cv2
import numpy as np


def _wrap_text(text, max_chars=46):
    """i wanto splitting long coaching lines so they fit on a 640px-wide window"""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines

#turrning the report dict into short lines for the on-screen card
def build_overlay_lines(report_bundle):
    trip_summary = report_bundle["trip_summary"]
    trip_report = report_bundle["trip_report"]
    tips = report_bundle["tips"]

    duration_min = round(trip_summary.get("duration_sec", 0) / 60.0, 1)
    alert_count = trip_summary.get("alert_count", 0)

    lines = ["TRIP COMPLETE", ""]

    if trip_report["has_data"]:
        score = trip_report["safety_score"]
        band = trip_report.get("band", "")
        lines.append(f"Safety score: {score}/100 — {band}")
    else:
        lines.append("No score — monitoring never started")
        lines.append("(Reach 15 km/h to activate DMS)")

    lines.append(f"Trip time: {duration_min} min | Alerts: {alert_count}")

    top = trip_report.get("top_contributors") or []
    if top:
        item = top[0]
        behavior = item.get("behavior", "")
        pct = item.get("pct_of_total_risk", "")
        lines.append(f"Top risk: {behavior} ({pct}% of risk)")

    if tips:
        lines.append("")
        lines.append("Coaching:")
        for rec in tips:
            for wrapped in _wrap_text(rec["message"]):
                lines.append(f"  • {wrapped}")

    lines.append("")
    lines.append("Press any key to dismiss")
    return lines

#drawing a dark panel over the camera frame with summary text
def draw_trip_summary_frame(frame, lines):
    display = frame.copy()
    height, width = display.shape[:2]

    panel_top = 40
    panel_bottom = min(height - 20, panel_top + 28 * len(lines) + 30)
    overlay = display.copy()
    cv2.rectangle(overlay, (20, panel_top), (width - 20, panel_bottom), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.82, display, 0.18, 0, display)
    cv2.rectangle(display, (20, panel_top), (width - 20, panel_bottom), (0, 200, 120), 2)

    y = panel_top + 32
    for i, line in enumerate(lines):
        if i == 0:
            color = (0, 255, 180)
            scale = 0.8
            thickness = 2
        elif line.startswith("  •"):
            color = (220, 220, 220)
            scale = 0.48
            thickness = 1
        else:
            color = (255, 255, 255)
            scale = 0.55
            thickness = 1

        cv2.putText(
            display,
            line,
            (36, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        y += 26 if scale >= 0.55 else 22

    return display

  
    #I show the summary card on screen until the timer ends or the driver presses a key.
    #frame: last camera frame (or any blank image the same size)
    #display_sec: how long to wait if the driver does not press a key

def show_trip_summary_overlay(frame, report_bundle, window_name, display_sec=12):
    if frame is None:
        frame = np.zeros((480, 640, 3), dtype=np.uint8)

    lines = build_overlay_lines(report_bundle)
    summary_frame = draw_trip_summary_frame(frame, lines)
    deadline = time.time() + display_sec

    while True:
        cv2.imshow(window_name, summary_frame)
        remaining_ms = max(1, int((deadline - time.time()) * 1000))
        key = cv2.waitKey(min(remaining_ms, 100)) & 0xFF
        if key != 255:
            break
        if time.time() >= deadline:
            break
