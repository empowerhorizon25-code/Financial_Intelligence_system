"""
Trust & Proof Agent
Builds trust through verifiable outcome data and performance metrics
"""
from agents.page_agents import PageAgent
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class TrustProofAgent(PageAgent):
    """Agent that provides transparency and builds trust through performance data"""

    def __init__(self):
        super().__init__("Trust & Proof Agent", "transparency")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate trust-building content from performance data

        Input:
        - performance_history: Last 30 signals with outcomes
        - current_metrics: Win rate, drawdown, Sharpe ratio, etc.
        - user_context: How long user has been using the service

        Output:
        - performance_summary: Key metrics explained in plain language
        - last_signal_result: Most recent signal outcome
        - metric_definitions: What each metric means
        - trust_message: Overall credibility statement
        """
        performance_history = input_data.get('performance_history', [])
        current_metrics = input_data.get('current_metrics', {})
        user_context = input_data.get('user_context', {})

        # Generate performance summary
        performance_summary = self._generate_performance_summary(current_metrics)

        # Get last signal result
        last_signal_result = self._get_last_signal_result(performance_history)

        # Generate metric definitions
        metric_definitions = self._generate_metric_definitions(current_metrics)

        # Generate trust message
        trust_message = self._generate_trust_message(
            current_metrics, len(performance_history), user_context
        )

        return {
            'performance_summary': performance_summary,
            'last_signal_result': last_signal_result,
            'metric_definitions': metric_definitions,
            'trust_message': trust_message,
            'ui_payload': {
                'performance_cards': self._format_performance_cards(current_metrics),
                'last_result_card': last_signal_result,
                'trust_badge': self._calculate_trust_score(current_metrics)
            }
        }

    def _generate_performance_summary(self, metrics: Dict[str, Any]) -> str:
        """Generate human-friendly performance summary"""
        win_rate = metrics.get('win_rate', 0) * 100
        total_signals = metrics.get('total_signals', 0)
        avg_return = metrics.get('avg_return', 0) * 100
        max_drawdown = metrics.get('max_drawdown', 0) * 100
        sharpe_ratio = metrics.get('sharpe_ratio', 0)

        summary_parts = []

        if total_signals > 0:
            summary_parts.append(f"Across {total_signals} signals, we've achieved a {win_rate:.1f}% win rate.")

            if avg_return > 0:
                summary_parts.append(f"Average return per signal: +{avg_return:.1f}%.")
            elif avg_return < 0:
                summary_parts.append(f"Average return per signal: {avg_return:.1f}%.")

            if max_drawdown > 0:
                summary_parts.append(f"Maximum drawdown: {max_drawdown:.1f}% (worst peak-to-trough decline).")

            if sharpe_ratio > 0:
                if sharpe_ratio > 1:
                    summary_parts.append("Sharpe ratio above 1 indicates good risk-adjusted returns.")
                else:
                    summary_parts.append("Sharpe ratio shows moderate risk-adjusted performance.")

        return " ".join(summary_parts) if summary_parts else "Performance data will be available after more signals are tracked."

    def _get_last_signal_result(self, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get the most recent signal result"""
        if not history:
            return {
                'status': 'no_data',
                'message': 'No signal history available yet.',
                'outcome': None
            }

        last_signal = history[0]  # Assuming history is sorted newest first

        return {
            'ticker': last_signal.get('ticker', 'UNKNOWN'),
            'signal': last_signal.get('signal', 'HOLD'),
            'confidence': last_signal.get('confidence', 0),
            'outcome': last_signal.get('outcome', 'pending'),
            'return_pct': last_signal.get('realized_return', 0) * 100,
            'timestamp': last_signal.get('timestamp', 'Unknown'),
            'message': self._format_last_result_message(last_signal)
        }

    def _format_last_result_message(self, signal: Dict[str, Any]) -> str:
        """Format last signal result into readable message"""
        ticker = signal.get('ticker', 'UNKNOWN')
        signal_type = signal.get('signal', 'HOLD')
        outcome = signal.get('outcome', 'pending')
        return_pct = signal.get('realized_return', 0) * 100

        if outcome == 'win':
            return f"{signal_type} signal on {ticker} resulted in +{return_pct:.1f}% gain"
        elif outcome == 'loss':
            return f"{signal_type} signal on {ticker} resulted in {return_pct:.1f}% loss"
        elif outcome == 'pending':
            return f"{signal_type} signal on {ticker} is still active."
        else:
            return f"{signal_type} signal on {ticker} - outcome pending."

    def _generate_metric_definitions(self, metrics: Dict[str, Any]) -> Dict[str, str]:
        """Provide plain language definitions for metrics"""
        definitions = {}

        win_rate = metrics.get('win_rate', 0) * 100
        if win_rate > 0:
            definitions['win_rate'] = ".1f"

        avg_return = metrics.get('avg_return', 0) * 100
        if avg_return != 0:
            definitions['avg_return'] = ".1f"

        max_drawdown = metrics.get('max_drawdown', 0) * 100
        if max_drawdown > 0:
            definitions['max_drawdown'] = ".1f"

        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        if sharpe_ratio != 0:
            definitions['sharpe_ratio'] = ".2f"

        return definitions

    def _generate_trust_message(self, metrics: Dict[str, Any], signal_count: int,
                              user_context: Dict[str, Any]) -> str:
        """Generate overall trust and credibility message"""
        if signal_count < 5:
            return "We're building our track record. All signals are based on proven technical and fundamental analysis."

        win_rate = metrics.get('win_rate', 0) * 100
        sharpe_ratio = metrics.get('sharpe_ratio', 0)

        if win_rate >= 60 and sharpe_ratio >= 0.5:
            return "Strong track record with consistent performance above market averages. Every signal includes clear entry, target, and stop levels."
        elif win_rate >= 50:
            return "Solid performance with balanced risk management. We show both wins and losses transparently to build trust."
        else:
            return "We're committed to transparency. Performance data helps you make informed decisions about our signals."

    def _format_performance_cards(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format metrics for UI performance cards"""
        cards = []

        win_rate = metrics.get('win_rate', 0) * 100
        if win_rate > 0:
            cards.append({
                'title': 'Win Rate',
                'value': '.1f',
                'description': 'Percentage of signals that hit target price'
            })

        avg_return = metrics.get('avg_return', 0) * 100
        if avg_return != 0:
            cards.append({
                'title': 'Avg Return',
                'value': '.1f',
                'description': 'Average return per signal'
            })

        max_drawdown = metrics.get('max_drawdown', 0) * 100
        if max_drawdown > 0:
            cards.append({
                'title': 'Max Drawdown',
                'value': '.1f',
                'description': 'Worst peak-to-trough decline'
            })

        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        if sharpe_ratio != 0:
            cards.append({
                'title': 'Sharpe Ratio',
                'value': '.2f',
                'description': 'Risk-adjusted return measure'
            })

        return cards

    def _calculate_trust_score(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall trust score for UI badge"""
        win_rate = metrics.get('win_rate', 0) * 100
        sharpe_ratio = metrics.get('sharpe_ratio', 0)
        signal_count = metrics.get('total_signals', 0)

        # Simple trust scoring
        trust_score = 0

        if signal_count >= 10:
            trust_score += 20
        elif signal_count >= 5:
            trust_score += 10

        if win_rate >= 60:
            trust_score += 30
        elif win_rate >= 50:
            trust_score += 20
        elif win_rate >= 40:
            trust_score += 10

        if sharpe_ratio >= 1.0:
            trust_score += 30
        elif sharpe_ratio >= 0.5:
            trust_score += 20
        elif sharpe_ratio >= 0:
            trust_score += 10

        trust_level = 'Low'
        if trust_score >= 70:
            trust_level = 'High'
        elif trust_score >= 40:
            trust_level = 'Medium'

        return {
            'score': trust_score,
            'level': trust_level,
            'description': f"{trust_level} trust score based on {signal_count} signals"
        }