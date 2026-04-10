from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass


@dataclass
class TurnRecord:
    turn: int
    price: float
    cap: float | None
    production: int
    demand: int
    sold: int
    wasted: int
    revenue: float
    total_cost: float
    profit: float
    vault: float

    def to_display_dict(self) -> dict[str, object]:
        cap_text = "-" if self.cap is None else round(self.cap, 2)
        return {
            "Turn": self.turn,
            "Price": round(self.price, 2),
            "Cap": cap_text,
            "Production": self.production,
            "Demand": self.demand,
            "Sold": self.sold,
            "Profit": round(self.profit, 2),
            "Vault": round(self.vault, 2),
        }


class MilkMarketGame:
    def __init__(self) -> None:
        self.random = random.Random()
        self.reference_price = 1.60
        self.cost_per_unit = 1.20
        self.fixed_cost = 180.0
        self.waste_cost = 0.12
        self.starting_vault = 3200.0
        self.market_max_price = 4.00
        self.price_floor = 0.01
        self.max_production = 2000
        self.reset()

    def reset(self) -> None:
        self.turn = 1
        self.vault = self.starting_vault
        self.history: list[TurnRecord] = []
        self.price_cap: float | None = None
        self.initial_cap: float | None = None
        self.government_started = False
        self.last_price = 1.55
        self.bankrupt = False
        self.cumulative_profit = 0.0
        self.baseline_demand = 760
        self.forecast_baseline = 760
        self.elasticity = 1.40
        self.current_news = (
            "The dairy opens in a free market. No legal ceiling exists yet, and consumers remain highly sensitive to price."
        )
        self._prepare_turn(initial=True)

    @property
    def phase_label(self) -> str:
        if self.price_cap is None:
            return "Free market"
        if self.price_cap >= self.cost_per_unit:
            return "Managed market"
        return "Confiscatory cap"

    @property
    def turns_survived(self) -> int:
        return max(0, self.turn - 1)

    def cap_to_cost_ratio(self) -> float | None:
        if self.price_cap is None:
            return None
        return self.price_cap / self.cost_per_unit

    def policy_pressure(self) -> float:
        if self.price_cap is None or self.initial_cap is None:
            return 0.0
        if self.price_cap <= self.cost_per_unit:
            return 100.0
        denominator = max(0.01, self.initial_cap - self.cost_per_unit)
        consumed = self.initial_cap - self.price_cap
        return max(0.0, min(100.0, consumed / denominator * 100.0))

    def allowed_price_max(self) -> float:
        if self.price_cap is None:
            return self.market_max_price
        return max(self.price_floor, min(self.market_max_price, self.price_cap))

    def _advance_regulation(self) -> None:
        if self.turn == 6 and self.history:
            self.government_started = True
            self.price_cap = round(self.last_price * 1.10, 2)
            self.initial_cap = self.price_cap
            self.current_news = (
                f"The government imposes a price ceiling at ${self.price_cap:.2f}. It looks harmless at first, because it still floats above cost."
            )
        elif self.turn > 6 and self.government_started and self.price_cap is not None:
            previous = self.price_cap
            self.price_cap = max(self.price_floor, round(self.price_cap * 0.90, 2))
            if previous >= self.cost_per_unit > self.price_cap:
                self.current_news = (
                    f"The legal ceiling falls to ${self.price_cap:.2f}, below the ${self.cost_per_unit:.2f} unit cost. The law now commands losses."
                )
            else:
                relation = "above" if self.price_cap >= self.cost_per_unit else "below"
                self.current_news = (
                    f"The state tightens the ceiling to ${self.price_cap:.2f}, still {relation} cost. Margins are squeezed harder this turn."
                )

    def _prepare_turn(self, initial: bool = False) -> None:
        if not initial:
            self._advance_regulation()
        phase = (self.turn - 1) / 2.4
        seasonal = 110 * math.sin(phase) + 35 * math.cos(phase / 2.2)
        market_noise = self.random.randint(-55, 55)
        self.elasticity = round(1.15 + self.random.random() * 0.95, 2)
        self.baseline_demand = max(260, int(790 + seasonal + market_noise))
        forecast_error = self.random.randint(-70, 70)
        self.forecast_baseline = max(230, self.baseline_demand + forecast_error)

    def demand_for_price(self, price: float) -> int:
        price = max(self.price_floor, price)
        raw = self.baseline_demand * (self.reference_price / price) ** self.elasticity
        return max(0, int(round(raw)))

    def forecast_for_price(self, price: float) -> int:
        price = max(self.price_floor, price)
        raw = self.forecast_baseline * (self.reference_price / price) ** self.elasticity
        return max(0, int(round(raw)))

    def estimate_turn(self, production: int, chosen_price: float) -> dict[str, float | int]:
        chosen_price = min(max(self.price_floor, chosen_price), self.allowed_price_max())
        production = max(0, min(self.max_production, int(production)))
        demand = self.forecast_for_price(chosen_price)
        sold = min(production, demand)
        wasted = max(0, production - sold)
        revenue = sold * chosen_price
        total_cost = production * self.cost_per_unit + self.fixed_cost + wasted * self.waste_cost
        profit = revenue - total_cost
        return {
            "demand": demand,
            "sold": sold,
            "wasted": wasted,
            "revenue": revenue,
            "total_cost": total_cost,
            "profit": profit,
        }

    def recommended_controls(self) -> tuple[int, float]:
        best_profit = float("-inf")
        best_prod = 0
        best_price = min(max(self.reference_price, self.price_floor), self.allowed_price_max())
        max_price = self.allowed_price_max()
        steps = max(2, int(round((max_price - self.price_floor) / 0.03)))
        for i in range(steps + 1):
            price = round(self.price_floor + i * 0.03, 2)
            price = min(price, max_price)
            demand = self.forecast_for_price(price)
            if price > self.cost_per_unit:
                production = min(self.max_production, int(round(demand / 10) * 10))
            else:
                production = 0
            estimate = self.estimate_turn(production, price)
            profit = float(estimate["profit"])
            if profit > best_profit:
                best_profit = profit
                best_prod = production
                best_price = price
        return best_prod, round(best_price, 2)

    def resolve_turn(self, production: int, chosen_price: float) -> TurnRecord:
        chosen_price = min(max(self.price_floor, round(chosen_price, 2)), self.allowed_price_max())
        production = max(0, min(self.max_production, int(production)))

        demand = self.demand_for_price(chosen_price)
        sold = min(production, demand)
        wasted = max(0, production - sold)

        revenue = sold * chosen_price
        production_cost = production * self.cost_per_unit
        waste_penalty = wasted * self.waste_cost
        total_cost = production_cost + self.fixed_cost + waste_penalty
        profit = revenue - total_cost
        self.vault += profit
        self.cumulative_profit += profit

        record = TurnRecord(
            turn=self.turn,
            price=chosen_price,
            cap=self.price_cap,
            production=production,
            demand=demand,
            sold=sold,
            wasted=wasted,
            revenue=revenue,
            total_cost=total_cost,
            profit=profit,
            vault=self.vault,
        )
        self.history.append(record)
        self.last_price = chosen_price

        if self.price_cap is None:
            regime = "The market remains free."
        elif self.price_cap >= self.cost_per_unit:
            regime = f"The ceiling of ${self.price_cap:.2f} is binding but still above cost."
        else:
            regime = f"The ceiling of ${self.price_cap:.2f} is below cost, so every compliant sale destroys capital."

        self.current_news = (
            f"Turn {record.turn}: you priced at ${record.price:.2f}, produced {record.production:,}, sold {record.sold:,}, "
            f"and posted {'profit' if record.profit >= 0 else 'loss'} of ${abs(record.profit):,.2f}. {regime}"
        )

        self.turn += 1
        self.bankrupt = self.vault <= 0

        if self.bankrupt:
            self.current_news = (
                f"Turn {record.turn}: the vault falls to ${self.vault:,.2f}. The dairy is bankrupt."
            )
        else:
            self._prepare_turn()

        return record

    def game_over(self) -> bool:
        return self.bankrupt
