"""The plan stair symbol: the cut, the break, the occlusion, the travel line, the ledger.

``test_stair_framing.py`` owns what the RESOLVER builds and is already large. This module
owns what the DRAWING says about it — which surfaces reach the sheet at all, and whether a
reader can count the risers.

The four reported symptoms, and the one fact behind them: both flights of a U-stair were
drawn in full, superimposed, in the same well. "Treads should be the same width but don't
seem to be" (41.06" lanes over 42.375" lanes, offset 1.3"); "an extra one on the right"
(ST-M2S's east lane has one riser more than ST-B2M's); "the landing weirdly has two stairs
to the north side of it" (two landing pairs, offset 10"). See
``houses/catlin/notes/u_stair_split_landing.md`` and ``emit/draw/stair_symbol.py``.
"""

from __future__ import annotations

import math

import pytest
from shapely.geometry import LineString, Polygon

from typehaus.emit.draw import build_floorplan
from typehaus.emit.draw.scene import Polyline, Text
from typehaus.emit.draw.stair_symbol import PLAN_CUT_HEIGHT_M
from typehaus.quantities import M_PER_IN
from typehaus.resolve.stairs.walkline import stair_walk_stations


def _stair(model, tag):
    return next(stair for stair in model.stairs if stair.tag == tag)


def _nodes(model, storey, uid=None, layer="A-STAIR"):
    return [node for node in build_floorplan(model, storey).nodes
            if getattr(node, "layer", None) == layer
            and (uid is None or getattr(node, "uid", None) == uid)]


def _polys(model, storey, uid=None, layer="A-STAIR"):
    return [node for node in _nodes(model, storey, uid, layer)
            if isinstance(node, Polyline)]


def _member_tags(model, storey, stair):
    keys = {member.child_key for member in stair.members}
    return {node.tag for node in _polys(model, storey, stair.uid) if node.tag in keys}


def _cut_z(model, storey):
    return model.plan.storey(storey).elevation.meters + PLAN_CUT_HEIGHT_M


# ----------------------------------------------------------------- 1. the cut plane
@pytest.mark.parametrize("tag,storey", [("ST-B2M", "basement"), ("ST-M2S", "main"),
                                        ("ST-S2A", "second")])
def test_a_departing_flight_is_cut_at_the_plan_cut_plane(catlin_model, tag, storey):
    """A plan is a horizontal cut 4'-0" up: everything above it is not in this drawing.

    One predicate, no storey branch — a walking surface draws iff its top is at or below
    the cut. That gives "cut the departing flight, draw the arriving one whole" for free on
    every layout, and the within-storey step-downs fall out uncut because none of them
    reaches 4'-0". Sixteen risers of a flight that leaves the storey is eight feet of stair
    that is not there.
    """
    stair = _stair(catlin_model, tag)
    cut = _cut_z(catlin_model, storey)
    surfaces = {m.child_key: m.z1_m for m in stair.members
                if m.category in ("tread", "winder", "landing") and m.p0 != m.p1}
    drawn = _member_tags(catlin_model, storey, stair)
    assert drawn, (tag, storey)
    assert any(z > cut for z in surfaces.values()), "nothing to cut — pick another case"
    for key in drawn:
        assert surfaces[key] <= cut + 1e-9, (tag, storey, key)


def test_a_within_storey_step_is_never_cut(catlin_model):
    """A 5-riser step-down never reaches the cut, so all of it draws — no special case."""
    stair = _stair(catlin_model, "ST-SG-PORCH")
    surfaces = {m.child_key for m in stair.members
                if m.category in ("tread", "winder", "landing") and m.p0 != m.p1}
    drawn = _member_tags(catlin_model, "main", stair)
    # Every surface either drew, or was suppressed by the ledger as a duplicate of the
    # flight's own footprint ring — never by the cut.
    assert drawn <= surfaces
    assert len(drawn) >= len(surfaces) - 1
    assert not [node for node in _polys(catlin_model, "main", stair.uid)
                if node.tag.startswith(f"{stair.tag}-break")]


