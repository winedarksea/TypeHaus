"""Soffit ladder framing (``resolve/framing/soffit.py``).

A dropped ceiling used to resolve to one solid box and nothing else: its authored
``FramingSpec`` was carried on ``Soffit.framing`` and read by no one, so the lumber
inside a duct chase reached no take-off, no framing sheet, and no interference check.

Mostly synthetic — a 2'-8" x 12'-0" soffit dropped 14" under a 9'-0" ceiling, framed in
2x2 at 16" o.c., which is the catlin SF-S-DUCT case at its *original* 32" width. The
stock size is the point: a 32" box framed in 2x2 clears 27.75" between the ladders where
the same box in 2x4 clears 23.75", and the two 14" ducts it carries need 28"
(``test_clear_width_between_the_ladders_is_the_full_stack`` measures exactly that — and
comes up 1/4" short, which is why the real soffit was widened).

``test_catlin_duct_soffit_frames_and_clears_the_two_trunks`` at the bottom runs the same
arithmetic against the resolved catlin model, where the box is now 35" and does clear.
"""

from __future__ import annotations

import uuid

from typehaus.model import (
    Assembly,
    Building,
    FramingSpec,
    Layer,
    LayerFunction,
    Library,
    Material,
    Node,
    PlanModel,
    Project,
    Site,
    Soffit,
    Storey,
    Wall,
    degF,
    ft,
    inch,
    pt,
)
from typehaus.resolve import resolve

LINING_IN = 0.625
STOCK_IN = 1.5


def _plan(framing: FramingSpec | None, outline=None) -> PlanModel:
    assembly = Assembly(tag="EXT", layers=(
        Layer(name="stud", material_ref="wood", thickness=inch(5.5),
              function=LayerFunction.STRUCTURE, framing=FramingSpec(member="2x6")),
    ))
    project = Project(
        name="Soffit", project_uuid=uuid.UUID("00000000-0000-4000-8000-0000000000a1"),
        site=Site(lat=44.9, lon=-93.2, elevation=ft(830), design_temp_heating=degF(-15),
                  design_temp_cooling=degF(90)), building=Building(name="Soffit"),
    )
    main = Storey(uid="STMAIN0001", tag="main", elevation=ft(0), default_ceiling_height=ft(9))
    nodes = tuple(
        Node(uid=f"N{i:09d}", tag=f"N-{i}", position=position)
        for i, position in enumerate((
            pt(ft(0), ft(0)), pt(ft(20), ft(0)), pt(ft(20), ft(14)), pt(ft(0), ft(14)),
        ), 1)
    )
    walls = tuple(
        Wall(uid=f"W{i:09d}", tag=f"W-{i}", start_node=f"N-{start}", end_node=f"N-{end}",
             assembly="EXT", top=ft(9))
        for i, (start, end) in enumerate(((1, 2), (2, 3), (3, 4), (4, 1)), 1)
    )
    # 2'-8" wide (x) x 12'-0" long (y), the duct-chase proportion.
    default_outline = (pt(ft(4), ft(1)), pt(ft(6, 8), ft(1)),
                       pt(ft(6, 8), ft(13)), pt(ft(4), ft(13)))
    soffit = Soffit(uid="SF00000001", tag="SF-1",
                    outline=outline if outline is not None else default_outline,
                    drop=inch(14), framing=framing)
    plan = PlanModel(project=project, library=Library(
        materials=(Material(tag="wood", name="Wood", r_per_inch=1.25),), assemblies=(assembly,)),
                     storeys=(main,))
    return plan.with_elements("main", (*nodes, *walls, soffit))


def _framed(**kwargs):
    model, findings = resolve(_plan(FramingSpec(member="2x2", spacing=inch(16)), **kwargs))
    assert model.soffits and model.soffits[0].tag == "SF-1"
    return model, findings


def _by_category(soffit, category):
    return [member for member in soffit.members if member.category == category]


