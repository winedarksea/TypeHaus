"""The **catlin truss**: one tier of flat horizontal girts on 4-1/2" blocks (→ 11 §Framing).

The owner's replacement for the Swinburne outrigger pack (``truss_frame.py``, still here and
still one assembly swap away). Everything outboard of the sheathing is 2x stock laid flat and
horizontal, in two bands and 6" total:

============  =======================  =================================================
band          depth off the sheathing  what
============  =======================  =================================================
A             0 – 4"                   ccSPF, one application, crossed only by **the
                                       block** — three loose 1-1/2" offcut plies stacked
                                       on the sheathing over every other stud at every
                                       24" course
A'            4 – 4-1/2"               the block's proud 1/2": the **continuous vent gap**
                                       behind every course
B             4-1/2 – 6"               the **girt** — KDAT 2x4 flat, 24" o.c., standing in
                                       free air: the cladding nailer and the window mount
                                       plane
============  =======================  =================================================

**The inner girt tier was deleted** (decision recorded in ``houses/catlin/CLAUDE.md`` and
``notes/catlin_truss_engineering.md``). It sat directly on the sheathing, so it gave its
screw no thermal break at all, and it cost 10.9% wood in the first 1-1/2" of the foam to
hold up a band that carried nothing but the block above it. The foam does not need it:
ccSPF is applied to a vertical surface with nothing in it (ESR-4073 §4.4.2), and its
racking contribution is its bond to the sheathing face, which is unchanged. The two-band
form is still legal here — another house may want it — so everything below is written for
*the tiers this wall actually has*, one or two, and ``self.tiers`` is the list.

The girt band is the FURRING layer; ``framing/furring.py`` frames its field courses like any
other horizontal batten and this pass reads back what it framed, which is what keeps a block
under the girt it actually carries rather than on a grid of its own that would drift the
moment a wall's length or a window's position changed. The pass adds what a course cannot
know about itself: the blocks it bears on, the jamb posts and head/sill courses at every
rough opening, and the buck.

Three rules run through everything here and are worth stating once rather than at each use.

**One fastener, and it is the whole load path.** One 8" SDWS22800DB per crossing, driven
through girt + block (6") and the sheathing, 1-1/2" into the stud. There is no second pass
and no nail: the block bears the cladding's gravity in direct compression on the sheathing,
so the screw is a pure withdrawal element at about 38% of its ASD allowable. Nothing else
holds the cladding on, which is why ``takeoff/fasteners.py`` bills it off the resolved
blocks rather than off a grid, and why the note names the screw pattern as the one thing
this wall cannot miss.

**Materials are by exposure.** On the one-tier wall everything outboard of the sheathing is
KDAT — the girt is a 3-1/2"-deep horizontal ledge behind the cladding that will wet-cycle
for the life of the wall, and the block plies stand in the same foam-face plane and get
their sides filleted rather than sealed. On the two-tier wall the inner tier was plain SPF,
encapsulated and never wet, and ``takeoff/framing.py`` — which keys rows by material — still
bills the two apart.

**The blocks are on the STUD module, not the girt module.** A girt course climbs its own 24"
elevation module; the blocks under it are what carry it back to the framing, so they land at
whole multiples of the *stud* spacing from the wall's layout line — the same phase
``solver._module_stations`` gives the studs. On the one-tier wall the block module is
**twice** that spacing: one block on every other stud, 32" on catlin, which is what makes a
crossing's tributary 32" x 24" and the screw count half what the two-tier scheme needed.
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

#: The tiers a girt wall may have, in the order the stack resolves them and the order they
#: are built in. They are also how a block spells which tier it belongs to, in its own child
#: key — ``block-1-...`` bears an inner girt, ``block-2-...`` the outer one — which is what
#: ``takeoff/fasteners.py`` reads to bill the screw lengths apart. Named, and read through
#: :func:`girt_block_tier`, so the key format lives in one place.
#:
#: A ONE-TIER wall (catlin) has only ``OUTER``: its sole band *is* the outer girt — the
#: cladding nailer, the mount plane, and the KDAT — and its blocks are ``block-2-...`` for
#: exactly that reason, not because a phantom inner tier is missing.
INNER, OUTER = "1", "2"

_TOL = 1e-9
_KEY_TOL = 6  # decimal places an elevation is keyed at when pairing the two bands


# --- the predicate ----------------------------------------------------------------


def truss_girt_bands(plan: PlanModel, assembly_tag: str | None
                     ) -> tuple[Layer | None, Layer] | None:
    """``(inner, outer)`` authored FURRING layers of a girt wall, or ``None``.

    The signature is ``FramingSpec.standoff == "block"``: the band is held off what is behind
    it by blocks at the framing module rather than lying on it. Read off the *authored*
    assembly, so a check can ask the question without a resolved wall in hand, and returned
    interior → exterior because which tier a piece belongs to is the whole of what decides
    its material.

    **The outer band is always ``[1]``; the inner one is ``None`` on a one-tier wall.** That
    shape rather than a bare list because every caller wants the OUTER band and only the
    frame cares whether there is an inner one: the outer girt is the mount plane, the
    cladding nailer, the band a course spacing is read from and the one whose continuation
    roles matter. A caller that indexes ``[1]`` is right on both wall types.

    ``None`` — deliberately, without complaint — for the ordinary case of no such layer at
    all. A *malformed* girt band (three of them, or one turned the wrong way) is a different
    thing and :func:`girt_band_findings` reports it; this returns ``None`` for that too, so
    every caller fails safe by simply not framing girts.
    """
    bands = _standoff_layers(plan, assembly_tag)
    if not 1 <= len(bands) <= 2 or not all(_is_girt_band(layer) for layer in bands):
        return None
    return (bands[0] if len(bands) == 2 else None), bands[-1]


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
    """One girt wall's band or bands, and every piece measured off them.

    Anchored on the OUTER band — that is the mount plane, the cladding nailer and the datum
    the buck runs out to — with the SHEATHING FACE read off the resolved stack rather than
    assumed. That single reading is what lets the same code frame both wall types: a block
    fills whatever sits between the sheathing and the band it carries, one 1-1/2" ply on the
    two-tier wall and three of them (4-1/2") on catlin's one-tier one, where the extra 1/2"
    over the 4" of foam IS the vent gap. The stack stays an authoring decision and this stays
    arithmetic.

    Every depth is a signed offset along ``across`` from the same origin the outer centreline
    is on (``BandFrame``), so a block and a buck cannot disagree about where the sheathing
    face is.
    """

    def __init__(self, wall: ResolvedWall, origin: Vec, direction: Vec, across: Vec,
                 first: float, last: float, inner: ResolvedLayer | None,
                 outer: ResolvedLayer, sheathing_face: float,
                 structure_material: str | None, spacing: float, phase: float,
                 block_phase: float,
                 continuations: tuple[str | None, str | None], run: float) -> None:
        super().__init__(wall, origin, direction, across, first, last,
                         outer.thickness_m, run)
        self.inner_name = inner.name if inner is not None else None
        self.outer_name = outer.name
        self.inner_material = inner.material_ref if inner is not None else None
        self.outer_material = outer.material_ref
        self.structure_material = structure_material
        # The stud module and its phase — NOT the girt module. See this file's header.
        self.spacing, self.phase = spacing, phase
        # And the BLOCK module's own phase, which is a different number and has to be. Both
        # are the wall-local station of the LAYOUT LINE's first module station
        # (``layout_lines.layout_phase``), and a phase is only line-locked modulo the spacing
        # it was solved for: a wall standing 16" along its line has stud phase 0 mod 16 but
        # block phase 16 mod 32. Taking ``phase % 32`` instead put half of a facade's wall
        # segments on the opposite 32" parity from the rest, so the facade's block grid
        # differed storey to storey while every block was still faithfully on a stud.
        self.block_phase = block_phase
        self.continuations = continuations

        section = cross_section(GIRT_MEMBER)
        #: 1-1/2" — a girt's thickness through the wall, and one block ply's depth.
        self.stock_thickness = section.width_m
        #: 3-1/2" — a course's height on the wall, a post's width along it, and a block's
        #: face in both. Everything here is the same board.
        self.stock_face = section.depth_m
        self.sheathing_face = sheathing_face

        #: The tiers this wall actually has, interior → exterior. One or two; everything
        #: below iterates it rather than the ``(INNER, OUTER)`` pair, so a one-tier wall
        #: frames nothing for a band that is not there instead of guessing at one.
        self.tiers: tuple[str, ...] = (INNER, OUTER) if inner is not None else (OUTER,)
        #: The BLOCK module. Two tiers put a block at every stud, which is what their two
        #: 5" screws assumed. One tier puts a block on every OTHER stud — 32" on catlin —
        #: which is the whole of why a crossing's tributary is 32" x 24" and the screw count
        #: is half what the offset scheme needed.
        self.block_spacing = spacing if inner is not None else spacing * 2.0

        self.inner_mid = mean_offset(inner, across) if inner is not None else 0.0
        self.inner_depth = inner.thickness_m if inner is not None else 0.0
        band_ins = {INNER: self.inner_mid - self.inner_depth / 2.0, OUTER: self.band_in}
        # A block fills the band behind the girt it carries, all the way back to what is
        # behind that — the sheathing for the innermost tier, the tier below for any other.
        thicknesses = {INNER: band_ins[INNER] - sheathing_face,
                       OUTER: (band_ins[OUTER] - sheathing_face if inner is None
                               else self.stock_thickness)}
        self.block_thickness = {tier: thicknesses[tier] for tier in self.tiers}
        self.block_depths = {tier: band_ins[tier] - self.block_thickness[tier] / 2.0
                             for tier in self.tiers}
        # The block is a STACK of flat 2x4 offcuts, so its profile is a ply count and not a
        # new size: three loose 3-1/2" x 3-1/2" x 1-1/2" pieces dropped on the sheathing and
        # clamped by the girt screw, never tacked. Derived from the depth the stack leaves
        # rather than named, so an assembly that moves the girt out moves the ply count with
        # it and the BOM cannot disagree with the geometry.
        self.block_plies = {tier: max(1, int(round(self.block_thickness[tier]
                                                   / self.stock_thickness)))
                            for tier in self.tiers}
        self.block_profiles = {
            tier: (GIRT_MEMBER if plies == 1 else f"{plies}-{GIRT_MEMBER}")
            for tier, plies in self.block_plies.items()}
        self.band_mids = {INNER: self.inner_mid, OUTER: self.band_mid}
        self.band_names = {INNER: self.inner_name, OUTER: self.outer_name}
        # Girt and jamb-post/course stock follows the tier's exposure; a block follows the
        # band it SERVES, so an inner block is the structure's own SPF and the outer girt's
        # block is KDAT. Two rows in the BOM where there are two tiers, which is what the
        # two purchases were; one row, all KDAT, on the one-tier wall.
        self.band_materials = {INNER: self.inner_material, OUTER: self.outer_material}
        self.block_materials = {INNER: structure_material, OUTER: self.outer_material}

        # The buck runs from the sheathing face to the outer girt's outboard face — 6" on
        # catlin on either wall type, but derived.
        mount_plane = self.band_mid + self.band_depth / 2.0
        self.buck_depth = mount_plane - sheathing_face
        self.buck_centre = (mount_plane + sheathing_face) / 2.0

    def _module(self, tier: str) -> tuple[float, float]:
        """``(spacing, phase)`` of one tier's block module, in metres.

        One tier: the block module, on the stud line the layout phase gives — every other
        stud, and which of the two is a consequence of the phase and not a choice made here.
        Two tiers: the stud module, with the outer tier shifted half a bay so the two tiers'
        screws are offset 8" rather than stacked.
        """
        if len(self.tiers) == 1:
            return self.block_spacing, self.block_phase
        phase = self.phase if tier == INNER else self.phase + self.spacing / 2.0
        return self.spacing, phase % self.spacing

    @classmethod
    def build(cls, plan: PlanModel, wall: ResolvedWall, inner: ResolvedLayer | None,
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
        block_spacing = spacing if inner is not None else spacing * 2.0
        block_phase = layout_phase(spec, cast("ResolvedLayoutLine | None", line),
                                   wall.tag, block_spacing)
        band_in = mean_offset(outer, turned) - outer.thickness_m / 2.0
        sheathing_face = _sheathing_face(wall, turned, band_in)
        if sheathing_face is None:
            # No resolved SHEATHING band inboard of the girt — an unsheathed girt wall is
            # not a thing this house builds, but the fallback frames one ply of block
            # rather than refusing outright.
            sheathing_face = band_in - cross_section(GIRT_MEMBER).width_m
        return cls(wall, start, direction, turned, first, last, inner, outer,
                   sheathing_face, assembly_structure_material(plan, wall.assembly),
                   spacing,
                   layout_phase(spec, cast("ResolvedLayoutLine | None", line),
                                wall.tag, spacing),
                   block_phase, continuations, run)

    # --- the field ---------------------------------------------------------------
    def blocks(self, field: dict[str, list[FramedMember]],
               voids: list[tuple[float, float, float, float]],
               butts: tuple[float, ...] = (),
               verticals: tuple[tuple[float, float, float], ...] = (),
               ) -> tuple[list[FramedMember], list[Finding]]:
        """One block under every module station each field course crosses, every tier.

        ``field`` is the courses ``frame_furring`` already framed, keyed by tier. On a
        TWO-tier wall they are paired by elevation — the two bands carry the same spec, so
        their courses are at the same elevations and in the same segments — and a pair whose
        halves disagree about how many segments they are in is reported rather than guessed
        at, because that is a girt that stops somewhere its partner does not and the blocks
        would be the last place to notice. A one-tier wall has nothing to pair and says so
        by having one tier, not by a special case here.

        The module is :meth:`_module`: every other stud on the one-tier wall, and on the
        two-tier one the stud module with the outer tier half a bay off it.
        """
        courses = {tier: _by_elevation(members, self.station_of)
                   for tier, members in field.items()}
        out: list[FramedMember] = []
        findings: list[Finding] = []
        elevations = sorted({z for tier in self.tiers for z in courses.get(tier, {})})
        for course, z in enumerate(elevations):
            segments = {tier: courses.get(tier, {}).get(z, ()) for tier in self.tiers}
            if len(self.tiers) == 2 and len(segments[INNER]) != len(segments[OUTER]):
                findings.append(self._pairing_finding(z, segments))
            for tier in self.tiers:
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

    def rake_blocks(self, rakes: dict[str, list[FramedMember]],
                    voids: list[tuple[float, float, float, float]],
                    verticals: tuple[tuple[float, float, float], ...] = (),
                    ) -> list[FramedMember]:
        """Blocks under a RAKED nailer, on the same module the field courses use.

        Its own branch rather than a case inside :meth:`blocks`, because everything that
        method does turns on a course having ONE elevation: it pairs the two tiers by
        ``z0_m`` and hands the pair's segments to ``_by_elevation``. A rake has an
        elevation per station, so a rake member read as a course pairs against whatever
        else happens to start at the same number, and the pairing finding fires on a
        mismatch that is not one.

        What does carry over is the module (:meth:`_module`), each block's own ``z0`` read
        off the rake at its own station. The block is drawn square, as every other block is;
        it is cut on the rake on the job, and the 3-1/2" it is wide puts its two upper
        corners within an inch of the nailer's underside on catlin's 6:12 gables.
        """
        out: list[FramedMember] = []
        for tier in self.tiers:
            for index, member in enumerate(rakes.get(tier, ())):
                seg_lo = self.station_of(member)
                seg_hi = seg_lo + length(sub(member.p1, member.p0))
                if seg_hi - seg_lo <= _TOL:
                    continue
                z_lo = member.z0_m
                z_hi = member.z0_end_m if member.z0_end_m is not None else member.z0_m
                half = self.stock_face / 2.0
                spacing, phase = self._module(tier)
                stations = _module_stations(
                    seg_lo + half, seg_hi - half, spacing, self.stock_face,
                    module=True, phase=phase,
                    continuations=self._segment_continuations(seg_lo, seg_hi),
                    seams=(0.0, self.run))
                count = 0
                for station in stations:
                    z0 = z_lo + (z_hi - z_lo) * (station - seg_lo) / (seg_hi - seg_lo)
                    z0 -= self.stock_face
                    if self._in_void(station, z0, voids):
                        continue
                    station = self.snap(station, z0, verticals, voids, (seg_lo, seg_hi))
                    out.append(self._block(
                        tier, station, z0,
                        f"block-{tier}-rake-{index:03d}-{count:02d}"))
                    count += 1
        return out

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

        This is the same class of mistake as a block landing on nothing, arrived at from
        the other direction, and ``test_truss_girt_geometry.py`` measures the lap rather
        than trusting the module.
        """
        seg_lo = self.station_of(course)
        seg_hi = seg_lo + length(sub(course.p1, course.p0))
        half = self.stock_face / 2.0
        spacing, phase = self._module(tier)
        stations = _module_stations(
            seg_lo + half, seg_hi - half, spacing, self.stock_face, module=True,
            phase=phase,
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
        """One block: a 3-1/2" square face on the wall, ``block_thickness`` deep through it.

        ``orient`` is ``across``, so the profile's ``width_m`` — 4-1/2" for the three-ply
        stack, 1-1/2" for a single ply — runs THROUGH the wall and its 3-1/2" ``depth_m``
        along it. One member per station rather than one per ply: the plies are loose
        offcuts clamped by the same screw, they are ordered as a ply count and not as a
        stick, and three coincident solids in the viewer would say nothing the profile
        string does not.
        """
        point = self.point(station, self.block_depths[tier])
        return FramedMember(
            self.wall.uid, key, BLOCK_CATEGORY, self.block_profiles[tier], point, point,
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
        """Every tier's jamb posts, head and sill courses, and their blocks, at one RO.

        No doubling anywhere. The head course spans the RO between the two posts' inner
        faces and is blocked back to the framing at every module station under it, so its
        span is the block module and not the 60" a French door's clear width would otherwise
        make it — which is what the Swinburne ladder had to double for.

        The jamb posts are blocked at every course elevation the RO crosses, so on the
        one-tier wall they take a block every 24" — the "≤ 24" under every jamb post, head
        and sill course" half of the fastener schedule.
        """
        half = opening.width_m / 2.0
        jambs = (opening.center_along_m - half, opening.center_along_m + half)
        z_sill = self.wall.base_ref_z_m + opening.sill_m
        z_head = z_sill + opening.height_m
        # The three elevations an opening adds to its own frame: the sill course under the
        # RO, the head course over it, and — for the posts — every field course between.
        sill_z, head_z = z_sill - self.stock_face, z_head
        out: list[FramedMember] = []
        for tier in self.tiers:
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
                spacing, phase = self._module(tier)
                half = self.stock_face / 2.0
                span = (jambs[0] + half, jambs[1] - half)
                for count, station in enumerate(
                        st for st in _module_stations(
                            span[0], span[1], spacing, self.stock_face,
                            module=True, phase=phase)
                        if abs(st - span[0]) > 1e-9 and abs(st - span[1]) > 1e-9):
                    out.append(self._block(
                        tier, station, z0,
                        f"block-{tier}-{name}-{index:03d}-{count:02d}"))
        return out


def _sheathing_face(wall: ResolvedWall, across: Vec, band_in: float) -> float | None:
    """The outboard face of the wall's SHEATHING, as a signed depth along ``across``.

    The block's back, and therefore its ply count, its depth and — with the girt's own
    outboard face — the buck's width. Read off the resolved stack rather than derived from
    the band above it: the depth between the sheathing and the girt is 4-1/2" of
    foam-and-air, not 1-1/2" of wood, and a frame that assumed one ply would put the girt
    inside the foam without saying so.

    ``band_in`` bounds the search to sheathing that is actually BEHIND the girt: an assembly
    is free to carry a second sheet outboard of the furring, and a block measured back to
    that one would be inside out.
    """
    faces = [mean_offset(layer, across) + layer.thickness_m / 2.0
             for layer in wall.layers
             if layer.function == "sheathing" and layer.polygon
             and mean_offset(layer, across) <= band_in + _TOL]
    return max(faces) if faces else None


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
