import streamlit as st

st.set_page_config(
    page_title="Alpha Trading — Mesa de Commodities",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'IBM Plex Sans', sans-serif;
}
.stApp {
    background-color: #0a0e1a;
    color: #e0e6f0;
}
.main-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.8rem;
    font-weight: 600;
    color: #00d4ff;
    letter-spacing: -0.02em;
    border-bottom: 1px solid #1e2d40;
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
}
.metric-card {
    background: #0f1729;
    border: 1px solid #1e2d40;
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.5rem;
}
.metric-label {
    font-size: 0.7rem;
    color: #6b8aaa;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-family: 'IBM Plex Mono', monospace;
}
.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    font-family: 'IBM Plex Mono', monospace;
    color: #00d4ff;
}
.metric-value.negative { color: #ff4d6d; }
.metric-value.positive { color: #00e676; }
.section-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.85rem;
    color: #6b8aaa;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 1rem;
    border-left: 3px solid #00d4ff;
    padding-left: 0.75rem;
}
div[data-testid="stSidebarNav"] { display: none; }
.stTabs [data-baseweb="tab-list"] {
    background-color: #0f1729;
    border-bottom: 1px solid #1e2d40;
}
.stTabs [data-baseweb="tab"] {
    color: #6b8aaa;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.8rem;
}
.stTabs [aria-selected="true"] {
    color: #00d4ff !important;
    border-bottom-color: #00d4ff !important;
}
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.markdown("""
<div style='font-family: IBM Plex Mono, monospace; color: #00d4ff; font-size:1.1rem; font-weight:600; padding: 1rem 0 0.5rem;'>
    ▸ ALPHA TRADING
</div>
<div style='font-family: IBM Plex Mono, monospace; color: #6b8aaa; font-size:0.7rem; margin-bottom:1.5rem;'>
    Mesa de Commodities v1.0
</div>
""", unsafe_allow_html=True)

pages = {
    "📊 Dashboard": "dashboard",
    "📥 Dados": "dados",
    "💰 Precificação": "precificacao",
    "🔍 Vol. Implícita": "vol_implicita",
    "⚖️ Métodos Numéricos": "metodos",
    "😄 Smile de Volatilidade": "smile",
    "🔢 Greeks": "greeks",
    "📉 VaR": "var",
    "⚡ Expected Shortfall": "es",
    "🔁 Backtesting": "backtest",
    "💥 Stress Testing": "stress",
    "📄 Relatório Final": "relatorio",
}

selected = st.sidebar.radio("", list(pages.keys()), label_visibility="collapsed")

# Route to pages
page_key = pages[selected]

if page_key == "dashboard":
    from pages import dashboard; dashboard.show()
elif page_key == "dados":
    from pages import dados; dados.show()
elif page_key == "precificacao":
    from pages import precificacao; precificacao.show()
elif page_key == "vol_implicita":
    from pages import vol_implicita; vol_implicita.show()
elif page_key == "metodos":
    from pages import metodos; metodos.show()
elif page_key == "smile":
    from pages import smile; smile.show()
elif page_key == "greeks":
    from pages import greeks; greeks.show()
elif page_key == "var":
    from pages import var; var.show()
elif page_key == "es":
    from pages import es; es.show()
elif page_key == "backtest":
    from pages import backtest; backtest.show()
elif page_key == "stress":
    from pages import stress; stress.show()
elif page_key == "relatorio":
    from pages import relatorio; relatorio.show()
