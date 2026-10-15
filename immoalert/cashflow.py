"""Überschuss-Rechnung (monatlicher Cashflow vor Steuern)."""

from dataclasses import dataclass


@dataclass
class Assumptions:
    rent_per_sqm: float = 11.0
    equity: float = 30000.0
    interest_pct: float = 3.8
    repayment_pct: float = 2.0
    closing_pct: float = 10.0
    costs_pct: float = 15.0


@dataclass
class Result:
    rent: float
    rent_estimated: bool
    loan: float
    loan_payment: float
    costs: float
    cashflow: float
    gross_yield_pct: float


def calculate(price, size_sqm, a: Assumptions, actual_rent=None):
    """Gibt None zurück, wenn weder Miete noch Fläche bekannt sind."""
    if not price:
        return None
    if actual_rent:
        rent, estimated = float(actual_rent), False
    elif size_sqm:
        rent, estimated = size_sqm * a.rent_per_sqm, True
    else:
        return None

    loan = max(0.0, price * (1 + a.closing_pct / 100) - a.equity)
    loan_payment = loan * (a.interest_pct + a.repayment_pct) / 100 / 12
    costs = rent * a.costs_pct / 100
    return Result(
        rent=round(rent, 2),
        rent_estimated=estimated,
        loan=round(loan, 2),
        loan_payment=round(loan_payment, 2),
        costs=round(costs, 2),
        cashflow=round(rent - loan_payment - costs, 2),
        gross_yield_pct=round(rent * 12 / price * 100, 2),
    )
