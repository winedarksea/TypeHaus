"""The Swinburne truss wall's geometry, asserted at the numbers the note claims.

`resolve/framing/truss_frame.py` places five kinds of piece off two numbers each — a station
along the band and a depth across it — and until 2026-08-23 nothing tested any of them. Three
defects lived in that gap and every one of them was a *quantity* bug an estimator would have
paid for and a *build* bug a framer would have found on site:

* the on-edge outrigger grid started half a stick off the stud grid, so 806 of 1,285 blocks
  half-lapped their stud and 74 landed on bare sheathing;
* 72 of 447 outriggers took no block and no tab at all — including 20 of the 21 jamb
  outriggers, the members the whole outie window hangs its flange on;
* head and sill blocking was trimmed to one 15-1/2" stub at every opening in the house,
  whatever the opening's width, because it gave way to every tab on the wall rather than to
  the ones at its own elevation.

None of the three is visible in a take-off total or a rendered elevation. They are visible
here.
"""

from __future__ import annotations

import pytest

from typehaus.resolve.framing.truss_frame import BLOCK_SPACING, TrussFrame
from typehaus.resolve.framing.truss_wall import truss_layer_name
from typehaus.resolve.geometry import sub, unit
from typehaus.resolve.layout_lines import layout_phase

IN = 0.0254


def _truss_walls(model):
    return [w for w in model.walls
            if truss_layer_name(model.plan, w.assembly) is not None]


def _station(member, wall):
    direction = unit(sub(wall.axis[1], wall.axis[0]))
    offset = sub(member.p0, wall.axis[0])
    return offset[0] * direction[0] + offset[1] * direction[1]


def _by_category(wall, category):
    return [m for m in wall.members if m.category == category]


def _module_phase(model, wall, spacing_m):
    """Wall-local station of this wall's first module station, in ``[0, spacing)``.

    0.0 for a wall whose framing lays out from its own start node, which is the default and
    was the only case until 2026-08-25. Catlin's exterior assemblies now set
    ``FramingSpec.layout_origin="line"``, so the module is the *layout line's* and a wall
    whose start node is off 16" carries a nonzero phase — its studs and its outriggers are
    still one grid, which is what these tests are about, but that grid is no longer a whole
    multiple of 16" from the wall's own end.
    """
    layer = truss_layer_name(model.plan, wall.assembly)
    assembly = model.plan.library.resolve_assembly(wall.assembly)
    spec = next((ly.framing for ly in assembly.layers
                 if ly.name == layer and ly.framing is not None), None)
    line = next((ln for ln in model.layout_lines if ln.member(wall.tag) is not None), None)
    return layout_phase(spec, line, wall.tag, spacing_m)


#: Everything the framing solver emits as a vertical stick on (or beside) the stud module.
#: A block screwed "over a stud" may equally land on the king or jack at an opening — they
#: are the same 1-1/2" of wood in the same plane — and testing only ``stud`` reports every
#: block at an RO edge as landing on nothing.
_STUDLIKE = ("stud", "king", "jack", "cripple", "corner", "trimmer")


def _studlike(wall):
    return [m for m in wall.members if m.category in _STUDLIKE]


def _opening_spans(model, wall):
    """``(station_lo, station_hi)`` of every rough opening hosted in ``wall``."""
    return [(o.center_along_m - o.width_m / 2.0, o.center_along_m + o.width_m / 2.0)
            for o in model.openings if o.host_wall == wall.tag]


def test_the_house_has_truss_walls_at_all(catlin_model):
    """Guard the rest of the module: every assertion below is vacuous without these."""
    walls = _truss_walls(catlin_model)
    assert len(walls) >= 30, "catlin's main/second/attic exterior walls are all truss walls"


