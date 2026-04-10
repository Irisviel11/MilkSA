from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from game_logic import MilkMarketGame


st.set_page_config(
    page_title="MilkSA — Price Cap Panic",
    page_icon="🥛",
    layout="wide",
    initial_sidebar_state="collapsed",
)

PALETTE = {
    "primary_100": "#AEEFFA",
    "primary_200": "#55CDF2",
    "primary_300": "#073660",
    "accent_100": "#61823A",
    "accent_200": "#F1DB51",
    "text_100": "#FAF6E5",
    "text_200": "#CDCABD",
    "bg_100": "#0C1E28",
    "bg_200": "#2D4F63",
    "bg_300": "#627B8B",
    "loss": "#ff6b6b",
}


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --primary-100: {PALETTE['primary_100']};
            --primary-200: {PALETTE['primary_200']};
            --primary-300: {PALETTE['primary_300']};
            --accent-100: {PALETTE['accent_100']};
            --accent-200: {PALETTE['accent_200']};
            --text-100: {PALETTE['text_100']};
            --text-200: {PALETTE['text_200']};
            --bg-100: {PALETTE['bg_100']};
            --bg-200: {PALETTE['bg_200']};
            --bg-300: {PALETTE['bg_300']};
            --loss: {PALETTE['loss']};
        }}
        .stApp {{
            background: linear-gradient(180deg, var(--bg-100) 0%, #08141b 100%);
            color: var(--text-100);
        }}
        .block-container {{
            max-width: 1550px;
            padding-top: 1.1rem;
            padding-bottom: 2rem;
        }}
        h1, h2, h3, h4, h5, h6, p, label, div, span {{
            color: var(--text-100);
        }}
        .hero-card, .panel-card, .controls-card {{
            background: linear-gradient(180deg, rgba(45,79,99,0.65), rgba(12,30,40,0.92));
            border: 1px solid rgba(174,239,250,0.18);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            box-shadow: 0 12px 30px rgba(0,0,0,0.18);
        }}
        .controls-card {{
            border-left: 5px solid var(--accent-200);
        }}
        .panel-title {{
            font-size: 0.92rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--accent-200);
            margin-bottom: 0.45rem;
        }}
        .big-title {{
            font-size: 2.2rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0;
        }}
        .subtitle {{
            color: var(--text-200);
            margin-top: 0.35rem;
            font-size: 1rem;
        }}
        .phase-title {{
            font-size: 2.05rem;
            font-weight: 800;
            margin-bottom: 0.2rem;
        }}
        .phase-stats {{
            color: var(--text-200);
            font-size: 0.96rem;
            margin-bottom: 0.55rem;
        }}
        .news-line {{
            font-size: 1rem;
            line-height: 1.45;
        }}
        .pressure-track {{
            width: 100%;
            height: 18px;
            border-radius: 999px;
            background: rgba(255,255,255,0.10);
            overflow: hidden;
            margin: 0.55rem 0 0.5rem;
            border: 1px solid rgba(255,255,255,0.08);
        }}
        .pressure-fill {{
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--primary-100), var(--accent-200), var(--accent-100));
        }}
        .pressure-text {{
            color: var(--text-200);
            font-size: 0.95rem;
            line-height: 1.4;
        }}
        .compact-metrics {{
            display: grid;
            grid-template-columns: 1fr;
            row-gap: 0.15rem;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.42rem 0;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}
        .metric-row:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            color: var(--text-200);
            font-size: 0.94rem;
        }}
        .metric-value {{
            color: var(--text-100);
            font-size: 1rem;
            font-weight: 700;
            text-align: right;
        }}
        .metric-value.gold {{ color: var(--accent-200); }}
        .metric-value.green {{ color: var(--primary-100); }}
        .warning-line {{
            margin-top: 0.7rem;
            color: var(--accent-200);
            font-size: 0.95rem;
            font-weight: 700;
            line-height: 1.35;
        }}
        .small-note {{
            color: var(--text-200);
            font-size: 0.94rem;
            line-height: 1.45;
        }}
        .stSlider {{ margin-bottom: 0.2rem; }}
        .stButton > button {{
            border-radius: 12px;
            border: 1px solid rgba(174,239,250,0.24);
            background: linear-gradient(180deg, rgba(98,123,139,0.18), rgba(12,30,40,0.85));
            color: var(--text-100);
            font-weight: 700;
            min-height: 2.6rem;
        }}
        .stButton > button:hover {{
            border-color: rgba(241,219,81,0.65);
            color: var(--text-100);
        }}
        div[data-testid="stDataFrame"] div[role="table"] {{
            background: rgba(12,30,40,0.85);
        }}
        div[data-testid="stDataFrame"] * {{
            color: var(--text-100) !important;
        }}
        div[data-testid="stDataFrame"] [data-testid="stTable"] thead tr th {{
            background: rgba(45,79,99,0.8) !important;
        }}
        .spacer-tight {{ margin-top: 0.35rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    if "game" not in st.session_state:
        st.session_state.game = MilkMarketGame()
    game = st.session_state.game
    if "production_choice" not in st.session_state:
        st.session_state.production_choice = 700
    if "price_choice" not in st.session_state:
        st.session_state.price_choice = 1.55
    if "turn_message" not in st.session_state:
        st.session_state.turn_message = ""
    if "last_turn_summary" not in st.session_state:
        st.session_state.last_turn_summary = "No turns played yet."
    if st.session_state.price_choice > game.allowed_price_max():
        st.session_state.price_choice = game.allowed_price_max()


def money(value: float) -> str:
    return f"${value:,.2f}"


def apply_recommended() -> None:
    game = st.session_state.game
    prod, price = game.recommended_controls()
    st.session_state.production_choice = prod
    st.session_state.price_choice = price
    st.session_state.turn_message = f"Applied analyst recommendation: production {prod:,}, price {money(price)}."


def match_cap() -> None:
    game = st.session_state.game
    if game.price_cap is None:
        st.session_state.turn_message = "There is no cap to match yet."
        return
    st.session_state.price_choice = game.allowed_price_max()
    st.session_state.turn_message = f"Price matched to the legal ceiling of {money(game.allowed_price_max())}."


def set_at_cost() -> None:
    game = st.session_state.game
    st.session_state.price_choice = min(max(game.cost_per_unit, game.price_floor), game.allowed_price_max())
    st.session_state.turn_message = f"Price set to the cost line at {money(st.session_state.price_choice)}."


def restart_game() -> None:
    st.session_state.game = MilkMarketGame()
    st.session_state.production_choice = 700
    st.session_state.price_choice = 1.55
    st.session_state.turn_message = "Campaign restarted."
    st.session_state.last_turn_summary = "No turns played yet."


def resolve_turn() -> None:
    game = st.session_state.game
    if game.game_over():
        return
    result = game.resolve_turn(
        int(st.session_state.production_choice),
        float(st.session_state.price_choice),
    )
    st.session_state.last_turn_summary = (
        f"Turn {result.turn}: produced {result.production:,}, sold {result.sold:,}, demand {result.demand:,}, "
        f"profit {money(result.profit)}, vault {money(result.vault)}."
    )
    if not game.game_over() and st.session_state.price_choice > game.allowed_price_max():
        st.session_state.price_choice = game.allowed_price_max()
    if game.game_over():
        st.session_state.turn_message = (
            f"Bankruptcy on turn {result.turn}. Final vault: {money(result.vault)}."
        )
    else:
        st.session_state.turn_message = (
            f"Turn {result.turn} resolved: revenue {money(result.revenue)}, total costs {money(result.total_cost)}, "
            f"profit {money(result.profit)}."
        )


def pressure_card(game: MilkMarketGame) -> str:
    pressure = round(game.policy_pressure())
    if game.price_cap is None:
        text = "Pressure: 0% — no formal ceiling yet."
    else:
        relation = "above cost" if game.price_cap >= game.cost_per_unit else "below cost"
        text = f"Pressure: {pressure}% — cap {relation} at {money(game.price_cap)} versus unit cost {money(game.cost_per_unit)}."
    return f"""
    <div class="hero-card">
        <div class="panel-title">Policy pressure</div>
        <div class="pressure-track"><div class="pressure-fill" style="width:{pressure}%;"></div></div>
        <div class="pressure-text">{text}</div>
    </div>
    """


def situation_card(game: MilkMarketGame) -> str:
    cap_text = "None" if game.price_cap is None else money(game.price_cap)
    ratio = game.cap_to_cost_ratio()
    ratio_text = "—" if ratio is None else f"{ratio:.2f}x"
    alert = (
        "No controls yet. The market still speaks."
        if game.price_cap is None
        else (
            "The cap binds, but still sits above cost."
            if game.price_cap >= game.cost_per_unit
            else "The ceiling is below cost. Every legal sale bleeds the dairy."
        )
    )
    return f"""
    <div class="panel-card">
        <div class="panel-title">Current situation</div>
        <div class="compact-metrics">
            <div class="metric-row"><span class="metric-label">Turn</span><span class="metric-value">{game.turn}</span></div>
            <div class="metric-row"><span class="metric-label">Vault</span><span class="metric-value green">{money(game.vault)}</span></div>
            <div class="metric-row"><span class="metric-label">Cumulative profit</span><span class="metric-value">{money(game.cumulative_profit)}</span></div>
            <div class="metric-row"><span class="metric-label">Unit cost</span><span class="metric-value">{money(game.cost_per_unit)}</span></div>
            <div class="metric-row"><span class="metric-label">Price cap</span><span class="metric-value gold">{cap_text}</span></div>
            <div class="metric-row"><span class="metric-label">Cap / cost</span><span class="metric-value">{ratio_text}</span></div>
            <div class="metric-row"><span class="metric-label">Elasticity</span><span class="metric-value">{game.elasticity:.2f}</span></div>
        </div>
        <div class="warning-line">{alert}</div>
    </div>
    """


def hero_block(game: MilkMarketGame) -> None:
    logo_path = Path(__file__).resolve().with_name("logo.png")
    left, middle, right = st.columns([1.15, 1.75, 1.05], gap="large")
    with left:
        st.markdown('<div class="hero-card">', unsafe_allow_html=True)
        brand_left, brand_right = st.columns([0.42, 0.58], gap="small")
        with brand_left:
            if logo_path.exists():
                st.image(str(logo_path), use_container_width=True)
        with brand_right:
            st.markdown(
                f"""
                <div class="big-title">MilkSA</div>
                <div class="subtitle">Price Cap Panic — run the dairy, price the milk, and watch the ceiling close like a vise.</div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)
    with middle:
        st.markdown(
            f"""
            <div class="hero-card">
                <div class="phase-title">{game.phase_label}</div>
                <div class="phase-stats">Turn {game.turn} • survived {game.turns_survived} completed turns • vault {money(game.vault)} • cumulative profit {money(game.cumulative_profit)}</div>
                <div class="news-line">{game.current_news}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(pressure_card(game), unsafe_allow_html=True)


def market_card(game: MilkMarketGame) -> None:
    st.markdown(
        f"""
        <div class="panel-card">
            <div class="panel-title">Market desk</div>
            <div class="small-note">Forecast baseline demand is roughly <b>{game.forecast_baseline:,}</b> units near the reference price of <b>{money(game.reference_price)}</b>. This turn's elasticity is <b>{game.elasticity:.2f}</b>, so demand will react sharply to price changes.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def controls_panel(game: MilkMarketGame) -> None:
    st.markdown('<div class="controls-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Manager controls</div>', unsafe_allow_html=True)
    st.session_state.production_choice = st.slider(
        "Production (units of milk)",
        min_value=0,
        max_value=game.max_production,
        value=int(st.session_state.production_choice),
        step=10,
        key="production_slider",
    )
    max_price = float(game.allowed_price_max())
    price_default = float(min(max(st.session_state.price_choice, game.price_floor), max_price))
    st.session_state.price_choice = st.slider(
        "Sale price per unit",
        min_value=float(game.price_floor),
        max_value=max_price,
        value=price_default,
        step=0.01,
        key="price_slider",
    )

    b1, b2, b3 = st.columns(3, gap="small")
    with b1:
        st.button("Recommended", use_container_width=True, on_click=apply_recommended)
    with b2:
        st.button("Match cap", use_container_width=True, on_click=match_cap)
    with b3:
        st.button("At cost", use_container_width=True, on_click=set_at_cost)

    estimate = game.estimate_turn(st.session_state.production_choice, st.session_state.price_choice)
    demand = int(estimate["demand"])
    sold = int(estimate["sold"])
    wasted = int(estimate["wasted"])
    profit = float(estimate["profit"])
    revenue = float(estimate["revenue"])
    costs = float(estimate["total_cost"])

    st.markdown(
        f"""
        <div class="small-note spacer-tight">Forecast at <b>{money(st.session_state.price_choice)}</b>: demand ≈ <b>{demand:,}</b>; expected sales ≈ <b>{sold:,}</b>; spoilage ≈ <b>{wasted:,}</b>.</div>
        <div class="small-note">Projected revenue <b>{money(revenue)}</b> versus projected total costs <b>{money(costs)}</b> for an estimated result of <b>{money(profit)}</b>.</div>
        """,
        unsafe_allow_html=True,
    )

    a1, a2 = st.columns([1, 1], gap="small")
    with a1:
        st.button(
            "End turn",
            type="primary",
            use_container_width=True,
            on_click=resolve_turn,
            disabled=game.game_over(),
        )
    with a2:
        st.button("Restart", use_container_width=True, on_click=restart_game)

    if st.session_state.turn_message:
        if game.game_over():
            st.error(st.session_state.turn_message)
        else:
            st.info(st.session_state.turn_message)
    st.markdown('</div>', unsafe_allow_html=True)


def rules_panel() -> None:
    with st.expander("Rules of the game", expanded=False):
        st.markdown(
            """
            - Choose **production** and **sale price** each turn.
            - Demand is **elastic**: higher prices reduce quantity demanded.
            - Unsold milk spoils and adds waste cost.
            - Every turn also includes a fixed operating cost.
            - From turn 6 onward, the state imposes a ceiling and cuts it by **10%** each turn.
            - The game ends only when the dairy is **bankrupt**.
            """
        )


def make_price_chart(game: MilkMarketGame) -> go.Figure:
    fig = go.Figure()
    turns = [r.turn for r in game.history]
    fig.add_trace(
        go.Scatter(
            x=turns,
            y=[r.price for r in game.history],
            mode="lines+markers",
            name="Manager price",
            line=dict(color=PALETTE["primary_100"], width=3),
        )
    )
    if any(r.cap is not None for r in game.history):
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=[r.cap for r in game.history],
                mode="lines+markers",
                name="Price cap",
                line=dict(color=PALETTE["accent_200"], width=3, dash="dash"),
            )
        )
    if turns:
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=[game.cost_per_unit for _ in turns],
                mode="lines",
                name="Unit cost",
                line=dict(color=PALETTE["primary_200"], width=2, dash="dot"),
            )
        )
    fig.update_layout(
        title="Prices: manager, cap, and cost (per unit)",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12,30,40,0.75)",
        font=dict(color=PALETTE["text_100"]),
        margin=dict(l=22, r=18, t=44, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_title="Turn",
        yaxis_title="Price",
        height=360,
    )
    return fig


def make_vault_chart(game: MilkMarketGame) -> go.Figure:
    fig = go.Figure()
    turns = [r.turn for r in game.history]
    vault_x = [0] + turns
    vault_y = [game.starting_vault] + [r.vault for r in game.history]
    fig.add_trace(
        go.Scatter(
            x=vault_x,
            y=vault_y,
            mode="lines+markers",
            name="Vault",
            line=dict(color=PALETTE["primary_100"], width=3),
        )
    )
    colors = [PALETTE["accent_100"] if r.profit >= 0 else PALETTE["loss"] for r in game.history]
    fig.add_trace(
        go.Bar(
            x=turns,
            y=[r.profit for r in game.history],
            name="Per-turn result",
            marker_color=colors,
            opacity=0.88,
        )
    )
    fig.update_layout(
        title="Vault and profit",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(12,30,40,0.75)",
        font=dict(color=PALETTE["text_100"]),
        margin=dict(l=22, r=18, t=44, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        xaxis_title="Turn",
        yaxis_title="Money",
        height=360,
        bargap=0.25,
    )
    fig.add_hline(y=0, line_dash="dot", line_color=PALETTE["bg_300"])
    return fig


def history_table(game: MilkMarketGame) -> None:
    st.markdown('<div class="panel-card">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Turn history</div>', unsafe_allow_html=True)
    if game.history:
        df = pd.DataFrame([r.to_display_dict() for r in game.history])
        st.dataframe(df, hide_index=True, use_container_width=True, height=585)
        st.caption(st.session_state.last_turn_summary)
    else:
        st.info("No turns played yet.")
    st.markdown('</div>', unsafe_allow_html=True)


def main() -> None:
    inject_css()
    init_state()
    game: MilkMarketGame = st.session_state.game

    hero_block(game)
    st.markdown('')

    left, center, right = st.columns([1.08, 1.55, 1.22], gap="large")

    with left:
        controls_panel(game)
        st.markdown('')
        st.markdown(situation_card(game), unsafe_allow_html=True)
        st.markdown('')
        rules_panel()

    with center:
        market_card(game)
        st.markdown('')
        if game.history:
            st.plotly_chart(make_price_chart(game), use_container_width=True)
            st.plotly_chart(make_vault_chart(game), use_container_width=True)
        else:
            st.plotly_chart(make_price_chart(game), use_container_width=True)
            st.plotly_chart(make_vault_chart(game), use_container_width=True)

    with right:
        history_table(game)

    if game.game_over():
        st.error(
            f"The dairy is bankrupt. Final vault: {money(game.vault)}. The game ends only when the company can no longer survive the cap."
        )


if __name__ == "__main__":
    main()
