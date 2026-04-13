"""Master Orchestrator Agent"""
from agents.base_agent import BaseAgent
from agents.market_data_agent import MarketDataAgent
from agents.sentiment_agent import SentimentAgent
from agents.risk_agent import RiskAgent
from agents.market_intelligence_agent import MarketIntelligenceAgent
from core.state_manager import StateManager
from core.llm_manager import LLMManager
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class MasterOrchestrator(BaseAgent):
    def __init__(self):
        super().__init__("Master Orchestrator", "orchestrator")
        self.state_manager = StateManager()
        self.llm_manager = LLMManager()

        # Initialize agents
        self.agents = {
            'market_data': MarketDataAgent(),
            'sentiment': SentimentAgent(),
            'risk': RiskAgent(),
            'market_intelligence': MarketIntelligenceAgent()
        }

    def analyze_stock(self, symbol: str, period: str = '1y', 
                     analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """Main entry point for stock analysis"""
        workflow_id = f"{symbol}_{analysis_type}"
        self.state_manager.create_workflow(workflow_id, list(self.agents.keys()))

        result = {
            'symbol': symbol,
            'period': period,
            'analysis_type': analysis_type,
            'agent_results': {},
            'overall_analysis': {},
            'recommendation': 'hold',
            'confidence': 0.0
        }

        try:
            # Execute Market Data Agent
            market_input = {'symbol': symbol, 'period': period}
            market_result = self.agents['market_data'].run(market_input)
            result['agent_results']['market_data'] = market_result
            self.state_manager.save_agent_result('market_data', market_result)

            # Execute Sentiment Agent (using news from market data)
            sentiment_input = {'news': market_result.get('news', [])}
            sentiment_result = self.agents['sentiment'].run(sentiment_input)
            result['agent_results']['sentiment'] = sentiment_result
            self.state_manager.save_agent_result('sentiment', sentiment_result)

            # Execute Risk Agent (using price data from market data)
            risk_input = {'price_data': market_result.get('price_data', {})}
            risk_result = self.agents['risk'].run(risk_input)
            result['agent_results']['risk'] = risk_result
            self.state_manager.save_agent_result('risk', risk_result)

            # Execute Market Intelligence Agent directly for combined signal
            mi_input = {
                'ticker': symbol,
                'risk_metrics': risk_result,
                'technical_indicators': market_result.get('technical_indicators', {}),
                'fundamental_metrics': market_result.get('company_info', {})
            }
            market_intelligence_result = self.agents['market_intelligence'].run(mi_input)
            result['agent_results']['market_intelligence'] = market_intelligence_result
            self.state_manager.save_agent_result('market_intelligence', market_intelligence_result)

            # Synthesize results
            result['overall_analysis'] = self._synthesize_results(result['agent_results'])
            result['recommendation'] = self._generate_recommendation(result['agent_results'])
            result['confidence'] = self._calculate_confidence(result['agent_results'])

            # Generate LLM summary if available
            if self.llm_manager.is_available():
                result['llm_summary'] = self._generate_llm_summary(symbol, result)

            self.state_manager.complete_workflow()

        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            result['error'] = str(e)
            self.state_manager.fail_workflow(str(e))

        return result

    def _synthesize_results(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize results from all agents"""
        synthesis = {}

        # Market overview
        market_data = agent_results.get('market_data', {})
        price_data = market_data.get('price_data', {})

        synthesis['current_price'] = price_data.get('current_price')
        synthesis['price_change'] = price_data.get('change_percent')

        # Sentiment
        sentiment_data = agent_results.get('sentiment', {})
        synthesis['sentiment'] = sentiment_data.get('overall_sentiment')

        # Risk
        risk_data = agent_results.get('risk', {})
        synthesis['risk_level'] = risk_data.get('risk_level')
        synthesis['volatility'] = risk_data.get('volatility')

        return synthesis

    def _generate_recommendation(self, agent_results: Dict[str, Any]) -> str:
        """Generate investment recommendation"""
        # Simple rule-based recommendation
        sentiment = agent_results.get('sentiment', {}).get('overall_sentiment', 'neutral')
        risk_level = agent_results.get('risk', {}).get('risk_level', 'Medium')
        market_intelligence = agent_results.get('market_intelligence', {})

        if market_intelligence.get('status') == 'success':
            mi_score = market_intelligence.get('final_score')
            if isinstance(mi_score, (int, float)):
                if mi_score >= 65.0 and risk_level != 'High':
                    return 'buy'
                if mi_score <= 35.0:
                    return 'sell'
                return 'hold'

        if sentiment == 'positive' and risk_level == 'Low':
            return 'buy'
        elif sentiment == 'negative' or risk_level == 'High':
            return 'sell'
        return 'hold'

    def _calculate_confidence(self, agent_results: Dict[str, Any]) -> float:
        """Calculate confidence with baseline and rescaling"""
        # Baseline confidence (minimum)
        baseline = 0.4

        # Weights for each component
        weights = {'market': 0.4, 'sentiment': 0.35, 'risk': 0.25}
        scores = {}

        # Market Data Score (0–1)
        md = agent_results.get('market_data', {})
        if md.get('status') == 'success':
            md_score = 0.0
            # Price exists
            if md['price_data'].get('current_price') is not None:
                md_score += 0.3
            # Price change magnitude (0–1 scaled)
            change_pct = abs(md['price_data'].get('change_percent', 0)) / 10
            md_score += min(change_pct, 0.2)
            # Company info
            if md['company_info'].get('name'):
                md_score += 0.2
            scores['market'] = min(md_score, 1.0)
        else:
            scores['market'] = 0.0

        # Sentiment Score (0–1)
        sa = agent_results.get('sentiment', {})
        if sa.get('status') == 'success':
            pos = sa['distribution'].get('positive', 0)
            neg = sa['distribution'].get('negative', 0)
            total = max(sa.get('articles_analyzed', 1), 1)
            raw = (pos - neg) / total  # -1..1
            # map -1..1 → 0..1
            sa_score = (raw + 1) / 2
            scores['sentiment'] = sa_score
        else:
            scores['sentiment'] = 0.0

        # Risk Score (0–1, inverted risk)
        ra = agent_results.get('risk', {})
        if ra.get('status') == 'success':
            level = ra.get('risk_level', 'Medium')
            # Lower risk→higher score
            mapping = {'Low': 1.0, 'Medium': 0.6, 'High': 0.3}
            scores['risk'] = mapping.get(level, 0.6)
        else:
            scores['risk'] = 0.0

        # Weighted sum (without baseline)
        conf = sum(scores[k] * weights[k] for k in weights)

        # Rescale: Add baseline, clamp between baseline and 1.0
        conf = baseline + (conf * (1.0 - baseline))
        conf = round(min(max(conf, baseline), 1.0), 2)

        print(f"[DEBUG] confidence components: {scores}, weighted={conf:.2f}")
        return conf


    def _generate_llm_summary(self, symbol: str, result: Dict[str, Any]) -> str:
        """Generate LLM summary of analysis"""
        try:
            prompt = f"""Provide a brief investment analysis summary for {symbol}:

Price: {result['overall_analysis'].get('current_price')}
Sentiment: {result['overall_analysis'].get('sentiment')}
Risk: {result['overall_analysis'].get('risk_level')}
Recommendation: {result['recommendation']}

Provide 2-3 sentences explaining the recommendation."""

            return self.llm_manager.generate(prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"LLM summary failed: {e}")
            return "Analysis completed. Check individual agent results for details."

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health status"""
        return {
            'orchestrator': self.get_metrics(),
            'agents': {name: agent.get_metrics() for name, agent in self.agents.items()},
            'llm_available': self.llm_manager.is_available()
        }

    def calculate_portfolio_metrics(self, holdings: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate portfolio-level metrics"""
        total_value = sum(h.get('market_value', 0) for h in holdings.values())
        return {
            'total_value': total_value,
            'positions': len(holdings)
        }

    def assess_portfolio_risk(self, holdings: Dict[str, Any]) -> Dict[str, Any]:
        """Assess portfolio risk"""
        return {
            'portfolio_risk': 'Medium',
            'diversification': len(holdings)
        }

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute orchestrated analysis"""
        return self.analyze_stock(
            symbol=input_data.get('symbol'),
            period=input_data.get('period', '1y'),
            analysis_type=input_data.get('analysis_type', 'comprehensive')
        )
