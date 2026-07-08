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

**c. AI Strategy**

- Which AI coding assistant features were most effective for building your scheduler?

Three features did the heavy lifting. First, **whole-file/multi-file context** — attaching `pawpal_system.py` and asking the assistant to review the skeleton for missing relationships and logic bottlenecks is what surfaced the `Owner`/`Scheduler` constraint duplication and led to the `from_owner` classmethod. Second, **inline reasoning on tradeoffs** rather than just code: asking "what breaks if two tasks share a start time?" produced a discussion of exact-match vs. interval-overlap detection, which let me choose the lightweight approach deliberately instead of accidentally. Third, **test scaffolding** — the assistant was fastest at turning a described behavior ("completing a daily task should spawn a new pending task one day later") into a concrete pytest case I could then read, run, and trust.

- Give one example of an AI suggestion you rejected or modified to keep your system design clean.

When I added conflict detection, the assistant proposed a full **interval-overlap** check — comparing each task's `[start, start + duration)` window against every other's. It was correct and more thorough, but it dragged in edge cases (back-to-back tasks that merely touch, tasks with no duration, sweep-line ordering) that the scenario didn't need. I **modified it down** to a single `O(n)` exact-start-time grouping in `detect_conflicts`, and documented *why* in the tradeoffs section so the scope choice is intentional and reversible. I made a similar call on data modeling: rather than a bidirectional `Pet`↔`Task` sync the assistant leaned toward, I kept `Pet.tasks` as the single source of truth and demoted `Task.pet_id` to a documented back-reference.

- How did using separate chat sessions for different phases help you stay organized?

I ran each phase in its own session — UML design, backend implementation, Streamlit UI wiring, the README, then the UML/reflection updates. Keeping them separate meant each conversation carried only the context relevant to that phase, so the assistant's suggestions stayed on-topic instead of re-litigating settled decisions, and I could revisit a phase's reasoning later without scrolling past unrelated work. It also enforced a natural checkpoint: I only moved to the next session once the current artifact (diagram, passing tests, working app) was actually done, which kept the phases from bleeding into each other.

- Summarize what you learned about being the "lead architect" when collaborating with powerful AI tools.

The assistant is excellent at producing *a* correct implementation quickly, but "correct" and "right for this system" aren't the same thing — that judgment stayed mine. My job as lead architect was to own the invariants (single source of truth, one responsibility per class, scope matched to the scenario) and treat AI output as a strong draft to accept, trim, or redirect against those invariants. The most valuable prompts weren't "write this for me" but "here's my design and my constraint — where does it break?" I learned to verify every suggestion against the actual code and tests rather than its plausibility, and that saying *no* to a technically-superior-but-heavier suggestion is itself a design decision worth documenting.

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
