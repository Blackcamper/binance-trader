"""What would go on the Danish tax return (årsopgørelse) if a strategy's paper trades
had been real. Read-only: rebuilt from the journal, nothing is sent anywhere.

Rules and sources: docs/research/S2-r3-skat-selvangivelse.md. Each sale is settled on
its own (FIFO cost): gains are added up for rubrik 20, losses for rubrik 58. Amounts
are converted at the run's fixed eur_dkk; a real return needs the rate of each trade
day. Each strategy is its own virtual account. In real life one person has a single
FIFO pool per coin across all exchanges and wallets.
"""

import csv
import time

from .ledger import year_of

RUBRIK_GAIN = (20, "Anden personlig indkomst")
RUBRIK_LOSS = (58, "Øvrige lønmodtagerudgifter")


def day(ts):
    return time.strftime("%Y-%m-%d", time.gmtime(ts)) if ts is not None else "?"


def kr(x):
    # Danish thousands separator, whole kroner as on the return
    return "{:,.0f}".format(x).replace(",", ".")


def breakeven(scenario):
    """How many kr of gains it takes to cover 1 kr of losses after tax."""
    return (1 - scenario["loss_value_rate"]) / (1 - scenario["gain_rate"])


def year_report(book, strat, cfg, year, bid=None, now=None):
    """Sales in `year` for one strategy, in DKK, plus the two rubrik totals."""
    rate = cfg["eur_dkk"]
    sales = []
    for d in book.disposals:
        if year_of(d["t"]) != year:
            continue
        sales.append({
            "date": day(d["t"]), "first_bought": day(d["first_bought"]),
            "pair": strat["pair"], "qty": d["qty"],
            "proceeds_dkk": d["proceeds"] * rate, "cost_dkk": d["cost"] * rate,
            "fee_dkk": d["fee"] * rate, "gain_dkk": d["gain"] * rate,
        })
    gains = sum(s["gain_dkk"] for s in sales if s["gain_dkk"] > 0)
    losses = -sum(s["gain_dkk"] for s in sales if s["gain_dkk"] < 0)
    rep = {
        "year": year, "id": strat["id"], "pair": strat["pair"], "sales": sales,
        "n_gain": sum(1 for s in sales if s["gain_dkk"] > 0),
        "n_loss": sum(1 for s in sales if s["gain_dkk"] < 0),
        "rubrik20_dkk": round(gains), "rubrik58_dkk": round(losses),
        "tax_dkk": {name: round(gains * sc["gain_rate"] - losses * sc["loss_value_rate"])
                    for name, sc in cfg["tax_scenarios"].items()},
        "net_if_netted_dkk": round(gains - losses),
    }
    if book.qty > 0:
        rep["open"] = {"qty": book.qty, "cost_dkk": book.cost_basis() * rate}
        if bid is not None:
            rep["open"]["value_dkk"] = book.qty * bid * rate
    return rep


def render(rep, cfg):
    sc = cfg["tax_scenarios"]
    L = []
    L.append("SKAT %d  strategi %s (%s)  PAPIRHANDEL, ikke rigtige penge"
             % (rep["year"], rep["id"], rep["pair"]))
    L.append("Salg i året: %d  (%d med gevinst, %d med tab)"
             % (len(rep["sales"]), rep["n_gain"], rep["n_loss"]))
    L.append("")
    L.append("Til årsopgørelsen (TastSelv), hele kroner:")
    L.append("  Rubrik %d  %-28s %10s kr   (summen af alle gevinster)"
             % (RUBRIK_GAIN[0], RUBRIK_GAIN[1], kr(rep["rubrik20_dkk"])))
    L.append("  Rubrik %d  %-28s %10s kr   (summen af alle tab)"
             % (RUBRIK_LOSS[0], RUBRIK_LOSS[1], kr(rep["rubrik58_dkk"])))
    L.append("")
    L.append("Anslået skat (gevinst x skattesats, minus tab x fradragsværdi):")
    for name, tax in sorted(rep["tax_dkk"].items()):
        L.append("  %-5s gevinst %2.0f%%, tab %2.0f%%: %10s kr" % (
            name, sc[name]["gain_rate"] * 100, sc[name]["loss_value_rate"] * 100, kr(tax)))
    diff = rep["rubrik20_dkk"] - rep["rubrik58_dkk"]
    L.append("  Netto handelsresultat %s kr. Gevinst og tab må ikke modregnes, så tabet"
             % kr(diff))
    L.append("  er mindre værd end gevinsten beskattes med. Gevinsterne skal være")
    L.append("  " + ", ".join("%.2f x (%s)" % (breakeven(c), n) for n, c in sorted(sc.items()))
             + " tabene for at gå i nul efter skat.")
    if rep.get("open"):
        o = rep["open"]
        line = "Åben beholdning: %.8f, anskaffet for %s kr" % (o["qty"], kr(o["cost_dkk"]))
        if "value_dkk" in o:
            line += ", værdi nu %s kr" % kr(o["value_dkk"])
        L.append(line + ". Ikke skattepligtig før den sælges.")
    if rep["sales"]:
        L.append("")
        L.append("%-10s %-10s %12s %12s %12s %8s %11s" % (
            "solgt", "købt", "mængde", "salgssum", "anskaffelse", "gebyr", "gevinst"))
        for s in rep["sales"]:
            L.append("%-10s %-10s %12.8f %12s %12s %8s %11s" % (
                s["date"], s["first_bought"], s["qty"], kr(s["proceeds_dkk"]),
                kr(s["cost_dkk"]), kr(s["fee_dkk"]), kr(s["gain_dkk"])))
        L.append("Salgssum er efter salgsgebyr; anskaffelse er inkl. købsgebyr (FIFO).")
    L.append("Kurs EUR/DKK %.5f fast for kørslen. Ikke skatterådgivning." % cfg["eur_dkk"])
    return "\n".join(L) + "\n"


def write_csv(reports, path):
    fields = ["strategy", "pair", "sold", "first_bought", "qty", "proceeds_dkk",
              "cost_dkk", "fee_dkk", "gain_dkk"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(fields)
        for rep in reports:
            for s in rep["sales"]:
                w.writerow([rep["id"], s["pair"], s["date"], s["first_bought"],
                            "%.8f" % s["qty"], "%.2f" % s["proceeds_dkk"],
                            "%.2f" % s["cost_dkk"], "%.2f" % s["fee_dkk"],
                            "%.2f" % s["gain_dkk"]])
