import pytest

from genesis.agents.agent import Agent
from genesis.agents.needs import Needs
from genesis.agents.personality import Personality


def test_agent_has_stable_identity_and_state() -> None:
    agent = Agent("citizen-1", "First Citizen")
    assert agent.agent_id == "citizen-1"
    assert agent.health == 1.0
    assert agent.needs.highest_priority() is None


def test_needs_priority_and_bounds() -> None:
    needs = Needs(hunger=0.2, thirst=0.8, energy=0.3)
    assert needs.highest_priority() == "thirst"
    with pytest.raises(ValueError):
        Needs(hunger=1.1)


def test_personality_bounds() -> None:
    Personality(curiosity=0.0, risk_tolerance=1.0)
    with pytest.raises(ValueError):
        Personality(patience=-0.1)
