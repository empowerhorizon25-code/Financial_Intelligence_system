"""Unit Tests for Agents"""
import unittest
from agents.market_data_agent import MarketDataAgent
from agents.sentiment_agent import SentimentAgent
from agents.market_intelligence_agent import MarketIntelligenceAgent
from agents.orchestrator import MasterOrchestrator

class TestMarketDataAgent(unittest.TestCase):
    def setUp(self):
        self.agent = MarketDataAgent()

    def test_agent_initialization(self):
        self.assertEqual(self.agent.agent_name, "Market Data Agent")
        self.assertEqual(self.agent.agent_type, "market_data")

    def test_execute_with_valid_symbol(self):
        result = self.agent.run({'symbol': 'AAPL', 'period': '1mo'})
        self.assertEqual(result['status'], 'success')
        self.assertIn('price_data', result)

class TestSentimentAgent(unittest.TestCase):
    def setUp(self):
        self.agent = SentimentAgent()

    def test_sentiment_analysis(self):
        news = [
            {'title': 'Stock surges on strong earnings', 'summary': ''},
            {'title': 'Company beats expectations', 'summary': ''}
        ]
        result = self.agent.run({'news': news})
        self.assertEqual(result['status'], 'success')
        self.assertIn('overall_sentiment', result)

class TestOrchestrator(unittest.TestCase):
    def setUp(self):
        self.orchestrator = MasterOrchestrator()

    def test_orchestrator_initialization(self):
        self.assertIsNotNone(self.orchestrator.agents)
        self.assertIn('market_data', self.orchestrator.agents)
        self.assertIn('market_intelligence', self.orchestrator.agents)

    def test_analyze_stock(self):
        result = self.orchestrator.analyze_stock('AAPL', '1mo')
        self.assertIn('symbol', result)
        self.assertIn('recommendation', result)
        self.assertIn('market_intelligence', result['agent_results'])

if __name__ == '__main__':
    unittest.main()
