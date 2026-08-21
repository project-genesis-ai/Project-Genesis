from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Job:
    job_id: str
    title: str
    employer_id: str
    wage_per_tick: float
    skill: str = "general"

    def __post_init__(self) -> None:
        if not self.job_id.strip() or not self.title.strip() or not self.employer_id.strip() or self.wage_per_tick < 0:
            raise ValueError("invalid job")


@dataclass(slots=True)
class LaborMarket:
    jobs: dict[str, Job] = field(default_factory=dict)
    workers: dict[str, str] = field(default_factory=dict)

    def post(self, job: Job) -> None:
        if job.job_id in self.jobs:
            raise ValueError(f"job already exists: {job.job_id}")
        self.jobs[job.job_id] = job

    def hire(self, agent_id: str, job_id: str) -> bool:
        if not agent_id.strip() or job_id not in self.jobs or agent_id in self.workers:
            return False
        self.workers[agent_id] = job_id
        return True

    def fire(self, agent_id: str) -> bool:
        return self.workers.pop(agent_id, None) is not None

    def wage(self, agent_id: str, ticks: int = 1) -> float:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        job_id = self.workers.get(agent_id)
        return 0.0 if job_id is None else self.jobs[job_id].wage_per_tick * ticks
