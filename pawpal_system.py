from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from datetime import date as DateType, timedelta
from typing import Any, Dict, List, Optional, Tuple

_TIME_HHMM = re.compile(r"^(\d{1,2}):(\d{2})$")

_DAY_PART_ORDER = {
    "morning": 0,
    "afternoon": 1,
    "evening": 2,
    "night": 3,
}


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes_per_day: int,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize an owner with availability, preferences, and pets."""
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences: Dict[str, Any] = preferences or {}
        self.pets: List[Pet] = []

    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update owner preferences with new values."""
        self.preferences.update(new_preferences)

    def is_available(self, time_slot: str) -> bool:
        """Return whether owner is available during the given time slot."""
        availability = self.preferences.get("availability")
        if availability is None:
            return True
        if isinstance(availability, dict):
            return bool(availability.get(time_slot, True))
        if isinstance(availability, (list, tuple, set)):
            return time_slot in availability
        return bool(availability)

    def get_daily_capacity(self) -> int:
        """Return total available minutes for the day."""
        return max(0, int(self.available_minutes_per_day))

    def add_pet(self, pet: Pet) -> None:
        """Attach a pet to this owner profile."""
        if pet not in self.pets:
            self.pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets linked to this owner."""
        return list(self.pets)

    def get_all_tasks(self) -> List[CareTask]:
        """Collect all tasks from every pet."""
        all_tasks: List[CareTask] = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks

    def filter_tasks(
        self,
        *,
        is_completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[CareTask]:
        """Filter all tasks across this owner's pets.

        Applies :func:`filter_care_tasks` to the union of every pet's task list.
        ``is_completed`` and ``pet_name`` are optional; unset filters are skipped.
        Pet name matching is case-insensitive.
        """
        return filter_care_tasks(
            self.get_all_tasks(),
            is_completed=is_completed,
            pet_name=pet_name,
        )


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: List[str] = field(default_factory=list)
    tasks: List[CareTask] = field(default_factory=list)

    def requires_task_type(self, task_type: str) -> bool:
        """Return True if this pet requires the provided task type."""
        normalized = task_type.strip().lower()
        return any(need.strip().lower() == normalized for need in self.special_needs)

    def get_care_profile(self) -> Dict[str, Any]:
        """Return normalized pet care details used by scheduling logic."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "special_needs": list(self.special_needs),
            "task_count": len(self.tasks),
        }

    def add_task(self, task: CareTask) -> None:
        """Add a care task to this pet."""
        if task.pet_name is None:
            task.pet_name = self.name
        self.tasks.append(task)

    def get_tasks(self) -> List[CareTask]:
        """Return this pet's tasks."""
        return list(self.tasks)

    def filter_tasks(
        self,
        *,
        is_completed: Optional[bool] = None,
        pet_name: Optional[str] = None,
    ) -> List[CareTask]:
        """Filter this pet's tasks.

        Delegates to :func:`filter_care_tasks` on :meth:`get_tasks`. Unset filters
        are not applied; ``pet_name`` matches ``task.pet_name`` case-insensitively.
        """
        return filter_care_tasks(
            self.get_tasks(),
            is_completed=is_completed,
            pet_name=pet_name,
        )


