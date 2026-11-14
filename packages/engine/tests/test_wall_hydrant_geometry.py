"""Model 19 wall-faucet geometry: mounting frame, open wheel/nozzle, and closed meshes."""

import math

import pytest

from typehaus.library.placeables.fixtures import WALL_HYDRANT_SELF_DRAINING
from typehaus.model.placeable_symbols import model_parts
from typehaus.model.placeable_symbols._wall_hydrant_config import MODEL_19
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_ir import signed_volume


def test_wall_hydrant_has_horizontal_barrel_wall_flange_and_open_hardware():
    product = WALL_HYDRANT_SELF_DRAINING
    d = MODEL_19
    parts = model_parts(product.plan_symbol, *(v.meters for v in product.footprint),
                        product.height.meters)
    barrel, inlet, flange = parts[:3]
    assert barrel['size'] == pytest.approx(tuple(v * M_PER_IN for v in (.875, 10.25, .875)))
    rear = inlet['center'][1] + inlet['size'][1] / 2
    flange_back = flange['center'][1] + flange['size'][1] / 2
    assert rear - flange_back == pytest.approx(10.25 * M_PER_IN)
    port, = product.ports
    assert tuple(v.meters for v in port.position) == pytest.approx(
        (0, rear, barrel['center'][2]))
    assert product.mount.elevation.meters + port.position[2].meters == pytest.approx(24 * M_PER_IN)
    wheel = next(p for p in parts if p['color'] == 'metal-black'
                 and p['size'][0] == pytest.approx(d.handle_width * M_PER_IN))
    assert wheel['size'] == pytest.approx(tuple(v * M_PER_IN for v in (2.65, .3, 2)))
    # Ring vertices leave finger openings; the hub and crossbar are separate solids.
    for x, _, z in wheel['mesh']['positions']:
        relative_z = z - d.barrel_axis_height * M_PER_IN
        radius = math.hypot(x / (d.handle_width * M_PER_IN / 2),
                            relative_z / (d.handle_height * M_PER_IN / 2))
        assert radius >= d.handle_opening_diameter - 1e-9
    nozzle = parts[-1]
    assert nozzle['size'][:2] == pytest.approx((1.0625 * M_PER_IN,) * 2)
    assert min(p[2] for p in nozzle['mesh']['positions']) == pytest.approx(0)
    for x, y, _ in nozzle['mesh']['positions']:
        assert math.hypot(x, y - nozzle['center'][1]) >= .75 * M_PER_IN / 2 - 1e-9
    for part in parts:
        mesh = part['mesh']
        assert signed_volume(mesh['positions'], mesh['triangles']) > 0
        assert len(mesh['normals']) == len(mesh['positions'])
        assert all(math.sqrt(sum(v * v for v in n)) == pytest.approx(1)
                   for n in mesh['normals'])

