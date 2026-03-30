import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import (
    Pet, Task, Schedule, Constraint, Owner, Planner, ConflictDetector
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_task(name="Task", duration=30, priority=5, category="general",
               mandatory=False, recurrence=None, deadline=None,
               scheduled_time=None, pet_name=""):
    return Task(
        name=name,
        duration=duration,
        priority=priority,
        category=category,
        is_mandatory=mandatory,
        recurrence=recurrence,
        deadline=deadline,
        scheduled_time=scheduled_time,
        pet_name=pet_name,
    )


def _make_planner(tasks, max_time=120, task_limits=None):
    """Return a Planner wired up with a minimal pet, owner, and constraint."""
    pet = Pet(name="Buddy", species="dog", age=3, energy_level=5)
    owner = Owner(
        name="Alex",
        available_time_per_day=max_time,
        preferred_schedule="morning",
        experience_level="intermediate",
    )
    constraint = Constraint(
        max_time_available=max_time,
        task_limits=task_limits or {},
    )
    return Planner(pet=pet, owner=owner, tasks=tasks, constraints=constraint)


# ---------------------------------------------------------------------------
# Test 1 — Task completion (existing)
# ---------------------------------------------------------------------------
def test_mark_complete_changes_status():
    task = Task(
        name="Morning walk",
        duration=30,
        priority=7,
        category="exercise",
        is_mandatory=True,
    )

    assert task.completed is False, "Task should start as incomplete"

    task.mark_complete()

    assert task.completed is True, "Task should be complete after mark_complete()"


# ---------------------------------------------------------------------------
# Test 2 — Adding a task to a Pet increases its task count (existing)
# ---------------------------------------------------------------------------
def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", age=3, energy_level=8)

    assert pet.task_count() == 0, "Pet should start with no tasks"

    pet.add_task(Task(name="Feeding", duration=10, priority=9, category="nutrition", is_mandatory=True))
    assert pet.task_count() == 1, "Pet should have 1 task after first addition"

    pet.add_task(Task(name="Play session", duration=20, priority=5, category="exercise", is_mandatory=False))
    assert pet.task_count() == 2, "Pet should have 2 tasks after second addition"


# ---------------------------------------------------------------------------
# SORTING
# ---------------------------------------------------------------------------

def test_sort_unscheduled_tasks_go_to_end():
    """Tasks missing scheduled_time should sort after all timed tasks."""
    t_timed = _make_task("Timed", scheduled_time=datetime(2026, 3, 29, 9, 0))
    t_untimed = _make_task("Untimed")  # scheduled_time=None

    schedule = Schedule()
    schedule.add_task(t_untimed)
    schedule.add_task(t_timed)
    schedule.sort_by_time()

    assert schedule.tasks[0].name == "Timed", "Timed task should come first"
    assert schedule.tasks[1].name == "Untimed", "Unscheduled task should sort to the end"


def test_sort_all_unscheduled_no_crash():
    """sort_by_time() with no scheduled_times should not raise and preserve count."""
    schedule = Schedule()
    schedule.add_task(_make_task("A"))
    schedule.add_task(_make_task("B"))
    schedule.add_task(_make_task("C"))

    schedule.sort_by_time()  # must not raise

    assert len(schedule.tasks) == 3, "All tasks should still be present after sorting"


def test_sort_chronological_order():
    """Tasks with different scheduled times should come out in ascending order."""
    base = datetime(2026, 3, 29, 8, 0)
    t1 = _make_task("First",  scheduled_time=base)
    t2 = _make_task("Second", scheduled_time=base + timedelta(hours=1))
    t3 = _make_task("Third",  scheduled_time=base + timedelta(hours=2))

    schedule = Schedule()
    # Add in reverse order
    for task in [t3, t1, t2]:
        schedule.add_task(task)

    schedule.sort_by_time()

    assert [t.name for t in schedule.tasks] == ["First", "Second", "Third"], \
        "Tasks should be sorted earliest-first"


# ---------------------------------------------------------------------------
# RECURRING TASKS — next_occurrence()
# ---------------------------------------------------------------------------

def test_weekdays_recurrence_skips_weekend_friday_to_monday():
    """A weekday task scheduled on Friday should next occur on Monday."""
    friday = datetime(2026, 3, 27, 8, 0)   # March 27, 2026 is a Friday
    assert friday.weekday() == 4, "Sanity check: date must be a Friday"

    task = _make_task("Daily med", recurrence="weekdays", scheduled_time=friday)
    nxt = task.next_occurrence()

    assert nxt.scheduled_time.weekday() == 0, \
        f"Next weekday after Friday should be Monday (0), got {nxt.scheduled_time.weekday()}"
    assert nxt.scheduled_time == datetime(2026, 3, 30, 8, 0), \
        "Next occurrence should be Monday March 30"


def test_weekends_recurrence_skips_weekdays_sunday_to_saturday():
    """A weekend task scheduled on Sunday should next occur on the following Saturday."""
    sunday = datetime(2026, 3, 29, 10, 0)   # March 29, 2026 is a Sunday
    assert sunday.weekday() == 6, "Sanity check: date must be a Sunday"

    task = _make_task("Weekend play", recurrence="weekends", scheduled_time=sunday)
    nxt = task.next_occurrence()

    assert nxt.scheduled_time.weekday() == 5, \
        f"Next weekend day after Sunday should be Saturday (5), got {nxt.scheduled_time.weekday()}"
    assert nxt.scheduled_time == datetime(2026, 4, 4, 10, 0), \
        "Next occurrence should be Saturday April 4"


def test_next_occurrence_daily_advances_one_day():
    """Daily recurrence should advance exactly 24 hours."""
    base = datetime(2026, 3, 29, 9, 0)
    task = _make_task("Feeding", recurrence="daily", scheduled_time=base)
    nxt = task.next_occurrence()

    assert nxt.scheduled_time == base + timedelta(days=1), \
        "Daily next occurrence should be exactly 1 day later"
    assert nxt.completed is False, "Next occurrence should start incomplete"


def test_next_occurrence_weekly_advances_seven_days():
    """Weekly recurrence should advance exactly 7 days."""
    base = datetime(2026, 3, 29, 9, 0)
    task = _make_task("Vet checkup", recurrence="weekly", scheduled_time=base)
    nxt = task.next_occurrence()

    assert nxt.scheduled_time == base + timedelta(weeks=1), \
        "Weekly next occurrence should be exactly 7 days later"


def test_next_occurrence_deadline_offset_preserved():
    """The gap between scheduled_time and deadline should be the same in the next occurrence."""
    base = datetime(2026, 3, 29, 8, 0)
    deadline = base + timedelta(hours=2)   # deadline is 2 hours after start
    task = _make_task("Medication", recurrence="daily", scheduled_time=base, deadline=deadline)

    nxt = task.next_occurrence()

    gap = nxt.deadline - nxt.scheduled_time
    assert gap == timedelta(hours=2), \
        f"Deadline offset should stay 2 hours after scheduled_time, got {gap}"


def test_next_occurrence_no_recurrence_raises():
    """Calling next_occurrence() on a non-recurring task should raise ValueError."""
    task = _make_task("One-off vet visit", recurrence=None)
    raised = False
    try:
        task.next_occurrence()
    except ValueError:
        raised = True
    assert raised, "next_occurrence() should raise ValueError for non-recurring tasks"


def test_complete_task_nonrecurring_returns_none_and_no_upcoming():
    """Completing a non-recurring task should return None and not populate upcoming."""
    schedule = Schedule()
    task = _make_task("Bath", recurrence=None)
    schedule.add_task(task)

    result = schedule.complete_task(task)

    assert result is None, "complete_task() should return None for non-recurring tasks"
    assert len(schedule.upcoming) == 0, "upcoming should stay empty for non-recurring tasks"


def test_complete_task_recurring_queues_next_occurrence():
    """Completing a recurring task should append the next occurrence to upcoming."""
    schedule = Schedule()
    base = datetime(2026, 3, 29, 8, 0)
    task = _make_task("Daily walk", recurrence="daily", scheduled_time=base)
    schedule.add_task(task)

    result = schedule.complete_task(task)

    assert result is not None, "complete_task() should return the next Task for recurring tasks"
    assert len(schedule.upcoming) == 1, "upcoming should have exactly one queued occurrence"
    assert schedule.upcoming[0].completed is False, "Queued next occurrence should be incomplete"


# ---------------------------------------------------------------------------
# RECURRING TASKS — is_due_today()
# ---------------------------------------------------------------------------

def test_is_due_today_no_recurrence_always_true():
    """Tasks without recurrence should always be due."""
    task = _make_task(recurrence=None)
    for weekday_offset in range(7):
        ref = datetime(2026, 3, 23) + timedelta(days=weekday_offset)
        assert task.is_due_today(ref), f"Non-recurring task should be due on any day"


def test_is_due_today_daily_always_true():
    task = _make_task(recurrence="daily")
    for weekday_offset in range(7):
        ref = datetime(2026, 3, 23) + timedelta(days=weekday_offset)
        assert task.is_due_today(ref), "Daily task should be due every day"


def test_is_due_today_weekdays_not_due_on_weekend():
    task = _make_task(recurrence="weekdays")
    saturday = datetime(2026, 3, 28)   # Saturday
    sunday   = datetime(2026, 3, 29)   # Sunday
    assert saturday.weekday() == 5 and sunday.weekday() == 6, "Sanity check"

    assert not task.is_due_today(saturday), "Weekday task should NOT be due on Saturday"
    assert not task.is_due_today(sunday),   "Weekday task should NOT be due on Sunday"


def test_is_due_today_weekdays_due_on_weekday():
    task = _make_task(recurrence="weekdays")
    monday = datetime(2026, 3, 23)
    friday = datetime(2026, 3, 27)
    assert task.is_due_today(monday), "Weekday task should be due on Monday"
    assert task.is_due_today(friday), "Weekday task should be due on Friday"


def test_is_due_today_weekends_not_due_on_weekday():
    task = _make_task(recurrence="weekends")
    monday = datetime(2026, 3, 23)
    friday = datetime(2026, 3, 27)
    assert not task.is_due_today(monday), "Weekend task should NOT be due on Monday"
    assert not task.is_due_today(friday), "Weekend task should NOT be due on Friday"


def test_is_due_today_weekly_no_deadline_falls_back_to_monday():
    """Weekly task with no deadline defaults to Monday as the target weekday."""
    task = _make_task(recurrence="weekly", deadline=None)
    monday = datetime(2026, 3, 23)   # weekday 0
    tuesday = datetime(2026, 3, 24)  # weekday 1

    assert task.is_due_today(monday),    "Weekly task with no deadline should be due on Monday"
    assert not task.is_due_today(tuesday), "Weekly task with no deadline should NOT be due on Tuesday"


def test_is_due_today_weekly_matches_deadline_weekday():
    """Weekly task should be due on the same weekday as its deadline."""
    wednesday_deadline = datetime(2026, 4, 1, 9, 0)   # April 1, 2026 is a Wednesday
    assert wednesday_deadline.weekday() == 2, "Sanity check: must be Wednesday"

    task = _make_task(recurrence="weekly", deadline=wednesday_deadline)

    wednesday_ref = datetime(2026, 3, 25)   # another Wednesday
    thursday_ref  = datetime(2026, 3, 26)   # Thursday
    assert task.is_due_today(wednesday_ref), "Weekly task should be due on the correct weekday"
    assert not task.is_due_today(thursday_ref), "Weekly task should NOT be due on a different weekday"


# ---------------------------------------------------------------------------
# CONFLICT DETECTION
# ---------------------------------------------------------------------------

def test_no_conflict_single_task():
    """A schedule with one task should never report a conflict."""
    schedule = Schedule()
    schedule.add_task(_make_task("Solo task", scheduled_time=datetime(2026, 3, 29, 8, 0)))

    assert schedule.check_conflicts() == [], "Single task should never produce a conflict"


def test_no_conflict_back_to_back_tasks():
    """Tasks that end exactly when the next begins should NOT be flagged as conflicting."""
    base = datetime(2026, 3, 29, 8, 0)
    t1 = _make_task("Walk",    duration=30, scheduled_time=base)
    t2 = _make_task("Feeding", duration=20, scheduled_time=base + timedelta(minutes=30))

    schedule = Schedule()
    schedule.add_task(t1)
    schedule.add_task(t2)

    assert schedule.check_conflicts() == [], \
        "Back-to-back tasks (no overlap) should not be reported as a conflict"


def test_conflict_detected_for_overlapping_tasks():
    """Tasks with overlapping windows should produce a warning."""
    base = datetime(2026, 3, 29, 8, 0)
    t1 = _make_task("Walk",    duration=30, scheduled_time=base)               # 08:00–08:30
    t2 = _make_task("Feeding", duration=30, scheduled_time=base + timedelta(minutes=15))  # 08:15–08:45

    schedule = Schedule()
    schedule.add_task(t1)
    schedule.add_task(t2)

    conflicts = schedule.check_conflicts()
    assert len(conflicts) == 1, "One overlapping pair should produce exactly one warning"
    assert "Walk" in conflicts[0] and "Feeding" in conflicts[0], \
        "Warning should name both conflicting tasks"


def test_conflict_same_start_time_reported():
    """Two tasks with the identical start time should be reported."""
    base = datetime(2026, 3, 29, 8, 0)
    t1 = _make_task("Medication", duration=10, scheduled_time=base, pet_name="Buddy")
    t2 = _make_task("Feeding",    duration=20, scheduled_time=base, pet_name="Buddy")

    schedule = Schedule()
    schedule.add_task(t1)
    schedule.add_task(t2)

    conflicts = schedule.check_conflicts()
    assert len(conflicts) == 1, "Exact same start time should produce one conflict"
    assert "same time" in conflicts[0], "Warning should mention 'same time'"


def test_no_conflict_empty_schedule():
    """check_conflicts() on an empty schedule should return an empty list."""
    schedule = Schedule()
    assert schedule.check_conflicts() == [], "Empty schedule should have no conflicts"


def test_no_conflict_tasks_without_scheduled_time():
    """Tasks with no scheduled_time should be ignored by conflict detection."""
    t1 = _make_task("Unscheduled A")  # scheduled_time=None
    t2 = _make_task("Unscheduled B")

    schedule = Schedule()
    schedule.add_task(t1)
    schedule.add_task(t2)

    assert schedule.check_conflicts() == [], \
        "Tasks without scheduled_time should not be considered for conflicts"


def test_conflict_detector_find_excluded_mandatory():
    """Mandatory tasks absent from the schedule should be surfaced by ConflictDetector."""
    mandatory = _make_task("Critical med", mandatory=True)
    optional  = _make_task("Play time",    mandatory=False)

    schedule = Schedule()  # neither task is in the schedule

    detector = ConflictDetector()
    excluded = detector.find_excluded_mandatory([mandatory, optional], schedule)

    assert mandatory in excluded, "Mandatory task not in schedule should appear in excluded list"
    assert optional not in excluded, "Non-mandatory task should not appear in excluded list"


def test_conflict_detector_overbooked_category():
    """ConflictDetector should flag categories that exceed their configured limit."""
    tasks = [
        _make_task("Walk 1", category="exercise"),
        _make_task("Walk 2", category="exercise"),
        _make_task("Walk 3", category="exercise"),
    ]
    constraints = Constraint(max_time_available=120, task_limits={"exercise": 1})
    detector = ConflictDetector()
    overbooked = detector.find_overbooked_categories(tasks, constraints)

    assert "exercise" in overbooked, "exercise category should be flagged as overbooked"
    assert overbooked["exercise"] == 3, "Should report the actual count (3)"


# ---------------------------------------------------------------------------
# SCHEDULING / CONSTRAINTS — Planner
# ---------------------------------------------------------------------------

def test_empty_task_list_produces_empty_schedule():
    """Generating a plan with no tasks should return an empty schedule without error."""
    planner = _make_planner(tasks=[])
    schedule = planner.generate_plan()

    assert len(schedule.tasks) == 0, "Empty task list should produce an empty schedule"
    assert schedule.total_time == 0, "Total time should be 0 for an empty schedule"


def test_zero_available_time_schedules_nothing():
    """When the owner has 0 minutes available, no tasks should be scheduled."""
    tasks = [_make_task("Walk", duration=1, mandatory=True)]
    planner = _make_planner(tasks=tasks, max_time=0)
    schedule = planner.generate_plan()

    assert len(schedule.tasks) == 0, "No tasks should fit when 0 time is available"


def test_category_limit_zero_blocks_all_tasks_in_that_category():
    """A category limit of 0 should prevent any task in that category from being scheduled."""
    tasks = [
        _make_task("Run",  category="exercise", duration=20),
        _make_task("Walk", category="exercise", duration=20),
    ]
    planner = _make_planner(tasks=tasks, max_time=120, task_limits={"exercise": 0})
    schedule = planner.generate_plan()

    scheduled_categories = [t.category for t in schedule.tasks]
    assert "exercise" not in scheduled_categories, \
        "No exercise tasks should be scheduled when category limit is 0"


def test_tasks_scheduled_within_available_time():
    """The planner should not schedule more minutes than the owner has available."""
    tasks = [
        _make_task("Task A", duration=40),
        _make_task("Task B", duration=40),
        _make_task("Task C", duration=40),   # this one should not fit (120 min limit)
    ]
    planner = _make_planner(tasks=tasks, max_time=80)
    schedule = planner.generate_plan()

    assert schedule.total_time <= 80, \
        f"Scheduled time ({schedule.total_time} min) must not exceed 80 min"


def test_mandatory_tasks_get_priority_boost():
    """A mandatory mid-priority task should be scheduled over a non-mandatory higher-priority one
    when only one fits, because mandatory tasks receive a pet (+2) and score (+3) boost.
    mandatory: base 5 → pet +2 → 7, score +3 → 10
    optional:  base 7 → no boost, score → 7   (mandatory wins)
    """
    mandatory = _make_task("Critical med", duration=60, priority=5, mandatory=True)
    optional   = _make_task("Fun play",    duration=60, priority=7, mandatory=False)

    planner = _make_planner(tasks=[mandatory, optional], max_time=60)
    schedule = planner.generate_plan()

    scheduled_names = [t.name for t in schedule.tasks]
    assert "Critical med" in scheduled_names, \
        "Mandatory task should be scheduled over a non-mandatory one when only one fits"


# ---------------------------------------------------------------------------
# PRIORITY SCORING
# ---------------------------------------------------------------------------

def test_is_urgent_no_deadline_returns_false():
    """is_urgent() with deadline=None should return False without raising."""
    task = _make_task(deadline=None)
    result = task.is_urgent(datetime.now())
    assert result is False, "Task with no deadline should never be urgent"


def test_is_urgent_deadline_within_24h_returns_true():
    task = _make_task(deadline=datetime.now() + timedelta(hours=12))
    assert task.is_urgent(datetime.now()), "Task with deadline <24h away should be urgent"


def test_is_urgent_deadline_beyond_24h_returns_false():
    task = _make_task(deadline=datetime.now() + timedelta(hours=48))
    assert not task.is_urgent(datetime.now()), "Task with deadline >24h away should not be urgent"


def test_priority_score_capped_at_10():
    """Urgent + mandatory stacking should not push the score above 10."""
    task = _make_task(
        priority=9,
        mandatory=True,
        deadline=datetime.now() + timedelta(hours=1),   # urgent
    )
    score = task.get_priority_score()
    assert score <= 10, f"Priority score must be capped at 10, got {score}"


def test_priority_score_non_mandatory_no_urgency():
    """A plain non-mandatory, non-urgent task should equal its base priority."""
    task = _make_task(priority=6, mandatory=False, deadline=None)
    assert task.get_priority_score() == 6, \
        "Score for plain task should equal its base priority"


def test_priority_score_mandatory_adds_three():
    """Mandatory flag should add 3 to the base priority (up to the cap)."""
    task = _make_task(priority=4, mandatory=True, deadline=None)
    assert task.get_priority_score() == 7, \
        "Mandatory task should have base + 3 = 7"


# ---------------------------------------------------------------------------
# Run directly via `python tests/test_pawpal.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        test_mark_complete_changes_status,
        test_add_task_increases_pet_task_count,
        # Sorting
        test_sort_unscheduled_tasks_go_to_end,
        test_sort_all_unscheduled_no_crash,
        test_sort_chronological_order,
        # next_occurrence
        test_weekdays_recurrence_skips_weekend_friday_to_monday,
        test_weekends_recurrence_skips_weekdays_sunday_to_saturday,
        test_next_occurrence_daily_advances_one_day,
        test_next_occurrence_weekly_advances_seven_days,
        test_next_occurrence_deadline_offset_preserved,
        test_next_occurrence_no_recurrence_raises,
        test_complete_task_nonrecurring_returns_none_and_no_upcoming,
        test_complete_task_recurring_queues_next_occurrence,
        # is_due_today
        test_is_due_today_no_recurrence_always_true,
        test_is_due_today_daily_always_true,
        test_is_due_today_weekdays_not_due_on_weekend,
        test_is_due_today_weekdays_due_on_weekday,
        test_is_due_today_weekends_not_due_on_weekday,
        test_is_due_today_weekly_no_deadline_falls_back_to_monday,
        test_is_due_today_weekly_matches_deadline_weekday,
        # Conflict detection
        test_no_conflict_single_task,
        test_no_conflict_back_to_back_tasks,
        test_conflict_detected_for_overlapping_tasks,
        test_conflict_same_start_time_reported,
        test_no_conflict_empty_schedule,
        test_no_conflict_tasks_without_scheduled_time,
        test_conflict_detector_find_excluded_mandatory,
        test_conflict_detector_overbooked_category,
        # Scheduling / constraints
        test_empty_task_list_produces_empty_schedule,
        test_zero_available_time_schedules_nothing,
        test_category_limit_zero_blocks_all_tasks_in_that_category,
        test_tasks_scheduled_within_available_time,
        test_mandatory_tasks_get_priority_boost,
        # Priority scoring
        test_is_urgent_no_deadline_returns_false,
        test_is_urgent_deadline_within_24h_returns_true,
        test_is_urgent_deadline_beyond_24h_returns_false,
        test_priority_score_capped_at_10,
        test_priority_score_non_mandatory_no_urgency,
        test_priority_score_mandatory_adds_three,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            test_fn()
            print(f"PASS  {test_fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {test_fn.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {test_fn.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed out of {len(tests)} tests")