def test_an_outrigger_lands_on_the_stud_line_it_is_screwed_to(catlin_model):
    """The premise of the whole detail, and the one the block geometry is derived from.

    An outrigger is not fastened to the sheathing — it is fastened, through a plywood tab and
    a flat block, to a STUD. So its grid has to be the stud grid. Only the strip at each end
    of a band is off-module, exactly as the end studs are.

    The module is taken from ``_module_phase``, not assumed to start at the wall's own end:
    since 2026-08-25 catlin's exterior walls phase from their layout line, and this test's
    claim is that the two grids AGREE — never that either one starts at a particular node.
    """
    off_module = []
    for wall in _truss_walls(catlin_model):
        phase = _module_phase(catlin_model, wall, 16.0 * IN) / IN
        for member in _by_category(wall, "strapping"):
            if member.material != "kdat" or "jamb" in member.child_key:
                continue
            # Measured against the 16" MODULE, not against whichever studs survived this
            # wall's openings: the grid is the invariant, and a stud missing under a window
            # is the opening's business, not the outrigger's.
            station = _station(member, wall) / IN - phase
            if abs(station - round(station / 16.0) * 16.0) > 0.01:
                off_module.append((wall.tag, round(station, 3)))
    # Two per wall at most: the end strip at each end of the mitred band.
    per_wall: dict[str, int] = {}
    for tag, _station_in in off_module:
        per_wall[tag] = per_wall.get(tag, 0) + 1
    assert all(count <= 2 for count in per_wall.values()), (
        f"only a band's two END strips may sit off the stud module: {per_wall}")


def test_a_block_covers_the_whole_stud_it_is_screwed_to(catlin_model):
    """Two screws per block, both over the stud — which needs the stud's full 1-1/2".

    The block is 3-1/2" wide on a 1-1/2" outrigger and slid so one side face is flush with
    the outrigger's. With the outrigger on the stud line that face is the stud's face too, so
    the block laps the stud completely — and if the grid ever drifts off the module again,
    this is the half inch that goes missing.

    Three exclusions, and none of them is a tolerance:

    * **Blocks with no stud at all.** Over a header or a rough sill (the framing above a door
      head and under a window spans the whole opening), and above an opening whose header
      runs to the top plate, where there are no cripples — a head gap shallower than a
      plate is not framed. That is wood, just not a stud.
    * **Blocks standing inside a rough opening**, which is the same idea stated by station
      rather than by elevation: an outrigger crossing an opening is blocked at the header,
      the rough sill and the plates, all of which run the width of the wall.
    * **The last 6" of each band.** A band's end strip is off-module by construction, like
      the end stud; its pack is slid to stay inside the mitred band, and it lands on a corner
      post whose other studs belong to the WALL NEXT DOOR and are not in this member list.

    What is left is the field, and the field has a floor: a pack may slide up to an inch to
    clear the one beside it (``TrussFrame._slide_clear``), so the lap can narrow to 3/4" but
    never past it.
    """
    laps: list[float] = []
    thin: list[tuple[str, float, float]] = []
    for wall in _truss_walls(catlin_model):
        studs = [_station(m, wall) for m in _studlike(wall)]
        if len(studs) < 4:
            continue
        run = max(studs)
        openings = _opening_spans(catlin_model, wall)
        for block in _by_category(wall, "truss_block"):
            centre = _station(block, wall)
            if centre < 6.0 * IN or centre > run - 6.0 * IN:
                continue
            # A block standing INSIDE a rough opening has no stud under it and wants none:
            # the outrigger crossing an opening is blocked at the header, the rough sill and
            # the plates, which is wood that runs the width of the wall. W-M-N3 is the case
            # to picture — a 4'-0" wall almost entirely filled by D-M-ENTRY. Before
            # 2026-08-25 the 4"-window skip below happened to exclude these; on the line's
            # grid they land nearer a jack and it no longer does, so state the rule outright
            # rather than leaving it to a coincidence of spacing.
            if any(lo - 1e-9 <= centre <= hi + 1e-9 for lo, hi in openings):
                continue
            nearest = min(studs, key=lambda s, c=centre: abs(s - c))
            if abs(nearest - centre) > 4.0 * IN:
                continue
            overlap = (min(centre + 1.75 * IN, nearest + 0.75 * IN)
                       - max(centre - 1.75 * IN, nearest - 0.75 * IN))
            laps.append(overlap)
            if overlap < 0.75 * IN - 1e-6:
                thin.append((wall.tag, round(centre / IN, 2), round(overlap / IN, 3)))
    # 717 today. The floor is a vacuity guard, not a quantity, and it has come down twice for
    # reasons that are both improvements: 800 -> 750 when blocks inside a rough opening
    # started being excluded by the rule above rather than by a coincidence of spacing, and
    # 750 -> 700 on 2026-08-25 when the doubled outrigger at every wall seam went away
    # (``solver.continuation_roles``) and took its blocks with it. Fewer blocks measured,
    # none of them thin — which is the thing this actually asserts.
    assert len(laps) > 700, "the field of the wall is what this measures"
    assert not thin, f"blocks lapping under 3/4\" of stud: {thin[:6]}"
    full = sum(1 for lap in laps if lap >= 1.5 * IN - 1e-6)
    assert full / len(laps) >= 0.85, (
        f"only {full}/{len(laps)} field blocks lap their whole stud — the outrigger grid "
        "has drifted off the 16\" module again")


