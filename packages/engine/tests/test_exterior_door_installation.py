"""Door anchorage, deep reveals and one-sided floor coordination."""
from dataclasses import replace
from types import SimpleNamespace as NS

import pytest
from shapely.geometry import Point, Polygon

from typehaus.model import DoorwayProductSpec, DoorwaySectionPart, ExteriorDoorInstallation
from typehaus.resolve.doorway import DoorwayAssembly, doorway_json
from typehaus.resolve.doorway_floors import extend_doorway_finishes
from typehaus.resolve.doorway_framing import clear_doorway_sole_plates
from typehaus.resolve.exterior_door import exterior_landing
from typehaus.resolve.geometry import opening_center, wall_frame
from typehaus.resolve.geometry_openings import opening_parts
from typehaus.resolve.opening_flashing import opening_flashing_frame, opening_flashing_meshes
from typehaus.resolve.walking_surface import FloorSurface
from typehaus.takeoff.doors import door_hardware_rows, door_installation_rows
from typehaus.takeoff.interior_trim import interior_trim_takeoff


@pytest.mark.parametrize("tag", ["D-M-ENTRY", "D-M-BALC", "D-S-DECK-E"])
def test_catlin_doors_have_structural_mount_and_independent_returns(catlin_model_ro, tag):
    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == tag)
    wall = model.wall(opening.host_wall)
    assembly = opening.doorway
    placement = assembly.exterior_placement
    assert placement.specification.mounting == "structural_wall"
    assert all(f is not None and f.surface_m is not None for f in assembly.adjacent_floors)
    assert assembly.adjacent_floors[0].room_tag is None
    assert placement.frame_outer_m != placement.frame_inner_m
    wood_boards = [b for b in placement.boards if b.role == "door_installation"]
    assert len([b for b in wood_boards if b.name.startswith("exterior-return")]) == 3
    assert len([b for b in wood_boards if b.name.startswith("exterior-casing")]) == 3
    assert all(b.height_m > 0 and b.depth_m > 0 for b in placement.boards)
    parts = opening_parts(wall, opening, next(t.operation for t in model.plan.library.door_types
                                            if t.tag == opening.type_ref),
                          is_glazed=tag != "D-M-ENTRY")
    origin, tangent, normal, _ = wall_frame(wall)
    for part in parts:
        if part.key != "frame":
            continue
        offsets = [sum((p[i] - origin[i]) * normal[i] for i in (0, 1))
                   for s in part.solids for p in s.ring]
        assert min(offsets) == pytest.approx(min(placement.frame_inner_m, placement.frame_outer_m))
        assert max(offsets) == pytest.approx(max(placement.frame_inner_m, placement.frame_outer_m))
    center = opening_center(wall, opening)
    for member in wall.members:
        if not member.child_key.startswith("plate-bottom"):
            continue
        ends = [sum((p[i] - origin[i]) * tangent[i] for i in (0, 1))
                for p in (member.p0, member.p1)]
        assert min(max(ends), opening.center_along_m + opening.width_m / 2) <= max(
            min(ends), opening.center_along_m - opening.width_m / 2) + .001
    floor = assembly.adjacent_floors[1]
    room = next(r for r in model.rooms if r.tag == floor.room_tag)
    point = tuple(center[i] + normal[i] * (placement.frame_inner_m + .002) for i in (0, 1))
    assert any(Polygon(outline, holes=list(holes)).covers(Point(point))
               for outline, holes in room.field_finish)
    frame = opening_flashing_frame(model, wall, opening)
    assert frame.back < placement.outward_sign * placement.frame_inner_m
    head = next(mesh for key, _, _, mesh in opening_flashing_meshes(wall, opening, frame)
                if key == "head")
    assert max(z for _, _, z in head.positions) > assembly.rough_opening_z_m + opening.height_m
    rows = [r for r in door_installation_rows(model) if tag in r.get("tags", [])]
    lumber_rows = [r for r in rows if r["cut_pieces"]]
    assert len(lumber_rows) == len(wood_boards)
    assert all(r["cut_pieces"][0]["thickness_in"] == pytest.approx(.75) for r in lumber_rows)
    trim = [r for r in interior_trim_takeoff(model)
            if tag in r["tags"] and "painted site-built board" in r["description"]]
    assert lumber_rows == trim
    assert not any(r["scope"] == "exterior door installation trim"
                   for r in door_hardware_rows(model))


