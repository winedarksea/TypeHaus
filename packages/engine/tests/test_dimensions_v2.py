"""Auto-dimensioner v2/v3 — plan dimension tiers + annotated roof plan.

Permit reviewers must be able to locate every opening and wall from the plan sheet, so the
floorplan carries a dimension LADDER, inner to outer: the per-facade opening strings at
14", the face-to-face interior partition chains at 44", and the overall bbox chain at 76".
The roof plan carries slope arrows, pitch notes, dashed ridges, and eave-overhang
dimensions.

Two things moved under these tests when the interior tier landed. Every exterior chain is
struck on the SHEATHING FACE rather than the wall axis — a builder pulls a tape to a face —
so the extents here come from ``_shared.wall_face_bounds``. And a crowded string staggers
onto one of ``STAGGER_ROWS`` rows rather than printing through its neighbour, so a tier is
now an offset *band* (base to base + 2 rows) rather than one literal offset.
"""

from __future__ import annotations

import math

import pytest

from typehaus.emit.draw._shared import (
    _FACADE_TOL_M,
    _MIN_STATION_GAP_IN,
    wall_face_bounds,
)
from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.roofplan import build_roof_plan
from typehaus.emit.draw.scene import ArchDimension, Polyline, Symbol, Text
from typehaus.quantities import M_PER_IN

STRING_OFFSET = 14.0
INTERIOR_OFFSET = 44.0
OVERALL_OFFSET = 76.0
# A staggered string sits up to two rows outside its tier's base offset; the tiers are 30"
# apart so a row can never be mistaken for the next tier down.
TIER_BAND = 25.0


@pytest.fixture(scope="module")
def main_scene(catlin_model):
    return build_floorplan(catlin_model, "main")


@pytest.fixture(scope="module")
def roof_scene(catlin_model):
    return build_roof_plan(catlin_model)


def _dims(scene):
    return [n for n in scene.nodes if isinstance(n, ArchDimension)]


def _axis_bbox_in(catlin_model, storey):
    """The FACE bbox, inches — the four coordinates a facade chain lies on."""
    walls = [w for w in catlin_model.walls if w.storey == storey]
    minx, maxx, miny, maxy = wall_face_bounds(walls)
    return minx / M_PER_IN, maxx / M_PER_IN, miny / M_PER_IN, maxy / M_PER_IN


def _facade_chain(scene, bbox, facade):
    """The string-tier segments on one facade, sorted along the facade."""
    minx, maxx, miny, maxy = bbox
    out = []
    for d in _dims(scene):
        if not STRING_OFFSET - 1e-6 <= abs(d.offset) <= STRING_OFFSET + TIER_BAND:
            continue
        horizontal = abs(d.p1[0] - d.p0[0]) >= abs(d.p1[1] - d.p0[1])
        if facade == "S" and horizontal and d.offset < 0 and abs(d.p0[1] - miny) < 1e-6:
            out.append(d)
        elif facade == "N" and horizontal and d.offset > 0 and abs(d.p0[1] - maxy) < 1e-6:
            out.append(d)
        elif facade == "W" and not horizontal and d.offset < 0 and abs(d.p0[0] - minx) < 1e-6:
            out.append(d)
        elif facade == "E" and not horizontal and d.offset > 0 and abs(d.p0[0] - maxx) < 1e-6:
            out.append(d)
    axis = 0 if facade in ("S", "N") else 1
    return sorted(out, key=lambda d: d.p0[axis]), axis


# --- floorplan facade strings -------------------------------------------------------

def test_overall_chain_moved_outside_the_string_tier(main_scene):
    overall = [d for d in _dims(main_scene) if abs(d.offset) == OVERALL_OFFSET]
    assert len(overall) == 2  # E-W + N-S bbox dims, now stacked outside the strings
    # ...and outside the interior tier too, which is the one that landed between them.
    interior = [d for d in _dims(main_scene)
                if INTERIOR_OFFSET - 1e-6 <= abs(d.offset) <= INTERIOR_OFFSET + TIER_BAND]
    assert interior, "the interior partition chains must reach the plan"
    assert max(abs(d.offset) for d in interior) < OVERALL_OFFSET


def test_the_overall_chain_measures_the_sheathing_face(catlin_model, main_scene):
    """The overall chain is struck on the SHEATHING FACE — a builder pulls a tape to a face.

    catlin reads 36'-0" either way and that is not a coincidence to lean on: the house
    aligns every exterior wall on ``face("sheathing-ext")``, so its sheathing plane sits
    exactly on the node line and the axis bbox happens to agree. A house authored on
    centrelines would be half a wall short at each end, which is a dimension nobody can
    pull, and the reference is what makes that case right too.
    """
    walls = [w for w in catlin_model.walls if w.storey == "main"]
    face_minx, face_maxx, face_miny, face_maxy = wall_face_bounds(walls)
    assert (face_maxx - face_minx) / M_PER_IN == pytest.approx(432.0, abs=1e-6)
    assert (face_maxy - face_miny) / M_PER_IN == pytest.approx(432.0, abs=1e-6)

    overall = [d for d in _dims(main_scene) if abs(d.offset) == OVERALL_OFFSET]
    horizontal = next(d for d in overall if abs(d.p1[0] - d.p0[0]) > abs(d.p1[1] - d.p0[1]))
    assert horizontal.p1[0] - horizontal.p0[0] == pytest.approx(
        (face_maxx - face_minx) / M_PER_IN, abs=1e-6)


