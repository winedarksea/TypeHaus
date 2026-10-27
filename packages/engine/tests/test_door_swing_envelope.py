"""Assembly datum and continuous sweep regressions with inexpensive synthetic geometry."""
from dataclasses import replace
from types import SimpleNamespace

import pytest
from scripts.garage_service_door_clearance import (
    SwingEnvelope,
    assembly_components,
    clearance_results,
    swept_intervals,
)
from shapely.geometry import Point

from typehaus.quantities import inch
from typehaus.resolve.geometry_ir import ElementGeometry, GeometryModel, GPart, GPrism

INCH = 0.0254


def assembly(**changes):
    values = dict(hinge_inset=inch(1), hinge_normal_offset=inch(2),
                  leaf_start=inch(0), leaf_end=inch(30),
                  leaf_face_min=inch(-0.875), leaf_face_max=inch(0.875),
                  leaf_bottom=inch(1), leaf_top=inch(80), lever_backset=inch(2.375),
                  lever_hingeward_extent=inch(4), lever_projection=inch(2.5),
                  lever_bottom=inch(35), lever_top=inch(40))
    values.update(changes)
    return SwingEnvelope(**values)


def opening(spec=None, width=34):
    return SimpleNamespace(tag="door", host_wall="wall", center_along_m=20 * INCH,
                           width_m=width * INCH, sill_m=0, flip_hinge=True, flip_swing=True,
                           swing_assembly=spec or assembly(), doorway=None)


def wall():
    return SimpleNamespace(axis=((0, 0), (4, 0)), base_ref_z_m=0)


def test_rough_opening_and_leaf_and_hinge_datums_are_independent():
    door = opening()
    hinge, components = assembly_components(wall(), door, door.swing_assembly)
    assert tuple(v / INCH for v in hinge) == pytest.approx((4, 2))
    assert (components[0].closed.bounds[2] - components[0].closed.bounds[0]) / INCH == \
        pytest.approx(30)
    changed = opening(assembly(hinge_inset=inch(2), leaf_end=inch(29)), width=36)
    hinge2, components2 = assembly_components(wall(), changed, changed.swing_assembly)
    assert tuple(v / INCH for v in hinge2) == pytest.approx((4, 2))
    assert (components2[0].closed.bounds[2] - components2[0].closed.bounds[0]) / INCH == \
        pytest.approx(29)


def test_continuous_sweep_catches_intermediate_rotation():
    door = opening()
    hinge, components = assembly_components(wall(), door, door.swing_assembly)
    leaf = components[0]
    intervals = swept_intervals(leaf, hinge, door, 90, door.swing_assembly)
    from shapely.affinity import rotate
    point = rotate(Point(hinge[0] + 25 * INCH, hinge[1]), -45.5, origin=hinge)
    assert not leaf.closed.intersects(point)
    assert not rotate(leaf.closed, -90, origin=hinge).intersects(point)
    assert any(shape.intersects(point) for _, _, shape in intervals)


def test_leaf_and_lever_clearance_use_separate_elevations():
    door = opening()
    hinge, _ = assembly_components(wall(), door, door.swing_assembly)
    x, y = hinge[0] + 27 * INCH, hinge[1]
    prism = GPrism(ring=((x, y - INCH), (x + INCH, y - INCH),
                         (x + INCH, y + INCH), (x, y + INCH)),
                   z0_m=10 * INCH, z1_m=12 * INCH)
    geometry = GeometryModel(elements=(ElementGeometry(uid="obstacle", kind="connector",
        parts=(GPart(key="body", material_key="steel", solids=(prism,)),)),))
    plan = SimpleNamespace(all_elements=lambda: ())
    model = SimpleNamespace(wall=lambda _: wall(), geometry=geometry, plan=plan, solids=())
    results = clearance_results(model, door, 90, door.swing_assembly)
    assert any(r.component == "leaf" and r.clearance_m < 0 for r in results)
    assert not any(r.component == "lever" for r in results)
    raised = replace(prism, z0_m=36 * INCH, z1_m=38 * INCH)
    model.geometry = GeometryModel(elements=(replace(geometry.elements[0],
        parts=(replace(geometry.elements[0].parts[0], solids=(raised,)),)),))
    components = {r.component for r in clearance_results(model, door, 90, door.swing_assembly)}
    assert components == {"leaf", "lever"}

