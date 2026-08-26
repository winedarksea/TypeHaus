"""The catlin truss's geometry, asserted at the numbers the notes claim.

`resolve/framing/truss_girts.py` replaced the Swinburne outrigger pack on 2026-08-26 with two
tiers of flat horizontal 2x4 girts, each course bearing on 3-1/2" blocks at the stud module.
It is a different *kind* of geometry problem from the pack it replaced — that one was
chirality and collision in plan, this one is pairing and continuity in elevation — so it gets
its own module rather than a branch inside `test_truss_wall_geometry.py`, which now runs the
retired frame on a synthetic fixture (`conftest.swinburne_model`).

Five claims, each of which is a build fact somebody would otherwise find on site:

* **a block is under a stud.** The girt courses climb their own 24" elevation module, but the
  blocks that carry them back to the framing land on the 16" STUD module — and block-2 on
  that module plus half a bay, which is the offset scheme the whole fastening story rests on
  (`notes/catlin_truss_engineering.md` §3);
* **a course is supported at both ends and everywhere between**, so no girt is a cantilever
  and no block bears on nothing;
* **the two tiers are one course.** Same elevations, same segments — block-2 screws into the
  inner girt, and a half-inch disagreement is a screw into air;
* **a course runs THROUGH a facade seam.** A girt is one stick on the job; the tee a facade is
  authored at is an artifact of where the partitions land inside, and a course that stopped
  half a board short on each side of it would leave a 3" notch in every course at every tee;
* **every rough opening has its own frame** — two jamb posts per band with their inner faces
  on the RO edge, head and sill courses spanning it, a 6" buck on four sides — and nothing
  anywhere reaches into the glass.
"""

from __future__ import annotations

import re

import pytest

from typehaus.resolve.framing.furring import course_elevations
from typehaus.resolve.framing.truss_wall import (
    FLANGE_BEARING,
    GirtFrame,
    truss_girt_bands,
    truss_kind,
)
from typehaus.resolve.geometry import sub, unit

IN = 0.0254
_STOCK_FACE = 3.5 * IN     # a course's height, a post's width, a block's face
_STUD_SPACING = 16.0 * IN
_COURSE_SPACING = 24.0 * IN

#: Everything the framing solver emits as a vertical stick on (or beside) the stud module.
#: A block screwed "over a stud" may equally land on a king, a jack or a cripple — the same
#: 1-1/2" of wood in the same plane — and testing only ``stud`` reports every block over a
#: header or under a rough sill as landing on nothing.
_STUDLIKE = ("stud", "king", "jack", "cripple", "corner", "trimmer")

#: And everything it emits as a member running ALONG the wall. A block landing on one of
#: these is on wood the whole width of the wall, so the module cannot miss it — which is why
#: a block over a header or under a rough sill is excluded from the stud-lap measurement
#: rather than counted as landing on nothing.
_HORIZONTAL = ("plate", "raked_plate", "header", "sill", "blocking")

#: A FIELD block's child key — ``block-{tier}-{course:03d}-{n:02d}``. The jamb-post and
#: head/sill blocks an opening adds are ``block-{tier}-jamb-...`` / ``-head-`` / ``-sill-``
#: and are deliberately not on the field module.
_FIELD_BLOCK = re.compile(r"^block-[12]-\d{3}-\d{2}$")


def _girt_walls(model):
    return [w for w in model.walls if truss_kind(model.plan, w.assembly) == "girt"]


def _bands(model, wall):
    """``(inner, outer)`` band NAMES for one girt wall."""
    inner, outer = truss_girt_bands(model.plan, wall.assembly)
    return inner.name, outer.name


def _frame(model, wall) -> GirtFrame:
    inner_name, outer_name = _bands(model, wall)
    resolved = {ly.name: ly for ly in wall.layers if ly.polygon}
    frame = GirtFrame.build(model.plan, wall, resolved[inner_name], resolved[outer_name],
                            None, (None, None))
    assert frame is not None, wall.tag
    return frame


def _station(member, wall, end: int = 0):
    direction = unit(sub(wall.axis[1], wall.axis[0]))
    point = member.p0 if end == 0 else member.p1
    offset = sub(point, wall.axis[0])
    return offset[0] * direction[0] + offset[1] * direction[1]


