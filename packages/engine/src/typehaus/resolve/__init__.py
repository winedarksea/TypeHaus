"""Resolve stage — validated PlanModel to the ResolvedModel IR (→ 11)."""

from __future__ import annotations

from typehaus.resolve.model import (
    BoundaryCondition,
    FramedMember,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedRoom,
    ResolvedRoof,
    ResolvedSolid,
    ResolvedStair,
    ResolvedWall,
    StackEdge,
)
from typehaus.resolve.pipeline import resolve

__all__ = [
    "resolve", "ResolvedModel", "ResolvedWall", "ResolvedLayer", "ResolvedOpening",
    "ResolvedRoom", "ResolvedSolid", "ResolvedRoof", "ResolvedStair", "FramedMember",
    "BoundaryCondition", "StackEdge",
]
