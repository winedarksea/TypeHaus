"""The model.json document itself: its header, its assembly order, and its writers.

Every other ``model_json_*`` module answers "how is one domain serialized"; this one
answers "what is a model.json". It owns the envelope fields (revision, content hash, units),
the project/site preamble, the building-science rollup, and — the load-bearing part — the
*order* the domain fragments are spread in, which is the wire contract
``ui/src/model/types.ts`` is checked against.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from typehaus.checks.registry import Preferences
from typehaus.findings import Finding
from typehaus.model.canvas import resolved_canvas_objects
from typehaus.resolve import site_earth
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_catalog import catalog_json
from typehaus.server.model_json_fabric import framing_json, shell_json, wall_graph_json
from typehaus.server.model_json_placeables import placeables_json
from typehaus.server.model_json_shared import _findings_json, _provenance
from typehaus.server.model_json_spaces import spaces_json
from typehaus.server.model_json_systems import systems_json
from typehaus.source.provenance import Provenance

if TYPE_CHECKING:
    from typehaus.diff.variants import VariantSpec


def _document_header(
    model: ResolvedModel,
    *,
    revision: str,
    content_hash: str,
    provenance: Provenance | None,
    findings: list[Finding] | None,
    preferences: Preferences | None,
) -> dict[str, Any]:
    """The payload preamble: revision/hash/units plus the project, site and storey frame."""
    return {
        # revision is the PATCH /plan precondition (#30); UI echoes it back on every op.
        "revision": revision,
        # Stable across server restarts unlike `revision` (a fresh uuid per process) — the
        # signal `npm run shots` needs to tell "the house changed" from "the server restarted".
        "contentHash": content_hash,
        "units": "imperial",
        "canvas_objects": resolved_canvas_objects(
            model, lambda tag: _provenance(provenance, tag)
        ),
        "projectNorth": model.plan.project.site.true_north.degrees,
        "findings": _findings_json(findings),
        "project": {
            "name": model.plan.project.name,
            "uuid": str(model.plan.project.project_uuid),
            "active_code_profile": model.plan.project.active_code_profile,
            "default_view_pan": list(model.plan.project.default_view_pan),
        },
        "site": {
            "lat": model.plan.project.site.lat,
            "lon": model.plan.project.site.lon,
            "true_north_deg": model.plan.project.site.true_north.degrees,
            "grade_m": (model.plan.project.site.grade.meters
                        if model.plan.project.site.grade is not None else None),
            "parcel": [list(point.xy_m) for point in model.plan.project.site.parcel],
            # Holes the site earth sheet must carry: one merged ring per excavated
            # footprint (house, garage, sunken garden). Derived once in
            # resolve/site_earth.py so the viewer, the IFC lot slab, and any future earth
            # emitter cut the same rings instead of each re-deriving them from rooms —
            # room-derived cuts can only ever see one storey of one structure.
            "earth_voids": [[list(point) for point in ring]
                            for ring in site_earth.earth_plane_void_rings(model)],
            # Spot elevations are currently consumed by 2D site/elevation emitters. Keep
            # them in the shared UI contract so a future earth surface can triangulate the
            # same authored grade data without inventing a second source of truth.
            "spot_elevations": [
                {"position": list(spot.position.xy_m), "elevation_m": spot.elevation.meters}
                for spot in model.plan.project.site.spot_elevations
            ],
        },
        "underlays": [
            {"path": item.path, "storey": item.storey, "origin_x_m": item.origin_x_m,
             "origin_y_m": item.origin_y_m, "width_m": item.width_m, "height_m": item.height_m,
             "rotation_deg": item.rotation_deg, "opacity": item.opacity,
             # Encode '../' rather than letting the browser normalize a reference path before
             # it reaches the deliberately sandboxed /underlay route.
             "url": "/underlay/" + quote(item.path, safe="")}
            for item in (preferences.underlays if preferences is not None else ())
        ],
        "storeys": [
            {"tag": s.tag, "elevation_m": s.elevation.meters,
             "ceiling_m": s.default_ceiling_height.meters}
            for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)
        ],
    }


def _building_science(
    model: ResolvedModel, preferences: Preferences | None
) -> dict[str, Any] | None:
    """The three advisory physics reports, or None when no preferences are loaded.

    Gated on ``preferences`` because every one of them needs an authored envelope target or
    setpoint; without those the honest payload is absence, not a report over defaults.
    """
    if preferences is None:
        return None
    from typehaus.checks.building_science.condensation import analyze_assembly
    from typehaus.checks.building_science.wwr import analyze_wwr
    from typehaus.energy import estimate_block_load

    heating = model.plan.project.site.design_temp_heating
    return {
        "wwr": [item.as_dict() for item in analyze_wwr(model)],
        "energy": estimate_block_load(model, preferences).as_dict(),
        "condensation": [
            analyze_assembly(
                assembly, model.plan.library,
                heating_design_temp_f=heating.fahrenheit if heating else None,
                preferences=preferences,
            ).as_dict()
            for assembly in model.plan.library.assemblies
        ],
    }


def model_to_dict(
    model: ResolvedModel,
    *,
    revision: str = "",
    content_hash: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
    preferences: Preferences | None = None,
    variants: Sequence[VariantSpec] | None = None,
) -> dict[str, Any]:
    """The whole UI contract, composed from the per-domain serializers.

    The spread order below *is* the emitted key order. Fragments are spread at the points
    the monolith emitted them, so re-splitting a domain later cannot silently reorder the
    payload out from under ``test_every_payload_key_has_a_ui_type``.
    """
    return {
        **_document_header(
            model, revision=revision, content_hash=content_hash, provenance=provenance,
            findings=findings, preferences=preferences,
        ),
        **wall_graph_json(model, provenance),
        **placeables_json(model, provenance),
        **shell_json(model, provenance),
        **systems_json(model, provenance, preferences),
        **framing_json(model, provenance),
        **spaces_json(model, provenance),
        "building_science": _building_science(model, preferences),
        **catalog_json(model, provenance, variants),
    }


def preview_to_dict(model: ResolvedModel) -> dict[str, Any]:
    """A minimal geometry payload for a live drag preview (→ Phase 4): just wall axes,
    opening placements, and room outlines — no layers/members/checks/catalog, so the
    reduced-resolve win isn't spent again re-serializing fields a ghost overlay never
    draws. Not the model.json contract; a preview client discards this once the drag ends
    and the next ``GET /model`` (post the real ``PATCH /plan``) lands."""
    return {
        "walls": [
            {"tag": w.tag, "storey": w.storey, "axis": [list(w.axis[0]), list(w.axis[1])]}
            for w in sorted(model.walls, key=lambda x: x.uid)
        ],
        "openings": [
            {"tag": o.tag, "host": o.host_wall, "kind": o.kind, "is_door": o.is_door,
             "width_m": o.width_m, "center_along_m": o.center_along_m}
            for o in model.openings
        ],
        "rooms": [
            {"tag": r.tag, "storey": r.storey, "area_m2": r.area_m2,
             "clear_face": [list(p) for p in r.clear_face]}
            for r in model.rooms
        ],
    }


def write_model_json(
    model: ResolvedModel,
    path: Path,
    *,
    revision: str = "",
    content_hash: str = "",
    provenance: Provenance | None = None,
    findings: list[Finding] | None = None,
    preferences: Preferences | None = None,
    variants: Sequence[VariantSpec] | None = None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = model_to_dict(
        model, revision=revision, content_hash=content_hash, provenance=provenance,
        findings=findings, preferences=preferences, variants=variants,
    )
    # sort_keys for byte-determinism (→ 02 §Determinism).
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path
