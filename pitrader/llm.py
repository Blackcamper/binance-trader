"""Daily status text from the local model on the NAS (Ollama, no key).

Runs as its own job (systemd timer), never inside the trading loop. The code works
out every number; the model only phrases them. If the model does not answer, the
job writes the status without model text and exits 0, so nothing else depends on it.
Settings live in config/llm.json, outside the locked run config.
"""

import json
import os
import time
import urllib.request

from .journal import write_atomic

SYSTEM = ("Du skriver en kort dansk status om en papirhandels-simulering med virtuelle "
          "penge. Brug kun de tal du får, regn ikke selv, og find ikke på tal. "
          "Maks 5 linjer. Ingen investeringsråd.")


def load_settings(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ask(settings, prompt, system=SYSTEM, opener=urllib.request.urlopen):
    body = {"model": settings["model"], "stream": False,
            # same num_ctx as Home Assistant, otherwise the NAS reloads the model (>1 min)
            "options": {"num_ctx": settings.get("num_ctx", 8192)},
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}]}
    req = urllib.request.Request(settings["url"], data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    try:
        with opener(req, timeout=settings.get("timeout", 180)) as r:
            return json.loads(r.read().decode("utf-8"))["message"]["content"].strip()
    except Exception:
        return None


def facts(status):
    """The few numbers the model may use, all computed here."""
    rows = status.get("strategies") or []
    ranked = sorted(rows, key=lambda r: r["after_tax_liquidation_dkk"].get("high", 0),
                    reverse=True)
    return {
        "dag": status.get("day"),
        "fase": status.get("phase"),
        "seneste_heartbeat_utc": status.get("heartbeat_utc"),
        "handel_aktiv": status.get("health", {}).get("trading_enabled"),
        "fejlede_polls": status.get("health", {}).get("polls_failed"),
        "startkapital_dkk": status.get("assumptions", {}).get("capital_dkk"),
        "strategier": [{"navn": r["id"], "vaerdi_dkk": r["equity_dkk"],
                        "afkast_pct": r["return_pct"],
                        "efter_skat_hoej_dkk": r["after_tax_liquidation_dkk"].get("high"),
                        "max_drawdown_pct": r["max_drawdown_pct"],
                        "handler": r["buys"] + r["sells"]} for r in ranked],
        "alternativ_afdrag_gaeld_dkk": status.get("baseline_debt_paydown_dkk"),
    }


def daily_summary(data_dir, settings, opener=urllib.request.urlopen, clock=time.time):
    with open(os.path.join(data_dir, "status.json"), "r", encoding="utf-8") as f:
        status = json.load(f)
    f_ = facts(status)
    text = ask(settings, "Skriv dagens status ud fra disse tal (JSON). Nævn bedste og "
                         "dårligste strategi og om systemet kører fejlfrit:\n"
                         + json.dumps(f_, ensure_ascii=False), opener=opener)
    out = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(clock())),
           "model": settings["model"], "llm_ok": text is not None,
           "text": text, "facts": f_}
    write_atomic(os.path.join(data_dir, "llm-summary.json"),
                 json.dumps(out, indent=1, ensure_ascii=False))
    return out