@pytest.mark.parametrize("known_side", [0, 1])
def test_one_known_floor_clears_obstructing_plate_but_keeps_support(known_side):
    from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedOpening, ResolvedWall

    plate = FramedMember("wall", "plate-bottom", "plate", "2x6", (0, 0), (4, 0), 0, .0381, 4)
    mudsill = replace(plate, child_key="mudsill", z0_m=-.05, z1_m=0)
    raised = replace(plate, child_key="sill-0", z0_m=.5, z1_m=.54)
    wall = ResolvedWall("wall", "W", "main", "A", ((0, 0), (4, 0)), (), 0, 3,
                        members=(plate, mudsill, raised))
    floors = [None, None]
    floors[known_side] = FloorSurface("slab", 0, "room", "plank", .25)
    assembly = DoorwayAssembly(0, tuple(floors), "transition", 0)
    opening = ResolvedOpening("door", "D", "W", None, .9, 2.1, 0, 2, "door", True,
                              doorway=assembly)
    model = ResolvedModel(NS(), walls=[wall], openings=[opening])
    clear_doorway_sole_plates(model)
    assert len([p for p in model.walls[0].members if p.child_key.startswith("plate-bottom")]) == 2
    assert mudsill in model.walls[0].members and raised in model.walls[0].members
    model.walls = [wall]
    model.openings = [replace(opening, doorway=replace(assembly, rough_opening_z_m=.6))]
    clear_doorway_sole_plates(model)
    assert model.walls[0].members == wall.members


def test_documented_design_geometry_does_not_require_order_confirmation():
    spec = DoorwayProductSpec(product_ref="TEST", variant="documented test section", role="sill",
        source_url="https://example.test/section", source_drawing="test", installation="test",
        section_documented=True, parts=(DoorwaySectionPart(name="test", material_ref="metal",
            polygon_m=((0,0),(.1,0),(.1,.01),(0,.01))),))
    assembly = DoorwayAssembly(0, (None,None), "transition", 0, selected_products=(spec,))
    serialized = doorway_json(assembly)
    assert serialized["section_status"] == "DOCUMENTED"
    assert serialized["supplier_status"] == "PENDING"
    assert serialized["fit_status"] == "VERIFIED"


def test_exterior_landing_search_crosses_gap_without_matching_elevation():
    from typehaus.resolve.model import ResolvedModel, ResolvedWall

    plan = NS(project=NS(site=NS(impervious_surfaces=())), by_tag=lambda tag: None,
              library=NS(materials=[]))
    slab = NS(tag="landing", category="slab", storey="main", z1_m=-.1, voids=(),
              outline=((0,.05),(4,.05),(4,2),(0,2)))
    model = ResolvedModel(plan, solids=[slab])
    wall = ResolvedWall("wall", "W", "main", "A", ((0,0),(4,0)), (), 0, 3)
    installation = ExteriorDoorInstallation(interior_material_ref="wood")
    floor = exterior_landing(model, wall, (2,.01), (0,1), installation)
    assert floor.deck_tag == "landing" and floor.surface_m == -.1
    assert exterior_landing(model, wall, (2,-1), (0,1), installation) is None


