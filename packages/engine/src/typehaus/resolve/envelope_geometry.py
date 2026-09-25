"""What stands on the thermal boundary — one derivation, read by both consumers.

The block load (``energy_load``) and the Minnesota prescriptive table
(``checks.code.mn_energy``) must agree about what the envelope is, and until now they did
not: each carried its own tuple of catlin tag prefixes (``"W-SG-"``, ``"W-RG-"``,
``"W-B-BRICK"``, ``"SL-G-"``, …), i.e. one house's naming convention compiled into the
engine. Rename a wall and the answer changed; author a porch in any other house and it was
graded against R-21.

The relation is derivable, and it is three tests, not one::

    envelope(wall) == bounds_conditioned_space(wall)
                  and (carries_a_weather_skin(wall) or wall.is_foundation)
                  and not both_faces_interior(wall)

The naive single test — "conditioned on exactly one side", probed off the wall faces — was
measured on catlin and rejected: it moved 25 walls, 12 right and 13 wrong. It re-admitted
``W-B-BRICK`` (the probe reaches *through* the 1" standoff into ``RM-B-GYM``), wrongly added
the walls around a bath chase and an unmodelled attic void, and wrongly dropped
``W-A-N2B`` / ``W-S-N3B`` / ``W-S-W1B`` — real envelope that no room polygon touches. Each
of the three tests above is there because it is the one that fixes one of those families:

* **``bounds_conditioned_space``** measures the wall *body* — not ``axis ± thickness/2``,
  because ``axis`` is an alignment reference and a ``face(...)``-aligned wall carries its
  whole depth to one side of it — against a conditioned room's AXIS cell on the same
  storey (the clear face is the finish face, a wall's depth short of the outboard band
  walls). It excludes ``W-B-BRICK``, admits the three "the room doesn't reach this wall"
  walls, and excludes every tag in both retired prefix tuples on geometry alone.
* **``carries_a_weather_skin``** keeps a bare bearing course out. A 2x plate laid flat on a
  deck under a story-and-a-half roof runs along a room's edge and encloses nothing: no
  sheathing, no foam, no cladding. The envelope at that line runs from the wall BELOW the
  plate to the roof ABOVE it. ``is_foundation`` is the second branch because a below-grade
  wall has no weather skin and is envelope anyway.
* **``both_faces_interior``** needs an *interior region*, not a room-coverage test::

      INTERIOR[storey] = fill_holes(⋃ room.clear_face ∪ ⋃ wall bodies) − ⋃ wall bodies

  Filling the holes is what turns the unmodelled attic void and the bath chase into
  interior. Subtracting the bodies back out is what stops the 1" gap behind ``W-B-BRICK``
  reading as interior for ``W-B-S2-FR``. A morphological closing does not reach either —
  they are holes, not concavities.

The vertical half (roofs and slabs) is the same question asked of a horizontal plane, and it
needs a *space* lookup rather than a plan-adjacency one: a floor between two conditioned
storeys carries no UA, a garage floor faces a buffer, and a yard pad faces neither. One
prism table per model answers it — ``_space_at(outline, z, direction)``.

Cached on the IR the way ``ResolvedModel._tag_index`` is: ``EnvelopeGeometry`` costs ~40 ms
and ``estimate_block_load`` runs eleven times in one check pass. ``ResolvedModel`` is a
mutable dataclass with ``__hash__ = None``, so an ``id()``-keyed module map would be unsafe.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from typehaus.model.enums import LayerFunction
from typehaus.resolve.roof_edge_geometry import skin_layers

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedSolid, ResolvedWall

# How far a wall's BODY may sit off a conditioned room's axis cell and still be that
# room's enclosure; this absorbs lining and junction resolution only.
_ENVELOPE_ADJACENCY_TOLERANCE_M = 0.05

# How far past a wall face to probe for the interior region. 6" clears the wall's own
# finish and any junction slop without reaching across a 4" partition into the space
# beyond. Measured stable over 2"–12".
_INTERIOR_PROBE_OFFSET_M = 6 * 0.0254
# Fraction of the probe line that must lie inside INTERIOR for that face to be interior.
# Measured stable over 0.2–0.8; a wall is either an enclosure line or it is not.
_INTERIOR_MIN_FRACTION = 0.5
# Shrink each end of the probe line by this much before measuring, so a corner junction —
# where the neighbouring wall's body legitimately covers the probe — does not read as
# exterior on a wall that is interior along its whole usable run.
_INTERIOR_PROBE_END_TRIM_M = 0.05

# How far above or below a horizontal plane a conditioned prism may sit and still be the
# space on that side of it. Load-bearing: a slab-on-grade's top is not at its storey datum
# (catlin's ``SL-B-FLOOR`` tops out 4" under ``basement``), so a tight tolerance reads
# "nothing above the basement floor" and bills it against outdoor air.
_FLOOR_SANDWICH_M = 1.0
# The share of a roof/slab plan outline a prism must cover to be the space on that side.
# A 6.9 sf equipment pad clipping the corner of a room is not that room's floor.
_MIN_PLAN_OVERLAP = 0.10


@dataclass(frozen=True)
class _Prism:
    """One room as a plan polygon between two elevations, for the vertical lookup."""

    room_tag: str
    storey: str
    polygon: object
    z0_m: float
    z1_m: float
    conditioned: bool


@dataclass
class EnvelopeGeometry:
    """The derived thermal boundary of one resolved model. Build through
    :func:`envelope_geometry`, which caches it on the IR."""

    bounding_wall_uids: frozenset[str]
    interior_by_storey: dict[str, object]
    prisms: tuple[_Prism, ...]
    # Unconditioned resolved rooms' clear faces, per storey — an attached garage, a cold
    # porch. A *buffer*, which is neither interior nor outdoors, and the thing this engine
    # has nowhere to get a temperature for (→ ``buffer_adjacent``).
    buffer_by_storey: dict[str, object] = field(default_factory=dict)
    _wall_cache: dict[str, bool] = field(default_factory=dict, repr=False)

    # --- walls -------------------------------------------------------------------------
    def bounds_conditioned_space(self, wall: ResolvedWall) -> bool:
        return wall.uid in self.bounding_wall_uids

    def is_envelope_wall(self, wall: ResolvedWall) -> bool:
        """The three-test rule from this module's docstring."""
        cached = self._wall_cache.get(wall.uid)
        if cached is not None:
            return cached
        result = (
            self.bounds_conditioned_space(wall)
            and (carries_a_weather_skin(wall) or wall.is_foundation)
            and not self.both_faces_interior(wall)
        )
        self._wall_cache[wall.uid] = result
        return result

    def both_faces_interior(self, wall: ResolvedWall) -> bool:
        """Is conditioned-or-enclosed space on *both* sides of this wall's body?

        A partition, a centre bearing wall, and the inboard leaf of a double wall all answer
        yes and carry no UA. Probed against the storey's interior region rather than against
        room polygons, because the gaps between rooms — a chase, a stair well, an unmodelled
        attic void — are interior too, and no room polygon covers them.
        """
        interior = self.interior_by_storey.get(wall.storey)
        if interior is None or interior.is_empty:
            return False
        for line in _face_probe_lines(wall):
            if line is None or line.length <= 0:
                return False
            inside = line.intersection(interior).length
            if inside / line.length < _INTERIOR_MIN_FRACTION:
                return False
        return True

    def exterior_face_probe(self, wall: ResolvedWall) -> object | None:
        """The probe line off the face that is NOT interior — the outdoor side.

        The grade split (``resolve.site_earth``) needs a wall's exterior face and
        ``both_faces_interior`` has already found it, so it is handed over rather than
        re-derived. ``None`` when neither face or both faces read interior.
        """
        interior = self.interior_by_storey.get(wall.storey)
        lines = _face_probe_lines(wall)
        if interior is None or any(line is None for line in lines):
            return None
        outward = []
        for line in lines:
            if line.length <= 0:
                return None
            share = 0.0 if interior.is_empty else (line.intersection(interior).length / line.length)
            outward.append(share < _INTERIOR_MIN_FRACTION)
        if outward == [True, False]:
            return lines[0]
        if outward == [False, True]:
            return lines[1]
        return None

    def buffer_adjacent(self, wall: ResolvedWall) -> str | None:
        """The tag of the unconditioned room on this wall's other face, or ``None``.

        A buffer-adjacent envelope surface stays envelope and is charged the **full outdoor
        ΔT** — conservative, so it oversizes and never undersizes — and the gap is NAMED in
        ``EnergyReport.unknown_inputs`` rather than closed with "garage = (indoor +
        outdoor) / 2", which is exactly the rule of thumb this package forbids. There is
        nowhere in the model to get a buffer temperature from: no element carries one.

        catlin emits zero such lines (its garage is detached and its walls are nobody's
        envelope), so nothing moves here today; the first house with an attached garage
        gets a named gap instead of a silent ~40% overstatement.
        """
        buffers = self.buffer_by_storey.get(wall.storey)
        if buffers is None or buffers.is_empty:
            return None
        body = _wall_body(wall)
        if body is None:
            return None
        for prism in self.prisms:
            if prism.conditioned or prism.storey != wall.storey or prism.polygon.is_empty:
                continue
            if body.distance(prism.polygon) <= _ENVELOPE_ADJACENCY_TOLERANCE_M:
                return prism.room_tag
        return None

    def exterior_grade_strip(self, wall: ResolvedWall) -> object | None:
        """The strip of ground this wall is graded by, for ``site_earth``'s ΔT question.

        The exterior face is the one :meth:`both_faces_interior` has already found, so no
        new geometry is derived here. ``None`` where neither face reads as the outdoor side
        (an interior partition, or a wall on a storey with no interior region).
        """
        from typehaus.resolve.site_earth import grade_strip

        line = self.exterior_face_probe(wall)
        if line is None:
            return None
        (x0, y0), (x1, y1) = wall.axis
        (px0, py0), (px1, py1) = list(line.coords)[0], list(line.coords)[-1]
        # The probe line is parallel to the axis and offset along the outward normal, so the
        # offset vector between their midpoints IS that normal.
        dx = (px0 + px1) / 2 - (x0 + x1) / 2
        dy = (py0 + py1) / 2 - (y0 + y1) / 2
        length = (dx * dx + dy * dy) ** 0.5
        if length < 1e-9:
            return None
        return grade_strip(line, (dx / length, dy / length))

    # --- horizontal planes -------------------------------------------------------------
    def space_at(
        self,
        outline,
        z_m: float,
        direction: int,
    ) -> tuple[str, str | None]:
        """What is immediately above (``direction=+1``) or below (``-1``) a plan outline.

        Returns ``("conditioned" | "buffer" | "outside", governing room tag)``. Nearest
        prism wins, capped at :data:`_FLOOR_SANDWICH_M`; the prism's plan overlap with the
        outline must reach :data:`_MIN_PLAN_OVERLAP` for it to count as the space on that
        side. ``"buffer"`` is a resolved but unconditioned room — a garage, a cold porch —
        which is a different fact from open air even though Phase 1 charges both the full
        outdoor ΔT (there is nowhere in the model to get a buffer temperature from, and
        "garage = (indoor+outdoor)/2" is the rule of thumb this package forbids).
        """
        from shapely.geometry import Polygon

        if len(outline) < 3:
            return "outside", None
        plan = Polygon(outline)
        if plan.area <= 0:
            return "outside", None
        best: tuple[float, _Prism] | None = None
        for prism in self.prisms:
            # The near edge of the prism on the requested side of the plane.
            gap = (prism.z0_m - z_m) if direction > 0 else (z_m - prism.z1_m)
            if gap < -_FLOOR_SANDWICH_M or gap > _FLOOR_SANDWICH_M:
                continue
            if prism.polygon.is_empty:
                continue
            overlap = plan.intersection(prism.polygon).area / plan.area
            if overlap < _MIN_PLAN_OVERLAP:
                continue
            distance = abs(gap)
            # A conditioned prism outranks an unconditioned one at the same distance: a
            # garage stair landing filed over a heated room is still over a heated room.
            key = (distance, 0 if prism.conditioned else 1)
            if best is None or key < (abs(best[0]), 0 if best[1].conditioned else 1):
                best = (gap, prism)
        if best is None:
            return "outside", None
        return ("conditioned" if best[1].conditioned else "buffer"), best[1].room_tag

    def is_envelope_slab(self, solid: ResolvedSolid) -> tuple[bool, str]:
        """Is this slab a thermal-boundary floor or ceiling? With the reason.

        Exactly one side conditioned. Both sides conditioned is an interior floor (catlin's
        ``SL-M-DECK`` over the living room, its tub deck); neither side is a yard pad or a
        porch deck. The reason string is returned so a test can assert on *why* rather than
        only on the outcome, and so ``unknown_inputs`` can name a buffer.
        """
        above, above_tag = self.space_at(solid.outline, solid.z1_m, +1)
        below, below_tag = self.space_at(solid.outline, solid.z0_m, -1)
        reason = f"above={above}({above_tag}) below={below}({below_tag})"
        conditioned_sides = (above == "conditioned") + (below == "conditioned")
        return conditioned_sides == 1, reason

    def is_envelope_roof(self, roof: ResolvedRoof) -> tuple[bool, str]:
        """Is this roof over conditioned space?

        One side only: nothing is above a roof. ``eave_z_m`` is the low edge of the deck
        plane, which is the elevation a prism under the roof can reach.
        """
        below, below_tag = self.space_at(roof.footprint, roof.eave_z_m, -1)
        return below == "conditioned", f"below={below}({below_tag})"