# ----------------------------------------------------------------- 2. the break line
@pytest.mark.parametrize("tag,storey", [("ST-B2M", "basement"), ("ST-M2S", "main"),
                                        ("ST-S2A", "second")])
def test_a_departing_flight_gets_exactly_one_break_line(catlin_model, tag, storey):
    """Two parallel diagonals, at the walk line's own crossing of the cut elevation.

    It cannot be pinned to a riser line: ST-B2M's break on the basement plan lands on a
    LANDING. Interpolating the walk route in ``z`` is the one derivation that works for a
    tread, a landing edge and a winder fan alike.
    """
    stair = _stair(catlin_model, tag)
    breaks = sorted((node for node in _polys(catlin_model, storey, stair.uid)
                     if node.tag.startswith(f"{tag}-break")), key=lambda n: n.tag)
    assert [node.tag for node in breaks] == [f"{tag}-break-0", f"{tag}-break-1"]
    first, second = (LineString(node.points) for node in breaks)
    assert first.length == pytest.approx(second.length, rel=1e-9)
    # Parallel: equal direction, and offset by the pitch rather than crossing.
    def direction(node):
        (x0, y0), (x1, y1) = node.points[0], node.points[-1]
        run = math.hypot(x1 - x0, y1 - y0)
        return ((x1 - x0) / run, (y1 - y0) / run)
    assert direction(breaks[0]) == pytest.approx(direction(breaks[1]), abs=1e-9)
    assert not first.intersects(second)
    # ...and it sits where the walk crosses the cut, not at either end of the flight.
    cut = _cut_z(catlin_model, storey)
    route = stair_walk_stations(stair)
    crossing = next((lo, hi) for lo, hi in zip(route, route[1:]) if lo[2] <= cut < hi[2])
    t = (cut - crossing[0][2]) / (crossing[1][2] - crossing[0][2])
    want = tuple((crossing[0][i][j] + (crossing[1][i][j] - crossing[0][i][j]) * t)
                 / M_PER_IN for i in (0, 1) for j in (0, 1))
    centre = LineString([(want[0], want[1]), (want[2], want[3])]).centroid
    assert first.distance(centre) < 8.0   # within a going of the crossing, both sides


def test_an_arriving_only_plan_has_no_break_line(catlin_model):
    """Nothing was excluded, so nothing is broken — and no special case says so."""
    for tag, storey in (("ST-B2M", "main"), ("ST-M2S", "second"), ("ST-S2A", "attic")):
        stair = _stair(catlin_model, tag)
        assert not [node for node in _polys(catlin_model, storey, stair.uid)
                    if node.tag.startswith(f"{tag}-break")], (tag, storey)


def test_level_turn_draws_one_landing_outline(catlin_model):
    stair = _stair(catlin_model, "ST-M2S")
    tags = [node.tag for node in _polys(catlin_model, "second", stair.uid)]
    assert tags.count("landing-level") == 1
    assert "landing-lower" not in tags and "landing-upper" not in tags
    assert tags.count("ST-M2S-travel") == 1


# ----------------------------------------------------------------- 3. occlusion
def test_an_arriving_flight_is_hidden_under_the_departing_one(catlin_model):
    """From above, the flight coming up hides the one going down where they overlap.

    Occluded on THE POINT the line marks, not on a fraction of the tread board's area: an
    area rule needs a magic threshold and gets ST-B2M's ``tread-lower-005`` wrong — its
    board pokes 2.7" of 11" past ST-M2S's break, so any fraction below 25% leaves one
    orphan riser line stranded behind the break line.
    """
    departing = _member_tags(catlin_model, "main", _stair(catlin_model, "ST-M2S"))
    arriving = _member_tags(catlin_model, "main", _stair(catlin_model, "ST-B2M"))
    # ST-M2S climbs the east lane and is cut: six risers from the deck edge to the break.
    assert {t for t in departing if t.startswith("tread-lower-")} == {
        f"tread-lower-{i:03d}" for i in range(6)}
    assert "tread-lower-006" not in departing
    assert not {t for t in departing if t.startswith(("tread-upper-", "landing-"))}
    # ST-B2M's own east-lane flight is underneath it and gone; its west lane and both
    # half-landings stand clear and draw.
    assert not {t for t in arriving if t.startswith("tread-lower-")}
    assert {t for t in arriving if t.startswith("tread-upper-")}
    assert {"landing-lower", "landing-upper"} <= arriving


