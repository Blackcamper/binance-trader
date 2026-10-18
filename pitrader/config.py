"""Load the run config and fingerprint it.

The config is locked for a run: its hash is written to the journal at start, and
the simulator refuses to continue a run whose config has changed (D22, lens 2).
"""

import hashlib
import json

STRATEGY_TYPES = ("buy_and_hold", "dca", "ema_cross", "donchian", "momentum")
REQUIRED = ("run_name", "capital_dkk", "eur_dkk", "poll_seconds", "taker_fee",
            "extra_slippage_bps", "depth_count", "tax_scenarios", "debt_baseline",
            "strategies")


class ConfigError(ValueError):
    pass


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    validate(cfg)
    return cfg


def validate(cfg):
    for key in REQUIRED:
        if key not in cfg:
            raise ConfigError("missing config key: %s" % key)
    if not 0 <= cfg["taker_fee"] < 0.1:
        raise ConfigError("taker_fee looks wrong: %r" % cfg["taker_fee"])
    ids = set()
    for s in cfg["strategies"]:
        if s.get("type") not in STRATEGY_TYPES:
            raise ConfigError("unknown strategy type: %r" % s.get("type"))
        if s["id"] in ids:
            raise ConfigError("duplicate strategy id: %s" % s["id"])
        ids.add(s["id"])
    for name, sc in cfg["tax_scenarios"].items():
        if "gain_rate" not in sc or "loss_value_rate" not in sc:
            raise ConfigError("tax scenario %s needs gain_rate and loss_value_rate" % name)


def fingerprint(cfg):
    canonical = json.dumps(cfg, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def pairs(cfg):
    return sorted({s["pair"] for s in cfg["strategies"]})
