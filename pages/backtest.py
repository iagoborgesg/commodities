import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import chi2, norm
from models import kupiec_test
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, LAYOUT_BASE
from data import download_prices, get_returns

CONFIDENCE_LEVELS = (0.95, 0.99)
CL_LABELS = {0.95: "95%", 0.99: "99%"}

def show():
    st.markdown('<div class="main-header">🔁 Backtesting do VaR</div>', unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        asset  = st.selectbox("Ativo", ["GLD", "USO", "SLV", "CL=F", "GC=F"])
        window = st.slider("Janela de estimação (dias)", 60, 500, 250)
    with c2:
        pv = st.number_input("Valor da Carteira (USD)", value=10_000_000, step=500_000, format="%d")
        cl_sel = st.select_slider("Nível de Confiança", [0.95, 0.99],
                                  format_func=lambda x: CL_LABELS[x])

    with st.spinner("Calculando backtesting..."):
        prices_df = download_prices([asset], period="3y")
        returns   = get_returns(prices_df)

    if prices_df.empty or asset not in returns.columns:
        st.error("Dados indisponíveis.")
        return

    ret = returns[asset].dropna()

    # ── Rolling VaR ──────────────────────
    var_series = {}
    p_actual   = {}

    idx = ret.index
    for i in range(window, len(ret)):
        window_ret = ret.iloc[i - window: i].values
        var_val = -np.percentile(window_ret, (1 - cl_sel) * 100) * pv
        var_series[idx[i]] = var_val
        p_actual[idx[i]]   = ret.iloc[i] * pv  # P&L

    var_s  = pd.Series(var_series, name="VaR")
    pnl_s  = pd.Series(p_actual,   name="P&L")

    violations = ((-pnl_s) > var_s).astype(int)
    n_violations = violations.sum()
    T = len(violations)
    expected_viol = int(T * (1 - cl_sel))
    viol_rate = n_violations / T

    # ── KPIs ─────────────────────────────
    st.markdown('<div class="section-title">Resumo do Backtesting</div>', unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(f"""<div class="metric-card">
        <div class="metric-label">Total de Dias</div>
        <div class="metric-value" style="font-size:1.1rem">{T:,}</div>
    </div>""", unsafe_allow_html=True)
    m2.markdown(f"""<div class="metric-card">
        <div class="metric-label">Violações Observadas</div>
        <div class="metric-value {'negative' if n_violations > expected_viol * 1.5 else 'positive'}" style="font-size:1.1rem">
            {n_violations}
        </div>
    </div>""", unsafe_allow_html=True)
    m3.markdown(f"""<div class="metric-card">
        <div class="metric-label">Violações Esperadas</div>
        <div class="metric-value" style="font-size:1.1rem">{expected_viol}</div>
    </div>""", unsafe_allow_html=True)
    m4.markdown(f"""<div class="metric-card">
        <div class="metric-label">Taxa de Violação</div>
        <div class="metric-value" style="font-size:1.1rem;color:#ffd60a">{viol_rate*100:.2f}%</div>
    </div>""", unsafe_allow_html=True)

    # ── Gráfico VaR × P&L ────────────────
    st.markdown('<div class="section-title">P&L vs VaR — Janela Móvel</div>', unsafe_allow_html=True)

    viol_dates = violations[violations == 1].index

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pnl_s.index, y=pnl_s.values / 1e6,
        name="P&L Diário", line=dict(color=CYAN, width=1),
        hovertemplate="%{x}<br>P&L: $%{y:.3f}M<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=var_s.index, y=-var_s.values / 1e6,
        name=f"−VaR {CL_LABELS[cl_sel]}", line=dict(color=YELLOW, width=1.5, dash="dash"),
        hovertemplate="%{x}<br>VaR: $%{y:.3f}M<extra></extra>"
    ))
    # Violações
    if len(viol_dates) > 0:
        fig.add_trace(go.Scatter(
            x=viol_dates,
            y=pnl_s.loc[viol_dates].values / 1e6,
            mode="markers", name="Violação",
            marker=dict(color=RED, size=8, symbol="x"),
            hovertemplate="%{x}<br>Violação: $%{y:.3f}M<extra></extra>"
        ))
    fig.update_layout(
        yaxis_title="P&L (USD M)",
        title=dict(text=f"Backtesting VaR {CL_LABELS[cl_sel]} — {asset}", font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Teste de Kupiec ───────────────────
    st.markdown('<div class="section-title">Teste de Kupiec (LR_uc)</div>', unsafe_allow_html=True)
    st.latex(r"LR_{uc} = -2 \ln\left[\frac{(1-p)^{T-N} p^N}{(1-N/T)^{T-N}(N/T)^N}\right]")

    kupiec = kupiec_test(n_violations, T, cl_sel)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""<div class="metric-card">
        <div class="metric-label">LR_uc</div>
        <div class="metric-value" style="font-size:1.2rem">{kupiec['LR']:.4f}</div>
    </div>""", unsafe_allow_html=True)
    c2.markdown(f"""<div class="metric-card">
        <div class="metric-label">p-valor</div>
        <div class="metric-value" style="font-size:1.2rem">{kupiec['p_value']:.4f}</div>
    </div>""", unsafe_allow_html=True)
    reject = kupiec["reject_h0"]
    c3.markdown(f"""<div class="metric-card">
        <div class="metric-label">Rejeita H₀ (α=5%)?</div>
        <div class="metric-value" style="font-size:1rem;color:{'#ff4d6d' if reject else '#00e676'}">
            {'❌ Sim — VaR inadequado' if reject else '✅ Não — VaR adequado'}
        </div>
    </div>""", unsafe_allow_html=True)

    # Chi-quadrado
    st.markdown("""
    <div style='background:#0f1729;border:1px solid #1e2d40;border-radius:8px;padding:1rem;font-size:0.85rem;color:#6b8aaa;margin-top:0.5rem'>
    <b style='color:#e0e6f0'>H₀:</b> A frequência de violações é consistente com o nível de confiança declarado.<br>
    Estatística LR_uc ~ χ²(1). Valor crítico 5% = 3.841.<br>
    Se LR_uc > 3.841 → rejeitar H₀ → o modelo de VaR é inadequado.
    </div>
    """, unsafe_allow_html=True)

    # ── Violações ao longo do tempo ───────
    st.markdown('<div class="section-title">Violações Acumuladas</div>', unsafe_allow_html=True)
    cum_viol = violations.cumsum()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=cum_viol.index, y=cum_viol.values,
        fill="tozeroy", fillcolor="rgba(255,77,109,0.2)",
        line=dict(color=RED, width=2), name="Violações Acumuladas"
    ))
    # Linha esperada
    expected_line = np.linspace(0, expected_viol, len(cum_viol))
    fig2.add_trace(go.Scatter(
        x=cum_viol.index, y=expected_line,
        line=dict(color=YELLOW, width=1.5, dash="dash"), name="Esperado"
    ))
    fig2.update_layout(
        yaxis_title="Violações Acumuladas",
        title=dict(text="Violações Acumuladas vs Esperado", font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig2, use_container_width=True)