def test_a_well_with_one_flight_draws_it_whole(catlin_model):
    """No neighbour, so the band union is empty and nothing is hidden. No special case."""
    stair = _stair(catlin_model, "ST-S2A")
    surfaces = {m.child_key for m in stair.members
                if m.category in ("tread", "winder") and m.p0 != m.p1}
    drawn = _member_tags(catlin_model, "attic", stair)
    # One face per riser: every tread draws except the one the opening ring itself covers.
    assert len(drawn) >= len(surfaces) - 1
    assert drawn <= surfaces


# ----------------------------------------------------------------- 4. the travel line
@pytest.mark.parametrize("tag,storey", [("ST-M2S", "second"), ("ST-S2A", "attic")])
def test_the_travel_line_follows_the_walk_line(catlin_model, tag, storey):
    """Every vertex is a walking station's midpoint — never a bounding-box centreline.

    The old symbol drew one straight segment between the two ends of ``stair.outline``,
    which IS the floor opening's ring. On a U that puts the heaviest line on the sheet
    (0.50 mm) exactly on the WELL PARTITION, between the two lanes and across the landing
    zone; on a winder it runs one straight segment across the fan.
    """
    stair = _stair(catlin_model, tag)
    travel = next(node for node in _polys(catlin_model, storey, stair.uid)
                  if node.tag == f"{tag}-travel")
    mids = {(round(((a[0] + b[0]) / 2.0) / M_PER_IN, 6),
             round(((a[1] + b[1]) / 2.0) / M_PER_IN, 6))
            for a, b, _ in stair_walk_stations(stair)}
    for point in travel.points:
        assert (round(point[0], 6), round(point[1], 6)) in mids, (tag, storey, point)
    assert len(travel.points) >= 3
    # Monotone in climb order: the vertices follow the route, they do not double back.
    order = [a for a, b, _ in stair_walk_stations(stair)]
    assert len(travel.points) == len({tuple(p) for p in travel.points}), "a repeated vertex"
    assert order  # the route exists; the per-vertex membership above is the real assertion


def test_the_travel_line_is_clipped_at_the_break(catlin_model):
    """A departing flight's travel line ends at the break, arrow pointing into it."""
    stair = _stair(catlin_model, "ST-M2S")
    travel = next(node for node in _polys(catlin_model, "main", stair.uid)
                  if node.tag == "ST-M2S-travel")
    breaks = [node for node in _polys(catlin_model, "main", stair.uid)
              if node.tag.startswith("ST-M2S-break")]
    end = travel.points[-1]
    assert min(LineString(node.points).distance(
        LineString([end, end]).centroid) for node in breaks) < 6.0
    # ...and the arriving flight below it starts where the departing one's band ends,
    # rather than running out from under it.
    below = next(node for node in _polys(catlin_model, "main",
                                         _stair(catlin_model, "ST-B2M").uid)
                 if node.tag == "ST-B2M-travel")
    assert below.points[0][1] > _stair(catlin_model, "ST-B2M").outline[0][1] / M_PER_IN