def test_interior_chains_measure_partition_faces_and_close_on_the_envelope(catlin_model):
    """Both bearing directions, face to face, and each chain still sums to the overall.

    The sum is the property that makes a chain a chain: ``plan_dimensions`` merges crowded
    stations at a coarser gap rather than dropping any, precisely so this holds.
    """
    walls = [w for w in catlin_model.walls if w.storey == "main"]
    minx, maxx, miny, maxy = (v / M_PER_IN for v in wall_face_bounds(walls))
    scene = build_floorplan(catlin_model, "main")
    chains = [d for d in _dims(scene)
              if INTERIOR_OFFSET - 1e-6 <= abs(d.offset) <= INTERIOR_OFFSET + TIER_BAND]
    for horizontal, lo, hi in ((True, minx, maxx), (False, miny, maxy)):
        axis = 0 if horizontal else 1
        chain = sorted((d for d in chains
                        if (abs(d.p1[0] - d.p0[0]) >= abs(d.p1[1] - d.p0[1])) is horizontal),
                       key=lambda d: d.p0[axis])
        assert chain, ("no interior chain on axis", axis)
        assert chain[0].p0[axis] == pytest.approx(lo, abs=1e-6)
        assert chain[-1].p1[axis] == pytest.approx(hi, abs=1e-6)
        for prev, nxt in zip(chain, chain[1:], strict=False):
            assert prev.p1[axis] == pytest.approx(nxt.p0[axis], abs=1e-6)  # contiguous
        total = sum(d.p1[axis] - d.p0[axis] for d in chain)
        assert total == pytest.approx(hi - lo, abs=1e-6)


def test_every_facade_chain_is_contiguous_sorted_and_sums_to_overall(
        catlin_model, main_scene):
    bbox = _axis_bbox_in(catlin_model, "main")
    minx, maxx, miny, maxy = bbox
    overall = {"S": maxx - minx, "N": maxx - minx, "W": maxy - miny, "E": maxy - miny}
    chains_found = 0
    for facade in ("S", "N", "W", "E"):
        chain, axis = _facade_chain(main_scene, bbox, facade)
        if not chain:
            continue  # a bare facade legitimately emits nothing extra
        chains_found += 1
        lo = minx if axis == 0 else miny
        hi = maxx if axis == 0 else maxy
        assert abs(chain[0].p0[axis] - lo) < 1e-6, facade
        assert abs(chain[-1].p1[axis] - hi) < 1e-6, facade
        total = 0.0
        for prev, nxt in zip(chain, chain[1:]):
            assert abs(prev.p1[axis] - nxt.p0[axis]) < 1e-6, facade  # contiguous
        for d in chain:
            seg = d.p1[axis] - d.p0[axis]
            assert seg >= _MIN_STATION_GAP_IN - 1e-6, facade  # no degenerate segments
            total += seg
        assert abs(total - overall[facade]) < 1e-6, facade  # segments sum to overall
    assert chains_found >= 2  # catlin's main floor has walls/openings on its facades


def test_stations_are_deduped(catlin_model, main_scene):
    bbox = _axis_bbox_in(catlin_model, "main")
    for facade in ("S", "N", "W", "E"):
        chain, axis = _facade_chain(main_scene, bbox, facade)
        stations = [d.p0[axis] for d in chain] + [d.p1[axis] for d in chain[-1:]]
        for a, b in zip(stations, stations[1:]):
            assert b - a >= _MIN_STATION_GAP_IN - 1e-6


def test_facade_opening_centerlines_appear_as_stations(catlin_model, main_scene):
    walls = {w.tag: w for w in catlin_model.walls if w.storey == "main"}
    bbox = _axis_bbox_in(catlin_model, "main")
    minx, maxx, miny, maxy = (v * M_PER_IN for v in bbox)
    checked = 0
    for op in catlin_model.openings:
        wall = walls.get(op.host_wall)
        if wall is None:
            continue
        (sx, sy), (ex, ey) = wall.axis
        # Only walls lying on a facade line participate in that facade's string.
        for facade, coord, axis in (("S", miny, 0), ("N", maxy, 0),
                                    ("W", minx, 1), ("E", maxx, 1)):
            perp = 1 - axis
            if (abs(wall.axis[0][perp] - coord) > _FACADE_TOL_M
                    or abs(wall.axis[1][perp] - coord) > _FACADE_TOL_M):
                continue
            length = math.hypot(ex - sx, ey - sy) or 1.0
            t = op.center_along_m / length
            station = (sx + (ex - sx) * t, sy + (ey - sy) * t)[axis] / M_PER_IN
            chain, _ = _facade_chain(main_scene, bbox, facade)
            ends = {round(d.p0[axis], 3) for d in chain} | {round(d.p1[axis], 3)
                                                            for d in chain}
            # The centerline is a chain station unless deduped into a neighbour <1" away.
            assert any(abs(e - station) < _MIN_STATION_GAP_IN for e in ends), (
                f"{op.tag} centerline missing from {facade} string")
            checked += 1
    assert checked > 0  # catlin has openings hosted on facade walls


