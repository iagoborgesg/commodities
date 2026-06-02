# Alpha Trading — Mesa de Commodities

Aplicativo Streamlit para avaliação de commodities, precificação de opções, volatilidade implícita e gestão de risco.

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
streamlit run app.py
```

## Estrutura

```
commodities_app/
├── app.py              # Entry point + sidebar + roteamento
├── models.py           # Black-Scholes, Black-76, Greeks, IV (4 métodos), VaR, ES, Kupiec
├── data.py             # yfinance, retornos, vol histórica, carteira
├── charts.py           # Tema visual Plotly (cores, layout)
├── requirements.txt
└── pages/
    ├── dashboard.py    # KPIs de mercado + posições
    ├── dados.py        # Preços, retornos, correlação, covariância
    ├── precificacao.py # BS e Black-76 com gráficos
    ├── vol_implicita.py# IV com 4 métodos + visualização f(σ)
    ├── metodos.py      # Comparação iterações/tempo/erro/convergência
    ├── smile.py        # Smile + superfície de volatilidade 3D
    ├── greeks.py       # Delta, Gamma, Vega, Theta, Rho por posição
    ├── var.py          # VaR histórico, paramétrico e Monte Carlo
    ├── es.py           # Expected Shortfall + comparação VaR
    ├── backtest.py     # Rolling VaR + violações + Teste de Kupiec
    ├── stress.py       # 7 cenários + heatmap de perdas
    └── relatorio.py    # 15 perguntas obrigatórias + critérios
```

## Modelos Implementados

- **Black-Scholes**: Opções europeias sobre ETFs (GLD, USO, SLV)
- **Black-76**: Opções sobre futuros (CL=F, GC=F, ZS=F, NG=F)
- **Greeks**: Delta, Gamma, Vega, Theta, Rho (analíticos)
- **IV**: Bisseção, Newton-Raphson, Secante, Brent
- **VaR**: Histórico, Paramétrico, Monte Carlo (10k cenários)
- **ES/CVaR**: Histórico e paramétrico
- **Backtesting**: Janela móvel 250 dias + Teste de Kupiec
- **Stress**: 7 cenários (recessão, fuga, choque de gás, safra, BRL, vol, correlação)