def test_the_travel_line_has_an_arrow_at_the_top_and_a_tick_at_the_start(catlin_model):
    """Both as plain IR geometry — a three-point V and a perpendicular tick.

    ``span-arrow``, the only arrow in the symbol vocabulary, renders as a bare LINE with no
    head in ``dxf_writer`` and in a hardcoded brown in ``pdf_writer``; a new symbol name
    costs entries in both writers plus ``SYMBOL_NAMES_WITH_DEDICATED_GLYPH`` and its two
    tests. ``Leader`` is not an option either — it requires ``text``.
    """
    stair = _stair(catlin_model, "ST-S2A")
    drawn = {node.tag: node for node in _polys(catlin_model, "attic", stair.uid)}
    travel, arrow, tick = (drawn["ST-S2A-travel"], drawn["ST-S2A-arrow"],
                           drawn["ST-S2A-start"])
    assert len(arrow.points) == 3 and not arrow.closed
    assert arrow.points[1] == travel.points[-1]      # the head is ON the ascending end
    assert len(tick.points) == 2
    start = travel.points[0]
    assert LineString(tick.points).centroid.distance(
        LineString([start, start]).centroid) < 1e-6
    # The tick is perpendicular to the travel line it starts.
    (tx0, ty0), (tx1, ty1) = tick.points
    (px, py), (qx, qy) = travel.points[0], travel.points[1]
    assert abs((tx1 - tx0) * (qx - px) + (ty1 - ty0) * (qy - py)) < 1e-6


# ----------------------------------------------------------------- 5. the ledger
def test_no_stair_line_is_doubled_on_a_landing_edge(catlin_model):
    """One line per riser face, and each face drawn by exactly ONE owner.

    On the second-floor plan the upper flight's springing riser lies on ``landing-upper``'s
    own south edge and its arrival nosing lies on ``FO-S-STAIR``'s ring — both drawn a
    second time as riser lines, which is the doubled line a reader counts as an extra
    riser. Not key equality: the landing rectangle spans lane → partition centre while the
    riser spans the lane, so they are collinear-but-unequal.
    """
    checked = 0
    for storey in (s.tag for s in catlin_model.plan.storeys):
        keys = {member.child_key for stair in catlin_model.stairs
                for member in stair.members if member.category in ("tread", "winder")}
        risers, owners = [], []
        for node in [*_polys(catlin_model, storey),
                     *_polys(catlin_model, storey, layer="A-FLOR-OPEN")]:
            points = list(node.points)
            ends = [*points[1:], points[0]] if node.closed else points[1:]
            edges = list(zip(points, ends))
            if node.tag in keys and len(points) == 2:
                risers.extend(edges)
            else:
                owners.extend(edges)
        for a, b in risers:
            checked += 1
            for p, q in [*owners, *(pair for pair in risers if pair != (a, b))]:
                assert not _covers(p, q, a, b), (storey, (a, b), (p, q))
    assert checked >= 30, "no riser lines were examined"


def _covers(p, q, a, b) -> bool:
    """``a``-``b`` collinear with ``p``-``q`` and inside it — the ledger's own predicate."""
    dx, dy = q[0] - p[0], q[1] - p[1]
    run = math.hypot(dx, dy)
    if run < 1e-6 or math.dist(a, b) < 1e-6:
        return False
    ux, uy = dx / run, dy / run
    ts = []
    for point in (a, b):
        ox, oy = point[0] - p[0], point[1] - p[1]
        if abs(ox * uy - oy * ux) > 1e-6:
            return False
        ts.append(ox * ux + oy * uy)
    return min(ts) >= -1e-6 and max(ts) <= run + 1e-6


def test_the_floor_opening_ring_closes_the_treads(catlin_model):
    """A flight in a well is bounded by the well's ring; one with no well draws its own.

    Every ``FloorOpening`` is drawn once, on the plan of the deck it perforates — which for
    all three catlin wells is the plan the stair ARRIVES at, so the ledger gets the arrival
    nosing for free and nothing is drawn twice. A within-storey step-down cuts no deck and
    has no ring, so ``dispatch._flight_footprint``'s own outline is what closes its treads.
    """
    rings = {node.tag for node in _polys(catlin_model, "second", layer="A-FLOR-OPEN")}
    assert "FO-S-STAIR" in rings
    # Two side edges per drawn tread flight, derived from the DRAWN marks so an occluded
    # flight leaves no stray line behind the break.
    edges = {node.tag for node in _polys(catlin_model, "second",
                                         _stair(catlin_model, "ST-M2S").uid)
             if "-edge-" in node.tag}
    assert edges == {"tread-lower-edge-0", "tread-lower-edge-1",
                     "tread-upper-edge-0", "tread-upper-edge-1"}
    # The step-down with no opening draws its own footprint ring instead.
    porch = _stair(catlin_model, "ST-SG-PORCH")
    well = next(node for node in _polys(catlin_model, "main", porch.uid)
                if node.tag == "ST-SG-PORCH-well")
    assert well.closed
    assert Polygon([(x * M_PER_IN, y * M_PER_IN) for x, y in well.points]).equals(
        Polygon(porch.outline))


