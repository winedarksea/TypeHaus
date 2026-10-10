"""Derived base and door casing (→ resolve/interior_trim.py, decision #85).

The synthetic cases mutate the starter house, whose upper storey is two rooms either side of
one cased interior door and whose main storey has one exterior door. The catlin cases pin
the expected findings the plan named for the owner to triage.
"""

from __future__ import annotations

import pytest
from shapely.geometry import Polygon

from typehaus.model import Furniture, FurnitureType, Material, TrimStandard, WallPaneling
from typehaus.quantities import inch, m, pt
from typehaus.resolve.pipeline import resolve
from typehaus.source.loader import load_plan

IN = 0.0254


@pytest.fixture(scope="module")
def starter(starter_dir):
    return load_plan(starter_dir).plan


def _resolved(plan):
    model, findings = resolve(plan)
    return model, findings


def _swap(plan, tag, **update):
    for storey, items in plan.elements.items():
        if any(el.tag == tag for el in items):
            return plan.with_elements(storey, [el.model_copy(update=update) if el.tag == tag
                                               else el for el in items])
    raise KeyError(tag)


def _add(plan, storey, *items):
    return plan.with_elements(storey, [*plan.storey_elements(storey), *items])


def _library(plan, **update):
    return plan.model_copy(update={"library": plan.library.model_copy(update=update)})


def _standard(plan):
    return next(el for el in plan.all_elements() if isinstance(el, TrimStandard))


def _along(wall, point) -> float:
    (x0, y0), (x1, y1) = wall.axis
    length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    return ((point[0] - x0) * (x1 - x0) + (point[1] - y0) * (y1 - y0)) / length


# --- the model ------------------------------------------------------------------------------

def test_trim_standard_is_a_registered_element_and_base_detail_a_material_field() -> None:
    from typehaus.model import element_kinds
    from typehaus.model.registry import constructor_names

    assert "TrimStandard" in element_kinds() and "TrimStandard" in constructor_names()
    assert Material(tag="t", name="t", base_detail="tile").base_detail == "tile"
    with pytest.raises(ValueError):
        Material(tag="t", name="t", base_detail="skirting")


# --- the starter: the default derivation ---------------------------------------------------

def test_a_cased_interior_door_gets_a_frame_on_both_faces(starter) -> None:
    model, _ = _resolved(starter)
    s = _standard(starter)
    casings = [c for c in model.door_casings if c.opening_ref == "D-201"]
    assert {c.room for c in casings} == {"RM-Upper", "RM-Upper-Hall"}
    opening = next(o for o in model.openings if o.tag == "D-201")
    wall = next(w for w in model.walls if w.tag == opening.host_wall)
    inner = opening.width_m / 2 - s.jamb_allowance.meters + s.reveal.meters
    head_z = (wall.base_ref_z_m + opening.sill_m + opening.height_m
              - s.jamb_allowance.meters + s.reveal.meters)
    for casing in casings:
        pieces = {p.name: p for p in casing.pieces}
        assert set(pieces) == {"leg_left", "leg_right", "head"}
        for name in ("leg_left", "leg_right"):
            leg = pieces[name]
            stations = sorted(abs(_along(wall, p) - opening.center_along_m)
                              for p in leg.outline)
            assert stations[0] == pytest.approx(inner, abs=1e-6)
            assert stations[-1] == pytest.approx(inner + s.casing_width.meters, abs=1e-6)
            assert leg.z1_m == pytest.approx(head_z)
        head = pieces["head"]
        assert head.z0_m == pytest.approx(head_z)
        assert head.length_m == pytest.approx(2 * (inner + s.casing_width.meters))
        # Flush, butt-jointed: the head sits ON the legs, never beside or behind them.
        assert Polygon(head.outline).area == pytest.approx(
            head.length_m * s.thickness.meters, rel=1e-6)


def test_an_exterior_door_is_cased_on_its_finished_face_only(starter) -> None:
    model, _ = _resolved(starter)
    casings = [c for c in model.door_casings if c.opening_ref == "D-101"]
    assert [c.room for c in casings] == ["RM-Main"]