def _tier(member) -> str | None:
    from typehaus.resolve.framing.truss_wall import girt_block_tier

    return girt_block_tier(member.child_key)


def _courses(wall, band_name):
    """Field course segments of one band, as ``(z0, lo_station, hi_station, member)``."""
    direction = unit(sub(wall.axis[1], wall.axis[0]))

    def station(point):
        offset = sub(point, wall.axis[0])
        return offset[0] * direction[0] + offset[1] * direction[1]

    out = []
    for member in wall.members:
        if not member.child_key.startswith(f"strapping-{band_name}-"):
            continue
        lo, hi = sorted((station(member.p0), station(member.p1)))
        out.append((member.z0_m, lo, hi, member))
    return sorted(out)


def _openings(model, wall):
    return [op for op in model.openings if op.host_wall == wall.tag]


def _modal_phase(stations_in: list[float]) -> float:
    """The 16"-phase most of these stations share, in inches.

    A girt wall carries off-module blocks on purpose — one at each free course end, one
    under each jamb post, and one snapped onto a cripple the opening's own rhythm put two
    inches off the wall's — so an average or a median over all of them reports a grid that is
    not there. The mode is the grid.
    """
    counts: dict[float, int] = {}
    for station in stations_in:
        key = round(station % 16.0, 4)
        counts[key] = counts.get(key, 0) + 1
    return max(counts.items(), key=lambda item: (item[1], -item[0]))[0]


# --- the wall is a girt wall at all --------------------------------------------------


def test_the_house_has_girt_walls_at_all(catlin_model):
    """Guard the rest of the module: every assertion below is vacuous without these."""
    walls = _girt_walls(catlin_model)
    assert len(walls) >= 30, "catlin's main/second/attic exterior walls are all girt walls"
    assert not [w for w in catlin_model.walls
                if truss_kind(catlin_model.plan, w.assembly) == "outrigger"], (
        "the Swinburne pack is retired on this house — it lives on conftest.swinburne_model")


# --- the blocks are on the stud module -----------------------------------------------


def test_block_one_lands_on_the_stud_it_is_screwed_to(catlin_model):
    """The premise of the whole detail: block-1's 5" screw goes into a STUD.

    The block is 3-1/2" wide on a 1-1/2" stud and centred on the stud station, so it laps the
    stud completely. Measured as a real overlap against the resolved studlike members rather
    than against an assumed module, because the module is what the frame *claims* and the
    studs are what is there.

    Three exclusions, none of them a tolerance.

    **A block on a CONTINUOUS HORIZONTAL member** — a sole or top plate, a header over a
    door, the rough sill under a window — is on wood, and on better wood than a stud: the
    piece runs the width of the wall, so the screw lands in it wherever the module puts the
    block. The lowest girt course on a wall with a raised door sill is that case, and so is
    every head course sitting in the depth of its own header.

    **A block with no vertical member within 4"** and no horizontal one either is in a head
    gap too shallow to frame cripples in. Rare, and not a stud.

    **The last 6" of a band**, where a course's end block lands on a corner post whose other
    studs belong to the wall next door and are not in this member list.

    What is left is measured against the studs that are actually there, never against an
    assumed module — the module is what the frame *claims*, and ``GirtFrame.snap`` exists
    precisely because near an opening the two part company. A block may lap as little as half
    a stud (the floor below), and 99% of them lap the whole of it.
    """
    laps: list[float] = []
    thin: list[tuple[str, float, float]] = []
    for wall in _girt_walls(catlin_model):
        studs = [(_station(m, wall), m.z0_m, m.z1_m) for m in wall.members
                 if m.category in _STUDLIKE]
        if len(studs) < 4:
            continue
        run = max(station for station, _z0, _z1 in studs)
        spanning = [(min(_station(m, wall), _station(m, wall, 1)),
                     max(_station(m, wall), _station(m, wall, 1)), m.z0_m, m.z1_m)
                    for m in wall.members
                    if m.category in _HORIZONTAL and m.p0 != m.p1]
        for block in wall.members:
            if block.category != "truss_block" or _tier(block) != "1":
                continue
            centre = _station(block, wall)
            if centre < 6.0 * IN or centre > run - 6.0 * IN:
                continue
            if any(lo - 1e-9 <= centre <= hi + 1e-9
                   and z0 < block.z1_m - 1e-9 and block.z0_m < z1 - 1e-9
                   for lo, hi, z0, z1 in spanning):
                continue
            # At the block's OWN elevation, which is the whole care in it: a wall's lowest
            # girt course runs opposite the floor band, 13" below the sole plate on this
            # house, where the nearest thing the solver calls a stud is a cripple that starts
            # a foot higher. Measuring against it reports a half-inch lap on wood that is not
            # at that height at all.
            at_height = [station for station, z0, z1 in studs
                         if z0 < block.z1_m - 1e-9 and block.z0_m < z1 - 1e-9]
            if not at_height:
                continue
            nearest = min(at_height, key=lambda s, c=centre: abs(s - c))
            if abs(nearest - centre) > 4.0 * IN:
                continue
            overlap = (min(centre + 1.75 * IN, nearest + 0.75 * IN)
                       - max(centre - 1.75 * IN, nearest - 0.75 * IN))
            laps.append(overlap)
            if overlap < 0.75 * IN - 1e-6:
                thin.append((wall.tag, round(centre / IN, 2), round(overlap / IN, 3)))
    assert len(laps) > 700, "the field of the wall is what this measures"
    assert not thin, (
        f"block-1s lapping under half a stud: {thin[:6]} — the block grid has drifted off "
        "the 16 in stud module")
    # And nearly all of them cover the stud WHOLE. The handful that do not are the end block
    # of a short raked stub at an attic gable: it cannot move onto the corner post beside it
    # without standing half its width out past the girt it carries (``GirtFrame.snap``'s
    # ``bounds``), so it takes half the post and that is the right trade. If this ratio ever
    # falls, the grid has drifted rather than a few gable stubs having been crowded.
    full = sum(1 for lap in laps if lap >= 1.5 * IN - 1e-6)
    assert full / len(laps) >= 0.99, (
        f"only {full}/{len(laps)} block-1s lap their whole stud")