def carries_a_weather_skin(wall: ResolvedWall) -> bool:
    """Whether this wall has an outboard side for a thermal boundary to run through.

    What this excludes is a bearing element that is not a wall in the enclosure sense: in a
    story-and-a-half the roof lands on a 2x plate laid flat on the deck, and that plate runs
    along a room's edge and encloses nothing — no sheathing, no foam, no cladding. The
    envelope at that line runs from the wall BELOW the plate up to the roof ABOVE it, and the
    plate sits inside both. Grading such a course against R-21 is a category error, and a
    permanent FAIL that says nothing about the building.

    **Either a SHEATHING or a CLADDING layer counts, and the two halves come from the two
    callers.** ``resolve/roof_edge.py``'s ``skin_layers`` is sheathing-and-outboard, which is
    the right reading for the roof-edge closure it was written for, and which the MN
    prescriptive check borrowed. The block load asked for cladding instead. A cladding-only
    assembly — a rainscreen over solid masonry, a fixture wall in a test — is a real exterior
    wall and the sheathing reading drops it; a sheathed wall whose cladding has been
    *forgotten* is a real exterior wall too and the cladding reading drops that. Neither
    alone is the question; the union is, and a bare plate still answers no to both.
    """
    if skin_layers(wall):
        return True
    return any(layer.function == LayerFunction.CLADDING.value for layer in wall.depth_layers())