def test_base_dies_into_the_casing_and_never_runs_through_it(starter) -> None:
    model, _ = _resolved(starter)
    legs = [(c.storey, Polygon(p.outline)) for c in model.door_casings for p in c.pieces
            if p.name.startswith("leg")]
    runs = [r for r in model.base_runs if r.kind == "trim"]
    assert runs
    for run in runs:
        board = Polygon(run.piece.outline)
        assert all(board.intersection(leg).area < 1e-9 for storey, leg in legs
                   if storey == run.storey), run.tag
    # ... and meets it: some base piece ends exactly at a leg's outer edge.
    touching = [r for r in runs if "D-201" in r.breaks]
    assert len(touching) == 4
    for run in touching:
        assert min(Polygon(run.piece.outline).distance(leg) for storey, leg in legs
                   if storey == run.storey) < 1e-6
    # The corners close: every piece of a closed wall-to-wall run meets its neighbours.
    main = [r for r in runs if r.room == "RM-Main"]
    assert sum(1 for r in main if r.end_corner) == 4


def test_base_sits_on_the_finished_floor_at_the_standard_height(starter) -> None:
    from typehaus.resolve.room_floor import room_finished_floor_elevation

    model, _ = _resolved(starter)
    s = _standard(starter)
    rooms = {r.tag: r for r in model.rooms}
    for run in model.base_runs:
        floor = room_finished_floor_elevation(model, rooms[run.room])
        assert run.piece.z0_m == pytest.approx(floor)
        assert run.piece.z1_m - run.piece.z0_m == pytest.approx(s.base_height.meters)
        assert run.uid.startswith(f"{rooms[run.room].uid}-base-")


# --- the switches --------------------------------------------------------------------------

def test_a_trimless_door_takes_no_casing_and_breaks_the_base_at_its_ro(starter) -> None:
    door = next(dt for dt in starter.library.door_types if dt.tag == "DT-INT-SWING32")
    trimless = door.model_copy(update={"tag": "DT-T", "trimless": True})
    plan = _swap(_library(starter, door_types=(*starter.library.door_types, trimless)),
                 "D-201", type_ref="DT-T")
    model, _ = _resolved(plan)
    assert not [c for c in model.door_casings if c.opening_ref == "D-201"]
    opening = next(o for o in model.openings if o.tag == "D-201")
    wall = next(w for w in model.walls if w.tag == opening.host_wall)
    ends = [abs(_along(wall, point) - opening.center_along_m)
            for run in model.base_runs if "D-201" in run.breaks
            for point in run.piece.outline]
    assert ends and min(ends) == pytest.approx(opening.width_m / 2, abs=1e-6)


def test_an_excluded_room_takes_no_base_and_no_casing(starter) -> None:
    s = _standard(starter)
    plan = _swap(starter, s.tag, excluded_rooms=("RM-Upper",))
    model, findings = _resolved(plan)
    assert not [f for f in findings if f.check_id == "integrity.trim_standard"]
    assert {r.room for r in model.base_runs} == {"RM-Main", "RM-Upper-Hall"}
    assert {c.room for c in model.door_casings if c.opening_ref == "D-201"} == {
        "RM-Upper-Hall"}


def test_two_standards_are_an_error_not_a_winner(starter) -> None:
    second = _standard(starter).model_copy(update={"uid": "TRIM2AAAAA", "tag": "TRIM-2"})
    model, findings = _resolved(_add(starter, "main", second))
    assert any(f.check_id == "integrity.trim_standard" and f.severity.value == "error"
               for f in findings)
    assert not model.base_runs and not model.door_casings


def test_the_floor_material_decides_the_base_kind(starter) -> None:
    from typehaus.resolve.geometry_millwork import base_run_prisms
    from typehaus.takeoff.interior_trim import interior_trim_takeoff

    tile = Material(tag="t-tile", name="tile", base_detail="tile", finish_thickness_in=0.5)
    plan = _swap(_library(starter, materials=(*starter.library.materials, tile)),
                 "RM-Upper", floor_finish="t-tile")
    model, _ = _resolved(plan)
    upper = [r for r in model.base_runs if r.room == "RM-Upper"]
    assert upper and {r.kind for r in upper} == {"tile"}
    assert {r.material_ref for r in upper} == {"t-tile"}
    assert all(base_run_prisms(r) == [] for r in upper)  # a tile base is not a board
    rows = [r for r in interior_trim_takeoff(model) if r["room"] == "RM-Upper"
            and r["kind"] == "tile base"]
    assert rows and rows[0]["item"] == "tile-base"


