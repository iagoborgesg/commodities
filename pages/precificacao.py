import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import bs_price, b76_price, bs_d1, b76_d1, greeks_bs
from charts import LAYOUT_BASE, CYAN, GREEN, RED, YELLOW, PALETTE

def show():
    st.markdown('<div class="main-header">💰 Precificação de Opções</div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Black-Scholes", "Black-76", "Comparação BS × B76"])

    # ── Black-Scholes ─────────────────────
    with tab1:
        st.markdown('<div class="section-title">Black-Scholes — Opções sobre ETFs</div>', unsafe_allow_html=True)
        st.latex(r"C = S_0 N(d_1) - K e^{-rT} N(d_2)")
        st.latex(r"P = K e^{-rT} N(-d_2) - S_0 N(-d_1)")

        c1, c2, c3 = st.columns(3)
        with c1:
            S  = st.number_input("Preço do ativo (S₀)", value=50.0, min_value=0.01, step=0.5, key="bs_S")
            K  = st.number_input("Strike (K)", value=50.0, min_value=0.01, step=0.5, key="bs_K")
        with c2:
            r  = st.number_input("Taxa livre de risco (r) %", value=5.3, min_value=0.0, step=0.1, key="bs_r") / 100
            T  = st.number_input("Vencimento (dias)", value=90, min_value=1, step=1, key="bs_T") / 365
        with c3:
            sigma = st.number_input("Volatilidade (σ) %", value=25.0, min_value=0.1, step=0.5, key="bs_sig") / 100
            opt_type = st.selectbox("Tipo", ["call", "put"], key="bs_type")

        price = bs_price(S, K, r, T, sigma, opt_type)
        greeks = greeks_bs(S, K, r, T, sigma, opt_type)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        for col, label, val, fmt in [
            (m1, "Preço", price, ".4f"),
            (m2, "Delta", greeks["delta"], ".4f"),
            (m3, "Gamma", greeks["gamma"], ".6f"),
            (m4, "Vega", greeks["vega"], ".4f"),
            (m5, "Theta", greeks["theta"], ".4f"),
            (m6, "Rho", greeks["rho"], ".4f"),
        ]:
            col.markdown(f"""<div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value" style="font-size:1.2rem">{val:{fmt}}</div>
            </div>""", unsafe_allow_html=True)

        # Gráfico preço vs spot
        st.markdown('<div class="section-title">Preço vs Spot</div>', unsafe_allow_html=True)
        spots = np.linspace(S * 0.6, S * 1.4, 200)
        prices_call = [bs_price(s, K, r, T, sigma, "call") for s in spots]
        prices_put  = [bs_price(s, K, r, T, sigma, "put")  for s in spots]
        intrinsic_c = np.maximum(spots - K, 0)
        intrinsic_p = np.maximum(K - spots, 0)

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=spots, y=prices_call, name="Call BS", line=dict(color=CYAN, width=2)))
        fig.add_trace(go.Scatter(x=spots, y=prices_put,  name="Put BS",  line=dict(color=GREEN, width=2)))
        fig.add_trace(go.Scatter(x=spots, y=intrinsic_c, name="Intrínseco Call",
                                 line=dict(color=CYAN, dash="dot", width=1), opacity=0.5))
        fig.add_trace(go.Scatter(x=spots, y=intrinsic_p, name="Intrínseco Put",
                                 line=dict(color=GREEN, dash="dot", width=1), opacity=0.5))
        fig.add_vline(x=S, line_color=YELLOW, line_dash="dash", annotation_text="S atual")
        fig.add_vline(x=K, line_color=RED,    line_dash="dash", annotation_text="Strike")
        fig.update_layout(xaxis_title="Spot", yaxis_title="Preço", **LAYOUT_BASE)
        st.plotly_chart(fig, use_container_width=True)

    # ── Black-76 ─────────────────────────
    with tab2:
        st.markdown('<div class="section-title">Black-76 — Opções sobre Futuros</div>', unsafe_allow_html=True)
        st.latex(r"C = e^{-rT}[F N(d_1) - K N(d_2)]")
        st.latex(r"P = e^{-rT}[K N(-d_2) - F N(-d_1)]")

        c1, c2, c3 = st.columns(3)
        with c1:
            F  = st.number_input("Preço do Futuro (F)", value=80.0, min_value=0.01, step=0.5, key="b76_F")
            K2 = st.number_input("Strike (K)", value=80.0, min_value=0.01, step=0.5, key="b76_K")
        with c2:
            r2 = st.number_input("Taxa livre de risco (r) %", value=5.3, step=0.1, key="b76_r") / 100
            T2 = st.number_input("Vencimento (dias)", value=90, min_value=1, key="b76_T") / 365
        with c3:
            sig2 = st.number_input("Volatilidade (σ) %", value=30.0, min_value=0.1, step=0.5, key="b76_sig") / 100
            opt2 = st.selectbox("Tipo", ["call", "put"], key="b76_type")

        price2 = b76_price(F, K2, r2, T2, sig2, opt2)

        m1, m2 = st.columns(2)
        m1.markdown(f"""<div class="metric-card">
            <div class="metric-label">Preço Black-76</div>
            <div class="metric-value">{price2:.4f}</div>
        </div>""", unsafe_allow_html=True)

        # Sensibilidade sigma
        sigs = np.linspace(0.05, 1.0, 200)
        p_sig = [b76_price(F, K2, r2, T2, s, opt2) for s in sigs]
        fig2 = go.Figure(go.Scatter(x=sigs*100, y=p_sig, line=dict(color=CYAN, width=2)))
        fig2.add_vline(x=sig2*100, line_color=YELLOW, line_dash="dash", annotation_text="σ atual")
        fig2.update_layout(xaxis_title="Volatilidade (%)", yaxis_title="Preço Opção",
                           title=dict(text="Sensibilidade ao Sigma", font=dict(color=CYAN)),
                           **LAYOUT_BASE)
        st.plotly_chart(fig2, use_container_width=True)

    # ── Comparação ───────────────────────
    with tab3:
        st.markdown('<div class="section-title">Black-Scholes vs Black-76</div>', unsafe_allow_html=True)
        st.info("Fixando S = F, os modelos devem coincidir quando r → 0. Explore as diferenças abaixo.")

        S3   = st.slider("Spot / Futuro", 50.0, 150.0, 100.0, 1.0)
        K3   = st.slider("Strike", 50.0, 150.0, 100.0, 1.0)
        sig3 = st.slider("Vol %", 5, 80, 25) / 100
        T3   = st.slider("Dias", 10, 365, 90) / 365
        r3   = st.slider("Taxa % a.a.", 0.0, 10.0, 5.3) / 100

        call_bs = bs_price(S3, K3, r3, T3, sig3, "call")
        put_bs  = bs_price(S3, K3, r3, T3, sig3, "put")
        call_b76 = b76_price(S3, K3, r3, T3, sig3, "call")
        put_b76  = b76_price(S3, K3, r3, T3, sig3, "put")

        rows = [
            ["Call", f"{call_bs:.4f}", f"{call_b76:.4f}", f"{call_bs - call_b76:.4f}"],
            ["Put",  f"{put_bs:.4f}",  f"{put_b76:.4f}",  f"{put_bs - put_b76:.4f}"],
        ]
        df = pd.DataFrame(rows, columns=["Tipo", "Black-Scholes", "Black-76", "Diferença"])
        st.dataframe(df.set_index("Tipo").style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True)
