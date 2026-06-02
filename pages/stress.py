import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import bs_price, b76_price
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, LAYOUT_BASE, PALETTE
from data import download_prices, get_returns, get_annualized_vol, PORTFOLIO, TICKER_LABELS, RISK_FREE_RATE

SCENARIOS = {
    "Recessão Global (CL=F −25%)":      {"CL=F": -0.25},
    "Fuga para Segurança (GC=F +15%)":  {"GC=F": +0.15},
    "Choque Oferta Gás (NG=F +40%)":    {"NG=F": +0.40},
    "Safra Recorde Soja (ZS=F −20%)":   {"ZS=F": -0.20},
    "Stress Brasil (USDBRL +15%)":      {"GLD": -0.05, "USO": -0.08, "SLV": -0.06},
    "Crise Volatilidade (+50% Vol)":    {"__vol": +0.50},
    "Contágio Sistêmico (Corr 0.85)":   {"__corr": 0.85},
}

def compute_pnl_stress(scenario_shocks, prices_df, vol_hist):
    r = RISK_FREE_RATE
    total_pnl = 0.0
    breakdown = []

    for pos in PORTFOLIO:
        t   = pos["asset"]
        qty = pos["qty"]
        dir_sign = 1 if pos["direction"] == "long" else -1

        S0 = prices_df[t].iloc[-1] if t in prices_df.columns else 50.0
        shock = scenario_shocks.get(t, 0.0)
        vol_shock = scenario_shocks.get("__vol", 0.0)

        S1 = S0 * (1 + shock)

        if pos["type"] == "future":
            pnl = (S1 - S0) * qty * dir_sign
            instrument = "Futuro"
        else:
            T      = pos["maturity_days"] / 365
            sig0   = vol_hist.get(t, 0.25)
            sig1   = sig0 * (1 + vol_shock)
            K      = S0
            ot     = pos["option_type"]
            p0     = bs_price(S0, K, r, T, sig0, ot)
            p1     = bs_price(S1, K, r, T, sig1, ot)
            pnl    = (p1 - p0) * qty * dir_sign
            instrument = f"Opção {ot.upper()}"

        total_pnl += pnl
        breakdown.append({
            "Ativo":      t,
            "Nome":       TICKER_LABELS.get(t, t),
            "Instrumento": instrument,
            "Direção":    pos["direction"].capitalize(),
            "Qtd":        qty,
            "Shock":      f"{shock*100:+.1f}%",
            "P&L":        pnl,
        })

    return total_pnl, pd.DataFrame(breakdown)


