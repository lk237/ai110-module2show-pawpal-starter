
from pawpal_system import (
    Owner,
    Pet,
    Task,
    Scheduler,
    Priority,
    TaskType,
    TaskStatus,
    format_minute,
)


def build_owner() -> Owner:
    """Create an owner with two pets and a handful of tasks.

    The tasks are deliberately added *out of time order* so that
    ``Scheduler.sort_by_time`` has something real to reorder.
    """
    owner = Owner(owner_id=1, name="Jordan", available_minutes=180)

    dog = Pet(pet_id=1, name="Rex", species="Dog", breed="Labrador")
    cat = Pet(pet_id=2, name="Luna", species="Cat", breed="Siamese")

    # Note the scrambled times ("12:30" added before "07:30", etc.) — this
    # proves the sorting method is doing the work, not the insertion order.
    dog.add_task(
        Task(
            task_id=1,
            title="Midday walk",
            duration_minutes=45,
            priority=Priority.HIGH,
            task_type=TaskType.WALKING,
            time="12:30",
        )
    )
    dog.add_task(
        Task(
            task_id=2,
            title="Breakfast feeding",
            duration_minutes=15,
            priority=Priority.HIGH,
            task_type=TaskType.FEEDING,
            time="07:30",
        )
    )
    cat.add_task(
        Task(
            task_id=3,
            title="Litter box cleaning",
            duration_minutes=10,
            priority=Priority.MEDIUM,
            task_type=TaskType.OTHER,
            time="18:00",
        )
    )
    cat.add_task(
        Task(
            task_id=4,
            title="Play / enrichment",
            duration_minutes=20,
            priority=Priority.LOW,
            task_type=TaskType.ENRICHMENT,
            time="09:15",
        )
    )
    # Two tasks deliberately booked for the SAME time (12:30) — one for the
    # dog, one for the cat — so the conflict detector has something to catch.
    dog.add_task(
        Task(
            task_id=5,
            title="Grooming session",
            duration_minutes=30,
            priority=Priority.MEDIUM,
            task_type=TaskType.GROOMING,
            time="12:30",  # clashes with Rex's "Midday walk"
        )
    )
    cat.add_task(
        Task(
            task_id=6,
            title="Vet check-up",
            duration_minutes=30,
            priority=Priority.HIGH,
            task_type=TaskType.VET_VISIT,
            time="12:30",  # same slot, different pet
        )
    )

    owner.add_pet(dog)
    owner.add_pet(cat)

    # Mark one task done so the status filter has something to hide/show.
    dog.tasks[1].mark_completed()  # Breakfast feeding

    return owner


def print_todays_schedule(owner: Owner) -> None:
    """Build and print today's schedule for the owner."""
    scheduler = Scheduler.from_owner(owner)
    plan = scheduler.build_plan(owner)

    print("=" * 40)
    print(f"Today's Schedule for {owner.name}")
    print("=" * 40)

    if not plan:
        print("Nothing scheduled today.")
        return

    # Map pet_id -> pet name so each line shows whose task it is.
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}

    for item in plan:
        task = item.task
        end = format_minute(item.start_minute + task.duration_minutes)
        pet = pet_names.get(task.pet_id, "Unknown")
        print(
            f"  {item.start_time}-{end}  {task.title} "
            f"({pet}, {task.duration_minutes} min) "
            f"[{task.priority.name.lower()}]"
        )

    print("-" * 40)
    print(scheduler.explain(plan))


def task_line(owner: Owner, task: Task) -> str:
    """One tidy display line for a task, including its pet and status."""
    pet_names = {pet.pet_id: pet.name for pet in owner.pets}
    pet = pet_names.get(task.pet_id, "Unknown")
    when = task.time or "--:--"
    return (
        f"  {when}  {task.title} "
        f"({pet}, {task.duration_minutes} min) "
        f"[{task.priority.name.lower()}, {task.status.value}]"
    )


def demo_sorting_and_filtering(owner: Owner) -> None:
    """Show the new sort_by_time and filter_tasks methods in the terminal."""
    scheduler = Scheduler.from_owner(owner)
    tasks = owner.all_tasks()

    print("=" * 44)
    print("Tasks as added (unsorted)")
    print("=" * 44)
    for task in tasks:
        print(task_line(owner, task))

    print()
    print("=" * 44)
    print("Sorted by time (sort_by_time)")
    print("=" * 44)
    for task in scheduler.sort_by_time(tasks):
        print(task_line(owner, task))

    print()
    print("=" * 44)
    print("Filtered: only PENDING tasks (filter_tasks)")
    print("=" * 44)
    pending = scheduler.filter_tasks(tasks, status=TaskStatus.PENDING)
    for task in scheduler.sort_by_time(pending):
        print(task_line(owner, task))

    print()
    print("=" * 44)
    print("Filtered: only Rex's tasks (filter_tasks by pet)")
    print("=" * 44)
    rex = next(p for p in owner.pets if p.name == "Rex")
    for task in scheduler.sort_by_time(scheduler.filter_tasks(tasks, pet_id=rex.pet_id)):
        print(task_line(owner, task))


def check_for_conflicts(owner: Owner) -> None:
    """Run the scheduler's lightweight conflict check and print any warnings."""
    scheduler = Scheduler.from_owner(owner)
    warnings = scheduler.detect_conflicts(owner.all_tasks())

    print("=" * 44)
    print("Conflict check (detect_conflicts)")
    print("=" * 44)
    if not warnings:
        print("No scheduling conflicts found.")
        return
    for warning in warnings:
        print(warning)


def main() -> None:
    owner = build_owner()
    demo_sorting_and_filtering(owner)
    print()
    check_for_conflicts(owner)
    print()
    print_todays_schedule(owner)


if __name__ == "__main__":
    main()
