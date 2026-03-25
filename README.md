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

## Smarter Scheduling

The core logic in `pawpal_system.py` goes beyond a simple list of tasks:

- **Ranking** — Tasks are sorted for planning by time slot (`time` / `due_window`, including clock-style `HH:MM` and day parts), then required vs optional, priority, duration, and title for stable ties.
- **Filtering** — `filter_care_tasks` and `Owner` / `Pet` `filter_tasks` narrow tasks by completion status and pet name (case-insensitive) without mutating the originals.
- **Recurring care** — Marking a `daily` or `weekly` task complete can append the next occurrence with a `due_date` computed with `timedelta` (pass `pet=` to store it on the pet). Completed tasks are skipped when building a plan.
- **Conflict awareness** — `Scheduler.detect_time_conflicts` finds overlapping scheduled intervals (half-open ranges so back-to-back slots are fine). `scheduling_conflict_warning` returns a short UI-safe string, or `None` if there are no overlaps.

Run `python main.py` for a terminal demo that exercises sorting, filtering, recurrence, and a sample overlap warning.

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
