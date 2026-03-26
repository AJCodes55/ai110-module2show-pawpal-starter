from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes — pure data containers (Pet, Task, Owner, Constraint, UserPreferences)
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    species: str
    age: int
    energy_level: int        # 1 (low) – 10 (high)
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Assign a task directly to this pet."""
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return the number of tasks assigned to this pet."""
        return len(self.tasks)

    def get_daily_needs(self) -> list[str]:
        """Return a base list of daily care tasks for this pet."""
        needs = ["feeding", "fresh water"]
        if self.species.lower() in ("dog", "puppy"):
            needs.append("walk")
        if self.energy_level >= 7:
            needs.append("play / exercise")
        if self.special_needs:
            needs.append(f"special care: {self.special_needs}")
        return needs

    def adjust_task_priority(self, task: Task) -> None:
        """Boost priority for mandatory tasks; scale with pet energy level."""
        if task.is_mandatory:
            task.priority = min(task.priority + 2, 10)
        if self.energy_level >= 7 and task.category == "exercise":
            task.priority = min(task.priority + 1, 10)


@dataclass
class Task:
    name: str
    duration: int            # minutes
    priority: int            # 1 (low) – 10 (high)
    category: str
    is_mandatory: bool
    deadline: Optional[datetime] = None
    completed: bool = False

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def get_priority_score(self) -> int:
        """Combine base priority with urgency into a single score (higher = sooner)."""
        score = self.priority
        if self.is_mandatory:
            score += 3
        if self.deadline and self.is_urgent(datetime.now()):
            score += 5
        return min(score, 10)

    def is_urgent(self, current_time: datetime) -> bool:
        """A task is urgent if its deadline is within the next 24 hours."""
        if self.deadline is None:
            return False
        return self.deadline - current_time <= timedelta(hours=24)


@dataclass
class Constraint:
    max_time_available: int              # minutes
    preferred_times: list[str] = field(default_factory=list)   # e.g. ["morning", "evening"]
    task_limits: dict[str, int] = field(default_factory=dict)  # category -> max occurrences

    def is_task_allowed(self, task: Task) -> bool:
        """Return False if the task's category has hit its daily limit."""
        limit = self.task_limits.get(task.category)
        if limit is not None and limit <= 0:
            return False
        return True

    def can_fit(self, task: Task, remaining_time: int) -> bool:
        """Return True if the task duration fits within remaining available time."""
        return task.duration <= remaining_time


@dataclass
class UserPreferences:
    preferred_task_times: dict[str, str] = field(default_factory=dict)  # task name -> time-of-day
    disliked_tasks: list[str] = field(default_factory=list)
    routine_style: str = "flexible"      # "morning" | "evening" | "flexible"

    def adjust_priority(self, task: Task) -> None:
        """Lower priority slightly for disliked (non-mandatory) tasks."""
        if task.name in self.disliked_tasks and not task.is_mandatory:
            task.priority = max(task.priority - 1, 1)

    def filter_tasks(self, tasks: list[Task]) -> list[Task]:
        """Remove disliked, non-mandatory tasks from the list."""
        return [t for t in tasks if t.name not in self.disliked_tasks or t.is_mandatory]


@dataclass
class Owner:
    name: str
    available_time_per_day: int          # minutes
    preferred_schedule: str              # "morning" | "evening" | "flexible"
    experience_level: str                # "new" | "intermediate" | "expert"
    preferences: UserPreferences = field(default_factory=UserPreferences)
    pets: list[Pet] = field(default_factory=list)

    def set_preferences(self, preferences: UserPreferences) -> None:
        self.preferences = preferences

    def update_availability(self, time: int) -> None:
        """Update the total minutes available per day."""
        self.available_time_per_day = time

    def get_available_time(self) -> int:
        return self.available_time_per_day

    def adjust_task_priority(self, task: Task) -> None:
        """New owners get mandatory tasks boosted so nothing critical is skipped."""
        if self.experience_level == "new" and task.is_mandatory:
            task.priority = min(task.priority + 1, 10)
        self.preferences.adjust_priority(task)


# ---------------------------------------------------------------------------
# Behaviour classes — logic-heavy (Schedule, Planner, ExplanationEngine)
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(self, max_time: int = 0) -> None:
        self.tasks: list[Task] = []
        self.total_time: int = 0
        self.unused_time: int = max_time

    def add_task(self, task: Task) -> None:
        """Append a task and update time tracking."""
        self.tasks.append(task)
        self.total_time += task.duration
        self.unused_time -= task.duration

    def get_summary(self) -> str:
        if not self.tasks:
            return "No tasks scheduled."
        lines = ["Scheduled tasks:"]
        for t in self.tasks:
            urgency = " [URGENT]" if t.is_urgent(datetime.now()) else ""
            lines.append(f"  • {t.name} ({t.duration} min, priority {t.priority}){urgency}")
        lines.append(f"Total time: {self.total_time} min | Unused: {self.unused_time} min")
        return "\n".join(lines)

    def validate(self, constraints: Constraint) -> bool:
        """Return True only if the schedule fits within all constraints."""
        if self.total_time > constraints.max_time_available:
            return False
        for task in self.tasks:
            if not constraints.is_task_allowed(task):
                return False
        return True


class ExplanationEngine:
    def explain(self, schedule: Schedule) -> str:
        """Produce a human-readable explanation of why this schedule was built."""
        if not schedule.tasks:
            return "No tasks were scheduled."
        lines = ["Here is why each task was included:"]
        for task in schedule.tasks:
            lines.append(f"  • {self.justify_task(task)}")
        return "\n".join(lines)

    def justify_task(self, task: Task) -> str:
        """Return a one-line reason a task was included in the schedule."""
        reasons = []
        if task.is_mandatory:
            reasons.append("mandatory")
        if task.is_urgent(datetime.now()):
            reasons.append("deadline within 24 h")
        if task.priority >= 8:
            reasons.append("high priority")
        reason_str = ", ".join(reasons) if reasons else "fits within available time"
        return f"{task.name}: {reason_str}"


class Planner:
    def __init__(self, pet: Pet, owner: Owner, tasks: list[Task], constraints: Constraint) -> None:
        self.pet = pet
        self.owner = owner
        self.tasks = tasks
        self.constraints = constraints
        self._explanation_engine = ExplanationEngine()

    def prioritize_tasks(self) -> list[Task]:
        """Apply all priority adjustments, filter by preferences, then sort."""
        for task in self.tasks:
            self.pet.adjust_task_priority(task)
            self.owner.adjust_task_priority(task)

        filtered = self.owner.preferences.filter_tasks(self.tasks)
        return sorted(filtered, key=lambda t: t.get_priority_score(), reverse=True)

    def generate_plan(self) -> Schedule:
        """Build a schedule by greedily adding tasks in priority order."""
        schedule = Schedule(max_time=self.owner.get_available_time())
        remaining = self.owner.get_available_time()

        for task in self.prioritize_tasks():
            if (self.constraints.is_task_allowed(task)
                    and self.constraints.can_fit(task, remaining)):
                schedule.add_task(task)
                remaining -= task.duration
                # Decrement the category limit if one is set
                if task.category in self.constraints.task_limits:
                    self.constraints.task_limits[task.category] -= 1

        return schedule

    def optimize_schedule(self) -> Schedule:
        """Re-run generation after bumping mandatory tasks that were left out."""
        for task in self.tasks:
            if task.is_mandatory:
                task.priority = min(task.priority + 2, 10)
        return self.generate_plan()

    def explain_plan(self) -> str:
        schedule = self.generate_plan()
        return self._explanation_engine.explain(schedule)
