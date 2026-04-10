
from __future__ import annotations

import math
import random
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import messagebox, ttk


@dataclass
class TurnRecord:
    turn: int
    phase: str
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
    margin_per_unit: float
    cap_ratio: float | None


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
        self.event_log: list[str] = []
        self.baseline_demand = 760
        self.forecast_baseline = 760
        self.elasticity = 1.40
        self._prepare_turn()
        self._log(
            "The dairy opens in a free market. Consumers are price-sensitive, but the ministry has not yet entered the barn."
        )

    def _log(self, message: str) -> None:
        self.event_log.append(message)

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
            self._log(
                f"Turn {self.turn}: the government imposes a price ceiling at ${self.price_cap:.2f}. "
                "At first it looks ornamental, not lethal."
            )
        elif self.turn > 6 and self.government_started and self.price_cap is not None:
            previous = self.price_cap
            self.price_cap = max(self.price_floor, round(self.price_cap * 0.90, 2))
            if previous >= self.cost_per_unit > self.price_cap:
                self._log(
                    f"Turn {self.turn}: the legal ceiling falls to ${self.price_cap:.2f}, now below the "
                    f"${self.cost_per_unit:.2f} unit cost. The law has crossed into confiscation."
                )

    def _prepare_turn(self) -> None:
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
            phase=self.phase_label,
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
            margin_per_unit=chosen_price - self.cost_per_unit,
            cap_ratio=(self.price_cap / self.cost_per_unit) if self.price_cap is not None else None,
        )
        self.history.append(record)
        self.last_price = chosen_price

        self._log(self._compose_turn_log(record))

        self.turn += 1
        self.bankrupt = self.vault <= 0

        if self.bankrupt:
            self._log(
                f"Turn {record.turn}: the company vault falls to ${self.vault:,.2f}. The dairy collapses under the weight of its losses."
            )
        else:
            self._prepare_turn()

        return record

    def _compose_turn_log(self, record: TurnRecord) -> str:
        lead = (
            f"Turn {record.turn}: priced at ${record.price:.2f}, produced {record.production:,}, "
            f"sold {record.sold:,}, wasted {record.wasted:,}."
        )
        tail = (
            f" Revenue ${record.revenue:,.2f}; total costs ${record.total_cost:,.2f}; "
            f"profit {record.profit:+,.2f}; vault ${record.vault:,.2f}."
        )
        if record.cap is None:
            return lead + tail
        if record.cap >= self.cost_per_unit:
            return lead + " The ceiling is binding, but not yet murderous." + tail
        return lead + " The ceiling now sits below cost; each sale deepens the wound." + tail

    def game_over(self) -> bool:
        return self.bankrupt


class MilkManagerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.game = MilkMarketGame()
        self.last_rendered_log_count = 0
        self.logo_image: tk.PhotoImage | None = None
        self.logo_source: Path = Path(__file__).resolve().with_name("logo.png")

        self.root.title("Milk Manager: Price Cap Panic")
        self.root.geometry("1500x920")
        self.root.minsize(1280, 820)

        self._setup_style()
        self._load_logo()
        self._build_layout()
        self._bind_redraws()
        self._refresh_view()

    def _setup_style(self) -> None:
        self.bg = "#08111f"
        self.panel = "#0f1b2d"
        self.panel_soft = "#13233a"
        self.card = "#0b1627"
        self.soft = "#d8e1ef"
        self.muted = "#9fb0c8"
        self.green = "#22c55e"
        self.gold = "#f59e0b"
        self.red = "#ef4444"
        self.blue = "#38bdf8"
        self.violet = "#a78bfa"
        self.teal = "#2dd4bf"

        self.root.configure(bg=self.bg)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=self.bg, foreground="white", fieldbackground=self.panel)
        style.configure("Shell.TFrame", background=self.bg)
        style.configure("Panel.TFrame", background=self.panel)
        style.configure("Card.TFrame", background=self.card)
        style.configure("Hero.TFrame", background=self.panel_soft)
        style.configure("Card.TLabelframe", background=self.panel, foreground="white", borderwidth=1, relief="solid")
        style.configure("Card.TLabelframe.Label", background=self.panel, foreground="white", font=("Segoe UI", 10, "bold"))
        style.configure("Hero.TLabel", background=self.panel_soft, foreground="white")
        style.configure("Panel.TLabel", background=self.panel, foreground=self.soft)
        style.configure("CardLabel.TLabel", background=self.card, foreground=self.soft)
        style.configure("Big.TLabel", background=self.panel_soft, foreground="white", font=("Segoe UI", 24, "bold"))
        style.configure("Sub.TLabel", background=self.panel_soft, foreground=self.muted, font=("Segoe UI", 11))
        style.configure("MetricName.TLabel", background=self.card, foreground=self.muted, font=("Segoe UI", 10))
        style.configure("MetricValue.TLabel", background=self.card, foreground="white", font=("Segoe UI", 17, "bold"))
        style.configure("MetricGreen.TLabel", background=self.card, foreground=self.green, font=("Segoe UI", 19, "bold"))
        style.configure("MetricGold.TLabel", background=self.card, foreground=self.gold, font=("Segoe UI", 19, "bold"))
        style.configure("MetricRed.TLabel", background=self.card, foreground=self.red, font=("Segoe UI", 19, "bold"))
        style.configure("Muted.TLabel", background=self.panel, foreground=self.muted, font=("Segoe UI", 10))
        style.configure("Warning.TLabel", background=self.panel, foreground=self.gold, font=("Segoe UI", 10, "bold"))
        style.configure("Danger.TLabel", background=self.panel, foreground=self.red, font=("Segoe UI", 10, "bold"))
        style.configure("Status.TLabel", background=self.bg, foreground=self.soft, font=("Segoe UI", 10))
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=10)
        style.configure("Slim.TButton", font=("Segoe UI", 9), padding=6)
        style.configure(
            "Pressure.Horizontal.TProgressbar",
            troughcolor="#09101c",
            background=self.red,
            bordercolor="#09101c",
            lightcolor=self.red,
            darkcolor=self.red,
        )

        style.configure(
            "Treeview",
            background="#091220",
            fieldbackground="#091220",
            foreground="white",
            rowheight=28,
            borderwidth=0,
        )
        style.configure(
            "Treeview.Heading",
            background="#18263b",
            foreground="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview.Heading", background=[("active", "#22324a")])

    def _load_logo(self) -> None:
        if not self.logo_source.exists():
            return
        try:
            logo = tk.PhotoImage(file=str(self.logo_source))
        except tk.TclError:
            return

        max_width = 116
        max_height = 116
        width = max(1, logo.width())
        height = max(1, logo.height())
        factor = max(1, (width + max_width - 1) // max_width, (height + max_height - 1) // max_height)
        if factor > 1:
            logo = logo.subsample(factor, factor)

        self.logo_image = logo
        try:
            self.root.iconphoto(True, self.logo_image)
        except tk.TclError:
            pass

    def _build_layout(self) -> None:
        shell = ttk.Frame(self.root, style="Shell.TFrame")
        shell.pack(fill="both", expand=True, padx=14, pady=14)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        self._build_hero(shell)

        body = ttk.Frame(shell, style="Shell.TFrame")
        body.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        body.columnconfigure(0, weight=0)
        body.columnconfigure(1, weight=1)
        body.columnconfigure(2, weight=1)
        body.rowconfigure(0, weight=1)

        self.sidebar = ttk.Frame(body, style="Shell.TFrame")
        self.sidebar.grid(row=0, column=0, sticky="nsw", padx=(0, 12))

        self.center = ttk.Frame(body, style="Shell.TFrame")
        self.center.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        self.center.rowconfigure(1, weight=1)
        self.center.columnconfigure(0, weight=1)

        self.right = ttk.Frame(body, style="Shell.TFrame")
        self.right.grid(row=0, column=2, sticky="nsew")
        self.right.rowconfigure(0, weight=1)
        self.right.rowconfigure(1, weight=1)
        self.right.columnconfigure(0, weight=1)

        self._build_sidebar()
        self._build_briefing(self.center)
        self._build_dashboards(self.center)
        self._build_history_panel(self.right)
        self._build_log_panel(self.right)
        self._build_statusbar(shell)

    def _build_hero(self, parent: ttk.Frame) -> None:
        hero = ttk.Frame(parent, style="Hero.TFrame")
        hero.grid(row=0, column=0, sticky="ew")
        hero.columnconfigure(0, weight=1)
        hero.columnconfigure(1, weight=1)
        hero.columnconfigure(2, weight=1)

        left = ttk.Frame(hero, style="Hero.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=16, pady=14)

        brand = ttk.Frame(left, style="Hero.TFrame")
        brand.pack(anchor="w", fill="x")
        if self.logo_image is not None:
            logo_label = tk.Label(
                brand,
                image=self.logo_image,
                bg=self.panel_soft,
                bd=0,
                highlightthickness=0,
            )
            logo_label.pack(side="left", padx=(0, 12))

        brand_text = ttk.Frame(brand, style="Hero.TFrame")
        brand_text.pack(side="left", fill="both", expand=True)
        ttk.Label(brand_text, text="Milk Manager", style="Big.TLabel").pack(anchor="w")
        ttk.Label(
            brand_text,
            text="Price Cap Panic — a slow administrative strangling of an ordinary dairy.",
            style="Sub.TLabel",
            wraplength=420,
            justify="left",
        ).pack(anchor="w", pady=(4, 0))

        middle = ttk.Frame(hero, style="Hero.TFrame")
        middle.grid(row=0, column=1, sticky="nsew", padx=16, pady=14)
        self.phase_var = tk.StringVar()
        self.hero_stats_var = tk.StringVar()
        ttk.Label(middle, textvariable=self.phase_var, style="Big.TLabel").pack(anchor="w")
        ttk.Label(middle, textvariable=self.hero_stats_var, style="Sub.TLabel", wraplength=420, justify="left").pack(
            anchor="w", pady=(4, 0)
        )

        right = ttk.Frame(hero, style="Hero.TFrame")
        right.grid(row=0, column=2, sticky="nsew", padx=16, pady=14)
        self.pressure_label_var = tk.StringVar()
        ttk.Label(right, text="Policy pressure", style="Sub.TLabel").pack(anchor="w")
        self.pressure = ttk.Progressbar(
            right,
            style="Pressure.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100,
            length=320,
        )
        self.pressure.pack(fill="x", pady=(8, 6))
        ttk.Label(right, textvariable=self.pressure_label_var, style="Sub.TLabel").pack(anchor="w")

    def _build_sidebar(self) -> None:
        self._metric_panel()
        self._control_panel()
        self._howto_panel()

    def _metric_panel(self) -> None:
        frame = ttk.LabelFrame(self.sidebar, text="Current Position", style="Card.TLabelframe")
        frame.pack(fill="x", pady=(0, 12))

        self.turn_var = tk.StringVar()
        self.vault_var = tk.StringVar()
        self.cum_profit_var = tk.StringVar()
        self.cost_var = tk.StringVar()
        self.cap_var = tk.StringVar()
        self.ratio_var = tk.StringVar()
        self.elasticity_var = tk.StringVar()
        self.forecast_var = tk.StringVar()
        self.alert_var = tk.StringVar()

        cards = [
            ("Turn", self.turn_var, "MetricValue.TLabel"),
            ("Vault", self.vault_var, "MetricGreen.TLabel"),
            ("Cumulative profit", self.cum_profit_var, "MetricValue.TLabel"),
            ("Unit cost", self.cost_var, "MetricValue.TLabel"),
            ("Price cap", self.cap_var, "MetricGold.TLabel"),
            ("Cap / cost", self.ratio_var, "MetricValue.TLabel"),
            ("Elasticity", self.elasticity_var, "MetricValue.TLabel"),
            ("Forecast", self.forecast_var, "MetricValue.TLabel"),
        ]
        for idx, (name, var, style_name) in enumerate(cards):
            card = ttk.Frame(frame, style="Card.TFrame")
            card.pack(fill="x", padx=12, pady=(12 if idx == 0 else 0, 8))
            ttk.Label(card, text=name, style="MetricName.TLabel").pack(anchor="w", padx=12, pady=(10, 0))
            ttk.Label(card, textvariable=var, style=style_name).pack(anchor="w", padx=12, pady=(2, 10))

        self.alert_label = ttk.Label(
            frame, textvariable=self.alert_var, style="Warning.TLabel", wraplength=280, justify="left"
        )
        self.alert_label.pack(anchor="w", padx=14, pady=(4, 14))

    def _control_panel(self) -> None:
        frame = ttk.LabelFrame(self.sidebar, text="Manager Controls", style="Card.TLabelframe")
        frame.pack(fill="x", pady=(0, 12))

        self.production_var = tk.IntVar(value=700)
        self.price_var = tk.DoubleVar(value=1.55)
        self.preview_demand_var = tk.StringVar()
        self.preview_profit_var = tk.StringVar()
        self.preview_extra_var = tk.StringVar()

        ttk.Label(frame, text="Production (units)", style="Panel.TLabel").pack(anchor="w", padx=14, pady=(12, 4))
        self.production_scale = tk.Scale(
            frame,
            from_=0,
            to=self.game.max_production,
            orient="horizontal",
            resolution=10,
            showvalue=True,
            variable=self.production_var,
            bg=self.panel,
            fg="white",
            highlightthickness=0,
            troughcolor="#22324a",
            activebackground=self.green,
            length=280,
            command=lambda _value: self._update_preview(),
        )
        self.production_scale.pack(padx=10, pady=(0, 10))

        ttk.Label(frame, text="Sale price per unit", style="Panel.TLabel").pack(anchor="w", padx=14, pady=(0, 4))
        self.price_scale = tk.Scale(
            frame,
            from_=self.game.price_floor,
            to=self.game.market_max_price,
            orient="horizontal",
            resolution=0.01,
            showvalue=True,
            variable=self.price_var,
            bg=self.panel,
            fg="white",
            highlightthickness=0,
            troughcolor="#22324a",
            activebackground=self.green,
            length=280,
            command=lambda _value: self._update_preview(),
        )
        self.price_scale.pack(padx=10, pady=(0, 10))

        buttons = ttk.Frame(frame, style="Panel.TFrame")
        buttons.pack(fill="x", padx=10, pady=(0, 4))
        ttk.Button(buttons, text="Recommended", style="Slim.TButton", command=self._apply_recommended).pack(
            side="left", padx=(0, 6)
        )
        ttk.Button(buttons, text="Match cap", style="Slim.TButton", command=self._match_cap).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="At cost", style="Slim.TButton", command=self._set_price_at_cost).pack(side="left")

        ttk.Label(frame, textvariable=self.preview_demand_var, style="Muted.TLabel", wraplength=292, justify="left").pack(
            anchor="w", padx=14, pady=(8, 2)
        )
        ttk.Label(frame, textvariable=self.preview_profit_var, style="Muted.TLabel", wraplength=292, justify="left").pack(
            anchor="w", padx=14, pady=(0, 2)
        )
        ttk.Label(frame, textvariable=self.preview_extra_var, style="Muted.TLabel", wraplength=292, justify="left").pack(
            anchor="w", padx=14, pady=(0, 10)
        )

        action_row = ttk.Frame(frame, style="Panel.TFrame")
        action_row.pack(fill="x", padx=10, pady=(0, 14))
        self.end_turn_button = ttk.Button(action_row, text="End Turn", style="Action.TButton", command=self._end_turn)
        self.end_turn_button.pack(side="left")
        ttk.Button(action_row, text="Restart", style="Action.TButton", command=self._restart).pack(side="left", padx=8)

    def _howto_panel(self) -> None:
        frame = ttk.LabelFrame(self.sidebar, text="Rules of the Game", style="Card.TLabelframe")
        frame.pack(fill="x")
        ttk.Label(
            frame,
            text=(
                "You control price and production each turn.\n"
                "Demand is elastic: higher prices reduce quantity demanded.\n"
                "Unsold milk spoils and adds waste cost.\n"
                "A fixed operating cost drains the firm every turn.\n"
                "From turn 6 onward, the state imposes a ceiling and cuts it by 10% every turn.\n"
                "The game no longer ends on a turn limit. It ends only when the dairy is bankrupt."
            ),
            style="Muted.TLabel",
            wraplength=292,
            justify="left",
        ).pack(anchor="w", padx=14, pady=14)

    def _build_briefing(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Market Desk", style="Card.TLabelframe")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.market_msg = tk.StringVar()
        self.gov_msg = tk.StringVar()
        ttk.Label(frame, textvariable=self.market_msg, style="Panel.TLabel", wraplength=480, justify="left").grid(
            row=0, column=0, sticky="w", padx=14, pady=12
        )
        ttk.Label(frame, textvariable=self.gov_msg, style="Panel.TLabel", wraplength=480, justify="left").grid(
            row=0, column=1, sticky="w", padx=14, pady=12
        )

    def _build_dashboards(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Company Dashboard", style="Card.TLabelframe")
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        self.price_canvas = tk.Canvas(frame, bg="#07101d", highlightthickness=0)
        self.vault_canvas = tk.Canvas(frame, bg="#07101d", highlightthickness=0)
        self.ops_canvas = tk.Canvas(frame, bg="#07101d", highlightthickness=0)
        self.policy_canvas = tk.Canvas(frame, bg="#07101d", highlightthickness=0)

        self.price_canvas.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=(10, 6))
        self.vault_canvas.grid(row=0, column=1, sticky="nsew", padx=(6, 10), pady=(10, 6))
        self.ops_canvas.grid(row=1, column=0, sticky="nsew", padx=(10, 6), pady=(6, 10))
        self.policy_canvas.grid(row=1, column=1, sticky="nsew", padx=(6, 10), pady=(6, 10))

    def _build_history_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Turn Ledger", style="Card.TLabelframe")
        frame.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        columns = ("turn", "phase", "price", "cap", "prod", "demand", "sold", "profit", "vault")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings")
        widths = {"turn": 52, "phase": 125, "price": 66, "cap": 66, "prod": 84, "demand": 76, "sold": 66, "profit": 84, "vault": 86}
        headings = {
            "turn": "Turn",
            "phase": "Phase",
            "price": "Price",
            "cap": "Cap",
            "prod": "Prod.",
            "demand": "Demand",
            "sold": "Sold",
            "profit": "Profit",
            "vault": "Vault",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="center", stretch=(col == "phase"))

        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

        self.last_turn_summary = tk.StringVar(value="No turns played yet.")
        ttk.Label(frame, textvariable=self.last_turn_summary, style="Muted.TLabel", wraplength=600, justify="left").grid(
            row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 12)
        )

    def _build_log_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Operations & Policy Log", style="Card.TLabelframe")
        frame.grid(row=1, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            frame,
            wrap="word",
            height=12,
            bg="#091220",
            fg="white",
            insertbackground="white",
            relief="flat",
            highlightthickness=0,
            padx=12,
            pady=12,
            font=("Consolas", 10),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        log_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set, state="disabled")
        log_scroll.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)

    def _build_statusbar(self, parent: ttk.Frame) -> None:
        self.status_var = tk.StringVar(value="Ready.")
        bar = ttk.Label(parent, textvariable=self.status_var, style="Status.TLabel", anchor="w")
        bar.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _bind_redraws(self) -> None:
        self.price_canvas.bind("<Configure>", lambda _e: self._draw_price_chart())
        self.vault_canvas.bind("<Configure>", lambda _e: self._draw_vault_chart())
        self.ops_canvas.bind("<Configure>", lambda _e: self._draw_operations_chart())
        self.policy_canvas.bind("<Configure>", lambda _e: self._draw_policy_chart())

    def _money(self, value: float) -> str:
        return f"${value:,.2f}"

    def _refresh_view(self) -> None:
        g = self.game
        self.turn_var.set(str(g.turn))
        self.vault_var.set(self._money(g.vault))
        self.cum_profit_var.set(self._money(g.cumulative_profit))
        self.cost_var.set(self._money(g.cost_per_unit))
        self.cap_var.set("None" if g.price_cap is None else self._money(g.price_cap))
        ratio = g.cap_to_cost_ratio()
        self.ratio_var.set("—" if ratio is None else f"{ratio:.2f}x")
        self.elasticity_var.set(f"{g.elasticity:.2f}")
        self.forecast_var.set(f"≈ {g.forecast_for_price(g.reference_price):,} @ {self._money(g.reference_price)}")

        if g.price_cap is None:
            self.alert_var.set("No controls yet. The market still speaks.")
            self.alert_label.configure(style="Warning.TLabel")
        elif g.price_cap >= g.cost_per_unit:
            self.alert_var.set("The cap binds, but still sits above cost. The noose is visible, not yet tight.")
            self.alert_label.configure(style="Warning.TLabel")
        else:
            self.alert_var.set("The ceiling is below cost. Every legal sale now bleeds the dairy.")
            self.alert_label.configure(style="Danger.TLabel")

        self.phase_var.set(g.phase_label)
        self.hero_stats_var.set(
            f"Turn {g.turn} • survived {g.turns_survived} completed turns • "
            f"vault {self._money(g.vault)} • cumulative profit {self._money(g.cumulative_profit)}"
        )
        pressure = g.policy_pressure()
        self.pressure["value"] = pressure
        if g.price_cap is None:
            self.pressure_label_var.set("Pressure: 0% — no formal ceiling yet.")
        else:
            relation = "above cost" if g.price_cap >= g.cost_per_unit else "below cost"
            self.pressure_label_var.set(
                f"Pressure: {pressure:.0f}% — cap {relation} at {self._money(g.price_cap)} versus unit cost {self._money(g.cost_per_unit)}."
            )

        self.market_msg.set(
            f"Forecast baseline demand is roughly {g.forecast_baseline:,} units near the reference price of "
            f"{self._money(g.reference_price)}. This turn's elasticity is {g.elasticity:.2f}, so demand will react sharply to price."
        )
        if g.price_cap is None:
            self.gov_msg.set(
                "The ministry has not yet legislated the market. You still choose price under ordinary commercial discipline."
            )
        elif g.price_cap >= g.cost_per_unit:
            self.gov_msg.set(
                f"The ministry caps the legal price at {self._money(g.price_cap)}. It still lies above unit cost, but the room to maneuver narrows."
            )
        else:
            self.gov_msg.set(
                f"The legal maximum is {self._money(g.price_cap)}, beneath the {self._money(g.cost_per_unit)} cost of production. "
                "The state now commands losses."
            )

        self.price_scale.configure(from_=g.price_floor, to=g.allowed_price_max())
        if self.price_var.get() > g.allowed_price_max():
            self.price_var.set(g.allowed_price_max())
        if self.price_var.get() < g.price_floor:
            self.price_var.set(g.price_floor)

        if g.game_over():
            self.end_turn_button.state(["disabled"])
        else:
            self.end_turn_button.state(["!disabled"])

        self._update_preview()
        self._refresh_history()
        self._refresh_log()
        self._draw_price_chart()
        self._draw_vault_chart()
        self._draw_operations_chart()
        self._draw_policy_chart()

    def _refresh_history(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for rec in self.game.history:
            cap_text = "-" if rec.cap is None else f"{rec.cap:.2f}"
            profit_text = f"{rec.profit:+.0f}"
            vault_text = f"{rec.vault:.0f}"
            self.tree.insert(
                "",
                "end",
                values=(
                    rec.turn,
                    rec.phase,
                    f"{rec.price:.2f}",
                    cap_text,
                    rec.production,
                    rec.demand,
                    rec.sold,
                    profit_text,
                    vault_text,
                ),
            )

        if self.game.history:
            r = self.game.history[-1]
            self.last_turn_summary.set(
                f"Turn {r.turn}: produced {r.production:,}, sold {r.sold:,}, wasted {r.wasted:,}. "
                f"Revenue {self._money(r.revenue)} against total costs {self._money(r.total_cost)} for "
                f"a profit of {self._money(r.profit)}. Vault now stands at {self._money(r.vault)}."
            )
        else:
            self.last_turn_summary.set("No turns played yet.")

    def _refresh_log(self) -> None:
        log = self.game.event_log
        if len(log) == self.last_rendered_log_count:
            return
        self.log_text.configure(state="normal")
        if self.last_rendered_log_count == 0:
            self.log_text.delete("1.0", "end")
        for entry in log[self.last_rendered_log_count:]:
            self.log_text.insert("end", "• " + entry + "\n\n")
        self.log_text.configure(state="disabled")
        self.log_text.see("end")
        self.last_rendered_log_count = len(log)

    def _update_preview(self) -> None:
        price = round(self.price_var.get(), 2)
        production = int(self.production_var.get())
        estimate = self.game.estimate_turn(production, price)
        demand = int(estimate["demand"])
        sold = int(estimate["sold"])
        wasted = int(estimate["wasted"])
        profit = float(estimate["profit"])
        revenue = float(estimate["revenue"])
        costs = float(estimate["total_cost"])

        self.preview_demand_var.set(
            f"Forecast at {self._money(price)}: demand ≈ {demand:,}; expected sales ≈ {sold:,}; spoilage ≈ {wasted:,}."
        )
        self.preview_profit_var.set(
            f"Projected revenue {self._money(revenue)} versus projected total costs {self._money(costs)} "
            f"for an estimated profit of {self._money(profit)}."
        )
        if price < self.game.cost_per_unit:
            warning = "Per-unit selling price is below cost."
        else:
            warning = f"Per-unit margin is {self._money(price - self.game.cost_per_unit)} before fixed and waste costs."
        self.preview_extra_var.set(warning)

    def _apply_recommended(self) -> None:
        production, price = self.game.recommended_controls()
        self.production_var.set(production)
        self.price_var.set(price)
        self._update_preview()
        self.status_var.set(f"Applied analyst recommendation: production {production:,}, price {self._money(price)}.")

    def _match_cap(self) -> None:
        if self.game.price_cap is None:
            self.status_var.set("There is no cap to match yet.")
            return
        self.price_var.set(self.game.allowed_price_max())
        self._update_preview()
        self.status_var.set(f"Price matched to the current legal ceiling of {self._money(self.game.allowed_price_max())}.")

    def _set_price_at_cost(self) -> None:
        price = min(max(self.game.cost_per_unit, self.game.price_floor), self.game.allowed_price_max())
        self.price_var.set(price)
        self._update_preview()
        self.status_var.set(f"Price set to the cost line at {self._money(price)}.")

    def _end_turn(self) -> None:
        if self.game.game_over():
            return

        production = self.production_var.get()
        chosen_price = round(self.price_var.get(), 2)
        result = self.game.resolve_turn(production, chosen_price)
        self._refresh_view()

        phase_line = f"Phase: {result.phase}"
        outcome = (
            f"{phase_line}\n\n"
            f"Demand: {result.demand:,}\n"
            f"Sold: {result.sold:,}\n"
            f"Wasted: {result.wasted:,}\n"
            f"Revenue: {self._money(result.revenue)}\n"
            f"Total costs: {self._money(result.total_cost)}\n"
            f"Profit: {self._money(result.profit)}\n"
            f"Vault: {self._money(result.vault)}"
        )
        messagebox.showinfo(f"Turn {result.turn} resolved", outcome)

        self.status_var.set(
            f"Turn {result.turn} resolved: price {self._money(result.price)}, production {result.production:,}, profit {self._money(result.profit)}."
        )

        if self.game.bankrupt:
            self._show_game_over()

    def _restart(self) -> None:
        self.game.reset()
        self.last_rendered_log_count = 0
        self.production_var.set(700)
        self.price_var.set(1.55)
        self.end_turn_button.state(["!disabled"])
        self._refresh_view()
        self.status_var.set("Campaign restarted.")

    def _show_game_over(self) -> None:
        r = self.game.history[-1]
        msg = (
            f"The dairy is bankrupt on turn {r.turn}.\n\n"
            f"Final vault: {self._money(r.vault)}\n"
            f"Cumulative profit: {self._money(self.game.cumulative_profit)}\n"
            f"Final legal cap: {self._money(r.cap or 0.0)}\n"
            f"Unit cost: {self._money(self.game.cost_per_unit)}\n\n"
            "There is no arbitrary turn limit anymore. The company dies only when the losses finally exhaust it."
        )
        messagebox.showinfo("Bankruptcy", msg)
        self.end_turn_button.state(["disabled"])

    def _draw_axes(
        self, canvas: tk.Canvas, title: str, y_label: str
    ) -> tuple[int, int, int, int]:
        canvas.delete("all")
        width = max(320, canvas.winfo_width())
        height = max(220, canvas.winfo_height())
        left, top, right, bottom = 54, 30, width - 14, height - 34
        canvas.create_text(left, 12, text=title, anchor="w", fill="white", font=("Segoe UI", 11, "bold"))
        canvas.create_line(left, top, left, bottom, fill="#64748b")
        canvas.create_line(left, bottom, right, bottom, fill="#64748b")
        canvas.create_text(12, top, text=y_label, anchor="nw", fill="#94a3b8", font=("Segoe UI", 8))
        return left, top, right, bottom

    def _draw_grid(self, canvas: tk.Canvas, left: int, top: int, right: int, bottom: int, labels: list[str]) -> None:
        count = max(1, len(labels) - 1)
        for idx, label in enumerate(labels):
            y = top + (bottom - top) * idx / count
            canvas.create_line(left, y, right, y, fill="#102036")
            canvas.create_text(left - 6, y, text=label, anchor="e", fill="#94a3b8", font=("Segoe UI", 8))

    def _legend(self, canvas: tk.Canvas, x: int, y: int, color: str, text: str, dashed: bool = False) -> None:
        if dashed:
            canvas.create_line(x, y, x + 16, y, fill=color, width=3, dash=(6, 4))
        else:
            canvas.create_line(x, y, x + 16, y, fill=color, width=3)
        canvas.create_text(x + 22, y, text=text, anchor="w", fill="#cbd5e1", font=("Segoe UI", 8))

    def _draw_price_chart(self) -> None:
        canvas = self.price_canvas
        left, top, right, bottom = self._draw_axes(canvas, "Prices: manager, cap, and cost", "price")
        data = self.game.history
        if not data:
            canvas.create_text((left + right) / 2, (top + bottom) / 2, text="Play a turn to draw prices.", fill="#94a3b8")
            return

        values = [r.price for r in data] + [self.game.cost_per_unit]
        values += [r.cap for r in data if r.cap is not None]
        y_min = min(values) * 0.9
        y_max = max(values) * 1.1
        if y_max - y_min < 0.3:
            y_max += 0.15
            y_min -= 0.15

        labels = [f"{y_min + (y_max-y_min)*(4-i)/4:.2f}" for i in range(5)]
        self._draw_grid(canvas, left, top, right, bottom, labels)

        def xy(i: int, value: float) -> tuple[float, float]:
            x = left + (right - left) * i / max(1, len(data) - 1)
            y = bottom - (bottom - top) * ((value - y_min) / (y_max - y_min))
            return x, y

        manager_points = []
        cap_points = []
        for i, rec in enumerate(data):
            manager_points.extend(xy(i, rec.price))
            if rec.cap is not None:
                cap_points.extend(xy(i, rec.cap))
            x_tick, _ = xy(i, y_min)
            canvas.create_text(x_tick, bottom + 14, text=str(rec.turn), fill="#94a3b8", font=("Segoe UI", 8))

        if len(manager_points) >= 4:
            canvas.create_line(*manager_points, fill=self.green, width=3, smooth=True)
        if len(cap_points) >= 4:
            canvas.create_line(*cap_points, fill=self.gold, width=3, dash=(6, 4), smooth=True)

        cost_y = xy(0, self.game.cost_per_unit)[1]
        canvas.create_line(left, cost_y, right, cost_y, fill=self.blue, dash=(2, 4), width=2)

        self._legend(canvas, right - 250, top + 8, self.green, "manager")
        self._legend(canvas, right - 165, top + 8, self.gold, "price cap", dashed=True)
        self._legend(canvas, right - 76, top + 8, self.blue, "cost")

    def _draw_vault_chart(self) -> None:
        canvas = self.vault_canvas
        left, top, right, bottom = self._draw_axes(canvas, "Vault and per-turn result", "money")
        data = self.game.history
        if not data:
            canvas.create_text((left + right) / 2, (top + bottom) / 2, text="The vault appears after turn one.", fill="#94a3b8")
            return

        vaults = [self.game.starting_vault] + [r.vault for r in data]
        profits = [r.profit for r in data]
        values = vaults + profits + [0]
        y_min = min(values) * 1.15 if min(values) < 0 else 0
        y_max = max(values) * 1.10 if max(values) > 0 else 10
        if y_max - y_min < 10:
            y_max += 5

        labels = [f"{y_min + (y_max-y_min)*(4-i)/4:.0f}" for i in range(5)]
        self._draw_grid(canvas, left, top, right, bottom, labels)

        def map_x(i: int, count: int) -> float:
            return left + (right - left) * i / max(1, count - 1)

        def map_y(value: float) -> float:
            return bottom - (bottom - top) * ((value - y_min) / (y_max - y_min))

        zero_y = map_y(0)
        canvas.create_line(left, zero_y, right, zero_y, fill="#334155", dash=(4, 3))

        vault_points = []
        for i, value in enumerate(vaults):
            vault_points.extend((map_x(i, len(vaults)), map_y(value)))
        if len(vault_points) >= 4:
            canvas.create_line(*vault_points, fill=self.violet, width=3, smooth=True)

        bar_width = max(12, (right - left) / max(10, len(profits) * 1.7))
        for i, value in enumerate(profits, start=1):
            x = map_x(i, len(vaults))
            y = map_y(value)
            fill = self.green if value >= 0 else self.red
            canvas.create_rectangle(x - bar_width / 2, y, x + bar_width / 2, zero_y, fill=fill, outline="")
            canvas.create_text(x, bottom + 14, text=str(i), fill="#94a3b8", font=("Segoe UI", 8))

        self._legend(canvas, right - 210, top + 8, self.violet, "vault")
        self._legend(canvas, right - 125, top + 8, self.green, "profit")
        self._legend(canvas, right - 48, top + 8, self.red, "loss")

    def _draw_operations_chart(self) -> None:
        canvas = self.ops_canvas
        left, top, right, bottom = self._draw_axes(canvas, "Operations: production, demand, and sales", "units")
        data = self.game.history
        if not data:
            canvas.create_text((left + right) / 2, (top + bottom) / 2, text="Volumes will draw after the first turn.", fill="#94a3b8")
            return

        values = [r.production for r in data] + [r.demand for r in data] + [r.sold for r in data]
        y_min = 0
        y_max = max(values) * 1.10 if max(values) > 0 else 10

        labels = [f"{y_min + (y_max-y_min)*(4-i)/4:.0f}" for i in range(5)]
        self._draw_grid(canvas, left, top, right, bottom, labels)

        def xy(i: int, value: float) -> tuple[float, float]:
            x = left + (right - left) * i / max(1, len(data) - 1)
            y = bottom - (bottom - top) * ((value - y_min) / (y_max - y_min))
            return x, y

        prod_points = []
        demand_points = []
        sold_points = []
        for i, rec in enumerate(data):
            prod_points.extend(xy(i, rec.production))
            demand_points.extend(xy(i, rec.demand))
            sold_points.extend(xy(i, rec.sold))
            x_tick, _ = xy(i, y_min)
            canvas.create_text(x_tick, bottom + 14, text=str(rec.turn), fill="#94a3b8", font=("Segoe UI", 8))

        canvas.create_line(*prod_points, fill=self.blue, width=3, smooth=True)
        canvas.create_line(*demand_points, fill=self.gold, width=3, smooth=True)
        canvas.create_line(*sold_points, fill=self.teal, width=3, smooth=True)

        self._legend(canvas, right - 210, top + 8, self.blue, "production")
        self._legend(canvas, right - 112, top + 8, self.gold, "demand")
        self._legend(canvas, right - 38, top + 8, self.teal, "sold")

    def _draw_policy_chart(self) -> None:
        canvas = self.policy_canvas
        left, top, right, bottom = self._draw_axes(canvas, "Margin and cap-to-cost ratio", "mixed")
        data = self.game.history
        if not data:
            canvas.create_text((left + right) / 2, (top + bottom) / 2, text="Policy stress will be drawn over time.", fill="#94a3b8")
            return

        margins = [r.margin_per_unit for r in data]
        ratios = [r.cap_ratio for r in data if r.cap_ratio is not None]
        y_min = min(margins + [0, -0.5])
        y_max = max(margins + [1.5])
        if y_max - y_min < 0.6:
            y_max += 0.3
            y_min -= 0.3

        labels = [f"{y_min + (y_max-y_min)*(4-i)/4:.2f}" for i in range(5)]
        self._draw_grid(canvas, left, top, right, bottom, labels)

        def x_for(i: int) -> float:
            return left + (right - left) * i / max(1, len(data) - 1)

        def y_margin(value: float) -> float:
            return bottom - (bottom - top) * ((value - y_min) / (y_max - y_min))

        zero_y = y_margin(0)
        canvas.create_line(left, zero_y, right, zero_y, fill="#334155", dash=(4, 3))

        bar_width = max(12, (right - left) / max(10, len(data) * 1.7))
        for i, rec in enumerate(data):
            x = x_for(i)
            y = y_margin(rec.margin_per_unit)
            fill = self.green if rec.margin_per_unit >= 0 else self.red
            canvas.create_rectangle(x - bar_width / 2, y, x + bar_width / 2, zero_y, fill=fill, outline="")
            canvas.create_text(x, bottom + 14, text=str(rec.turn), fill="#94a3b8", font=("Segoe UI", 8))

        if ratios:
            ratio_min = 0.0
            ratio_max = max(1.8, max(ratios) * 1.1)

            def y_ratio(value: float) -> float:
                return bottom - (bottom - top) * ((value - ratio_min) / (ratio_max - ratio_min))

            ratio_points = []
            for i, rec in enumerate(data):
                if rec.cap_ratio is not None:
                    ratio_points.extend((x_for(i), y_ratio(rec.cap_ratio)))
            if len(ratio_points) >= 4:
                canvas.create_line(*ratio_points, fill=self.gold, width=3, smooth=True)
            threshold_y = y_ratio(1.0)
            canvas.create_line(left, threshold_y, right, threshold_y, fill=self.gold, dash=(2, 4))
            canvas.create_text(right - 4, threshold_y - 8, text="cap = cost", anchor="e", fill=self.gold, font=("Segoe UI", 8))

        self._legend(canvas, right - 208, top + 8, self.green, "margin")
        self._legend(canvas, right - 110, top + 8, self.red, "negative")
        self._legend(canvas, right - 40, top + 8, self.gold, "cap/cost")

def main() -> None:
    root = tk.Tk()
    MilkManagerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
