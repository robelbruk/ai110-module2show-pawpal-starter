from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as DateType
from typing import Any, Dict, List, Optional


class Owner:
    def __init__(
        self,
        name: str,
        available_minutes_per_day: int,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences: Dict[str, Any] = preferences or {}

    def update_preferences(self, new_preferences: Dict[str, Any]) -> None:
        """Update owner preferences with new values."""
        pass

    def is_available(self, time_slot: str) -> bool:
        """Return whether owner is available during the given time slot."""
        pass

    def get_daily_capacity(self) -> int:
        """Return total available minutes for the day."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int
    special_needs: List[str] = field(default_factory=list)

    def requires_task_type(self, task_type: str) -> bool:
        """Return True if this pet requires the provided task type."""
        pass

    def get_care_profile(self) -> Dict[str, Any]:
        """Return normalized pet care details used by scheduling logic."""
        pass


@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: str
    task_type: str
    due_window: Optional[str] = None
    is_required: bool = False

    def priority_score(self) -> int:
        """Convert priority label to numeric value."""
        pass

    def fits_in(self, remaining_minutes: int) -> bool:
        """Return True if task duration fits in remaining minutes."""
        pass

    def describe(self) -> str:
        """Return a user-friendly description of the task."""
        pass


@dataclass
class PlanItem:
    task: CareTask
    start_time: str
    end_time: str
    reason: str

    def duration(self) -> int:
        """Return task duration in minutes."""
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize this plan item for display."""
        pass


@dataclass
class DailyPlan:
    date: DateType
    scheduled_items: List[PlanItem] = field(default_factory=list)
    total_minutes: int = 0
    unscheduled_tasks: List[CareTask] = field(default_factory=list)

    def add_item(self, task: CareTask, start_time: str, end_time: str, reason: str) -> None:
        """Append a scheduled plan item and update total minutes."""
        pass

    def remaining_time(self, owner_capacity_minutes: int) -> int:
        """Return remaining minutes given the owner's daily capacity."""
        pass

    def to_display_rows(self) -> List[Dict[str, Any]]:
        """Convert plan items to tabular rows for UI."""
        pass

    def explain(self) -> str:
        """Return a human-readable explanation of the schedule."""
        pass


class Scheduler:
    def __init__(
        self,
        owner: Owner,
        pet: Pet,
        tasks: List[CareTask],
        rules: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks = tasks
        self.rules: Dict[str, Any] = rules or {}

    def generate_plan(self, date: DateType) -> DailyPlan:
        """Generate and return a daily plan from available tasks."""
        pass

    def filter_feasible_tasks(self) -> List[CareTask]:
        """Return tasks that satisfy constraints (time, needs, preferences)."""
        pass

    def sort_or_rank_tasks(self) -> List[CareTask]:
        """Return tasks ordered by priority and scheduling heuristics."""
        pass

    def build_explanations(self, plan: DailyPlan) -> Dict[str, str]:
        """Build explanation strings for scheduled/unscheduled decisions."""
        pass