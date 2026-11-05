"""The derived soffit panel under a roof overhang, and its corner closure (→ B2).

The soffit is the one roof-edge piece that does not tile a rake corner the ``mitred_span``
way. Fascia boards lap there, eave over rake; a soffit cannot. A level eave panel run through
the corner square leaves the sloped rake panel starting above it, with an open riser. So
at a corner whose rake closes a soffit, the rake owns the square and slopes from the eave
fascia, and the eave panel stops at the gable wall's face. The vertical triangle left
between them, on that face line, is closed by a return cut from the same stock.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from typehaus.model.trim import EaveTrim
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_edge_geometry import (
    CLOSURE_TOLERANCE_M,
    EdgeRun,
    cut_span,
    wall_face_inset,
)

_VENTED = "eave-trim:vented-soffit"
# Same vented panel, but outboard of the sheathed gable truss and climbing to the ridge: it
# feeds no eave-to-ridge channel and is not R806.2 "lower portion" intake.
_RAKE_VENTED = "eave-trim:rake-soffit"
_RETURN = "eave-trim:soffit-return"


class SoffitRun(NamedTuple):
    """An edge run that closes a soffit, with its two faces along the outward normal."""

    run: EdgeRun
    trim: EaveTrim
    outer: float  # inner face of the innermost fascia board (or the roof edge)
    inset: float  # the wall's outermost face

    @property
    def drop(self) -> float:
        """The panel's underside below the roof edge: the fascia's foot, or its own depth."""
        return self.trim.fascia[0].depth.meters if self.trim.fascia else self.thickness

    @property
    def thickness(self) -> float:
        return self.trim.soffit_thickness.meters


def soffit_runs(
    runs: tuple[EdgeRun, ...], trims: dict[str, EaveTrim], walls: tuple[ResolvedWall, ...],
) -> dict[str, SoffitRun]:
    """Every run in ``trims`` (the roof's unabutted edges) that has an overhang to close."""
    out: dict[str, SoffitRun] = {}
    for run in runs:
        trim = trims.get(run.key)
        if trim is None or trim.soffit_thickness is None:
            continue
        inset = wall_face_inset(run.normal, run.p0, walls)
        outer = -trim.fascia[0].thickness.meters if trim.fascia else 0.0
        if outer - inset > CLOSURE_TOLERANCE_M:  # a flush edge has no underside to close
            out[run.key] = SoffitRun(run, trim, outer, inset)
    return out


def soffit_members(
    roof: ResolvedRoof, key: str, soffits: dict[str, SoffitRun],
) -> tuple[FramedMember, ...]:
    """The panel closing run ``key``'s overhang underside, plus an eave's corner returns."""
    this = soffits.get(key)
    if this is None:
        return ()
    run = this.run
    if run.is_eave:
        rakes = (_partner(soffits, run, run.p0), _partner(soffits, run, run.p1))
        # A rake with its own soffit owns the corner: stop at its inner (wall) face.
        start, end = (-rake.inset if rake is not None else -this.outer for rake in rakes)
    else:
        corner = run.p0 if run.corner_at_p0 else run.p1
        eave = _partner(soffits, run, corner)
        # Into the corner, to the eave panel's outer face (the eave fascia's inner face).
        cut = -eave.outer if eave is not None else -this.inset
        start, end = (cut if run.corner_at_p0 else 0.0, cut if run.corner_at_p1 else 0.0)
    panel = _panel(roof, this, start, end)
    if panel is None or not run.is_eave:
        return () if panel is None else (panel,)
    returns = []
    for index, (rake, corner, sign) in enumerate(((rakes[0], run.p0, 1.0),
                                                  (rakes[1], run.p1, -1.0))):
        rake_panel = None if rake is None else soffit_members(roof, rake.run.key, soffits)
        if rake_panel:
            closure = _return(roof, this, rake_panel[0], corner, sign, -rake.inset, index)
            returns.extend(m for m in (closure,) if m is not None)
    return (panel, *returns)


def _partner(soffits: dict[str, SoffitRun], run: EdgeRun, corner) -> SoffitRun | None:
    """The run of the other kind (eave vs rake) that closes a soffit at plan point ``corner``."""
    for other in soffits.values():
        if other.run.is_eave == run.is_eave:
            continue
        ends = ((other.run.p0, other.run.corner_at_p0), (other.run.p1, other.run.corner_at_p1))
        if any(at and math.dist(point, corner) <= CLOSURE_TOLERANCE_M for point, at in ends):
            return other
    return None


def _panel(roof: ResolvedRoof, this: SoffitRun, start: float, end: float) -> FramedMember | None:
    run, trim = this.run, this.trim
    span = cut_span(run, start, end)
    if span is None:
        return None
    width, center = this.outer - this.inset, (this.inset + this.outer) / 2.0
    a, b = _offset(span.p0, run.normal, center), _offset(span.p1, run.normal, center)
    connection = (f"eave-trim:{trim.soffit_material}" if not trim.soffit_vented
                  else _VENTED if run.is_eave else _RAKE_VENTED)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-soffit", category="soffit",
        profile=panel_profile(width / M_PER_IN, this.thickness / M_PER_IN),
        p0=a, p1=b, z0_m=span.z0_m - this.drop, z1_m=span.z0_m - this.drop + this.thickness,
        length_m=math.hypot(b[0] - a[0], b[1] - a[1], span.z1_m - span.z0_m),
        z0_end_m=span.z1_m - this.drop, z1_end_m=span.z1_m - this.drop + this.thickness,
        connection=connection, material=trim.soffit_material,
    )


