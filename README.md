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

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
========================================
Today's Schedule for Jordan
========================================
  08:00-08:15  Breakfast feeding (Rex, 15 min) [high]
  08:15-09:00  Morning walk (Rex, 45 min) [high]
  09:00-09:10  Litter box cleaning (Luna, 10 min) [medium]
  09:10-09:30  Play / enrichment (Luna, 20 min) [low]
----------------------------------------
Daily plan:
  08:00–08:15  Breakfast feeding (15 min) [priority: high]
  08:15–09:00  Morning walk (45 min) [priority: high]
  09:00–09:10  Litter box cleaning (10 min) [priority: medium]
  09:10–09:30  Play / enrichment (20 min) [priority: low]
Scheduled 4 task(s) using 90 of 180 available minutes, highest-priority tasks first.
```


## 🧪 Testing PawPal+

Run the full test suite from the project root:

```bash
python -m pytest
```

### What the tests cover

The suite in [tests/test_pawpal.py](tests/test_pawpal.py) exercises the core
backend behaviors of the scheduler:

- **Task state** — `mark_completed()` flips a task to `COMPLETED` and stamps a completion time.
- **Task management** — adding a task to a `Pet` grows its task list.
- **Sorting correctness** — `Scheduler.sort_by_time()` returns tasks in chronological (`HH:MM`) order, with untimed tasks sorted last.
- **Recurrence logic** — completing a `DAILY` task auto-spawns a new `PENDING` task due one day later (and `WEEKLY` one week later), each with a unique id; one-off tasks do **not** respawn.
- **Conflict detection** — `Scheduler.detect_conflicts()` flags two tasks sharing a start time with a single warning, ignores untimed tasks, and returns an empty list when there are no clashes.

### Successful test run

```
============================= test session starts =============================
platform win32 -- Python 3.14.3, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\lkach\Documents\codepath AI\ai110-module2show-pawpal-starter
plugins: anyio-4.13.0
collected 8 items

tests\test_pawpal.py ........                                            [100%]

============================== 8 passed in 0.03s ==============================
```

### Confidence Level: ★★★★☆ (4 / 5)

All 8 tests pass and cover the highest-risk logic — sorting, recurrence
roll-forward, and conflict detection. I'm holding back one star because a few
behaviors aren't tested yet: the greedy `build_plan()` time-budgeting (including
the "task larger than the whole budget is skipped, not truncated" case), the
empty-pet edge case, and boundary conditions like a task duration exactly equal
to the remaining minutes. Adding those would raise confidence to 5/5.

## 📐 Smarter Scheduling

All scheduling logic lives in [pawpal_system.py](pawpal_system.py). The table
summarizes each feature and the method that implements it; details follow below.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Priority sorting | `Scheduler.sort_tasks()` | High priority first, shorter task breaks ties |
| Time sorting | `Scheduler.sort_by_time()` | Chronological by `HH:MM`; untimed tasks sort last |
| Filtering | `Scheduler.filter_tasks()` | By completion status and/or pet |
| Time-budget fit | `Scheduler.fits()` / `Scheduler.build_plan()` | Skips tasks that exceed remaining minutes |
| Conflict detection | `Scheduler.detect_conflicts()` | Warns on tasks sharing the same start time |
| Recurring tasks | `Task.next_due_date()`, `Task.spawn_next()`, `Pet.complete_task()` | Daily / weekly auto-respawn on completion |

### Sorting behavior

- **`Scheduler.sort_tasks()`** — the ordering the planner uses. Sorts by
  descending priority (`HIGH` → `LOW`) and breaks ties with the *shorter*
  duration first, so more tasks fit in the available time.
- **`Scheduler.sort_by_time()`** — chronological ordering for display. Sorts on
  the zero-padded `"HH:MM"` `time` string; because the strings are zero-padded,
  lexicographic order matches clock order, so no time parsing is needed. Tasks
  with no time set sort to the end via a `"99:99"` fallback.

### Filtering behavior

- **`Scheduler.filter_tasks()`** — keeps the tasks matching every filter passed.
  Both filters are optional keyword args:
  - `status=TaskStatus.COMPLETED` (or `PENDING`/`MISSED`) filters by completion status.
  - `pet_id=<id>` narrows to a single pet.
  - Combining them (e.g. `status=PENDING, pet_id=1`) applies both. Passing
    neither returns the list unchanged.

### Conflict detection logic

- **`Scheduler.detect_conflicts()`** — a lightweight, non-raising check. It
  groups tasks by their `time` string and reports any slot holding two or more
  tasks, returning a list of human-readable warning strings (empty when there
  are none). It compares start times only — not durations or partial overlap —
  which cheaply catches the common "two things booked for 08:00" mistake. Tasks
  with no time set are ignored, since an unset time can't clash yet.

### Recurring task logic

- **`Task.next_due_date()`** — computes the next due datetime for a `DAILY`
  (`+1 day`) or `WEEKLY` (`+7 days`) task, or `None` if the task doesn't recur.
  It uses `datetime.timedelta`, so month/year rollovers and leap years are
  handled correctly.
- **`Task.spawn_next()`** — returns a fresh `PENDING` copy for the next
  occurrence: descriptive fields (title, duration, priority, time, notes…) are
  preserved while the tracking fields (status, `completed_at`, `due_date`) are
  reset/advanced. Returns `None` for non-recurring tasks.
- **`Pet.complete_task()`** — ties it together. When a task is marked complete,
  if it recurs, a new instance is spawned, given a unique `task_id`, and
  appended to the pet's task list — so recurring chores reappear automatically.

### Building the plan

- **`Scheduler.build_plan()`** — greedily places pending tasks under the owner's
  time budget: it walks the priority-sorted tasks and, for each that still
  `fits()` in the remaining minutes, assigns a back-to-back time slot starting at
  the owner's preferred start time. **`Scheduler.explain()`** produces the
  human-readable summary of the resulting plan.

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
