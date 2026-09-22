"""The plants as glTF instances: one shared mesh per prototype, one light node per plant.

Mirrors ``ui/src/three/builders/plants.ts``: the same prototypes (``resolve/plant_models``),
the same role colours, the same base-to-tip shade (``COLOR_0``, 0.7 at the root to 1.0 at
the top). A two-sided part (a blade, a leaf) is emitted twice, the second copy reversed with
negated normals, so every plant material stays OPAQUE and single-sided.
"""

from __future__ import annotations

import math

from typehaus.emit.gltf.geometry import _to_gltf
from typehaus.emit.gltf.palette import _hex_rgba
from typehaus.emit.trade_rules import solid_trades
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.plant_models import role_colors

SHADE_BASE = 0.7
_KIND = "solid"


def plant_instance_uids(model: ResolvedModel) -> set[str]:
    """Uids of the plant solids an instance draws in their place."""
    return {p.uid for p in model.plants if p.model_ref in model.plant_models}


def _primitives(proto, colors: dict[str, str]):
    out = []
    for part in proto.parts:
        positions = [_to_gltf(*p) for p in part.positions]
        normals = [_to_gltf(*n) for n in part.normals]
        shade = [SHADE_BASE + (1.0 - SHADE_BASE) * s for s in proto.shade(part)]
        tint = [(s, s, s) for s in shade]
        indices = [i for tri in part.triangles for i in tri]
        if part.two_sided:
            n = len(positions)
            indices += [i + n for a, b, c in part.triangles for i in (a, c, b)]
            positions = positions + positions
            normals = normals + [(-x, -y, -z) for x, y, z in normals]
            tint = tint + tint
        out.append((_hex_rgba(colors.get(part.role, colors["foliage"])), positions, normals,
                    tint, indices))
    return out


def add_plants(scene, model: ResolvedModel) -> None:
    types = {t.tag: t for t in model.plan.library.plant_types}
    materials = {m.tag: m for m in model.plan.library.materials}
    for plant in sorted(model.plants, key=lambda p: p.uid):
        proto = model.plant_models.get(plant.model_ref)
        ptype = types.get(plant.type_ref)
        if proto is None or ptype is None:
            continue
        if not scene.has_shared_mesh(proto.ref) and not scene.add_shared_mesh(
                proto.ref, _primitives(proto, role_colors(ptype, materials))):
            continue
        x, y = plant.position
        half = plant.rotation_rad / 2.0
        sx, sy, sz = plant.scale
        # A turn about plan z is a turn about glTF +Y by the same angle; plan (sx, sy, sz)
        # is glTF (sx, sz, sy).
        rotation = (0.0, math.sin(half), 0.0, math.cos(half))
        scene.add_instance(proto.ref, _to_gltf(x, y, plant.ground_z_m), rotation, (sx, sz, sy),
                           solid_trades("plant", ptype.foliage_material), _KIND, plant.uid)
