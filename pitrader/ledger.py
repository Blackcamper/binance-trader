"""Per-strategy virtual account with FIFO lots and a Danish tax shadow ledger.

Amounts are kept in EUR (Kraken EUR pairs) and converted to DKK at a fixed rate for
reporting. Buy fees go into the cost basis, sell fees reduce the proceeds.

Tax model (docs/research/S2-r3-skat-selvangivelse.md): every sale is a realisation,
FIFO per coin, and each sale is settled on its own. Gains are summed and taxed at
gain_rate (personal income, rubrik 20); losses are summed and are only worth
loss_value_rate (ligningsmæssigt fradrag, rubrik 58). A loss never cancels a gain at
the full rate. "After-tax equity" also taxes the open position as if sold at the
current bid, so buy-and-hold carries its notional tax too.
"""

import time
from collections import deque


def year_of(ts):
    return time.gmtime(ts).tm_year


class Book:
    def __init__(self, cash_eur):
        self.start_eur = cash_eur
        self.cash = cash_eur
        self.lots = deque()          # [qty, cost_eur, bought_ts] per lot, oldest first
        self.fees = 0.0
        self.buys = 0
        self.sells = 0
        self.realised = {}           # year -> net realised gain EUR
        self.disposals = []          # one dict per sale, for the tax report

    @property
    def qty(self):
        return sum(l[0] for l in self.lots)

    def buy(self, qty, gross_eur, fee_eur, ts=None):
        self.cash -= gross_eur + fee_eur
        if self.cash < -1e-6:
            raise ValueError("buy exceeds cash")
        self.cash = max(self.cash, 0.0)
        self.lots.append([qty, gross_eur + fee_eur, ts])
        self.fees += fee_eur
        self.buys += 1

    def sell(self, qty, gross_eur, fee_eur, ts):
        if qty > self.qty * (1 + 1e-9):
            raise ValueError("sell exceeds holding")
        net = gross_eur - fee_eur
        cost = 0.0
        left = qty
        first_bought = self.lots[0][2] if self.lots else None
        while left > 1e-15 and self.lots:
            lot = self.lots[0]
            take = min(lot[0], left)
            part = lot[1] * take / lot[0]
            cost += part
            lot[0] -= take
            lot[1] -= part
            left -= take
            if lot[0] <= 1e-15:
                self.lots.popleft()
        y = year_of(ts)
        self.realised[y] = self.realised.get(y, 0.0) + net - cost
        self.disposals.append({"t": ts, "qty": qty, "proceeds": net, "cost": cost,
                               "fee": fee_eur, "gain": net - cost,
                               "first_bought": first_bought})
        self.cash += net
        self.fees += fee_eur
        self.sells += 1

    def cost_basis(self):
        return sum(l[1] for l in self.lots)

    def value(self, bid):
        return self.cash + self.qty * bid

    def tax(self, bid, fee_rate, scenario, now):
        """Tax owed (negative = deduction value) if everything were sold now at bid."""
        gains = [d["gain"] for d in self.disposals]
        q = self.qty
        if q > 0:
            gains.append(q * bid * (1 - fee_rate) - self.cost_basis())
        total = 0.0
        for g in gains:
            total += g * (scenario["gain_rate"] if g > 0 else scenario["loss_value_rate"])
        return total

    def after_tax_value(self, bid, fee_rate, scenario, now):
        """Liquidation value after sell fee and tax."""
        q = self.qty
        liquid = self.cash + q * bid * (1 - fee_rate)
        return liquid - self.tax(bid, fee_rate, scenario, now)


def walk_buy(asks, budget_eur, fee_rate, slip):
    """Spend budget_eur (fee included) walking the ask side.
    Returns (qty, gross_eur, fee_eur, avg_price, exhausted)."""
    gross_budget = budget_eur / (1 + fee_rate)
    spent = 0.0
    qty = 0.0
    exhausted = True
    for price, vol in asks:
        room = gross_budget - spent
        take = min(vol, room / price)
        qty += take
        spent += take * price
        if spent >= gross_budget * (1 - 1e-12):
            exhausted = False
            break
    if exhausted and asks:
        # book too thin: rest at the worst seen level plus 1% penalty
        worst = asks[-1][0] * 1.01
        qty += (gross_budget - spent) / worst
    if qty <= 0:
        raise ValueError("no ask liquidity")
    vwap = gross_budget / qty
    price = vwap * (1 + slip)
    qty = gross_budget / price
    return qty, gross_budget, gross_budget * fee_rate, price, exhausted


def walk_sell(bids, qty, fee_rate, slip):
    """Sell qty walking the bid side. Returns (qty, gross_eur, fee_eur, avg_price, exhausted)."""
    left = qty
    gross = 0.0
    exhausted = True
    for price, vol in bids:
        take = min(vol, left)
        gross += take * price
        left -= take
        if left <= qty * 1e-12:
            exhausted = False
            break
    if exhausted and bids:
        gross += left * bids[-1][0] * 0.99
    if gross <= 0:
        raise ValueError("no bid liquidity")
    price = gross / qty * (1 - slip)
    gross = qty * price
    return qty, gross, gross * fee_rate, price, exhausted
