"""model.json — the UI contract (→ 20 §model.json). Emitted from the ResolvedModel.

Carries resolved wall layer polygons, framed members, rooms, openings, and derived
conditions in canonical SI meters; element uid/tag ride along for pick → provenance.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from typehaus.findings import Finding
from typehaus.resolve.model import ResolvedModel
from typehaus.source.provenance import Provenance


def _provenance(prov: Provenance | None, tag: str) -> dict[str, Any] | None:
    if prov is None:
        return None
    loc = prov.location(tag)
    return {"file": loc.file, "line": loc.line} if loc is not None else None


def _findings_json(findings: list[Finding] | None) -> list[dict[str, Any]]:
    return [f.model_dump(mode="json") for f in (findings or [])]


def model_to_dict(
    model: ResolvedModel,
    *,
    revision: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
) -> dict[str, Any]:
    return {
        # revision is the PATCH /plan precondition (#30); UI echoes it back on every op.
        "revision": revision,
        "units": "imperial",
        "projectNorth": 0.0,
        "findings": _findings_json(findings),
        "project": {
            "name": model.plan.project.name,
            "uuid": str(model.plan.project.project_uuid),
        },
        "storeys": [
            {"tag": s.tag, "elevation_m": s.elevation.meters,
             "ceiling_m": s.default_ceiling_height.meters}
            for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)
        ],
        "walls": [
            {
                "uid": w.uid, "tag": w.tag, "storey": w.storey, "assembly": w.assembly,
                "provenance": _provenance(provenance, w.tag),
                "axis": [list(w.axis[0]), list(w.axis[1])],
                "z0_m": w.z0_m, "z1_m": w.z1_m, "is_foundation": w.is_foundation,
                "layers": [
                    {"name": ly.name, "function": ly.function, "material": ly.material_ref,
                     "thickness_m": ly.thickness_m, "polygon": [list(p) for p in ly.polygon],
                     "control": sorted(ly.control)}
                    for ly in w.layers
                ],
                "members": [
                    {"key": m.child_key, "category": m.category, "profile": m.profile,
                     "p0": list(m.p0), "p1": list(m.p1), "z0_m": m.z0_m, "z1_m": m.z1_m}
                    for m in w.members
                ],
            }
            for w in sorted(model.walls, key=lambda x: x.uid)
        ],
        "openings": [
            {"uid": o.uid, "tag": o.tag, "host": o.host_wall, "is_door": o.is_door,
             "provenance": _provenance(provenance, o.tag),
             "width_m": o.width_m, "height_m": o.height_m, "sill_m": o.sill_m,
             "center_along_m": o.center_along_m}
            for o in model.openings
        ],
        "rooms": [
            {"uid": r.uid, "tag": r.tag, "storey": r.storey, "occupancy": r.occupancy,
             "provenance": _provenance(provenance, r.tag),
             "conditioned": r.conditioned, "area_m2": r.area_m2,
             "clear_face": [list(p) for p in r.clear_face], "floor_finish": r.floor_finish}
            for r in model.rooms
        ],
        "conditions": [
            {"kind": c.kind.value, "key": c.key, "elements": list(c.element_tags)}
            for c in model.conditions
        ],
        "stack_edges": [
            {"lower": e.lower_wall, "upper": e.upper_wall, "overlap_m": e.overlap_m,
             "width_change": e.width_change}
            for e in model.stack_edges
        ],
    }


def write_model_json(
    model: ResolvedModel,
    path: Path,
    *,
    revision: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = model_to_dict(
        model, revision=revision, provenance=provenance, findings=findings
    )
    # sort_keys for byte-determinism (→ 02 §Determinism).
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path