# ---------------------------------------------------------------- layout + counts
def test_ladder_layout_member_counts() -> None:
    """Two ladders + rungs: 4 continuous rails, 2 studs per station, a rung per interior
    station, and one end blocking closing each end.

    The lined interior runs 144" - 2 x 5/8" = 142.75". The end stations sit half a stock
    thickness in (0.75" / 142.0"), and the 16" module contributes 16"..128" — station 0
    is swallowed by the end stud — so there are 10 stations, 8 of them interior."""
    model, _ = _framed()
    soffit = model.soffits[0]
    plates = _by_category(soffit, "plate")
    studs = _by_category(soffit, "stud")
    blocking = _by_category(soffit, "blocking")

    assert len(plates) == 4
    assert {plate.child_key for plate in plates} == {
        "soffit-plate-top-w", "soffit-plate-bottom-w",
        "soffit-plate-top-e", "soffit-plate-bottom-e",
    }
    assert len(studs) == 20  # 10 stations x 2 sides
    assert len({stud.child_key for stud in studs}) == 20
    assert len([m for m in blocking if m.child_key.startswith("soffit-rung-")]) == 8
    assert {m.child_key for m in blocking if m.child_key.startswith("soffit-end-")} == {
        "soffit-end-s", "soffit-end-n",
    }
    assert len(soffit.members) == 34
    assert all(member.parent_uid == soffit.uid for member in soffit.members)
    assert all(member.profile == "2x2" for member in soffit.members)


def test_rails_run_the_full_lined_length() -> None:
    model, _ = _framed()
    expected = ft(12).meters - 2 * inch(LINING_IN).meters
    for plate in _by_category(model.soffits[0], "plate"):
        assert abs(plate.length_m - expected) < 1e-9
        assert abs(abs(plate.p1[1] - plate.p0[1]) - expected) < 1e-9
        assert plate.p0[0] == plate.p1[0]  # the rail runs the long (y) way


def test_stud_stations_sit_on_the_sixteen_inch_module() -> None:
    model, _ = _framed()
    origin = ft(1).meters + inch(LINING_IN).meters
    stations = sorted({round((stud.p0[1] - origin) / inch(1).meters, 4)
                       for stud in _by_category(model.soffits[0], "stud")})
    assert stations[0] == 0.75 and stations[-1] == 142.0
    assert stations[1:-1] == [16.0 * n for n in range(1, 9)]


# ---------------------------------------------------------------- inside the box
def test_every_member_stays_inside_the_lined_soffit_box() -> None:
    model, _ = _framed()
    soffit = model.soffits[0]
    lining = inch(LINING_IN).meters
    x0, x1 = ft(4).meters + lining, ft(6, 8).meters - lining
    y0, y1 = ft(1).meters + lining, ft(13).meters - lining
    z0, z1 = soffit.z0_m + lining, soffit.z1_m
    assert abs((soffit.z1_m - soffit.z0_m) - inch(14).meters) < 1e-9
    for member in soffit.members:
        for x, y in (member.p0, member.p1):
            assert x0 - 1e-9 <= x <= x1 + 1e-9, member.child_key
            assert y0 - 1e-9 <= y <= y1 + 1e-9, member.child_key
        assert z0 - 1e-9 <= member.z0_m < member.z1_m <= z1 + 1e-9, member.child_key


def test_members_are_inset_from_the_finished_faces() -> None:
    """Lining covers the underside and returns; top rails meet the overhead structure."""
    model, _ = _framed()
    soffit = model.soffits[0]
    lining = inch(LINING_IN).meters
    xs = [x for member in soffit.members for x, _ in (member.p0, member.p1)]
    ys = [y for member in soffit.members for _, y in (member.p0, member.p1)]
    assert min(xs) >= ft(4).meters + lining - 1e-9
    assert max(xs) <= ft(6, 8).meters - lining + 1e-9
    assert min(ys) >= ft(1).meters + lining - 1e-9
    assert max(ys) <= ft(13).meters - lining + 1e-9
    assert min(m.z0_m for m in soffit.members) >= soffit.z0_m + lining - 1e-9
    assert max(m.z1_m for m in soffit.members) <= soffit.z1_m + 1e-9


def test_clear_width_between_the_ladders_is_the_full_stack() -> None:
    """The reason the spec says 2x2, and the dimension a duct has to fit through.

    A 32" finished box gives up 2 x 5/8" of lining and 2 x 1.5" of ladder, so the clear
    span the rung measures is 27.75". Framed in 2x4 instead it would be 23.75" — which
    is why the generator must never widen the spec's stock to a default.

    Note for the duct: 27.75" is a quarter inch *short* of two 14" ducts laid side by
    side (28"). The catlin SF-S-DUCT rationale used to quote 29.5" clear, which is the
    lumber-only figure — it did not account for the gwb lining wrapping the box. That is
    what this synthetic case caught, and the real soffit was widened to 35" in response.
    Asserted here as arithmetic rather than as a passing clearance, because at 32" it
    does not pass; see the catlin test at the bottom of this module for the one that does.
    """
    model, _ = _framed()
    rung = next(m for m in model.soffits[0].members if m.child_key.startswith("soffit-rung-"))
    clear_in = rung.length_m / inch(1).meters
    assert abs(clear_in - (32 - 2 * LINING_IN - 2 * STOCK_IN)) < 1e-6
    assert abs(clear_in - 27.75) < 1e-6
    assert clear_in < 28.0  # see the docstring: the box, as drawn, is 1/4" tight


