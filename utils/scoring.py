"""Deterministic scoring utilities for Market Intelligence Agent."""
from typing import Any, Dict, Optional
import math

# Weights for final score calculation
TECHNICAL_WEIGHT = 0.35
SENTIMENT_WEIGHT = 0.20
MARKET_WEIGHT = 0.20
FUNDAMENTALS_WEIGHT = 0.15
RISK_PENALTY_WEIGHT = 0.10


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))


def normalize_linear(value: float, min_value: float, max_value: float) -> float:
    if math.isnan(value) or max_value == min_value:
        return 0.0
    return clamp((value - min_value) / (max_value - min_value), 0.0, 1.0)


def score_technical(technicals: Dict[str, Any], historical_data) -> float:
    if not technicals:
        return 50.0

    rsi = float(technicals.get('rsi_14', 50.0) or 50.0)
    macd = float(technicals.get('macd_line', 0.0) or 0.0)
    signal = float(technicals.get('signal_line', 0.0) or 0.0)
    trend_bonus = 15.0 if macd > signal else -15.0

    rsi_score = 50.0
    if rsi < 30:
        rsi_score = 70.0
    elif rsi < 50:
        rsi_score = 90.0
    elif rsi <= 70:
        rsi_score = 80.0
    else:
        rsi_score = 55.0

    moving_average_score = 50.0
    if historical_data is not None and len(historical_data) >= 50:
        close = historical_data['Close']
        ma50 = close.rolling(50).mean().iloc[-1]
        ma200 = close.rolling(200).mean().iloc[-1] if len(close) >= 200 else ma50
        current_price = float(technicals.get('current_price', close.iloc[-1]))
        if current_price >= ma50:
            moving_average_score += 10.0
        if current_price >= ma200:
            moving_average_score += 10.0

    score = rsi_score * 0.55 + moving_average_score * 0.35 + trend_bonus * 0.10
    return clamp(score, 0.0, 100.0)


def score_news(company_sentiment: float, macro_sentiment: float, sector_strength: float) -> float:
    if company_sentiment is None:
        company_sentiment = 0.0
    if macro_sentiment is None:
        macro_sentiment = 0.0
    if sector_strength is None:
        sector_strength = 50.0

    company_component = clamp((company_sentiment + 100.0) / 2.0, 0.0, 100.0)
    macro_component = clamp((macro_sentiment + 100.0) / 2.0, 0.0, 100.0)
    sector_component = clamp(sector_strength, 0.0, 100.0)

    score = company_component * 0.55 + macro_component * 0.25 + sector_component * 0.20
    return clamp(score, 0.0, 100.0)


def score_market_regime(regime_data: Dict[str, Any]) -> float:
    if not regime_data or regime_data.get('score') is None:
        return 0.0
    return clamp(float(regime_data.get('score', 0.0)), -100.0, 100.0)


def score_fundamentals(fundamentals: Dict[str, Any]) -> float:
    if not fundamentals:
        return 50.0

    pe = fundamentals.get('pe_ratio')
    forward_pe = fundamentals.get('forward_pe')
    market_cap = fundamentals.get('market_cap')
    revenue_growth = fundamentals.get('revenue_growth')

    score = 50.0

    # Valuation score
    try:
        pe = float(pe)
        if 8 <= pe <= 25:
            score += 15.0
        elif 25 < pe <= 35:
            score += 5.0
        elif pe < 8:
            score += 10.0
        else:
            score -= 10.0
    except Exception:
        score += 0.0

    try:
        forward_pe = float(forward_pe)
        if 8 <= forward_pe <= 22:
            score += 10.0
        elif 22 < forward_pe <= 35:
            score += 2.0
        elif forward_pe > 35:
            score -= 8.0
    except Exception:
        score += 0.0

    try:
        if isinstance(market_cap, (int, float)) and market_cap > 0:
            size_score = clamp((math.log10(market_cap) - 8.0) * 10.0, 0.0, 20.0)
            score += size_score
    except Exception:
        score += 0.0

    try:
        revenue_growth = float(revenue_growth)
        if revenue_growth >= 0.15:
            score += 10.0
        elif revenue_growth >= 0.05:
            score += 5.0
        elif revenue_growth < 0:
            score -= 5.0
    except Exception:
        score += 0.0

    return clamp(score, 0.0, 100.0)


def score_risk(risk_metrics: Dict[str, Any]) -> float:
    if not risk_metrics:
        return 50.0

    volatility = float(risk_metrics.get('volatility', 0.0) or 0.0)
    current_drawdown = float(risk_metrics.get('current_drawdown', 0.0) or 0.0)
    sharpe = float(risk_metrics.get('sharpe_ratio', 0.0) or 0.0)

    volatility_component = clamp(volatility / 0.50 * 100.0, 0.0, 100.0)
    drawdown_component = clamp(abs(current_drawdown) / 0.50 * 100.0, 0.0, 100.0)
    sharpe_penalty = clamp((1.5 - sharpe) / 1.5 * 100.0, 0.0, 100.0)

    score = 0.55 * volatility_component + 0.35 * drawdown_component + 0.10 * sharpe_penalty
    return clamp(score, 0.0, 100.0)


def compute_final_score(
    technical_score: float,
    news_score: float,
    market_regime_score: float,
    fundamentals_score: float,
    risk_score: float
) -> float:
    normalized_news = clamp((news_score + 100.0) / 2.0, 0.0, 100.0)
    normalized_market = clamp((market_regime_score + 100.0) / 2.0, 0.0, 100.0)

    raw = (
        technical_score * TECHNICAL_WEIGHT
        + normalized_news * SENTIMENT_WEIGHT
        + normalized_market * MARKET_WEIGHT
        + fundamentals_score * FUNDAMENTALS_WEIGHT
        - risk_score * RISK_PENALTY_WEIGHT
    )

    return clamp(raw, 0.0, 100.0)
