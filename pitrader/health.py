"""Pi health probes. Each returns None when the tool is not available (e.g. on a PC)."""

import subprocess


def _run(args):
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip()


def ntp_synced():
    """True/False from systemd; None if timedatectl is missing. The Pi Zero has no
    real-time clock, so trading is gated until the clock is synced (lens 2, 9)."""
    v = _run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"])
    if v is None:
        return None
    return v == "yes"


def throttled():
    """Raw `vcgencmd get_throttled` value, e.g. '0x0'. Bit 0 = undervoltage now,
    bit 16 = undervoltage since boot."""
    v = _run(["vcgencmd", "get_throttled"])
    if v is None or "=" not in v:
        return None
    return v.split("=", 1)[1]


def check():
    return {"ntp_synced": ntp_synced(), "throttled": throttled()}
