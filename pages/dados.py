import streamlit as st
import numpy as np
import pandas as pd
from data import download_prices, get_returns, get_annualized_vol, get_corr_matrix, get_cov_matrix, TICKERS_ALL, TICKER_LABELS
from charts import line_chart, histogram, heatmap

def show():
    st.markdown('<div class="main-header">📥 Importação e Tratamento de Dados</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        tickers_sel = st.multiselect(
            "Selecione os ativos", TICKERS_ALL,
            default=["CL=F", "GC=F", "ZS=F", "NG=F", "GLD", "USO", "SLV"],
            format_func=lambda t: f"{t} — {TICKER_LABELS.get(t, t)}"
        )
    with col2:
        period = st.selectbox("Período", ["1y", "2y", "3y", "5y"], index=1)

    if not tickers_sel:
        st.info("Selecione ao menos um ativo.")
        return

    with st.spinner("Baixando dados..."):
        prices = download_prices(tickers_sel, period=period)

    if prices.empty:
        st.error("Falha ao carregar dados.")
        return

    returns = get_returns(prices)
    vol     = get_annualized_vol(returns)
    corr    = get_corr_matrix(returns)
    cov     = get_cov_matrix(returns)

    # ── Estatísticas básicas ─────────────
    st.markdown('<div class="section-title">Estatísticas dos Retornos Log</div>', unsafe_allow_html=True)
    stats = returns.describe().T
    stats["vol_anual"] = vol
    stats.index = [TICKER_LABELS.get(i, i) for i in stats.index]
    st.dataframe(stats.style.format("{:.6f}").set_properties(**{
        "background-color": "#0f1729", "color": "#e0e6f0", "border": "1px solid #1e2d40"
    }), use_container_width=True)

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Preços", "📉 Retornos", "🔗 Correlação", "📦 Covariância"])

    with tab1:
        sel = [t for t in tickers_sel if t in prices.columns]
        norm = (prices[sel] / prices[sel].iloc[0] * 100)
        norm.columns = [TICKER_LABELS.get(c, c) for c in norm.columns]
        st.plotly_chart(line_chart(norm, "Preços Normalizados (Base 100)"), use_container_width=True)

        st.markdown('<div class="section-title">Dados Brutos</div>', unsafe_allow_html=True)
        display = prices[sel].copy()
        display.columns = [TICKER_LABELS.get(c, c) for c in display.columns]
        st.dataframe(display.tail(30).style.format("{:.2f}").set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)

    with tab2:
        sel_r = [t for t in tickers_sel if t in returns.columns]
        ret_disp = returns[sel_r].copy()
        ret_disp.columns = [TICKER_LABELS.get(c, c) for c in ret_disp.columns]
        st.plotly_chart(line_chart(ret_disp, "Retornos Logarítmicos Diários"), use_container_width=True)

        chosen = st.selectbox("Histograma de retornos", list(ret_disp.columns))
        if chosen:
            col = ret_disp[chosen].dropna()
            st.plotly_chart(histogram(col.values, title=f"Distribuição — {chosen}"), use_container_width=True)

    with tab3:
        if len(sel_r) >= 2:
            corr_disp = corr.loc[sel_r, sel_r].copy()
            corr_disp.index   = [TICKER_LABELS.get(i, i) for i in corr_disp.index]
            corr_disp.columns = [TICKER_LABELS.get(c, c) for c in corr_disp.columns]
            st.plotly_chart(heatmap(corr_disp, "Matriz de Correlação"), use_container_width=True)
        else:
            st.info("Selecione ao menos 2 ativos para ver correlação.")

    with tab4:
        if len(sel_r) >= 2:
            cov_disp = cov.loc[sel_r, sel_r].copy()
            cov_disp.index   = [TICKER_LABELS.get(i, i) for i in cov_disp.index]
            cov_disp.columns = [TICKER_LABELS.get(c, c) for c in cov_disp.columns]
            st.dataframe(cov_disp.style.format("{:.6f}").set_properties(**{
                "background-color": "#0f1729", "color": "#e0e6f0"
            }), use_container_width=True)
        else:
            st.info("Selecione ao menos 2 ativos.")
