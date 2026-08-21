from genesis.knowledge.model import Experience
from genesis.knowledge.repository import KnowledgeRepository


def test_experience_capacity_is_deterministically_bounded() -> None:
    repo = KnowledgeRepository(max_experiences_per_domain=2)
    for tick in range(3):
        repo.record(
            Experience(
                f"e:{tick}",
                "science",
                "actor",
                tick,
                "obs",
                "act",
                "out",
                True,
            )
        )
    assert tuple(repo.domains["science"].experiences) == ("e:1", "e:2")
