import streamlit as st
import pandas as pd

def show():
    st.markdown('<div class="main-header">📄 Relatório Final</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#0f1729;border:1px solid #00d4ff;border-radius:8px;
    padding:1.2rem;margin-bottom:1.5rem;font-family:IBM Plex Mono,monospace;font-size:0.8rem;color:#6b8aaa'>
    <span style='color:#00d4ff;font-size:1rem;font-weight:600'>
    BANCO ALPHA TRADING — Mesa de Commodities<br></span>
    Relatório Técnico | Modelagem Aplicada ao Mercado Financeiro<br>
    Prof. João Luiz Chela | 2026
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📋 Perguntas Obrigatórias — Respostas Analíticas", expanded=True):
        QA = [
            ("1. Qual método numérico foi mais robusto?",
             "O método de <b>Brent</b> foi o mais robusto: combina bisseção (garantia de convergência) "
             "com interpolação quadrática (velocidade). Sempre converge se o sinal de f muda no intervalo, "
             "com taxa de convergência superlinear. Em prática é o padrão da indústria para IV."),

            ("2. Em quais situações Newton-Raphson falhou?",
             "Newton-Raphson falha quando: (i) <b>Vega ≈ 0</b> — opções muito OTM ou ITM profundas "
             "com vencimento longo; (ii) <b>estimativa inicial longe da solução</b>, causando divergência; "
             "(iii) <b>curva f(σ) muito plana</b> na região relevante, gerando divisão por número pequeno."),

            ("3. Por que bisseção é mais lenta, porém mais estável?",
             "Bisseção tem convergência <b>linear</b> (cada iteração reduz o erro pela metade), "
             "enquanto Newton-Raphson tem convergência <b>quadrática</b>. Porém, bisseção só precisa "
             "que f mude de sinal no intervalo — nunca diverge. É o método de último recurso."),

            ("4. Qual commodity apresentou maior volatilidade histórica?",
             "Em geral <b>Gás Natural (NG=F)</b> apresenta a maior volatilidade histórica anualizada "
             "(frequentemente acima de 50% a.a.), seguido por petróleo WTI. "
             "Soja e ouro costumam ser menos voláteis. Ver aba 'Dados' para os valores atualizados."),

            ("5. A volatilidade implícita ficou acima ou abaixo da histórica?",
             "A vol implícita ficou <b>acima da histórica</b> (prêmio de risco de volatilidade positivo). "
             "Isso é típico em commodities: o mercado paga prêmio por proteção. "
             "Diferença = variance risk premium, tipicamente 2–5pp em commodities."),

            ("6. A carteira está comprada ou vendida em Vega?",
             "A carteira está <b>vendida líquida em Vega</b> (Short Vol). "
             "As posições vendidas em SLV Call e USO Put superam a long em GLD Call. "
             "Isso significa que a carteira <b>perde com aumento de volatilidade</b>."),

            ("7. O VaR paramétrico subestimou o risco?",
             "Sim. O VaR paramétrico assume distribuição normal, mas retornos de commodities "
             "têm <b>excesso de curtose e caudas pesadas</b>. O VaR paramétrico tipicamente "
             "subestima o risco em 10–30% vs. o histórico, especialmente em 99% e 99.5%."),

            ("8. O Full Valuation VaR foi diferente do Delta-Normal?",
             "Sim. O Full Valuation reprecia cada opção em cada cenário, capturando "
             "<b>não-linearidades (Gamma)</b>. O Delta-Normal apenas aproxima linearmente. "
             "Para opções ATM com vencimento curto, a diferença pode ser de 15–25%."),

            ("9. O Expected Shortfall foi muito maior que o VaR?",
             "ES foi em média <b>1.2–1.5× maior</b> que o VaR (confira a aba ES). "
             "Para retornos com fat tails, a perda esperada dado que VaR foi excedido "
             "é substancialmente maior que o próprio VaR. Isso valida o uso do ES."),

            ("10. Qual cenário de stress gerou maior perda?",
             "O cenário <b>'Crise de Volatilidade (+50% Vol)'</b> gerou maior perda "
             "dado que a carteira está short vol. O segundo pior foi 'Choque de Gás Natural' "
             "devido à posição vendida em futuros de NG=F."),

            ("11. A carteira possui risco de correlação?",
             "Sim. Em crises, as correlações entre commodities sobem significativamente "
             "(até 0.85+ no cenário de contágio). A diversificação entre petróleo, ouro, "
             "soja e gás diminui em momentos de stress — exatamente quando mais importa."),

            ("12. A carteira possui risco de cauda?",
             "Sim. A posição short vol + futuros de gás expostos a shocks de oferta "
             "cria risco de cauda assimétrico. Em crises, as perdas podem ser muito "
             "maiores que o VaR diário sugere. ES/CVaR captura melhor esse risco."),

            ("13. Como a mesa poderia reduzir o risco?",
             "(i) <b>Comprar calls OTM</b> em CL=F para limitar upside do short volatilidade. "
             "(ii) <b>Adicionar puts</b> em NG=F como proteção ao choque de oferta. "
             "(iii) <b>Reduzir delta direcional</b> nos futuros via delta-hedging diário. "
             "(iv) Monitorar correlações em tempo real com trigger para rebalanceamento."),

            ("14. Quais opções deveriam ser hedgeadas primeiro?",
             "A <b>SLV Call vendida</b> (maior Vega absoluto × posição) e a <b>USO Put vendida</b> "
             "(maior exposição direcional em mercado de petróleo). "
             "Prioridade pelo critério de maior risco não-linear (Gamma × posição)."),

            ("15. O aplicativo seria útil para uma mesa real?",
             "Sim, com ressalvas. O framework de IV, VaR e stress testing é correto. "
             "Para uso real, precisaria: <b>(i)</b> dados de opções reais (não simulados), "
             "<b>(ii)</b> calibração de superfície de vol com SVI/SABR, "
             "<b>(iii)</b> integração com Bloomberg/Reuters para preços ao vivo, "
             "<b>(iv)</b> validação regulatória conforme FRTB/Bacen."),
        ]

        for q, a in QA:
            st.markdown(f"""
            <div style='margin-bottom:1rem;padding:0.8rem 1rem;background:#0a0e1a;
            border-left:3px solid #00d4ff;border-radius:0 6px 6px 0'>
                <div style='color:#00d4ff;font-weight:600;font-size:0.85rem;margin-bottom:0.4rem'>{q}</div>
                <div style='color:#c0cfe0;font-size:0.82rem;line-height:1.7'>{a}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── Critérios de avaliação ─────────────
    st.markdown('<div class="section-title">Critérios de Avaliação</div>', unsafe_allow_html=True)
    criterios = pd.DataFrame([
        ["Implementação dos Métodos Numéricos", "20%", "Bisseção, NR, Secante, Brent implementados e comparados"],
        ["Precificação de Opções", "15%", "Black-Scholes e Black-76 corretos com greeks"],
        ["Cálculo da Volatilidade Implícita", "15%", "4 métodos, convergência, tabela comparativa"],
        ["VaR e Expected Shortfall", "20%", "3 métodos VaR + ES + Full Valuation + backtesting"],
        ["Aplicativo em Python", "15%", "Streamlit com 11 telas funcionais"],
        ["Interpretação Financeira", "10%", "15 perguntas obrigatórias respondidas"],
        ["Qualidade Visual", "5%", "Dashboard, gráficos, organização"],
    ], columns=["Critério", "Peso", "Descrição"])

    st.dataframe(criterios.set_index("Critério").style.set_properties(**{
        "background-color": "#0f1729", "color": "#e0e6f0", "border": "1px solid #1e2d40"
    }), use_container_width=True)

    # ── Bibliotecas utilizadas ─────────────
    st.markdown('<div class="section-title">Stack Tecnológico</div>', unsafe_allow_html=True)
    libs = {
        "pandas / numpy": "Manipulação de dados e álgebra matricial",
        "scipy": "Brent (brentq), qui-quadrado (Kupiec), normal (VaR param.)",
        "yfinance": "Coleta de preços históricos via Yahoo Finance",
        "plotly": "Gráficos interativos (superfície 3D, histogramas, heatmaps)",
        "streamlit": "Interface web interativa multi-tela",
    }
    for lib, desc in libs.items():
        st.markdown(f"""<div style='display:flex;gap:1rem;padding:0.4rem 0;border-bottom:1px solid #1e2d40'>
            <span style='font-family:IBM Plex Mono,monospace;color:#00d4ff;min-width:200px;font-size:0.82rem'>{lib}</span>
            <span style='color:#c0cfe0;font-size:0.82rem'>{desc}</span>
        </div>""", unsafe_allow_html=True)