def test_block_two_is_mid_bay_not_stacked_over_block_one(catlin_model):
    """8" off the block-1 line, and that offset is the fastening design, not a convenience.

    Stacking the two tiers would put block-2's screw into block-1's. Offset, each tier's 5"
    SDWS is a plain wood-to-wood connection with continuous lateral support — girt → block →
    sheathing → stud for one, girt → block → inner girt for the other — and nothing bears on
    foam, which is what takes this wall out of IRC Table R703.15.1 and into R301.1.3
    (`notes/catlin_truss_engineering.md` §6).

    Measured against the wall's own MODULE STUDS rather than against an absolute phase or
    against either tier's own mode. ``stud`` is the category the solver mints only for a
    module stud — a king, a jack, a cripple and a corner post are all their own categories —
    so the mode of their stations mod 16 IS the wall's module, read off the thing the block
    is supposed to be screwed into.

    Field blocks only. The pair under a JAMB POST is deliberately at the same station in both
    tiers (there is one post per band and they are in line), and a rule that forbade every
    coincidence would forbid that too.
    """
    checked = 0
    for wall in _girt_walls(catlin_model):
        module = [_station(m, wall) / IN for m in wall.members if m.category == "stud"]
        if len(module) < 4:
            continue
        phase = _modal_phase(module)
        field = {"1": [], "2": []}
        field_z: dict[str, list[tuple[float, float]]] = {"1": [], "2": []}
        for member in wall.members:
            tier = _tier(member)
            if member.category != "truss_block" or tier is None:
                continue
            if not _FIELD_BLOCK.match(member.child_key):
                continue
            station = round(_station(member, wall) / IN, 4)
            field[tier].append(station)
            field_z[tier].append((station, member.z0_m))
        if len(field["1"]) < 3 or len(field["2"]) < 3:
            continue
        on_one = [s for s in field["1"] if abs((s - phase) % 16.0) < 0.02
                  or abs((s - phase) % 16.0 - 16.0) < 0.02]
        on_two = [s for s in field["2"] if abs((s - phase - 8.0) % 16.0) < 0.02
                  or abs((s - phase - 8.0) % 16.0 - 16.0) < 0.02]
        assert len(on_one) >= 0.6 * len(field["1"]), (
            f"{wall.tag}: only {len(on_one)}/{len(field['1'])} block-1s on the stud module")
        assert len(on_two) >= 0.6 * len(field["2"]), (
            f"{wall.tag}: only {len(on_two)}/{len(field['2'])} block-2s on the half-bay")
        # And never pulled BACK onto the stud line. Both tiers carry the same courses cut
        # into the same segments, so their off-module end blocks — at a mitred band edge, at
        # the raked top of an attic gable, snapped onto the same gable stud — land at one
        # station by construction, and on site that pair is driven with an inch of vertical
        # stagger inside the block's 3-1/2" height (a construction note,
        # notes/outie_window_truss_detail.md). What must never happen is a block-2 sharing a
        # station ON THE STUD MODULE with a block-1 at the same elevation: that is the
        # offset scheme collapsing, and it is exactly what an unbounded ``GirtFrame.snap``
        # did before its reach was cut from half a bay to one board.
        on_module = [(s, z) for s, z in field_z["2"]
                     if abs((s - phase) % 16.0) < 0.02
                     or abs((s - phase) % 16.0 - 16.0) < 0.02]
        stacked = [s for s, z in on_module
                   if any(abs(s - t) < 0.02 and abs(z - w) < 1e-9 for t, w in field_z["1"])]
        assert not stacked, (
            f"{wall.tag}: block-2 sitting on the stud module over a block-1 at "
            f"{sorted(set(stacked))[:6]} — the two tiers are meant to be half a bay apart")
        checked += 1
    assert checked >= 20, "vacuity guard"


