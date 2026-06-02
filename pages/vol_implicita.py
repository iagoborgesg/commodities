import streamlit as st
import numpy as np
import pandas as pd
from models import bs_price, b76_price, compare_iv_methods
from charts import CYAN, GREEN, RED, YELLOW, LAYOUT_BASE
import plotly.graph_objects as go
from data import download_prices, get_annualized_vol, get_returns, TICKER_LABELS, RISK_FREE_RATE

def show():
    st.markdown('<div class="main-header">🔍 Volatilidade Implícita</div>', unsafe_allow_html=True)

    st.latex(r"f(\sigma) = P_{\text{modelo}}(\sigma) - P_{\text{mercado}} = 0")

    tab1, tab2 = st.tabs(["Calculadora Manual", "Calcular dos Dados de Mercado"])

    with tab1:
        st.markdown('<div class="section-title">Calcular IV para opção específica</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            model   = st.selectbox("Modelo", ["Black-Scholes", "Black-76"])
            opt_type = st.selectbox("Tipo", ["call", "put"])
            P_mkt   = st.number_input("Preço de Mercado", value=5.0, min_value=0.01, step=0.1)
        with c2:
            S_or_F  = st.number_input("Spot / Futuro (S ou F)", value=100.0, min_value=0.01, step=1.0)
            K       = st.number_input("Strike (K)", value=100.0, min_value=0.01, step=1.0)
        with c3:
            r       = st.number_input("Taxa r (%)", value=5.3, step=0.1) / 100
            T       = st.number_input("Vencimento (dias)", value=90, min_value=1) / 365

        model_key = "bs" if "Scholes" in model else "b76"

        if st.button("▸ Calcular Volatilidade Implícita", type="primary"):
            results = compare_iv_methods(P_mkt, S_or_F, K, r, T, opt_type, model_key)

            st.markdown('<div class="section-title">Resultado por Método</div>', unsafe_allow_html=True)
            rows = []
            for name, res in results.items():
                iv_str = f"{res['iv']*100:.4f}%" if res['iv'] is not None else "N/C"
                err_str = f"{res['error']:.2e}" if res['error'] is not None else "—"
                time_str = f"{res['time']*1000:.3f} ms"
                status = "✅" if res["converged"] else "❌"
                rows.append([name, iv_str, res["iterations"], err_str, time_str, status])

            df = pd.DataFrame(rows, columns=["Método", "Vol. Implícita", "Iterações", "Erro Final", "Tempo", "Convergiu"])
            st.dataframe(df.set_index("Método").style.set_properties(**{
                "background-color": "#0f1729", "color": "#e0e6f0", "border": "1px solid #1e2d40"
            }), use_container_width=True)

            # Verificação
            first_iv = next((r["iv"] for r in results.values() if r["iv"] is not None), None)
            if first_iv:
                if model_key == "bs":
                    price_check = bs_price(S_or_F, K, r, T, first_iv, opt_type)
                else:
                    price_check = b76_price(S_or_F, K, r, T, first_iv, opt_type)

                st.success(f"✔ Verificação: σ = {first_iv*100:.4f}% → Preço recalculado = {price_check:.4f} (mercado = {P_mkt:.4f}, erro = {abs(price_check - P_mkt):.2e})")

                # Gráfico f(sigma)
                sigs = np.linspace(0.01, 3.0, 500)
                if model_key == "bs":
                    fs = [bs_price(S_or_F, K, r, T, s, opt_type) - P_mkt for s in sigs]
                else:
                    fs = [b76_price(S_or_F, K, r, T, s, opt_type) - P_mkt for s in sigs]

                fig = go.Figure()
                fig.add_trace(go.Scatter(x=sigs*100, y=fs, name="f(σ)", line=dict(color=CYAN, width=2)))
                fig.add_hline(y=0, line_color=YELLOW, line_dash="dash")
                fig.add_vline(x=first_iv*100, line_color=GREEN, line_dash="dash",
                              annotation_text=f"σ_imp = {first_iv*100:.2f}%")
                fig.update_layout(
                    xaxis_title="Volatilidade σ (%)", yaxis_title="f(σ) = Modelo − Mercado",
                    title=dict(text="Função Objetivo — Raiz = Volatilidade Implícita",
                               font=dict(color=CYAN, size=13)),
                    **LAYOUT_BASE
                )
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-title">IV Estimada para Ativos da Carteira</div>', unsafe_allow_html=True)
        st.info("A volatilidade implícita é estimada usando preço de mercado ≈ ATM com σ₀ histórico. "
                "Em produção, seria necessário cotações de opções reais.")

        with st.spinner("Carregando dados..."):
            prices = download_prices(["GLD", "USO", "SLV"])
            returns = get_returns(prices)
            vol_hist = get_annualized_vol(returns)

        options_cart = [
            {"asset": "GLD",  "option_type": "call", "T_days": 90,  "qty": 25000},
            {"asset": "USO",  "option_type": "put",  "T_days": 120, "qty": 40000},
            {"asset": "SLV",  "option_type": "call", "T_days": 180, "qty": 30000},
        ]

        rows = []
        for opt in options_cart:
            t = opt["asset"]
            if t not in prices.columns:
                continue
            S   = prices[t].iloc[-1]
            K   = S  # ATM
            T   = opt["T_days"] / 365
            r   = RISK_FREE_RATE
            sig_hist = vol_hist.get(t, 0.3)

            # Simula preço de mercado como BS com vol histórica * 1.10 (prêmio de risco)
            P_mkt = bs_price(S, K, r, T, sig_hist * 1.10, opt["option_type"])

            res = compare_iv_methods(P_mkt, S, K, r, T, opt["option_type"], "bs")
            iv_brent = res["Brent"]["iv"]

            rows.append({
                "Ativo":        t,
                "Tipo":         opt["option_type"].upper(),
                "Venc (dias)":  opt["T_days"],
                "Preço Spot":   f"${S:.2f}",
                "Vol Hist":     f"{sig_hist*100:.1f}%",
                "Vol Implícita (Brent)": f"{iv_brent*100:.2f}%" if iv_brent else "N/C",
                "Prêmio de Vol": f"{(iv_brent - sig_hist)*100:.2f}%" if iv_brent else "N/C",
                "Preço Opção":  f"${P_mkt:.4f}",
            })

        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df.set_index("Ativo").style.set_properties(**{
                "background-color": "#0f1729", "color": "#e0e6f0"
            }), use_container_width=True)
