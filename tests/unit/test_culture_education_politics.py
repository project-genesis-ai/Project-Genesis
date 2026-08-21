from genesis.civilization import Innovation, InnovationSystem
from genesis.education import Course, EducationSystem
from genesis.politics import Election, PoliticalFaction, PoliticalSystem, Treaty


def test_education_progresses_to_completion() -> None:
    education = EducationSystem()
    education.add_course(Course("c1", "Farming", "farming", 10))
    assert not education.study("a1", "c1", 4)
    assert education.study("a1", "c1", 6)


def test_election_and_treaty_are_deterministic() -> None:
    politics = PoliticalSystem()
    politics.add_faction(PoliticalFaction("f1", "Civic", influence=0.5))
    politics.start_election(Election("e1", ("alice", "bob")))
    politics.vote("e1", "bob")
    politics.vote("e1", "bob")
    politics.vote("e1", "alice")
    assert politics.elections["e1"].winner() == "bob"
    politics.sign_treaty(Treaty("t1", ("a", "b"), ("peace",), 20))
    assert "t1" in politics.treaties


def test_innovation_requires_prerequisites_and_tracks_adoption() -> None:
    system = InnovationSystem()
    innovation = Innovation("wheel", "Wheel", "a1", frozenset({"fire"}), utility=0.8)
    assert not system.discover(innovation, set())
    assert system.discover(innovation, {"fire"})
    system.adopt("wheel", "a2")
    assert system.adoption_rate("wheel", 4) == 0.5
