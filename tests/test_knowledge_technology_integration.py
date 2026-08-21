from genesis.agents.agent import Agent
from genesis.civilization.technology import Technology
from genesis.knowledge.model import KnowledgeStatus
from genesis.knowledge.repository import KnowledgeRepository
from genesis.knowledge.runtime import KnowledgeRuntime
from genesis.science.research import ResearchProject


def test_completed_research_becomes_evidence_backed_verified_knowledge() -> None:
    repository = KnowledgeRepository()
    runtime = KnowledgeRuntime()
    technology = Technology("irrigation", "Irrigation", research_cost=1.0, progress=1.0, unlocked=True)
    project = ResearchProject("research:irrigation", "irrigation", progress=1.0, researchers={"a", "b", "c"})

    lesson = runtime.publish_research_result(repository, technology, project, tick=12)

    assert lesson.lesson_id == "technology:irrigation"
    assert lesson.status is KnowledgeStatus.VERIFIED
    assert len(lesson.evidence_ids) == 3
    assert repository.domains_with_verified_knowledge() == ("technology",)


def test_research_publication_is_idempotent() -> None:
    repository = KnowledgeRepository()
    runtime = KnowledgeRuntime()
    technology = Technology("metallurgy", "Metallurgy", research_cost=1.0, progress=1.0, unlocked=True)
    project = ResearchProject("research:metallurgy", "metallurgy", progress=1.0, researchers={"a", "b", "c"})

    first = runtime.publish_research_result(repository, technology, project, tick=4)
    second = runtime.publish_research_result(repository, technology, project, tick=9)

    assert first == second
    assert len(repository.domains["technology"].experiences) == 3


def test_verified_technology_transfers_to_living_agents_only() -> None:
    repository = KnowledgeRepository()
    runtime = KnowledgeRuntime()
    technology = Technology("writing", "Writing", research_cost=1.0, progress=1.0, unlocked=True)
    project = ResearchProject("research:writing", "writing", progress=1.0, researchers={"a", "b", "c"})
    runtime.publish_research_result(repository, technology, project, tick=2)

    living = Agent("learner", "Learner")
    dead = Agent("dead", "Dead", health=0.0)
    result = runtime.step(repository, {living.agent_id: living, dead.agent_id: dead}, tick=3)

    assert [item.lesson_id for item in result.transfers] == ["technology:writing"]
    assert "technology:writing" in living.knowledge
    assert "technology:writing" not in dead.knowledge
