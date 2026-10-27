"""Assembly datum and continuous sweep regressions with inexpensive synthetic geometry."""
from dataclasses import replace
from types import SimpleNamespace

import pytest
from shapely.geometry import Point

from typehaus.model.exterior_door import ExteriorDoorSwingAssembly
from typehaus.quantities import inch
from typehaus.resolve.door_swing_envelope import (
    assembly_components,
    clearance_results,
    installed_swing_sector,
    swept_intervals,
)
from typehaus.resolve.geometry_ir import ElementGeometry, GeometryModel, GPart, GPrism

INCH = 0.0254


def assembly(**changes):
    values = dict(source_url="https://example.com/section", source_drawing="test section",
                  hinge_inset=inch(1), hinge_normal_offset=inch(2),
                  leaf_start=inch(0), leaf_end=inch(30),
                  leaf_face_min=inch(-0.875), leaf_face_max=inch(0.875),
                  leaf_bottom=inch(1), leaf_top=inch(80), lever_backset=inch(2.375),
                  lever_hingeward_extent=inch(4), lever_projection=inch(2.5),
                  lever_bottom=inch(35), lever_top=inch(40))
    values.update(changes)
    return ExteriorDoorSwingAssembly(**values)


def opening(spec=None, width=34):
    return SimpleNamespace(tag="door", host_wall="wall", center_along_m=20 * INCH,
                           width_m=width * INCH, sill_m=0, flip_hinge=True, flip_swing=True,
                           swing_assembly=spec or assembly(), doorway=None)


def wall():
    return SimpleNamespace(axis=((0, 0), (4, 0)), base_ref_z_m=0)


def test_rough_opening_and_leaf_and_hinge_datums_are_independent():
    door = opening()
    hinge, components = assembly_components(wall(), door)
    assert tuple(v / INCH for v in hinge) == pytest.approx((4, 2))
    assert (components[0].closed.bounds[2] - components[0].closed.bounds[0]) / INCH == \
        pytest.approx(30)
    changed = opening(assembly(hinge_inset=inch(2), leaf_end=inch(29)), width=36)
    hinge2, components2 = assembly_components(wall(), changed)
    assert tuple(v / INCH for v in hinge2) == pytest.approx((4, 2))
    assert (components2[0].closed.bounds[2] - components2[0].closed.bounds[0]) / INCH == \
        pytest.approx(29)


def test_continuous_sweep_catches_intermediate_rotation():
    door = opening()
    hinge, components = assembly_components(wall(), door)
    leaf = components[0]
    intervals = swept_intervals(leaf, hinge, door, 90)
    from shapely.affinity import rotate
    point = rotate(Point(hinge[0] + 25 * INCH, hinge[1]), -45.5, origin=hinge)
    assert not leaf.closed.intersects(point)
    assert not rotate(leaf.closed, -90, origin=hinge).intersects(point)
    assert any(shape.intersects(point) for _, _, shape in intervals)


def test_leaf_and_lever_clearance_use_separate_elevations():
    door = opening()
    hinge, _ = assembly_components(wall(), door)
    x, y = hinge[0] + 27 * INCH, hinge[1]
    prism = GPrism(ring=((x, y - INCH), (x + INCH, y - INCH),
                         (x + INCH, y + INCH), (x, y + INCH)),
                   z0_m=10 * INCH, z1_m=12 * INCH)
    geometry = GeometryModel(elements=(ElementGeometry(uid="obstacle", kind="connector",
        parts=(GPart(key="body", material_key="steel", solids=(prism,)),)),))
    plan = SimpleNamespace(all_elements=lambda: ())
    model = SimpleNamespace(wall=lambda _: wall(), geometry=geometry, plan=plan, solids=())
    results = clearance_results(model, door, 90)
    assert any(r.component == "leaf" and r.clearance_m < 0 for r in results)
    assert not any(r.component == "lever" for r in results)
    raised = replace(prism, z0_m=36 * INCH, z1_m=38 * INCH)
    model.geometry = GeometryModel(elements=(replace(geometry.elements[0],
        parts=(replace(geometry.elements[0].parts[0], solids=(raised,)),)),))
    assert {r.component for r in clearance_results(model, door, 90)} == {"leaf", "lever"}


def test_confirmed_assembly_requires_framed_dimensions():
    with pytest.raises(ValueError, match="rough-opening dimensions"):
        assembly(supplier_confirmed=True)


def test_installed_sector_and_framed_size_use_confirmed_assembly():
    from typehaus.resolve.pipeline import _opening_size

    spec = assembly(supplier_confirmed=True, rough_opening_width=inch(34),
                    rough_opening_height=inch(81))
    door = opening(spec)
    hinge, _ = assembly_components(wall(), door)
    sector = installed_swing_sector(wall(), door, 90)
    assert sector[0] == pytest.approx(hinge)
    assert (sector[1][0] - hinge[0]) / INCH == pytest.approx(30)
    assert (sector[-1][1] - hinge[1]) / INCH == pytest.approx(-30)
    element = SimpleNamespace(element_kind="Door", type_ref="type", exterior_installation=
                              SimpleNamespace(swing_assembly=spec))
    plan = SimpleNamespace(library=SimpleNamespace(door_types=(
        SimpleNamespace(tag="type", width=inch(32), height=inch(80)),)))
    width, height, is_door, _ = _opening_size(plan, element)
    assert (width / INCH, height / INCH, is_door) == pytest.approx((34, 81, True))
