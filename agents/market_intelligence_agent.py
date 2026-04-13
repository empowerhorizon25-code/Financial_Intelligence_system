"""Market Intelligence Agent for the Financial Intelligence System."""
from typing import Any, Dict, List
import yfinance as yf
from agents.base_agent import BaseAgent
from utils.news_adapter import NewsAdapter
from utils.market_context import MarketContext
from utils.scoring import (
    score_technical,
    score_news,
    score_market_regime,
    score_fundamentals,
    score_risk,
    compute_final_score,
    clamp
)


class MarketIntelligenceAgent(BaseAgent):
    def __init__(self):
        super().__init__('Market Intelligence Agent', 'market_intelligence')

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        ticker = input_data.get('ticker')
        historical_data = input_data.get('historical_data')
        fundamentals = input_data.get('fundamental_metrics') or {}
        technicals = input_data.get('technical_indicators') or {}
        risk_metrics = input_data.get('risk_metrics') or {}

        if not ticker:
            raise ValueError('Ticker symbol is required for Market Intelligence Agent')

        if historical_data is None:
            historical_data = self._load_historical_data(ticker)

        fundamental_snapshot = fundamentals
        if not fundamentals:
            fundamental_snapshot = MarketContext.get_fundamental_snapshot(ticker)

        market_regime = MarketContext.get_market_regime()
        sector_strength = MarketContext.get_sector_strength(ticker)

        company_news = NewsAdapter.get_company_news(ticker)
        macro_news = NewsAdapter.get_macro_news()

        company_sentiment = NewsAdapter.analyze_sentiment(company_news)
        macro_sentiment = NewsAdapter.analyze_sentiment(macro_news)

        technical_score = score_technical(technicals, historical_data)
        news_score = score_news(company_sentiment, macro_sentiment, sector_strength.get('strength_score', 50.0))
        market_regime_score = score_market_regime(market_regime)
        fundamentals_score = score_fundamentals(fundamental_snapshot)
        risk_score = score_risk(risk_metrics)

        final_score = compute_final_score(
            technical_score,
            news_score,
            market_regime_score,
            fundamentals_score,
            risk_score
        )

        confidence_score = self._adjust_confidence(
            final_score,
            news_score,
            market_regime,
            sector_strength,
            risk_score
        )

        recommendation = self._recommendation(final_score, risk_score, market_regime)
        warning_flags = self._build_warning_flags(market_regime, sector_strength, news_score, risk_score)
        key_drivers = self._build_key_drivers(
            technical_score,
            news_score,
            market_regime_score,
            fundamentals_score,
            risk_score,
            sector_strength
        )

        short_explanation = self._build_short_explanation(recommendation, technical_score, market_regime, news_score)
        long_explanation = self._build_long_explanation(
            recommendation,
            technical_score,
            news_score,
            market_regime,
            fundamentals_score,
            risk_score,
            sector_strength
        )

        return {
            'ticker': ticker,
            'recommendation': recommendation,
            'confidence_score': confidence_score,
            'technical_score': round(technical_score, 1),
            'news_score': round(news_score, 1),
            'market_regime_score': round(market_regime_score, 1),
            'fundamentals_score': round(fundamentals_score, 1),
            'risk_score': round(risk_score, 1),
            'final_score': round(final_score, 1),
            'short_explanation': short_explanation,
            'long_explanation': long_explanation,
            'key_drivers': key_drivers,
            'warning_flags': warning_flags,
            'news_sentiment': {
                'company_sentiment': round(company_sentiment, 1),
                'macro_sentiment': round(macro_sentiment, 1)
            },
            'market_context': market_regime,
            'sector_context': sector_strength,
            'company_news': company_news[:3],
            'macro_news': macro_news[:2]
        }

    def _load_historical_data(self, ticker: str):
        try:
            return yf.Ticker(ticker).history(period='2y', auto_adjust=True)
        except Exception:
            return None

    def _adjust_confidence(
        self,
        final_score: float,
        news_score: float,
        market_regime: Dict[str, Any],
        sector_strength: Dict[str, Any],
        risk_score: float
    ) -> float:
        confidence = final_score

        vix = market_regime.get('vix')
        if vix and vix > 25:
            confidence -= 12.0

        if sector_strength.get('strength_score', 50.0) < 40.0:
            confidence -= 8.0

        if news_score < -60.0 and confidence > 60.0:
            confidence = 60.0

        if risk_score > 70.0:
            confidence -= 10.0

        if market_regime.get('regime') == 'risk-on' and final_score > 55:
            confidence += 5.0

        return int(clamp(confidence, 0.0, 100.0))

    def _recommendation(self, final_score: float, risk_score: float, market_regime: Dict[str, Any]) -> str:
        if final_score >= 65.0 and risk_score < 75.0:
            if market_regime.get('regime') == 'risk-off' and final_score < 75.0:
                return 'HOLD'
            return 'BUY'
        if final_score <= 35.0:
            return 'SELL'
        return 'HOLD'

    def _build_warning_flags(
        self,
        market_regime: Dict[str, Any],
        sector_strength: Dict[str, Any],
        news_score: float,
        risk_score: float
    ) -> List[str]:
        flags = []
        vix = market_regime.get('vix')
        if vix and vix >= 25.0:
            flags.append('VIX elevated')
        if sector_strength.get('strength_score', 50.0) < 40.0:
            flags.append('Weak sector momentum')
        if news_score <= -50.0:
            flags.append('Strongly negative news flow')
        if risk_score >= 65.0:
            flags.append('High quantified risk')
        if market_regime.get('regime') == 'risk-off':
            flags.append('Market regime risk-off')
        return flags

    def _build_key_drivers(
        self,
        technical_score: float,
        news_score: float,
        market_regime_score: float,
        fundamentals_score: float,
        risk_score: float,
        sector_strength: Dict[str, Any]
    ) -> List[str]:
        drivers = []
        if technical_score >= 65.0:
            drivers.append('Technicals support directional momentum')
        else:
            drivers.append('Technicals are mixed')

        if news_score >= 30.0:
            drivers.append('Positive news flow')
        elif news_score <= -30.0:
            drivers.append('Negative news flow')
        else:
            drivers.append('Neutral headline sentiment')

        if market_regime_score >= 20.0:
            drivers.append('Risk-on market regime')
        elif market_regime_score <= -20.0:
            drivers.append('Risk-off market regime')
        else:
            drivers.append('Neutral market regime')

        sector = sector_strength.get('sector')
        score = sector_strength.get('strength_score', 50.0)
        if sector and score >= 60.0:
            drivers.append(f'{sector} sector strength supportive')
        elif sector:
            drivers.append(f'{sector} sector under pressure')

        if fundamentals_score >= 60.0:
            drivers.append('Fundamentals are constructive')
        else:
            drivers.append('Fundamentals are cautious')

        return drivers[:5]

    def _build_short_explanation(
        self,
        recommendation: str,
        technical_score: float,
        market_regime: Dict[str, Any],
        news_score: float
    ) -> str:
        regime = market_regime.get('regime', 'neutral')
        return (
            f"{recommendation} based on disciplined technical momentum, {regime} market regime, "
            f"and {'positive' if news_score >= 0 else 'negative'} news sentiment."
        )

    def _build_long_explanation(
        self,
        recommendation: str,
        technical_score: float,
        news_score: float,
        market_regime: Dict[str, Any],
        fundamentals_score: float,
        risk_score: float,
        sector_strength: Dict[str, Any]
    ) -> str:
        sections = [
            f"The Market Intelligence Agent combines technical indicators, market regime, news flow, fundamentals, and quantified risk.",
            f"Technicals scored {technical_score:.1f}/100, news sentiment scored {news_score:.1f}/100, and fundamentals scored {fundamentals_score:.1f}/100.",
            f"Sector strength is {sector_strength.get('strength_score', 50.0):.1f}/100 for {sector_strength.get('sector', 'Unknown')}.",
            f"The model-adjusted risk score is {risk_score:.1f}/100, and the market regime is {market_regime.get('regime', 'neutral')}.",
            f"After deterministic weighting and regime adjustments, the final signal is {recommendation}."
        ]
        return ' '.join(sections)
