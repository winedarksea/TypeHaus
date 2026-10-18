"""Fit, occupied space and service access for Catlin's two independent sauna levels."""

from pathlib import Path

import pytest
from shapely.geometry import LineString, MultiPoint, Point, Polygon, box

from typehaus.cli.price_file import load_prices
from typehaus.emit.draw.detail_components.sauna_seating import sauna_benches
from typehaus.model.placeable_symbols import place_local, symbol_geometry
from typehaus.model.placeable_symbols._sauna_recliner import (
    BACK_LENGTH_IN,
    LEG_LENGTH_IN,
    LOCKING_BACK_ANGLES_DEG,
    MATTRESS_THICKNESS_IN,
    REFERENCE_DEPTH_IN,
    SEAT_LENGTH_IN,
    WOOD_THICKNESS_IN,
    _geometry,
    profile_height_in,
)
from typehaus.quantities import M_PER_IN
from typehaus.takeoff.lighting import PSU_SIZING_FACTOR
from typehaus.takeoff.placeables import placeables_takeoff

HOUSE = Path(__file__).resolve().parents[3] / "houses" / "catlin"
BASE_TAGS = ("UPPER", "LOWER", "READING", "STEP")


def _object(model, suffix):
    return next(o for o in model.canvas_objects if o.tag == "FURN-B-SAUNA-" + suffix)


def _footprint(obj):
    return Polygon([(x / M_PER_IN, y / M_PER_IN) for x, y in obj.footprint])


def _floor(model):
    return next(s.z1_m for s in model.solids if s.tag == "SL-B-FLOOR")


def _parts(model, obj):
    catalog = next(t for t in model.plan.library.furniture_types if t.tag == obj.type_ref)
    return symbol_geometry(
        catalog.plan_symbol, *(d.meters for d in catalog.footprint), obj.body_z1_m - obj.body_z0_m
    )[1]


def test_platforms_fit_without_fixture_collisions(catlin_model_ro):
    model = catlin_model_ro
    room = next(r for r in model.rooms if r.tag == "RM-B-SAUNA")
    clear = Polygon(room.clear_face).buffer(1e-6)
    platforms = [_object(model, tag) for tag in BASE_TAGS]
    fixtures = [
        o
        for o in model.canvas_objects
        if o.tag in {"FX-B-SAUNA-SH", "EQ-B-SAUNA-HTR", "ED-B-SAUNA-JB"}
    ]
    for obj in platforms + [_object(model, "RECLINER"), _object(model, "MATTRESS")]:
        assert clear.covers(Polygon(obj.footprint)), obj.tag
        for fixture in fixtures:
            assert _footprint(obj).intersection(_footprint(fixture)).area < 1e-8
    for index, obj in enumerate(platforms):
        for other in platforms[index + 1 :]:
            assert _footprint(obj).intersection(_footprint(other)).area < 1e-8
    upper, lower, reading, step = platforms
    assert _footprint(upper).bounds == pytest.approx((123.25, 38.1875, 151.25, 116.1875))
    assert 209.75 - _footprint(step).bounds[2] == pytest.approx(24.5)
    assert 209.75 - _footprint(reading).bounds[2] == pytest.approx(28)
    heater = next(o for o in fixtures if o.tag == "EQ-B-SAUNA-HTR")
    junction = next(o for o in fixtures if o.tag == "ED-B-SAUNA-JB")
    assert _footprint(reading).distance(_footprint(heater)) == pytest.approx(10.5)
    assert _footprint(reading).distance(_footprint(junction)) == pytest.approx(4)
    # US HPCS11U1H listing: 1.2" side/back, 4" front, 32.5" above; 78" room minimum.
    assert 209.75 - _footprint(heater).bounds[2] >= 1.2
    assert _footprint(heater).bounds[1] - 9.5 >= 1.2
    ceiling = next(c for c in model.ceilings if c.room_ref == room.tag)
    assert (ceiling.z0_m - heater.body_z1_m) / M_PER_IN >= 32.5
    assert (ceiling.z0_m - _floor(model)) / M_PER_IN >= 78


