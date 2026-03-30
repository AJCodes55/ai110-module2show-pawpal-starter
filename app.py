from datetime import datetime

import streamlit as st
from pawpal_system import (
    Constraint,
    ConflictDetector,
    Owner,
    Pet,
    Planner,
    Schedule,
    Task,
    UserPreferences,
)

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation — runs every re-run, creates objects only once
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state["owner"] = None

if "tasks" not in st.session_state:
    st.session_state["tasks"] = []          # list[Task]

# ---------------------------------------------------------------------------
# Owner + Pet setup
# ---------------------------------------------------------------------------
st.subheader("Owner & Pet Setup")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_time = st.number_input("Available time today (minutes)", min_value=10, max_value=480, value=90)
    experience = st.selectbox("Experience level", ["new", "intermediate", "expert"], index=1)
    schedule_pref = st.selectbox("Preferred schedule", ["morning", "evening", "flexible"])

with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=2)
    energy_level = st.slider("Energy level", min_value=1, max_value=10, value=6)
    special_needs = st.text_input("Special needs (optional)", value="")

if st.button("Save Owner & Pet"):
    pet = Pet(
        name=pet_name,
        species=species,
        age=int(age),
        energy_level=int(energy_level),
        special_needs=special_needs,
    )
    owner = Owner(
        name=owner_name,
        available_time_per_day=int(available_time),
        preferred_schedule=schedule_pref,
        experience_level=experience,
        preferences=UserPreferences(),
        pets=[pet],
    )
    st.session_state["owner"] = owner
    st.success(f"Saved! Owner: {owner.name} | Pet: {pet.name} ({pet.species})")

st.divider()

# ---------------------------------------------------------------------------
# Add Tasks
# ---------------------------------------------------------------------------
st.subheader("Add Tasks")

PRIORITY_MAP = {"low": 3, "medium": 6, "high": 9}

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
    category = st.selectbox("Category", ["exercise", "nutrition", "health", "grooming", "hygiene"])
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    is_mandatory = st.checkbox("Mandatory?", value=True)
with col3:
    priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    recurrence_label = st.selectbox("Recurrence", ["none", "daily", "weekdays", "weekends", "weekly"])

if st.button("Add Task"):
    owner_now = st.session_state["owner"]
    pet_name_for_task = owner_now.pets[0].name if owner_now else ""
    task = Task(
        name=task_title,
        duration=int(duration),
        priority=PRIORITY_MAP[priority_label],
        category=category,
        is_mandatory=is_mandatory,
        recurrence=None if recurrence_label == "none" else recurrence_label,
        pet_name=pet_name_for_task,
    )
    st.session_state["tasks"].append(task)

    if owner_now is not None:
        pet = owner_now.pets[0]
        pet.add_task(task)
        st.success(f'Added "{task.name}" and assigned it to {pet.name} (now has {pet.task_count()} task(s))')
    else:
        st.success(f'Added "{task.name}" to task list')


def _priority_badge(priority: int) -> str:
    if priority >= 8:
        return "High"
    if priority >= 5:
        return "Medium"
    return "Low"


def _task_rows(tasks: list[Task]) -> list[dict]:
    return [
        {
            "Task": t.name,
            "Duration (min)": t.duration,
            "Priority": _priority_badge(t.priority),
            "Score": t.get_priority_score(),
            "Category": t.category,
            "Mandatory": "Yes" if t.is_mandatory else "No",
            "Recurring": t.recurrence if t.recurrence else "—",
            "Pet": t.pet_name or "—",
            "Done": "Yes" if t.completed else "No",
        }
        for t in tasks
    ]


