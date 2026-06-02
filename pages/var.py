import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import var_historico, var_parametrico, var_montecarlo, bs_price
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, LAYOUT_BASE, histogram
from data import download_prices, get_returns, get_annualized_vol, RISK_FREE_RATE

CONFIDENCE_LEVELS = (0.95, 0.99, 0.995)
CL_LABELS = {0.95: "95%", 0.99: "99%", 0.995: "99.5%"}

def show():
    st.markdown('<div class="main-header">📉 Value at Risk (VaR)</div>', unsafe_allow_html=True)

    # ── Seleção de ativo ─────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        asset = st.selectbox("Ativo de referência", ["GLD", "USO", "SLV", "CL=F", "GC=F"],
                             format_func=lambda x: x)
        n_sim = st.number_input("Simulações Monte Carlo", value=10000, min_value=1000,
                                max_value=100000, step=1000)
    with col2:
        pv = st.number_input("Valor da Carteira (USD)", value=10_000_000, step=500_000,
                             format="%d")
    with col3:
        horizon = st.selectbox("Horizonte", ["1 dia", "5 dias", "10 dias"])
        h_days = {"1 dia": 1, "5 dias": 5, "10 dias": 10}[horizon]

    with st.spinner("Calculando VaR..."):
        prices_df = download_prices([asset])
        returns   = get_returns(prices_df)

    if prices_df.empty or asset not in returns.columns:
        st.error("Dados indisponíveis.")
        return

    ret = returns[asset].dropna().values
    # Ajuste por horizonte (raiz do tempo)
    ret_h = ret * np.sqrt(h_days)

    S0    = prices_df[asset].iloc[-1]
    mu    = np.mean(ret)
    sigma = np.std(ret)

    # ── Calcular os 3 VaRs ───────────────
    var_hist   = var_historico(ret_h, pv)
    var_param  = var_parametrico(ret_h, pv)
    var_mc, pnl_mc = var_montecarlo(S0, mu * 252, sigma * np.sqrt(252),
                                     h_days / 252, pv, n_sim=int(n_sim))

    # ── KPIs ─────────────────────────────
    st.markdown('<div class="section-title">Resumo do VaR</div>', unsafe_allow_html=True)
    col_h = st.columns(3)
    for i, (label, var_dict) in enumerate([("Histórico", var_hist),
                                            ("Paramétrico", var_param),
                                            ("Monte Carlo", var_mc)]):
        with col_h[i]:
            st.markdown(f"<div class='section-title'>{label}</div>", unsafe_allow_html=True)
            for cl in CONFIDENCE_LEVELS:
                v = var_dict[cl]
                st.markdown(f"""<div class="metric-card">
                    <div class="metric-label">VaR {CL_LABELS[cl]}</div>
                    <div class="metric-value negative" style="font-size:1.1rem">
                        ${v:,.0f} ({v/pv*100:.2f}%)
                    </div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["VaR Histórico", "VaR Paramétrico", "VaR Monte Carlo", "Comparação"])

    with tab1:
        st.markdown('<div class="section-title">Distribuição Empírica dos Retornos</div>',
                    unsafe_allow_html=True)
        var_95 = var_hist[0.95] / pv
        fig = histogram(ret_h, title="Retornos × VaR Histórico", var_line=var_95)
        for cl in CONFIDENCE_LEVELS:
            v = -var_hist[cl] / pv
            fig.add_vline(x=v, line_color=[RED, ORANGE, PURPLE][list(CONFIDENCE_LEVELS).index(cl)],
                          line_dash="dash",
                          annotation_text=f"VaR {CL_LABELS[cl]}",
                          annotation_font_color=RED)
        st.plotly_chart(fig, use_container_width=True)

        df_h = pd.DataFrame([
            {"Nível": CL_LABELS[cl], "VaR ($)": f"${var_hist[cl]:,.0f}",
             "VaR (%)": f"{var_hist[cl]/pv*100:.3f}%"}
            for cl in CONFIDENCE_LEVELS
        ])
        st.dataframe(df_h.set_index("Nível").style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)

    with tab2:
        st.markdown('<div class="section-title">VaR Paramétrico — Assumindo Normalidade</div>',
                    unsafe_allow_html=True)
        st.latex(r"VaR_\alpha = z_\alpha \cdot \sigma_p \cdot V")

        from scipy.stats import norm
        z_vals = [norm.ppf(cl) for cl in CONFIDENCE_LEVELS]
        x = np.linspace(-4, 4, 500)
        fig_norm = go.Figure()
        fig_norm.add_trace(go.Scatter(
            x=x, y=norm.pdf(x),
            fill="tozeroy", fillcolor="rgba(0,212,255,0.1)",
            line=dict(color=CYAN, width=2), name="N(0,1)"
        ))
        for i, (cl, z) in enumerate(zip(CONFIDENCE_LEVELS, z_vals)):
            clr = [RED, ORANGE, PURPLE][i]
            fig_norm.add_vline(x=-z, line_color=clr, line_dash="dash",
                               annotation_text=f"-z({CL_LABELS[cl]})={-z:.2f}",
                               annotation_font_color=clr)
        fig_norm.update_layout(
            title=dict(text="Distribuição Normal — Quantis VaR", font=dict(color=CYAN, size=13)),
            xaxis_title="z", yaxis_title="Densidade",
            **LAYOUT_BASE
        )
        st.plotly_chart(fig_norm, use_container_width=True)

        df_p = pd.DataFrame([
            {"Nível": CL_LABELS[cl], "z": f"{z:.4f}",
             "VaR ($)": f"${var_param[cl]:,.0f}",
             "VaR (%)": f"{var_param[cl]/pv*100:.3f}%"}
            for cl, z in zip(CONFIDENCE_LEVELS, z_vals)
        ])
        st.dataframe(df_p.set_index("Nível").style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)

    with tab3:
        st.markdown('<div class="section-title">Simulação de Monte Carlo</div>', unsafe_allow_html=True)
        st.latex(r"S_T = S_0 \exp\!\left[(\mu - \tfrac{1}{2}\sigma^2)T + \sigma\sqrt{T}\,Z\right]")

        fig_mc = histogram(pnl_mc / pv, title=f"Distribuição P&L — {int(n_sim):,} cenários")
        for cl in CONFIDENCE_LEVELS:
            v = -var_mc[cl] / pv
            fig_mc.add_vline(x=v, line_color=RED, line_dash="dash",
                             annotation_text=f"VaR {CL_LABELS[cl]}")
        st.plotly_chart(fig_mc, use_container_width=True)

        df_mc = pd.DataFrame([
            {"Nível": CL_LABELS[cl],
             "VaR ($)": f"${var_mc[cl]:,.0f}",
             "VaR (%)": f"{var_mc[cl]/pv*100:.3f}%"}
            for cl in CONFIDENCE_LEVELS
        ])
        st.dataframe(df_mc.set_index("Nível").style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)

    with tab4:
        st.markdown('<div class="section-title">Comparação dos 3 Métodos</div>', unsafe_allow_html=True)
        rows = []
        for cl in CONFIDENCE_LEVELS:
            rows.append({
                "Nível":       CL_LABELS[cl],
                "Histórico":   f"${var_hist[cl]:,.0f}",
                "Paramétrico": f"${var_param[cl]:,.0f}",
                "Monte Carlo": f"${var_mc[cl]:,.0f}",
                "Subestimação Param.": f"{(var_param[cl] - var_hist[cl])/var_hist[cl]*100:+.1f}%",
            })
        df_cmp = pd.DataFrame(rows).set_index("Nível")
        st.dataframe(df_cmp.style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)

        # Gráfico de barras agrupadas
        x_ = [CL_LABELS[cl] for cl in CONFIDENCE_LEVELS]
        fig_cmp = go.Figure()
        for method, var_d, color in [
            ("Histórico", var_hist, CYAN),
            ("Paramétrico", var_param, GREEN),
            ("Monte Carlo", var_mc, YELLOW),
        ]:
            fig_cmp.add_trace(go.Bar(
                name=method, x=x_,
                y=[var_d[cl] for cl in CONFIDENCE_LEVELS],
                marker_color=color,
                text=[f"${var_d[cl]/1e6:.2f}M" for cl in CONFIDENCE_LEVELS],
                textposition="outside",
            ))
        fig_cmp.update_layout(
            barmode="group", yaxis_title="VaR (USD)",
            title=dict(text="Comparação VaR — 3 Métodos", font=dict(color=CYAN, size=13)),
            **LAYOUT_BASE
        )
        st.plotly_chart(fig_cmp, use_container_width=True)

        st.info("💡 O VaR paramétrico tende a subestimar o risco em caudas pesadas (fat tails). "
                "O método histórico captura a distribuição real dos retornos, incluindo assimetria e curtose.")
