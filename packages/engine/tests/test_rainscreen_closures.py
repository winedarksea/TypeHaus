"""catlin's rainscreen cavity drains, vents and is insect-tight at its base, heads and band.

The ccSPF face in the 2" vented cavity has no protection but a physical one, so these pin the
derived closures (``resolve/rainscreen_closures.py``, ``rainscreen_strips.py``,
``opening_head_cap.py``), the roof deck that caps the top, and the grade that reads them.
"""

from __future__ import annotations

from copy import copy
from dataclasses import replace

import pytest

from typehaus.model.enums import TrimKind
from typehaus.quantities import inch
from typehaus.resolve.geometry import wall_frame
from typehaus.resolve.rainscreen_closures import (
    BASE_SCREEN_PRODUCT,
    cavity_base_run,
    net_free_area_cm2_per_m,
    opening_head_spans,
    rainscreen_cavity_m,
)
from typehaus.resolve.rainscreen_strips import BAND_OUTLET_PRODUCT, STRIP_PRODUCT
from typehaus.takeoff.envelope import bug_screen_takeoff

_RAINSCREEN = ("EXT_2X6", "PLANT_EXT_2X6_HUMID",
               "EXT_2X6_BOARD_BATTEN", "PLANT_EXT_2X6_HUMID_BOARD_BATTEN")
_M_TO_FT = 3.280839895
_IN = inch(1).meters


def _of(model, host, product):
    return [s for s in model.solids if s.host_ref == host and s.product == product]


def test_every_metal_window_head_is_capped_and_every_head_seats_on_a_strip(catlin_model_ro):
    model = catlin_model_ro
    walls = {w.tag: w for w in model.walls}
    assert not [s for s in model.solids if s.tag.endswith("-HEADSCREEN")]
    windows = [o for o in model.openings if o.kind == "window"
               and walls[o.host_wall].assembly in _RAINSCREEN]
    assert len(windows) >= 38
    face = inch(3.5).meters
    for opening in windows:
        wall = walls[opening.host_wall]
        caps = _of(model, opening.tag, "OPENING_HEAD_CAP")
        assert caps and all(c.category == "cladding_trim" for c in caps), opening.tag
        assert [s.category for s in _of(model, opening.tag, STRIP_PRODUCT)] \
            == [TrimKind.BUG_SCREEN.value]
        # On the head course, over both jamb posts: the RO plus a 3-1/2" face each side.
        head = wall.base_ref_z_m + opening.sill_m + opening.height_m
        origin, tangent, _across, _length = wall_frame(wall)
        stations = [(x - origin[0]) * tangent[0] + (y - origin[1]) * tangent[1]
                    for c in caps for x, y, _ in c.body_mesh.positions]
        assert max(stations) - min(stations) == pytest.approx(opening.width_m + 2 * face,
                                                              abs=1e-6)
        assert min(c.z0_m for c in caps) < head + face < max(c.z1_m for c in caps)
    rough = [o for o in model.openings if o.kind == "rough_opening"]
    assert rough and not [o for o in rough if _of(model, o.tag, "OPENING_HEAD_CAP")]
    bare = [o for o in model.openings if rainscreen_cavity_m(walls[o.host_wall].layers) is None]
    assert bare and not [o for o in bare if _of(model, o.tag, STRIP_PRODUCT)]


def test_the_take_off_is_the_resolved_pieces(catlin_model_ro):
    model = catlin_model_ro
    rows = {row["kind"]: row for row in bug_screen_takeoff(model)}
    assert set(rows) == {BASE_SCREEN_PRODUCT, STRIP_PRODUCT, BAND_OUTLET_PRODUCT, "EPDM_PAD"}
    for kind, row in rows.items():
        pieces = [s for s in model.solids if s.product == kind]
        assert row["length_ft"] == pytest.approx(
            sum(s.trim_length_m for s in pieces) * _M_TO_FT, abs=0.1), kind
    runs = [run for wall in model.walls if (run := cavity_base_run(model, wall))]
    assert rows[BASE_SCREEN_PRODUCT]["tags"] == sorted(run.wall.tag for run in runs)
    heads = sum(len(opening_head_spans(model, w)) for w in model.walls)
    assert len({s.host_ref for s in model.solids if "-HEADSTRIP-" in s.tag
                and s.product == STRIP_PRODUCT}) <= heads


