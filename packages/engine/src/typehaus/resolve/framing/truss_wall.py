"""The intermittent truss that holds a truss wall's cladding off the sheathing (→ 11 §Framing).

A Swinburne truss wall replaces continuous rigid insulation and its 8" structural screws with
spray foam and a *discontinuous* wooden truss. Three pieces make one node:

* a **block** — a 2x4 laid flat against the sheathing, long axis vertical, 3-1/2" on the wall
  and 1-1/2" out from it, slid sideways so one side face is flush with the stud's face. Its
  screws land squarely over the stud;
* a **tab** — 1/2" plywood lying against that flush face, the only piece that crosses the
  insulation zone, and intermittent even there;
* the **outrigger** — a KDAT 2x4 stood on edge in the furring band, lap-screwed to the tab's
  inner face, which lands it centred on the stud line.

The outriggers themselves are not framed here: they are a FURRING layer with a ``FramingSpec``
carrying ``laid="edge"``, and ``framing/furring.py`` lays them out on their own grid like any
other batten. This pass runs *after* it and reads what it framed, which is what keeps the
blocks under the outriggers they actually carry rather than on a grid of their own that would
drift the moment a wall's length or a window's position changed.

Openings get the rest of it. A truss wall's windows are **outie**: the unit sits in the truss
plane with its flanges bearing on the outriggers, not in the stud plane. So every rough
opening also needs

* head and sill **blocking** between the two flanking outriggers, in the truss plane;
* a **jamb outrigger** wherever the 16" field grid puts no outrigger within flange-bearing
  distance of the RO edge — with its own block and tab, over the king stud beside the jack;
* a non-structural 3/8" plywood **buck** lining the RO on all four sides, sheathing face out
  to the truss plane. It closes the foam, faces the reveal, and carries the pan and the head
  flashing.

Everything here is derived. Nothing about a truss wall is authored on a wall or a window, and
no window carries a wall-normal coordinate: the mount plane *is* the outer face of the
outermost FURRING layer, so it follows the assembly.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.enums import LayerFunction
from typehaus.model.plan import PlanModel
from typehaus.quantities import inch
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.framing.furring import EDGE, VERTICAL, band_extent
from typehaus.resolve.framing.profiles import cross_section, panel_profile
from typehaus.resolve.framing.solver import band_axis
from typehaus.resolve.geometry import add, length, scale, sub, unit, wall_frame
from typehaus.resolve.model import (
    FramedMember,
    ResolvedLayer,
    ResolvedModel,
    ResolvedOpening,
    ResolvedWall,
)

#: A plan-frame point or unit vector, in metres (``resolve/geometry``'s convention).
Vec = tuple[float, float]

#: Categories the truss pieces bill under. Each is its own rather than folded into the
#: existing ``blocking``/``strapping`` rows, for two reasons that point the same way. A
#: 3-1/2" block, a 1/2" plywood tab, a 3/8" buck and a doubled ladder head are four different
#: purchases, and one ``blocking`` row over all of them says nothing an estimator can act on.
#: And none of them carries structural load — they carry cladding and a window — which
#: ``checks/structural/interference`` has to know: they sit OUTBOARD of the sheathing, where
#: the model's floor joists and eave stiffeners are laid to the wall's *axis* rather than its
#: face (defect D3), so a shared square inch there is that datum offset and not the
#: elevation-arithmetic bug that check exists to catch.
BLOCK_CATEGORY = "truss_block"
TAB_CATEGORY = "truss_tab"
LADDER_CATEGORY = "truss_blocking"
BUCK_CATEGORY = "buck"

#: The four together, for ``checks.structural.interference``. One name, one place to be wrong.
TRUSS_CATEGORIES = frozenset({BLOCK_CATEGORY, TAB_CATEGORY, LADDER_CATEGORY, BUCK_CATEGORY})

#: Block length, and the spacing up an outrigger. Two screws per block into the stud behind it;
#: at 40" o.c. that is 1 block per 3.3 LF of outrigger, against the 24" x 1 screw grid a
#: continuous-insulation fastener schedule assumes (→ ``takeoff/fasteners.py``).
BLOCK_LENGTH = inch(8.0)
BLOCK_SPACING = inch(40.0)

#: Tab stock. 1/2" plywood, cut to the full truss depth so it laps the block over the whole
#: 1-1/2" the block projects and the outrigger over its whole 3-1/2". Buck stock is 3/8",
#: non-structural, lining the RO from the sheathing face out to the truss plane.
TAB_THICKNESS_IN = 0.5
BUCK_THICKNESS_IN = 0.375

#: How far a rough-opening jamb may sit from the nearest outrigger face and still have the
#: window's nailing flange land on wood. A flange is about 1-1/4" wide, so 1" of gap is the
#: last position where a screw through it still bites. ``checks/structural`` reads the same
#: constant, so the check and the emitter cannot disagree about which jambs are supported.
FLANGE_BEARING = inch(1.0)

#: Clear span past which head/sill blocking doubles up. A 60" French door's head blocking
#: spans about 63" between flanking outriggers, which is more than a single 2x4 on edge
#: carries with a window's weight and a snow-loaded head flashing on it.
DOUBLE_HEADER_SPAN = inch(48.0)

_TOL = 1e-9


def frame_truss_walls(plan: PlanModel, model: ResolvedModel) -> None:
    """Attach blocks, tabs, opening ladders and bucks to every truss wall in the model.

    Silent by design — there is no authoring mistake this pass can catch that
    ``frame_furring`` has not already reported, and the one real question (does every RO jamb
    reach an outrigger?) is a *check*, ``structural.truss_wall_opening_support``, not a
    resolve-time finding. A resolver that reported it here would fire once per wall per
    build; the check fires once, with the section it is answerable against.
    """
    by_host: dict[str, list[ResolvedOpening]] = {}
    for opening in model.openings:
        by_host.setdefault(opening.host_wall, []).append(opening)

    framed: list[ResolvedWall] = []
    for wall in model.walls:
        members = frame_wall_truss(plan, wall, by_host.get(wall.tag, []))
        framed.append(replace(wall, members=wall.members + members) if members else wall)
    model.walls = framed


def truss_layer_name(plan: PlanModel, assembly_tag: str | None) -> str | None:
    """The name of the FURRING layer that is a truss wall's outrigger band, or ``None``.

    The signature is a vertical FURRING layer whose ``FramingSpec`` stands the stick on edge:
    a batten laid flat is a rainscreen strip and frames nothing but itself. Read off the
    *authored* assembly, so a check can ask the question without a resolved wall in hand.
    """
    assembly = plan.library.resolve_assembly(assembly_tag) if assembly_tag else None
    if assembly is None:
        return None
    for layer in assembly.layers:
        spec = layer.framing
        if (layer.function is LayerFunction.FURRING and spec is not None
                and spec.laid == EDGE
                and (spec.direction or VERTICAL).strip().lower() == VERTICAL):
            return layer.name
    return None


def frame_wall_truss(plan: PlanModel, wall: ResolvedWall,
                     openings: list[ResolvedOpening]) -> tuple[FramedMember, ...]:
    """Every truss piece on one wall, or ``()`` if the wall is not a truss wall.

    Order matters and is the whole of the sequencing here. The jamb outriggers come first,
    because they are outriggers and carry packs like any other; the packs come next, because
    where their tabs land is not knowable until they are placed; and the ladder blocking and
    the bucks come last, because both have to give way to a tab rather than run through one.
    """
    layer_name = truss_layer_name(plan, wall.assembly)
    if layer_name is None:
        return ()
    band = next((layer for layer in wall.layers if layer.name == layer_name
                 and layer.polygon), None)
    if band is None:
        return ()
    frame = _TrussFrame.build(plan, wall, band)
    if frame is None:
        return ()

    field = [member for member in wall.members
             if member.child_key.startswith(f"strapping-{layer_name}-")]
    stations = sorted(frame.station_of(member) for member in field)

    members: list[FramedMember] = []
    packable: list[tuple[FramedMember, float]] = [(member, 1.0) for member in field]
    supports: list[tuple[float, float]] = []
    for index, opening in enumerate(openings):
        jambs, added = frame.jamb_outriggers(opening, index, stations)
        supports.append(jambs)
        members.extend(member for member, _prefer in added)
        packable.extend(added)

    # The rough openings, as plan-and-elevation voids no block or tab may reach into. A
    # field outrigger is already cut around an opening, so its pack cannot land in one; a
    # JAMB outrigger runs past the RO from the sole plate to the head, and without this its
    # 3-1/2" block would swing straight across the glass whenever the hand it wanted was
    # taken by the pack next door.
    voids = [(opening.center_along_m - opening.width_m / 2.0,
              opening.center_along_m + opening.width_m / 2.0,
              wall.z0_m + opening.sill_m,
              wall.z0_m + opening.sill_m + opening.height_m)
             for opening in openings]
    packs, tabs = frame.pack_all(packable, voids)
    members.extend(packs)

    for index, opening in enumerate(openings):
        members.extend(frame.ladder(supports[index], opening, index, tabs))
        members.extend(frame.buck(opening, index))
    return tuple(members)


class _TrussFrame:
    """The plan frame of one truss wall's outrigger band, and the pieces measured off it.

    Holding it as an object rather than threading eight floats through six functions: every
    piece here is placed by the same two numbers — a station along the wall and a depth out
    from the sheathing — and they are worth deriving once.
    """

    strapping_category = "strapping"

    def __init__(self, wall: ResolvedWall, origin: Vec, direction: Vec, across: Vec,
                 first: float, last: float, band_depth: float,
                 block_material: str | None, band_material: str) -> None:
        self.wall = wall
        self.origin = origin            # band centreline start, in plan
        self.direction = direction      # unit vector along the wall
        self.across = across            # unit vector, sheathing -> cladding
        # The band's own first and last station, mitred into its neighbours — the same
        # extent ``frame_furring`` holds the outriggers inside. A block is 3-1/2" wide and
        # sits 1" off its outrigger's centre, so without this it would happily reach past
        # the mitre and into the next wall's truss.
        self.first, self.last = first, last
        # Every depth in this class is a signed offset along ``across`` in the plan frame,
        # measured from the same origin the band centreline is on. One datum, so a block and
        # a buck cannot disagree about where the sheathing face is.
        self.band_mid = origin[0] * across[0] + origin[1] * across[1]
        self.band_depth = band_depth
        self.band_in = self.band_mid - band_depth / 2.0
        self.block_material = block_material
        self.band_material = band_material
        self.outrigger_width = cross_section("2x4").width_m
        self.block_face = cross_section("2x4").depth_m
        self.block_depth = cross_section("2x4").width_m
        self.tab_thickness = inch(TAB_THICKNESS_IN).meters
        self.truss_depth = self.block_depth + band_depth
        self.buck_thickness = inch(BUCK_THICKNESS_IN).meters

    @classmethod
    def build(cls, plan: PlanModel, wall: ResolvedWall,
              band: ResolvedLayer) -> _TrussFrame | None:
        _origin, _tangent, across, axis_length = wall_frame(wall)
        if axis_length <= _TOL:
            return None
        start, end = band_axis(wall.axis, band.polygon)
        run = length(sub(end, start))
        if run <= _TOL:
            return None
        direction = unit(sub(end, start))
        # Which way is out. The stack resolves interior -> exterior, so the outermost body
        # layer is further along the wall's own normal than the innermost by exactly the
        # amount that names the sign. Reading it off the geometry rather than off
        # ``outward_sign`` keeps this pass independent of how the topology solver spelled it.
        bodies = [layer for layer in wall.layers if not layer.is_cavity and layer.polygon]
        if len(bodies) < 2:
            return None
        inner, outer = _mean_offset(bodies[0], across), _mean_offset(bodies[-1], across)
        if outer < inner:
            across = (-across[0], -across[1])
        first, last = band_extent(band.polygon, start, direction, run)
        return cls(wall, start, direction, across, first, last, band.thickness_m,
                   assembly_structure_material(plan, wall.assembly), band.material_ref)

    # --- placement -----------------------------------------------------------------
    def point(self, station: float, depth: float) -> Vec:
        """The plan point at ``station`` along the band, at signed ``depth`` across it."""
        return add(add(self.origin, scale(self.direction, station)),
                   scale(self.across, depth - self.band_mid))

    def station_of(self, member: FramedMember) -> float:
        """Where along the band a vertical member of this frame stands."""
        offset = sub(member.p0, self.origin)
        return float(offset[0] * self.direction[0] + offset[1] * self.direction[1])

    # --- the three-piece pack ------------------------------------------------------
    def pack_all(self, outriggers: list[tuple[FramedMember, float]],
                 voids: list[tuple[float, float, float, float]]
                 ) -> tuple[list[FramedMember], list[tuple[float, float]]]:
        """Blocks and tabs for every outrigger, and the plan spans the tabs took.

        The pack is *chiral* — block one side of the outrigger, tab the other — so each one
        is placed at whichever hand fits: inside the band's mitred extent, clear of the pack
        beside it, and (at an opening) with the tab outside the glass rather than across it.
        An outrigger with no hand left is one standing within a few inches of another, and
        the pack already there carries both.
        """
        occupied: list[tuple[float, float]] = []
        members: list[FramedMember] = []
        tabs: list[tuple[float, float]] = []
        for index, (outrigger, prefer) in enumerate(outriggers):
            station = self.station_of(outrigger)
            placed = None
            for sign in (prefer, -prefer):
                span = self._pack_span(station, sign)
                shifted = self._shift_into_band(span)
                if shifted is None:
                    continue
                if any(lo < shifted[1] - _TOL and shifted[0] < hi - _TOL
                       for lo, hi in occupied):
                    continue
                if any(lo < shifted[1] - _TOL and shifted[0] < hi - _TOL
                       and z0 < outrigger.z1_m - _TOL and outrigger.z0_m < z1 - _TOL
                       for lo, hi, z0, z1 in voids):
                    continue
                placed = (sign, shifted[0] - span[0])
                break
            if placed is None:
                continue
            sign, shift = placed
            occupied.append(self._pack_span(station, sign, shift))
            tabs.append(self._tab_span(station, sign, shift))
            members.extend(self._pack(outrigger, index, station, sign, shift))
        return members, tabs

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

    def _shift_into_band(self, span: tuple[float, float]) -> tuple[float, float] | None:
        """``span`` slid the least distance that puts it inside the band, or ``None``."""
        lo, hi = span
        if hi - lo > self.last - self.first + _TOL:
            return None
        shift = max(0.0, self.first - lo) - max(0.0, hi - self.last)
        return lo + shift, hi + shift

    def _pack(self, outrigger: FramedMember, index: int, station: float,
              sign: float, shift: float) -> list[FramedMember]:
        """One outrigger's blocks and tabs, at :data:`BLOCK_SPACING` up its length.

        The block sits inboard of the band, its side face flush with the stud's — 1" of the
        wall off the outrigger's centre, since the block is 3-1/2" wide and the outrigger
        1-1/2". The tab lies against that same face from the other side, so it clears both
        pieces in plan while lapping both in depth: 1-1/2" onto the block, 3-1/2" onto the
        outrigger, and it is the only piece that crosses the insulation.
        """
        block_point = self.point(self._block_station(station, sign, shift),
                                 self.band_in - self.block_depth / 2.0)
        tab_point = self.point(self._tab_station(station, sign, shift),
                               self.band_in - self.block_depth + self.truss_depth / 2.0)
        block_len = BLOCK_LENGTH.meters
        out: list[FramedMember] = []
        for count, z0 in enumerate(_stations(outrigger.z0_m, outrigger.z1_m,
                                             BLOCK_SPACING.meters, block_len)):
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
    def jamb_outriggers(self, opening: ResolvedOpening, index: int, stations: list[float]
                        ) -> tuple[tuple[float, float], list[tuple[FramedMember, float]]]:
        """The two members the window's flanges bear on, and any that had to be added.

        Returns ``((left station, right station), [(member, preferred pack hand)])``. A jamb
        outrigger stands directly over the *jack* — half an outrigger outboard of the RO edge
        — with its tab and block over the *king* beside it, which is why the preferred hand
        is the one that throws the tab away from the glass.
        """
        half = opening.width_m / 2.0
        jambs = (opening.center_along_m - half, opening.center_along_m + half)
        z_head = self.wall.z0_m + opening.sill_m + opening.height_m
        supports: list[float] = []
        added: list[tuple[FramedMember, float]] = []
        for side, jamb in enumerate(jambs):
            gap = nearest_outrigger_gap(jamb, stations, self.outrigger_width)
            if gap is not None and gap <= FLANGE_BEARING.meters + _TOL:
                jamb_station = jamb
                supports.append(min(stations,
                                    key=lambda s: abs(s - jamb_station)))
                continue
            outward = -1.0 if side == 0 else 1.0
            # Half an outrigger plus a tab outboard of the RO edge. Half an outrigger is
            # where the jack stands; the extra tab thickness is what lets the pack's tab
            # land exactly ON the RO edge and its block over the king beyond, instead of
            # half an inch of plywood standing in front of the glass. The outrigger's inner
            # face is then 1/2" clear of the jamb — inside :data:`FLANGE_BEARING`, so the
            # flange still bears — and nothing in the pack crosses the opening.
            station = jamb + outward * (self.outrigger_width / 2.0 + self.tab_thickness)
            supports.append(station)
            point = self.point(station, self.band_mid)
            added.append((FramedMember(
                self.wall.uid, f"strapping-jamb-{index:03d}-{side}",
                self.strapping_category, "2x4", point, point,
                self.wall.z0_m, z_head, z_head - self.wall.z0_m,
                orient=self.direction, material=self.band_material), outward))
        return (min(supports), max(supports)), added

    def ladder(self, supports: tuple[float, float], opening: ResolvedOpening, index: int,
               tabs: list[tuple[float, float]]) -> list[FramedMember]:
        """Head and sill blocking in the truss plane, fitted between the two flanking outriggers.

        Fitted, not lapped: it runs face to face, and gives way to any tab standing in the
        way of an end. The window's head and sill flanges bear on it, so it is doubled where
        the span is long enough that a single 2x4 on edge would not carry them.
        """
        lo, hi = supports
        a = lo + self.outrigger_width / 2.0
        b = hi - self.outrigger_width / 2.0
        for tab_lo, tab_hi in tabs:
            if tab_hi <= a + _TOL or tab_lo >= b - _TOL:
                continue
            if tab_lo - a <= b - tab_hi:
                a = max(a, tab_hi)
            else:
                b = min(b, tab_lo)
        span = b - a
        if span <= _TOL:
            return []
        z_sill = self.wall.z0_m + opening.sill_m
        z_head = z_sill + opening.height_m
        profile = "2-2x4" if hi - lo > DOUBLE_HEADER_SPAN.meters else "2x4"
        thickness = cross_section(profile).width_m
        p_a, p_b = self.point(a, self.band_mid), self.point(b, self.band_mid)
        return [FramedMember(
            self.wall.uid, f"ladder-{name}-{index:03d}", LADDER_CATEGORY, profile,
            p_a, p_b, z0, z0 + thickness, span, material=self.band_material)
            for name, z0 in (("head", z_head), ("sill", z_sill - thickness))]

    def buck(self, opening: ResolvedOpening, index: int) -> list[FramedMember]:
        """3/8" plywood lining the RO on all four sides, sheathing face out to the truss plane.

        Non-structural — it closes the foam at the reveal, gives the reveal a face, and
        carries the sill pan and the head flashing. Bills as a panel, never as lumber. And it
        goes in BEFORE the foam: with no WRB in the stack, the ccSPF is the water plane, and
        it can only be continuous around an opening if the buck is already there to spray to.
        """
        profile = panel_profile(self.truss_depth / 0.0254, BUCK_THICKNESS_IN)
        thickness = self.buck_thickness
        centre = self.band_in - self.block_depth + self.truss_depth / 2.0
        half = opening.width_m / 2.0
        lo, hi = opening.center_along_m - half, opening.center_along_m + half
        z_sill = self.wall.z0_m + opening.sill_m
        z_head = z_sill + opening.height_m
        p_a, p_b = self.point(lo, centre), self.point(hi, centre)
        out: list[FramedMember] = []
        # Head and sill line the RO from *inside* it, so the flashing above and the blocking
        # below land on the buck's back rather than clashing through it.
        for name, z0 in (("head", z_head - thickness), ("sill", z_sill)):
            out.append(FramedMember(
                self.wall.uid, f"buck-{name}-{index:03d}", BUCK_CATEGORY, profile,
                p_a, p_b, z0, z0 + thickness, hi - lo, material="struct-1-plywood"))
        z0, z1 = z_sill + thickness, z_head - thickness
        if z1 - z0 > _TOL:
            for side, jamb in enumerate((lo, hi)):
                inward = 1.0 if side == 0 else -1.0
                point = self.point(jamb + inward * thickness / 2.0, centre)
                out.append(FramedMember(
                    self.wall.uid, f"buck-jamb-{index:03d}-{side}", BUCK_CATEGORY, profile,
                    point, point, z0, z1, z1 - z0,
                    orient=self.across, material="struct-1-plywood"))
        return out


def nearest_outrigger_gap(jamb: float, stations: list[float],
                          outrigger_width: float) -> float | None:
    """Clear gap from an RO jamb to the nearest outrigger *face*, or ``None`` with no outriggers.

    Zero when an outrigger straddles the jamb — the flange lands squarely on wood — and the
    distance to the nearer face otherwise. Shared by this pass and
    ``checks.structural.truss_wall_opening_support`` so both answer the question the same way.
    """
    if not stations:
        return None
    half = outrigger_width / 2.0
    return min(max(0.0, abs(station - jamb) - half) for station in stations)


def _stations(z0: float, z1: float, spacing: float, piece: float) -> list[float]:
    """Block bottoms from ``z0`` up, on centre, with one always at the top of the run."""
    if z1 - z0 < piece:
        return []
    out = [z0]
    index = 1
    while z0 + index * spacing + piece <= z1 - piece + _TOL:
        out.append(z0 + index * spacing)
        index += 1
    if z1 - piece - out[-1] > piece - _TOL:
        out.append(z1 - piece)
    return out


def _mean_offset(layer: ResolvedLayer, across: Vec) -> float:
    """A layer band's mean signed offset along ``across``, in the plan frame."""
    points = list(layer.polygon)
    return float(sum(x * across[0] + y * across[1] for x, y in points) / len(points))


