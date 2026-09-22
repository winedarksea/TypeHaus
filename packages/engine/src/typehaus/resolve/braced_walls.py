"""IRC R602.10 braced wall lines, what kind each is, and the panels authored on them.

The one reading the check (``checks/structural/braced_wall*.py``), the S-103 sheet and the
handoff list share; a check reading a drawing module was backwards.

**Lines are derived, panels are authored.** A line is a ``resolve/layout_lines.py`` chain
carrying a light-frame wall on the weather envelope. Its ``kind`` is MEASURED, and only a
``braced`` line owes R602.10.3 a length:

- ``engineered`` — every wall carries ``Wall.shear_panel``: an engineered shear wall, out
  of the prescriptive path.
- ``plate`` — every wall is under 12" tall (a rafter plate is not a wall).
- ``gable_end`` — on the topmost storey of its building, where the perpendicular sides are
  plates: the roof assembly braces it.
- ``foundation`` — no wall resolves a framing member in its STRUCTURE layer (a liner's
  furring is not a stud).
- ``interior`` — rooms on both sides of every wall.
- ``infill`` — framed, on a storey that carries R404 foundation walls: its lateral system is
  the concrete box around it.
- ``braced`` — everything else.

**A panel is never derived from sheathed length.** Sheathing a wall is not bracing it — a
panel has a minimum length, and at a line's end a return, a hold-down or a minimum-length
panel. Counting sheathed feet would pass a house with no hold-downs in it.

**Rules that live only here.** Collinear same-method panels within 1/4" MERGE (a run that
crosses a wall butt is authored per wall). A door or window inside a panel is reported by
the check as an error. A ``RoughOpening`` no larger than 24" x 24" is a service penetration
and does NOT split a panel — **no code section states that threshold**; it is the softest
number in the bracing path (``houses/catlin/notes/wall_bracing_layout.md``), chosen because
an ERV port or a hose bibb is not an opening a panel is bounded by.
"""

from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point, Polygon

from typehaus.model.braced_wall import BracedWallPanel
from typehaus.quantities import M_PER_IN

#: Wood structural panel sheathing, by the material refs a house uses. ``siding-303-mdo``
#: is APA Rated Siding 303, a wood structural panel sold as a finished face.
_WSP_MATERIALS = frozenset({
    "struct-1-plywood", "cdx-plywood", "cdx", "osb", "zip-sheathing", "plywood",
    "siding-303-mdo",
})

METHOD_WSP = "WSP"
METHOD_CS_WSP = "CS-WSP"
METHOD_UNRATED = "not rated"

KIND_BRACED = "braced"
KIND_ENGINEERED = "engineered"
KIND_PLATE = "plate"
KIND_GABLE_END = "gable_end"
KIND_FOUNDATION = "foundation"
KIND_INTERIOR = "interior"
KIND_INFILL = "infill"

_PLATE_MAX_M = 12.0 * M_PER_IN
_MERGE_TOL_M = 0.25 * M_PER_IN
#: The service-penetration threshold (see module docstring): no code basis.
PENETRATION_MAX_IN = 24.0
#: How far off a wall's axis the both-sides room probe looks.
_ROOM_PROBE_M = 12.0 * M_PER_IN


@dataclass(frozen=True)
class BracedWallLine:
    """One derived line: where it runs, what its sheathing could support, and its kind."""

    tag: str
    storey: str
    direction: str                     #: "x" or "y"
    p0: tuple[float, float]            #: metres; stations run from here
    p1: tuple[float, float]
    length_m: float
    method: str                        #: what the sheathing COULD support, not what it is
    wall_tags: tuple[str, ...]
    kind: str = KIND_BRACED

    @property
    def length_ft(self) -> float:
        return self.length_m / M_PER_IN / 12.0

    def station_m(self, point) -> float:
        ux, uy = self._unit()
        return (point[0] - self.p0[0]) * ux + (point[1] - self.p0[1]) * uy

    def _unit(self) -> tuple[float, float]:
        dx, dy = self.p1[0] - self.p0[0], self.p1[1] - self.p0[1]
        return dx / self.length_m, dy / self.length_m


