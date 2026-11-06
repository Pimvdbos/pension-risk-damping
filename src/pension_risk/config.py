"""Illustrative contract choices from Appendix A.3-A.11."""

from dataclasses import dataclass

GRID = (25, 35, 45, 55, 67)
MECHS = ("spreading", "reserve", "hedge", "lifecycle")
FULL = dict.fromkeys(MECHS, True)


@dataclass(frozen=True)
class Settings:
    entry_age: int = 25
    retirement_age: int = 68
    end_age: int = 95
    contribution: float = 1.0
    projection: float = 0.03
    spread_years: int = 5
    fill_rate: float = 0.25
    reserve_cap: float = 2.0

    @property
    def pay_years(self):
        return self.end_age - self.retirement_age