def test_a_wood_band_carries_the_base_and_a_tile_band_breaks_it(starter) -> None:
    wood = Material(tag="t-pine", name="pine shiplap", species="pine", nominal_quarters=4)
    tile = Material(tag="t-wall-tile", name="wall tile")
    lib = _library(starter, materials=(*starter.library.materials, wood, tile))

    def band(material: str):
        return WallPaneling(uid="WPTESTAAAA", tag="WP-TEST", room="RM-Upper",
                            material_ref=material, height=inch(36), walls=("W-202",))

    model, _ = _resolved(_add(lib, "upper", band("t-pine")))
    on_band = [r for r in model.base_runs if r.room == "RM-Upper" and r.wall_tag == "W-202"]
    assert on_band and all(r.offset_m == pytest.approx(0.75 * IN) for r in on_band)
    model, _ = _resolved(_add(lib, "upper", band("t-wall-tile")))
    assert not [r for r in model.base_runs if r.room == "RM-Upper" and r.wall_tag == "W-202"]


def test_a_cabinet_beside_the_door_scribes_the_leg_and_says_so(starter) -> None:
    from _helpers import check_context

    from typehaus.checks.advisory.interior_trim import casing_clipped

    model, _ = _resolved(starter)
    casing = next(c for c in model.door_casings
                  if c.opening_ref == "D-201" and c.room == "RM-Upper")
    leg = max((p for p in casing.pieces if p.name.startswith("leg")),
              key=lambda p: min(y for _x, y in p.outline))
    face_x = min(x for x, _y in leg.outline)
    inner_y = min(y for _x, y in leg.outline)
    # A 24" base cabinet whose end stands 2 1/2" past the leg's inner edge.
    cab = FurnitureType(tag="FT-T-BASE", name="base cabinet", footprint=(inch(24), inch(24)),
                        height=inch(34.5), work_surface=True)
    item = Furniture(uid="FUTESTAAAA", tag="FURN-T-BASE", type_ref="FT-T-BASE",
                     room="RM-Upper",
                     position=pt(m(face_x + 12.01 * IN), m(inner_y + 2.5 * IN + 12 * IN)))
    plan = _add(_library(starter, furniture_types=(*starter.library.furniture_types, cab)),
                "upper", item)
    model, _ = _resolved(plan)
    casing = next(c for c in model.door_casings
                  if c.opening_ref == "D-201" and c.room == "RM-Upper")
    assert [(k.obstruction, k.dropped) for k in casing.clips] == [("FURN-T-BASE", False)]
    assert casing.clips[0].remaining_m == pytest.approx(2.5 * IN, abs=0.002)
    leg = next(p for p in casing.pieces if p.name == casing.clips[0].piece)
    assert leg.width_m == pytest.approx(casing.clips[0].remaining_m)
    findings = casing_clipped(check_context(plan, model))
    assert any("FURN-T-BASE" in f.message and "scribed" in f.message for f in findings)
    # The base stops at the cabinet as well as at the casing.
    board = Polygon(next(o for o in model.canvas_objects if o.tag == "FURN-T-BASE").footprint)
    assert all(Polygon(r.piece.outline).intersection(board).area < 1e-9
               for r in model.base_runs)


def test_procurement_is_the_material(starter) -> None:
    """Bought stock bills by the LF and is not the sawyer's; milled stock is both."""
    from typehaus.takeoff.hardwood import hardwood_takeoff
    from typehaus.takeoff.interior_trim import interior_trim_takeoff

    model, _ = _resolved(starter)
    assert {r["item"] for r in interior_trim_takeoff(model)} == {"poplar-trim-paint"}
    assert not [r for r in hardwood_takeoff(model)
                if r["use"] in ("baseboard", "door casing")]
    milled = Material(tag="t-oak", name="oak trim", species="oak", nominal_quarters=4,
                      milling_profile="S4S", requires_custom_milling=True)
    plan = _swap(_library(starter, materials=(*starter.library.materials, milled)),
                 "TRIM-STANDARD", material_ref="t-oak")
    model, _ = _resolved(plan)
    rows = [r for r in hardwood_takeoff(model) if r["use"] in ("baseboard", "door casing")]
    assert {r["use"] for r in rows} == {"baseboard", "door casing"}
    assert all(r["also_in_interior_trim"] and r["material"] == "t-oak" for r in rows)
    base = next(r for r in rows if r["use"] == "baseboard")
    total_ft = sum(r.length_m for r in model.base_runs) / 0.3048
    assert base["total_length_ft"] == pytest.approx(total_ft, abs=0.1)
    assert base["pieces"] * base["finished_length_in"] >= total_ft * 12 - 1e-6