# ---------------------------------------------------------------- the None case
def test_soffit_without_a_framing_spec_frames_nothing() -> None:
    model, findings = resolve(_plan(None))
    assert model.soffits and model.soffits[0].framing is None
    assert model.soffits[0].members == []
    assert not [f for f in findings if f.check_id.startswith("framing.soffit")]
    # The finished box is unchanged either way.
    assert any(solid.category == "soffit" for solid in model.solids)


def test_soffit_members_reach_the_shared_member_set() -> None:
    model, _ = _framed()
    keys = {(m.parent_uid, m.child_key) for m in model.all_members()}
    assert all((m.parent_uid, m.child_key) in keys for m in model.soffits[0].members)


# ---------------------------------------------------------------- the real house
def test_catlin_duct_soffit_frames_and_clears_the_two_trunks(catlin_model_ro) -> None:
    """SF-S-DUCT, resolved from the catlin plan, actually fits the ducts it exists for.

    The synthetic case above is this soffit in miniature and deliberately *fails* the
    clearance at the old 32" width. The box was widened to 35" (x 18'-6 1/2" ..
    21'-5 1/2", plan/storeys/second.py), so the arithmetic here comes out the other way:
    The wall-width box has 37.24" conservative clearance, with rungs extending further
    to wall-backed ledgers. Assert the built span and attachment records rather than a
    stale authored width.
    """
    soffit = next(s for s in catlin_model_ro.soffits if s.tag == "SF-S-DUCT")
    assert soffit.framing is not None and soffit.framing.member == "2x2"

    # It resolves real ladder framing, not an empty box.
    assert soffit.members
    categories = {member.category for member in soffit.members}
    assert {"plate", "stud", "blocking"} <= categories
    assert any(member.connection and "screw-to-studs" in member.connection
               for member in soffit.members)
    assert all(member.profile == "2x2" for member in soffit.members)
    assert all(member.parent_uid == soffit.uid for member in soffit.members)

    rungs = [m for m in soffit.members if m.child_key.startswith("soffit-rung-")]
    assert rungs, "a 28'-long soffit must have interior rungs"
    clear_in = min(rung.length_m for rung in rungs) / inch(1).meters
    assert clear_in >= 37.24
    assert clear_in >= 30.0  # 14" + 2" gap + 14", the reason the box was widened


# ---------------------------------------------------------------- non-rectangles
def test_non_rectangular_soffit_warns_instead_of_guessing() -> None:
    ell = (pt(ft(4), ft(1)), pt(ft(6, 8), ft(1)), pt(ft(6, 8), ft(13)),
           pt(ft(5), ft(13)), pt(ft(5), ft(8)), pt(ft(4), ft(8)))
    model, findings = resolve(_plan(FramingSpec(member="2x2", spacing=inch(16)), outline=ell))
    assert model.soffits[0].members == []
    warning = next(f for f in findings if f.check_id == "framing.soffit_shape")
    assert warning.severity.value == "warn" and warning.result.value == "unknown"
    assert warning.element_tags == ("SF-1",)


def test_finish_geometry_is_board_with_an_open_service_cavity() -> None:
    from shapely.geometry import Point, Polygon

    from typehaus.takeoff.framing import structural_solids_takeoff

    model, _ = _framed()
    soffit = model.soffits[0]
    middle = Polygon(soffit.outline).centroid
    assert any(panel.key.startswith("underside") for panel in soffit.finish_panels)
    assert not any(Polygon(panel.prism.ring).contains(Point(middle.x, middle.y))
                   and panel.prism.z1_m == soffit.z1_m for panel in soffit.finish_panels)
    geometry = model.geometry.by_uid(soffit.uid)
    assert [part.solids[0] for part in geometry.parts] == [
        panel.prism for panel in soffit.finish_panels]
    row = next(row for row in structural_solids_takeoff(model) if row["category"] == "soffit")
    actual_board_area = sum(panel.area_m2 for panel in soffit.finish_panels)
    assert abs(row["finish_area_sqft"] - actual_board_area / ft(1).meters ** 2) < 0.05
    assert row["volume_cuft"] < 10  # The old service-envelope volume was over 37 cu ft.