def test_every_outrigger_is_actually_fastened_to_the_wall(catlin_model):
    """A block and a tab, or the model is drawing a stick of wood held on by air.

    A handful may legitimately share the pack beside them where two verticals stand within a
    pack's width of each other — a band end, a jamb outrigger — and those are REPORTED
    (``structural.truss_wall_unpacked_outrigger``). More than a handful is this pass broken.
    """
    total = unpacked = 0
    for wall in _truss_walls(catlin_model):
        outriggers = [m for m in _by_category(wall, "strapping") if m.material == "kdat"]
        packs = {m.child_key.split("-")[2] for m in _by_category(wall, "truss_tab")}
        total += len(outriggers)
        unpacked += max(0, len(outriggers) - len(packs))
    assert total > 300
    assert unpacked <= 10, f"{unpacked} of {total} outriggers took no block or tab"


def test_head_and_sill_blocking_spans_its_opening(catlin_model):
    """The window's flange bears on this. A 60" door needs about 63", not 15-1/2"."""
    widest = {}
    for wall in _truss_walls(catlin_model):
        openings = [op for op in catlin_model.openings if op.host_wall == wall.tag]
        for opening in openings:
            pieces = [m for m in _by_category(wall, "truss_blocking")
                      if abs(m.z0_m - (wall.z0_m + opening.sill_m + opening.height_m)) < 1e-6]
            if pieces:
                widest[opening.tag] = sum(m.length_m for m in pieces) / IN
    assert widest, "every opening in a truss wall takes head blocking"
    for tag, span in widest.items():
        opening = next(op for op in catlin_model.openings if op.tag == tag)
        assert span >= opening.width_m / IN - 4.0, (
            f"{tag}: head blocking spans {span:.1f}\" of a {opening.width_m / IN:.0f}\" RO")


def test_blocks_climb_an_outrigger_at_no_more_than_the_stated_spacing(catlin_model):
    """`takeoff/fasteners.py` prints this spacing as the screw count's basis.

    A gap may be LONGER than the spacing where a block was dropped for landing inside a
    rough opening in plan — that block would be in the glass — so the test is on the shape of
    the distribution rather than on every gap: the typical climb is at or under the stated
    spacing, and no gap swallows more blocks than the openings it passes can explain.

    The per-wall ceiling is the arithmetic of that sentence rather than a flat multiple of
    the spacing. A pack running past an RO loses every block the RO covers PLUS the two that
    straddle its sill and its head, so the widest defensible gap on a wall is that wall's
    tallest RO plus two climbs. On a wall with no opening it collapses to the old 3x bound,
    which is the same statement with a zero-height opening.

    That distinction started to matter on 2026-08-24: widening the attic juliet pair
    18" -> 24" moved the RO over the bay beside the outrigger at x 15'-4", so a pack on
    W-A-S2/W-A-S3 now gives up three blocks to a 64"-tall opening (a 125" gap) where the
    flat 120" bound allowed only two.
    """
    gaps: list[float] = []
    for wall in _truss_walls(catlin_model):
        tallest = max((op.height_m for op in catlin_model.openings
                       if op.host_wall == wall.tag), default=0.0)
        ceiling = max(3.0, tallest / BLOCK_SPACING.meters + 2.0) * BLOCK_SPACING.meters
        by_pack: dict[str, list[float]] = {}
        for block in _by_category(wall, "truss_block"):
            by_pack.setdefault(block.child_key.split("-")[2], []).append(block.z0_m)
        for elevations in by_pack.values():
            elevations.sort()
            for lower, upper in zip(elevations, elevations[1:], strict=False):
                gaps.append(upper - lower)
                assert upper - lower <= ceiling + 1e-6, (
                    f"{wall.tag}: a block gap of {(upper - lower) / IN:.1f}\" runs past what "
                    f"its tallest RO ({tallest / IN:.0f}\") plus two climbs can explain "
                    f"({ceiling / IN:.1f}\")")
    assert gaps
    gaps.sort()
    assert gaps[len(gaps) // 2] <= BLOCK_SPACING.meters + 1e-6, (
        f"typical block climb is {gaps[len(gaps) // 2] / IN:.1f}\", past the stated "
        f"{BLOCK_SPACING.inches:g}\"")


