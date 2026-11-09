"""The uniform line load on a wall header, walked down the stack.

What a published load table's Allowable Total Load (plf) is read against: the takedown on
``HeaderCondition``'s own roofs, floors and walls above, at each one's tributary to this
wall's line. Roof and floor psf are ``typehaus.loads``' (valid at Pg 50 only); walls above are
their resolved assemblies, or ``_WALL_PSF`` where a layer states no density (catlin's gypsum
states none), heaviest per storey. The header's own weight and the short wall over it are left
out: the table's capacity is net of self weight and the rest is a few plf.

A point load or stair ledger in the span is outside a uniform row, so it returns a reason, as
does anything not derivable. Oracle: ``houses/catlin/notes/header_spans_r602_7.md`` §5b.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.loads import (
    FLOOR_DEAD_LOAD_PSF,
    FLOOR_LIVE_LOAD_PSF,
    ROOF_DEAD_PSF,
    ROOF_SNOW_PSF,
)
from typehaus.resolve.assembly_weight import wall_line_plf

_FT = 0.3048
_TOL_M = 0.0127
#: A stud wall sheathed with gypsum both faces (ASCE 7-16 Table C3.1-1a: wood studs 4 psf at
#: 2x4, 5 taken at 2x6, gypsum board 2.2 psf per 1/2" a face, rounded up).
_WALL_PSF = 10.0


@dataclass(frozen=True)
class HeaderLineLoad:
    dead_plf: float
    live_plf: float
    snow_plf: float
    basis: str

    @property
    def governing_plf(self) -> float:
        """The largest ASCE 7-16 §2.4.1 ASD combination of these three."""
        dead, live, snow = self.dead_plf, self.live_plf, self.snow_plf
        return max(dead + live, dead + snow, dead + 0.75 * (live + snow))


def _tributary(c: float, lines: list[float]) -> float | None:
    """Metres of deck this line carries, halfway to its nearest bearing line each side."""
    left = [line for line in lines if line < c - _TOL_M]
    right = [line for line in lines if line > c + _TOL_M]
    if not any(abs(line - c) <= _TOL_M for line in lines) or not (left or right):
        return None
    return ((c - max(left) if left else 0.0) + (min(right) - c if right else 0.0)) / 2


def _roof_tributary(index, tag: str, axis: int, c: float) -> float | None:
    roof = index.plan.by_tag(tag)
    if (0 if roof.ridge_direction == "y" else 1) != axis:
        return None
    lines = [line for ref in roof.bearing_refs
             if (line := index._line_coordinate(ref, axis)) is not None]
    resolved = next((r for r in index.model.roofs if r.tag == tag), None)
    ridge = index._ridge_beam(resolved) if resolved is not None else None
    if ridge is not None:
        lines.append(index._line_coordinate(ridge, axis))
    return _tributary(c, lines)


def _level_tributary(index, tags: list[str], axis: int, c: float) -> float | None:
    """A floor LEVEL's tributary: each side's longest field, so two fields one side of the
    line meeting inside the span (FS-M-EAST / FS-M-NE at D-B-GYM) count once."""
    lefts: list[float] = [0.0]
    rights: list[float] = [0.0]
    for tag in tags:
        floor = index.plan.by_tag(tag)
        if (0 if floor.joists.direction == "x" else 1) != axis:
            return None
        # An outline-less deck fills its storey: the same fallback as ``LoadIndex._floor_width``.
        storey = index.storey_of.get(tag)
        coords = [p.xy_m[axis] for p in floor.outline] or [
            p[axis] for wall in index.walls.values() if wall.storey == storey for p in wall.axis]
        if not coords:
            return None
        lefts.append(max(0.0, c - min(coords)))
        rights.append(max(0.0, max(coords) - c))
    return (max(lefts) + max(rights)) / 2


def header_line_load(ctx, index, wall, condition) -> HeaderLineLoad | str:
    """The derived load on the span ``condition`` describes, or why there is none."""
    if condition.point_loads or condition.strips:
        return "a point load or stair ledger stands in the span"
    (x0, _y0), (x1, _y1) = wall.axis
    axis = 0 if abs(x1 - x0) <= _TOL_M else 1
    c = wall.axis[0][axis]
    dead = live = snow = 0.0
    parts: list[str] = []
    for tag in condition.roofs:
        trib = _roof_tributary(index, tag, axis, c)
        if trib is None:
            return f"{tag} has no tributary to this wall's line"
        feet = trib / _FT
        dead += feet * ROOF_DEAD_PSF
        snow += feet * ROOF_SNOW_PSF
        parts.append(f"{tag} {feet:.1f}'")
    for level, _kind in condition.floors:
        trib = _level_tributary(index, level.split("+"), axis, c)
        if trib is None:
            return f"{level}'s joists do not span to this wall's line"
        feet = trib / _FT
        dead += feet * FLOOR_DEAD_LOAD_PSF
        live += feet * FLOOR_LIVE_LOAD_PSF
        parts.append(f"{level} {feet:.1f}'")
    heaviest: dict[str, float] = {}
    for tag in condition.via:
        upper = index.walls[tag]
        plf, _basis = wall_line_plf(ctx, upper)
        if plf is None:
            plf = _WALL_PSF * (upper.z1_m - upper.z0_m) / _FT
        heaviest[upper.storey] = max(heaviest.get(upper.storey, 0.0), plf)
    walls = sum(heaviest.values())
    dead += walls
    parts.append(f"walls above {walls:.0f} plf")
    return HeaderLineLoad(dead, live, snow, ", ".join(parts))
