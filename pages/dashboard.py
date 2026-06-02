import streamlit as st
import numpy as np
import pandas as pd
from data import download_prices, get_returns, get_annualized_vol, get_portfolio_summary, TICKER_LABELS, PORTFOLIO
from charts import line_chart, bar_chart, CYAN, GREEN, RED, YELLOW

def show():
    st.markdown('<div class="main-header">📊 Dashboard — Mesa de Commodities</div>', unsafe_allow_html=True)

    with st.spinner("Carregando dados de mercado..."):
        prices = download_prices()

    if prices.empty:
        st.error("Não foi possível carregar os dados. Verifique sua conexão.")
        return

    returns = get_returns(prices)
    vol     = get_annualized_vol(returns)
    latest  = prices.iloc[-1]
    prev    = prices.iloc[-2]
    chg     = (latest - prev) / prev * 100

    # ── KPIs ────────────────────────────────
    st.markdown('<div class="section-title">Mercado Atual</div>', unsafe_allow_html=True)

    main_tickers = ["CL=F", "GC=F", "ZS=F", "NG=F", "GLD", "USO", "SLV"]
    cols = st.columns(len(main_tickers))
    for i, t in enumerate(main_tickers):
        price = latest.get(t, np.nan)
        delta = chg.get(t, 0)
        color = "positive" if delta >= 0 else "negative"
        arrow = "▲" if delta >= 0 else "▼"
        with cols[i]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{TICKER_LABELS.get(t, t)}</div>
                <div class="metric-value">${price:,.2f}</div>
                <div style="color: {'#00e676' if delta >= 0 else '#ff4d6d'}; font-size:0.8rem; font-family: IBM Plex Mono">
                    {arrow} {delta:+.2f}%
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Gráficos principais ────────────────
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="section-title">Preços Normalizados (base 100)</div>', unsafe_allow_html=True)
        subset = [t for t in ["CL=F", "GC=F", "ZS=F", "NG=F"] if t in prices.columns]
        norm = (prices[subset] / prices[subset].iloc[0] * 100).dropna()
        norm.columns = [TICKER_LABELS.get(c, c) for c in norm.columns]
        fig = line_chart(norm, "")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-title">Volatilidade Histórica Anualizada</div>', unsafe_allow_html=True)
        vol_subset = vol[[t for t in main_tickers if t in vol.index]].sort_values(ascending=True)
        labels = [TICKER_LABELS.get(t, t) for t in vol_subset.index]
        fig2 = bar_chart(labels, vol_subset.values * 100, orientation="h")
        fig2.update_layout(xaxis_title="Vol % a.a.")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Tabela carteira ────────────────────
    st.markdown('<div class="section-title">Posições da Mesa</div>', unsafe_allow_html=True)
    df_port = get_portfolio_summary(prices)
    st.dataframe(
        df_port.style
            .applymap(lambda v: f"color: {GREEN}" if v == "Long"  else
                                f"color: {RED}"   if v == "Short" else "",
                      subset=["Direção"])
            .set_properties(**{"background-color": "#0f1729", "color": "#e0e6f0",
                                "border": "1px solid #1e2d40"}),
        use_container_width=True,
        hide_index=True,
    )

    # ── Retornos recentes ────────────────
    st.markdown('<div class="section-title">Retornos Diários (últimos 60 dias)</div>', unsafe_allow_html=True)
    ret60 = returns.tail(60)[[t for t in ["CL=F", "GC=F", "ZS=F", "NG=F"] if t in returns.columns]]
    ret60.columns = [TICKER_LABELS.get(c, c) for c in ret60.columns]
    fig3 = line_chart(ret60, "")
    fig3.add_hline(y=0, line_color="#1e2d40")
    st.plotly_chart(fig3, use_container_width=True)