def test_lying_surface_and_finished_headroom(catlin_model_ro):
    model = catlin_model_ro
    upper = _object(model, "UPPER")
    floor = _floor(model)
    ceiling = next(c for c in model.ceilings if c.room_ref == "RM-B-SAUNA")
    assert (upper.body_z1_m - floor) / M_PER_IN == pytest.approx(42)
    assert (ceiling.z0_m - upper.body_z1_m) / M_PER_IN == pytest.approx(41.0625)
    assert _footprint(upper).covers(box(124.25, 43.1875, 150.25, 111.1875))  # 26 x 68
    for tag, height in (("LOWER", 24), ("READING", 24), ("STEP", 12)):
        assert (_object(model, tag).body_z1_m - floor) / M_PER_IN == pytest.approx(height)


def test_four_people_include_seats_legs_and_access(catlin_model_ro):
    model = catlin_model_ro
    upper, lower, reading = (
        _footprint(_object(model, tag)) for tag in ("UPPER", "LOWER", "READING")
    )
    envelopes = []
    for south in (38.1875, 64.1875, 90.1875):
        seat, feet = box(133.25, south, 151.25, south + 26), box(151.25, south, 171.25, south + 26)
        assert upper.buffer(1e-8).covers(seat)
        assert lower.buffer(1e-8).covers(feet)
        envelopes.append(seat.union(feet))
    # Remove recliner/pad: fourth bather sits below, at the west end of the south deck.
    seat, feet = box(123.75, 11, 145.75, 37), box(145.75, 11, 167.75, 37)
    assert reading.covers(seat.union(feet))
    envelopes.append(seat.union(feet))
    for index, occupied in enumerate(envelopes):
        for other in envelopes[index + 1 :]:
            assert occupied.intersection(other).area == 0
        assert occupied.intersection(box(185.25, 38, 209.75, 80.1875)).area == 0


def test_removable_decks_preserve_drain_and_exhaust(catlin_model_ro):
    model = catlin_model_ro
    protected = [o for o in model.canvas_objects if o.tag in {"FX-B-SAUNA-FD", "REG-B-EXH2"}]
    for suffix in BASE_TAGS:
        obj = _object(model, suffix)
        for part in _parts(model, obj):
            center, size = part["center"], part["size"]
            z0 = obj.body_z0_m + center[2] - size[2] / 2
            z1 = z0 + size[2]
            corners = [
                (center[0] + dx * size[0] / 2, center[1] + dy * size[1] / 2)
                for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))
            ]
            frame = Polygon(place_local(corners, obj.position, obj.rotation_degrees))
            for fixture in protected:
                if z0 < fixture.body_z1_m and z1 > fixture.body_z0_m:
                    assert frame.intersection(Polygon(fixture.footprint)).area < 1e-10
    drain = next(o for o in protected if o.tag == "FX-B-SAUNA-FD")
    assert _footprint(_object(model, "LOWER")).covers(_footprint(drain))
    cleanout = next(c for c in model.drain_cleanouts if c.tag == "CO-B-SAUNA-HEAD")
    cap = tuple(v / M_PER_IN for v in cleanout.cap_position)
    assert cap == pytest.approx((181, 60))
    extension = next(s for s in model.solids if s.tag == "CO-B-SAUNA-HEAD-EXT")
    assert extension.z1_m <= cleanout.cap_z_m + 1e-8
    assert extension.sweep.path[-1][:2] == cleanout.cap_position
    assert extension.sweep.path[-2][:2] == cleanout.cap_position
    access = box(cap[0] - 9, cap[1] - 9, cap[0] + 9, cap[1] + 9)
    for suffix in BASE_TAGS:
        assert access.intersection(_footprint(_object(model, suffix))).area == 0
    assert Point(cap).within(access)


