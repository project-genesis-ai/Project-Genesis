from genesis.social.physiology import HumanPhysiology, LifeStage
from genesis.social.relationships import RelationType, Relationship, RelationshipGraph
from genesis.social.social import SocialGroup, SocialSystem


def test_human_physiology_lifecycle_and_recovery() -> None:
    human = HumanPhysiology(age_ticks=799)
    assert human.life_stage is LifeStage.ADOLESCENT
    human.rest(5)
    human.eat(0.2)
    human.drink(0.2)
    assert human.energy > 0.9
    human.step(1, activity=0.0)
    assert human.age_ticks == 800
    assert human.life_stage is LifeStage.ADULT


def test_injury_and_death_are_bounded() -> None:
    human = HumanPhysiology(health=0.6)
    human.injure(0.5)
    assert 0.0 <= human.health <= 1.0
    human.injure(1.0)
    assert human.health == 0.0
    assert not human.alive


def test_relationship_trust_and_neighbors() -> None:
    graph = RelationshipGraph()
    relation = Relationship("a", "b", RelationType.FRIEND)
    graph.connect(relation)
    relation.interact(positive=1.0)
    assert graph.trust("a", "b") > 0.5
    assert len(graph.neighbors("a")) == 1


def test_family_and_group_membership() -> None:
    social = SocialSystem()
    social.establish_family("parent", "child")
    assert social.relationships.get("parent", "child", RelationType.PARENT) is not None
    group = SocialGroup("village")
    group.join("child")
    group.update_reputation("child", 0.5)
    assert group.reputation["child"] == 0.5