def test_access_hatch_cuts_the_underside_board() -> None:
    from shapely.geometry import Point, Polygon

    from typehaus.model import SoffitOpening

    plan = _plan(FramingSpec(member="2x2", spacing=inch(16)))
    host = plan.by_tag("SF-1")
    opening = SoffitOpening(tag="HATCH", outline=(
        pt(ft(4, 6), ft(5)), pt(ft(6, 2), ft(5)),
        pt(ft(6, 2), ft(7)), pt(ft(4, 6), ft(7))))
    host = host.model_copy(update={"openings": (opening,)})
    elements = [host if element.tag == host.tag else element
                for element in plan.storey_elements("main")]
    model, _ = resolve(plan.with_elements("main", elements))
    center = Point(ft(5).meters, ft(6).meters)
    underside = [panel.prism for panel in model.soffits[0].finish_panels
                 if panel.key.startswith("underside")]
    assert underside
    assert not any(Polygon(prism.ring, prism.voids).contains(center) for prism in underside)


def test_partial_wall_contact_removes_only_the_backed_return() -> None:
    from dataclasses import replace

    from shapely.geometry import Point, Polygon

    from typehaus.resolve.soffits import resolve_soffit_contacts, resolve_soffit_finishes

    model, _ = _framed()
    soffit = model.soffits[0]
    # Reuse the synthetic west wall, shortening its body layers halfway down the box.
    wall = model.walls[3]
    edge_x = min(x for x, _ in soffit.outline)
    wall = replace(wall, layers=[replace(layer, polygon=[
        (edge_x - inch(5.5).meters, ft(1).meters), (edge_x, ft(1).meters),
        (edge_x, ft(7).meters), (edge_x - inch(5.5).meters, ft(7).meters)])
        for layer in wall.layers])
    model.walls = [wall]
    resolve_soffit_contacts(model)
    resolve_soffit_finishes(model)
    assert soffit.wall_contacts
    backed = Point(edge_x + inch(0.25).meters, ft(4).meters)
    exposed = Point(edge_x + inch(0.25).meters, ft(10).meters)
    returns = [Polygon(panel.prism.ring) for panel in soffit.finish_panels
               if panel.key.startswith("return")]
    assert not any(polygon.contains(backed) for polygon in returns)
    assert any(polygon.contains(exposed) for polygon in returns)


def test_adjacent_boxes_have_no_internal_cap_but_keep_the_step() -> None:
    from dataclasses import replace

    from shapely.geometry import Point, Polygon

    from typehaus.resolve.soffits import resolve_soffit_finishes

    model, _ = _framed()
    host = model.soffits[0]
    next_box = replace(host, uid="SF00000002", tag="SF-2", outline=[
        (x, y + ft(12).meters) for x, y in host.outline],
        z0_m=host.z0_m - inch(6).meters, members=[])
    model.soffits.append(next_box)
    resolve_soffit_finishes(model)
    x = ft(5).meters
    seam = ft(13).meters
    hidden_z = host.z0_m + inch(3).meters
    assert not any(panel.prism.z0_m < hidden_z < panel.prism.z1_m
                   and Polygon(panel.prism.ring).contains(Point(x, seam - inch(0.25).meters))
                   for panel in host.finish_panels)
    step_z = host.z0_m - inch(3).meters
    assert any(panel.prism.z0_m < step_z < panel.prism.z1_m
               and Polygon(panel.prism.ring).contains(Point(x, seam + inch(0.25).meters))
               for panel in next_box.finish_panels)


def test_catlin_width_channel_and_wall_support_share_the_boundaries(catlin_model_ro) -> None:
    from shapely.geometry import LineString, Polygon

    from typehaus.resolve.framing.footprint import member_footprint
    from typehaus.resolve.soffits import wall_footprint

    model = catlin_model_ro
    host = next(host for host in model.soffits if host.tag == "SF-S-DUCT")
    west = next(wall for wall in model.walls if wall.tag == "W-S-C2B")
    east = next(wall for wall in model.walls if wall.tag == "W-S-BW1")
    xmin, _ymin, xmax, _ymax = Polygon(host.outline).bounds
    assert abs(xmin - wall_footprint(west).bounds[2]) < 1e-9
    assert abs(xmax - wall_footprint(east).bounds[0]) < 1e-9
    assert abs(host.z0_m / inch(1).meters - 214) < 1e-9
    run = next(run for run in model.light_runs if run.tag == "LR-S-HALL-GAP")
    assert run.soffit_ref == host.tag and run.emission_side == "left"
    # The plaster-in profile's slot centre stands 2 1/2" in from each wall (#103).
    assert run.profile == "plaster_in" and run.host_ref == host.tag
    assert abs(min(x for x, _ in run.path) - xmin - inch(2.5).meters) < 1e-9
    assert abs(max(x for x, _ in run.path) - xmax + inch(2.5).meters) < 1e-9
    slot = LineString(run.path).buffer(run.aperture_m / 2, cap_style=2, join_style=2)
    for panel in host.finish_panels:
        if panel.key.startswith("underside"):
            assert Polygon(panel.prism.ring, panel.prism.voids).intersection(slot).area < 1e-9
    for member in host.members:
        assert member.z0_m >= run.z_m - 1e-9  # The recessed channel fits below its backing.
        footprint = Polygon(member_footprint(member)[0])
        for wall in model.walls:
            if wall.storey == host.storey and wall.z0_m < member.z1_m and wall.z1_m > member.z0_m:
                assert footprint.intersection(wall_footprint(wall)).area < 1e-8, (
                    member.child_key, wall.tag)


