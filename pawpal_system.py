"""
pawpal_system.py

Logic layer for the PawPal+ app.
Backend classes based on the UML diagram (Owner, Pet, Task, Scheduler).
Uses dataclasses to keep the data objects clean.
"""

from dataclasses import dataclass, field, replace
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Recurrence(Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"


class TaskStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    MISSED = "missed"


class TaskType(Enum):
    FEEDING = "feeding"
    WALKING = "walking"
    GROOMING = "grooming"
    VET_VISIT = "vet_visit"
    MEDICATION = "medication"
    ENRICHMENT = "enrichment"
    OTHER = "other"


def format_minute(minute: int) -> str:
    """Turn minutes-since-midnight into an HH:MM string (e.g. 480 -> '08:00')."""
    minute %= 24 * 60
    return f"{minute // 60:02d}:{minute % 60:02d}"


@dataclass
class Task:
    """A single pet-care activity: what to do, how long, how often, and its state."""

    task_id: int
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    recurrence: Recurrence = Recurrence.NONE
    # Scheduled start time as a zero-padded "HH:MM" string (e.g. "08:00").
    # Empty means the task has no fixed time yet.
    time: str = ""
    # NOTE: pet_id duplicates the Pet.tasks link. Treat Pet.tasks as the
    # source of truth; pet_id is a convenience back-reference only.
    pet_id: Optional[int] = None
    notes: str = ""
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def priority_rank(self) -> int:
        """Numeric rank for sorting (higher = more important)."""
        return self.priority.value

    def mark_completed(self, when: Optional[datetime] = None) -> None:
        """Mark the task completed, recording when it happened.

        This only changes *this* task's state. Auto-creating the next
        occurrence of a recurring task is handled by ``Pet.complete_task``,
        which owns the task list (the source of truth) and can append the
        new instance to it.
        """
        self.status = TaskStatus.COMPLETED
        self.completed_at = when or datetime.now()

    def next_due_date(self, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """Compute when this task should next fall due, or ``None`` if it doesn't recur.

        The offset is added with :class:`datetime.timedelta`, which does the
        calendar math correctly — rolling over month and year boundaries — so
        we never have to worry about "day 32" or leap years:

        * ``DAILY``  -> base + ``timedelta(days=1)``  (today + 1 day)
        * ``WEEKLY`` -> base + ``timedelta(weeks=1)`` (today + 7 days)

        The base time is the first of these that is set: the caller-supplied
        ``from_time``, this task's ``due_date``, its ``completed_at``, or — as
        a last resort — ``datetime.now()``.
        """
        if self.recurrence == Recurrence.NONE:
            return None

        base = from_time or self.due_date or self.completed_at or datetime.now()

        if self.recurrence == Recurrence.DAILY:
            return base + timedelta(days=1)
        if self.recurrence == Recurrence.WEEKLY:
            return base + timedelta(weeks=1)
        return None

    def spawn_next(self, from_time: Optional[datetime] = None) -> Optional["Task"]:
        """Return a fresh PENDING copy of this task for its next occurrence.

        Returns ``None`` for non-recurring tasks. The copy keeps every
        descriptive field (title, duration, priority, time, notes, …) but
        resets the tracking fields: it is PENDING again, has no completion
        time, and its ``due_date`` is advanced by ``next_due_date``. The
        ``task_id`` is copied as a placeholder — callers that manage a task
        list (see ``Pet.complete_task``) reassign it to a unique value.
        """
        next_due = self.next_due_date(from_time)
        if next_due is None:
            return None

        return replace(
            self,
            status=TaskStatus.PENDING,
            completed_at=None,
            due_date=next_due,
        )

    def mark_missed(self) -> None:
        """Mark the task missed and clear any completion time."""
        self.status = TaskStatus.MISSED
        self.completed_at = None

    def is_pending(self) -> bool:
        """Return True if the task is still pending."""
        return self.status == TaskStatus.PENDING

    def update_notes(self, notes: str) -> None:
        """Replace the task's notes."""
        self.notes = notes


@dataclass
class Pet:
    """Stores pet details and the list of tasks that belong to this pet."""

    pet_id: int
    name: str
    species: str
    breed: str = ""
    birth_date: Optional[date] = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet, keeping its back-reference in sync."""
        task.pet_id = self.pet_id  # keep the back-reference consistent
        self.tasks.append(task)

    def remove_task(self, task_id: int) -> None:
        """Remove the task with the given id from this pet."""
        self.tasks = [t for t in self.tasks if t.task_id != task_id]

    def _next_task_id(self) -> int:
        """Smallest unused id for a new task on this pet (max existing + 1)."""
        return max((t.task_id for t in self.tasks), default=0) + 1

    def complete_task(
        self, task_id: int, when: Optional[datetime] = None
    ) -> Optional[Task]:
        """Complete one of this pet's tasks and roll a recurring one forward.

        Marks the task with ``task_id`` completed. If that task is DAILY or
        WEEKLY, a fresh PENDING instance is created for the next occurrence
        (via ``Task.spawn_next``), given a unique id, and appended to this
        pet's task list — so recurring chores reappear automatically.

        Returns the newly created task, or ``None`` if the task wasn't found
        or doesn't recur.
        """
        task = next((t for t in self.tasks if t.task_id == task_id), None)
        if task is None:
            return None

        task.mark_completed(when)

        next_task = task.spawn_next(from_time=task.completed_at)
        if next_task is None:
            return None

        next_task.task_id = self._next_task_id()
        self.add_task(next_task)
        return next_task

    def get_pending_tasks(self) -> list[Task]:
        """Return this pet's tasks that are still pending."""
        return [t for t in self.tasks if t.status == TaskStatus.PENDING]

    def get_completed_tasks(self) -> list[Task]:
        """Return this pet's tasks that are completed."""
        return [t for t in self.tasks if t.status == TaskStatus.COMPLETED]

    def update_notes(self, notes: str) -> None:
        """Replace the pet's notes."""
        self.notes = notes


@dataclass
class Owner:
    """Manages multiple pets and provides access to all their tasks."""

    owner_id: int
    name: str
    available_minutes: int = 120
    # Minutes since midnight (e.g. 8 * 60 = 480 for 08:00) so scheduling is
    # plain integer math instead of parsing/formatting time strings.
    preferred_start_minute: int = 8 * 60
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_id: int) -> None:
        """Remove the pet with the given id from this owner."""
        self.pets = [p for p in self.pets if p.pet_id != pet_id]

    def get_pet(self, pet_id: int) -> Optional[Pet]:
        """Return the pet with the given id, or None if not found."""
        return next((p for p in self.pets if p.pet_id == pet_id), None)

    def all_tasks(self) -> list[Task]:
        """Every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def all_pending_tasks(self) -> list[Task]:
        """Pending tasks across all pets — the scheduler's input."""
        return [task for task in self.all_tasks() if task.status == TaskStatus.PENDING]


@dataclass
class ScheduledItem:
    """One task placed at a time slot in the daily plan."""

    start_minute: int  # minutes since midnight
    task: Task

    @property
    def start_time(self) -> str:
        """The slot's start time as an HH:MM string."""
        return format_minute(self.start_minute)


@dataclass
class Scheduler:
    """The 'brain': retrieves, organizes, and time-slots tasks across pets."""

    available_minutes: int
    start_minute: int = 8 * 60

    @classmethod
    def from_owner(cls, owner: Owner) -> "Scheduler":
        """Build a scheduler from the owner's constraints (single source of truth)."""
        return cls(
            available_minutes=owner.available_minutes,
            start_minute=owner.preferred_start_minute,
        )

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """High priority first; break ties with the shorter task so more fit."""
        return sorted(
            tasks,
            key=lambda t: (-t.priority_rank(), t.duration_minutes),
        )

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks chronologically by their "HH:MM" ``time`` string.

        Because the strings are zero-padded ("08:00", not "8:00"), sorting them
        lexicographically gives the same order as sorting by clock time, so a
        plain string ``key`` works — no time parsing needed. Tasks with no time
        set ("") sort to the end via the "99:99" fallback.
        """
        return sorted(tasks, key=lambda t: t.time or "99:99")

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        status: Optional[TaskStatus] = None,
        pet_id: Optional[int] = None,
    ) -> list[Task]:
        """Return the tasks matching every filter that was provided.

        Each filter is optional; passing ``None`` (the default) means "don't
        filter on this field". So ``filter_tasks(tasks, status=COMPLETED)``
        keeps only completed tasks, and adding ``pet_id=1`` narrows to that pet.
        """
        result = tasks
        if status is not None:
            result = [t for t in result if t.status == status]
        if pet_id is not None:
            result = [t for t in result if t.pet_id == pet_id]
        return result

    def fits(self, task: Task, remaining_minutes: int) -> bool:
        """Whether the task's duration fits in the time left."""
        return task.duration_minutes <= remaining_minutes

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Flag tasks scheduled at the same clock time — as warnings, not errors.

        This is a deliberately *lightweight* check: it groups tasks by their
        ``time`` string (the same zero-padded "HH:MM" the scheduler already
        relies on) and reports any slot holding two or more tasks. It does not
        consider durations or overlap — just identical start times, which is
        cheap and catches the common "two things booked for 08:00" mistake.

        Tasks with no time set ("") are ignored, since an unset time can't
        clash with anything yet. The method never raises: it returns a list of
        human-readable warning strings (empty when there are no conflicts), so
        callers can print them and keep going.
        """
        by_time: dict[str, list[Task]] = {}
        for task in tasks:
            if not task.time:  # skip tasks with no fixed time yet
                continue
            by_time.setdefault(task.time, []).append(task)

        warnings: list[str] = []
        for time in sorted(by_time):
            clashing = by_time[time]
            if len(clashing) < 2:
                continue
            titles = ", ".join(
                f"'{t.title}' (pet {t.pet_id})" for t in clashing
            )
            warnings.append(
                f"[!] Conflict at {time}: {len(clashing)} tasks overlap - {titles}"
            )
        return warnings

    def build_plan(self, owner: Owner) -> list[ScheduledItem]:
        """Greedily place the owner's pending tasks under the time budget.

        Tasks are considered in priority order; each that fits is placed back
        to back starting at ``start_minute``. Tasks that don't fit are skipped.
        """
        plan: list[ScheduledItem] = []
        clock = self.start_minute
        remaining = self.available_minutes

        for task in self.sort_tasks(owner.all_pending_tasks()):
            if self.fits(task, remaining):
                plan.append(ScheduledItem(start_minute=clock, task=task))
                clock += task.duration_minutes
                remaining -= task.duration_minutes

        return plan

    def explain(self, plan: list[ScheduledItem]) -> str:
        """Human-readable reasoning for the plan."""
        if not plan:
            return "No tasks could be scheduled within the available time."

        lines = ["Daily plan:"]
        for item in plan:
            t = item.task
            end = format_minute(item.start_minute + t.duration_minutes)
            lines.append(
                f"  {item.start_time}–{end}  {t.title} "
                f"({t.duration_minutes} min) [priority: {t.priority.name.lower()}]"
            )

        used = sum(item.task.duration_minutes for item in plan)
        lines.append(
            f"Scheduled {len(plan)} task(s) using {used} of "
            f"{self.available_minutes} available minutes, "
            "highest-priority tasks first."
        )
        return "\n".join(lines)

