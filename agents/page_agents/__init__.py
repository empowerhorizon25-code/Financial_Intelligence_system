"""
Page Agent Framework for AI Stock Signals SaaS
Provides base classes and management for page-specific AI agents
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from agents.base_agent import BaseAgent
from core.state_manager import StateManager
import logging

logger = logging.getLogger(__name__)

class PageAgent(BaseAgent, ABC):
    """Abstract base class for page-specific agents"""

    def __init__(self, agent_name: str, page_context: str):
        super().__init__(agent_name, "page_agent")
        self.page_context = page_context
        self.state_manager = StateManager()

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute page-specific logic
        Must be implemented by subclasses
        """
        pass

    def get_shared_state(self, key: str) -> Optional[Any]:
        """Get value from shared state"""
        return self.state_manager.get_agent_result(key)

    def set_shared_state(self, key: str, value: Any):
        """Set value in shared state"""
        self.state_manager.save_agent_result(key, value)

class PageAgentManager:
    """Manages page agents and shared state"""

    def __init__(self):
        self.agents: Dict[str, PageAgent] = {}
        self.state_manager = StateManager()

    def register_agent(self, agent_name: str, agent: PageAgent):
        """Register a page agent"""
        self.agents[agent_name] = agent
        logger.info(f"Registered page agent: {agent_name}")

    def run(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run a page agent with given context"""
        if agent_name not in self.agents:
            raise ValueError(f"Page agent '{agent_name}' not registered")

        agent = self.agents[agent_name]
        return agent.run(context)

    def get_shared_state(self, key: str) -> Optional[Any]:
        """Get shared state value"""
        return self.state_manager.get_agent_result(key)

    def set_shared_state(self, key: str, value: Any):
        """Set shared state value"""
        self.state_manager.save_agent_result(key, value)

    def get_all_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        return {name: agent.get_metrics() for name, agent in self.agents.items()}

# Global page agent manager instance
page_agent_manager = PageAgentManager()

# Initialize agents
def initialize_page_agents():
    """Initialize and register all page agents"""
    try:
        from agents.page_agents.signal_analyst_agent import SignalAnalystAgent
        from agents.page_agents.trust_proof_agent import TrustProofAgent
        from agents.page_agents.conversion_agent import ConversionAgent
        from agents.page_agents.acquisition_agent import AcquisitionAgent

        # Register Signal Analyst Agent
        signal_agent = SignalAnalystAgent()
        page_agent_manager.register_agent('signal_analyst', signal_agent)

        # Register Trust & Proof Agent
        trust_agent = TrustProofAgent()
        page_agent_manager.register_agent('trust_proof', trust_agent)

        # Register Conversion Agent
        conversion_agent = ConversionAgent()
        page_agent_manager.register_agent('conversion', conversion_agent)

        # Register Acquisition Agent
        acquisition_agent = AcquisitionAgent()
        page_agent_manager.register_agent('acquisition', acquisition_agent)

        logger.info("All page agents initialized successfully")
        return page_agent_manager

    except Exception as e:
        logger.error(f"Failed to initialize page agents: {e}")
        raise

# Initialize agents when module is imported
page_agent_manager = initialize_page_agents()