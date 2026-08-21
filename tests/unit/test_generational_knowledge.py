import pytest

from genesis.agents.agent import Agent
from genesis.core.simulation import Simulation
from genesis.knowledge.model import Experience, KnowledgeStatus
from genesis.knowledge.repository import KnowledgeRepository


def experience(i: int, actor: str, domain: str = "medicine", success: bool = True) -> Experience:
    return Experience(
        experience_id=f"exp:{domain}:{i}",
        domain=domain,
        actor_id=actor,
        tick=i,
        observation="controlled observation",
        action="tested intervention",
        outcome="measured outcome",
        success=success,
        confidence=0.9,
    )


def test_lessons_require_independent_repeated_evidence() -> None:
    repo = KnowledgeRepository(minimum_verification_evidence=3)
    repo.record(experience(1, "a"))
    repo.record(experience(2, "a"))
    provisional = repo.propose_lesson(
        lesson_id="lesson:1",
        domain="medicine",
        statement="The intervention is useful under the observed condition.",
        evidence_ids=("exp:medicine:1", "exp:medicine:2"),
    )
    assert provisional.status is KnowledgeStatus.PROVISIONAL

    repo.record(experience(3, "b"))
    verified = repo.propose_lesson(
        lesson_id="lesson:2",
        domain="medicine",
        statement="The intervention is reproducibly useful under the observed condition.",
        evidence_ids=("exp:medicine:1", "exp:medicine:2", "exp:medicine:3"),
        generation=1,
    )
    assert verified.status is KnowledgeStatus.VERIFIED


def test_domains_do_not_cross_contaminate() -> None:
    repo = KnowledgeRepository()
    for i, actor in enumerate(("a", "b", "c"), start=1):
        repo.record(experience(i, actor, "trading"))
    lesson = repo.propose_lesson(
        lesson_id="lesson:trading:1",
        domain="trading",
        statement="The tested strategy was robust in the observed regime.",
        evidence_ids=("exp:trading:1", "exp:trading:2", "exp:trading:3"),
    )
    assert [item.lesson_id for item in repo.verified_lessons("medicine")] == []
    assert repo.verified_lessons("trading") == (lesson,)


def test_verified_knowledge_reaches_living_agents_deterministically() -> None:
    simulation = Simulation()
    for agent_id in ("a", "b", "c"):
        simulation.add_agent(Agent(agent_id, agent_id))
    for i, actor in enumerate(("a", "b", "c"), start=1):
        simulation.state.record_knowledge_experience(experience(i, actor, "engineering"))
    simulation.state.knowledge.propose_lesson(
        lesson_id="lesson:engineering:1",
        domain="engineering",
        statement="The tested design survives the observed load.",
        evidence_ids=("exp:engineering:1", "exp:engineering:2", "exp:engineering:3"),
        generation=1,
    )
    simulation.step()
    assert all("lesson:engineering:1" in agent.knowledge for agent in simulation.state.agents.values())
    assert len(simulation.state.knowledge_runtime.transfers) == 3


def test_duplicate_experience_is_rejected() -> None:
    repo = KnowledgeRepository()
    item = experience(1, "a")
    repo.record(item)
    with pytest.raises(ValueError, match="duplicate experience"):
        repo.record(item)
