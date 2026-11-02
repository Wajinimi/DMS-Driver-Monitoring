#!/usr/bin/env python3
"""Hardware smoke test — plug OBDLink USB in, ignition ON, then run this."""
import time

import yaml

from src.phase12.obd_speed_provider import ObdSpeedProvider


def main():
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    obd_cfg = config.get("drive_gating", {}).get("obd", {}) or {}

    print("Scanning for OBD adapter...")
    print("  port:", obd_cfg.get("port") or "auto")
    print("Turn ignition ON (engine can be idling). Ctrl+C to stop.\n")

    provider = ObdSpeedProvider(
        port=obd_cfg.get("port") or None,
        baudrate=obd_cfg.get("baudrate"),
        timeout=obd_cfg.get("timeout", 0.2),
        delay_cmds=obd_cfg.get("poll_interval_sec", 0.25),
        rpm_run_threshold=obd_cfg.get("rpm_run_threshold", 400),
    )
    if not provider.connect():
        print("FAILED:", provider._last_error)
        print()
        print("Mac USB checklist:")
        print("  1. Plug OBDLink into the car AND the Mac (USB-C adapter if needed)")
        print("  2. Ignition ON")
        print("  3. ls /dev/cu.usbserial*")
        print("  4. If you see a port, set drive_gating.obd.port in config.yaml")
        print("  5. pip install obd")
        return 1

    try:
        for _ in range(20):
            reading = provider.poll()
            print(
                "connected=%s  speed=%s km/h  rpm=%s  ignition=%s"
                % (
                    reading["connected"],
                    reading["speed_kmh"],
                    reading["rpm"],
                    reading["ignition"],
                )
            )
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        provider.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