def structural_door_model(reverse=False, exterior_side=1):
    """Physical layers stay fixed when the wall's local axis reverses."""
    from typehaus.model import DoorType
    from typehaus.quantities import m
    from typehaus.resolve.model import ResolvedLayer, ResolvedModel, ResolvedOpening, ResolvedWall

    def ring(low, high):
        a, b = sorted((exterior_side * low, exterior_side * high))
        return ((0, a), (4, a), (4, b), (0, b))
    layers = (
        ResolvedLayer("finish", "wood", "finish", .015, ring(-.085, -.07)),
        ResolvedLayer("stud", "wood", "structure", .14, ring(-.07, .07)),
        ResolvedLayer("clad", "wood", "cladding", .02, ring(.28, .3)),
    )
    wall = ResolvedWall("wall", "W", "main", "A",
        ((4, 0), (0, 0)) if reverse else ((0, 0), (4, 0)), layers, 0, 3)
    installation = ExteriorDoorInstallation(interior_material_ref="wood")
    door_type = DoorType(tag="DT", width=m(.9), height=m(2.1), exterior=True)
    authored = NS(exterior_installation=installation, doorway=None)
    plan = NS(library=NS(door_types=(door_type,), materials=[]), by_tag=lambda tag: authored,
              project=NS(site=NS(impervious_surfaces=())))
    opening = ResolvedOpening("door", "D", "W", "DT", .9, 2.1, 0, 2, "door", True,
                              swing_clearance=[(1.6, 0), (1.6, -exterior_side * .8)])
    return ResolvedModel(plan, walls=[wall], openings=[opening])


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("exterior_side", [-1, 1])
def test_structural_installation_and_sections_follow_mirrored_wall(reverse, exterior_side):
    from typehaus.resolve.doorway import DoorwayComponent
    from typehaus.resolve.exterior_door import place_exterior_door

    model = structural_door_model(reverse, exterior_side)
    wall, opening = model.walls[0], model.openings[0]
    _, _, normal, _ = wall_frame(wall)
    spec = DoorwayProductSpec(product_ref="TEST", variant="synthetic section", role="sill",
        source_url="https://example.test/section", source_drawing="test", installation="test",
        normal_offset_m=.015 * exterior_side * normal[1])
    component = DoorwayComponent(spec, 0, spec.normal_offset_m, .8, 0)
    assembly = DoorwayAssembly(0, (None, None), "transition", 0, components=(component,))
    placement_assembly = place_exterior_door(model, wall, opening, assembly,
        ExteriorDoorInstallation(interior_material_ref="wood"))
    placement = placement_assembly.exterior_placement
    assert normal[1] * placement.frame_outer_m == pytest.approx(exterior_side * .07)
    assert normal[1] * placement.frame_inner_m == pytest.approx(-exterior_side * .07)
    assert normal[1] * placement.leaf_normal_m == pytest.approx(-exterior_side * (.07 - .0225))
    assert normal[1] * placement_assembly.components[0].normal_m == pytest.approx(
        exterior_side * (-.07 + .015))
    returns = [b for b in placement.boards if b.name.startswith("exterior-return")]
    assert len(returns) == 3
    assert all(b.depth_m == pytest.approx(.23) for b in returns)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("exterior_side", [-1, 1])
def test_inswing_clearance_moves_with_leaf_once(reverse, exterior_side):
    from typehaus.resolve.doorway import resolve_doorways

    model = structural_door_model(reverse, exterior_side)
    original = tuple(model.openings[0].swing_clearance)
    resolve_doorways(model)
    moved = tuple(model.openings[0].swing_clearance)
    offset = -exterior_side * (.07 - .0225)
    assert moved == pytest.approx([(x, y + offset) for x, y in original])
    resolve_doorways(model)
    assert tuple(model.openings[0].swing_clearance) == moved


@pytest.mark.parametrize("known_side", [0, 1])
def test_finish_extension_uses_known_room_without_other_surface(known_side):
    from typehaus.resolve.model import ResolvedRoom

    model = structural_door_model()
    low, high = (-2, -.085) if known_side == 0 else (.3, 2)
    outline = ((0, low), (4, low), (4, high), (0, high))
    room = ResolvedRoom("r", "R", "main", "habitable", True, outline,
        4 * (high - low), "plank", field_finish=((outline, ()),))
    model.rooms = [room]
    floors = [None, None]
    floors[known_side] = FloorSurface("slab", 0, "R", "plank", .25)
    assembly = DoorwayAssembly(0, tuple(floors), "transition", 0)
    model.openings = [replace(model.openings[0], doorway=assembly)]
    extend_doorway_finishes(model)
    probe = Point(2, -.04 if known_side == 0 else .15)
    assert any(Polygon(ring, holes=list(holes)).covers(probe)
               for ring, holes in model.rooms[0].field_finish)


def test_catlin_garage_keeps_raised_service_support_and_overhead_operation(catlin_model_ro):
    service = next(o for o in catlin_model_ro.openings if o.tag == "D-G-SERVICE")
    overhead = next(o for o in catlin_model_ro.openings if o.tag == "D-G-OVERHEAD")
    assert service.doorway.exterior_placement is None
    assert overhead.doorway.exterior_placement is None
    sill = next(m for m in catlin_model_ro.wall(service.host_wall).members
                if m.child_key == "sill-0")
    assert sill.z1_m == pytest.approx(service.doorway.rough_opening_z_m)
    assert sill.z0_m < sill.z1_m
    product = next(t for t in catlin_model_ro.plan.library.door_types
                   if t.tag == overhead.type_ref)
    assert product.operation.value == "overhead"
    parts = opening_parts(catlin_model_ro.wall(overhead.host_wall), overhead, product.operation)
    assert not any(p.key.startswith("installation:") for p in parts)
    assert len(next(p for p in parts if p.key == "frame").solids) == 3