@dataclass(frozen=True)
class LineOpening:
    """An opening on a line, as stations along it. Service penetrations are not listed."""

    tag: str
    kind: str
    u0_m: float
    u1_m: float
    #: The taller of the clear height and the head above the storey datum — conservative
    #: for a window and exact for a door; a garage door hung below its plate reads 84".
    height_in: float


@dataclass(frozen=True)
class ResolvedPanel:
    """Contiguous same-method authored panels on one line, merged."""

    tags: tuple[str, ...]
    line_tag: str
    storey: str
    wall_tags: tuple[str, ...]
    u0_m: float
    u1_m: float
    method: str
    hold_down_refs: tuple[str, ...]
    #: Height of the opening each end of the run meets first, outward (None = the line end).
    adjacent_opening_heights_in: tuple[float | None, float | None]
    contains_opening: tuple[str, ...]

    @property
    def length_in(self) -> float:
        return (self.u1_m - self.u0_m) / M_PER_IN

    @property
    def u0_ft(self) -> float:
        return self.u0_m / M_PER_IN / 12.0

    @property
    def u1_ft(self) -> float:
        return self.u1_m / M_PER_IN / 12.0

    @property
    def adjacent_opening_height_in(self) -> float | None:
        heights = [h for h in self.adjacent_opening_heights_in if h is not None]
        return max(heights) if heights else None


def braced_wall_lines(model, storey: str) -> list[BracedWallLine]:
    """Derived braced wall lines for one storey, longest first, each with its kind."""
    walls = {wall.tag: wall for wall in model.walls if wall.storey == storey}
    raw: list[BracedWallLine] = []
    for line in model.layout_lines:
        tags = tuple(sorted({m.wall_tag for m in line.members if m.wall_tag in walls}))
        if not tags:
            continue
        members = [walls[tag] for tag in tags]
        if not any(_is_envelope(wall) and wall.members for wall in members):
            continue
        span = _span(members)
        if span is None:
            continue
        p0, p1, length = span
        raw.append(BracedWallLine(
            tag=f"BWL-{line.tag.removeprefix('LL-')}", storey=storey,
            direction="x" if abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1]) else "y",
            p0=p0, p1=p1, length_m=length, method=_method(members), wall_tags=tags))
    lines = [_with_kind(model, line, walls) for line in raw]
    lines = _mark_gable_ends(model, storey, lines)
    return sorted(lines, key=lambda item: (-item.length_m, item.tag))


def _is_envelope(wall) -> bool:
    """Candidate line: an assembly not tagged interior. ``interior`` then catches the rest."""
    assembly = getattr(wall, "assembly", "") or ""
    return bool(assembly) and "INT" not in assembly and "PARTITION" not in assembly


def _with_kind(model, line: BracedWallLine, walls) -> BracedWallLine:
    members = [walls[tag] for tag in line.wall_tags]
    plan = model.plan
    authored = [plan.by_tag(tag) for tag in line.wall_tags]
    if all(getattr(el, "shear_panel", None) is not None for el in authored):
        kind = KIND_ENGINEERED
    elif all((w.z1_m - w.z0_m) < _PLATE_MAX_M for w in members):
        kind = KIND_PLATE
    elif not any(_frames_structure(w) for w in members):
        kind = KIND_FOUNDATION
    elif all(_rooms_both_sides(model, w) for w in members if _frames_structure(w)):
        kind = KIND_INTERIOR
    elif any(w.is_foundation for w in model.walls if w.storey == line.storey):
        kind = KIND_INFILL
    else:
        kind = KIND_BRACED
    return _replace(line, kind)


def _replace(line: BracedWallLine, kind: str) -> BracedWallLine:
    from dataclasses import replace
    return replace(line, kind=kind)


def _frames_structure(wall) -> bool:
    """A stud in the STRUCTURE layer — furring on a concrete wall's liner does not count."""
    return any(m.category in ("stud", "plate", "king", "jack", "corner")
               for m in wall.members)


