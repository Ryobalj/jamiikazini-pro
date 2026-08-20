# syllabus/services/master_timetable_generator.py
#
# Auto-generates a conflict-free school master timetable: assigns every
# teacher-subject-class combination on a roster to day/period slots
# without ever double-booking a teacher (or a class) at the same
# day+period. Plain Python/dataclasses, no external CSP solver - a
# school's staff is small (tens of teachers, a handful of classes, ~45
# non-break slots/week), and the input already describes a real working
# school, so a greedy-with-local-backtrack-and-randomized-restart
# approach (same style as scheme_timeline_builder.py) is both sufficient
# and easy to reason about/debug.

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from django.db import transaction

from syllabus.models.master_timetable import (
    MasterTimetableRoster,
    TimetablePeriodSlot,
    TimetableSlot,
    TimetableTeacherAssignment,
)
from syllabus.models.timetable import TimeTable

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 20

# (day_of_week, period_slot_id)
SlotKey = Tuple[int, str]


@dataclass
class DemandUnit:
    assignment_id: str
    teacher_id: str
    class_level_id: str
    periods_needed: int


@dataclass
class UnplacedDemand:
    assignment_id: str
    teacher_name: str
    subject_name: str
    class_level_name: str
    periods_short: int


@dataclass
class GenerationResult:
    placed_count: int = 0
    unplaced: List[UnplacedDemand] = field(default_factory=list)

    @property
    def is_complete(self) -> bool:
        return not self.unplaced


