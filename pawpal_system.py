from __future__ import annotations
from dataclasses import dataclass, field, replace
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
    scheduled_time: Optional[datetime] = None   # assigned start time in the daily schedule
    recurrence: Optional[str] = None            # "daily" | "weekdays" | "weekends" | "weekly"
    pet_name: str = ""                          # which pet this task belongs to

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

    def next_occurrence(self) -> "Task":
        """Return a new Task instance scheduled for the next recurrence.

        The next scheduled_time is computed from the current scheduled_time
        (or now if not set) by advancing according to the recurrence rule:
          - daily    → +1 day
          - weekly   → +7 days
          - weekdays → +1 day, skipping Saturday and Sunday
          - weekends → +1 day, skipping Monday through Friday

        The returned task is a copy with completed=False and an updated
        scheduled_time. If the original had a deadline, it is shifted by
        the same interval so urgency tracking stays accurate.
        """
        if self.recurrence is None:
            raise ValueError(f"'{self.name}' is not a recurring task.")

        base = self.scheduled_time or datetime.now()

        if self.recurrence == "daily":
            next_time = base + timedelta(days=1)
        elif self.recurrence == "weekly":
            next_time = base + timedelta(weeks=1)
        elif self.recurrence == "weekdays":
            next_time = base + timedelta(days=1)
            while next_time.weekday() >= 5:          # skip Sat (5) and Sun (6)
                next_time += timedelta(days=1)
        elif self.recurrence == "weekends":
            next_time = base + timedelta(days=1)
            while next_time.weekday() < 5:           # skip Mon (0) – Fri (4)
                next_time += timedelta(days=1)
        else:
            next_time = base + timedelta(days=1)

        interval = next_time - base
        next_deadline = self.deadline + interval if self.deadline else None

        return replace(
            self,
            completed=False,
            scheduled_time=next_time,
            deadline=next_deadline,
        )

    def is_due_today(self, reference_date: Optional[datetime] = None) -> bool:
        """Return True if this task should run today based on its recurrence rule."""
        if self.recurrence is None:
            return True
        weekday = (reference_date or datetime.now()).weekday()  # 0=Mon … 6=Sun
        if self.recurrence == "daily":
            return True
        if self.recurrence == "weekdays":
            return weekday < 5
        if self.recurrence == "weekends":
            return weekday >= 5
        if self.recurrence == "weekly":
            # Due on same weekday as deadline; fall back to Monday if no deadline
            target = self.deadline.weekday() if self.deadline else 0
            return weekday == target
        return True


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


# Start hour for each schedule preference (24-h clock)
_SCHEDULE_START_HOUR: dict[str, int] = {
    "morning": 8,
    "evening": 18,
    "flexible": 9,
}


# ---------------------------------------------------------------------------
# Behaviour classes — logic-heavy (Schedule, Planner, ExplanationEngine)
# ---------------------------------------------------------------------------