# --- a course is carried, end to end --------------------------------------------------


def test_every_course_segment_is_carried(catlin_model):
    """No girt is a cantilever, and no bay is longer than the stud module plus a board.

    Three claims in one walk, per band.

    **Nothing runs unsupported for more than a module.** A block lands on every stud station
    a course crosses, so the run from either end of a segment to the block nearest it, and
    every bay between blocks, is bounded. The bound is the 16" stud spacing, plus (for a bay
    only) one 3-1/2" board: a course's off-module END block is the one piece that can sit
    past the last module station, and on a raked attic gable that puts 18-1/4" between the
    last two.

    **A segment with NO block of its own is legal only where BOTH of its ends are carried by
    something other than a block of its own** — a jamb post it butts, or the band's own
    mitred edge, where a collinear neighbour's course runs through and the seam block belongs
    to the ``"owner"`` side. That is the short piece of girt between a window and a facade
    tee, or between two windows 3-1/2" apart, fitted between two posts each of which is
    blocked at this very elevation and screwed to the jack and king behind it. Fifteen of
    catlin's course segments are that piece. Any other blockless segment is a stick of wood
    held on by air, which is the Swinburne pack's 2026-08-23 defect arriving from the other
    direction.
    """
    unsupported: list[tuple[str, str, float]] = []
    long_bays: list[tuple[str, str, float]] = []
    orphans: list[tuple[str, str, float]] = []
    measured = 0
    for wall in _girt_walls(catlin_model):
        inner_name, outer_name = _bands(catlin_model, wall)
        butts = set()
        for opening in _openings(catlin_model, wall):
            half = opening.width_m / 2.0
            butts.add(round(opening.center_along_m - half - _STOCK_FACE, 6))
            butts.add(round(opening.center_along_m + half + _STOCK_FACE, 6))
        for band, tier in ((inner_name, "1"), (outer_name, "2")):
            blocks = [(m.z0_m, _station(m, wall)) for m in wall.members
                      if m.category == "truss_block" and _tier(m) == tier]
            if not blocks:
                continue
            segments = _courses(wall, band)
            edges = {round(min(seg[1] for seg in segments), 6),
                     round(max(seg[2] for seg in segments), 6)}
            for z0, lo, hi, member in segments:
                measured += 1
                on_it = sorted(station for z, station in blocks
                               if abs(z - z0) < 1e-9
                               and lo - 1.9 * IN <= station <= hi + 1.9 * IN)
                if not on_it:
                    carried = butts | edges
                    if not (round(lo, 6) in carried and round(hi, 6) in carried):
                        orphans.append((wall.tag, member.child_key, (hi - lo) / IN))
                    continue
                if on_it[0] - lo > _STUD_SPACING + 1e-6:
                    unsupported.append((wall.tag, member.child_key,
                                        (on_it[0] - lo) / IN))
                if hi - on_it[-1] > _STUD_SPACING + 1e-6:
                    unsupported.append((wall.tag, member.child_key,
                                        (hi - on_it[-1]) / IN))
                for a, b in zip(on_it, on_it[1:], strict=False):
                    if b - a > _STUD_SPACING + _STOCK_FACE + 1e-6:
                        long_bays.append((wall.tag, member.child_key, (b - a) / IN))
    assert measured > 500, "vacuity guard: the house's girt courses"
    assert not orphans, (
        f"girt course segments with no block and no post to bear on: {orphans[:6]}")
    assert not unsupported, f"girt course ends running past a module: {unsupported[:6]}"
    assert not long_bays, f"block bays past a module plus a board: {long_bays[:6]}"


