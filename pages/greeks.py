import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import greeks_bs, bs_price
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, PALETTE, LAYOUT_BASE
from data import download_prices, get_annualized_vol, get_returns, PORTFOLIO, RISK_FREE_RATE, TICKER_LABELS

def show():
    st.markdown('<div class="main-header">🔢 Greeks da Carteira</div>', unsafe_allow_html=True)

    with st.spinner("Calculando greeks..."):
        prices_df = download_prices(["GLD", "USO", "SLV"])
        returns   = get_returns(prices_df)
        vol_hist  = get_annualized_vol(returns)

    options = [p for p in PORTFOLIO if p["type"] == "option"]
    r = RISK_FREE_RATE

    rows = []
    for opt in options:
        t = opt["asset"]
        S = prices_df[t].iloc[-1] if t in prices_df.columns else 50.0
        T = opt["maturity_days"] / 365
        sig = vol_hist.get(t, 0.25)
        K   = S  # ATM
        ot  = opt["option_type"]
        dir_sign = 1 if opt["direction"] == "long" else -1
        qty = opt["qty"] * dir_sign

        price = bs_price(S, K, r, T, sig, ot)
        g = greeks_bs(S, K, r, T, sig, ot)

        rows.append({
            "Ativo":       t,
            "Nome":        TICKER_LABELS.get(t, t),
            "Tipo":        ot.upper(),
            "Direção":     opt["direction"].capitalize(),
            "Qtd":         f"{qty:+,}",
            "Preço":       f"${price:.4f}",
            "Vol (σ)":     f"{sig*100:.1f}%",
            "Delta":       g["delta"],
            "Gamma":       g["gamma"],
            "Vega":        g["vega"],
            "Theta":       g["theta"],
            "Rho":         g["rho"],
            "Δ Carteira":  g["delta"] * qty,
            "Vega Cart.":  g["vega"]  * qty,
        })

    df = pd.DataFrame(rows)

    # ── Tabela ───────────────────────────
    st.markdown('<div class="section-title">Greeks por Posição</div>', unsafe_allow_html=True)
    display_cols = ["Ativo", "Tipo", "Direção", "Qtd", "Preço", "Vol (σ)",
                    "Delta", "Gamma", "Vega", "Theta", "Rho"]

    def color_sign(val):
        try:
            v = float(str(val).replace("+","").replace(",",""))
            return f"color: {'#00e676' if v >= 0 else '#ff4d6d'}"
        except:
            return ""

    st.dataframe(
        df[display_cols].style
            .applymap(color_sign, subset=["Delta", "Gamma", "Vega", "Theta", "Rho"])
            .applymap(lambda v: f"color: {'#00e676' if v=='Long' else '#ff4d6d'}",
                      subset=["Direção"])
            .set_properties(**{"background-color": "#0f1729", "color": "#e0e6f0",
                                "border": "1px solid #1e2d40"}),
        use_container_width=True, hide_index=True
    )

    # ── Agregados da carteira ─────────────
    st.markdown('<div class="section-title">Exposição Agregada da Carteira</div>', unsafe_allow_html=True)
    total_delta = df["Δ Carteira"].sum()
    total_vega  = df["Vega Cart."].sum()
    total_gamma = sum(
        rows[i]["Gamma"] * int(rows[i]["Qtd"].replace("+","").replace(",",""))
        for i in range(len(rows))
    )

    m1, m2, m3, m4 = st.columns(4)
    for col, label, val in [
        (m1, "Delta Total", total_delta),
        (m2, "Vega Total", total_vega),
        (m3, "Gamma Total", total_gamma),
    ]:
        color = "#00e676" if val >= 0 else "#ff4d6d"
        col.markdown(f"""<div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value" style="color:{color};font-size:1.2rem">{val:+,.2f}</div>
        </div>""", unsafe_allow_html=True)

    m4.markdown(f"""<div class="metric-card">
        <div class="metric-label">Posição em Vega</div>
        <div class="metric-value" style="color:{'#00e676' if total_vega > 0 else '#ff4d6d'};font-size:1rem">
            {"📈 Comprado" if total_vega > 0 else "📉 Vendido"}
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Perguntas obrigatórias ────────────
    st.markdown('<div class="section-title">Análise Interpretativa</div>', unsafe_allow_html=True)
    vega_sign = "COMPRADA" if total_vega > 0 else "VENDIDA"
    max_vega_idx = df["Vega Cart."].abs().idxmax()

    st.markdown(f"""
    <div style='background:#0f1729;border:1px solid #1e2d40;border-radius:8px;padding:1.2rem;font-size:0.85rem;color:#e0e6f0;line-height:2'>
    <b style='color:#00d4ff'>1. A carteira está comprada ou vendida em volatilidade?</b><br>
    A carteira está <b style='color:{'#00e676' if total_vega > 0 else '#ff4d6d'}'>{vega_sign} em Vega</b>
    (Vega total = {total_vega:+.2f}). {"Ganha com aumento de volatilidade." if total_vega > 0 else "Perde com aumento de volatilidade."}<br><br>

    <b style='color:#00d4ff'>2. A carteira ganha ou perde com aumento da volatilidade?</b><br>
    {"✅ Ganha — posição long em Vega líquida." if total_vega > 0 else "❌ Perde — posição short em Vega líquida. Um choque de vol aumentaria as perdas da carteira."}<br><br>

    <b style='color:#00d4ff'>3. Qual opção tem maior Vega?</b><br>
    <b style='color:#ffd60a'>{df.loc[max_vega_idx, "Ativo"]}</b> ({df.loc[max_vega_idx, "Nome"]}) —
    Vega total = {df.loc[max_vega_idx, "Vega Cart."]:+.2f}<br><br>

    <b style='color:#00d4ff'>4. Qual commodity gera maior risco não-linear (Gamma)?</b><br>
    Gamma mede a curvatura do Delta. Posições compradas em opções têm Gamma positivo (risco não-linear favorável).
    Posições vendidas têm Gamma negativo (risco de convexidade adversa).
    </div>
    """, unsafe_allow_html=True)

    # ── Gráficos de Greeks ───────────────
    st.markdown('<div class="section-title">Perfil de Delta × Spot</div>', unsafe_allow_html=True)

    asset_sel = st.selectbox("Ativo para análise de sensibilidade",
                             [o["asset"] for o in options if o["asset"] in prices_df.columns])

    opt_row = next(o for o in options if o["asset"] == asset_sel)
    S_curr  = prices_df[asset_sel].iloc[-1]
    sig_    = vol_hist.get(asset_sel, 0.25)
    T_      = opt_row["maturity_days"] / 365
    K_      = S_curr

    spots = np.linspace(S_curr * 0.6, S_curr * 1.4, 200)
    deltas = [greeks_bs(s, K_, r, T_, sig_, opt_row["option_type"])["delta"] for s in spots]
    gammas = [greeks_bs(s, K_, r, T_, sig_, opt_row["option_type"])["gamma"] for s in spots]
    vegas  = [greeks_bs(s, K_, r, T_, sig_, opt_row["option_type"])["vega"]  for s in spots]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=spots, y=deltas, name="Delta", line=dict(color=CYAN, width=2)))
    fig.add_trace(go.Scatter(x=spots, y=[g * 100 for g in gammas], name="Gamma ×100",
                             line=dict(color=GREEN, width=2, dash="dot")))
    fig.add_vline(x=S_curr, line_color=YELLOW, line_dash="dash",
                  annotation_text=f"S = {S_curr:.2f}")
    fig.update_layout(
        xaxis_title="Spot", yaxis_title="Greek",
        title=dict(text=f"Delta e Gamma — {asset_sel} ({opt_row['option_type'].upper()})",
                   font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig, use_container_width=True)