def _wall_body(wall: ResolvedWall):
    """The wall's occupied plan footprint, as a union of its depth layers' polygons."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    bodies = [Polygon(layer.polygon) for layer in wall.depth_layers() if len(layer.polygon) >= 3]
    if not bodies:
        return None
    return union_all(bodies)


def _face_probe_lines(wall: ResolvedWall) -> list[object | None]:
    """Two lines, one off each face of the wall body, offset :data:`_INTERIOR_PROBE_OFFSET_M`.

    Offsets are taken from the BODY's own reach on each side rather than from
    ``axis ± thickness/2``: a ``face(...)``-aligned wall carries its whole depth to one side
    of the axis, so half-thickness is both the wrong distance and the wrong direction.
    """
    from shapely.geometry import LineString

    (x0, y0), (x1, y1) = wall.axis
    run = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    if run < 1e-9:
        return [None, None]
    tangent = ((x1 - x0) / run, (y1 - y0) / run)
    normal = (-tangent[1], tangent[0])
    body = _wall_body(wall)
    if body is None or body.is_empty:
        return [None, None]
    # Signed perpendicular reach of the body on each side of the axis.
    reaches = [(px - x0) * normal[0] + (py - y0) * normal[1] for px, py in _outline_points(body)]
    if not reaches:
        return [None, None]
    trim = min(_INTERIOR_PROBE_END_TRIM_M, run / 4)
    lines: list[object | None] = []
    for offset in (
        max(reaches) + _INTERIOR_PROBE_OFFSET_M,
        min(reaches) - _INTERIOR_PROBE_OFFSET_M,
    ):
        ax = x0 + tangent[0] * trim + normal[0] * offset
        ay = y0 + tangent[1] * trim + normal[1] * offset
        bx = x1 - tangent[0] * trim + normal[0] * offset
        by = y1 - tangent[1] * trim + normal[1] * offset
        lines.append(LineString([(ax, ay), (bx, by)]))
    return lines


def _outline_points(geom) -> list[tuple[float, float]]:
    parts = getattr(geom, "geoms", None)
    if parts is not None:
        return [pt for part in parts for pt in _outline_points(part)]
    exterior = getattr(geom, "exterior", None)
    if exterior is None:
        return []
    return list(exterior.coords)


def _fill_holes(geom):
    """Every part of ``geom`` rebuilt from its exterior ring alone."""
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import union_all

    parts = getattr(geom, "geoms", None)
    if parts is not None:
        filled = [_fill_holes(part) for part in parts]
        return union_all([p for p in filled if p is not None and not p.is_empty])
    exterior = getattr(geom, "exterior", None)
    if exterior is None:
        return geom
    return Polygon(exterior.coords)


def _build(model: ResolvedModel) -> EnvelopeGeometry:
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import difference, union_all
    from typehaus.resolve.room_lookup import axis_polygon

    # --- bounds_conditioned_space ------------------------------------------------------
    # Adjacency is read off the AXIS cells: the clear face is the finish face, which the
    # outboard band walls (W-S-W1B and kin) stand a full wall off. The interior region and
    # the prisms below keep the clear faces.
    conditioned_faces: dict[str, list[object]] = {}
    conditioned_cells: dict[str, list[object]] = {}
    for room in model.rooms:
        if room.conditioned and len(room.clear_face) >= 3:
            conditioned_faces.setdefault(room.storey, []).append(Polygon(room.clear_face))
            conditioned_cells.setdefault(room.storey, []).append(axis_polygon(room))
    bodies_by_storey: dict[str, list[object]] = {}
    body_by_uid: dict[str, object] = {}
    for wall in model.walls:
        body = _wall_body(wall)
        if body is None or body.is_empty:
            continue
        body_by_uid[wall.uid] = body
        bodies_by_storey.setdefault(wall.storey, []).append(body)
    bounding: set[str] = set()
    for wall in model.walls:
        body = body_by_uid.get(wall.uid)
        near = conditioned_cells.get(wall.storey, ())
        if body is None or not near:
            continue
        # Distances per room polygon rather than over a union: min() answers the question
        # and an overlay of every room would be a lot of GEOS work to get there.
        if any(body.distance(face) <= _ENVELOPE_ADJACENCY_TOLERANCE_M for face in near):
            bounding.add(wall.uid)

    # --- the interior region -----------------------------------------------------------
    interior: dict[str, object] = {}
    for storey in set(conditioned_faces) | set(bodies_by_storey):
        rooms = conditioned_faces.get(storey, [])
        walls = bodies_by_storey.get(storey, [])
        if not rooms:
            # No conditioned room on this storey: nothing is interior here, and a wall
            # standing alone must not read as a partition because its neighbours touch it.
            interior[storey] = Polygon()
            continue
        occupied = union_all(rooms + walls)
        wall_union = union_all(walls) if walls else None
        filled = _fill_holes(occupied)
        interior[storey] = filled if wall_union is None else difference(filled, wall_union)

    # --- the prism table ---------------------------------------------------------------
    # The height source is the storey's ``default_ceiling_height``, the same one
    # ``_volume_ft3`` uses — deliberately NOT ``room.clear_height_m``, which is floor to the
    # lowest obstruction and would put the top of RM-M-LIVING under SL-M-DECK's underside
    # instead of at the deck.
    elevations = {storey.tag: storey.elevation.meters for storey in model.plan.storeys}
    heights = {storey.tag: storey.default_ceiling_height.meters for storey in model.plan.storeys}
    prisms = tuple(
        _Prism(
            room.tag,
            room.storey,
            Polygon(room.clear_face),
            elevations.get(room.storey, 0.0),
            elevations.get(room.storey, 0.0) + heights.get(room.storey, 0.0),
            room.conditioned,
        )
        for room in model.rooms
        if len(room.clear_face) >= 3
    )
    buffers: dict[str, object] = {}
    for room in model.rooms:
        if not room.conditioned and len(room.clear_face) >= 3:
            buffers.setdefault(room.storey, []).append(Polygon(room.clear_face))
    buffer_union = {storey: union_all(faces) for storey, faces in buffers.items()}
    return EnvelopeGeometry(frozenset(bounding), interior, prisms, buffer_union)


def envelope_geometry(model: ResolvedModel) -> EnvelopeGeometry:
    """The model's derived thermal boundary, built once and cached on the IR."""
    cached = getattr(model, "_envelope_geometry", None)
    if cached is not None:
        return cached
    built = _build(model)
    # A hand-built or frozen stand-in in a test may not carry the field; the derivation is
    # correct either way, it just pays for itself again on the next ask.
    with contextlib.suppress(AttributeError, TypeError):
        model._envelope_geometry = built
    return built
