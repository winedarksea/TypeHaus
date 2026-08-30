"""The plan frame of one truss wall's outrigger band, and every piece measured off it.

Split out of :mod:`typehaus.resolve.framing.truss_wall` for file size (AGENTS.md), and the
seam is a real one: this module knows *where* a block, a tab, a filler, a ladder and a buck
go on one wall, and nothing about which walls are truss walls or how the pass is driven.
The constants live here rather than beside the pass because they are dimensions of the
pieces, and every one of them is read by something that only wants the geometry —
``checks/structural/truss_wall.py`` wants the flange bearing, ``takeoff/fasteners.py`` the
block spacing, ``checks/structural/interference.py`` the categories.

``truss_wall`` re-exports the names other modules use, so nothing outside this package has
to know the split happened.
"""

from __future__ import annotations

import math

from typehaus.model.plan import PlanModel
from typehaus.quantities import inch
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.corners import neighbour_band_insets
from typehaus.resolve.framing.furring import band_extent
from typehaus.resolve.framing.profiles import cross_section, panel_profile
from typehaus.resolve.framing.solver import _wall_top_elevations, band_axis
from typehaus.resolve.framing.truss_common import (  # noqa: F401 - re-exported by truss_wall
    BLOCK_CATEGORY,
    BUCK_CATEGORY,
    BUCK_THICKNESS_IN,
    FLANGE_BEARING,
    JAMB_PREFIX,
    LADDER_CATEGORY,
    BandFrame,
    Vec,
    nearest_bearing_gap,
    outward_across,
)
from typehaus.resolve.geometry import length, sub, unit, wall_frame
from typehaus.resolve.intervals import subtract as subtract_spans
from typehaus.resolve.model import (
    FramedMember,
    ResolvedLayer,
    ResolvedOpening,
    ResolvedWall,
)

#: The two categories only the Swinburne pack has. The three both frames share —
#: ``BLOCK_CATEGORY``, ``LADDER_CATEGORY``, ``BUCK_CATEGORY`` — live in ``truss_common`` and
#: are imported above, so a girt's block and an outrigger's block bill on one row.
TAB_CATEGORY = "truss_tab"
#: A jamb FILLER: the rip that closes a gap too small to stand another outrigger in. It is
#: laminated to the outrigger beside it and carries no pack of its own — that outrigger's
#: block and tab hold both — so it is not "held on by air" the way a free-standing member
#: with no pack would be, and it must not be counted as one.
FILLER_CATEGORY = "truss_filler"
#: The Larsen/Swinburne plywood corner box (FHB Jan 2024): two 1/2" rips per owned L
#: corner, closing the band's two outboard faces where its own mitre leaves a full-height
#: void with no framed member in it. Its own category rather than ``TAB_CATEGORY`` (same
#: material, same thickness) because it is billed and rendered as its own line — a corner
#: closure, not a lap piece — and because ``checks/structural/interference`` needs to know
#: it, like every other truss piece, sits outboard of the sheathing.
CORNER_CAP_CATEGORY = "truss_corner_cap"

#: The six together, for ``checks.structural.interference``. One name, one place to be wrong.
TRUSS_CATEGORIES = frozenset({BLOCK_CATEGORY, TAB_CATEGORY, LADDER_CATEGORY, BUCK_CATEGORY,
                              FILLER_CATEGORY, CORNER_CAP_CATEGORY})

#: Block length, and the spacing up an outrigger. Two screws per block into the stud behind it;
#: at 40" o.c. that is 1 block per 3.3 LF of outrigger, against the 24" x 1 screw grid a
#: continuous-insulation fastener schedule assumes (→ ``takeoff/fasteners.py``).
BLOCK_LENGTH = inch(8.0)
BLOCK_SPACING = inch(40.0)

