"""News data adapter interface and placeholder sentiment analysis."""
from typing import List, Dict, Any
import yfinance as yf
import re

POSITIVE_KEYWORDS = [
    'upgrade', 'beats', 'profit', 'growth', 'beat', 'record', 'strong', 'outperform', 'raise', 'surge'
]
NEGATIVE_KEYWORDS = [
    'downgrade', 'miss', 'loss', 'weak', 'cut', 'fall', 'decline', 'sell', 'downturn', 'warn'
]


class NewsAdapter:
    @staticmethod
    def get_company_news(ticker: str) -> List[Dict[str, Any]]:
        try:
            yf_ticker = yf.Ticker(ticker)
            raw_news = getattr(yf_ticker, 'news', []) or []

            if raw_news:
                return [
                    {
                        'headline': item.get('title', ''),
                        'source': item.get('publisher', item.get('provider', 'Unknown')),
                        'url': item.get('link', ''),
                        'publish_date': item.get('providerPublishTime'),
                        'sentiment': NewsAdapter._score_headline(item.get('title', ''))
                    }
                    for item in raw_news[:10]
                ]
        except Exception:
            pass

        return NewsAdapter._mock_company_news(ticker)

    @staticmethod
    def get_macro_news() -> List[Dict[str, Any]]:
        return [
            {
                'headline': 'Federal Reserve signals rate stability but notes inflation risks.',
                'source': 'MacroDesk',
                'sentiment': NewsAdapter._score_headline('Federal Reserve signals rate stability but notes inflation risks.')
            },
            {
                'headline': 'Earnings season remains mixed, technology showing continued outperformance.',
                'source': 'MarketBrief',
                'sentiment': NewsAdapter._score_headline('Earnings season remains mixed, technology showing continued outperformance.')
            }
        ]

    @staticmethod
    def get_analyst_updates(ticker: str) -> List[Dict[str, Any]]:
        return [
            {
                'headline': f'{ticker} receives analyst upgrade from neutral to buy.',
                'source': 'AnalystWire',
                'sentiment': 40
            }
        ]

    @staticmethod
    def analyze_sentiment(headlines: List[Dict[str, Any]]) -> float:
        if not headlines:
            return 0.0

        scores = [item.get('sentiment', 0.0) for item in headlines]
        return sum(scores) / len(scores)

    @staticmethod
    def _score_headline(text: str) -> float:
        if not text:
            return 0.0

        text_lower = text.lower()
        score = 0.0
        for positive in POSITIVE_KEYWORDS:
            if re.search(rf'\b{re.escape(positive)}\b', text_lower):
                score += 10.0
        for negative in NEGATIVE_KEYWORDS:
            if re.search(rf'\b{re.escape(negative)}\b', text_lower):
                score -= 10.0

        if score > 50.0:
            score = 50.0
        if score < -50.0:
            score = -50.0
        return score

    @staticmethod
    def _mock_company_news(ticker: str) -> List[Dict[str, Any]]:
        return [
            {
                'headline': f'{ticker} remains in focus after mixed quarterly results.',
                'source': 'MockNews',
                'sentiment': -10.0
            },
            {
                'headline': f'Analysts expect {ticker} to maintain growth in the coming quarter.',
                'source': 'MockNews',
                'sentiment': 15.0
            }
        ]