@pytest.mark.parametrize("tag", ["D-M-ENTRY", "D-M-BALC", "D-S-DECK-E"])
def test_sill_design_conceals_pan_without_claiming_factory_approval(catlin_model_ro, tag):
    from shapely.geometry import LineString
    from shapely.ops import unary_union

    from typehaus.resolve.flashing_config import FLASHING
    from typehaus.resolve.opening_flashing import _pan_outlet

    model = catlin_model_ro
    opening = next(o for o in model.openings if o.tag == tag)
    wall = model.wall(opening.host_wall)
    assembly = opening.doorway
    placement = assembly.exterior_placement
    sign = placement.outward_sign
    assert placement.sill_design_status == "SCHEMATIC"
    assert assembly.section_status == "UNKNOWN" and assembly.supplier_status == "PENDING"
    assert assembly.status == "UNKNOWN" and not assembly.conflicts
    assert any("structural support/anchorage" in message for message in assembly.unknown)
    frame = opening_flashing_frame(model, wall, opening)
    outlet = _pan_outlet(opening, frame, FLASHING)
    base = assembly.rough_opening_z_m
    polygons = {s.name: Polygon([(sign * n, z) for n, z in s.polygon_m])
                for s in placement.sections}
    assert all(p.is_valid and p.area > 0 for p in polygons.values())
    pan_top = LineString(((sign * placement.frame_inner_m,
        base + (outlet - sign * placement.frame_inner_m) * FLASHING.drainage_slope),
        (outlet, base)))
    for name, polygon in polygons.items():
        if "nosing" not in name:
            assert polygon.intersection(pan_top).length == 0
    walk = [p for name, p in polygons.items() if "bearing-strip" not in name]
    covered = unary_union([LineString(((p.bounds[0], 0), (p.bounds[2], 0))) for p in walk])
    expected = LineString(((sign * placement.frame_inner_m, 0), (outlet, 0)))
    assert expected.difference(covered).length < 1e-8
    crest = max(p.bounds[3] for p in walk)
    assert assembly.leaf_bottom_z_m > crest
    plate = polygons["approach-walking-plate"]
    assert plate.exterior.coords[2][1] < plate.exterior.coords[3][1]
    strips = [s for s in placement.sections if "bearing-strip" in s.name]
    assert all(b.along_m - a.along_m > a.span_m
               for a, b in zip(strips, strips[1:], strict=False))
    assert all(s.span_m < opening.width_m for s in strips)
    isolation = placement.specification.wrap_isolation_thickness.meters
    for strip in strips:
        wood = polygons[strip.name]
        assert wood.distance(polygons["approach-walking-plate"]) >= isolation * .99
        assert wood.distance(polygons["threshold-design-envelope"]) >= isolation * .99
    deck = next(f for f in model.floors if f.tag == assembly.adjacent_floors[0].deck_tag)
    center = opening_center(wall, opening)
    _, tangent, normal, _ = wall_frame(wall)
    def local(point):
        delta = tuple(point[i] - center[i] for i in (0, 1))
        return (sum(delta[i] * tangent[i] for i in (0, 1)),
                sign * sum(delta[i] * normal[i] for i in (0, 1)))
    deck_footprint = Polygon([local(p) for p in deck.deck_outline])
    nose = polygons["approach-drip-nosing"]
    from shapely.geometry import box

    nose_footprint = box(-opening.width_m / 2, nose.bounds[0],
                         opening.width_m / 2, nose.bounds[2])
    assert nose_footprint.intersection(deck_footprint).area < 1e-10
    pan = next(mesh for key, _, _, mesh in opening_flashing_meshes(wall, opening, frame)
               if key == "sill")
    origin = wall.axis[0]
    # Tall side dams end behind the return, rather than projecting as red fins at the drip.
    assert all(sum((p[i] - origin[i]) * frame.outward[i] for i in (0, 1))
               <= frame.clad + 1e-8 for p in pan.positions if p[2] > base + .05)
    parts = opening_parts(wall, opening, next(t.operation for t in model.plan.library.door_types
                         if t.tag == opening.type_ref), is_glazed=tag != "D-M-ENTRY")
    if tag != "D-M-ENTRY":
        assert min(s.z0_m for p in parts if p.key == "mullion" for s in p.solids) \
            >= assembly.leaf_bottom_z_m
    site_rows = [r for r in door_installation_rows(model)
                 if tag in r["tags"] and r["kind"] == "exterior door approach"]
    assert len(site_rows) == len([s for s in placement.sections if s.purchase == "site"])
    assert all(section.name not in row["description"] for section in placement.sections
               if section.purchase == "factory_included" for row in site_rows)


