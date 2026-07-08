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

from pawpal_system import Pet, Task, TaskStatus, Recurrence, Scheduler


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


def test_sort_by_time_returns_chronological_order():
    """Sorting Correctness: sort_by_time() orders tasks by their HH:MM time.

    We deliberately hand the scheduler the tasks out of order and with one
    task that has NO time set. The expected result is early-to-late clock
    order, with the timeless task pushed to the very end (the scheduler uses
    a "99:99" fallback so unset times sort last).
    """
    scheduler = Scheduler(available_minutes=120)

    evening = Task(task_id=1, title="Evening walk", duration_minutes=30, time="18:00")
    morning = Task(task_id=2, title="Breakfast", duration_minutes=10, time="08:00")
    midday = Task(task_id=3, title="Play", duration_minutes=15, time="12:30")
    no_time = Task(task_id=4, title="Someday grooming", duration_minutes=20, time="")

    # Pass them in a jumbled order to prove the sort is doing the work.
    ordered = scheduler.sort_by_time([evening, no_time, midday, morning])

    # Reading off the titles is the clearest way to assert the order.
    assert [t.title for t in ordered] == [
        "Breakfast",       # 08:00
        "Play",            # 12:30
        "Evening walk",    # 18:00
        "Someday grooming",  # "" -> sorts last
    ]


def test_detect_conflicts_flags_duplicate_times():
    """Conflict Detection: two tasks at the same time produce one warning.

    Two tasks share 08:00, one is alone at 09:00, and one has no time. Only
    the 08:00 pair should be flagged: we expect exactly one warning string,
    and it should mention the clashing time.
    """
    scheduler = Scheduler(available_minutes=120)

    tasks = [
        Task(task_id=1, title="Feed cat", duration_minutes=10, time="08:00", pet_id=1),
        Task(task_id=2, title="Feed dog", duration_minutes=10, time="08:00", pet_id=2),
        Task(task_id=3, title="Walk", duration_minutes=30, time="09:00", pet_id=2),
        Task(task_id=4, title="Later", duration_minutes=15, time="", pet_id=1),
    ]

    warnings = scheduler.detect_conflicts(tasks)

    # Exactly one clash (the 08:00 pair); 09:00 is alone and "" is ignored.
    assert len(warnings) == 1
    assert "08:00" in warnings[0]


def test_detect_conflicts_returns_empty_when_no_clash():
    """Conflict Detection: distinct times produce no warnings at all."""
    scheduler = Scheduler(available_minutes=120)

    tasks = [
        Task(task_id=1, title="Feed", duration_minutes=10, time="08:00"),
        Task(task_id=2, title="Walk", duration_minutes=30, time="09:00"),
    ]

    assert scheduler.detect_conflicts(tasks) == []
