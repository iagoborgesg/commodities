"""
data.py — Captura e tratamento de dados via yfinance
"""

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime, timedelta

# ─────────────────────────────────────────────
# CARTEIRA DA MESA
# ─────────────────────────────────────────────

PORTFOLIO = [
    # futuros
    {"asset": "CL=F", "type": "future",  "direction": "long",  "maturity_months": 3,  "qty": 120,    "option_type": None},
    {"asset": "GC=F", "type": "future",  "direction": "short", "maturity_months": 6,  "qty": 80,     "option_type": None},
    {"asset": "ZS=F", "type": "future",  "direction": "long",  "maturity_months": 4,  "qty": 150,    "option_type": None},
    {"asset": "NG=F", "type": "future",  "direction": "short", "maturity_months": 2,  "qty": 100,    "option_type": None},
    # opções
    {"asset": "GLD",  "type": "option",  "direction": "long",  "maturity_days":  90,  "qty": 25000,  "option_type": "call"},
    {"asset": "USO",  "type": "option",  "direction": "short", "maturity_days": 120,  "qty": 40000,  "option_type": "put"},
    {"asset": "SLV",  "type": "option",  "direction": "short", "maturity_days": 180,  "qty": 30000,  "option_type": "call"},
]

TICKERS_ALL = ["CL=F", "GC=F", "ZS=F", "NG=F", "GLD", "USO", "SLV",
               "SI=F", "ZC=F", "ZW=F", "DBC"]

TICKER_LABELS = {
    "CL=F": "Petróleo WTI",
    "GC=F": "Ouro",
    "ZS=F": "Soja",
    "NG=F": "Gás Natural",
    "GLD":  "Ouro ETF (GLD)",
    "USO":  "Petróleo ETF (USO)",
    "SLV":  "Prata ETF (SLV)",
    "SI=F": "Prata",
    "ZC=F": "Milho",
    "ZW=F": "Trigo",
    "DBC":  "Índice Commodities",
}

RISK_FREE_RATE = 0.053   # taxa livre de risco (~Tesouro EUA)


# ─────────────────────────────────────────────
# DOWNLOAD
# ─────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def download_prices(tickers=None, period="2y"):
    if tickers is None:
        tickers = TICKERS_ALL
    try:
        raw = yf.download(tickers, period=period, auto_adjust=True, progress=False)
        if isinstance(raw.columns, pd.MultiIndex):
            prices = raw["Close"]
        else:
            prices = raw[["Close"]] if "Close" in raw.columns else raw
        prices = prices.ffill().dropna(how="all")
        return prices
    except Exception as e:
        st.error(f"Erro ao baixar dados: {e}")
        return pd.DataFrame()


def get_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices / prices.shift(1)).dropna()


def get_annualized_vol(returns: pd.DataFrame) -> pd.Series:
    return returns.std() * np.sqrt(252)


def get_corr_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.corr()


def get_cov_matrix(returns: pd.DataFrame) -> pd.DataFrame:
    return returns.cov() * 252


def get_latest_prices(prices: pd.DataFrame) -> pd.Series:
    return prices.iloc[-1]


def get_portfolio_summary(prices: pd.DataFrame) -> pd.DataFrame:
    latest = get_latest_prices(prices)
    returns = get_returns(prices)
    vol = get_annualized_vol(returns)

    rows = []
    for pos in PORTFOLIO:
        ticker = pos["asset"]
        price  = latest.get(ticker, np.nan)
        v      = vol.get(ticker, np.nan)
        rows.append({
            "Ativo":       ticker,
            "Nome":        TICKER_LABELS.get(ticker, ticker),
            "Tipo":        pos["type"].capitalize(),
            "Direção":     pos["direction"].capitalize(),
            "Qtd":         pos["qty"],
            "Preço Atual": round(price, 2) if not np.isnan(price) else "N/A",
            "Vol Hist (a.a.)": f"{v*100:.1f}%" if not np.isnan(v) else "N/A",
        })
    return pd.DataFrame(rows)
