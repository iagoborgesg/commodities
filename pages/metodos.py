import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from models import compare_iv_methods, bs_price, b76_price
from charts import CYAN, GREEN, RED, YELLOW, ORANGE, PURPLE, LAYOUT_BASE

def show():
    st.markdown('<div class="main-header">⚖️ Comparação dos Métodos Numéricos</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#0f1729;border:1px solid #1e2d40;border-radius:8px;padding:1rem;margin-bottom:1rem;font-size:0.85rem;color:#6b8aaa;font-family:IBM Plex Mono,monospace'>
    Os 4 métodos buscam a raiz de <b style='color:#00d4ff'>f(σ) = P_modelo(σ) − P_mercado = 0</b><br>
    Bisseção: garantida, lenta · Newton-Raphson: rápido, pode divergir · Secante: compromisso · Brent: robusto e eficiente
    </div>
    """, unsafe_allow_html=True)

    # ── Configuração ─────────────────────
    st.markdown('<div class="section-title">Parâmetros da Opção</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        P_mkt = st.number_input("Preço de Mercado", value=8.5, min_value=0.01, step=0.5, key="mn_p")
        S     = st.number_input("Spot (S)", value=100.0, min_value=0.01, step=1.0, key="mn_s")
    with c2:
        K     = st.number_input("Strike (K)", value=100.0, min_value=0.01, step=1.0, key="mn_k")
        r     = st.number_input("Taxa r (%)", value=5.3, step=0.1, key="mn_r") / 100
    with c3:
        T     = st.number_input("Vencimento (dias)", value=90, min_value=1, key="mn_t") / 365
        model = st.selectbox("Modelo", ["Black-Scholes", "Black-76"], key="mn_model")
    with c4:
        opt_type = st.selectbox("Tipo", ["call", "put"], key="mn_type")
        run = st.button("▸ Executar Comparação", type="primary", key="mn_run")

    model_key = "bs" if "Scholes" in model else "b76"

    if run or True:  # executa por padrão
        results = compare_iv_methods(P_mkt, S, K, r, T, opt_type, model_key)

        # ── Tabela principal ─────────────
        st.markdown('<div class="section-title">Tabela Comparativa</div>', unsafe_allow_html=True)
        rows = []
        for name, res in results.items():
            iv_val = res["iv"]
            rows.append({
                "Método":         name,
                "Vol Implícita":  f"{iv_val*100:.6f}%" if iv_val else "N/C",
                "Iterações":      res["iterations"],
                "Erro Final":     f"{res['error']:.2e}" if res["error"] is not None else "—",
                "Tempo (ms)":     f"{res['time']*1000:.4f}",
                "Convergiu":      "✅" if res["converged"] else "❌",
            })

        df = pd.DataFrame(rows).set_index("Método")
        st.dataframe(df.style.set_properties(**{
            "background-color": "#0f1729", "color": "#e0e6f0", "border": "1px solid #1e2d40"
        }), use_container_width=True)

        # ── Gráficos comparativos ─────────
        valid = {k: v for k, v in results.items() if v["iv"] is not None}
        if valid:
            c1, c2 = st.columns(2)

            with c1:
                names = list(valid.keys())
                iters = [valid[n]["iterations"] for n in names]
                colors = [CYAN, GREEN, YELLOW, ORANGE]
                fig_iter = go.Figure(go.Bar(
                    x=names, y=iters,
                    marker_color=colors[:len(names)],
                    text=iters, textposition="outside"
                ))
                fig_iter.update_layout(
                    title=dict(text="Número de Iterações", font=dict(color=CYAN, size=13)),
                    yaxis_title="Iterações", **LAYOUT_BASE
                )
                st.plotly_chart(fig_iter, use_container_width=True)

            with c2:
                times_ms = [valid[n]["time"] * 1000 for n in names]
                fig_time = go.Figure(go.Bar(
                    x=names, y=times_ms,
                    marker_color=colors[:len(names)],
                    text=[f"{t:.4f}" for t in times_ms], textposition="outside"
                ))
                fig_time.update_layout(
                    title=dict(text="Tempo Computacional (ms)", font=dict(color=CYAN, size=13)),
                    yaxis_title="ms", **LAYOUT_BASE
                )
                st.plotly_chart(fig_time, use_container_width=True)

            # ── Convergência visual ───────
            st.markdown('<div class="section-title">Trajetória de Convergência — Bisseção vs Newton-Raphson</div>',
                        unsafe_allow_html=True)

            fig_conv = go.Figure()
            for method, color in [("Bisseção", CYAN), ("Newton-Raphson", GREEN)]:
                # Simula trajetória do método
                traj = _get_trajectory(method, P_mkt, S, K, r, T, opt_type, model_key)
                if traj:
                    fig_conv.add_trace(go.Scatter(
                        x=list(range(1, len(traj)+1)), y=traj,
                        name=method, line=dict(color=color, width=2),
                        mode="lines+markers", marker=dict(size=4)
                    ))

            if valid.get("Brent", {}).get("iv"):
                fig_conv.add_hline(y=valid["Brent"]["iv"] * 100,
                                   line_color=YELLOW, line_dash="dash",
                                   annotation_text="IV Brent (referência)")
            fig_conv.update_layout(
                xaxis_title="Iteração", yaxis_title="σ estimado (%)",
                title=dict(text="Convergência do σ por Iteração", font=dict(color=CYAN)),
                **LAYOUT_BASE
            )
            st.plotly_chart(fig_conv, use_container_width=True)

        # ── Análise textual ───────────────
        st.markdown('<div class="section-title">Análise dos Métodos</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#0f1729;border:1px solid #1e2d40;border-radius:8px;padding:1.2rem;font-size:0.85rem;color:#e0e6f0;line-height:1.8'>
        <b style='color:#00d4ff'>Bisseção</b> — Garantidamente converge se f(a)·f(b) < 0. Divide o intervalo pela metade a cada iteração.
        Lenta (convergência linear), mas extremamente robusta. Não falha.<br><br>
        <b style='color:#00e676'>Newton-Raphson</b> — Usa a derivada (Vega) para saltar diretamente à raiz. Convergência quadrática quando
        próximo da solução. Falha quando Vega ≈ 0 (opções muito OTM/ITM profundas) ou com estimativa inicial ruim.<br><br>
        <b style='color:#ffd60a'>Secante</b> — Aproxima a derivada por diferenças finitas. Não precisa calcular Vega analiticamente.
        Convergência superlinear (~1.618). Pode divergir se os dois pontos iniciais forem mal escolhidos.<br><br>
        <b style='color:#ff9100'>Brent</b> — Combina bisseção, secante e interpolação quadrática inversa. Garante convergência como
        a bisseção, mas com velocidade próxima aos métodos de alta ordem. Considerado o mais robusto na prática.
        </div>
        """, unsafe_allow_html=True)