def test_the_takeoff_reconciles_to_the_records(starter) -> None:
    from typehaus.takeoff.interior_trim import interior_trim_takeoff

    model, _ = _resolved(starter)
    rows = interior_trim_takeoff(model)
    base = sum(r["length_ft"] for r in rows if r["kind"] == "baseboard")
    casing = sum(r["length_ft"] for r in rows if r["kind"] == "door casing")
    assert base == pytest.approx(sum(r.length_m for r in model.base_runs) / 0.3048, abs=0.05)
    assert casing == pytest.approx(sum(p.length_m for c in model.door_casings
                                       for p in c.pieces) / 0.3048, abs=0.05)
    # Each corner counted once: by the piece arriving at it.
    assert sum(r["inside_corners"] + r["outside_corners"] for r in rows) == sum(
        1 for run in model.base_runs if run.end_corner)


# --- catlin: what the plan said to expect ---------------------------------------------------

def test_catlin_trimless_bookcase_and_overhead_doors_take_no_casing(catlin_model_ro) -> None:
    cased = {c.opening_ref for c in catlin_model_ro.door_casings}
    assert cased.isdisjoint({"D-M-STUDY", "D-M-BED2", "D-A-STUDY", "D-G-OVERHEAD"})
    # An exterior door is cased on its room face only.
    for door in ("D-M-ENTRY", "D-M-BALC", "D-S-DECK-E"):
        assert len([c for c in catlin_model_ro.door_casings if c.opening_ref == door]) == 1


def test_catlin_base_scope_follows_the_standard_and_the_floor(catlin_model_ro) -> None:
    rooms = {r.room for r in catlin_model_ro.base_runs}
    assert "RM-B-STAIR" in rooms
    assert rooms.isdisjoint({"RM-B-FURNACE", "RM-B-ESS", "RM-B-WORKSHOP", "RM-B-GYM",
                             "RM-B-SAUNA", "RM-S-PLANT", "RM-GARAGE", "RM-A-POCKET",
                             "RM-A-EAST-UNFIN"})
    kinds = {r.room: r.kind for r in catlin_model_ro.base_runs}
    assert kinds["RM-M-BATH2"] == "tile" and kinds["RM-S-SUITEBATH"] == "tile"
    assert kinds["RM-B-BATH"] == "integral_cove" and kinds["RM-A-STUDIO"] == "integral_cove"
    assert kinds["RM-S-HALL"] == "trim"


def test_catlin_expected_clips(catlin_model_ro) -> None:
    clips = {(c.opening_ref, c.room): {(k.obstruction, k.dropped) for k in c.clips}
             for c in catlin_model_ro.door_casings if c.clips}
    assert clips[("D-S-BED1", "RM-S-BED1")] == {("FURN-S-BED1-PAX-SHELF", False)}
    assert clips[("D-S-BED2", "RM-S-BED2")] == {("FURN-S-BED2-PAX-SHELF", False)}
    assert ("FX-M-BATH2-SINK", True) in clips[("D-M-BATH2", "RM-M-BATH2")]


def test_catlin_base_stops_at_the_bare_faces(catlin_model_ro) -> None:
    """The fireplace brick and the mudroom's exposed studs take no base."""
    walls = {r.wall_tag for r in catlin_model_ro.base_runs}
    assert not {w for w in walls if w.startswith("W-M-FIRE-")}
    assert not [r for r in catlin_model_ro.base_runs
                if r.wall_tag == "W-M-STRW2" and r.room == "RM-M-MUDROOM"]
