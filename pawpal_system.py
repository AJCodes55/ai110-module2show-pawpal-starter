from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes — pure data containers (Pet, Task, Owner, Constraint, UserPreferences)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    energy_level: int
    special_needs: str = ""

    def get_daily_needs(self) -> list[str]:
        pass

    def adjust_task_priority(self, _task: Task) -> None:
        pass


@dataclass
class Task:
    name: str
    duration: int          # minutes
    priority: int
    category: str
    is_mandatory: bool
    deadline: Optional[datetime] = None

    def get_priority_score(self) -> int:
        pass

    def is_urgent(self, _current_time: datetime) -> bool:
        pass


@dataclass
class Constraint:
    max_time_available: int            # minutes
    preferred_times: list[str] = field(default_factory=list)
    task_limits: dict[str, int] = field(default_factory=dict)

    def is_task_allowed(self, _task: Task) -> bool:
        pass

    def can_fit(self, _task: Task, _remaining_time: int) -> bool:
        pass


@dataclass
class UserPreferences:
    preferred_task_times: dict[str, str] = field(default_factory=dict)
    disliked_tasks: list[str] = field(default_factory=list)
    routine_style: str = "flexible"    # e.g. "morning", "evening", "flexible"

    def adjust_priority(self, _task: Task) -> None:
        pass

    def filter_tasks(self, _tasks: list[Task]) -> list[Task]:
        pass


@dataclass
class Owner:
    name: str
    available_time_per_day: int        # minutes
    preferred_schedule: str            # "morning" | "evening" | "flexible"
    experience_level: str              # "new" | "intermediate" | "expert"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    pets: list[Pet] = field(default_factory=list)

    def set_preferences(self, _preferences: UserPreferences) -> None:
        pass

    def update_availability(self, _time: int) -> None:
        pass

    def get_available_time(self) -> int:
        pass

    def adjust_task_priority(self, _task: Task) -> None:
        pass


# ---------------------------------------------------------------------------
# Behaviour classes — logic-heavy (Schedule, Planner, ExplanationEngine)
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(self) -> None:
        self.tasks: list[Task] = []
        self.total_time: int = 0
        self.unused_time: int = 0

    def add_task(self, task: Task) -> None:
        pass

    def get_summary(self) -> str:
        pass

    def validate(self, constraints: Constraint) -> bool:
        pass


class ExplanationEngine:
    def explain(self, schedule: Schedule) -> str:
        pass

    def justify_task(self, task: Task) -> str:
        pass


class Planner:
    def __init__(self, pet: Pet, owner: Owner, tasks: list[Task], constraints: Constraint) -> None:
        self.pet = pet
        self.owner = owner
        self.tasks = tasks
        self.constraints = constraints
        self._explanation_engine = ExplanationEngine()

    def generate_plan(self) -> Schedule:
        pass

    def prioritize_tasks(self) -> list[Task]:
        pass

    def optimize_schedule(self) -> Schedule:
        pass

    def explain_plan(self) -> str:
        pass