class MasterTimetableGenerator:
    """Generates TimetableSlot rows (source=GENERATED) for a roster's
    TimetableTeacherAssignments, without disturbing any existing
    source=MANUAL rows (whole-school activity blocks, hand-fixed cells -
    those are placed by the roster owner before generating and are
    always treated as already-occupied)."""

    def __init__(self, roster: MasterTimetableRoster):
        self.roster = roster
        self.days = [d for d, _ in TimeTable.DayOfWeek.choices]

    def generate(self) -> GenerationResult:
        period_slots = list(
            self.roster.period_slots.filter(is_break=False).order_by("order")
        )
        if not period_slots:
            return GenerationResult(unplaced=[])

        demand = self._build_demand()
        if not demand:
            return GenerationResult(placed_count=0, unplaced=[])

        manual_occupancy = self._load_manual_occupancy()

        best_result = None
        best_placements: Optional[List[Tuple[str, int, str]]] = None  # (assignment_id, day, period_slot_id)

        rng = random.Random(f"{self.roster.id}")
        for attempt in range(MAX_ATTEMPTS):
            placements, unplaced = self._attempt_once(demand, period_slots, manual_occupancy, rng)
            placed_count = sum(len(v) for v in placements.values())
            if not unplaced:
                best_placements = self._flatten(placements)
                best_result = GenerationResult(placed_count=placed_count, unplaced=[])
                break
            if best_result is None or placed_count > best_result.placed_count:
                best_placements = self._flatten(placements)
                best_result = GenerationResult(placed_count=placed_count, unplaced=unplaced)

        self._persist(best_placements or [])
        return best_result or GenerationResult()

    # ------------------------------------------------------------------
    # Demand
    # ------------------------------------------------------------------
    def _build_demand(self) -> List[DemandUnit]:
        assignments = (
            self.roster.assignments
            .select_related("teacher", "subject_version", "subject_version__subject", "subject_version__class_level")
        )
        demand = [
            DemandUnit(
                assignment_id=str(a.id),
                teacher_id=str(a.teacher_id),
                class_level_id=str(a.subject_version.class_level_id),
                periods_needed=a.effective_periods_per_week,
            )
            for a in assignments
        ]
        # Most-constrained-first: schedule the heaviest loads before the
        # lighter ones so they have the most free slots to choose from.
        demand.sort(key=lambda d: d.periods_needed, reverse=True)
        return demand

    # ------------------------------------------------------------------
    # Manual (already-placed) occupancy - never overwritten
    # ------------------------------------------------------------------
    def _load_manual_occupancy(self) -> Dict[str, Set]:
        """Returns {'teacher': {(teacher_id, day, slot_id)}, 'class': {(class_level_id, day, slot_id)}}
        seeded from every existing TimetableSlot (both MANUAL and any
        previously-GENERATED rows still on the roster at call time -
        the caller is expected to have already decided whether to keep
        or clear prior GENERATED rows before invoking generate())."""
        teacher_busy: Set[Tuple[str, int, str]] = set()
        class_busy: Set[Tuple[str, int, str]] = set()

        existing = self.roster.slots.select_related("assignment").filter(
            source=TimetableSlot.Source.MANUAL
        )
        for slot in existing:
            key_period = str(slot.period_slot_id)
            if slot.class_level_id is None:
                # Whole-school block: reserves this day+period for every
                # class, and for the teacher (if any) running it.
                for cl_id in self._all_class_level_ids():
                    class_busy.add((cl_id, slot.day_of_week, key_period))
            else:
                class_busy.add((str(slot.class_level_id), slot.day_of_week, key_period))
            if slot.assignment_id:
                teacher_busy.add((str(slot.assignment.teacher_id), slot.day_of_week, key_period))

        return {"teacher": teacher_busy, "class": class_busy}

    def _all_class_level_ids(self) -> Set[str]:
        return {
            str(cl_id)
            for cl_id in self.roster.assignments.values_list(
                "subject_version__class_level_id", flat=True
            ).distinct()
        }

    # ------------------------------------------------------------------
    # One generation attempt
    # ------------------------------------------------------------------
    def _attempt_once(
        self,
        demand: List[DemandUnit],
        period_slots: List[TimetablePeriodSlot],
        manual_occupancy: Dict[str, Set],
        rng: random.Random,
    ) -> Tuple[Dict[str, List[Tuple[int, str]]], List[UnplacedDemand]]:
        teacher_busy: Set[Tuple[str, int, str]] = set(manual_occupancy["teacher"])
        class_busy: Set[Tuple[str, int, str]] = set(manual_occupancy["class"])
        teacher_days_used: Dict[str, Set[int]] = {}
        class_period_load: Dict[Tuple[str, int], int] = {}

        placements: Dict[str, List[Tuple[int, str]]] = {d.assignment_id: [] for d in demand}
        unplaced: List[UnplacedDemand] = []

        all_slots = [(day, str(ps.id)) for day in self.days for ps in period_slots]

        for unit in demand:
            placed_for_unit = 0
            attempts_this_unit = 0
            local_teacher_busy = set()
            local_class_busy = set()

            for _ in range(unit.periods_needed):
                candidates = [
                    (day, slot_id) for day, slot_id in all_slots
                    if (unit.teacher_id, day, slot_id) not in teacher_busy
                    and (unit.class_level_id, day, slot_id) not in class_busy
                    and (unit.teacher_id, day, slot_id) not in local_teacher_busy
                    and (unit.class_level_id, day, slot_id) not in local_class_busy
                ]
                if not candidates:
                    break

                # Prefer a day this teacher/class pair hasn't used yet
                # (spread across the week), then the lightest-loaded
                # period slot for this class (balance within a day).
                used_days = teacher_days_used.get(unit.teacher_id, set())
                candidates.sort(
                    key=lambda c: (
                        c[0] in used_days,
                        class_period_load.get((unit.class_level_id, c[0]), 0),
                        rng.random(),
                    )
                )
                day, slot_id = candidates[0]

                teacher_busy.add((unit.teacher_id, day, slot_id))
                class_busy.add((unit.class_level_id, day, slot_id))
                local_teacher_busy.add((unit.teacher_id, day, slot_id))
                local_class_busy.add((unit.class_level_id, day, slot_id))
                teacher_days_used.setdefault(unit.teacher_id, set()).add(day)
                class_period_load[(unit.class_level_id, day)] = (
                    class_period_load.get((unit.class_level_id, day), 0) + 1
                )
                placements[unit.assignment_id].append((day, slot_id))
                placed_for_unit += 1

            if placed_for_unit < unit.periods_needed:
                unplaced.append(
                    UnplacedDemand(
                        assignment_id=unit.assignment_id,
                        teacher_name="",
                        subject_name="",
                        class_level_name="",
                        periods_short=unit.periods_needed - placed_for_unit,
                    )
                )

        return placements, self._enrich_unplaced(unplaced)

    def _enrich_unplaced(self, unplaced: List[UnplacedDemand]) -> List[UnplacedDemand]:
        if not unplaced:
            return unplaced
        assignment_ids = [u.assignment_id for u in unplaced]
        assignments = {
            str(a.id): a
            for a in TimetableTeacherAssignment.objects.filter(id__in=assignment_ids)
            .select_related("teacher", "subject_version__subject", "subject_version__class_level")
        }
        for u in unplaced:
            a = assignments.get(u.assignment_id)
            if a:
                u.teacher_name = a.teacher.full_name
                u.subject_name = a.subject_version.subject.name
                u.class_level_name = a.subject_version.class_level.name
        return unplaced

    @staticmethod
    def _flatten(placements: Dict[str, List[Tuple[int, str]]]) -> List[Tuple[str, int, str]]:
        return [
            (assignment_id, day, slot_id)
            for assignment_id, entries in placements.items()
            for day, slot_id in entries
        ]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _persist(self, placements: List[Tuple[str, int, str]]) -> None:
        assignments = {
            str(a.id): a
            for a in self.roster.assignments.select_related("subject_version__class_level")
        }
        with transaction.atomic():
            self.roster.slots.filter(source=TimetableSlot.Source.GENERATED).delete()
            new_rows = [
                TimetableSlot(
                    roster=self.roster,
                    day_of_week=day,
                    period_slot_id=slot_id,
                    class_level_id=assignments[assignment_id].subject_version.class_level_id,
                    assignment_id=assignment_id,
                    source=TimetableSlot.Source.GENERATED,
                )
                for assignment_id, day, slot_id in placements
                if assignment_id in assignments
            ]
            TimetableSlot.objects.bulk_create(new_rows)
        logger.info(f"Master timetable generated: roster={self.roster.id}, placed={len(new_rows)}")
