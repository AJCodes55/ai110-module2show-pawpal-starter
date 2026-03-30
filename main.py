from datetime import datetime, timedelta

from pawpal_system import (
    Constraint,
    ConflictDetector,
    Owner,
    Pet,
    Planner,
    Task,
    UserPreferences,
)

# ---------------------------------------------------------------------------
# Pets
# ---------------------------------------------------------------------------
buddy = Pet(
    name="Buddy",
    species="dog",
    age=3,
    energy_level=8,
    special_needs="",
)

luna = Pet(
    name="Luna",
    species="cat",
    age=5,
    energy_level=4,
    special_needs="arthritis – avoid high-impact play",
)

# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------
prefs = UserPreferences(
    preferred_task_times={"walk": "morning", "feeding": "morning"},
    disliked_tasks=["teeth brushing"],
    routine_style="morning",
)

owner = Owner(
    name="Alex",
    available_time_per_day=90,   # 90 minutes free today
    preferred_schedule="morning",
    experience_level="intermediate",
    preferences=prefs,
    pets=[buddy, luna],
)

# ---------------------------------------------------------------------------
# Tasks  (mix of durations, priorities, mandatory flags, and one near-deadline)
# ---------------------------------------------------------------------------
tasks = [
    Task(
        name="Morning walk",
        duration=30,
        priority=7,
        category="exercise",
        is_mandatory=True,
        recurrence="daily",          # recurring: happens every day
        pet_name="Buddy",
    ),
    Task(
        name="Feeding",
        duration=10,
        priority=9,
        category="nutrition",
        is_mandatory=True,
        recurrence="daily",
        pet_name="Buddy",
    ),
    Task(
        name="Play session",
        duration=20,
        priority=5,
        category="exercise",
        is_mandatory=False,
        recurrence="weekdays",       # recurring: weekdays only
        pet_name="Buddy",
    ),
    Task(
        name="Vet medication – Luna",
        duration=5,
        priority=8,
        category="health",
        is_mandatory=True,
        deadline=datetime.now() + timedelta(hours=6),  # urgent — due in 6 h
        pet_name="Luna",
    ),
    Task(
        name="Teeth brushing",
        duration=10,
        priority=4,
        category="grooming",
        is_mandatory=False,
        recurrence="weekends",       # recurring: weekends only
        pet_name="Buddy",
    ),
    Task(
        name="Litter box cleaning",
        duration=10,
        priority=6,
        category="hygiene",
        is_mandatory=True,
        recurrence="daily",
        pet_name="Luna",
    ),
]

# ---------------------------------------------------------------------------
# Constraints  (cap exercise at 2 sessions, stay within owner's 90 min)
# ---------------------------------------------------------------------------
constraints = Constraint(
    max_time_available=owner.available_time_per_day,
    preferred_times=["morning"],
    task_limits={"exercise": 2},
)

# ---------------------------------------------------------------------------
# Build and display today's schedule
# ---------------------------------------------------------------------------
planner = Planner(
    pet=buddy,          # primary pet driving priority adjustments
    owner=owner,
    tasks=tasks,
    constraints=constraints,
)

from pawpal_system import ExplanationEngine, Schedule

schedule = planner.generate_plan()