if st.session_state["tasks"]:
    # Build a Schedule object so we can use its sorting and filtering methods
    task_schedule = Schedule()
    for t in st.session_state["tasks"]:
        task_schedule.add_task(t)

    # Sort by priority score (highest first) for the overview table
    sorted_by_score = sorted(task_schedule.tasks, key=lambda t: t.get_priority_score(), reverse=True)

    st.write("Current tasks (sorted by priority score):")
    st.table(_task_rows(sorted_by_score))

    with st.expander("Filter tasks"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_pet = st.text_input("Filter by pet name (leave blank for all)")
        with col_f2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

        # Use Schedule's filter_by_pet and filter_by_status methods
        if filter_pet.strip():
            filtered = task_schedule.filter_by_pet(filter_pet.strip())
        else:
            filtered = list(task_schedule.tasks)

        if filter_status == "Pending":
            # Create a temp schedule from the already-pet-filtered list to call filter_by_status
            tmp = Schedule()
            for t in filtered:
                tmp.add_task(t)
            filtered = tmp.filter_by_status(completed=False)
        elif filter_status == "Completed":
            tmp = Schedule()
            for t in filtered:
                tmp.add_task(t)
            filtered = tmp.filter_by_status(completed=True)

        if filtered:
            st.table(_task_rows(filtered))
        else:
            st.info("No tasks match the current filter.")

    # Highlight recurring tasks
    recurring = [t for t in task_schedule.tasks if t.recurrence]
    if recurring:
        with st.expander(f"Recurring tasks ({len(recurring)})"):
            st.table([
                {
                    "Task": t.name,
                    "Recurrence": t.recurrence,
                    "Category": t.category,
                    "Duration (min)": t.duration,
                    "Pet": t.pet_name or "—",
                }
                for t in recurring
            ])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Generate Schedule
# ---------------------------------------------------------------------------
st.subheader("Build Schedule")

if st.button("Generate Schedule"):
    owner = st.session_state["owner"]

    if owner is None:
        st.error("Please save an Owner & Pet first.")
    elif not st.session_state["tasks"]:
        st.error("Please add at least one task first.")
    else:
        constraints = Constraint(
            max_time_available=owner.available_time_per_day,
            preferred_times=[owner.preferred_schedule],
        )

        planner = Planner(
            pet=owner.pets[0],
            owner=owner,
            tasks=list(st.session_state["tasks"]),
            constraints=constraints,
        )

        schedule = planner.generate_plan()
        # sort_by_time is already called inside generate_plan(), but call it
        # explicitly here to make the dependency on Schedule's method clear
        schedule.sort_by_time()

        explanation = planner._explanation_engine.explain(schedule)

        # --- Schedule table ---
        st.success("Today's Schedule (sorted by start time)")
        st.table([
            {
                "Start Time": t.scheduled_time.strftime("%I:%M %p") if t.scheduled_time else "—",
                "Task": t.name,
                "Duration (min)": t.duration,
                "Priority": _priority_badge(t.priority),
                "Score": t.get_priority_score(),
                "Mandatory": "Yes" if t.is_mandatory else "No",
                "Recurring": t.recurrence if t.recurrence else "—",
                "Urgent": "Yes" if t.is_urgent(datetime.now()) else "No",
            }
            for t in schedule.tasks
        ])

        # --- Time metrics ---
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Tasks scheduled", len(schedule.tasks))
        col_m2.metric("Total time scheduled", f"{schedule.total_time} min")
        col_m3.metric("Unused time", f"{schedule.unused_time} min")

        # --- Conflict report using Schedule.check_conflicts() ---
        st.markdown("**Conflict report**")
        conflict_warnings = schedule.check_conflicts()
        if conflict_warnings:
            for warning in conflict_warnings:
                st.warning(warning)
        else:
            st.success("No time conflicts detected.")

        # --- Excluded mandatory tasks via ConflictDetector ---
        detector = ConflictDetector()
        excluded = detector.find_excluded_mandatory(st.session_state["tasks"], schedule)
        if excluded:
            st.markdown("**Mandatory tasks that could not be scheduled (not enough time):**")
            for t in excluded:
                st.warning(f"'{t.name}' — {t.duration} min required, but it did not fit in today's schedule.")
        else:
            st.success("All mandatory tasks fit in today's schedule.")

        # --- Overbooked categories ---
        overbooked = detector.find_overbooked_categories(st.session_state["tasks"], constraints)
        if overbooked:
            st.markdown("**Overbooked categories:**")
            for cat, count in overbooked.items():
                limit = constraints.task_limits[cat]
                st.warning(f"Category '{cat}' has {count} tasks but the daily limit is {limit}.")

        # --- Explanation ---
        st.markdown("**Why these tasks?**")
        st.text(explanation)

        # --- Recurring: show tasks due in future ---
        recurring_in_schedule = [t for t in schedule.tasks if t.recurrence]
        if recurring_in_schedule:
            st.markdown("**Upcoming recurrences (next occurrence preview):**")
            next_rows = []
            for t in recurring_in_schedule:
                nxt = t.next_occurrence()
                next_rows.append({
                    "Task": t.name,
                    "Recurrence": t.recurrence,
                    "Next Due": nxt.scheduled_time.strftime("%A, %b %d %I:%M %p") if nxt.scheduled_time else "—",
                })
            st.table(next_rows)
