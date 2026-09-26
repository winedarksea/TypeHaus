"""The overhung eave (catlin's garage): leaders only, over the real trim the cut draws.

Fascia, soffit, formed drip edge and K-gutter are all derived roof members, so the section
already cuts every one of them; this overlay only names them, anchored on what was drawn.
"""

from __future__ import annotations

from typehaus.emit.draw.detail_components.eave import eave_frame
from typehaus.emit.draw.detail_components.eave_labels import (
    eave_labels,
    member_anchor,
    roof_labels,
)
from typehaus.emit.draw.scene import IRNode


def overhang_eave(model, wall, crop, direction, station, scale=None) -> list[IRNode]:
    """Name the drip edge, metal fascia over its nailer, vented soffit and hung gutter."""
    frame = eave_frame(model, wall, direction, station) if crop is not None else None
    if frame is None:
        return []
    roof, clad_out, junction_z, out_sign, slope = frame
    at = (roof, direction, station, clad_out, junction_z)
    trim = getattr(model.plan.by_tag(roof.tag), "eave_trim", None) if roof else None
    vented = trim is not None and trim.soffit_vented
    gutter = trim.gutter if trim is not None else None
    width = f'{gutter.thickness.inches:g}" ' if gutter is not None else ""
    outer = len(trim.fascia) - 1 if trim is not None and trim.fascia else 0
    entries = roof_labels(model, roof, clad_out, junction_z, out_sign, slope) + [
        (member_anchor(*at, "drip_edge", "-flange"),
         "formed drip edge: flange ON the deck, membrane laps OVER it"),
        (member_anchor(*at, "drip_edge", "-face"),
         "drip edge face over the metal fascia, kick into the gutter"),
        (member_anchor(*at, "fascia", f"-fascia-{outer}"),
         "metal fascia over the wood nailer" if outer else "fascia"),
        (member_anchor(*at, "soffit"),
         "vented soffit — the attic's intake" if vented else "soffit"),
        (member_anchor(*at, "gutter"), f"{width}hung gutter, back sheet BEHIND the drip edge"),
    ]
    return eave_labels(entries, clad_out, junction_z, out_sign, scale)