def _rooms_both_sides(model, wall) -> bool:
    (ax, ay), (bx, by) = wall.axis
    length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    if length <= 0.0:
        return False
    nx, ny = -(by - ay) / length, (bx - ax) / length
    mid = ((ax + bx) / 2.0, (ay + by) / 2.0)
    faces = [Polygon(room.clear_face) for room in model.rooms
             if room.storey == wall.storey and len(room.clear_face) >= 3]
    sides = [Point(mid[0] + s * nx * _ROOM_PROBE_M, mid[1] + s * ny * _ROOM_PROBE_M)
             for s in (1.0, -1.0)]
    return all(any(face.contains(p) for face in faces) for p in sides)


def _mark_gable_ends(model, storey: str, lines: list[BracedWallLine]) -> list[BracedWallLine]:
    """On the topmost storey of its building, a line whose perpendicular sides are all
    plates is a gable end: the roof, not a panel, braces it."""
    if not lines or _storeys_above(model.plan, storey):
        return lines
    out = []
    for line in lines:
        perpendicular = [o for o in lines if o.direction != line.direction]
        if (line.kind == KIND_BRACED and perpendicular
                and all(o.kind == KIND_PLATE for o in perpendicular)):
            line = _replace(line, KIND_GABLE_END)
        out.append(line)
    return out


def _storeys_above(plan, storey: str) -> list[str]:
    """Storeys of the same building whose elevation is above this one's."""
    here = plan.storey(storey)
    if here is None:
        return []
    return [s.tag for s in plan.storeys
            if s.building == here.building and s.elevation.meters > here.elevation.meters]


def _method(walls) -> str:
    """The R602.10.4 panel method these walls' sheathing COULD support."""
    materials = {layer.material_ref for wall in walls for layer in wall.layers
                 if layer.function == "sheathing"}
    if materials and materials <= _WSP_MATERIALS:
        return METHOD_WSP
    return METHOD_UNRATED


def _span(walls):
    """``(p0, p1, length)`` of the chain's outermost endpoints, or ``None``."""
    points = [point for wall in walls for point in (wall.axis[0], wall.axis[1])]
    if len(points) < 2:
        return None
    p0 = min(points, key=lambda p: (p[0], p[1]))
    p1 = max(points, key=lambda p: (p[0], p[1]))
    length = ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5
    return (p0, p1, length) if length > 0.0 else None


def line_openings(model, line: BracedWallLine) -> list[LineOpening]:
    """Doors, windows and rough openings on the line, as stations; penetrations dropped."""
    walls = {w.tag: w for w in model.walls if w.tag in line.wall_tags}
    out = []
    for opening in model.openings:
        wall = walls.get(opening.host_wall)
        if wall is None or is_service_penetration(opening):
            continue
        a, b = _wall_point(wall, opening.center_along_m - opening.width_m / 2.0), \
            _wall_point(wall, opening.center_along_m + opening.width_m / 2.0)
        u0, u1 = sorted((line.station_m(a), line.station_m(b)))
        height = max(opening.height_m, opening.sill_m + opening.height_m) / M_PER_IN
        out.append(LineOpening(opening.tag, opening.kind, u0, u1, height))
    return sorted(out, key=lambda o: o.u0_m)


def is_service_penetration(opening) -> bool:
    limit = PENETRATION_MAX_IN * M_PER_IN + 1e-9
    return (opening.kind == "rough_opening" and opening.width_m <= limit
            and opening.height_m <= limit)


def _wall_point(wall, station_m: float) -> tuple[float, float]:
    (ax, ay), (bx, by) = wall.axis
    length = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    t = station_m / length if length else 0.0
    return ax + (bx - ax) * t, ay + (by - ay) * t


def authored_panels(plan) -> list[BracedWallPanel]:
    return [el for el in plan.all_elements() if isinstance(el, BracedWallPanel)]


@dataclass(frozen=True)
class UnplacedPanel:
    tag: str
    wall_ref: str
    reason: str


