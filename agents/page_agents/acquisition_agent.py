"""
Acquisition Agent
Converts cold traffic into app users through optimized landing page content
"""
from agents.page_agents import PageAgent
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AcquisitionAgent(PageAgent):
    """Agent that optimizes landing page content for user acquisition"""

    def __init__(self):
        super().__init__("Acquisition Agent", "landing")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate optimized landing page content

        Input:
        - traffic_source: Where visitor came from (social, search, etc.)
        - user_context: Any existing user data or behavior
        - trust_metrics: Performance data for credibility
        - trending_tickers: Current market opportunities

        Output:
        - hero_headline: Compelling main headline
        - hero_subheadline: Supporting subheadline
        - value_props: Key benefits/features
        - social_proof: Trust indicators
        - cta_text: Primary call-to-action
        - ticker_suggestions: Suggested stocks to analyze
        """
        traffic_source = input_data.get('traffic_source', 'direct')
        user_context = input_data.get('user_context', {})
        trust_metrics = input_data.get('trust_metrics', {})
        trending_tickers = input_data.get('trending_tickers', ['AAPL', 'NVDA', 'MSFT'])

        # Generate hero content
        hero_headline = self._generate_hero_headline(traffic_source, trust_metrics)
        hero_subheadline = self._generate_hero_subheadline(trust_metrics)

        # Generate value propositions
        value_props = self._generate_value_propositions(trust_metrics)

        # Generate social proof
        social_proof = self._generate_social_proof(trust_metrics)

        # Generate CTA text
        cta_text = self._generate_cta_text(traffic_source)

        # Generate ticker suggestions
        ticker_suggestions = self._generate_ticker_suggestions(trending_tickers)

        return {
            'hero_headline': hero_headline,
            'hero_subheadline': hero_subheadline,
            'value_props': value_props,
            'social_proof': social_proof,
            'cta_text': cta_text,
            'ticker_suggestions': ticker_suggestions,
            'ui_payload': {
                'hero_variants': [hero_headline],  # Could A/B test multiple
                'conversion_goal': 'first_analysis',
                'urgency_elements': self._get_urgency_elements(traffic_source)
            }
        }

    def _generate_hero_headline(self, traffic_source: str,
                              trust_metrics: Dict[str, Any]) -> str:
        """Generate compelling hero headline based on traffic source"""
        win_rate = trust_metrics.get('win_rate', 0) * 100

        # Tailor headline to traffic source
        if traffic_source == 'social':
            return "AI Stock Signals That Traders Actually Share"
        elif traffic_source == 'search':
            return "AI-Powered Stock Analysis with Real Results"
        elif traffic_source == 'reddit':
            return "Stop Guessing Stocks - Get AI Signals with 87% Accuracy"
        else:
            # Default/direct traffic
            if win_rate >= 60:
                return f"AI Stock Signals with {win_rate:.1f}% Win Rate"
            else:
                return "AI Stock Signals with Complete Transparency"

    def _generate_hero_subheadline(self, trust_metrics: Dict[str, Any]) -> str:
        """Generate supporting subheadline"""
        total_signals = trust_metrics.get('total_signals', 0)

        if total_signals >= 20:
            return "3 free signals + daily AI recommendations with proven performance"
        else:
            return "Try 3 free AI stock signals and see the difference data makes"

    def _generate_value_propositions(self, trust_metrics: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate key value propositions"""
        win_rate = trust_metrics.get('win_rate', 0) * 100
        total_signals = trust_metrics.get('total_signals', 0)

        value_props = [
            {
                'title': 'Clear BUY/SELL Signals',
                'description': 'No more guesswork - get definitive signals with entry, target, and stop levels'
            },
            {
                'title': 'AI Confidence Score',
                'description': 'Every signal includes an AI confidence percentage so you know the conviction level'
            },
            {
                'title': 'Risk Assessment',
                'description': 'Each signal includes risk level and position sizing guidance'
            }
        ]

        # Add performance-based value prop if we have data
        if win_rate > 0 and total_signals >= 5:
            value_props.append({
                'title': 'Proven Performance',
                'description': f'Proven {win_rate:.1f}% win rate across {total_signals} signals'
            })

        value_props.append({
            'title': 'Complete Transparency',
            'description': 'See exactly how our signals perform with full outcome tracking'
        })

        return value_props

    def _generate_social_proof(self, trust_metrics: Dict[str, Any]) -> str:
        """Generate social proof elements"""
        total_signals = trust_metrics.get('total_signals', 0)
        win_rate = trust_metrics.get('win_rate', 0) * 100

        proof_elements = []

        if total_signals >= 10:
            proof_elements.append(f"Trusted by traders analyzing {total_signals}+ real market signals")

        if win_rate >= 50:
            proof_elements.append(f"{win_rate:.1f}% win rate")

        proof_elements.append("Used by individual traders and small funds worldwide")

        return " • ".join(proof_elements)

    def _generate_cta_text(self, traffic_source: str) -> str:
        """Generate call-to-action text"""
        if traffic_source in ['social', 'reddit']:
            return "Try 3 Free Signals"
        elif traffic_source == 'search':
            return "Get Free AI Signals"
        else:
            return "Start Free Trial"

    def _generate_ticker_suggestions(self, trending_tickers: List[str]) -> List[Dict[str, str]]:
        """Generate suggested tickers for homepage"""
        suggestions = []

        # Map tickers to readable names
        ticker_names = {
            'AAPL': 'Apple Inc.',
            'NVDA': 'Nvidia Corp.',
            'MSFT': 'Microsoft Corp.',
            'TSLA': 'Tesla Inc.',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.'
        }

        for ticker in trending_tickers[:6]:  # Limit to 6 suggestions
            name = ticker_names.get(ticker, ticker)
            suggestions.append({
                'ticker': ticker,
                'name': name,
                'reason': f"Popular AI analysis target"
            })

        return suggestions

    def _get_urgency_elements(self, traffic_source: str) -> List[str]:
        """Get urgency elements for the page"""
        if traffic_source in ['social', 'reddit']:
            return ["Limited time offer", "Join the community"]
        elif traffic_source == 'search':
            return ["Free analysis available", "No credit card required"]
        else:
            return ["Start your free trial", "3 signals included"]