def filter_care_tasks(
    tasks: List[CareTask],
    *,
    is_completed: Optional[bool] = None,
    pet_name: Optional[str] = None,
) -> List[CareTask]:
    """Linear scan: keep tasks that pass optional completion and pet-name predicates.

    Algorithm: single pass over ``tasks`` in order. If ``is_completed`` is set,
    drop tasks whose flag differs. If ``pet_name`` is set, normalize it and
    ``task.pet_name`` to lowercase for comparison; tasks with no ``pet_name``
    never match a non-empty ``pet_name`` filter.

    Args:
        tasks: Input list (not copied unless building the result).
        is_completed: If given, only tasks with this completion flag are kept.
        pet_name: If given, only tasks whose ``pet_name`` matches (case-insensitive).

    Returns:
        A new list containing tasks that satisfy all provided filters.
    """
    pet_key = pet_name.strip().lower() if pet_name else None
    out: List[CareTask] = []
    for task in tasks:
        if is_completed is not None and task.is_completed != is_completed:
            continue
        if pet_key is not None:
            task_pet = (task.pet_name or "").strip().lower()
            if task_pet != pet_key:
                continue
        out.append(task)
    return out


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    task_type: str
    pet_name: Optional[str] = None
    due_window: Optional[str] = None
    time: Optional[str] = None
    is_required: bool = False
    frequency: str = "daily"
    due_date: Optional[DateType] = None
    is_completed: bool = False

    def priority_score(self) -> int:
        """Convert priority label to numeric value."""
        priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4,
        }
        return priority_map.get(self.priority.strip().lower(), 1)

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if task duration fits in remaining minutes."""
        return self.duration_minutes <= remaining_minutes

    def describe(self) -> str:
        """Return a user-friendly description of the task."""
        parts = [f"{self.title} ({self.duration_minutes} min)"]
        if self.pet_name:
            parts.append(f"for {self.pet_name}")
        if self.time:
            parts.append(f"at {self.time}")
        elif self.due_window:
            parts.append(f"during {self.due_window}")
        parts.append(f"[{self.priority}]")
        if self.due_date:
            parts.append(f"due {self.due_date.isoformat()}")
        if self.is_completed:
            parts.append("completed")
        return " ".join(parts)

    def mark_complete(
        self,
        *,
        pet: Optional["Pet"] = None,
        as_of: Optional[DateType] = None,
    ) -> Optional["CareTask"]:
        """Mark this task complete and optionally queue the next recurring instance.

        Idempotent: if already completed, returns ``None`` without side effects.

        For ``frequency`` in ``daily`` / ``weekly``, computes the next due date as
        ``as_of`` (or today's date) plus :class:`datetime.timedelta`
        of one or seven days, clones this task with :func:`dataclasses.replace`,
        clears completion, and sets ``due_date``. If ``pet`` is given, appends the
        new task via :meth:`Pet.add_task`.

        Other frequencies only flip ``is_completed``; no clone is created.

        Returns:
            The new :class:`CareTask` when a recurring next instance is created,
            otherwise ``None``.
        """
        if self.is_completed:
            return None
        self.is_completed = True
        freq = self.frequency.strip().lower()
        if freq not in ("daily", "weekly"):
            return None
        completion_day = as_of if as_of is not None else DateType.today()
        delta = timedelta(days=1 if freq == "daily" else 7)
        next_due = completion_day + delta
        new_task = replace(
            self,
            is_completed=False,
            due_date=next_due,
        )
        if pet is not None:
            pet.add_task(new_task)
        return new_task

    def reset_completion(self) -> None:
        """Mark this task as not completed."""
        self.is_completed = False


def _task_time_sort_key(task: CareTask) -> Tuple[int, int, str]:
    """Build a tuple key for ordering tasks by time-of-day for :func:`sorted`.

    Uses ``task.time`` or ``due_window`` as the time signal. Returns a 3-tuple
    ``(tier, primary, tiebreak)`` so that:

    * **Clock times** ``HH:MM`` (tier ``0``) sort by minutes from midnight first.
    * **Named day parts** (tier ``1``), e.g. *morning*, use :data:`_DAY_PART_ORDER`;
      unknown labels get a middle rank ``50``.
    * **Missing** time (tier ``2``) sort last.
    * **tiebreak** is the lowercased label string for stable ordering within a tier.

    Lexicographic comparison on this tuple implements the desired ordering.
    """
    raw = (task.time or task.due_window or "").strip()
    if not raw:
        return (2, 0, "")
    lower = raw.lower()
    m = _TIME_HHMM.match(lower)
    if m:
        mins = int(m.group(1)) * 60 + int(m.group(2))
        return (0, mins, lower)
    part = _DAY_PART_ORDER.get(lower, 50)
    return (1, part, lower)


@dataclass
class PlanItem:
    task: CareTask
    start_time: str
    end_time: str
    reason: str

    def duration(self) -> int:
        """Return task duration in minutes."""
        return self.task.duration_minutes

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this plan item for display."""
        return {
            "task": self.task.title,
            "pet": self.task.pet_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_minutes": self.duration(),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ScheduleConflict:
    """Two scheduled items whose time ranges overlap (same or different pet)."""

    first: PlanItem
    second: PlanItem


@dataclass
class DailyPlan:
    date: DateType
    scheduled_items: List[PlanItem] = field(default_factory=list)
    unscheduled_tasks: List[CareTask] = field(default_factory=list)

    def add_item(self, task: CareTask, start_time: str, end_time: str, reason: str) -> None:
        """Append a scheduled plan item."""
        self.scheduled_items.append(
            PlanItem(task=task, start_time=start_time, end_time=end_time, reason=reason)
        )

    def total_minutes(self) -> int:
        """Return the total scheduled minutes for this plan."""
        return sum(item.duration() for item in self.scheduled_items)

    def remaining_time(self, owner_capacity_minutes: int) -> int:
        """Return remaining minutes given the owner's daily capacity."""
        return max(0, owner_capacity_minutes - self.total_minutes())

    def to_display_rows(self) -> List[Dict[str, Any]]:
        """Convert plan items to tabular rows for UI."""
        return [item.to_dict() for item in self.scheduled_items]

    def explain(self) -> str:
        """Return a human-readable explanation of the schedule."""
        lines: List[str] = [f"Plan for {self.date.isoformat()}:"]
        if not self.scheduled_items:
            lines.append("No tasks were scheduled.")
        else:
            for item in self.scheduled_items:
                lines.append(
                    f"- {item.start_time}-{item.end_time}: {item.task.title} ({item.reason})"
                )
        if self.unscheduled_tasks:
            lines.append("Unscheduled tasks:")
            for task in self.unscheduled_tasks:
                lines.append(f"- {task.title}")
        return "\n".join(lines)


class Scheduler:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        tasks: List[CareTask],
        rules: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize the scheduler with owner context, pet, tasks, and rules."""
        self.owner = owner
        self.pet = pet
        self.tasks = tasks
        self.rules: Dict[str, Any] = rules or {}

    def generate_plan(self, date: DateType) -> DailyPlan:
        """Greedy sequential schedule: one owner timeline, earliest slot first.

        Algorithm:

        #. Rank tasks with :meth:`sort_or_rank_tasks`.
        #. Walk in order; track remaining owner capacity and a running clock
           starting at ``rules['day_start']`` (default ``08:00``).
        #. For each task, if its duration fits in ``remaining``, append a
           :class:`PlanItem` from ``current_time`` to ``current_time + duration``,
           subtract minutes, advance the clock; otherwise push the task to
           ``unscheduled_tasks``.

        Does not split tasks or run parallel tracks; complexity is O(n) in the
        number of ranked tasks.
        """
        plan = DailyPlan(date=date)
        ranked_tasks = self.sort_or_rank_tasks()
        remaining = self.owner.get_daily_capacity()
        current_time = self.rules.get("day_start", "08:00")

        for task in ranked_tasks:
            if task.fits_in(remaining):
                end_time = self._add_minutes(current_time, task.duration_minutes)
                reason = "High-priority task that fits current time budget."
                plan.add_item(task, current_time, end_time, reason)
                remaining -= task.duration_minutes
                current_time = end_time
            else:
                plan.unscheduled_tasks.append(task)

        return plan

    def filter_feasible_tasks(self) -> List[CareTask]:
        """Collect tasks that can be considered for scheduling today.

        Algorithm: gather tasks from :meth:`Owner.get_all_tasks`, or fall back to
        ``self.tasks`` if empty. Drop any task that is completed, whose
        ``task_type`` is listed in ``owner.preferences['exclude_task_types']``,
        or whose ``due_window`` is set and the owner is unavailable for that slot
        (:meth:`Owner.is_available`).

        Returns:
            Feasible tasks in no particular order (sorting is done in
            :meth:`sort_or_rank_tasks`).
        """
        all_tasks = self.owner.get_all_tasks()
        if not all_tasks:
            all_tasks = list(self.tasks)

        excluded_types = set(self.owner.preferences.get("exclude_task_types", []))
        feasible: List[CareTask] = []
        for task in all_tasks:
            if task.is_completed:
                continue
            if task.task_type in excluded_types:
                continue
            if task.due_window and not self.owner.is_available(task.due_window):
                continue
            feasible.append(task)
        return feasible

    def sort_or_rank_tasks(self) -> List[CareTask]:
        """Return feasible tasks in deterministic scheduling order.

        Calls :meth:`filter_feasible_tasks`, then :func:`sorted` with a composite
        key (tuple comparison, ascending):

        #. Time key from :func:`_task_time_sort_key` (time-of-day / day-part).
        #. Required tasks before optional (``0`` vs ``1``).
        #. Higher :meth:`CareTask.priority_score` first (negated).
        #. Shorter ``duration_minutes`` first.
        #. Title, case-insensitive, for stable ties.

        Returns:
            A new list; input feasible set is not mutated.
        """
        feasible_tasks = self.filter_feasible_tasks()
        return sorted(
            feasible_tasks,
            key=lambda task: (
                _task_time_sort_key(task),
                0 if task.is_required else 1,
                -task.priority_score(),
                task.duration_minutes,
                task.title.lower(),
            ),
        )

    def build_explanations(self, plan: DailyPlan) -> Dict[str, str]:
        """Build explanation strings for scheduled/unscheduled decisions."""
        explanations: Dict[str, str] = {}
        for item in plan.scheduled_items:
            explanations[item.task.title] = item.reason
        for task in plan.unscheduled_tasks:
            explanations[task.title] = "Not scheduled due to limited remaining time."
        return explanations

    def detect_time_conflicts(self, plan: DailyPlan) -> List[ScheduleConflict]:
        """Find all unordered pairs of overlapping scheduled intervals.

        Algorithm: brute-force over ``plan.scheduled_items`` — for each pair
        ``i < j``, convert both items to minute intervals via
        :meth:`_plan_item_interval_minutes` and test overlap with
        :meth:`_plan_items_time_overlap`. Pet identity is ignored; same-pet and
        cross-pet overlaps are both reported.

        Overlap rule: half-open intervals ``[start, end)`` in minutes from
        midnight. Touching boundaries (end of A equals start of B) do **not**
        overlap. If ``end <= start`` on an item, the span is treated as crossing
        midnight (end adjusted by 24 hours).

        Time complexity: O(n²) in the number of scheduled items; each pair does
        constant-time arithmetic after parsing times.

        Returns:
            A list of :class:`ScheduleConflict` records, one per overlapping pair.
        """
        items = plan.scheduled_items
        conflicts: List[ScheduleConflict] = []
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if self._plan_items_time_overlap(items[i], items[j]):
                    conflicts.append(ScheduleConflict(first=items[i], second=items[j]))
        return conflicts

    def has_time_conflicts(self, plan: DailyPlan) -> bool:
        """Return whether :meth:`detect_time_conflicts` would return a non-empty list.

        Equivalent to ``bool(self.detect_time_conflicts(plan))`` but kept for a
        clear boolean API at call sites.
        """
        return bool(self.detect_time_conflicts(plan))

    def scheduling_conflict_warning(self, plan: DailyPlan) -> Optional[str]:
        """Summarize overlap problems for display; safe when times are malformed.

        Calls :meth:`detect_time_conflicts` and formats a short human-readable
        message listing the conflict count and one example pair (titles, pets,
        time ranges). If multiple pairs exist, appends a count of additional
        overlaps.

        Catches :exc:`ValueError`, :exc:`TypeError`, and :exc:`AttributeError`
        from the conflict pipeline (e.g. unparsable ``HH:MM``) and returns a
        generic warning string instead of raising—suitable for UI layers that
        must not crash on bad data.

        Returns:
            ``None`` if there are no overlaps, otherwise a non-empty warning string.
        """
        try:
            conflicts = self.detect_time_conflicts(plan)
        except (ValueError, TypeError, AttributeError):
            return (
                "Warning: could not verify the schedule for overlapping times "
                "(check that start and end times use HH:MM)."
            )
        if not conflicts:
            return None
        n = len(conflicts)
        c0 = conflicts[0]
        a = c0.first.task.title
        b = c0.second.task.title
        pa = c0.first.task.pet_name or "pet"
        pb = c0.second.task.pet_name or "pet"
        base = (
            f"Warning: {n} overlapping time slot(s). "
            f"Example: “{a}” ({pa}) overlaps “{b}” ({pb}) "
            f"({c0.first.start_time}–{c0.first.end_time} vs {c0.second.start_time}–{c0.second.end_time})."
        )
        if n > 1:
            return f"{base} (+{n - 1} other overlap(s).)"
        return base

    def _hhmm_to_minutes(self, hhmm: str) -> int:
        """Parse a ``HH:MM`` string into minutes from midnight (0–1439 typical).

        Expects at least one colon separating hours and minutes. Used by interval
        helpers for conflict detection; invalid strings raise (caught by
        :meth:`scheduling_conflict_warning`).
        """
        hours_s, mins_s = hhmm.strip().split(":", maxsplit=1)
        return int(hours_s) * 60 + int(mins_s)

    def _plan_item_interval_minutes(self, item: PlanItem) -> Tuple[int, int]:
        """Convert a plan row to integer minute bounds for interval logic.

        Parses ``item.start_time`` and ``item.end_time`` via :meth:`_hhmm_to_minutes`.
        If the end is at or before the start (including midnight wrap), adds
        ``24 * 60`` to ``end`` so the interval is a forward span on the line.

        Returns:
            ``(start_minutes, end_minutes)`` suitable for :meth:`_plan_items_time_overlap`.
        """
        start = self._hhmm_to_minutes(item.start_time)
        end = self._hhmm_to_minutes(item.end_time)
        if end <= start:
            end += 24 * 60
        return (start, end)

    def _plan_items_time_overlap(self, a: PlanItem, b: PlanItem) -> bool:
        """Return whether two intervals overlap using half-open ``[start, end)`` math.

        For ``(sa, ea)`` and ``(sb, eb)`` from :meth:`_plan_item_interval_minutes`,
        overlap is ``sa < eb and sb < ea`` (standard interval intersection test).
        """
        sa, ea = self._plan_item_interval_minutes(a)
        sb, eb = self._plan_item_interval_minutes(b)
        return sa < eb and sb < ea

    def _add_minutes(self, start_time: str, minutes: int) -> str:
        """Add minutes to HH:MM time strings."""
        hours, mins = start_time.split(":")
        total = int(hours) * 60 + int(mins) + minutes
        total %= 24 * 60
        end_hours = total // 60
        end_mins = total % 60
        return f"{end_hours:02d}:{end_mins:02d}"