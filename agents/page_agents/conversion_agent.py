"""
Conversion Agent
Converts free users into paid subscribers through personalized messaging
"""
from agents.page_agents import PageAgent
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConversionAgent(PageAgent):
    """Agent that personalizes upgrade messaging and drives conversions"""

    def __init__(self):
        super().__init__("Conversion Agent", "paywall")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate personalized conversion messaging

        Input:
        - user_usage: Free signals used, remaining, total usage
        - last_analysis: Most recent signal analysis
        - trust_metrics: Performance data for credibility
        - pricing_state: Current plan details

        Output:
        - upgrade_headline: Compelling headline
        - value_proposition: What user gets by upgrading
        - urgency_message: Why upgrade now
        - social_proof: Trust indicators
        - cta_text: Call-to-action copy
        """
        user_usage = input_data.get('user_usage', {})
        last_analysis = input_data.get('last_analysis', {})
        trust_metrics = input_data.get('trust_metrics', {})
        pricing_state = input_data.get('pricing_state', {'price': 14, 'period': 'month'})

        # Generate upgrade headline
        upgrade_headline = self._generate_upgrade_headline(user_usage, last_analysis)

        # Generate value proposition
        value_proposition = self._generate_value_proposition(
            user_usage, trust_metrics, pricing_state
        )

        # Generate urgency message
        urgency_message = self._generate_urgency_message(user_usage)

        # Generate social proof
        social_proof = self._generate_social_proof(trust_metrics)

        # Generate CTA text
        cta_text = self._generate_cta_text(user_usage, pricing_state)

        return {
            'upgrade_headline': upgrade_headline,
            'value_proposition': value_proposition,
            'urgency_message': urgency_message,
            'social_proof': social_proof,
            'cta_text': cta_text,
            'ui_payload': {
                'modal_title': upgrade_headline,
                'pricing_display': f"${pricing_state.get('price', 14)}/{pricing_state.get('period', 'month')}",
                'remaining_free': max(0, 3 - user_usage.get('used_today', 0)),
                'conversion_probability': self._estimate_conversion_probability(user_usage, trust_metrics)
            }
        }

    def _generate_upgrade_headline(self, user_usage: Dict[str, Any],
                                 last_analysis: Dict[str, Any]) -> str:
        """Generate compelling upgrade headline"""
        used_today = user_usage.get('used_today', 0)
        remaining = max(0, 3 - used_today)

        if remaining == 0:
            return "You've Used Your 3 Free Signals Today"
        elif remaining == 1:
            return "1 Free Signal Remaining - Ready for Unlimited Access?"
        elif remaining == 2:
            return "2 Free Signals Left - See Why Users Upgrade"
        else:
            # Fresh user
            last_ticker = last_analysis.get('ticker', '')
            if last_ticker:
                return f"Great Analysis on {last_ticker} - Unlock Daily Signals"
            return "Experience the Full Power of AI Stock Signals"

    def _generate_value_proposition(self, user_usage: Dict[str, Any],
                                  trust_metrics: Dict[str, Any],
                                  pricing_state: Dict[str, Any]) -> str:
        """Generate personalized value proposition"""
        price = pricing_state.get('price', 14)
        period = pricing_state.get('period', 'month')

        win_rate = trust_metrics.get('win_rate', 0) * 100
        total_signals = trust_metrics.get('total_signals', 0)

        value_parts = []

        # Core value
        value_parts.append(f"Get daily AI signals with clear entry, target, and stop levels for only ${price}/{period}.")

        # Performance proof
        if win_rate > 0 and total_signals >= 5:
            value_parts.append(".1f")

        # Risk management
        value_parts.append("Every signal includes risk assessment and position sizing guidance.")

        # Additional benefits
        value_parts.append("Access to transparency dashboard showing real performance metrics.")

        return " ".join(value_parts)

    def _generate_urgency_message(self, user_usage: Dict[str, Any]) -> str:
        """Generate urgency without being spammy"""
        used_today = user_usage.get('used_today', 0)
        remaining = max(0, 3 - used_today)

        if remaining == 0:
            return "Your free signals reset tomorrow. Upgrade now to continue analyzing stocks today."
        elif remaining == 1:
            return "Make the most of your last free signal, then unlock unlimited access."
        elif remaining == 2:
            return "You're running low on free signals. See why thousands upgrade for unlimited access."
        else:
            return "Join traders who get daily AI signals with proven performance."

    def _generate_social_proof(self, trust_metrics: Dict[str, Any]) -> str:
        """Generate trust-building social proof"""
        win_rate = trust_metrics.get('win_rate', 0) * 100
        total_signals = trust_metrics.get('total_signals', 0)
        sharpe_ratio = trust_metrics.get('sharpe_ratio', 0)

        proof_parts = []

        if total_signals >= 10:
            proof_parts.append(f"Based on {total_signals} real signals with transparent outcomes.")

        if win_rate >= 50:
            proof_parts.append(".1f")

        if sharpe_ratio >= 0.5:
            proof_parts.append("Risk-adjusted returns that outperform basic strategies.")

        proof_parts.append("Used by traders who value data-driven decisions over guesswork.")

        return " ".join(proof_parts) if proof_parts else "Backed by proven AI analysis and transparent performance tracking."

    def _generate_cta_text(self, user_usage: Dict[str, Any],
                         pricing_state: Dict[str, Any]) -> str:
        """Generate compelling call-to-action text"""
        price = pricing_state.get('price', 14)
        period = pricing_state.get('period', 'month')
        remaining = max(0, 3 - user_usage.get('used_today', 0))

        if remaining == 0:
            return f"Upgrade Now - ${price}/{period}"
        elif remaining == 1:
            return f"Get Unlimited Access - ${price}/{period}"
        else:
            return f"Start Unlimited Plan - ${price}/{period}"

    def _estimate_conversion_probability(self, user_usage: Dict[str, Any],
                                       trust_metrics: Dict[str, Any]) -> float:
        """Estimate conversion likelihood for personalization"""
        # Simple scoring based on engagement
        score = 0.0

        # Usage indicates interest
        used_today = user_usage.get('used_today', 0)
        if used_today >= 2:
            score += 0.3
        elif used_today >= 1:
            score += 0.2

        # Trust metrics indicate credibility
        win_rate = trust_metrics.get('win_rate', 0) * 100
        if win_rate >= 60:
            score += 0.3
        elif win_rate >= 50:
            score += 0.2

        total_signals = trust_metrics.get('total_signals', 0)
        if total_signals >= 20:
            score += 0.2
        elif total_signals >= 10:
            score += 0.1

        return min(1.0, score)