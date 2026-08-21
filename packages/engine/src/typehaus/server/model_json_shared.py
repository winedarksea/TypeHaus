"""The primitives every model.json domain serializer shares.

A provenance badge, a framed member, a wall layer, a finding, an enum — the five shapes
that recur across walls, roofs, floors, stairs and the catalog. They live here rather than
in any one domain module because the payload's whole value is that a member serialized for
a wall and a member serialized for a stair are byte-for-byte the same shape: the 3D panel
picks them with one reader. A second copy of :func:`_member_json` would be a second
contract.
"""

from __future__ import annotations

from typing import Any

from typehaus.findings import Finding
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.source.provenance import Provenance


def _provenance(prov: Provenance | None, tag: str) -> dict[str, Any] | None:
    if prov is None:
        return None
    loc = prov.location(tag)
    if loc is None:
        return None
    # editable=False marks runtime-captured (params-generated) authorship: the badge is
    # a read-only "defined here" pointer, never a writeback destination.
    return {"file": loc.file, "line": loc.line, "editable": prov.is_editable(tag)}


def _member_json(m: FramedMember) -> dict[str, Any]:
    """The one member serialization every trade (walls/roofs/floors/stairs) shares.

    The UI never parses ``profile`` strings — this is the only place that calls
    :func:`cross_section`, so every consumer gets ``shape``/``width_m``/``depth_m``
    (and i-joist flange/web dims) pre-resolved.

    ``key`` is the member's identity: unique within its parent (wall/roof/floor/stair), so
    ``<parent uid>/<key>`` names one member stably across rebuilds. The 3D panel's per-member
    picking addresses studs that way rather than by draw-call index, which would shift the
    moment the framer re-lays a wall. ``length_m`` is the resolver's own run length — a raked
    rafter's true sloped length, which p0/p1 alone cannot give the client.
    """
    section = cross_section(m.profile)
    return {
        "key": m.child_key, "category": m.category, "profile": m.profile,
        "p0": list(m.p0), "p1": list(m.p1), "z0_m": m.z0_m, "z1_m": m.z1_m,
        "length_m": m.length_m,
        "z0_end_m": m.z0_end_m, "z1_end_m": m.z1_end_m,
        "plan_outline": [list(point) for point in m.plan_outline] if m.plan_outline else None,
        "riser_line": [list(point) for point in m.riser_line] if m.riser_line else None,
        "shape": section.shape, "width_m": section.width_m, "depth_m": section.depth_m,
        "flange_width_m": section.flange_width_m,
        "flange_thickness_m": section.flange_thickness_m,
        "web_thickness_m": section.web_thickness_m, "plies": section.plies,
        "orient": list(m.orient) if m.orient is not None else None,
        "connection": m.connection,
        "material": m.material,
        # Explicit visibility trade override (fascia is trim *and* framing); ``None`` leaves
        # the consumer on its category-derived default.
        "trade": m.trade,
    }


def _layer_json(layer) -> dict[str, Any]:
    """One resolved layer, including its band when it has one.

    ``z0_m``/``z1_m`` are ``Layer.extent`` resolved to absolute elevations — null on the
    full-height layers that are almost all of them. The viewer needs them for the same
    reason the glTF emitter and the takeoff do: a banded layer covers part of the wall,
    and drawing it full height puts a protection panel over nine feet of buried foam, or
    stacks three brick colours on top of each other in one place.
    """
    return {"name": layer.name, "material": layer.material_ref, "function": layer.function,
            "thickness_m": layer.thickness_m, "polygon": [list(point) for point in layer.polygon],
            "control": sorted(layer.control),
            "is_cavity": layer.is_cavity, "cavity_host": layer.cavity_host,
            "z0_m": layer.z0_m, "z1_m": layer.z1_m}


def _findings_json(findings: list[Finding] | None) -> list[dict[str, Any]]:
    return [f.model_dump(mode="json") for f in (findings or [])]


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value
