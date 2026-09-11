"""Getting the building built: visits, inspections and readiness.

A **leaf**, exactly as ``routing/`` and ``engineering/`` are. It reads the model, the
findings somebody else produced and the owner's authored site state, and it derives what
is ready. It never grades the building — a readiness state that moved when a check moved
would still be a statement about site state, and a ``Finding`` is where facts about the
building live. ``tests/test_schedule_leaf.py`` walks the AST and enforces it.

The commitment underneath the whole package: **readiness is derived, dates are authored**.
Nothing here computes a duration, a lead time or a calendar date, for the same reason
``takeoff/tasks.py`` does not: a fabricated duration is the number a schedule gets built
on, and there is nothing in a geometry model that implies one.
"""

from __future__ import annotations

from typehaus.schedule.model import (
    AUTHORITIES,
    INSPECTION_READINESS,
    VISIT_READINESS,
    VISIT_STATUSES,
    Applicability,
    Board,
    Constraint,
    HandoffItem,
    InspectionReadiness,
    Milestone,
    Prerequisite,
    Visit,
    VisitReadiness,
)

__all__ = [
    "AUTHORITIES", "INSPECTION_READINESS", "VISIT_READINESS", "VISIT_STATUSES",
    "Applicability", "Board", "Constraint", "HandoffItem", "InspectionReadiness",
    "Milestone", "Prerequisite", "Visit", "VisitReadiness",
]