def _return(
    roof: ResolvedRoof, eave: SoffitRun, rake_panel: FramedMember, corner, sign: float,
    cut: float, index: int,
) -> FramedMember | None:
    """The vertical closure on the gable wall's face line, eave panel up to the rake panel.

    It spans the eave overhang across, from the eave fascia's inner face to the eave wall
    face, standing one panel thickness corner-side of the eave panel's cut end.
    """
    run = eave.run
    dx, dy = run.p1[0] - run.p0[0], run.p1[1] - run.p0[1]
    length = math.hypot(dx, dy)
    along = cut - eave.thickness / 2.0
    station = (corner[0] + sign * dx / length * along, corner[1] + sign * dy / length * along)
    a, b = _offset(station, run.normal, eave.outer), _offset(station, run.normal, eave.inset)
    across = math.dist(a, b)
    bottom = run.z0_m - eave.drop
    top0, top1 = _underside_at(rake_panel, a), _underside_at(rake_panel, b)
    if across <= CLOSURE_TOLERANCE_M or min(top0, top1) - bottom <= 1e-6:
        return None
    # The box fields bound the triangle (a board on edge); the sweep draws it.
    top = max(top0, top1)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-soffit-return-{index}", category="soffit",
        profile=panel_profile(eave.thickness / M_PER_IN, (top - bottom) / M_PER_IN),
        p0=a, p1=b, z0_m=bottom, z1_m=top, length_m=across,
        z0_end_m=bottom, z1_end_m=top, connection=_RETURN, material=eave.trim.soffit_material,
        elevation_profile=((0.0, bottom), (across, bottom), (across, top1), (0.0, top0)),
        plan_width_m=eave.thickness,
    )


def _underside_at(member: FramedMember, point) -> float:
    """``member``'s underside, interpolated along its axis at ``point``'s projection."""
    (ax, ay), (bx, by) = member.p0, member.p1
    dx, dy = bx - ax, by - ay
    fraction = ((point[0] - ax) * dx + (point[1] - ay) * dy) / (dx * dx + dy * dy)
    end = member.z0_m if member.z0_end_m is None else member.z0_end_m
    return member.z0_m + (end - member.z0_m) * fraction


def _offset(point, normal, distance: float) -> tuple[float, float]:
    return (point[0] + normal[0] * distance, point[1] + normal[1] * distance)
