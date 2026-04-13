"""Market regime and sector strength helper functions."""
from typing import Any, Dict, Optional
import yfinance as yf
import pandas as pd

SECTOR_ETF_MAP = {
    'Technology': 'XLK',
    'Financial Services': 'XLF',
    'Healthcare': 'XLV',
    'Consumer Cyclical': 'XLY',
    'Communication Services': 'XLC',
    'Industrials': 'XLI',
    'Consumer Defensive': 'XLP',
    'Energy': 'XLE',
    'Materials': 'XLB',
    'Real Estate': 'XLRE',
    'Utilities': 'XLU'
}


class MarketContext:
    @staticmethod
    def get_market_regime() -> Dict[str, Any]:
        regime = {
            'regime': 'neutral',
            'score': 0.0,
            'vix': None,
            'spy_trend': 'neutral',
            'qqq_trend': 'neutral',
            'is_risk_on': None
        }

        try:
            spy = yf.Ticker('SPY').history(period='1y')
            qqq = yf.Ticker('QQQ').history(period='1y')
            vix = yf.Ticker('^VIX').history(period='1mo')

            if not spy.empty and not qqq.empty:
                spy_trend = MarketContext._trend_score(spy['Close'])
                qqq_trend = MarketContext._trend_score(qqq['Close'])
                regime['spy_trend'] = 'bullish' if spy_trend > 0 else 'bearish' if spy_trend < 0 else 'neutral'
                regime['qqq_trend'] = 'bullish' if qqq_trend > 0 else 'bearish' if qqq_trend < 0 else 'neutral'
                regime['score'] = clamp((spy_trend + qqq_trend) / 2.0, -100.0, 100.0)
                regime['regime'] = 'risk-on' if regime['score'] > 10 else 'risk-off' if regime['score'] < -10 else 'neutral'
                regime['is_risk_on'] = regime['regime'] == 'risk-on'

            if not vix.empty:
                regime['vix'] = float(vix['Close'].iloc[-1])
        except Exception:
            pass

        return regime

    @staticmethod
    def get_sector_strength(ticker: str) -> Dict[str, Any]:
        result = {
            'sector': 'Unknown',
            'strength_score': 50.0,
            'sector_etf': None
        }
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get('sector', 'Unknown')
            result['sector'] = sector

            etf = SECTOR_ETF_MAP.get(sector)
            if etf:
                etf_data = yf.Ticker(etf).history(period='6mo')
                spy_data = yf.Ticker('SPY').history(period='6mo')
                if not etf_data.empty and not spy_data.empty:
                    etf_return = MarketContext._total_return(etf_data['Close'])
                    spy_return = MarketContext._total_return(spy_data['Close'])
                    result['sector_etf'] = etf
                    score = 50.0 + (etf_return - spy_return) * 100.0
                    result['strength_score'] = clamp(score, 0.0, 100.0)
        except Exception:
            pass

        return result

    @staticmethod
    def get_fundamental_snapshot(ticker: str) -> Dict[str, Any]:
        snapshot = {
            'ticker': ticker,
            'market_cap': None,
            'pe_ratio': None,
            'forward_pe': None,
            'revenue_growth': None,
            'sector': None,
            'industry': None,
            'earnings_date': None
        }
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            snapshot.update({
                'market_cap': info.get('marketCap'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'revenue_growth': info.get('revenueGrowth'),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'earnings_date': info.get('earningsDate')
            })
        except Exception:
            pass
        return snapshot

    @staticmethod
    def _trend_score(series: pd.Series) -> float:
        short = series.rolling(50).mean().iloc[-1] if len(series) >= 50 else series.iloc[-1]
        long = series.rolling(200).mean().iloc[-1] if len(series) >= 200 else series.iloc[-1]
        if short is None or long is None or long == 0:
            return 0.0
        return ((short - long) / long) * 100.0

    @staticmethod
    def _total_return(series: pd.Series) -> float:
        if series.empty:
            return 0.0
        return float(series.iloc[-1] / series.iloc[0] - 1.0)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