# --- the two tiers are one course -----------------------------------------------------


def test_the_two_girt_bands_are_one_course(catlin_model):
    """Same elevations, same segments. Block-2 screws into the inner girt; a half-inch
    disagreement between the tiers is a 5" screw into a 1/2" air gap.

    Asserted on the resolved members rather than on the spec, because both bands carry the
    same authored `FramingSpec` and the interesting failure is a *resolver* one — a band
    mitred differently at a corner, a course cut differently around an opening.
    """
    for wall in _girt_walls(catlin_model):
        inner_name, outer_name = _bands(catlin_model, wall)
        inner = _courses(wall, inner_name)
        outer = _courses(wall, outer_name)
        assert len(inner) == len(outer), (
            f"{wall.tag}: {len(inner)} inner course segments against {len(outer)} outer")
        for (za, loa, hia, _a), (zb, lob, hib, _b) in zip(inner, outer, strict=True):
            assert za == pytest.approx(zb, abs=1e-9), wall.tag
            assert loa == pytest.approx(lob, abs=1e-9), wall.tag
            assert hia == pytest.approx(hib, abs=1e-9), wall.tag


def test_course_elevations_are_the_authored_module_and_the_frame_agrees(catlin_model):
    """One list, computed once — `furring.course_elevations` — and both passes read it.

    The girt courses are framed by `frame_furring` and blocked by `frame_truss_walls`, two
    passes that run minutes apart in the pipeline. A block half an inch below the girt it
    carries is not a tolerance, it is a block bearing on nothing, so the two readings cannot
    be allowed to be two readings.
    """
    checked = 0
    for wall in _girt_walls(catlin_model):
        inner_band, outer_band = truss_girt_bands(catlin_model.plan, wall.assembly)
        expected = course_elevations(wall, outer_band.framing, _STOCK_FACE)
        framed = sorted({round(z, 9) for z, _lo, _hi, _m in _courses(wall, outer_band.name)})
        assert framed, wall.tag
        for z in framed:
            assert any(abs(z - e) < 1e-9 for e in expected), (
                f"{wall.tag}: a course at {(z - wall.z0_m) / IN:.2f}\" above the base is not "
                "one of the elevations course_elevations names")
        # And on a wall with no opening in it, the framed set is the WHOLE expected set:
        # nothing has been dropped for a reason the elevation list does not know about.
        # (A wall WITH an opening legitimately loses the courses the opening's own frame
        # replaces — W-M-N3 is a 4'-0" wall almost entirely filled by D-M-ENTRY, and its
        # girts run below the sill and above the head and nowhere between.)
        if not _openings(catlin_model, wall):
            assert len(framed) == len(expected), (
                f"{wall.tag}: {len(framed)} courses framed of {len(expected)} elevations, "
                "on a wall with no opening to explain the difference")
        _ = inner_band
        checked += 1
    assert checked >= 30


# --- a course runs through a facade seam ----------------------------------------------


