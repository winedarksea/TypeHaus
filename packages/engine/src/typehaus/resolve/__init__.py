"""Resolve stage — validated PlanModel to the ResolvedModel IR (→ 11)."""

from __future__ import annotations

from typehaus.resolve.model import (
    BoundaryCondition,
    FramedMember,
    ResolvedCanvasObject,
    ResolvedFloorHeat,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedRoof,
    ResolvedRoom,
    ResolvedSolid,
    ResolvedStair,
    ResolvedWall,
    StackEdge,
)
from typehaus.resolve.pipeline import resolve, resolve_preview

__all__ = [
    "resolve", "resolve_preview", "ResolvedModel", "ResolvedWall", "ResolvedLayer",
    "ResolvedOpening",
    "ResolvedRoom", "ResolvedSolid", "ResolvedRoof", "ResolvedStair", "ResolvedFloorHeat",
    "ResolvedCanvasObject", "FramedMember",
    "BoundaryCondition", "StackEdge",
]