def resolved_braced_wall_panels(model, storey: str,
                                lines: list[BracedWallLine] | None = None,
                                ) -> tuple[list[ResolvedPanel], list[UnplacedPanel]]:
    """Authored panels on this storey's lines, merged; and the ones that land on none."""
    lines = braced_wall_lines(model, storey) if lines is None else lines
    walls = {w.tag: w for w in model.walls}
    by_wall = {tag: line for line in lines for tag in line.wall_tags}
    pieces: dict[tuple[str, str], list[tuple[float, float, BracedWallPanel]]] = {}
    unplaced: list[UnplacedPanel] = []
    for panel in authored_panels(model.plan):
        wall = walls.get(panel.wall_ref)
        if wall is None:
            if _panel_storey(model.plan, panel) == storey:
                unplaced.append(UnplacedPanel(panel.tag, panel.wall_ref,
                                              "names no wall in this model"))
            continue
        if wall.storey != storey:
            continue
        line = by_wall.get(wall.tag)
        if line is None:
            unplaced.append(UnplacedPanel(panel.tag, panel.wall_ref,
                                          "its wall is on no braced wall line"))
            continue
        (ax, ay), (bx, by) = wall.axis
        wall_len = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
        s0 = 0.0 if panel.start is None else panel.start.meters
        s1 = wall_len if panel.width is None else s0 + panel.width.meters
        if s0 < -_MERGE_TOL_M or s1 > wall_len + _MERGE_TOL_M or s1 <= s0:
            unplaced.append(UnplacedPanel(panel.tag, panel.wall_ref,
                                          "its stations run off the wall"))
            continue
        u0, u1 = sorted((line.station_m(_wall_point(wall, s0)),
                         line.station_m(_wall_point(wall, s1))))
        pieces.setdefault((line.tag, panel.method), []).append((u0, u1, panel))
    line_by_tag = {line.tag: line for line in lines}
    merged: list[ResolvedPanel] = []
    for (line_tag, method), runs in sorted(pieces.items()):
        line = line_by_tag[line_tag]
        openings = line_openings(model, line)
        for group in _merge(sorted(runs, key=lambda r: r[0])):
            merged.append(_panel(line, method, group, openings))
    return sorted(merged, key=lambda p: (p.line_tag, p.u0_m)), unplaced


def _panel_storey(plan, panel) -> str | None:
    for storey in plan.storeys:
        if panel in plan.storey_elements(storey.tag):
            return storey.tag
    return None


def _merge(runs):
    """Contiguous runs on DIFFERENT walls become one panel; two on one wall stay two.

    Merging exists for one reason — a panel that crosses a wall butt has to be authored per
    wall — and it stops there. Two panels authored on one wall are two designations, and
    R602.10.2.3 ("Braced wall lines greater than 16 feet ... shall have not less than two
    braced wall panels") is a rule about designations: a 24-foot blind wall is drawn as two
    panels, and collapsing them here would make the drawing and the rule disagree.
    """
    groups: list[list] = []
    for run in runs:
        previous = groups[-1] if groups else None
        if (previous is not None
                and run[0] <= max(r[1] for r in previous) + _MERGE_TOL_M
                and run[2].wall_ref not in {r[2].wall_ref for r in previous}):
            previous.append(run)
        else:
            groups.append([run])
    return groups


def _panel(line: BracedWallLine, method: str, group, openings) -> ResolvedPanel:
    u0 = min(r[0] for r in group)
    u1 = max(r[1] for r in group)
    inside = tuple(o.tag for o in openings
                   if o.u1_m > u0 + _MERGE_TOL_M and o.u0_m < u1 - _MERGE_TOL_M)
    before = [o for o in openings if o.u1_m <= u0 + _MERGE_TOL_M]
    after = [o for o in openings if o.u0_m >= u1 - _MERGE_TOL_M]
    left = max(before, key=lambda o: o.u1_m).height_in if before else None
    right = min(after, key=lambda o: o.u0_m).height_in if after else None
    panels = [r[2] for r in group]
    return ResolvedPanel(
        tags=tuple(p.tag for p in panels), line_tag=line.tag, storey=line.storey,
        wall_tags=tuple(dict.fromkeys(p.wall_ref for p in panels)), u0_m=u0, u1_m=u1,
        method=method,
        hold_down_refs=tuple(p.hold_down_ref for p in panels if p.hold_down_ref),
        adjacent_opening_heights_in=(left, right), contains_opening=inside)