def test_the_cavity_top_stays_closed_by_the_roof_deck(catlin_model_ro):
    """Decision: no screen at the eave or rake, because there is no opening there. The deck
    oversails to the girt's OUTER face on every edge of RF-HOUSE, so the cavity's top is the
    underside of the deck. Clipped back at the wall sheathing face instead, it would leave
    the whole 2" cavity open into the roof edge."""
    from typehaus.model.enums import LayerFunction
    from typehaus.resolve.roof_layer_setbacks import above_structure_layers, layer_edge_setbacks

    model = catlin_model_ro
    roof = next(r for r in model.roofs if r.tag == "RF-HOUSE")
    layers = above_structure_layers(model.plan.library.resolve_assembly(roof.assembly))
    deck_index = next(i for i, layer in enumerate(layers)
                      if layer.function is LayerFunction.SHEATHING)
    deck = layer_edge_setbacks(model, roof)[deck_index]
    girt_face = max(
        sum(ly.thickness_m for ly in w.depth_layers()[i + 1:])
        for w in model.walls if w.assembly in _RAINSCREEN
        for i in [max(j for j, ly in enumerate(w.depth_layers()) if ly.function == "furring")])
    for edge in ("west", "east", "south", "north"):
        assert 0.0 <= deck[edge] <= girt_face + 1e-6, (edge, deck[edge], girt_face)


def test_every_base_screen_stands_at_least_six_inches_above_grade(catlin_model_ro):
    """A screen at grade is a screen under mulch and snow, which neither vents nor drains."""
    from typehaus.resolve.site_earth import local_grade_elevation_m

    model = catlin_model_ro
    bases = [s for s in model.solids if s.product == BASE_SCREEN_PRODUCT]
    assert bases
    for screen in bases:
        grade, _why = local_grade_elevation_m(model, list(screen.outline))
        assert screen.z0_m - grade >= inch(6).meters, (screen.tag, screen.z0_m - grade)


def test_base_stack_on_a_house_wall(catlin_model_ro):
    """W-M-W4 by hand, S = the seat at -1'-1 7/16": the 2x2 U spans the 2" cavity on the pan;
    the trim foot stands at S+1" with its back leg on the girt plane, lapping the U 1" on the
    EPDM; the strip sits on the foot; the starter girt runs S+2-1/4" to S+5-3/4"."""
    model = catlin_model_ro
    wall = model.wall("W-M-W4")
    run = cavity_base_run(model, wall)
    seat = wall.z0_m
    assert seat / _IN == pytest.approx(-13.4375)
    screen = _of(model, "W-M-W4", BASE_SCREEN_PRODUCT)
    n = run.outward
    offsets = [x * n[0] + y * n[1] for s in screen for x, y, _ in s.body_mesh.positions]
    assert (max(offsets) - min(offsets)) / _IN == pytest.approx(2.0)
    assert (max(s.z1_m for s in screen) - seat) / _IN == pytest.approx(2.04, abs=0.01)
    trim = [s for s in model.solids if s.tag.startswith("TRIM-W-M-W4-BASE-")]
    assert sorted(round(p.trim_length_m / _IN, 2) for p in trim) == [42.75, 122.0]
    leg = min(x * n[0] + y * n[1] for t in trim for x, y, _ in t.body_mesh.positions)
    assert leg >= run.outer_offset + inch(0.0625).meters - 1e-6
    foot = max(z for t in trim for x, y, z in t.body_mesh.positions
               if x * n[0] + y * n[1] < leg + inch(0.05).meters and z < seat + 2 * _IN)
    assert (foot - seat) / _IN == pytest.approx(1.0, abs=1e-6)
    epdm = _of(model, "W-M-W4", "EPDM_BASE_ISOLATION")[0]
    assert (epdm.z0_m - seat) / _IN == pytest.approx(1.0, abs=1e-6)
    assert epdm.z1_m == pytest.approx(max(s.z1_m for s in screen))
    strips = [s for s in _of(model, "W-M-W4", STRIP_PRODUCT) if "-BASESTRIP-" in s.tag]
    assert strips and min(s.z0_m for s in strips) == pytest.approx(foot + inch(1 / 16).meters)
    starter = min((m for m in wall.members if m.child_key.startswith("strapping-outer-girt")),
                  key=lambda m: m.z0_m)
    assert ((starter.z0_m - seat) / _IN, (starter.z1_m - seat) / _IN) \
        == pytest.approx((2.25, 5.75))
    # The hand count: 1.002" of open screen at 32.6% open is 83 cm2/m (DIN 18516-1: 50).
    fraction = model.plan.library.material(screen[0].material).open_area_fraction
    assert fraction == pytest.approx(0.326, abs=5e-4)
    assert net_free_area_cm2_per_m(epdm.z0_m - (seat - 0.0017 * _IN), fraction) \
        == pytest.approx(83.0, abs=0.5)


def _grade(model, part):
    from typehaus.checks.integrity import rainscreen_cavity

    return getattr(rainscreen_cavity, part)(model)


def test_cavity_grades_pass_catlin(catlin_model_ro):
    for part in ("_base", "_kdat", "_heads", "_band", "_panel_end_strips"):
        findings = _grade(catlin_model_ro, part)
        assert any(f.result.name == "PASS" for f in findings), part
        # The one ungraded head is the catalog door's, a recorded hold point.
        assert [f.element_tags for f in findings if f.result.name != "PASS"] \
            == ([("D-S-DECK-E",)] if part == "_heads" else []), (part, findings)


