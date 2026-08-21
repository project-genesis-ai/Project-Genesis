import pytest

from genesis.agents.agent import Agent
from genesis.agents.needs import Needs
from genesis.agents.personality import Personality
from genesis.social.runtime import SocialRuntime
from genesis.social.social import SocialSystem


def test_positive_social_interaction_relieves_social_and_comfort_needs() -> None:
    agents = {
        "a": Agent("a", "A", needs=Needs(social=0.8, comfort=0.6)),
        "b": Agent("b", "B", needs=Needs(social=0.8, comfort=0.6)),
    }
    result = SocialRuntime().step(SocialSystem(), agents, tick=1)

    assert result.interactions == 1
    assert agents["a"].needs.social < 0.8
    assert agents["b"].needs.social < 0.8
    assert agents["a"].needs.comfort < 0.6
    assert agents["b"].needs.comfort < 0.6


def test_conflict_adds_bounded_social_stress() -> None:
    hostile = Personality(curiosity=0.0, risk_tolerance=0.0, cooperation=0.0, patience=0.0)
    opposite = Personality(curiosity=1.0, risk_tolerance=1.0, cooperation=1.0, patience=1.0)
    agents = {
        "a": Agent("a", "A", personality=hostile, needs=Needs(social=0.2, hunger=1.0, thirst=1.0)),
        "b": Agent("b", "B", personality=opposite, needs=Needs(social=0.2, hunger=1.0, thirst=1.0)),
    }

    SocialRuntime().step(SocialSystem(), agents, tick=1)

    assert agents["a"].needs.social > 0.2
    assert agents["b"].needs.social > 0.2
    assert agents["a"].needs.social <= 1.0
    assert agents["b"].needs.social <= 1.0


def test_social_runtime_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        SocialRuntime(max_interactions_per_agent=0)
    with pytest.raises(ValueError):
        SocialRuntime(social_relief_per_positive=-0.1)
