# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

My initial design followed the three steps a pet owner naturally takes:

1. **Enter owner + pet info** — capture who the owner is and which pet the plan is for.
2. **Enter tasks with duration + restrictions** — each care task has a duration and a priority, plus constraints like how much total time is available that day.
3. **Generate a daily plan** — feed the collected info into a scheduler that selects and orders tasks, then produces a readable daily plan.

- What classes did you include, and what responsibilities did you assign to each?

| Class | Responsibility |
|-------|----------------|
| `Owner` | Holds owner name and preferences (available minutes per day, preferred start time). |
| `Pet` | Holds pet name and species — the subject the plan is built for. |
| `Task` | Represents one care task: title, `duration_minutes`, and `priority` (low/medium/high). Knows how to compare itself to other tasks for sorting. |
| `Scheduler` | The core logic. Takes the tasks plus the owner's time constraints, sorts by priority, drops tasks that don't fit the available time, and assigns each chosen task a time slot. |
| `DailyPlan` | The output. Holds the ordered, scheduled tasks and formats/explains the plan for display. |

Relationships: an `Owner` has one or more `Pet`s; a `Pet` has many `Task`s; the `Scheduler` consumes tasks + constraints and produces one `DailyPlan`.

**b. Design changes**

- Did your design change during implementation?

Yes.

- If yes, describe at least one change and why you made it.

I originally planned to put the scheduling logic directly inside the `Pet` class (a `pet.build_plan()` method). During implementation I pulled that logic out into a dedicated `Scheduler` class. Separating scheduling from `Pet` kept each class focused on one responsibility — `Pet` just stores data, while `Scheduler` owns the sorting/filtering/time-assignment rules. This made the scheduling behavior much easier to unit-test in isolation (I could pass a fixed list of tasks and assert on the resulting plan) and left room to swap scheduling strategies later without touching the data classes.

After a review pass on the skeleton (asking an AI assistant to flag missing relationships and logic bottlenecks), I made three further changes:

1. **Wired `Scheduler` to `Owner` instead of duplicating its constraints.** Both classes originally stored `available_minutes` and a start time, so they could silently disagree. I added a `Scheduler.from_owner(owner)` classmethod so the owner's preferences are the single source of truth.
2. **Switched time from strings to minutes-since-midnight (int).** `preferred_start_time = "08:00"` became `preferred_start_minute = 480`, and `ScheduledItem` now stores `start_minute`. `build_plan` has to advance the clock as it places tasks, and integer math avoids fragile string parsing — I format back to `HH:MM` only for display.
3. **Added a `Recurrence` enum (none/daily/weekly) to `Task`.** The scenario calls for recurring tasks, and my first skeleton had no way to express them.

I also documented (via a comment) that `Task.pet_id` duplicates the `Pet.tasks` link and chose `Pet.tasks` as the source of truth to prevent the two from drifting out of sync.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

**Conflict detection only flags *exact* start-time matches, not overlapping durations.**
`Scheduler.detect_conflicts` groups tasks by their zero-padded `"HH:MM"` `time`
string and warns whenever two or more land in the same slot. It deliberately
ignores each task's `duration_minutes`: an 08:00 task that runs 90 minutes and
an 09:00 task are treated as *no conflict*, even though they physically overlap
from 09:00–09:30. Only two tasks stamped with the identical `"08:00"` are
flagged.

The `build_plan` greedy packer makes a related tradeoff — it places tasks back
to back from `start_minute` and never assigns them to a task's own preferred
`time`, so the plan it builds and the `time` field the conflict check reads are
two separate notions of "when." Conflict detection is a lightweight warning pass
over user-entered times, not a validation of the generated plan.

- Why is that tradeoff reasonable for this scenario?

For a pet-care day planner the common mistake is booking two chores for the
*same* moment ("feed the cat and walk the dog, both at 08:00"), and exact-match
grouping catches that in a single `O(n)` dictionary pass with no interval math,
no sweep-line, and no sorting of endpoints. Full overlap detection would mean
comparing every task's `[start, start + duration)` window against every other's —
more code, more edge cases (back-to-back tasks that merely touch, tasks with no
duration set), and more ways to be subtly wrong — to catch a case that rarely
bites a hobbyist scheduling a handful of tasks. The method returns warnings
rather than raising, so even when a real overlap slips through, the plan is still
produced and the owner stays in control. If the app later grew fixed-time
appointments (vet visits, medication windows) where true overlap matters,
upgrading this one method to an interval check is a contained change — the rest
of the scheduler wouldn't need to know.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
