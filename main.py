from datetime import datetime, timedelta

from pawpal_system import (
    Constraint,
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
    ),
    Task(
        name="Feeding",
        duration=10,
        priority=9,
        category="nutrition",
        is_mandatory=True,
    ),
    Task(
        name="Play session",
        duration=20,
        priority=5,
        category="exercise",
        is_mandatory=False,
    ),
    Task(
        name="Vet medication – Luna",
        duration=5,
        priority=8,
        category="health",
        is_mandatory=True,
        deadline=datetime.now() + timedelta(hours=6),  # urgent — due in 6 h
    ),
    Task(
        name="Teeth brushing",
        duration=10,
        priority=4,
        category="grooming",
        is_mandatory=False,
    ),
    Task(
        name="Litter box cleaning",
        duration=10,
        priority=6,
        category="hygiene",
        is_mandatory=True,
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

schedule = planner.generate_plan()

print("=" * 50)
print("       PawPal+ — Today's Schedule")
print("=" * 50)
print(f"Owner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print("-" * 50)
print(schedule.get_summary())
print("-" * 50)
print("\n--- Why these tasks? ---")
from pawpal_system import ExplanationEngine
engine = ExplanationEngine()
print(engine.explain(schedule))
print("=" * 50)
