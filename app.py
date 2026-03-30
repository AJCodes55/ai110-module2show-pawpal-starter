from datetime import datetime

import streamlit as st
from pawpal_system import (
    Constraint,
    ConflictDetector,
    Owner,
    Pet,
    Planner,
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

    # Also assign the task to the pet if an owner is set
    if owner_now is not None:
        pet = owner_now.pets[0]
        pet.add_task(task)
        st.success(f'Added "{task.name}" and assigned it to {pet.name} (now has {pet.task_count()} task(s))')
    else:
        st.success(f'Added "{task.name}" to task list')

if st.session_state["tasks"]:
    st.write("Current tasks:")
    st.table([
        {
            "Task": t.name,
            "Duration (min)": t.duration,
            "Priority": t.priority,
            "Category": t.category,
            "Mandatory": t.is_mandatory,
            "Recurrence": t.recurrence or "—",
            "Pet": t.pet_name or "—",
            "Done": t.completed,
        }
        for t in st.session_state["tasks"]
    ])

    with st.expander("Filter tasks"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_pet = st.text_input("Filter by pet name (leave blank for all)")
        with col_f2:
            filter_status = st.selectbox("Filter by status", ["All", "Pending", "Completed"])

        filtered = list(st.session_state["tasks"])
        if filter_pet.strip():
            filtered = [t for t in filtered if t.pet_name.lower() == filter_pet.strip().lower()]
        if filter_status == "Pending":
            filtered = [t for t in filtered if not t.completed]
        elif filter_status == "Completed":
            filtered = [t for t in filtered if t.completed]

        if filtered:
            st.table([
                {
                    "Task": t.name,
                    "Category": t.category,
                    "Recurrence": t.recurrence or "—",
                    "Pet": t.pet_name or "—",
                    "Done": t.completed,
                }
                for t in filtered
            ])
        else:
            st.info("No tasks match the current filter.")
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
        explanation = planner._explanation_engine.explain(schedule)

        st.success("Today's Schedule")
        st.table([
            {
                "Start Time": t.scheduled_time.strftime("%I:%M %p") if t.scheduled_time else "—",
                "Task": t.name,
                "Duration (min)": t.duration,
                "Priority": t.priority,
                "Mandatory": t.is_mandatory,
                "Recurrence": t.recurrence or "—",
                "Urgent": t.is_urgent(datetime.now()),
            }
            for t in schedule.tasks
        ])

        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Total time scheduled", f"{schedule.total_time} min")
        col_m2.metric("Unused time", f"{schedule.unused_time} min")

        st.markdown("**Why these tasks?**")
        st.text(explanation)

        st.markdown("**Conflict report**")
        detector = ConflictDetector()
        report = detector.report(schedule, st.session_state["tasks"], constraints)
        if report == "No conflicts detected.":
            st.success(report)
        else:
            st.warning(report)