def test_courses_abut_at_a_facade_seam_with_one_block_in_the_joint(catlin_model):
    """A girt is ONE stick; the tee is an artifact of where the partitions land inside.

    Two collinear segments of a facade each used to hold their courses half a board back from
    the shared node, leaving a 3" notch in every course at every tee. `continuation_roles`
    (extended to horizontal bands on 2026-08-26 by adding `direction` to
    `_furring_module_signature`) now lets the module run through: the courses meet at the
    seam, and the block there belongs to the ``"owner"`` side alone so the joint carries one
    block rather than two stacked in the same 1-1/2".
    """
    from typehaus.resolve.framing.corners import corner_junctions

    seams = [j for j in catlin_model.junctions if j.kind in ("collinear", "t")]
    assert seams, "catlin's facades are authored as chains of segments"
    by_tag = {w.tag: w for w in catlin_model.walls}
    girt_tags = {w.tag for w in _girt_walls(catlin_model)}
    checked = 0
    for junction in seams:
        through = [item for item in junction.incidents
                   if item.wall_tag in junction.through_walls
                   and item.wall_tag in girt_tags]
        if len(through) != 2:
            continue
        walls = [by_tag[item.wall_tag] for item in through]
        if walls[0].storey != walls[1].storey:
            continue
        _inner, outer = _bands(catlin_model, walls[0])
        # The two courses that meet here: for each wall, the course-segment end nearest the
        # shared node, per elevation. They abut when the two ends land on the same point.
        node = junction.point
        ends = []
        for wall in walls:
            direction = unit(sub(wall.axis[1], wall.axis[0]))
            offset = sub(node, wall.axis[0])
            seam = offset[0] * direction[0] + offset[1] * direction[1]
            near = [min(abs(lo - seam), abs(hi - seam))
                    for _z, lo, hi, _m in _courses(wall, outer)]
            if near:
                ends.append(min(near))
        if len(ends) == 2:
            # Each wall's nearest course end is AT the seam, not half a board short of it.
            assert max(ends) < 0.02 * IN, (
                f"{junction.node_tag}: a girt course stops "
                f"{max(ends) / IN:.3f} in short of a seam it should run through")
            checked += 1
    assert checked >= 5, "vacuity guard: catlin's facade seams between girt walls"
    _ = corner_junctions


# --- the rough opening's own frame -----------------------------------------------------


def test_every_rough_opening_has_a_jamb_post_in_both_bands(catlin_model):
    """Inner face ON the RO edge, in each band, so the flange bears and the reveal is wood."""
    bearing = FLANGE_BEARING.meters
    for wall in _girt_walls(catlin_model):
        inner_name, outer_name = _bands(catlin_model, wall)
        for index, opening in enumerate(_openings(catlin_model, wall)):
            half = opening.width_m / 2.0
            jambs = (opening.center_along_m - half, opening.center_along_m + half)
            for band in (inner_name, outer_name):
                for side, jamb in enumerate(jambs):
                    key = f"strapping-jamb-{band}-{index:03d}-{side}"
                    post = next((m for m in wall.members if m.child_key == key), None)
                    assert post is not None, f"{wall.tag}: no {key}"
                    inward = 1.0 if side == 0 else -1.0
                    face = _station(post, wall) + inward * _STOCK_FACE / 2.0
                    assert abs(face - jamb) <= bearing + 1e-9, (
                        f"{wall.tag} {key}: post face {abs(face - jamb) / IN:.2f}\" from the "
                        "RO edge")


def test_head_and_sill_courses_span_the_rough_opening(catlin_model):
    """Post inner face to post inner face — the RO's own width, in both bands."""
    checked = 0
    for wall in _girt_walls(catlin_model):
        inner_name, outer_name = _bands(catlin_model, wall)
        for index, opening in enumerate(_openings(catlin_model, wall)):
            z_sill = wall.base_ref_z_m + opening.sill_m
            z_head = z_sill + opening.height_m
            for band in (inner_name, outer_name):
                for name, z0 in (("head", z_head), ("sill", z_sill - _STOCK_FACE)):
                    key = f"ladder-{name}-{band}-{index:03d}"
                    piece = next((m for m in wall.members if m.child_key == key), None)
                    assert piece is not None, f"{wall.tag}: no {key}"
                    assert piece.z0_m == pytest.approx(z0, abs=1e-9), key
                    assert piece.z1_m - piece.z0_m == pytest.approx(_STOCK_FACE, abs=1e-9)
                    assert piece.length_m == pytest.approx(opening.width_m, abs=1e-9), (
                        f"{wall.tag} {key}: spans {piece.length_m / IN:.1f}\" of a "
                        f"{opening.width_m / IN:.1f}\" RO")
                    checked += 1
    assert checked >= 4 * 30