#: Tab stock. 1/2" plywood, cut to the full truss depth so it laps the block over the whole
#: 1-1/2" the block projects and the outrigger over its whole 3-1/2".
TAB_THICKNESS_IN = 0.5
#: Corner box stock — the FHB Jan 2024 detail's "rips of plywood or OSB" — the same 1/2"
#: as the tab, so ``family_of`` resolves it to the same OSB finish.
CORNER_CAP_THICKNESS_IN = 0.5

#: Clear span past which head/sill blocking doubles up. A 60" French door's head blocking
#: spans about 63" between flanking outriggers, which is more than a single 2x4 on edge
#: carries with a window's weight and a snow-loaded head flashing on it.
DOUBLE_HEADER_SPAN = inch(48.0)

#: Gap past which a jamb takes a whole new outrigger instead of plies laminated to the
#: member beside it. Below this there is no room for a free member's block and tab — the
#: pack next door already holds that plan — so a free outrigger there ends up with neither
#: and is fastened to nothing, which is what happened to 20 of catlin's 21 jamb outriggers
#: before 2026-08-23. Six inches is where a pack reliably stops colliding with its
#: neighbour's, and a 4-1/2" build-up at a jamb is an ordinary three-ply jamb post, not an
#: exotic piece. Past it the gap is wide enough to stand a real outrigger over the jack.
FILLER_LIMIT = inch(6.0)

_TOL = 1e-9


