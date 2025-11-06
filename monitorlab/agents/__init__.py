"""Domain agents for testing complete features and workflows."""

from monitorlab.agents.base_agent import DomainAgent, AgentState
from monitorlab.agents.homepage_agent import HomepageAgent
from monitorlab.agents.auth_agent import AuthenticationAgent
from monitorlab.agents.checkout_agent import CheckoutAgent
from monitorlab.agents.generic_agent import GenericTestAgent

__all__ = [
    "DomainAgent",
    "AgentState",
    "HomepageAgent",
    "AuthenticationAgent",
    "CheckoutAgent",
    "GenericTestAgent",
]