def _failing(model, part, needle):
    return [f for f in _grade(model, part) if f.result.name == "FAIL" and needle in f.message]


@pytest.mark.parametrize("case", ["coarse", "no screen", "dammed", "kdat", "no band strip",
                                  "no head cap"])
def test_cavity_grade_fails(catlin_model_ro, monkeypatch, case):
    model = copy(catlin_model_ro)
    if case == "coarse":
        from typehaus.checks.integrity import rainscreen_cavity

        monkeypatch.setattr(rainscreen_cavity, "perforation", lambda *_: (0.2, 0.326))
        assert _failing(model, "_base", "insects pass")
    elif case == "no screen":
        model.solids = [s for s in model.solids
                        if not (s.host_ref == "W-M-W4" and s.product == BASE_SCREEN_PRODUCT)]
        assert _failing(model, "_base", "W-M-W4: the cavity base is open to insects")
    elif case == "dammed":
        drop = inch(1).meters

        def lowered(s):
            mesh = replace(s.body_mesh, positions=tuple(
                (x, y, z - drop) for x, y, z in s.body_mesh.positions))
            return replace(s, body_mesh=mesh)
        model.solids = [lowered(s) if s.tag.startswith("TRIM-W-M-W4-BASE-")
                        or (s.host_ref == "W-M-W4" and s.product == "EPDM_BASE_ISOLATION")
                        else s for s in model.solids]
        assert _failing(model, "_base", "W-M-W4: the base trim dams the pan edge")
    elif case == "kdat":
        wall = model.wall("W-M-W4")
        rise = wall.girt_starter_rise_m
        members = tuple(replace(m, z0_m=m.z0_m - rise, z1_m=m.z1_m - rise)
                        if m.z0_m < wall.z0_m + inch(6).meters else m for m in wall.members)
        model.walls = [replace(w, members=members) if w.tag == "W-M-W4" else w
                       for w in model.walls]
        model.index_by_tag()
        assert _failing(model, "_kdat", "W-M-W4: KDAT")
    elif case == "no head cap":
        model.solids = [s for s in model.solids
                        if not (s.host_ref == "WIN-M-BED-S1" and s.product == "OPENING_HEAD_CAP")]
        assert _failing(model, "_heads", "WIN-M-BED-S1: the cavity over the head has no cap")
    else:
        model.solids = [s for s in model.solids
                        if not (s.host_ref == "W-S-S1" and s.product == BAND_OUTLET_PRODUCT)]
        assert _failing(model, "_band", "W-S-S1: the band has no vented outlet")


def test_base_z_matches_screen_and_follows_stock_laps(catlin_model_ro):
    model = catlin_model_ro
    runs = [run for wall in model.walls if (run := cavity_base_run(model, wall)) is not None]
    assert len(runs) == 14
    run = next(run for run in runs if run.wall.tag == "W-M-W4")
    assert (run.end - run.start) / _IN == pytest.approx(162)
    pieces = _of(model, "W-M-W4", "RAINSCREEN_BASE_Z")
    assert sorted(s.trim_length_m / _IN for s in pieces) == pytest.approx([44, 120])
    assert all(s.material == "aluminum-flat-pvdf" for s in pieces)
    assert sorted(s.trim_length_m / _IN for s in _of(model, "W-M-W4", BASE_SCREEN_PRODUCT)) \
        == pytest.approx([44, 120])
    assert len([s for s in model.solids if s.product == "EPDM_BASE_ISOLATION"]) == 14


def test_base_run_is_independent_of_wall_axis_direction(catlin_model_ro):
    model = catlin_model_ro
    wall = model.wall("W-M-W4")
    forward = cavity_base_run(model, wall)
    reverse = cavity_base_run(model, replace(wall, axis=tuple(reversed(wall.axis))))
    assert reverse.end - reverse.start == pytest.approx(forward.end - forward.start)
    assert reverse.depth_m == pytest.approx(forward.depth_m)
    assert reverse.outward == pytest.approx(forward.outward)


@pytest.mark.parametrize("product", ["RAINSCREEN_BASE_Z", "EPDM_BASE_ISOLATION"])
def test_base_cavity_grade_detects_missing_and_displaced_parts(catlin_model_ro, product):
    model = copy(catlin_model_ro)
    target = next(s for s in model.solids if s.host_ref == "W-M-W4" and s.product == product)
    model.solids = [s for s in model.solids if not (s.host_ref == "W-M-W4"
                                                     and s.product == product)]
    assert _failing(model, "_base", "W-M-W4")
    mesh = replace(target.body_mesh, positions=tuple((x, y, z + inch(2).meters)
                                                    for x, y, z in target.body_mesh.positions))
    model.solids = [s for s in catlin_model_ro.solids if s is not target]
    model.solids.append(replace(target, body_mesh=mesh))
    assert _failing(model, "_base", "W-M-W4")