def test_condensate_outlets_land_over_grate_and_clear_joinery(catlin_model_ro):
    model = catlin_model_ro
    drain = next(o for o in model.canvas_objects if o.tag == "FX-B-SAUNA-FD")
    # PR-B-ERV-COND drains to FX-B-BATH-LAV since 2026-10-17 (test_plumbing_pass.py).
    runs = [r for r in model.pipe_runs if r.tag == "PR-B-COND"]
    assert len(runs) == 1
    for run in runs:
        radius = run.diameter_m / 2
        assert Polygon(drain.footprint).covers(Point(run.path[-1]).buffer(radius))
        assert (run.z_m[-1] - _floor(model)) / M_PER_IN == pytest.approx(9)
        for suffix in BASE_TAGS:
            obj = _object(model, suffix)
            for part in _parts(model, obj):
                center, size = part["center"], part["size"]
                ring = [
                    (center[0] + dx * size[0] / 2, center[1] + dy * size[1] / 2)
                    for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))
                ]
                frame = Polygon(place_local(ring, obj.position, obj.rotation_degrees))
                bottom = obj.body_z0_m + center[2] - size[2] / 2
                top = bottom + size[2]
                for index, (a, b) in enumerate(zip(run.path, run.path[1:], strict=False)):
                    low, high = sorted(run.z_m[index : index + 2])
                    if low - radius >= top or high + radius <= bottom:
                        continue
                    axis = Point(a) if a == b else LineString((a, b))
                    assert frame.intersection(axis.buffer(radius)).area < 1e-10, (
                        obj.tag,
                        run.tag,
                        index,
                    )


def test_all_wood_members_connect_to_the_support_frame(catlin_model_ro):
    # These members are x extrusions of convex y/z profiles, so this contact test uses
    # real inclined faces; their overlapping bounding boxes would hide floating slats.
    for suffix in (*BASE_TAGS, "RECLINER"):
        parts = _parts(catlin_model_ro, _object(catlin_model_ro, suffix))
        profiles = []
        for part in parts:
            center, size = part["center"], part["size"]
            yz = (
                MultiPoint([(y, z) for _, y, z in part["mesh"]["positions"]]).convex_hull
                if "mesh" in part
                else box(
                    center[1] - size[1] / 2,
                    center[2] - size[2] / 2,
                    center[1] + size[1] / 2,
                    center[2] + size[2] / 2,
                )
            )
            profiles.append((center[0] - size[0] / 2, center[0] + size[0] / 2, yz))
        connected = {0}
        while True:
            adjacent = {
                i
                for i, (lo, hi, yz) in enumerate(profiles)
                if i not in connected
                and any(
                    max(lo, profiles[j][0]) <= min(hi, profiles[j][1]) + 1e-8
                    and yz.distance(profiles[j][2]) < 1e-8
                    for j in connected
                )
            }
            if not adjacent:
                break
            connected.update(adjacent)
        assert len(connected) == len(parts), suffix


def test_recliner_and_thick_pad_share_profile_and_mount(catlin_model_ro):
    model = catlin_model_ro
    wood, pad = (_object(model, tag) for tag in ("RECLINER", "MATTRESS"))
    assert wood.position == pad.position and wood.rotation_degrees == pad.rotation_degrees == 90
    assert wood.body_z0_m == pad.body_z0_m == pytest.approx(_object(model, "READING").body_z1_m)
    assert BACK_LENGTH_IN + SEAT_LENGTH_IN + LEG_LENGTH_IN == 80
    assert MATTRESS_THICKNESS_IN == 4
    for angle in LOCKING_BACK_ANGLES_DEG:
        for mattress in (False, True):
            _, parts = _geometry(
                26 * M_PER_IN,
                REFERENCE_DEPTH_IN * M_PER_IN,
                profile_height_in(mattress=mattress, angle_degrees=angle) * M_PER_IN,
                mattress=mattress,
                angle_degrees=angle,
            )
            for part in parts:
                cy, depth = part["center"][1], part["size"][1]
                assert abs(cy) + depth / 2 <= REFERENCE_DEPTH_IN * M_PER_IN / 2 + 1e-8
    wood_parts, pad_parts = _parts(model, wood), _parts(model, pad)
    for part in wood_parts + pad_parts:
        if "mesh" not in part:
            continue
        for point, normal in zip(part["mesh"]["positions"], part["mesh"]["normals"], strict=True):
            assert sum((point[i] - part["center"][i]) * normal[i] for i in range(3)) > 0
    # Horizontal seat/leg surfaces meet the pad at 1.5" and have its 4" normal thickness.
    horizontal = [
        part
        for part in pad_parts
        if "mesh" in part and part["size"][2] / M_PER_IN == pytest.approx(4)
    ]
    assert len(horizontal) == 2
    for part in horizontal:
        assert (part["center"][2] - part["size"][2] / 2) / M_PER_IN == pytest.approx(
            WOOD_THICKNESS_IN
        )
    assert wood_parts
    sections = [
        MultiPoint([(y, z) for _, y, z in part["mesh"]["positions"]]).convex_hull
        for part in pad_parts
        if part["color"] == "mattress"
    ]
    for a, b in zip(sections, sections[1:], strict=False):
        assert a.intersection(b).area < 1e-10  # filling meets at the hinge without overlap
        assert a.distance(b) < 1e-8
    pad_type = next(t for t in model.plan.library.furniture_types if t.tag == pad.type_ref)
    strokes, parts = symbol_geometry(
        pad_type.plan_symbol, *(d.meters for d in pad_type.footprint), pad.body_z1_m - pad.body_z0_m
    )
    for stroke, part in zip(strokes, parts, strict=True):
        projection = MultiPoint([(x, y) for x, y, _ in part["mesh"]["positions"]]).convex_hull
        assert Polygon(stroke["points"]).symmetric_difference(projection).area < 1e-10
    for obj in (wood, pad):
        assert _footprint(_object(model, "READING")).covers(_footprint(obj))


