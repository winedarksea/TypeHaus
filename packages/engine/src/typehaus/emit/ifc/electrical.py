"""IFC emission for electrical raceways — kept out of emitter.py (already over the
500-line budget; → emit/ifc/roof.py precedent for a discipline module).

One ``IfcCableCarrierSegment`` (PredefinedType CONDUITSEGMENT) per horizontal plan
segment, plus one vertical segment at the run's last point when the end elevations
differ — the same geometry contract the resolver's developed length is computed from.
Conduits stay out of the diff adapter's scope, matching pipes and ducts (route geometry
is not reconciled with an architect's IFC; devices are).
"""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid, derive_guid
from typehaus.resolve.geometry import rect_between
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874015748
_MIN_RISE_M = 0.05  # a rise smaller than this is drawn flat


def emit_conduits(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                  project_uuid: Any, assign_representation) -> None:
    for run in model.conduits:
        _emit_conduit_run(f, body, run, storeys, project_uuid, assign_representation)


def emit_solar_panels(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                      project_uuid: Any, assign_representation) -> None:
    """One ``IfcSolarDevice`` (SOLARPANEL) per module, as the resolver's tilted box.

    The faceted shell reuses the resolved corner rings directly — bottom reversed so
    every face winds outward, the same closed-box contract as emit/ifc/roof.py."""
    for panel in model.solar_panels:
        bottom = [tuple(point) for point in panel.corners_bottom]
        top = [tuple(point) for point in panel.corners_top]
        faces: list[list[tuple[float, ...]]] = [list(reversed(bottom)), list(top)]
        for index in range(len(bottom)):
            following = (index + 1) % len(bottom)
            faces.append([bottom[index], bottom[following], top[following], top[index]])
        element = ll.create_entity(f, "IfcSolarDevice", name=panel.tag)
        element.PredefinedType = "SOLARPANEL"
        element.GlobalId = derive_guid(project_uuid, panel.uid)
        assign_representation(f, element, ll.add_faceted_solids(f, body, [faces]))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": panel.uid, "tag": panel.tag})
        ll.ensure_pset(f, element, "TypeHaus_Solar", {
            "watts": panel.watts, "product": panel.product, "roof_ref": panel.roof_ref,
        })
        ll.assign_container(f, element, storeys[panel.storey])


def _emit_conduit_run(f: Any, body: Any, run: Any, storeys: dict[str, Any],
                      project_uuid: Any, assign_representation) -> None:
    half = run.trade_size_m / 2.0
    z_flat = run.z_start_m if run.z_start_m is not None else 0.0
    segments: list[tuple[str, Any]] = []
    for index in range(len(run.path) - 1):
        p0, p1 = run.path[index], run.path[index + 1]
        if ((p1[0] - p0[0]) ** 2 + (p1[1] - p0[1]) ** 2) ** 0.5 < 1e-6:
            continue
        profile = rect_between(p0, p1, -half, half)
        segments.append((f"seg-{index:02d}",
                         (profile, run.trade_size_m, z_flat - half)))
    if (run.z_start_m is not None and run.z_end_m is not None
            and abs(run.z_end_m - run.z_start_m) > _MIN_RISE_M):
        x, y = run.path[-1]
        profile = [(x - half, y - half), (x + half, y - half),
                   (x + half, y + half), (x - half, y + half)]
        z0, z1 = sorted((run.z_start_m, run.z_end_m))
        segments.append(("riser", (profile, z1 - z0, z0)))
    for child_key, (profile, height, z0) in segments:
        element = ll.create_entity(f, "IfcCableCarrierSegment",
                                   name=f"{run.tag}/{child_key}")
        element.PredefinedType = "CONDUITSEGMENT"
        element.GlobalId = derive_child_guid(project_uuid, run.uid, child_key)
        assign_representation(f, element, ll.add_prism_from_profile(
            f, body, profile, height, z0,
        ))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": run.uid, "tag": run.tag})
        ll.ensure_pset(f, element, "TypeHaus_Conduit", {
            "trade_size_in": run.trade_size_m * _M_TO_IN,
            "from_ref": run.from_ref or "", "to_ref": run.to_ref or "",
            "length_ft": run.length_m * 3.280839895013123,
        })
        ll.assign_container(f, element, storeys[run.storey])
