from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class PoliticalFaction:
    faction_id: str
    name: str
    members: set[str] = field(default_factory=set)
    influence: float = 0.0

    def __post_init__(self) -> None:
        if not self.faction_id.strip() or not self.name.strip() or not 0.0 <= self.influence <= 1.0:
            raise ValueError("invalid faction")


@dataclass(frozen=True, slots=True)
class Election:
    election_id: str
    candidates: tuple[str, ...]
    votes: dict[str, int] = field(default_factory=dict)

    def winner(self) -> str | None:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda candidate: (self.votes.get(candidate, 0), candidate))


@dataclass(frozen=True, slots=True)
class Treaty:
    treaty_id: str
    parties: tuple[str, ...]
    terms: tuple[str, ...]
    duration_ticks: int

    def __post_init__(self) -> None:
        if not self.treaty_id.strip() or len(self.parties) < 2 or self.duration_ticks < 1:
            raise ValueError("invalid treaty")


@dataclass(slots=True)
class PoliticalSystem:
    factions: dict[str, PoliticalFaction] = field(default_factory=dict)
    elections: dict[str, Election] = field(default_factory=dict)
    treaties: dict[str, Treaty] = field(default_factory=dict)
    conflicts: dict[tuple[str, str], float] = field(default_factory=dict)

    def add_faction(self, faction: PoliticalFaction) -> None:
        if faction.faction_id in self.factions:
            raise ValueError(f"faction already exists: {faction.faction_id}")
        self.factions[faction.faction_id] = faction

    def start_election(self, election: Election) -> None:
        if election.election_id in self.elections:
            raise ValueError(f"election already exists: {election.election_id}")
        self.elections[election.election_id] = election

    def vote(self, election_id: str, candidate: str) -> None:
        election = self.elections[election_id]
        if candidate not in election.candidates:
            raise ValueError("candidate is not on the ballot")
        votes = dict(election.votes)
        votes[candidate] = votes.get(candidate, 0) + 1
        self.elections[election_id] = Election(election.election_id, election.candidates, votes)

    def sign_treaty(self, treaty: Treaty) -> None:
        if treaty.treaty_id in self.treaties:
            raise ValueError(f"treaty already exists: {treaty.treaty_id}")
        self.treaties[treaty.treaty_id] = treaty

    def set_conflict(self, left: str, right: str, intensity: float) -> None:
        if left == right or not 0.0 <= intensity <= 1.0:
            raise ValueError("invalid conflict")
        self.conflicts[tuple(sorted((left, right)))] = intensity