def _get_trajectory(method, P_mkt, S, K, r, T, opt_type, model):
    """Simula trajetória iterativa para visualização."""
    from models import _objective
    from scipy.stats import norm

    if model == "bs":
        price_fn = lambda sig: __import__('models').bs_price(S, K, r, T, sig, opt_type)
    else:
        price_fn = lambda sig: __import__('models').b76_price(S, K, r, T, sig, opt_type)

    traj = []
    try:
        if method == "Bisseção":
            lo, hi = 0.0001, 5.0
            for _ in range(30):
                mid = (lo + hi) / 2
                traj.append(mid * 100)
                f = price_fn(mid) - P_mkt
                if abs(f) < 1e-6:
                    break
                f_lo = price_fn(lo) - P_mkt
                if f_lo * f < 0:
                    hi = mid
                else:
                    lo = mid

        elif method == "Newton-Raphson":
            sig = 0.3
            for _ in range(30):
                traj.append(sig * 100)
                f = price_fn(sig) - P_mkt
                if abs(f) < 1e-6:
                    break
                if model == "bs":
                    from models import bs_d1
                    d1 = bs_d1(S, K, r, T, sig)
                    vega = S * np.sqrt(T) * norm.pdf(d1)
                else:
                    from models import b76_d1
                    d1 = b76_d1(S, K, r, T, sig)
                    vega = np.exp(-r * T) * S * np.sqrt(T) * norm.pdf(d1)
                if abs(vega) < 1e-10:
                    break
                sig = max(0.0001, sig - f / vega)
    except Exception:
        pass

    return traj
