# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smart Scheduling

PawPal+ goes beyond a basic task list with a set of scheduling intelligence features built into `pawpal_system.py`.

### Time-aware scheduling

Every task that makes it into the daily plan is assigned a concrete **start time** based on the owner's preferred schedule (morning = 8 AM, evening = 6 PM, flexible = 9 AM). Tasks are placed back-to-back in priority order and automatically sorted chronologically so the day reads like a real timetable.

```
08:00 AM  Morning walk       (30 min) [daily]
08:30 AM  Feeding            (10 min) [daily]
08:40 AM  Vet medication     ( 5 min) [URGENT]
```

### Recurring tasks

Tasks can be marked with a recurrence rule so they only appear on the right days:

| Rule | Behaviour |
|---|---|
| `daily` | Scheduled every day |
| `weekdays` | Monday – Friday only |
| `weekends` | Saturday – Sunday only |
| `weekly` | Same weekday each week |

When a recurring task is completed via `Schedule.complete_task()`, a new instance for the **next occurrence** is automatically created and queued in `schedule.upcoming` — no manual re-entry needed.

### Filtering

After a schedule is generated you can slice it two ways:

- **By pet** — `schedule.filter_by_pet("Buddy")` returns only Buddy's tasks.
- **By status** — `schedule.filter_by_status(completed=False)` returns pending tasks; `completed=True` returns finished ones.

Both methods return plain lists, so they compose easily (filter by pet, then filter that list by status).

### Conflict detection

`Schedule.check_conflicts()` scans every pair of scheduled tasks for time-window overlaps and returns a list of plain warning strings — it never raises an exception or stops the program.

Three situations are reported:

- **Same pet, same start time** — `WARNING: 'Feeding' and 'Medication' [both: Buddy] start at the same time (08:00 AM)`
- **Different pets, overlapping windows** — `WARNING: 'Walk' and 'Vet visit' [Buddy & Luna] overlap (08:00–08:30 AM vs 08:20–08:30 AM)`
- **Clean schedule** — returns an empty list; the Streamlit UI shows a green success banner.

The Streamlit UI (`app.py`) surfaces all of these features: a recurrence dropdown when adding tasks, a collapsible filter panel on the task list, and a conflict report that appears automatically after every schedule generation.

## Testing PawPal+

Run the full test suite with:

```bash
python3 -m pytest
```

All 39 tests pass. The suite covers four areas of the scheduling system:

**Sorting** — verifies that tasks with a scheduled time sort earliest-first, that unscheduled tasks fall to the end of the list, and that sorting never raises on edge inputs (empty schedule, all-unscheduled).

**Recurring tasks** — checks every recurrence rule (`daily`, `weekly`, `weekdays`, `weekends`) including boundary crossings (Friday → Monday for weekdays, Sunday → Saturday for weekends), that deadline offsets are preserved proportionally on each new occurrence, that `is_due_today` correctly gates tasks by day of week, and that the weekly fallback when no deadline is set defaults to Monday.

**Conflict detection** — confirms that overlapping task windows are flagged, that back-to-back tasks (touching but not overlapping) are not, and that edge cases like a single task, an empty schedule, and tasks with no scheduled time are all handled without false positives. Also covers `ConflictDetector`'s mandatory-exclusion and overbooked-category reports.

**Scheduling and priority** — validates that the planner respects time and category constraints (zero available time, category limit of 0), that mandatory tasks receive their priority boost and win scheduling slots over higher-base-priority optional tasks, and that `get_priority_score()` is correctly capped at 10 even when urgency and mandatory flags stack.

### Confidence Level

★★★★☆ (4 / 5)

The core scheduling logic — priority scoring, recurrence rules, conflict detection, and constraint enforcement — is fully exercised and passes 100%. One star is held back because the test suite does not yet cover the Streamlit UI layer (`app.py`) or multi-pet scheduling interactions; those paths contain real user-facing logic that would benefit from integration tests.

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