class Schedule:
    def __init__(self, max_time: int = 0) -> None:
        self.tasks: list[Task] = []
        self.total_time: int = 0
        self.unused_time: int = max_time
        self.upcoming: list[Task] = []   # next occurrences queued by complete_task()

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
            time_str = f" @ {t.scheduled_time.strftime('%I:%M %p')}" if t.scheduled_time else ""
            recur_str = f" [{t.recurrence}]" if t.recurrence else ""
            lines.append(f"  • {t.name}{time_str} ({t.duration} min, priority {t.priority}){recur_str}{urgency}")
        lines.append(f"Total time: {self.total_time} min | Unused: {self.unused_time} min")
        return "\n".join(lines)

    def sort_by_time(self) -> None:
        """Sort scheduled tasks by assigned start time (earliest first)."""
        self.tasks.sort(key=lambda t: (t.scheduled_time or datetime.max))

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only tasks belonging to the named pet (case-insensitive)."""
        return [t for t in self.tasks if t.pet_name.lower() == pet_name.lower()]

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks matching the given completion status."""
        return [t for t in self.tasks if t.completed == completed]

    def check_conflicts(self) -> list[str]:
        """Scan all scheduled tasks for time-window conflicts.

        Compares every pair of tasks that have a scheduled_time assigned.
        For each overlapping pair it builds a plain warning string that
        describes what type of conflict occurred and which pets are involved.

        Returns a list of warning strings — empty means no conflicts.
        Never raises an exception; safe to call at any point.
        """
        warnings: list[str] = []
        timed = [t for t in self.tasks if t.scheduled_time is not None]

        for i, a in enumerate(timed):
            a_end = a.scheduled_time + timedelta(minutes=a.duration)  # type: ignore[operator]
            for b in timed[i + 1:]:
                b_end = b.scheduled_time + timedelta(minutes=b.duration)  # type: ignore[operator]

                # Overlap condition: the two half-open windows [start, end) intersect
                if not (a.scheduled_time < b_end and b.scheduled_time < a_end):  # type: ignore[operator]
                    continue

                # --- describe which pets are involved ---
                if a.pet_name and b.pet_name:
                    if a.pet_name == b.pet_name:
                        pet_note = f" [both: {a.pet_name}]"
                    else:
                        pet_note = f" [{a.pet_name} & {b.pet_name}]"
                else:
                    pet_note = ""

                # --- describe the conflict type ---
                if a.scheduled_time == b.scheduled_time:
                    time_note = (
                        f"start at the same time "
                        f"({a.scheduled_time.strftime('%I:%M %p')})"  # type: ignore[union-attr]
                    )
                else:
                    a_win = (
                        f"{a.scheduled_time.strftime('%I:%M')}"  # type: ignore[union-attr]
                        f"–{a_end.strftime('%I:%M %p')}"
                    )
                    b_win = (
                        f"{b.scheduled_time.strftime('%I:%M')}"  # type: ignore[union-attr]
                        f"–{b_end.strftime('%I:%M %p')}"
                    )
                    time_note = f"overlap ({a_win} vs {b_win})"

                warnings.append(
                    f"WARNING: '{a.name}' and '{b.name}'{pet_note} {time_note}"
                )

        return warnings

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and, if it recurs, queue the next occurrence.

        The next occurrence is stored in self.upcoming — it is NOT added to
        today's schedule so time totals stay accurate. Returns the new Task
        if one was created, otherwise None.
        """
        task.mark_complete()
        if task.recurrence is not None:
            next_task = task.next_occurrence()
            self.upcoming.append(next_task)
            return next_task
        return None

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


class ConflictDetector:
    """Identifies scheduling problems before or after a plan is generated."""

    def find_time_conflicts(self, schedule: Schedule) -> list[tuple[Task, Task]]:
        """Return pairs of tasks whose scheduled time windows overlap."""
        conflicts: list[tuple[Task, Task]] = []
        timed = [t for t in schedule.tasks if t.scheduled_time is not None]
        for i, a in enumerate(timed):
            a_end = a.scheduled_time + timedelta(minutes=a.duration)  # type: ignore[operator]
            for b in timed[i + 1:]:
                b_end = b.scheduled_time + timedelta(minutes=b.duration)  # type: ignore[operator]
                if a.scheduled_time < b_end and b.scheduled_time < a_end:  # type: ignore[operator]
                    conflicts.append((a, b))
        return conflicts

    def find_excluded_mandatory(self, all_tasks: list[Task], schedule: Schedule) -> list[Task]:
        """Return mandatory tasks that did not make it into the schedule."""
        scheduled_names = {t.name for t in schedule.tasks}
        return [t for t in all_tasks if t.is_mandatory and t.name not in scheduled_names]

    def find_overbooked_categories(
        self, tasks: list[Task], constraints: Constraint
    ) -> dict[str, int]:
        """Return categories where the task count exceeds the configured limit."""
        from collections import Counter
        counts: Counter[str] = Counter(t.category for t in tasks)
        return {
            cat: count
            for cat, count in counts.items()
            if cat in constraints.task_limits and count > constraints.task_limits[cat]
        }

    def report(
        self,
        schedule: Schedule,
        all_tasks: list[Task],
        constraints: Constraint,
    ) -> str:
        """Return a human-readable summary of all detected conflicts."""
        lines: list[str] = []

        for a, b in self.find_time_conflicts(schedule):
            lines.append(
                f"  • Time overlap: '{a.name}' and '{b.name}' share scheduled time"
            )

        for t in self.find_excluded_mandatory(all_tasks, schedule):
            lines.append(f"  • Mandatory task excluded (no time): '{t.name}' ({t.duration} min)")

        for cat, count in self.find_overbooked_categories(all_tasks, constraints).items():
            limit = constraints.task_limits[cat]
            lines.append(f"  • Category '{cat}' has {count} tasks but limit is {limit}")

        return "\n".join(lines) if lines else "No conflicts detected."


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

    def _schedule_start_time(self) -> datetime:
        """Return today's start datetime based on the owner's preferred schedule."""
        hour = _SCHEDULE_START_HOUR.get(self.owner.preferred_schedule, 9)
        return datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)

    def generate_plan(self) -> Schedule:
        """Build a schedule by greedily adding tasks in priority order.

        Only includes tasks that are due today (respects recurrence rules).
        Each scheduled task receives an assigned start time so the day can
        be sorted chronologically and checked for conflicts.
        """
        schedule = Schedule(max_time=self.owner.get_available_time())
        remaining = self.owner.get_available_time()
        current_time = self._schedule_start_time()
        today = datetime.now()
        # Use a local copy so the original constraints stay unmodified
        remaining_limits: dict[str, int] = dict(self.constraints.task_limits)

        for task in self.prioritize_tasks():
            if not task.is_due_today(today):
                continue
            limit = remaining_limits.get(task.category)
            allowed = limit is None or limit > 0
            if allowed and self.constraints.can_fit(task, remaining):
                task.scheduled_time = current_time
                schedule.add_task(task)
                remaining -= task.duration
                current_time += timedelta(minutes=task.duration)
                if task.category in remaining_limits:
                    remaining_limits[task.category] -= 1

        schedule.sort_by_time()
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
