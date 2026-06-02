import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import iv_brent, bs_price
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, PALETTE, LAYOUT_BASE
from data import download_prices, get_annualized_vol, get_returns, RISK_FREE_RATE

def show():
    st.markdown('<div class="main-header">😄 Smile de Volatilidade</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Smile por Strike", "Superfície de Volatilidade"])

    with tab1:
        st.markdown('<div class="section-title">Construção do Smile</div>', unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            asset_sel = st.selectbox("Ativo", ["GLD", "USO", "SLV"], key="smile_asset")
            opt_type  = st.selectbox("Tipo", ["call", "put"], key="smile_type")
        with c2:
            T_days = st.slider("Vencimento (dias)", 30, 365, 90, key="smile_T")
            n_strikes = st.slider("Nº de Strikes", 5, 15, 9, key="smile_ns")
        with c3:
            moneyness_range = st.slider("Range de Moneyness (%)", 10, 50, 30, key="smile_range")

        with st.spinner("Calculando..."):
            prices_df = download_prices([asset_sel])
            returns   = get_returns(prices_df)
            vol_hist  = get_annualized_vol(returns)

        if prices_df.empty or asset_sel not in prices_df.columns:
            st.error("Dados indisponíveis.")
            return

        S       = prices_df[asset_sel].iloc[-1]
        sig_h   = vol_hist.get(asset_sel, 0.25)
        T       = T_days / 365
        r       = RISK_FREE_RATE

        # Grade de strikes
        lo = S * (1 - moneyness_range / 100)
        hi = S * (1 + moneyness_range / 100)
        strikes = np.linspace(lo, hi, n_strikes)
        moneyness = strikes / S  # K/S

        iv_list  = []
        price_list = []
        for K in strikes:
            # Simula preço de mercado: vol histórica + skew negativo realista
            skew_adj = -0.15 * (K / S - 1)   # skew negativo típico de equity/commodities
            sig_mkt  = max(0.05, sig_h * (1 + skew_adj + 0.08 * abs(K/S - 1)**0.5))
            p_mkt    = bs_price(S, K, r, T, sig_mkt, opt_type)
            price_list.append(p_mkt)

            # Calcula IV via Brent
            res = iv_brent(p_mkt, S, K, r, T, opt_type, "bs")
            iv_list.append(res["iv"] * 100 if res["iv"] else np.nan)

        # ── Smile Plot ────────────────────
        fig_smile = go.Figure()
        fig_smile.add_trace(go.Scatter(
            x=moneyness, y=iv_list,
            mode="lines+markers",
            name="Vol Implícita",
            line=dict(color=CYAN, width=2),
            marker=dict(size=8, symbol="circle"),
            hovertemplate="K/S: %{x:.3f}<br>Vol: %{y:.2f}%<extra></extra>"
        ))
        fig_smile.add_hline(y=sig_h*100, line_color=YELLOW, line_dash="dash",
                            annotation_text=f"Vol Histórica ({sig_h*100:.1f}%)")
        fig_smile.add_vline(x=1.0, line_color=RED, line_dash="dot",
                            annotation_text="ATM")
        fig_smile.update_layout(
            xaxis_title="Moneyness (K/S)",
            yaxis_title="Volatilidade Implícita (%)",
            title=dict(text=f"Smile de Volatilidade — {asset_sel} ({T_days}d {opt_type.upper()})",
                       font=dict(color=CYAN, size=13)),
            **LAYOUT_BASE
        )
        st.plotly_chart(fig_smile, use_container_width=True)

        # ── Tabela de dados ───────────────
        df_smile = pd.DataFrame({
            "Strike":         strikes.round(2),
            "Moneyness (K/S)": moneyness.round(4),
            "Preço Opção":    [f"${p:.4f}" for p in price_list],
            "Vol Implícita":  [f"{v:.3f}%" if not np.isnan(v) else "N/C" for v in iv_list],
        })
        st.dataframe(df_smile.style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0"
        }), use_container_width=True, hide_index=True)

        # ── Comparação hist × impl ────────
        st.markdown('<div class="section-title">Volatilidade Histórica × Implícita</div>', unsafe_allow_html=True)
        fig_comp = go.Figure()
        fig_comp.add_trace(go.Scatter(
            x=moneyness, y=iv_list, name="Vol Implícita",
            line=dict(color=CYAN, width=2), mode="lines+markers"
        ))
        fig_comp.add_hline(y=sig_h * 100, line_color=YELLOW, line_width=2,
                           annotation_text=f"Vol Histórica Anual ({sig_h*100:.1f}%)")
        fig_comp.update_layout(
            xaxis_title="Moneyness (K/S)", yaxis_title="Volatilidade (%)",
            title=dict(text="Hist. vs Implícita", font=dict(color=CYAN, size=13)),
            **LAYOUT_BASE
        )
        st.plotly_chart(fig_comp, use_container_width=True)

    with tab2:
        st.markdown('<div class="section-title">Superfície de Volatilidade (Strike × Vencimento)</div>',
                    unsafe_allow_html=True)

        asset2 = st.selectbox("Ativo", ["GLD", "USO", "SLV"], key="surf_asset")
        opt2   = st.selectbox("Tipo", ["call", "put"], key="surf_type")

        with st.spinner("Construindo superfície..."):
            prices_df2 = download_prices([asset2])
            returns2   = get_returns(prices_df2)
            vol_hist2  = get_annualized_vol(returns2)

        S2     = prices_df2[asset2].iloc[-1] if asset2 in prices_df2.columns else 50.0
        sig_h2 = vol_hist2.get(asset2, 0.25)
        r2     = RISK_FREE_RATE

        T_range = [30, 60, 90, 120, 180, 270, 365]
        K_range = np.linspace(S2 * 0.75, S2 * 1.25, 9)

        Z = np.zeros((len(T_range), len(K_range)))
        for i, T_days2 in enumerate(T_range):
            T2 = T_days2 / 365
            for j, K2 in enumerate(K_range):
                skew  = -0.15 * (K2 / S2 - 1)
                term  = 0.03 * np.sqrt(T2)
                sig_mkt = max(0.05, sig_h2 * (1 + skew + 0.05 * abs(K2/S2 - 1)**0.5) + term)
                p_mkt = bs_price(S2, K2, r2, T2, sig_mkt, opt2)
                res   = iv_brent(p_mkt, S2, K2, r2, T2, opt2, "bs")
                Z[i, j] = res["iv"] * 100 if res["iv"] else np.nan

        fig_surf = go.Figure(go.Surface(
            x=K_range.round(2),
            y=T_range,
            z=Z,
            colorscale=[[0, "#0f1729"], [0.3, "#00d4ff"], [0.7, "#ffd60a"], [1.0, "#ff4d6d"]],
            hovertemplate="Strike: %{x:.2f}<br>Venc: %{y}d<br>Vol: %{z:.2f}%<extra></extra>",
            showscale=True,
        ))
        fig_surf.update_layout(
            scene=dict(
                xaxis_title="Strike",
                yaxis_title="Vencimento (dias)",
                zaxis_title="Vol Implícita (%)",
                bgcolor=LAYOUT_BASE["paper_bgcolor"],
            ),
            paper_bgcolor=LAYOUT_BASE["paper_bgcolor"],
            font=dict(color="#e0e6f0", family="IBM Plex Mono"),
            title=dict(text=f"Superfície de Volatilidade — {asset2}", font=dict(color=CYAN, size=13)),
            margin=dict(l=0, r=0, t=40, b=0),
            height=550,
        )
        st.plotly_chart(fig_surf, use_container_width=True)
