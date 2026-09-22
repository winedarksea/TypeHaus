"""model.json's plants: the procedural prototypes once, then one light record per plant.

The viewer instances each prototype part (``ui/src/three/builders/plants.ts``); a plant's
bounding solid still rides in ``solids`` under the same uid, as its pick record. Normals are
not shipped: the viewer derives the same area-weighted ones the GLB carries
(``resolve/plant_models.vertex_normals``).
"""

from __future__ import annotations

from typing import Any

from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.plant_models import QUANTUM, role_colors


def _r(value: float, ndigits: int = 4) -> float:
    return round(value, ndigits) + 0.0


def plants_json(model: ResolvedModel) -> dict[str, Any]:
    types = {t.tag: t for t in model.plan.library.plant_types}
    materials = {m.tag: m for m in model.plan.library.materials}
    prototypes = []
    for ref, proto in sorted(model.plant_models.items()):
        ptype = types.get(proto.type_ref)
        prototypes.append({
            "ref": ref, "type_ref": proto.type_ref, "form": proto.form,
            "height": _r(proto.height),
            # Positions are integers of ``quantum``: exact, since a model is built rounded.
            "quantum": QUANTUM,
            "colors": role_colors(ptype, materials) if ptype is not None else {},
            "parts": [{"role": part.role, "two_sided": part.two_sided,
                       "positions": [round(c / QUANTUM) for p in part.positions for c in p],
                       "indices": [i for t in part.triangles for i in t]}
                      for part in proto.parts],
        })
    plants = [
        {"uid": p.uid, "tag": p.tag, "storey": p.storey, "type_ref": p.type_ref,
         "model": p.model_ref, "x": _r(p.position[0]), "y": _r(p.position[1]),
         "z": _r(p.ground_z_m), "rotation": _r(p.rotation_rad),
         "scale": [_r(s) for s in p.scale], "source": p.source_ref, "accent": p.accent}
        for p in sorted(model.plants, key=lambda item: item.uid) if p.model_ref
    ]
    return {"plant_models": prototypes, "plants": plants}
