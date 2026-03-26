import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Pet, Task


# ---------------------------------------------------------------------------
# Test 1 — Task completion
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
# Test 2 — Adding a task to a Pet increases its task count
# ---------------------------------------------------------------------------
def test_add_task_increases_pet_task_count():
    pet = Pet(name="Buddy", species="dog", age=3, energy_level=8)

    assert pet.task_count() == 0, "Pet should start with no tasks"

    pet.add_task(Task(name="Feeding", duration=10, priority=9, category="nutrition", is_mandatory=True))
    assert pet.task_count() == 1, "Pet should have 1 task after first addition"

    pet.add_task(Task(name="Play session", duration=20, priority=5, category="exercise", is_mandatory=False))
    assert pet.task_count() == 2, "Pet should have 2 tasks after second addition"


# ---------------------------------------------------------------------------
# Run directly via `python tests/test_pawpal.py`
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_mark_complete_changes_status()
    print("PASS  test_mark_complete_changes_status")

    test_add_task_increases_pet_task_count()
    print("PASS  test_add_task_increases_pet_task_count")