# ----------------------------------------------------------------- 6. the labels
def test_the_up_and_down_labels_sit_on_their_own_lanes(catlin_model):
    """Two flights in one well no longer share a bbox centre, so nothing is nudged apart.

    "UP 16 R" and "UP 15 R" were printed on top of each other in the middle of one well —
    both reading UP, because which way a flight goes is a fact about the READER's storey.
    Each label now sits beside its own travel line, on the side away from the other one.
    """
    texts = [node for node in _nodes(catlin_model, "main") if isinstance(node, Text)]
    up = next(node for node in texts if node.content == "UP 16 R")
    down = next(node for node in texts if node.content == "DN 15 R")
    lane = max(math.dist(node.points[0], node.points[-1])
               for node in _polys(catlin_model, "main",
                                  _stair(catlin_model, "ST-M2S").uid)
               if node.tag.startswith("tread-lower-"))
    assert abs(up.anchor[0] - down.anchor[0]) >= lane
    # Each is nearer its OWN flight's travel line than the other's.
    for label, tag in ((up, "ST-M2S"), (down, "ST-B2M")):
        own, other = (next(node for node in _polys(catlin_model, "main",
                                                   _stair(catlin_model, t).uid)
                           if node.tag == f"{t}-travel")
                      for t in ((tag, "ST-B2M") if tag == "ST-M2S" else (tag, "ST-M2S")))
        point = LineString([label.anchor, label.anchor]).centroid
        assert LineString(own.points).distance(point) < \
            LineString(other.points).distance(point), label.content


def test_a_floor_opening_says_what_is_over_it(catlin_model):
    """A-104 names the hole the attic's stair hall is, which is the whole of TODO 370.

    A hole in a deck and a deck look identical from above, and the architectural plan never
    read ``FloorSystem.openings`` at all — ``houses/catlin/plan/views.py`` answered the
    question with a SECTION (``SL-D-STAIRVOID``) because the plan could not. There was no
    ``OPEN TO BELOW`` string anywhere in the repo.
    """
    notes = [node for node in build_floorplan(catlin_model, "attic").nodes
             if isinstance(node, Text) and node.layer == "A-ANNO-TEXT"]
    captions = [node.content for node in notes]
    assert captions.count("OPEN TO STAIR BELOW") == 2   # FO-A-STAIR and FO-A-HALL
    # The ring is drawn too, and on its own layer.
    rings = {node.tag for node in _polys(catlin_model, "attic", layer="A-FLOR-OPEN")}
    holes = {tag for tag in catlin_model.plan.by_tag("FS-ATTIC").openings
             if tag not in ("FO-A-STAIR", "FO-A-HALL")}
    assert holes, "the attic deck's chase and riser holes"
    # The chase and riser holes (2026-09-24) draw their rings too; only the wells say BELOW.
    assert rings == {"FO-A-STAIR", "FO-A-HALL"} | holes
    # A chase says so, and nothing says "OPEN TO ABOVE" on the storey below.
    main = [node.content for node in build_floorplan(catlin_model, "main").nodes
            if isinstance(node, Text) and node.layer == "A-ANNO-TEXT"]
    # Too narrow for the full caption, a chase shortens to CHASE rather than spill next door.
    assert "CHASE" in main
    assert not [caption for caption in main + captions if "ABOVE" in caption]