def test_exports_contain_the_board_volume_and_separate_framing(tmp_path) -> None:
    import struct

    import ifcopenshell
    import pytest

    from typehaus.emit.gltf.emitter import emit_gltf_dict
    from typehaus.emit.ifc import emit_ifc

    model, _ = _framed()
    host = model.soffits[0]
    expected = sum(panel.area_m2 for panel in host.finish_panels) * inch(LINING_IN).meters
    gltf, binary = emit_gltf_dict(model, lod="framed")
    nodes = [node for node in gltf["nodes"] if node.get("extras", {}).get("uid") == host.uid]
    assert {node["extras"]["trade"] for node in nodes} == {"drywall", "framing"}
    drywall = next(node for node in nodes if node["extras"]["trade"] == "drywall")
    signed_volume = 0.0
    for primitive in gltf["meshes"][drywall["mesh"]]["primitives"]:
        accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
        view = gltf["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        positions = [struct.unpack_from("<fff", binary, offset + index * 12)
                     for index in range(accessor["count"])]
        for index in range(0, len(positions), 3):
            a, b, c = positions[index:index + 3]
            signed_volume += (a[0] * (b[1] * c[2] - b[2] * c[1])
                              + a[1] * (b[2] * c[0] - b[0] * c[2])
                              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
    assert abs(signed_volume) == pytest.approx(expected, abs=1e-5)
    path = tmp_path / "soffit.ifc"
    emit_ifc(model, path)
    file = ifcopenshell.open(str(path))
    covering = next(product for product in file.by_type("IfcCovering") if product.Name == host.tag)
    items = covering.Representation.Representations[0].Items
    assert len(items) == len(host.finish_panels)
    assert sorted(item.Depth for item in items) == pytest.approx(sorted(
        panel.prism.z1_m - panel.prism.z0_m for panel in host.finish_panels))
    assert len([member for member in file.by_type("IfcMember")
                if member.Name.startswith(host.tag + "/")]) == len(host.members)


def test_missing_width_wall_reports_a_resolve_error() -> None:
    plan = _plan(FramingSpec(member="2x2", spacing=inch(16)))
    host = plan.by_tag("SF-1").model_copy(update={"width_between_walls": ("W-4", "MISSING")})
    elements = [host if element.tag == host.tag else element
                for element in plan.storey_elements("main")]
    model, findings = resolve(plan.with_elements("main", elements))
    assert not model.soffits
    assert any(finding.check_id == "integrity.soffit_width" for finding in findings)


def test_wall_clipping_clears_the_stock_width_even_when_the_axis_misses() -> None:
    from dataclasses import replace

    from shapely.geometry import Polygon

    from typehaus.resolve.framing.footprint import member_footprint
    from typehaus.resolve.framing.soffit_support import coordinate_soffit_support

    model, _ = _framed()
    host = model.soffits[0]
    rail = next(member for member in host.members if member.child_key == "soffit-plate-bottom-w")
    # This wall overlaps the rail's outer half, while its plan axis remains unobstructed.
    x = rail.p0[0] - inch(0.25).meters
    obstruction = [(x - inch(5.5).meters, ft(5).meters), (x, ft(5).meters),
                   (x, ft(7).meters), (x - inch(5.5).meters, ft(7).meters)]
    wall = model.walls[3]
    model.walls = [replace(wall, layers=tuple(
        replace(layer, polygon=obstruction) for layer in wall.layers))]
    pieces = coordinate_soffit_support(model, host, [rail])
    assert len(pieces) == 2
    assert all(Polygon(member_footprint(piece)[0]).intersection(
        Polygon(obstruction)).area < 1e-9 for piece in pieces)
