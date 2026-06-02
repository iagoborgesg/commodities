"""
models.py — Núcleo de modelos financeiros
Black-Scholes, Black-76, Greeks, métodos numéricos para volatilidade implícita
"""

import numpy as np
from scipy.stats import norm
from scipy.optimize import brentq
import time


# ─────────────────────────────────────────────
# BLACK-SCHOLES (opções sobre ETFs / spot)
# ─────────────────────────────────────────────

def bs_d1(S, K, r, T, sigma):
    return (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))

def bs_d2(S, K, r, T, sigma):
    return bs_d1(S, K, r, T, sigma) - sigma * np.sqrt(T)

def bs_call(S, K, r, T, sigma):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0)
    d1 = bs_d1(S, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)

def bs_put(S, K, r, T, sigma):
    if T <= 0 or sigma <= 0:
        return max(K - S, 0)
    d1 = bs_d1(S, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def bs_price(S, K, r, T, sigma, option_type="call"):
    if option_type.lower() == "call":
        return bs_call(S, K, r, T, sigma)
    return bs_put(S, K, r, T, sigma)


# ─────────────────────────────────────────────
# BLACK-76 (opções sobre futuros)
# ─────────────────────────────────────────────

def b76_d1(F, K, r, T, sigma):
    return (np.log(F / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))

def b76_call(F, K, r, T, sigma):
    if T <= 0 or sigma <= 0:
        return np.exp(-r * T) * max(F - K, 0)
    d1 = b76_d1(F, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    return np.exp(-r * T) * (F * norm.cdf(d1) - K * norm.cdf(d2))

def b76_put(F, K, r, T, sigma):
    if T <= 0 or sigma <= 0:
        return np.exp(-r * T) * max(K - F, 0)
    d1 = b76_d1(F, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    return np.exp(-r * T) * (K * norm.cdf(-d2) - F * norm.cdf(-d1))

def b76_price(F, K, r, T, sigma, option_type="call"):
    if option_type.lower() == "call":
        return b76_call(F, K, r, T, sigma)
    return b76_put(F, K, r, T, sigma)


# ─────────────────────────────────────────────
# GREEKS — Black-Scholes
# ─────────────────────────────────────────────

def greeks_bs(S, K, r, T, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "gamma": 0, "vega": 0, "theta": 0, "rho": 0}
    d1 = bs_d1(S, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    nd1 = norm.pdf(d1)
    
    gamma = nd1 / (S * sigma * np.sqrt(T))
    vega  = S * np.sqrt(T) * nd1 / 100  # por 1% de vol

    if option_type.lower() == "call":
        delta = norm.cdf(d1)
        theta = (-(S * nd1 * sigma) / (2 * np.sqrt(T))
                 - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365
        rho   = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        delta = norm.cdf(d1) - 1
        theta = (-(S * nd1 * sigma) / (2 * np.sqrt(T))
                 + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365
        rho   = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}


def greeks_b76(F, K, r, T, sigma, option_type="call"):
    if T <= 0 or sigma <= 0:
        return {"delta": 0, "gamma": 0, "vega": 0, "theta": 0, "rho": 0}
    d1 = b76_d1(F, K, r, T, sigma)
    d2 = d1 - sigma * np.sqrt(T)
    nd1 = norm.pdf(d1)
    disc = np.exp(-r * T)

    gamma = disc * nd1 / (F * sigma * np.sqrt(T))
    vega  = disc * F * np.sqrt(T) * nd1 / 100

    if option_type.lower() == "call":
        delta = disc * norm.cdf(d1)
        theta = (disc * (-(F * nd1 * sigma) / (2 * np.sqrt(T))
                 + r * (F * norm.cdf(d1) - K * norm.cdf(d2)))) / 365
        rho   = -T * b76_call(F, K, r, T, sigma) / 100
    else:
        delta = -disc * norm.cdf(-d1)
        theta = (disc * (-(F * nd1 * sigma) / (2 * np.sqrt(T))
                 - r * (K * norm.cdf(-d2) - F * norm.cdf(-d1)))) / 365
        rho   = -T * b76_put(F, K, r, T, sigma) / 100

    return {"delta": delta, "gamma": gamma, "vega": vega, "theta": theta, "rho": rho}


# ─────────────────────────────────────────────
# VOLATILIDADE IMPLÍCITA — 4 métodos
# ─────────────────────────────────────────────

def _objective(sigma, price_market, S, K, r, T, option_type, model):
    if model == "bs":
        price_model = bs_price(S, K, r, T, sigma, option_type)
    else:
        price_model = b76_price(S, K, r, T, sigma, option_type)
    return price_model - price_market


def iv_bissecao(price_market, S, K, r, T, option_type="call", model="bs",
                sigma_low=0.0001, sigma_high=5.0, tol=1e-6, max_iter=500):
    start = time.perf_counter()
    f_low  = _objective(sigma_low,  price_market, S, K, r, T, option_type, model)
    f_high = _objective(sigma_high, price_market, S, K, r, T, option_type, model)

    if f_low * f_high > 0:
        return {"iv": None, "iterations": 0, "error": None,
                "time": time.perf_counter() - start, "converged": False}

    sigma_mid = sigma_low
    for i in range(1, max_iter + 1):
        sigma_mid = (sigma_low + sigma_high) / 2
        f_mid = _objective(sigma_mid, price_market, S, K, r, T, option_type, model)
        if abs(f_mid) < tol:
            break
        if f_low * f_mid < 0:
            sigma_high = sigma_mid
        else:
            sigma_low  = sigma_mid
            f_low = f_mid

    elapsed = time.perf_counter() - start
    return {"iv": sigma_mid, "iterations": i, "error": abs(f_mid),
            "time": elapsed, "converged": abs(f_mid) < tol}


def iv_newton_raphson(price_market, S, K, r, T, option_type="call", model="bs",
                      sigma0=0.3, tol=1e-6, max_iter=500):
    start = time.perf_counter()
    sigma = sigma0

    for i in range(1, max_iter + 1):
        f = _objective(sigma, price_market, S, K, r, T, option_type, model)
        if abs(f) < tol:
            break
        # Vega como derivada
        if model == "bs":
            d1 = bs_d1(S, K, r, T, sigma)
            vega = S * np.sqrt(T) * norm.pdf(d1)
        else:
            d1 = b76_d1(S, K, r, T, sigma)
            vega = np.exp(-r * T) * S * np.sqrt(T) * norm.pdf(d1)

        if abs(vega) < 1e-10:
            break
        sigma = sigma - f / vega
        if sigma <= 0:
            sigma = 0.001

    elapsed = time.perf_counter() - start
    f_final = _objective(sigma, price_market, S, K, r, T, option_type, model)
    return {"iv": sigma, "iterations": i, "error": abs(f_final),
            "time": elapsed, "converged": abs(f_final) < tol}


def iv_secante(price_market, S, K, r, T, option_type="call", model="bs",
               sigma0=0.2, sigma1=0.4, tol=1e-6, max_iter=500):
    start = time.perf_counter()
    s0, s1 = sigma0, sigma1
    f0 = _objective(s0, price_market, S, K, r, T, option_type, model)

    for i in range(1, max_iter + 1):
        f1 = _objective(s1, price_market, S, K, r, T, option_type, model)
        if abs(f1) < tol:
            break
        denom = f1 - f0
        if abs(denom) < 1e-12:
            break
        s2 = s1 - f1 * (s1 - s0) / denom
        s2 = max(0.0001, s2)
        s0, f0 = s1, f1
        s1 = s2

    elapsed = time.perf_counter() - start
    f_final = _objective(s1, price_market, S, K, r, T, option_type, model)
    return {"iv": s1, "iterations": i, "error": abs(f_final),
            "time": elapsed, "converged": abs(f_final) < tol}


def iv_brent(price_market, S, K, r, T, option_type="call", model="bs",
             sigma_low=0.0001, sigma_high=5.0, tol=1e-6):
    start = time.perf_counter()
    try:
        f = lambda sig: _objective(sig, price_market, S, K, r, T, option_type, model)
        # Conta iterações via wrapper
        count = [0]
        def f_counted(sig):
            count[0] += 1
            return f(sig)

        iv = brentq(f_counted, sigma_low, sigma_high, xtol=tol, maxiter=500)
        f_final = f(iv)
        converged = abs(f_final) < tol
    except Exception:
        iv, count[0], f_final, converged = None, 0, None, False

    elapsed = time.perf_counter() - start
    return {"iv": iv, "iterations": count[0], "error": abs(f_final) if f_final is not None else None,
            "time": elapsed, "converged": converged}


def compare_iv_methods(price_market, S, K, r, T, option_type="call", model="bs"):
    """Roda os 4 métodos e retorna tabela comparativa."""
    results = {}
    results["Bisseção"]         = iv_bissecao(price_market, S, K, r, T, option_type, model)
    results["Newton-Raphson"]   = iv_newton_raphson(price_market, S, K, r, T, option_type, model)
    results["Secante"]          = iv_secante(price_market, S, K, r, T, option_type, model)
    results["Brent"]            = iv_brent(price_market, S, K, r, T, option_type, model)
    return results


# ─────────────────────────────────────────────
# VaR
# ─────────────────────────────────────────────

def var_historico(returns, portfolio_value, confidence_levels=(0.95, 0.99, 0.995)):
    results = {}
    for cl in confidence_levels:
        percentile = np.percentile(returns, (1 - cl) * 100)
        results[cl] = -percentile * portfolio_value
    return results


def var_parametrico(returns, portfolio_value, confidence_levels=(0.95, 0.99, 0.995)):
    mu    = np.mean(returns)
    sigma = np.std(returns)
    results = {}
    for cl in confidence_levels:
        z = norm.ppf(cl)
        results[cl] = (z * sigma - mu) * portfolio_value
    return results


def var_montecarlo(S0, mu, sigma, T, portfolio_value, n_sim=10000,
                   confidence_levels=(0.95, 0.99, 0.995), seed=42):
    np.random.seed(seed)
    Z  = np.random.standard_normal(n_sim)
    ST = S0 * np.exp((mu - 0.5 * sigma**2) * T + sigma * np.sqrt(T) * Z)
    pnl = (ST - S0) / S0 * portfolio_value
    results = {}
    for cl in confidence_levels:
        results[cl] = -np.percentile(pnl, (1 - cl) * 100)
    return results, pnl


def expected_shortfall(returns, portfolio_value, confidence_levels=(0.95, 0.99, 0.995)):
    results = {}
    for cl in confidence_levels:
        threshold = np.percentile(returns, (1 - cl) * 100)
        tail = returns[returns <= threshold]
        results[cl] = -np.mean(tail) * portfolio_value if len(tail) > 0 else 0
    return results


# ─────────────────────────────────────────────
# BACKTESTING — teste de Kupiec
# ─────────────────────────────────────────────

def kupiec_test(violations, T, confidence_level):
    """
    LR_uc = -2 * ln[ (1-p)^(T-N) * p^N / (1-N/T)^(T-N) * (N/T)^N ]
    H0: frequência de violações = p esperado
    """
    from scipy.stats import chi2
    p = 1 - confidence_level
    N = violations
    if N == 0 or N == T:
        return {"LR": np.inf, "p_value": 0, "reject_h0": True}
    
    freq = N / T
    LR = -2 * (
        (T - N) * np.log(1 - p) + N * np.log(p)
        - (T - N) * np.log(1 - freq) - N * np.log(freq)
    )
    p_value = 1 - chi2.cdf(LR, df=1)
    return {"LR": LR, "p_value": p_value, "reject_h0": p_value < 0.05}