print("=" * 50)
print("       PawPal+ — Today's Schedule")
print("=" * 50)
print(f"Owner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print("-" * 50)
print(schedule.get_summary())

print("\n--- Why these tasks? ---")
engine = ExplanationEngine()
print(engine.explain(schedule))

print("\n--- Conflict Report ---")
detector = ConflictDetector()
print(detector.report(schedule, tasks, constraints))

# ---------------------------------------------------------------------------
# SORT DEMO — tasks manually created with times out of chronological order
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("       SORT DEMO: sort_by_time()")
print("=" * 50)

today = datetime.now()
def at(hour: int, minute: int = 0) -> datetime:
    return today.replace(hour=hour, minute=minute, second=0, microsecond=0)

# Tasks are intentionally added in scrambled time order
scrambled_tasks = [
    Task("Evening grooming",    duration=10, priority=4, category="grooming",
         is_mandatory=False, pet_name="Buddy",  scheduled_time=at(18, 30)),
    Task("Morning feeding",     duration=10, priority=9, category="nutrition",
         is_mandatory=True,  pet_name="Buddy",  scheduled_time=at(8,  0)),
    Task("Afternoon walk",      duration=30, priority=7, category="exercise",
         is_mandatory=True,  pet_name="Buddy",  scheduled_time=at(13, 0)),
    Task("Morning medication",  duration=5,  priority=8, category="health",
         is_mandatory=True,  pet_name="Luna",   scheduled_time=at(8, 30)),
    Task("Litter box cleaning", duration=10, priority=6, category="hygiene",
         is_mandatory=True,  pet_name="Luna",   scheduled_time=at(10, 0)),
    Task("Midday play",         duration=20, priority=5, category="exercise",
         is_mandatory=False, pet_name="Buddy",  scheduled_time=at(12, 0)),
]

demo_schedule = Schedule(max_time=90)
for t in scrambled_tasks:
    demo_schedule.add_task(t)

print("\nBEFORE sort_by_time()  (insertion order — scrambled):")
for t in demo_schedule.tasks:
    print(f"  {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

demo_schedule.sort_by_time()

print("\nAFTER  sort_by_time()  (chronological order):")
for t in demo_schedule.tasks:
    print(f"  {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

# ---------------------------------------------------------------------------
# FILTER DEMO — filter by pet name and by completion status
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("       FILTER DEMO")
print("=" * 50)

# Use complete_task() instead of mark_complete() so recurring tasks
# automatically queue their next occurrence in demo_schedule.upcoming.
demo_schedule.complete_task(demo_schedule.tasks[0])   # Morning feeding   (daily)
demo_schedule.complete_task(demo_schedule.tasks[1])   # Morning medication (no recurrence set)

print("\nfilter_by_pet('Buddy'):")
for t in demo_schedule.filter_by_pet("Buddy"):
    status = "done" if t.completed else "pending"
    print(f"  • [{status}] {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

print("\nfilter_by_pet('Luna'):")
for t in demo_schedule.filter_by_pet("Luna"):
    status = "done" if t.completed else "pending"
    print(f"  • [{status}] {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

print("\nfilter_by_status(completed=True)  — finished tasks:")
for t in demo_schedule.filter_by_status(completed=True):
    print(f"  • {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

print("\nfilter_by_status(completed=False)  — still pending:")
for t in demo_schedule.filter_by_status(completed=False):
    print(f"  • {t.scheduled_time.strftime('%I:%M %p')}  {t.name}")

# ---------------------------------------------------------------------------
# RECURRENCE DEMO — complete_task() queues next occurrences automatically
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("       RECURRENCE DEMO: complete_task()")
print("=" * 50)

# Build a small schedule with one task of each recurrence type
recur_tasks = [
    Task("Daily feeding",    duration=10, priority=9, category="nutrition",
         is_mandatory=True,  pet_name="Buddy",
         recurrence="daily",    scheduled_time=at(8, 0)),
    Task("Weekday walk",     duration=30, priority=7, category="exercise",
         is_mandatory=True,  pet_name="Buddy",
         recurrence="weekdays", scheduled_time=at(9, 0)),
    Task("Weekend grooming", duration=15, priority=5, category="grooming",
         is_mandatory=False, pet_name="Buddy",
         recurrence="weekends", scheduled_time=at(10, 0)),
    Task("Weekly vet check", duration=20, priority=8, category="health",
         is_mandatory=True,  pet_name="Luna",
         recurrence="weekly",   scheduled_time=at(11, 0)),
]

recur_schedule = Schedule(max_time=120)
for t in recur_tasks:
    recur_schedule.add_task(t)

print("\nInitial schedule (all pending):")
for t in recur_schedule.tasks:
    print(f"  • {t.scheduled_time.strftime('%I:%M %p')}  {t.name}  [{t.recurrence}]")

print("\nCompleting all four tasks via complete_task()...")
for t in list(recur_schedule.tasks):
    next_t = recur_schedule.complete_task(t)
    if next_t:
        print(f"  ✓ '{t.name}' done → next occurrence queued for "
              f"{next_t.scheduled_time.strftime('%A %b %d @ %I:%M %p')}")
    else:
        print(f"  ✓ '{t.name}' done → no recurrence, nothing queued")

print(f"\nUpcoming queue ({len(recur_schedule.upcoming)} task(s)):")
for t in recur_schedule.upcoming:
    print(f"  • {t.scheduled_time.strftime('%A %b %d @ %I:%M %p')}  "
          f"{t.name}  [{t.recurrence}]  completed={t.completed}")

# ---------------------------------------------------------------------------
# CONFLICT DETECTION DEMO — check_conflicts() catches overlapping windows
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("       CONFLICT DETECTION DEMO: check_conflicts()")
print("=" * 50)

# --- Scenario 1: two tasks for the SAME pet start at exactly the same time ---
print("\nScenario 1 — same pet, exact same start time:")
conflict_schedule_1 = Schedule(max_time=120)
conflict_schedule_1.add_task(Task(
    "Morning feeding", duration=10, priority=9, category="nutrition",
    is_mandatory=True, pet_name="Buddy", scheduled_time=at(8, 0),
))
conflict_schedule_1.add_task(Task(
    "Morning medication", duration=5, priority=8, category="health",
    is_mandatory=True, pet_name="Buddy", scheduled_time=at(8, 0),   # ← same time
))
conflict_schedule_1.add_task(Task(
    "Afternoon walk", duration=30, priority=7, category="exercise",
    is_mandatory=True, pet_name="Buddy", scheduled_time=at(13, 0),  # ← no conflict
))

for t in conflict_schedule_1.tasks:
    print(f"  {t.scheduled_time.strftime('%I:%M %p')}  {t.name}  ({t.pet_name})")

warnings_1 = conflict_schedule_1.check_conflicts()
print(f"\n  check_conflicts() → {len(warnings_1)} warning(s):")
for w in warnings_1:
    print(f"  {w}")

# --- Scenario 2: two tasks for DIFFERENT pets whose windows overlap ---
print("\nScenario 2 — different pets, overlapping windows:")
conflict_schedule_2 = Schedule(max_time=120)
conflict_schedule_2.add_task(Task(
    "Morning walk",    duration=30, priority=7, category="exercise",
    is_mandatory=True,  pet_name="Buddy", scheduled_time=at(8, 0),   # 08:00–08:30
))
conflict_schedule_2.add_task(Task(
    "Vet medication",  duration=10, priority=8, category="health",
    is_mandatory=True,  pet_name="Luna",  scheduled_time=at(8, 20),  # 08:20–08:30 ← overlaps
))
conflict_schedule_2.add_task(Task(
    "Litter box",      duration=10, priority=6, category="hygiene",
    is_mandatory=True,  pet_name="Luna",  scheduled_time=at(9, 0),   # 09:00–09:10 ← clean
))

for t in conflict_schedule_2.tasks:
    end = t.scheduled_time + __import__("datetime").timedelta(minutes=t.duration)
    print(f"  {t.scheduled_time.strftime('%I:%M')}–{end.strftime('%I:%M %p')}  "
          f"{t.name}  ({t.pet_name})")

warnings_2 = conflict_schedule_2.check_conflicts()
print(f"\n  check_conflicts() → {len(warnings_2)} warning(s):")
for w in warnings_2:
    print(f"  {w}")

# --- Scenario 3: a clean schedule — check_conflicts() returns nothing ---
print("\nScenario 3 — clean schedule, no conflicts:")
clean_schedule = Schedule(max_time=60)
clean_schedule.add_task(Task(
    "Feeding",    duration=10, priority=9, category="nutrition",
    is_mandatory=True, pet_name="Buddy", scheduled_time=at(8, 0),
))
clean_schedule.add_task(Task(
    "Walk",       duration=30, priority=7, category="exercise",
    is_mandatory=True, pet_name="Buddy", scheduled_time=at(8, 10),
))

warnings_3 = clean_schedule.check_conflicts()
if warnings_3:
    for w in warnings_3:
        print(f"  {w}")
else:
    print("  No conflicts detected — schedule is clean.")

print("=" * 50)