def test_sections_cut_placed_recliner_and_mattress(catlin_model_ro):
    model = catlin_model_ro
    nodes = sauna_benches(model, "x", 24 * M_PER_IN)
    for suffix in ("READING", "RECLINER", "MATTRESS"):
        obj = _object(model, suffix)
        cut = [n for n in nodes if n.node == "polyline" and n.uid == obj.uid]
        assert cut
        assert max(z for n in cut for _, z in n.points) == pytest.approx(
            obj.body_z1_m / M_PER_IN, abs=0.125
        )
    pad_nodes = [
        n for n in nodes if n.node == "polyline" and n.tag == "detail-component:sauna-mattress"
    ]
    assert any(len({round(z, 6) for _, z in n.points}) >= 4 for n in pad_nodes)
    assert sauna_benches(model, "x", 200 * M_PER_IN) == []


def test_underbench_tape_is_attached_and_driver_has_capacity(catlin_model_ro):
    model = catlin_model_ro
    runs = [r for r in model.light_runs if r.room == "RM-B-SAUNA"]
    edge = _footprint(_object(model, "LOWER")).boundary.union(
        _footprint(_object(model, "READING")).boundary
    )
    for run in runs:
        assert (run.z_m - _floor(model)) / M_PER_IN == pytest.approx(16)
        for a, b in zip(run.path, run.path[1:], strict=False):
            midpoint = Point((a[0] + b[0]) / (2 * M_PER_IN), (a[1] + b[1]) / (2 * M_PER_IN))
            assert edge.distance(midpoint) < 1e-7
            attached = False
            for suffix in ("LOWER", "READING"):
                obj = _object(model, suffix)
                for part in _parts(model, obj):
                    center, size = part["center"], part["size"]
                    if not (
                        obj.body_z0_m + center[2] - size[2] / 2
                        <= run.z_m + 1e-8
                        <= obj.body_z0_m + center[2] + size[2] / 2 + 1e-8
                    ):
                        continue
                    ring = [
                        (center[0] + dx * size[0] / 2, center[1] + dy * size[1] / 2)
                        for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))
                    ]
                    face = Polygon(
                        [
                            (x / M_PER_IN, y / M_PER_IN)
                            for x, y in place_local(ring, obj.position, obj.rotation_degrees)
                        ]
                    )
                    attached |= face.buffer(1e-8).covers(midpoint)
            assert attached, run.tag
        assert run.psu_ref == "ED-B-SAUNA-LT-PSU"
    tape_types = {t.tag: t for t in model.plan.library.electrical_device_types}
    watts = sum(r.length_m / M_PER_IN / 12 * tape_types[r.type_ref].watts_per_ft for r in runs)
    assert watts == pytest.approx(29.171875)
    driver = next(
        t for t in model.plan.library.electrical_device_types if t.tag == "ED-T-LT-PSU-60"
    )
    assert watts * PSU_SIZING_FACTOR <= driver.load_va * 0.8


def test_all_custom_seating_is_counted_and_priced_once(catlin_model_ro, catlin_plan):
    types = {
        t.tag for t in catlin_plan.library.furniture_types if t.tag.startswith("FT-CATLIN-SAUNA-")
    }
    assert len(types) == 6
    rows = {r["type"]: r for r in placeables_takeoff(catlin_model_ro)}
    prices = load_prices(HOUSE)
    for tag in types:
        assert rows[tag]["count"] == 1
        assert tag in prices.placeables
