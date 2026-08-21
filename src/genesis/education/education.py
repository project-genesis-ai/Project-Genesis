from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Course:
    course_id: str
    subject: str
    skill: str
    duration_ticks: int
    difficulty: float = 0.5

    def __post_init__(self) -> None:
        if not self.course_id.strip() or not self.subject.strip() or not self.skill.strip() or self.duration_ticks < 1 or not 0.0 <= self.difficulty <= 1.0:
            raise ValueError("invalid course")


@dataclass(slots=True)
class StudentRecord:
    agent_id: str
    course_id: str
    progress: float = 0.0
    completed: bool = False

    def study(self, ticks: int, course: Course) -> bool:
        if ticks < 0:
            raise ValueError("ticks cannot be negative")
        self.progress = min(1.0, self.progress + ticks / course.duration_ticks)
        self.completed = self.progress >= 1.0
        return self.completed


@dataclass(slots=True)
class EducationSystem:
    courses: dict[str, Course] = field(default_factory=dict)
    students: dict[tuple[str, str], StudentRecord] = field(default_factory=dict)

    def add_course(self, course: Course) -> None:
        if course.course_id in self.courses:
            raise ValueError(f"course already exists: {course.course_id}")
        self.courses[course.course_id] = course

    def enroll(self, agent_id: str, course_id: str) -> StudentRecord:
        if course_id not in self.courses:
            raise ValueError(f"unknown course: {course_id}")
        key = (agent_id, course_id)
        record = self.students.setdefault(key, StudentRecord(agent_id, course_id))
        return record

    def study(self, agent_id: str, course_id: str, ticks: int) -> bool:
        record = self.enroll(agent_id, course_id)
        return record.study(ticks, self.courses[course_id])
