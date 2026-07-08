"""
Simple unit tests for the PawPal+ backend (pawpal_system.py).

Run from the project root with:
    python -m pytest tests/test_pawpal.py
"""

import os
import sys

# Make the project root importable so `pawpal_system` is found when
# pytest runs from the tests/ directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta

from pawpal_system import Pet, Task, TaskStatus, Recurrence


def test_mark_completed_changes_status():
    """Task Completion: mark_completed() should flip status to COMPLETED."""
    task = Task(task_id=1, title="Morning walk", duration_minutes=20)

    # A fresh task starts out pending.
    assert task.status == TaskStatus.PENDING

    task.mark_completed()

    # After marking complete, the status should have changed.
    assert task.status == TaskStatus.COMPLETED
    assert task.completed_at is not None


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet increases that pet's task count."""
    pet = Pet(pet_id=1, name="Mochi", species="cat")

    # A new pet has no tasks.
    assert len(pet.tasks) == 0

    pet.add_task(Task(task_id=1, title="Feed breakfast", duration_minutes=10))

    # The task count should go up by one.
    assert len(pet.tasks) == 1


def test_completing_daily_task_spawns_next_day():
    """A DAILY task, once completed, respawns due one day later."""
    pet = Pet(pet_id=1, name="Rex", species="dog")
    due = datetime(2026, 7, 7, 8, 0)
    pet.add_task(
        Task(
            task_id=1,
            title="Morning walk",
            duration_minutes=30,
            recurrence=Recurrence.DAILY,
            due_date=due,
        )
    )

    new_task = pet.complete_task(1, when=due)

    # The original is now completed...
    assert pet.tasks[0].status == TaskStatus.COMPLETED
    # ...and a brand-new pending instance was added for the next occurrence.
    assert new_task is not None
    assert len(pet.tasks) == 2
    assert new_task.status == TaskStatus.PENDING
    assert new_task.due_date == due + timedelta(days=1)
    # The spawned task gets a fresh, unique id and keeps the recurrence.
    assert new_task.task_id != 1
    assert new_task.recurrence == Recurrence.DAILY


def test_completing_weekly_task_spawns_next_week():
    """A WEEKLY task respawns due seven days later."""
    pet = Pet(pet_id=1, name="Rex", species="dog")
    due = datetime(2026, 7, 7, 9, 0)
    pet.add_task(
        Task(
            task_id=1,
            title="Bath",
            duration_minutes=45,
            recurrence=Recurrence.WEEKLY,
            due_date=due,
        )
    )

    new_task = pet.complete_task(1, when=due)

    assert new_task is not None
    assert new_task.due_date == due + timedelta(weeks=1)


def test_completing_one_off_task_does_not_respawn():
    """A non-recurring task should NOT create a new instance."""
    pet = Pet(pet_id=1, name="Rex", species="dog")
    pet.add_task(Task(task_id=1, title="Vet visit", duration_minutes=60))

    new_task = pet.complete_task(1)

    assert new_task is None
    assert len(pet.tasks) == 1
    assert pet.tasks[0].status == TaskStatus.COMPLETED