class TrussFrame(BandFrame):
    """The plan frame of one truss wall's outrigger band, and the pieces measured off it.

    Holding it as an object rather than threading eight floats through six functions: every
    piece here is placed by the same two numbers — a station along the wall and a depth out
    from the sheathing — and they are worth deriving once. The datum itself, and the two
    pieces that do not care which frame placed them, are ``truss_common.BandFrame``.
    """

    strapping_category = "strapping"

    def __init__(self, wall: ResolvedWall, origin: Vec, direction: Vec, across: Vec,
                 first: float, last: float, band_depth: float,
                 block_material: str | None, band_material: str,
                 run: float = 0.0) -> None:
        super().__init__(wall, origin, direction, across, first, last, band_depth, run)
        self.block_material = block_material
        self.band_material = band_material
        self.outrigger_width = cross_section("2x4").width_m
        self.block_face = cross_section("2x4").depth_m
        self.block_depth = cross_section("2x4").width_m
        self.tab_thickness = inch(TAB_THICKNESS_IN).meters
        self.truss_depth = self.block_depth + band_depth
        # The buck lines the RO from the sheathing face out to the truss plane: 1-1/2" of
        # block plus the 3-1/2" band, so 5" on this wall.
        self.buck_depth = self.truss_depth
        self.buck_centre = self.band_in - self.block_depth + self.truss_depth / 2.0

    @classmethod
    def build(cls, plan: PlanModel, wall: ResolvedWall,
              band: ResolvedLayer) -> TrussFrame | None:
        _origin, _tangent, across, axis_length = wall_frame(wall)
        if axis_length <= _TOL:
            return None
        start, end = band_axis(wall.axis, band.polygon)
        run = length(sub(end, start))
        if run <= _TOL:
            return None
        direction = unit(sub(end, start))
        turned = outward_across(wall, across)
        if turned is None:
            return None
        across = turned
        first, last = band_extent(band.polygon, start, direction, run)
        return cls(wall, start, direction, across, first, last, band.thickness_m,
                   assembly_structure_material(plan, wall.assembly), band.material_ref,
                   run=run)

    # --- the corner box --------------------------------------------------------------
    def corner_box(self, at_start: bool, neighbour_band_polygon) -> FramedMember | None:
        """The plywood rip that closes THIS band's outboard face at an owned L corner.

        Runs from this band's own mitred edge (``first``/``last`` — where every other
        piece in the band stops, because that is where its own wall's cladding stops) out
        to the true building corner: the far face of the *neighbour's* outrigger band,
        projected onto this axis (``corners.neighbour_band_insets``, the same reading
        ``solver.wall_end_framing`` gives the OWNER of an L corner for its stud framing —
        an L corner's owner is the one whose framing runs through the shared square).
        Deliberately placed outside ``[first, last]``: that is the whole point of it,
        closing the void nothing else in this band reaches.

        ``None`` when the neighbour's band cannot be read, or the two already meet with no
        gap to close (a degenerate or unresolved corner).
        """
        outer_inset, _inner_inset = neighbour_band_insets(
            neighbour_band_polygon, self.origin, self.direction, self.run, at_start)
        edge = self.first if at_start else self.last
        corner_station = outer_inset if at_start else self.run - outer_inset
        gap = (edge - corner_station) if at_start else (corner_station - edge)
        if gap <= _TOL:
            return None
        centre = (edge + corner_station) / 2.0
        # The band's own outboard face — flush with the cladding, which is exactly the
        # face this rip closes.
        depth = self.band_mid + self.band_depth / 2.0
        top_start, top_end = _wall_top_elevations(self.wall)
        fraction = centre / self.run if self.run else 0.0
        top = top_start + (top_end - top_start) * fraction
        point = self.point(centre, depth)
        endpoint = "start" if at_start else "end"
        return FramedMember(
            self.wall.uid, f"corner-cap-{endpoint}", CORNER_CAP_CATEGORY,
            panel_profile(gap / 0.0254, CORNER_CAP_THICKNESS_IN, "corner"),
            point, point, self.wall.z0_m, top, top - self.wall.z0_m,
            orient=self.direction, material="struct-1-plywood")

    # --- the three-piece pack ------------------------------------------------------
    @property
    def pack_width(self) -> float:
        """Plan width of one block-and-tab pack — the room an outrigger needs beside it."""
        low, high = self._pack_span(0.0, 1.0)
        return high - low

    def crowded_end_neighbours(self, field: list[FramedMember],
                               loose: tuple[str, ...]) -> tuple[str, ...]:
        """Field outriggers a band END strip is crowded against, when that strip went unpacked.

        The end strips land where the band ends, not on the module, so a wall whose length is
        not a whole number of modules finishes with the last module outrigger and the end
        strip two or three inches apart. Neither can then take its 3-1/2" block and its tab
        without reaching into the other's, and no carpenter stands two studs that close: the
        MODULE one is the one that goes, because the end strip is the cladding's edge nailer
        and the band's mitre and cannot move.

        Read off a **trial pack**, not off the stations alone, and that is the whole care in
        it. Two outriggers inside a pack's width of each other are common and mostly fine —
        the pack is chiral, so the second one takes the other hand and both are fastened. Only
        where the end strip came back with no block and no tab is there a stick to delete, and
        deleting one anywhere else would take framing off walls that are correctly framed.

        Returned as child keys, so the caller drops them from the wall's own field and frames
        again — one fewer stick on the wall and one fewer in the order, rather than a stick the
        model shows fastened to nothing.
        """
        by_station: dict[float, list[str]] = {}
        for member in field:
            by_station.setdefault(round(self.station_of(member), 6), []).append(
                member.child_key)
        stations = sorted(by_station)
        if len(stations) < 2:
            return ()
        unpacked = set(loose)
        dropped: list[str] = []
        for outer, inner in ((0, 1), (-1, -2)):
            if not any(key in unpacked for key in by_station[stations[outer]]):
                continue
            if abs(stations[outer] - stations[inner]) < self.pack_width - _TOL:
                dropped.extend(by_station[stations[inner]])
        return tuple(dict.fromkeys(dropped))

    def pack_all(self, outriggers: list[tuple[FramedMember, float]],
                 voids: list[tuple[float, float, float, float]]
                 ) -> tuple[list[FramedMember], list[tuple[float, float, float, float]],
                            tuple[str, ...]]:
        """Blocks and tabs for every outrigger, and the plan spans the tabs took.

        The pack is *chiral* — block one side of the outrigger, tab the other — so each one
        is placed at whichever hand fits: inside the band's mitred extent, clear of the pack
        beside it, and (at an opening) with the tab outside the glass rather than across it.
        An outrigger with no hand left is one standing within a few inches of another, and
        the pack already there carries both.

        **The occupancy test is 3D**, and has to be: an outrigger cut around a window is two
        segments at the SAME station, one below the sill and one above the head, and a
        plan-only test reads the second as colliding with the first at every hand.

        **The rough openings are dodged per PIECE, in ``_pack``, not per outrigger.** A
        block is 3-1/2" wide on a 1-1/2" outrigger, so a stud one inch off an RO edge
        unavoidably carries a block that laps the opening in plan — but only the block at an
        elevation *between* the sill and the head is actually in the glass, and the ones
        above and below are ordinary wall. Rejecting the whole outrigger for that plan
        overlap left 49 of catlin's outriggers with no block and no tab at all.

        Between them these two were dropping 72 of 447 segments — including 20 of the 21
        jamb outriggers, the members the whole outie window hangs its flange on. An unpacked
        outrigger is not a smaller order; it is a stick of wood held on by air.
        """
        occupied: list[tuple[float, float, float, float]] = []
        members: list[FramedMember] = []
        tabs: list[tuple[float, float, float, float]] = []
        loose: list[str] = []
        for index, (outrigger, prefer) in enumerate(outriggers):
            station = self.station_of(outrigger)
            z0, z1 = outrigger.z0_m, outrigger.z1_m
            placed = None
            for sign in (prefer, -prefer):
                span = self._pack_span(station, sign)
                shifted = self._slide_clear(span, occupied, z0, z1)
                if shifted is None:
                    continue
                shift = shifted[0] - span[0]
                pieces = self._pack(outrigger, index, station, sign, shift, voids)
                if not pieces:
                    continue
                placed = (sign, shift, pieces)
                break
            if placed is None:
                loose.append(outrigger.child_key)
                continue
            sign, shift, pieces = placed
            pack = self._pack_span(station, sign, shift)
            occupied.append((pack[0], pack[1], z0, z1))
            plan = self._tab_span(station, sign, shift)
            # Per PIECE, not per outrigger. A tab is an 8" lap every 40"; recording the
            # outrigger's whole run instead makes every ladder below think there is plywood
            # standing at its elevation when the nearest tab is feet away.
            tabs.extend((plan[0], plan[1], m.z0_m, m.z1_m)
                        for m in pieces if m.category == TAB_CATEGORY)
            members.extend(pieces)
        return members, tabs, tuple(loose)

    def _block_station(self, station: float, sign: float, shift: float = 0.0) -> float:
        return station + sign * (self.block_face - self.outrigger_width) / 2.0 + shift

    def _tab_station(self, station: float, sign: float, shift: float = 0.0) -> float:
        return station - sign * (self.outrigger_width + self.tab_thickness) / 2.0 + shift

    def _tab_span(self, station: float, sign: float, shift: float) -> tuple[float, float]:
        centre = self._tab_station(station, sign, shift)
        return centre - self.tab_thickness / 2.0, centre + self.tab_thickness / 2.0

    def _pack_span(self, station: float, sign: float,
                   shift: float = 0.0) -> tuple[float, float]:
        block = self._block_station(station, sign, shift)
        tab = self._tab_span(station, sign, shift)
        return (min(block - self.block_face / 2.0, tab[0]),
                max(block + self.block_face / 2.0, tab[1]))

    def _slide_clear(self, span: tuple[float, float],
                     occupied: list[tuple[float, float, float, float]],
                     z0: float, z1: float) -> tuple[float, float] | None:
        """``span`` slid the least distance that puts it in the band and clear of every pack.

        The block is 3-1/2" over a 1-1/2" stud, so it can move up to an inch either way and
        still cover that stud completely — which is exactly the room needed where two
        verticals stand a few inches apart (a band end, a jamb outrigger beside a field one)
        and the second pack would otherwise land on the first and be dropped. Past an inch
        the block starts coming off the stud, and the pack is refused instead: half a block
        on bare sheathing is worse than a member the pack beside it also holds.
        """
        width = span[1] - span[0]
        reach = (self.block_face - self.outrigger_width) / 2.0
        candidates = [span]
        for lo, hi, oz0, oz1 in occupied:
            if oz0 >= z1 - _TOL or z0 >= oz1 - _TOL:
                continue
            candidates.append((hi, hi + width))
            candidates.append((lo - width, lo))
        best: tuple[float, tuple[float, float]] | None = None
        for candidate in candidates:
            shifted = self._shift_into_band(candidate)
            if shifted is None or abs(shifted[0] - span[0]) > reach + _TOL:
                continue
            if any(lo < shifted[1] - _TOL and shifted[0] < hi - _TOL
                   and oz0 < z1 - _TOL and z0 < oz1 - _TOL
                   for lo, hi, oz0, oz1 in occupied):
                continue
            move = abs(shifted[0] - span[0])
            if best is None or move < best[0]:
                best = (move, shifted)
        return best[1] if best is not None else None

    def _shift_into_band(self, span: tuple[float, float]) -> tuple[float, float] | None:
        """``span`` slid the least distance that puts it inside the band, or ``None``."""
        lo, hi = span
        if hi - lo > self.last - self.first + _TOL:
            return None
        shift = max(0.0, self.first - lo) - max(0.0, hi - self.last)
        return lo + shift, hi + shift

    def _pack(self, outrigger: FramedMember, index: int, station: float,
              sign: float, shift: float,
              voids: list[tuple[float, float, float, float]]) -> list[FramedMember]:
        """One outrigger's blocks and tabs, at :data:`BLOCK_SPACING` up its length.

        The block sits inboard of the band, its side face flush with the stud's — 1" of the
        wall off the outrigger's centre, since the block is 3-1/2" wide and the outrigger
        1-1/2". The tab lies against that same face from the other side, so it clears both
        pieces in plan while lapping both in depth: 1-1/2" onto the block, 3-1/2" onto the
        outrigger, and it is the only piece that crosses the insulation.

        A block or tab whose own elevation falls inside a rough opening it laps in plan is
        skipped: that one is in the glass, and the rest of the run up the same outrigger is
        not.
        """
        block_point = self.point(self._block_station(station, sign, shift),
                                 self.band_in - self.block_depth / 2.0)
        tab_point = self.point(self._tab_station(station, sign, shift),
                               self.band_in - self.block_depth + self.truss_depth / 2.0)
        block_len = BLOCK_LENGTH.meters
        pack_lo, pack_hi = self._pack_span(station, sign, shift)
        out: list[FramedMember] = []
        for count, z0 in enumerate(_stations(outrigger.z0_m, outrigger.z1_m,
                                             BLOCK_SPACING.meters, block_len)):
            if any(lo < pack_hi - _TOL and pack_lo < hi - _TOL
                   and vz0 < z0 + block_len - _TOL and z0 < vz1 - _TOL
                   for lo, hi, vz0, vz1 in voids):
                continue
            key = f"truss-{index:03d}-{count:02d}"
            out.append(FramedMember(
                self.wall.uid, f"block-{key}", BLOCK_CATEGORY, "2x4",
                block_point, block_point, z0, z0 + block_len, block_len,
                orient=self.across, material=self.block_material))
            out.append(FramedMember(
                self.wall.uid, f"tab-{key}", TAB_CATEGORY,
                panel_profile(self.truss_depth / 0.0254, TAB_THICKNESS_IN),
                tab_point, tab_point, z0, z0 + block_len, block_len,
                orient=self.across, material="struct-1-plywood"))
        return out

    # --- openings ------------------------------------------------------------------
    def jamb_outriggers(self, opening: ResolvedOpening, index: int,
                        stations: list[tuple[float, float, float]]
                        ) -> tuple[tuple[float, float], list[tuple[FramedMember, float]],
                                   list[FramedMember]]:
        """What the window's flanges bear on at each jamb, and whatever had to be added.

        Returns ``((left face, right face), [(member, preferred pack hand)], [filler, ...])``
        — the two FACES the head and sill blocking runs between, not the two centrelines, so
        a support that is not a whole outrigger can still say where the blocking stops.

        Three cases, and the middle one is the reason this is not a two-liner:

        * **The grid already serves it.** An outrigger face within a flange's bearing of the
          RO edge. Nothing is added. On a 16" module this is every 14", 30" and 38" RO.
        * **The gap is smaller than an outrigger.** A 27" RO centred on a stud line leaves
          1-3/4" at each jamb: too far for the flange, too near to stand another 1-1/2"
          member in — its block and tab would have to occupy plan the pack beside it already
          holds, and it would end up with neither. What a framer cuts here is a **rip**
          filling the gap, laminated to the outrigger's face. It carries no pack because the
          outrigger it is nailed to carries one.
        * **The gap is a whole outrigger or more.** A full jamb outrigger over the jack, half
          an outrigger plus a tab outboard of the RO edge — the offset that lands the pack's
          tab exactly ON the RO edge and its block over the king beyond, rather than half an
          inch of plywood standing in front of the glass.
        """
        half = opening.width_m / 2.0
        jambs = (opening.center_along_m - half, opening.center_along_m + half)
        z_sill = self.wall.base_ref_z_m + opening.sill_m
        z_head = z_sill + opening.height_m
        faces: list[float] = []
        added: list[tuple[FramedMember, float]] = []
        fillers: list[FramedMember] = []
        half_out = self.outrigger_width / 2.0
        spans = [(station - half_out, station + half_out, z0, z1)
                 for station, z0, z1 in stations]
        for side, jamb in enumerate(jambs):
            inward = 1.0 if side == 0 else -1.0
            outward = -inward
            found = nearest_bearing_gap(jamb, spans, z_sill, z_head)
            gap, near_face = found if found is not None else (None, 0.0)
            if gap is not None and gap <= FLANGE_BEARING.meters + _TOL:
                faces.append(near_face)
                continue
            if gap is not None and gap < FILLER_LIMIT.meters:
                # One or more plies of the same 2x4, laminated to that member's face and
                # running TOWARD the jamb, until what is left is inside a flange's bearing.
                # Not a ripped-to-fit piece: a filler is stock nailed on, and the remainder
                # is the shim it always is on a job. Two plies close a 4" gap to 1".
                toward = 1.0 if jamb > near_face else -1.0
                plies = max(1, math.ceil((gap - FLANGE_BEARING.meters)
                                         / self.outrigger_width - _TOL))
                width = plies * self.outrigger_width
                point = self.point(near_face + toward * width / 2.0, self.band_mid)
                fillers.append(FramedMember(
                    self.wall.uid, f"filler-{index:03d}-{side}", FILLER_CATEGORY,
                    "2x4" if plies == 1 else f"{plies}-2x4",
                    point, point, z_sill, z_head, z_head - z_sill,
                    orient=self.direction, material=self.band_material))
                faces.append(near_face + toward * width)
                continue
            # Half an outrigger plus a tab outboard of the RO edge. Half an outrigger is
            # where the jack stands; the extra tab thickness is what lets the pack's tab
            # land exactly ON the RO edge and its block over the king beyond, instead of
            # half an inch of plywood standing in front of the glass. The outrigger's inner
            # face is then 1/2" clear of the jamb — inside :data:`FLANGE_BEARING`, so the
            # flange still bears — and nothing in the pack crosses the opening.
            station = jamb + outward * (self.outrigger_width / 2.0 + self.tab_thickness)
            faces.append(station + inward * self.outrigger_width / 2.0)
            point = self.point(station, self.band_mid)
            added.append((FramedMember(
                self.wall.uid, f"{JAMB_PREFIX}{index:03d}-{side}",
                self.strapping_category, "2x4", point, point,
                self.wall.z0_m, z_head, z_head - self.wall.z0_m,
                orient=self.direction, material=self.band_material), outward))
        return (min(faces), max(faces)), added, fillers

    def ladder(self, supports: tuple[float, float], opening: ResolvedOpening, index: int,
               tabs: list[tuple[float, float, float, float]]) -> list[FramedMember]:
        """Head and sill blocking in the truss plane, fitted between the two jamb supports.

        ``supports`` is the pair of FACES ``jamb_outriggers`` returned, so the run is
        already face to face and this does not re-derive it from a centreline — a jamb
        filler is not half an outrigger wide and a centreline would misplace it.

        Fitted, not lapped: it runs face to face between the two supports, and gives way to
        any tab genuinely standing in its path. The window's head and sill flanges bear on
        it, so it is doubled where the clear span is long enough that a single 2x4 on edge
        would not carry them.

        **A tab is only in the way if it is at this piece's own elevation.** Trimming the
        run against every tab on the wall — which is what this did until 2026-08-23 — left
        one 15-1/2" stub at every opening in the house regardless of its width, so a 60"
        door's flange bore on wood over a quarter of its head and the KDAT order was 80 LF
        short. And where a tab genuinely does stand in the run (a field outrigger cut at the
        head has its lowest tab right there), the answer is the pieces on either side of it,
        not the last bay: this returns every surviving sub-span, so the blocking is as
        continuous as the truss lets it be and the take-off counts what is really cut.
        """
        a, b = supports
        if b - a <= _TOL:
            return []
        z_sill = self.wall.base_ref_z_m + opening.sill_m
        z_head = z_sill + opening.height_m
        profile = "2-2x4" if b - a > DOUBLE_HEADER_SPAN.meters else "2x4"
        thickness = cross_section(profile).width_m
        out: list[FramedMember] = []
        for name, z0 in (("head", z_head), ("sill", z_sill - thickness)):
            z1 = z0 + thickness
            cuts = [(tab_lo, tab_hi) for tab_lo, tab_hi, tz0, tz1 in tabs
                    if tz0 < z1 - _TOL and z0 < tz1 - _TOL]
            for count, (seg_a, seg_b) in enumerate(subtract_spans(a, b, cuts)):
                span = seg_b - seg_a
                if span <= _TOL:
                    continue
                out.append(FramedMember(
                    self.wall.uid, f"ladder-{name}-{index:03d}-{count:02d}",
                    LADDER_CATEGORY, profile,
                    self.point(seg_a, self.band_mid), self.point(seg_b, self.band_mid),
                    z0, z1, span, material=self.band_material))
        return out


def _stations(z0: float, z1: float, spacing: float, piece: float) -> list[float]:
    """Block bottoms up one outrigger run: one at each end, the rest spread evenly between.

    ``spacing`` is a MAXIMUM, not a rhythm to hold until the run ends. Laying blocks out at
    exactly the spacing and then forcing one more against the top gave every run a short last
    bay — a 9'-0" outrigger came out 0/40/80/100, four blocks with 20" between the last two —
    which is a block nobody would cut and a screw count an estimator cannot reconcile against
    the "40 in o.c." the schedule prints. Dividing the run into the fewest bays that all
    clear the maximum gives 0/33/67/100 for the same stick: the same four blocks, evenly
    spread, and the basis stays true.

    Both ends are always blocked. An outrigger held only at the bottom is a lever, and a run
    is a *segment* — the piece above a window head is its own stick and needs its own two.
    """
    run = z1 - z0 - piece
    if run < -_TOL:
        return []
    if run <= _TOL:
        return [z0]
    bays = max(1, math.ceil(run / spacing - _TOL))
    step = run / bays
    return [z0 + index * step for index in range(bays + 1)]
