"""
Signal Analyst Agent
Converts raw model output into persuasive, trade-ready explanations
"""
from agents.page_agents import PageAgent
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SignalAnalystAgent(PageAgent):
    """Agent that transforms raw analysis into convincing signal explanations"""

    def __init__(self):
        super().__init__("Signal Analyst Agent", "signal_results")

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw analysis into persuasive signal explanation

        Input:
        - raw_analysis: Full analysis result from MasterOrchestrator
        - user_context: User behavior, usage count, etc.

        Output:
        - signal_summary: Human-friendly signal description
        - why_this_trade: Detailed reasoning
        - risk_assessment: Clear risk explanation
        - similar_opportunities: Related tickers to consider
        - confidence_explanation: What confidence means
        """
        raw_analysis = input_data.get('raw_analysis', {})
        user_context = input_data.get('user_context', {})

        # Extract key data
        ticker = raw_analysis.get('ticker', 'UNKNOWN')
        recommendation = raw_analysis.get('recommendation', 'HOLD').upper()
        confidence = raw_analysis.get('confidence_score', 0)
        risk_level = raw_analysis.get('risk_level', 'Medium')
        entry_price = raw_analysis.get('entry_price', 0)
        target_price = raw_analysis.get('target_price', 0)
        stop_loss = raw_analysis.get('stop_loss', 0)
        simple_explanation = raw_analysis.get('simple_explanation', '')

        # Generate persuasive signal summary
        signal_summary = self._generate_signal_summary(
            ticker, recommendation, confidence, risk_level
        )

        # Generate detailed reasoning
        why_this_trade = self._generate_trade_reasoning(
            raw_analysis, confidence, risk_level
        )

        # Generate risk assessment
        risk_assessment = self._generate_risk_assessment(
            risk_level, entry_price, target_price, stop_loss
        )

        # Generate similar opportunities
        similar_opportunities = self._generate_similar_opportunities(
            ticker, recommendation, raw_analysis
        )

        # Generate confidence explanation
        confidence_explanation = self._generate_confidence_explanation(
            confidence, raw_analysis
        )

        return {
            'signal_summary': signal_summary,
            'why_this_trade': why_this_trade,
            'risk_assessment': risk_assessment,
            'similar_opportunities': similar_opportunities,
            'confidence_explanation': confidence_explanation,
            'ui_payload': {
                'recommendation_badge': recommendation,
                'confidence_percentage': confidence,
                'risk_badge': risk_level,
                'entry_target_stop': {
                    'entry': entry_price,
                    'target': target_price,
                    'stop': stop_loss
                }
            }
        }

    def _generate_signal_summary(self, ticker: str, recommendation: str,
                               confidence: float, risk_level: str) -> str:
        """Generate compelling signal summary"""
        if recommendation == 'BUY':
            if confidence >= 80:
                return f"Strong BUY signal on {ticker} with {confidence}% confidence. Multiple technical and fundamental factors align for potential upside."
            elif confidence >= 60:
                return f"BUY opportunity on {ticker} with {confidence}% confidence. Solid setup with {risk_level.lower()} risk profile."
            else:
                return f"Potential BUY setup on {ticker} with {confidence}% confidence. Monitor closely for confirmation."
        elif recommendation == 'SELL':
            if confidence >= 80:
                return f"Strong SELL signal on {ticker} with {confidence}% confidence. Risk indicators suggest caution."
            elif confidence >= 60:
                return f"SELL opportunity on {ticker} with {confidence}% confidence. Technical weakness detected."
            else:
                return f"Potential SELL setup on {ticker} with {confidence}% confidence. Consider reducing exposure."
        else:
            return f"HOLD signal on {ticker} with {confidence}% confidence. Current conditions suggest waiting for clearer direction."

    def _generate_trade_reasoning(self, analysis: Dict[str, Any],
                                confidence: float, risk_level: str) -> str:
        """Generate detailed trade reasoning"""
        reasoning_parts = []

        # Technical factors
        tech_indicators = analysis.get('technical_indicators', {})
        if tech_indicators:
            rsi = tech_indicators.get('rsi_14')
            trend = tech_indicators.get('trend')
            if rsi:
                if rsi > 70:
                    reasoning_parts.append("RSI indicates overbought conditions, suggesting potential reversal.")
                elif rsi < 30:
                    reasoning_parts.append("RSI indicates oversold conditions, suggesting potential bounce.")
            if trend:
                reasoning_parts.append(f"Price trend analysis shows {trend.lower()} momentum.")

        # Risk factors
        risk_metrics = analysis.get('risk_metrics', {})
        volatility = risk_metrics.get('volatility')
        if volatility:
            vol_pct = volatility * 100
            if vol_pct > 50:
                reasoning_parts.append(".2f")
            elif vol_pct < 20:
                reasoning_parts.append(".2f")

        # Key drivers
        key_drivers = analysis.get('key_drivers', [])
        if key_drivers:
            reasoning_parts.append("Key factors driving this signal:")
            for driver in key_drivers[:3]:
                reasoning_parts.append(f"• {driver}")

        # Confidence context
        if confidence >= 75:
            reasoning_parts.append("High confidence due to strong alignment across multiple indicators.")
        elif confidence >= 50:
            reasoning_parts.append("Moderate confidence with some conflicting signals but overall directional bias.")
        else:
            reasoning_parts.append("Lower confidence suggests this is more of a watchlist idea than an immediate trade.")

        return " ".join(reasoning_parts) if reasoning_parts else "Analysis based on technical and fundamental indicators."

    def _generate_risk_assessment(self, risk_level: str, entry: float,
                                target: float, stop: float) -> str:
        """Generate clear risk assessment"""
        if not entry or not target or not stop:
            return f"Risk level: {risk_level}. Please verify entry, target, and stop levels."

        upside = ((target - entry) / entry) * 100
        downside = ((entry - stop) / entry) * 100
        risk_reward = upside / downside if downside > 0 else 0

        assessment = f"Risk Level: {risk_level}\n"
        assessment += f"Upside potential: +{upside:.1f}%\n"
        assessment += f"Downside risk: -{downside:.1f}%\n"
        assessment += f"Risk/Reward ratio: 1:{risk_reward:.2f}"

        if risk_level == 'Low':
            assessment += " Conservative approach with tight risk management."
        elif risk_level == 'Medium':
            assessment += " Balanced risk-reward setup for most traders."
        else:
            assessment += " Higher volatility expected - use appropriate position sizing."

        return assessment

    def _generate_similar_opportunities(self, ticker: str, recommendation: str,
                                      analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate similar ticker suggestions"""
        # Simple placeholder - in production, this would analyze sector, market cap, etc.
        similar_tickers = {
            'AAPL': ['MSFT', 'GOOGL', 'NVDA'],
            'MSFT': ['AAPL', 'GOOGL', 'AMZN'],
            'NVDA': ['AMD', 'INTC', 'QCOM'],
            'TSLA': ['F', 'GM', 'RIVN'],
            'AMZN': ['MSFT', 'GOOGL', 'META']
        }

        similar = similar_tickers.get(ticker.upper(), ['SPY', 'QQQ', 'IWM'])
        opportunities = []

        for similar_ticker in similar[:3]:
            opportunities.append({
                'ticker': similar_ticker,
                'reason': f"Similar {recommendation.lower()} setup to {ticker}",
                'confidence': max(50, analysis.get('confidence_score', 0) - 10)  # Slightly lower confidence
            })

        return opportunities

    def _generate_confidence_explanation(self, confidence: float,
                                       analysis: Dict[str, Any]) -> str:
        """Explain what confidence score means"""
        if confidence >= 80:
            return "High confidence (80%+) means strong alignment across technical, fundamental, and sentiment indicators. This represents a high-probability setup."
        elif confidence >= 60:
            return "Moderate confidence (60-79%) indicates good directional bias but some conflicting signals. Use as part of a diversified approach."
        elif confidence >= 40:
            return "Lower confidence (40-59%) suggests this is more of a watchlist opportunity than an immediate trade. Monitor for confirmation."
        else:
            return "Low confidence (<40%) indicates significant uncertainty. Consider this a directional bias rather than a strong signal."