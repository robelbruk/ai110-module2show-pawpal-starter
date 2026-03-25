# PawPal+ Project Reflection

## 1. System Design
- Core User Actions
    - Enter basic owner + pet info
    - Add/edit care tasks (with at least duration and prioirty)
    - Generate a daily schedule/plan based on constraints and priorities

**a. Initial design**

- Briefly describe your initial UML design.
  - My initial UML used six classes: `Owner`, `Pet`, `CareTask`, `Scheduler`, `DailyPlan`, and `PlanItem`. I separated "data holder" classes (`Pet`, `CareTask`, `PlanItem`) from orchestration/output classes (`Scheduler`, `DailyPlan`) so scheduling logic stayed centralized instead of scattered.
- What classes did you include, and what responsibilities did you assign to each?
  - `Owner`: stores owner-level constraints (name, available daily minutes, preferences) and provides availability/capacity helpers.
  - `Pet`: stores pet profile data (name, species, age, special needs) and exposes methods that describe care requirements.
  - `CareTask`: represents one care action with duration, priority, type, and scheduling metadata.
  - `Scheduler`: orchestrates filtering feasible tasks, ranking tasks, and generating a `DailyPlan`.
  - `DailyPlan`: stores one day's output, including scheduled and unscheduled tasks, plus display/explanation helpers.
  - `PlanItem`: models one scheduled entry (task + time range + reason) so each scheduled decision is explicit and explainable.

**b. Design changes**
- Did your design change during implementation?
    - Yes. I made two design updates after reviewing the skeleton
- If yes, describe at least one change and why you made it.
    - I added `Owner.pets` and an `add_pet()` method to explicitly model the owner-to-pet relationship instead of assuming a single pet forever.
    - I added `CareTask.pet_name` so tasks can be tied to a specific pet, which prevents ambiguity if the app expands to multi-pet scheduling.
    - I removed `DailyPlan.total_minutes` as a stored field and replaced it with a `total_minutes()` method to avoid state drift between `scheduled_items` and a manually maintained total.
    - These changes make the model safer to evolve and reduce avoidable consistency bugs in scheduling logic.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- **Describe one tradeoff your scheduler makes.**

  - The main tradeoff is **sequential single-line scheduling**: `generate_plan` walks the ranked task list and places each task **immediately after** the previous one on **one** owner timeline (`day_start` → …). It does not allocate **parallel** tracks (e.g., two pets at once with help, or overlapping real-world windows). That keeps the implementation small and the output easy to read, but it **forces a strict order** and may **serialize** work that could overlap in practice. (Note: **conflict detection** is different—it compares **intervals** (`start`–`end`) and flags **overlapping durations**, not “exact same timestamp” only; half-open ranges mean **back-to-back** slots are not treated as conflicts. The default generator never produces overlaps, so that check is mainly for **manual or merged** plans.)

- **Why is that tradeoff reasonable for this scenario?**
  - For this project, **one owner** and **one daily minute budget** are the core constraints; a single ordered queue matches that story and is straightforward to test and print. A richer model (parallel resources, travel time, multiple caregivers) would be better for production but is heavier than needed here.

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