def test_study_door_uses_oak_floor_and_sloping_balcony(catlin_model_ro):
    opening = next(o for o in catlin_model_ro.openings if o.tag == "D-S-DECK-E")
    exterior, interior = opening.doorway.adjacent_floors
    assert exterior.deck_tag == "FS-SG-DECK" and exterior.room_tag is None
    assert interior.room_tag == "RM-S-STUDY2" and interior.finish_ref == "oak-floor-custom"
    deck = next(f for f in catlin_model_ro.floors if f.tag == exterior.deck_tag)
    low, high = deck.deck_top_range()
    assert high > low
    assert low <= exterior.surface_m <= high
    assert exterior.surface_m < interior.surface_m < opening.doorway.leaf_bottom_z_m
    sills = [product for product in opening.doorway.selected_products if product.role == "sill"]
    assert sills and all(product.purchase == "factory_included" and not product.section_documented
                         for product in sills)


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("exterior_side", [-1, 1])
def test_sill_and_steel_wrap_follow_mirrored_structural_wall(reverse, exterior_side):
    from typehaus.model import ExteriorDoorSillDesign
    from typehaus.quantities import inch
    from typehaus.resolve.exterior_door import place_exterior_door

    model = structural_door_model(reverse, exterior_side)
    wall, opening = model.walls[0], model.openings[0]
    sign = exterior_side * wall_frame(wall)[2][1]
    floors = (FloorSurface("landing", 0, None, None, 0),
              FloorSurface("interior", 0, "room", "wood", .25))
    if sign > 0:
        floors = floors[::-1]
    assembly = DoorwayAssembly(0, floors, "transition", 0)
    specification = ExteriorDoorInstallation(interior_material_ref="wood",
        exterior_wrap_material_ref="steel", sill_design=ExteriorDoorSillDesign(
            source_url="https://example.test/design", source_drawing="synthetic design",
            threshold_depth=inch(4.5), threshold_height=inch(1.5), cap_depth=inch(1.5)))
    placed = place_exterior_door(model, wall, opening, assembly, specification)
    assert not placed.conflicts
    placement = placed.exterior_placement
    assert placement.sill_design_status == "SCHEMATIC"
    for board in placement.boards:
        if board.role != "door_trim_wrap" or "outer-edge" in board.name:
            continue
        substrate = next(b for b in placement.boards
                         if b.name == board.name.removesuffix("-door_trim_wrap"))
        if "casing" in board.name:
            gap = sign * (board.normal_m - substrate.normal_m) \
                - (board.depth_m + substrate.depth_m) / 2
        elif "jamb" in board.name:
            gap = abs(board.along_m - substrate.along_m) \
                - (board.width_m + substrate.width_m) / 2
        else:
            gap = substrate.z_m - board.z_m - (board.height_m + substrate.height_m) / 2
        assert gap == pytest.approx(specification.wrap_isolation_thickness.meters)
        assert board.material_ref == "steel"
    for section in placement.sections:
        assert Polygon(section.polygon_m).is_valid


def test_local_deck_cutback_reaches_model_json(catlin_model_ro):
    from typehaus.server.model_json import model_to_dict

    floor = next(f for f in catlin_model_ro.floors if f.tag == "FS-BW-FLOOR")
    assert len(floor.deck_outline) > 4
    packet = next(f for f in model_to_dict(catlin_model_ro)["floors"] if f["tag"] == floor.tag)
    assert packet["deck_outline"] == [list(p) for p in floor.deck_outline]
    assert packet["deck_voids"] == [[list(p) for p in ring] for ring in floor.deck_voids]
