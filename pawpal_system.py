"""
pawpal_system.py

Logic layer for the PawPal+ app.
Backend class skeletons based on the UML diagram (Owner, Pet, Task, Scheduler).
Uses dataclasses to keep the data objects clean.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


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


@dataclass
class Task:
    task_id: int
    title: str
    duration_minutes: int
    priority: Priority = Priority.MEDIUM
    task_type: TaskType = TaskType.OTHER
    pet_id: Optional[int] = None
    notes: str = ""
    status: TaskStatus = TaskStatus.PENDING
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def priority_rank(self) -> int:
        """Numeric rank for sorting (higher = more important)."""
        pass

    def mark_completed(self) -> None:
        pass

    def mark_missed(self) -> None:
        pass

    def update_notes(self, notes: str) -> None:
        pass


@dataclass
class Pet:
    pet_id: int
    name: str
    species: str
    breed: str = ""
    birth_date: Optional[date] = None
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        pass

    def remove_task(self, task_id: int) -> None:
        pass

    def get_pending_tasks(self) -> list[Task]:
        pass

    def get_completed_tasks(self) -> list[Task]:
        pass

    def update_notes(self, notes: str) -> None:
        pass


@dataclass
class Owner:
    owner_id: int
    name: str
    available_minutes: int = 120
    preferred_start_time: str = "08:00"
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        pass

    def remove_pet(self, pet_id: int) -> None:
        pass

    def get_pet(self, pet_id: int) -> Optional[Pet]:
        pass


@dataclass
class ScheduledItem:
    """One task placed at a time slot in the daily plan."""
    start_time: str
    task: Task


@dataclass
class Scheduler:
    available_minutes: int
    start_time: str = "08:00"

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority (then duration) so important ones win."""
        pass

    def fits(self, task: Task, remaining_minutes: int) -> bool:
        """Whether the task's duration fits in the time left."""
        pass

    def build_plan(self, pet: Pet) -> list[ScheduledItem]:
        """Select and time-slot tasks under the available-minutes budget."""
        pass

    def explain(self, plan: list[ScheduledItem]) -> str:
        """Human-readable reasoning for why each task was chosen and placed."""
        pass