def show():
    st.markdown('<div class="main-header">💥 Stress Testing</div>', unsafe_allow_html=True)

    with st.spinner("Carregando dados..."):
        tickers = list({p["asset"] for p in PORTFOLIO})
        prices_df = download_prices(tickers)
        returns   = get_returns(prices_df)
        vol_hist  = get_annualized_vol(returns)

    if prices_df.empty:
        st.error("Dados indisponíveis.")
        return

    # ── Seleção de cenários ───────────────
    st.markdown('<div class="section-title">Cenários de Stress</div>', unsafe_allow_html=True)
    sel_scenarios = st.multiselect(
        "Selecione os cenários a executar",
        list(SCENARIOS.keys()),
        default=list(SCENARIOS.keys())
    )

    if not sel_scenarios:
        st.info("Selecione ao menos um cenário.")
        return

    pv = st.number_input("Valor base da carteira (USD)", value=10_000_000,
                         step=500_000, format="%d")

    # ── Executar todos os cenários ────────
    results = {}
    for sc in sel_scenarios:
        shocks = SCENARIOS[sc]
        total_pnl, breakdown = compute_pnl_stress(shocks, prices_df, vol_hist)
        results[sc] = {"total_pnl": total_pnl, "breakdown": breakdown}

    # ── Gráfico de perdas por cenário ─────
    st.markdown('<div class="section-title">P&L Total por Cenário</div>', unsafe_allow_html=True)
    names  = list(results.keys())
    totals = [results[n]["total_pnl"] for n in names]
    colors = [GREEN if t >= 0 else RED for t in totals]

    fig = go.Figure(go.Bar(
        x=[t / 1e6 for t in totals], y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{'+'if t>=0 else ''}{t/1e6:.2f}M" for t in totals],
        textposition="outside",
        hovertemplate="%{y}<br>P&L: $%{x:.3f}M<extra></extra>"
    ))
    fig.update_layout(
        xaxis_title="P&L (USD M)",
        title=dict(text="Impacto de Stress por Cenário", font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig, use_container_width=True)

    # Pior cenário
    worst_idx = np.argmin(totals)
    worst_name = names[worst_idx]
    worst_pnl  = totals[worst_idx]

    st.error(f"🔴 Pior cenário: **{worst_name}** → P&L = ${worst_pnl/1e6:.2f}M ({worst_pnl/pv*100:.1f}% da carteira)")

    # ── Drill-down por cenário ─────────────
    st.markdown('<div class="section-title">Detalhamento por Posição</div>', unsafe_allow_html=True)
    chosen = st.selectbox("Cenário para detalhar", sel_scenarios)
    df_detail = results[chosen]["breakdown"]

    # Colorir P&L
    def pnl_style(v):
        try:
            return f"color: {'#00e676' if v >= 0 else '#ff4d6d'}"
        except:
            return ""

    df_show = df_detail.copy()
    df_show["P&L (USD)"] = df_show["P&L"].apply(lambda x: f"{'+'if x>=0 else ''}{x:,.0f}")

    st.dataframe(
        df_show[["Ativo", "Nome", "Instrumento", "Direção", "Qtd", "Shock", "P&L (USD)"]].style
            .applymap(lambda v: f"color: {'#00e676' if '+' in str(v) and v!='N/A' else '#ff4d6d'}",
                      subset=["P&L (USD)"])
            .set_properties(**{"background-color": "#0f1729", "color": "#e0e6f0",
                                "border": "1px solid #1e2d40"}),
        use_container_width=True, hide_index=True
    )

    # ── Gráfico por ativo dentro do cenário ─
    fig2 = go.Figure(go.Bar(
        x=df_detail["Ativo"].tolist(),
        y=(df_detail["P&L"] / 1e6).tolist(),
        marker_color=[GREEN if v >= 0 else RED for v in df_detail["P&L"]],
        text=[f"{v/1e6:+.3f}M" for v in df_detail["P&L"]],
        textposition="outside",
    ))
    fig2.update_layout(
        yaxis_title="P&L (USD M)", xaxis_title="Ativo",
        title=dict(text=f"P&L por Ativo — {chosen}", font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Heatmap de perdas ─────────────────
    st.markdown('<div class="section-title">Heatmap de Perdas (Cenário × Ativo)</div>', unsafe_allow_html=True)
    assets = [p["asset"] for p in PORTFOLIO]
    matrix = pd.DataFrame(index=sel_scenarios, columns=assets, dtype=float)

    for sc in sel_scenarios:
        df_sc = results[sc]["breakdown"].set_index("Ativo")
        for a in assets:
            matrix.loc[sc, a] = df_sc.loc[a, "P&L"] / 1e6 if a in df_sc.index else 0.0

    import plotly.graph_objects as go_
    fig3 = go_.Figure(go_.Heatmap(
        z=matrix.values.astype(float),
        x=assets,
        y=sel_scenarios,
        colorscale=[[0, RED], [0.5, "#0f1729"], [1, GREEN]],
        zmid=0,
        text=matrix.round(2).values.astype(str),
        texttemplate="%{text}M",
        hovertemplate="%{y}<br>%{x}<br>%{z:.3f}M<extra></extra>",
    ))
    fig3.update_layout(
        title=dict(text="Heatmap de P&L por Cenário × Ativo (USD M)",
                   font=dict(color=CYAN, size=13)),
        xaxis_title="Ativo", yaxis_title="Cenário",
        paper_bgcolor=LAYOUT_BASE["paper_bgcolor"],
        plot_bgcolor=LAYOUT_BASE["plot_bgcolor"],
        font=LAYOUT_BASE["font"],
        margin=dict(l=200, r=20, t=40, b=40),
        height=max(350, len(sel_scenarios) * 55 + 80),
    )
    st.plotly_chart(fig3, use_container_width=True)