def test_the_opening_support_check_passes_on_every_girt_wall(catlin_model, catlin_plan):
    """The frame places the posts; the check re-derives whether a flange lands on them.

    Two different readings of the same wall, on purpose — `truss_girts.py` from the band
    centreline it built on, `checks/structural/truss_wall.py` from the resolved members — so
    a frame that ever declines to add a post is caught rather than assumed away.
    """
    from _helpers import check_context

    from typehaus.checks.structural.truss_wall import truss_wall_opening_support

    findings = truss_wall_opening_support(
        check_context(catlin_plan, catlin_model, profile=None))
    fails = [f for f in findings if f.result.value == "fail"]
    assert not fails, [f.message for f in fails]
    passes = [f for f in findings if f.result.value == "pass"]
    assert passes, "the check must actually reach the openings, not skip every wall"


def test_the_buck_lines_the_rough_opening_out_to_the_mount_plane(catlin_model):
    """4 sides per opening, 3/8" plywood, sheathing face to the mount plane — 6" now, not 5".

    The profile string is derived from the stack (`BandFrame.buck`), so this is the assertion
    that catches the mount plane moving without the buck following it.
    """
    for wall in _girt_walls(catlin_model):
        openings = _openings(catlin_model, wall)
        bucks = [m for m in wall.members if m.category == "buck"]
        assert len(bucks) == 4 * len(openings), wall.tag
        assert all(m.profile == "6x0.375 panel" for m in bucks), wall.tag


def test_no_girt_member_stands_inside_a_rough_opening(catlin_model):
    """Nothing in this frame may reach into the glass — not a course, not a block, not a post.

    The field courses are held one piece width clear of every RO
    (`furring.OPENING_MARGIN_IN`); the jamb posts sit outboard of the edge; the head and sill
    courses sit above and below. This is the assertion that the three rules together leave
    the opening empty, measured in 3D — plan footprint AND elevation band — because a course
    above a head laps the RO in plan and is perfectly correct there.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint
    from typehaus.resolve.framing.truss_wall import TRUSS_CATEGORIES

    categories = set(TRUSS_CATEGORIES) | {"strapping"}
    intrusions: list[tuple[str, str, float]] = []
    for wall in _girt_walls(catlin_model):
        direction = unit(sub(wall.axis[1], wall.axis[0]))
        for opening in _openings(catlin_model, wall):
            half = opening.width_m / 2.0
            lo, hi = opening.center_along_m - half, opening.center_along_m + half
            z0 = wall.base_ref_z_m + opening.sill_m
            z1 = z0 + opening.height_m
            for member in wall.members:
                if member.category not in categories or member.category == "buck":
                    continue
                if member.z1_m <= z0 + 1e-9 or member.z0_m >= z1 - 1e-9:
                    continue
                ring, _mz0, _mz1 = member_footprint(member)
                stations = [(x - wall.axis[0][0]) * direction[0]
                            + (y - wall.axis[0][1]) * direction[1] for x, y in ring]
                overlap = min(max(stations), hi) - max(min(stations), lo)
                if overlap > 1e-6:
                    intrusions.append((wall.tag, member.child_key, overlap / IN))
                _ = Polygon
    assert not intrusions, f"girt members standing in the glass: {intrusions[:8]}"


# --- one datum -------------------------------------------------------------------------


def test_the_frame_reads_the_band_the_same_way_the_members_were_placed(catlin_model):
    """One datum. A rebuilt `GirtFrame` puts a member back where the pass put it."""
    wall = next(w for w in _girt_walls(catlin_model) if len(w.members) > 60)
    frame = _frame(catlin_model, wall)
    _inner, outer_name = _bands(catlin_model, wall)
    course = next(m for m in wall.members
                  if m.child_key.startswith(f"strapping-{outer_name}-"))
    assert frame.station_of(course) == pytest.approx(_station(course, wall), abs=1e-6)
    # And the derived depths: the buck runs from the sheathing face to the outer girt's
    # outboard face, which is 6" on this stack.
    assert frame.buck_depth / IN == pytest.approx(6.0, abs=1e-6)
    assert (frame.band_mid - frame.inner_mid) / IN == pytest.approx(3.0, abs=1e-6)
