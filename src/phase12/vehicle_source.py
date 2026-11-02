# Phase 12 — I choose mock keyboard vs real OBD for DriveContext inputs
import logging

from src.phase12.drive_context import DriveContext
from src.phase12.obd_speed_provider import ObdSpeedProvider

logger = logging.getLogger(__name__)


def create_vehicle_source(drive_gating_cfg):
    """
    I open the configured vehicle source.

    Returns (source_name, obd_provider, mock_enabled)
      source_name:  "obd" or "mock"
      obd_provider: ObdSpeedProvider or None
      mock_enabled: True only when laptop +/- keys should work
    """
    source = str(drive_gating_cfg.get("source", "mock")).lower()
    mock_cfg = drive_gating_cfg.get("mock", {}) or {}
    obd_cfg = drive_gating_cfg.get("obd", {}) or {}
    fallback = bool(obd_cfg.get("fallback_to_mock", True))

    if source != "obd":
        logger.info("Vehicle source: mock (keyboard +/- and i)")
        return "mock", None, True

    provider = ObdSpeedProvider(
        port=obd_cfg.get("port") or None,
        baudrate=obd_cfg.get("baudrate"),
        timeout=obd_cfg.get("timeout", 0.2),
        delay_cmds=obd_cfg.get("poll_interval_sec", 0.25),
        rpm_run_threshold=obd_cfg.get("rpm_run_threshold", 400),
    )
    if provider.connect():
        logger.info("Vehicle source: OBD (keyboard speed keys disabled)")
        return "obd", provider, False

    if fallback:
        logger.warning(
            "OBD failed (%s) — falling back to mock keyboard. "
            "Set drive_gating.obd.fallback_to_mock: false to require a real adapter.",
            provider._last_error or "not connected",
        )
        provider.close()
        return "mock", None, True

    logger.error("OBD required and not connected. Laptop +/- will not work.")
    return "obd", None, False


def ignition_from_config(mock_cfg):
    value = mock_cfg.get("default_ignition", DriveContext.IGNITION_RUN)
    return value
