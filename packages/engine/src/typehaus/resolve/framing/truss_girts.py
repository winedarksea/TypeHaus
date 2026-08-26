"""The **catlin truss**: two tiers of flat horizontal girts on blocks (→ 11 §Framing).

The owner's replacement for the Swinburne outrigger pack (``truss_frame.py``, still here and
still one assembly swap away). Four 1-1/2" layers outboard of the sheathing, all 2x stock,
all horizontal:

============  =======================  =================================================
band          depth off the sheathing  what
============  =======================  =================================================
A             0 – 1-1/2"               ccSPF, crossed by **block-1** at every stud station
B             1-1/2 – 3"               the **inner girt** — SPF 2x4 flat, 24" o.c., buried
C             3 – 4-1/2"               1" ccSPF + a 1/2" vent gap, crossed by **block-2**
D             4-1/2 – 6"               the **outer girt** — KDAT 2x4 flat, the cladding nailer
============  =======================  =================================================

The two girt bands are the FURRING layers; ``framing/furring.py`` frames their field courses
like any other horizontal batten and this pass reads back what it framed, which is what keeps
a block under the girt it actually carries rather than on a grid of its own that would drift
the moment a wall's length or a window's position changed. The pass adds what a course cannot
know about itself: the blocks it bears on, the jamb posts and head/sill courses at every
rough opening, and the buck.

Two rules run through everything here and are worth stating once rather than at each use.

**Materials are by exposure.** Everything inboard of the foam face — block-1, the inner girt,
and the inner band's jamb posts and head/sill courses — is plain SPF: it is encapsulated in
closed-cell foam and never sees water. Everything standing in or outboard of the vent gap —
block-2, the outer girt, and the outer band's posts and courses — is KDAT. The outer girt is
a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle for the life of the
wall, and block-2's face is a ledge every 16" on the foam plane. So the two blocks are two
purchases, and ``takeoff/framing.py`` — which keys rows by material — bills them apart.

**The blocks are on the STUD module, not the girt module.** A girt course climbs its own 24"
elevation module; the blocks under it are what carry it back to the framing, so they land at
whole multiples of the *stud* spacing from the wall's layout line — the same phase
``solver._module_stations`` gives the studs. Block-2 takes that same module shifted half a
bay, so the two tiers' screws are offset 8" rather than stacked: an offset scheme, not a
through-screw one, which is what lets each tier's 5" screw be a plain wood-to-wood connection
with continuous lateral support instead of a fastener cantilevering through foam.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import cast

from typehaus.findings import Finding, Result, Severity
from typehaus.model.assembly import FramingSpec, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.furring import (  # noqa: F401 - re-exported by truss_wall
    HORIZONTAL,
    STRAPPING_CATEGORY,
    VERTICAL,
    _module_stations,
    band_extent,
    course_elevations,
    opening_margin,
)
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import band_axis
from typehaus.resolve.framing.tables import DEFAULT_SPACING
from typehaus.resolve.framing.truss_common import (
    BLOCK_CATEGORY,
    JAMB_PREFIX,
    LADDER_CATEGORY,
    BandFrame,
    Vec,
    mean_offset,
    outward_across,
)
from typehaus.resolve.geometry import length, sub, unit, wall_frame
from typehaus.resolve.layout_lines import ResolvedLayoutLine, layout_phase
from typehaus.resolve.model import (
    FramedMember,
    ResolvedLayer,
    ResolvedOpening,
    ResolvedWall,
)

#: The stock every piece here is cut from. One string, because the whole design is 2x4 flat:
#: a girt, a jamb post, a head course and a block are the same board turned four ways.
GIRT_MEMBER = "2x4"

#: Categories the framing solver emits as a vertical stick a block's screw can land in. A
#: block "over a stud" may equally land on a king, a jack, a cripple or a corner post — the
#: same 1-1/2" of wood in the same plane — and reading only ``stud`` would report every block
#: beside a rough opening as landing on nothing.
STUDLIKE = frozenset({"stud", "king", "jack", "cripple", "corner", "trimmer"})

#: The two tiers, in the order the stack resolves them and the order they are built in.
#: They are also how a block spells which tier it belongs to, in its own child key —
#: ``block-1-...`` bears the inner girt, ``block-2-...`` the outer — which is what
#: ``takeoff/fasteners.py`` reads to bill the two screw lengths apart. Named, and read
#: through :func:`girt_block_tier`, so the key format lives in one place.
INNER, OUTER = "1", "2"

_TOL = 1e-9
_KEY_TOL = 6  # decimal places an elevation is keyed at when pairing the two bands


# --- the predicate ----------------------------------------------------------------


def truss_girt_bands(plan: PlanModel, assembly_tag: str | None
                     ) -> tuple[Layer, Layer] | None:
    """``(inner, outer)`` authored FURRING layers of a girt wall, or ``None``.

    The signature is ``FramingSpec.standoff == "block"``: the band is held off what is behind
    it by 1-1/2" blocks at the framing module rather than lying on it. Read off the *authored*
    assembly, so a check can ask the question without a resolved wall in hand, and returned
    interior → exterior because which tier a piece belongs to is the whole of what decides
    its material.

    ``None`` — deliberately, without complaint — for the ordinary case of no such layer at
    all. A *malformed* girt band (one, three, or a band turned the wrong way) is a different
    thing and :func:`girt_band_findings` reports it; this returns ``None`` for that too, so
    every caller fails safe by simply not framing girts.
    """
    bands = _standoff_layers(plan, assembly_tag)
    if len(bands) != 2 or not all(_is_girt_band(layer) for layer in bands):
        return None
    return bands[0], bands[1]


def _standoff_layers(plan: PlanModel, assembly_tag: str | None) -> list[Layer]:
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    if assembly is None:
        return []
    return [layer for layer in assembly.layers
            if layer.function is LayerFunction.FURRING and layer.framing is not None
            and getattr(layer.framing, "standoff", "none") == "block"]


def _is_girt_band(layer: Layer) -> bool:
    spec = layer.framing
    if spec is None:
        return False
    return (spec.laid != "edge"
            and (spec.direction or VERTICAL).strip().lower() == HORIZONTAL)


def girt_block_tier(child_key: str) -> str | None:
    """``"1"``/``"2"`` for a girt block's child key, ``None`` for anything else.

    ``None`` covers a Swinburne block (``block-truss-...``) as well as every non-block
    member, so a caller can walk one wall's members without first asking what kind of
    truss wall it is.
    """
    for tier in (INNER, OUTER):
        if child_key.startswith(f"block-{tier}-"):
            return tier
    return None


# --- the frame ----------------------------------------------------------------------


class GirtFrame(BandFrame):
    """One girt wall's two bands, and every piece measured off them.

    Anchored on the OUTER band — that is the mount plane, the cladding nailer and the datum
    the buck runs out to — with the inner band's own depth read off its resolved polygon
    rather than assumed, so the four 1-1/2" layers stay an authoring decision and this stays
    arithmetic. Every depth is a signed offset along ``across`` from the same origin the
    outer centreline is on (``BandFrame``), so a block and a buck cannot disagree about where
    the sheathing face is.
    """

    def __init__(self, wall: ResolvedWall, origin: Vec, direction: Vec, across: Vec,
                 first: float, last: float, inner: ResolvedLayer, outer: ResolvedLayer,
                 structure_material: str | None, spacing: float, phase: float,
                 continuations: tuple[str | None, str | None], run: float) -> None:
        super().__init__(wall, origin, direction, across, first, last,
                         outer.thickness_m, run)
        self.inner_name, self.outer_name = inner.name, outer.name
        self.inner_material, self.outer_material = inner.material_ref, outer.material_ref
        self.structure_material = structure_material
        # The stud module and its phase — NOT the girt module. See this file's header.
        self.spacing, self.phase = spacing, phase
        self.continuations = continuations

        section = cross_section(GIRT_MEMBER)
        #: 1-1/2" — a girt's thickness through the wall, and a block's depth.
        self.stock_thickness = section.width_m
        #: 3-1/2" — a course's height on the wall, a post's width along it, and a block's
        #: face in both. Everything here is the same board.
        self.stock_face = section.depth_m

        self.inner_mid = mean_offset(inner, across)
        self.inner_depth = inner.thickness_m
        # A block sits directly inboard of the girt it carries, filling the band behind it.
        self.block_depths = {
            INNER: self.inner_mid - (self.inner_depth + self.stock_thickness) / 2.0,
            OUTER: self.band_mid - (self.band_depth + self.stock_thickness) / 2.0,
        }
        self.band_mids = {INNER: self.inner_mid, OUTER: self.band_mid}
        self.band_names = {INNER: self.inner_name, OUTER: self.outer_name}
        # Girt and jamb-post/course stock follows the tier's exposure; a block follows the
        # band it SERVES, so block-1 is the structure's own SPF and block-2 the outer girt's
        # KDAT. Two rows in the BOM, which is what the two purchases are.
        self.band_materials = {INNER: self.inner_material, OUTER: self.outer_material}
        self.block_materials = {INNER: structure_material, OUTER: self.outer_material}

        # Sheathing face: inboard of the inner girt by block-1's own depth. The buck runs
        # from there to the outer girt's outboard face — 6" on catlin, but derived.
        sheathing_face = self.inner_mid - self.inner_depth / 2.0 - self.stock_thickness
        mount_plane = self.band_mid + self.band_depth / 2.0
        self.buck_depth = mount_plane - sheathing_face
        self.buck_centre = (mount_plane + sheathing_face) / 2.0

    @classmethod
    def build(cls, plan: PlanModel, wall: ResolvedWall, inner: ResolvedLayer,
              outer: ResolvedLayer, line: object | None,
              continuations: tuple[str | None, str | None]) -> GirtFrame | None:
        _origin, _tangent, across, axis_length = wall_frame(wall)
        if axis_length <= _TOL:
            return None
        start, end = band_axis(wall.axis, outer.polygon)
        run = length(sub(end, start))
        if run <= _TOL:
            return None
        turned = outward_across(wall, across)
        if turned is None:
            return None
        direction = unit(sub(end, start))
        first, last = band_extent(outer.polygon, start, direction, run)
        spec = _structure_spec(plan, wall.assembly)
        spacing = (getattr(spec, "spacing", None) or DEFAULT_SPACING).meters
        return cls(wall, start, direction, turned, first, last, inner, outer,
                   assembly_structure_material(plan, wall.assembly), spacing,
                   layout_phase(spec, cast("ResolvedLayoutLine | None", line),
                                wall.tag, spacing), continuations, run)

    # --- the field ---------------------------------------------------------------
    def blocks(self, field: dict[str, list[FramedMember]],
               voids: list[tuple[float, float, float, float]],
               butts: tuple[float, ...] = (),
               verticals: tuple[tuple[float, float, float], ...] = (),
               ) -> tuple[list[FramedMember], list[Finding]]:
        """One block under every stud station each field course crosses, both tiers.

        ``field`` is the courses ``frame_furring`` already framed, keyed by tier. They are
        paired by elevation — the two bands carry the same spec, so their courses are at the
        same elevations and in the same segments — and a pair whose halves disagree about how
        many segments they are in is reported rather than guessed at, because that is a girt
        that stops somewhere its partner does not and the blocks would be the last place to
        notice.

        The two tiers' stations differ by half a bay and only by that: block-1 lands on the
        stud, block-2 8" off it, which is the whole of the offset scheme.
        """
        courses = {tier: _by_elevation(members, self.station_of)
                   for tier, members in field.items()}
        out: list[FramedMember] = []
        findings: list[Finding] = []
        elevations = sorted(set(courses[INNER]) | set(courses[OUTER]))
        for course, z in enumerate(elevations):
            segments = {tier: courses[tier].get(z, ()) for tier in (INNER, OUTER)}
            if len(segments[INNER]) != len(segments[OUTER]):
                findings.append(self._pairing_finding(z, segments))
            for tier in (INNER, OUTER):
                count = 0
                for segment in segments[tier]:
                    seg_lo = self.station_of(segment)
                    seg_hi = seg_lo + length(sub(segment.p1, segment.p0))
                    for station in self._block_stations(segment, tier, butts):
                        if self._in_void(station, segment.z0_m, voids):
                            continue
                        station = self.snap(station, segment.z0_m, verticals, voids,
                                            (seg_lo, seg_hi))
                        out.append(self._block(tier, station, segment.z0_m,
                                               f"block-{tier}-{course:03d}-{count:02d}"))
                        count += 1
        return out, findings

    def _in_void(self, station: float, z0: float,
                 voids: list[tuple[float, float, float, float]]) -> bool:
        """Whether a block at ``station``/``z0`` would stand in a rough opening.

        Belt and braces: a girt band's field courses are already cut a jamb post's width
        clear of every RO (``furring.opening_margin``), so no block placed inside one should
        ever reach here. It is kept because the cost of being wrong is a 2x4 across the
        glass, and because a house may yet author a girt band without that margin.
        """
        half = self.stock_face / 2.0
        lo, hi = station - half, station + half
        return any(vlo < hi - _TOL and lo < vhi - _TOL
                   and vz0 < z0 + self.stock_face - _TOL and z0 < vz1 - _TOL
                   for vlo, vhi, vz0, vz1 in voids)

    def snap(self, station: float, z0: float,
             verticals: tuple[tuple[float, float, float], ...],
             voids: list[tuple[float, float, float, float]] = (),  # type: ignore[assignment]
             bounds: tuple[float, float] | None = None) -> float:
        """``station`` moved onto the wall's actual vertical member there, if there is one.

        The blocks lay out on the STUD module, and away from an opening that is exactly
        where the studs are — the module station and the stud station are the same station
        by construction. **Near an opening they part company**, and the design's central
        claim goes with them if nothing does this. ``opening_exclusions`` drops the module
        stud inside a rough opening's king/jack pack, and the cripples above the head and
        below the sill are then laid out on the OPENING's own rhythm, not the wall's: on
        W-M-S2 they stand at 26", 42" and 58" while the module is at 24", 40" and 56". A
        3-1/2" block centred on the module there laps a 1-1/2" cripple by half an inch, and
        its 5" screw — driven at the block's centre — misses the wood altogether.

        So a block whose module station does not already cover the nearest stick moves onto
        it — **a small correction, never a relocation**. Three bounds keep it that way, and
        each of them is a bug this would otherwise be:

        * **at most one board's width** (3-1/2"). A block-2 is deliberately half a bay off
          the studs, so a reach of half a bay would pull every one of them back onto the
          block-1 line and delete the offset scheme the whole fastening story rests on;
        * **only onto a member at this block's own elevation.** Above a head the wood is
          usually the HEADER, continuous across the whole opening, so there is nothing to
          move onto and no reason to move; and the lowest course of a wall runs opposite the
          floor band, a foot below the nearest cripple;
        * **never into a rough opening.** A jack stands ON the RO edge, so snapping onto one
          would put half a block across the glass — which is what the field course was held
          3-1/2" clear of the opening to prevent in the first place;
        * **never past the end of the course it carries.** ``bounds`` is that segment, and
          without it the end block of a short raked stub at an attic gable slid onto the
          corner post beyond it and stood half its width out in the air past the girt.

        Returns ``station`` unchanged whenever the module is right, which is the field of
        every wall and most of the wall beside every opening.
        """
        if not verticals:
            return station
        half = self.stock_face / 2.0
        z1 = z0 + self.stock_face
        reach = self.stock_face
        best: tuple[float, float] | None = None
        for centre, vz0, vz1 in verticals:
            if vz0 >= z1 - _TOL or z0 >= vz1 - _TOL:
                continue
            offset = abs(centre - station)
            if offset > reach + _TOL:
                continue
            if best is None or offset < best[0]:
                best = (offset, centre)
        if best is None:
            return station
        offset, centre = best
        # Already covering it whole? A 3-1/2" block over a 1-1/2" stick covers it completely
        # while their centres are within an inch, which is the ordinary module case and every
        # slide ``_module_stations`` makes at a band end.
        if offset <= half - self.stock_thickness / 2.0 + _TOL:
            return station
        if bounds is not None and (centre - half < bounds[0] - _TOL
                                   or centre + half > bounds[1] + _TOL):
            return station
        return station if self._in_void(centre, z0, list(voids)) else centre

    def _block_stations(self, course: FramedMember, tier: str,
                        butts: tuple[float, ...] = ()) -> list[float]:
        """Stud stations one course segment crosses, plus one at each free end of it.

        ``butts`` are the stations at which a course end lands against an opening's JAMB
        POST — its outer face, since the field is held exactly one post width clear of every
        RO (``furring.opening_margin``). Such an end is not free and must NOT take the
        mandatory end block, for the plainest possible reason: **there is no stud there.**
        The course stops 3-1/2" short of the RO edge, so a block held its own half-width
        inside that stops 5-1/4" short of it — between the last module stud and the jack,
        on bare sheathing. What actually carries that end is the jamb post it butts, which
        is blocked at this very elevation and screwed to the jack and the king behind it.

        This is the same class of mistake the Swinburne pack made before 2026-08-23 (74 of
        its blocks landed on nothing), arrived at from the other direction, and
        ``test_truss_girt_geometry.py`` measures the lap rather than trusting the module.
        """
        seg_lo = self.station_of(course)
        seg_hi = seg_lo + length(sub(course.p1, course.p0))
        half = self.stock_face / 2.0
        # Half a bay for the outer tier: block-2 is deliberately NOT stacked over block-1.
        phase = self.phase if tier == INNER else self.phase + self.spacing / 2.0
        stations = _module_stations(
            seg_lo + half, seg_hi - half, self.spacing, self.stock_face, module=True,
            phase=phase % self.spacing,
            continuations=self._segment_continuations(seg_lo, seg_hi),
            seams=(0.0, self.run))
        if not stations:
            return stations
        if any(abs(seg_lo - butt) < 1e-6 for butt in butts):
            stations = [s for s in stations if abs(s - (seg_lo + half)) > 1e-9]
        if any(abs(seg_hi - butt) < 1e-6 for butt in butts):
            stations = [s for s in stations if abs(s - (seg_hi - half)) > 1e-9]
        return stations

    def _segment_continuations(self, seg_lo: float,
                               seg_hi: float) -> tuple[str | None, str | None]:
        """Which of this SEGMENT's ends are the band's own continued ends.

        A course cut in two by a window has four ends and only the outer two can be the
        seam a collinear neighbour runs through; handing ``_module_stations`` the wall's
        reading for an end that is really a window jamb would drop the mandatory end block
        there and leave the girt unsupported over the glass.
        """
        start_cont, end_cont = self.continuations
        course_first = self.first if start_cont else self.first + self.stock_thickness / 2.0
        course_last = self.last if end_cont else self.last - self.stock_thickness / 2.0
        return (start_cont if abs(seg_lo - course_first) < 1e-6 else None,
                end_cont if abs(seg_hi - course_last) < 1e-6 else None)

    def _block(self, tier: str, station: float, z0: float, key: str) -> FramedMember:
        point = self.point(station, self.block_depths[tier])
        return FramedMember(
            self.wall.uid, key, BLOCK_CATEGORY, GIRT_MEMBER, point, point,
            z0, z0 + self.stock_face, self.stock_face,
            orient=self.across, material=self.block_materials[tier])

    def _pairing_finding(self, z: float,
                         segments: dict[str, tuple[FramedMember, ...]]) -> Finding:
        return Finding(
            check_id="structural.truss_girt_bands",
            severity=Severity.WARN, result=Result.UNKNOWN,
            message=(f"{self.wall.tag}: the girt course at "
                     f"{(z - self.wall.z0_m) / 0.0254:.1f}\" above the wall base runs in "
                     f"{len(segments[INNER])} segment(s) in {self.inner_name} but "
                     f"{len(segments[OUTER])} in {self.outer_name}; the two tiers are one "
                     "course and their blocks assume they are"),
            element_tags=(self.wall.tag,),
            fix_hint=("give both girt bands the same member, spacing and direction — a "
                      "difference in any of the three moves one band's courses"))

    # --- openings ------------------------------------------------------------------
    def opening_frame(self, opening: ResolvedOpening, index: int,
                      elevations: list[float]) -> list[FramedMember]:
        """Both tiers' jamb posts, head and sill courses, and their blocks, at one RO.

        No doubling anywhere. The head course spans the RO between the two posts' inner
        faces and is blocked back to the framing at every stud station under it, so its span
        is 16" and not the 60" a French door's clear width would otherwise make it — which
        is what the Swinburne ladder had to double for.
        """
        half = opening.width_m / 2.0
        jambs = (opening.center_along_m - half, opening.center_along_m + half)
        z_sill = self.wall.base_ref_z_m + opening.sill_m
        z_head = z_sill + opening.height_m
        # The three elevations an opening adds to its own frame: the sill course under the
        # RO, the head course over it, and — for the posts — every field course between.
        sill_z, head_z = z_sill - self.stock_face, z_head
        out: list[FramedMember] = []
        for tier in (INNER, OUTER):
            band = self.band_names[tier]
            for side, jamb in enumerate(jambs):
                # Outward from the opening: the post's INNER face lands on the RO edge, so
                # the reveal is the post and nothing stands in front of the glass.
                outward = -1.0 if side == 0 else 1.0
                station = jamb + outward * self.stock_face / 2.0
                point = self.point(station, self.band_mids[tier])
                out.append(FramedMember(
                    self.wall.uid, f"{JAMB_PREFIX}{band}-{index:03d}-{side}",
                    STRAPPING_CATEGORY, GIRT_MEMBER, point, point,
                    sill_z, head_z + self.stock_face,
                    head_z + self.stock_face - sill_z,
                    orient=self.across, material=self.band_materials[tier]))
                crossed = {round(z, _KEY_TOL) for z in elevations
                           if sill_z - _TOL <= z
                           and z + self.stock_face <= head_z + self.stock_face + _TOL}
                crossed |= {round(sill_z, _KEY_TOL), round(head_z, _KEY_TOL)}
                for count, z in enumerate(sorted(crossed)):
                    out.append(self._block(
                        tier, station, z,
                        f"block-{tier}-jamb-{index:03d}-{side}-{count:02d}"))
            for name, z0 in (("head", head_z), ("sill", sill_z)):
                out.append(FramedMember(
                    self.wall.uid, f"ladder-{name}-{band}-{index:03d}",
                    LADDER_CATEGORY, GIRT_MEMBER,
                    self.point(jambs[0], self.band_mids[tier]),
                    self.point(jambs[1], self.band_mids[tier]),
                    z0, z0 + self.stock_face, jambs[1] - jambs[0],
                    material=self.band_materials[tier]))
                # And blocked back to the framing at every MODULE station across the RO,
                # which is what makes this a 16" span rather than the opening's own clear
                # width. Over the head those blocks land on the cripples above the header
                # and under the sill on the cripples below the rough sill — ordinary wall,
                # not the void: nothing here is inside the opening, only above and below it.
                #
                # Module stations ONLY — the mandatory end block ``_module_stations`` frames
                # at each end of a run is dropped, and for the same reason the field course's
                # is dropped where it butts a post (see ``_block_stations``): there is no
                # stud 1-3/4" inside a rough opening's edge. What carries this course's ends
                # is the two jamb posts it runs between, each of them blocked at this very
                # elevation. A course too narrow to contain a module station is a 14" RO,
                # spanning post to post inside the 16" the design is sized for anyway.
                phase = self.phase if tier == INNER else self.phase + self.spacing / 2.0
                half = self.stock_face / 2.0
                span = (jambs[0] + half, jambs[1] - half)
                for count, station in enumerate(
                        st for st in _module_stations(
                            span[0], span[1], self.spacing, self.stock_face,
                            module=True, phase=phase % self.spacing)
                        if abs(st - span[0]) > 1e-9 and abs(st - span[1]) > 1e-9):
                    out.append(self._block(
                        tier, station, z0,
                        f"block-{tier}-{name}-{index:03d}-{count:02d}"))
        return out


def _structure_spec(plan: PlanModel, assembly_tag: str | None) -> FramingSpec | None:
    """The wall's STRUCTURE ``FramingSpec`` — the module every block on it lands on."""
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    if assembly is None:
        return None
    index = assembly.structure_index()
    if index is None:
        return None
    return assembly.layers[index].framing


def _by_elevation(members: list[FramedMember],
                  station_of: Callable[[FramedMember], float],
                  ) -> dict[float, tuple[FramedMember, ...]]:
    """Course segments keyed by rounded bottom elevation, each in station order."""
    out: dict[float, list[FramedMember]] = {}
    for member in members:
        out.setdefault(round(member.z0_m, _KEY_TOL), []).append(member)
    return {z: tuple(sorted(segments, key=station_of)) for z, segments in out.items()}