def test_the_buck_lines_the_rough_opening_out_to_the_truss_plane(catlin_model):
    """4 sides per opening, 3/8" plywood, sheathing face to the truss plane."""
    for wall in _truss_walls(catlin_model):
        openings = [op for op in catlin_model.openings if op.host_wall == wall.tag]
        bucks = _by_category(wall, "buck")
        assert len(bucks) == 4 * len(openings), wall.tag
        assert all(m.profile == "5x0.375 panel" for m in bucks), wall.tag


def test_every_owned_truss_wall_l_corner_carries_a_clear_plywood_corner_cap(catlin_model):
    """The Larsen/Swinburne corner box: two 1/2" rips per owned L corner between two truss
    walls, standing clear of the end outriggers on both sides of it.

    The box exists to close the void OUTSIDE the band the mitre leaves the end outriggers
    in (``TrussFrame.corner_box`` deliberately sits outside ``[first, last]``) — the whole
    point is a piece that reaches somewhere nothing else does, never one that overlaps the
    wood already there.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint

    truss_tags = {wall.tag for wall in _truss_walls(catlin_model)}
    corners = [j for j in catlin_model.junctions
              if j.kind == "l" and j.framing_owner
              and all(item.wall_tag in truss_tags for item in j.incidents)]
    assert corners, "catlin's exterior L corners are all truss-wall corners"
    by_tag = {w.tag: w for w in catlin_model.walls}
    by_uid = {w.uid: w for w in catlin_model.walls}
    checked = 0
    for junction in corners:
        owner = by_tag[junction.framing_owner]
        caps = _by_category(owner, "truss_corner_cap")
        assert len(caps) == 2, f"{owner.tag}: expected 2 corner-cap rips, found {len(caps)}"
        for cap in caps:
            cap_ring, cap_lo, cap_hi = member_footprint(cap)
            cap_poly = Polygon(cap_ring)
            host = by_uid.get(cap.parent_uid)
            assert host is not None, f"{cap.child_key}: no wall owns parent_uid {cap.parent_uid}"
            outriggers = [m for m in host.members
                         if m.category == "strapping" and m.material == "kdat"]
            for outrigger in outriggers:
                if outrigger.z1_m <= cap_lo or outrigger.z0_m >= cap_hi:
                    continue
                other_ring, _, _ = member_footprint(outrigger)
                overlap = cap_poly.intersection(Polygon(other_ring)).area
                assert overlap < 1e-6, (
                    f"{cap.child_key} on {host.tag} overlaps outrigger "
                    f"{outrigger.child_key} by {overlap:.6f} m^2")
            checked += 1
    assert checked == 2 * len(corners)


def test_the_frame_reads_the_band_the_same_way_the_check_does(catlin_model):
    """One datum. The check re-derives stations off the band centreline; so does the frame."""
    wall = next(w for w in _truss_walls(catlin_model) if len(w.members) > 40)
    layer_name = truss_layer_name(catlin_model.plan, wall.assembly)
    band = next(layer for layer in wall.layers
                if layer.name == layer_name and layer.polygon)
    frame = TrussFrame.build(catlin_model.plan, wall, band)
    assert frame is not None
    outrigger = next(m for m in _by_category(wall, "strapping") if m.material == "kdat")
    assert frame.station_of(outrigger) == pytest.approx(_station(outrigger, wall), abs=1e-6)