def test_second_storey_also_gets_strings(catlin_model):
    scene = build_floorplan(catlin_model, "second")
    bbox = _axis_bbox_in(catlin_model, "second")
    assert any(_facade_chain(scene, bbox, f)[0] for f in ("S", "N", "W", "E"))


# --- roof plan ----------------------------------------------------------------------

def test_roof_plan_has_downslope_arrows_with_pitch_notes(catlin_model, roof_scene):
    arrows = [n for n in roof_scene.nodes if isinstance(n, Symbol)
              and n.name == "span-arrow"]
    gables = [r for r in catlin_model.roofs if r.form == "gable"]
    assert len(arrows) == 2 * len(gables)  # one per plane
    for roof in gables:
        expected = 90.0 if roof.ridge_direction == "x" else 0.0
        rotations = {a.rotation for a in arrows if a.uid == roof.uid}
        assert rotations == {expected, (expected + 180.0) % 360.0}
    # The two roofs differ in pitch (RF-HOUSE 6:12, RF-GARAGE 4:12), so the note is
    # per-plane and per-roof, not one string for the house.
    for roof in gables:
        pitch = catlin_model.plan.by_tag(roof.tag).pitch
        note = f"{pitch.rise:g}:{pitch.run:g}"
        notes = [n for n in roof_scene.nodes if isinstance(n, Text) and n.content == note]
        assert len(notes) == 2, (roof.tag, note, [n.content for n in roof_scene.nodes
                                                 if isinstance(n, Text)])
    assert {"4:12", "6:12"} <= {n.content for n in roof_scene.nodes if isinstance(n, Text)}


def test_roof_plan_ridge_is_dashed(catlin_model, roof_scene):
    ridges = [n for n in roof_scene.nodes if isinstance(n, Polyline)
              and (n.tag or "").endswith("-ridge")]
    assert len(ridges) == len(catlin_model.roofs)
    assert all(r.linetype == "DASHED" for r in ridges)


def test_roof_plan_dimensions_the_garage_overhang_once(catlin_model, roof_scene):
    garage = next(r for r in catlin_model.roofs if r.tag == "RF-GARAGE")
    house = next(r for r in catlin_model.roofs if r.tag == "RF-HOUSE")
    dims = _dims(roof_scene)
    garage_dims = [d for d in dims if d.uid == garage.uid]
    # 1'-4" authored overhang on every edge, measured wall face → roof edge: one dim
    # per *distinct* value (the two eave faces differ by their wall alignment).
    assert garage_dims
    lengths = [round(math.hypot(d.p1[0] - d.p0[0], d.p1[1] - d.p0[1]) * 4)
               for d in garage_dims]
    assert len(lengths) == len(set(lengths))  # deduped by value
    for d in garage_dims:
        length = math.hypot(d.p1[0] - d.p0[0], d.p1[1] - d.p0[1])
        assert 6.0 <= length <= 16.0 + 1e-6  # 16" less the cladding the eave clears
    # The zero-overhang house roof gets no fabricated eave dimension — except the one the
    # cladding LAP produces, which is not an overhang: the footprint runs 7 1/4" past the
    # sheathing datum to cover the wall panel, and the roof plan dimensions that face-to-edge
    # distance like any other. The attic's bearing walls are skinless rafter plates, and
    # `roof_layer_setbacks._skinned` resolves their stand-in to draw the lap.
    house_dims = [d for d in dims if d.uid == house.uid]
    for d in house_dims:
        length = math.hypot(d.p1[0] - d.p0[0], d.p1[1] - d.p0[1])
        # 7 3/4": the 7 1/4" wall stack outboard of the sheathing datum plus the 1/2" the
        # rafter plate's axis sits inboard of that datum (it stands over the studs below,
        # not over the sheathing). Anything larger would be a real fabricated overhang.
        assert length <= 7.75 + 1e-6, (length, "that is an overhang, not a cladding lap")


def test_roof_plan_symbols_are_known_to_both_writers(roof_scene):
    from typehaus.emit.draw.dxf_writer import (
        SYMBOL_NAMES_WITH_DEDICATED_GLYPH as DXF_GLYPHS,
    )
    from typehaus.emit.draw.pdf_writer import (
        SYMBOL_NAMES_WITH_DEDICATED_GLYPH as PDF_GLYPHS,
    )

    names = {n.name for n in roof_scene.nodes if isinstance(n, Symbol)}
    assert names <= DXF_GLYPHS and names <= PDF_GLYPHS
