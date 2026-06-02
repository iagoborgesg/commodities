import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import var_historico, var_parametrico, expected_shortfall
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, LAYOUT_BASE
from data import download_prices, get_returns, RISK_FREE_RATE

CONFIDENCE_LEVELS = (0.95, 0.99, 0.995)
CL_LABELS = {0.95: "95%", 0.99: "99%", 0.995: "99.5%"}

def show():
    st.markdown('<div class="main-header">⚡ Expected Shortfall (CVaR)</div>', unsafe_allow_html=True)
    st.latex(r"ES_\alpha = \mathbb{E}[L \mid L > VaR_\alpha]")

    c1, c2 = st.columns(2)
    with c1:
        asset = st.selectbox("Ativo", ["GLD", "USO", "SLV", "CL=F", "GC=F"])
        pv    = st.number_input("Valor da Carteira (USD)", value=10_000_000, step=500_000, format="%d")

    with st.spinner("Calculando..."):
        prices_df = download_prices([asset])
        returns   = get_returns(prices_df)

    if prices_df.empty or asset not in returns.columns:
        st.error("Dados indisponíveis.")
        return

    ret = returns[asset].dropna().values
    var_hist = var_historico(ret, pv)
    es_hist  = expected_shortfall(ret, pv)
    var_par  = var_parametrico(ret, pv)

    # ES paramétrico
    from scipy.stats import norm
    mu_r, sig_r = np.mean(ret), np.std(ret)
    es_par = {}
    for cl in CONFIDENCE_LEVELS:
        z = norm.ppf(cl)
        es_par[cl] = (norm.pdf(z) / (1 - cl) * sig_r - mu_r) * pv

    # ── KPIs ─────────────────────────────
    st.markdown('<div class="section-title">VaR × Expected Shortfall</div>', unsafe_allow_html=True)
    for cl in CONFIDENCE_LEVELS:
        col1, col2, col3 = st.columns(3)
        col1.markdown(f"""<div class="metric-card">
            <div class="metric-label">VaR Histórico {CL_LABELS[cl]}</div>
            <div class="metric-value negative" style="font-size:1rem">${var_hist[cl]:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        col2.markdown(f"""<div class="metric-card">
            <div class="metric-label">ES Histórico {CL_LABELS[cl]}</div>
            <div class="metric-value negative" style="font-size:1rem">${es_hist[cl]:,.0f}</div>
        </div>""", unsafe_allow_html=True)
        ratio = es_hist[cl] / var_hist[cl] if var_hist[cl] > 0 else 0
        col3.markdown(f"""<div class="metric-card">
            <div class="metric-label">ES / VaR {CL_LABELS[cl]}</div>
            <div class="metric-value" style="font-size:1rem;color:#ffd60a">{ratio:.3f}×</div>
        </div>""", unsafe_allow_html=True)

    # ── Visualização distribuição de cauda ─
    st.markdown('<div class="section-title">Distribuição com Cauda ES</div>', unsafe_allow_html=True)
    losses = -ret * pv
    cl_sel = st.select_slider("Nível de confiança", [0.95, 0.99, 0.995],
                              format_func=lambda x: CL_LABELS[x])
    var_val = var_hist[cl_sel]
    es_val  = es_hist[cl_sel]

    fig = go.Figure()
    # Histograma completo
    fig.add_trace(go.Histogram(
        x=losses, nbinsx=80, name="Perdas",
        marker_color="rgba(0,212,255,0.4)",
        hovertemplate="Perda: %{x:,.0f}<br>Count: %{y}<extra></extra>"
    ))
    # Cauda
    tail_mask = losses >= var_val
    fig.add_trace(go.Histogram(
        x=losses[tail_mask], nbinsx=40, name=f"Cauda > VaR {CL_LABELS[cl_sel]}",
        marker_color="rgba(255,77,109,0.7)",
        hovertemplate="Perda: %{x:,.0f}<br>Count: %{y}<extra></extra>"
    ))
    fig.add_vline(x=var_val, line_color=YELLOW, line_dash="dash",
                  annotation_text=f"VaR ${var_val/1e6:.2f}M",
                  annotation_font_color=YELLOW)
    fig.add_vline(x=es_val, line_color=RED, line_dash="dash",
                  annotation_text=f"ES ${es_val/1e6:.2f}M",
                  annotation_font_color=RED)
    fig.update_layout(
        barmode="overlay",
        xaxis_title="Perda (USD)", yaxis_title="Frequência",
        title=dict(text=f"Distribuição de Perdas — {asset}", font=dict(color=CYAN, size=13)),
        **LAYOUT_BASE
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabela comparativa ────────────────
    st.markdown('<div class="section-title">Comparação Completa</div>', unsafe_allow_html=True)
    rows = []
    for cl in CONFIDENCE_LEVELS:
        rows.append({
            "Nível":         CL_LABELS[cl],
            "VaR Hist.":     f"${var_hist[cl]:,.0f}",
            "ES Hist.":      f"${es_hist[cl]:,.0f}",
            "VaR Param.":    f"${var_par[cl]:,.0f}",
            "ES Param.":     f"${es_par[cl]:,.0f}",
            "ES/VaR":        f"{es_hist[cl]/var_hist[cl]:.3f}×",
            "Excesso ES":    f"${es_hist[cl]-var_hist[cl]:,.0f}",
        })
    df = pd.DataFrame(rows).set_index("Nível")
    st.dataframe(df.style.set_properties(**{
        "background-color": "#0f1729", "color": "#e0e6f0"
    }), use_container_width=True)

    # ── Análise textual ───────────────────
    st.markdown('<div class="section-title">Por que o ES é mais adequado?</div>', unsafe_allow_html=True)
    avg_ratio = np.mean([es_hist[cl] / var_hist[cl] for cl in CONFIDENCE_LEVELS])
    st.markdown(f"""
    <div style='background:#0f1729;border:1px solid #1e2d40;border-radius:8px;padding:1.2rem;font-size:0.85rem;color:#e0e6f0;line-height:1.9'>
    <b style='color:#00d4ff'>VaR</b> responde apenas: <i>"Quanto posso perder com probabilidade α?"</i>
    Não diz nada sobre a <b>magnitude</b> das perdas além desse limiar.<br><br>

    <b style='color:#00d4ff'>Expected Shortfall (ES/CVaR)</b> responde: <i>"Dado que a perda superou o VaR, qual é a perda esperada?"</i>
    É uma medida de risco <b>coerente</b> (satisfaz subaditividade), enquanto o VaR não é.<br><br>

    Para esta carteira, o ES é em média <b style='color:#ffd60a'>{avg_ratio:.2f}× maior que o VaR</b>,
    sugerindo caudas pesadas significativas. Usar apenas o VaR subestimaria substancialmente
    o risco em cenários de cauda.<br><br>

    <b style='color:#00d4ff'>Basilea III / FRTB</b> substituiu o VaR 99% pelo ES 97.5% exatamente
    por essa razão: capturar melhor os riscos extremos das carteiras de trading.
    </div>
    """, unsafe_allow_html=True)
