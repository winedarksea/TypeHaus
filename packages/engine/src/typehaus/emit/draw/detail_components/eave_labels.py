"""Leaders naming the eave water chain, each anchored on the piece the cut actually drew.

Anchors are read back off the geometry: the roof's derived members (drip edge, gutter,
fascia, soffit) sliced through the same ``member_solid`` the section draws, plus any authored
gutter solids. A label for a piece the cut does not pass through is dropped, never guessed.
"""

from __future__ import annotations

from typehaus.emit.draw.annotate import LabelSpec, dodge, place_column, wrap_label
from typehaus.emit.draw.scene import IRNode, Leader, NamedPoint
from typehaus.emit.draw.typography import TEXT_PT
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import CutPlane, slice_solid
from typehaus.resolve.roof_layer_setbacks import assembly_layer_spans, structure_datum_m

# How far from the eave a piece may sit and still be this eave's: across the cut, from the
# wall's cladding face (an overhang reaches ~2'), and up/down from the roof plane (rejects a
# different storey's flashing or gutter on the same wall line).
_REACH_U_IN = 30.0
_REACH_Z_IN = 36.0

Anchor = tuple[float, float]


def above_structure_bands(model, roof) -> list:
    """``(layer, z_lo_in, z_hi_in)`` for every layer outboard of the roof's structure,
    measured up from ``roof_height_at`` — the top of the structure, not of the roofing.
    Empty when the roof has no framed structure layer to measure from."""
    if roof is None:
        return []
    asm = model.plan.library.resolve_assembly(roof.assembly)
    spans = assembly_layer_spans(asm)
    if not any(layer.function.value == "structure" for (layer, _lo, _hi) in spans):
        return []
    base = structure_datum_m(asm)
    return [(layer, (lo - base) / M_PER_IN, (hi - base) / M_PER_IN)
            for (layer, lo, hi) in spans if lo >= base - 1e-9]


def _near(points, clad_out: float, junction_z: float) -> bool:
    us = [u for u, _ in points]
    zs = [z for _, z in points]
    return (min(abs(min(us) - clad_out), abs(max(us) - clad_out)) <= _REACH_U_IN
            and min(abs(min(zs) - junction_z), abs(max(zs) - junction_z)) <= _REACH_Z_IN)


def _centre(points) -> Anchor | None:
    if not points:
        return None
    us = [u for u, _ in points]
    zs = [z for _, z in points]
    return ((min(us) + max(us)) / 2.0, (min(zs) + max(zs)) / 2.0)


def member_anchor(roof, direction: str, station: float, clad_out: float, junction_z: float,
                  category: str, leg: str | None = None) -> Anchor | None:
    """Centre of the roof's ``category`` members this cut passes through, near the eave."""
    if roof is None:
        return None
    plane = CutPlane(axis=direction, station_m=station)
    points: list[Anchor] = []
    for member in roof.members:
        if member.category != category or (leg and not member.child_key.endswith(leg)):
            continue
        solid = member_solid(member)
        if solid is None:
            continue
        for profile in slice_solid(solid, plane):
            cut = [(u / M_PER_IN, z / M_PER_IN) for u, z in profile.outline]
            if _near(cut, clad_out, junction_z):
                points += cut
    return _centre(points)


def solid_anchor(model, direction: str, station: float, clad_out: float,
                 junction_z: float, category: str) -> Anchor | None:
    """Centre of the authored ``category`` solids crossing this station, near the eave."""
    axis, cross = (0, 1) if direction == "x" else (1, 0)
    points: list[Anchor] = []
    for solid in model.solids:
        if solid.category != category:
            continue
        along = [p[cross] / M_PER_IN for p in solid.outline]
        if not min(along) <= station / M_PER_IN <= max(along):
            continue
        across = [p[axis] / M_PER_IN for p in solid.outline]
        box = [(min(across), solid.z0_m / M_PER_IN), (max(across), solid.z1_m / M_PER_IN)]
        if _near(box, clad_out, junction_z):
            points += box
    return _centre(points)


def roof_labels(model, roof, clad_out: float, junction_z: float, out_sign: float,
                slope: float) -> list[tuple[Anchor, str]]:
    """The roofing and vent-mat leaders, only for layers the roof actually has."""
    bands = {layer.function.value: (lo, hi)
             for (layer, lo, hi) in above_structure_bands(model, roof)}

    def mid(function: str) -> float:
        lo, hi = bands[function]
        return junction_z + (lo + hi) / 2.0 * slope

    entries: list[tuple[Anchor, str]] = []
    if "cladding" in bands:
        entries.append(((clad_out - out_sign * 6.0, mid("cladding")),
                        "standing seam on concealed floating clips"))
    if "airgap" in bands:
        entries.append(((clad_out - out_sign * 3.0, mid("airgap")),
                        "vent mat intake, insect screened — the roof's only outward "
                        "drying path"))
    return entries


def eave_labels(entries, clad_out: float, junction_z: float, out_sign: float,
                scale=None) -> list[IRNode]:
    """Stack the leaders in one column outboard of the outermost piece they name.

    The chain is a *lap order* — deck, drip edge, underlayment over the drip, metal, gutter
    back behind the drip — and a lap order not written on the piece it applies to is the thing
    that gets built backwards.
    """
    live = [(target, text) for target, text in entries if target is not None]
    if not live:
        return []
    reach = max((out_sign * (u - clad_out) for (u, _z), _text in live), default=0.0)
    column = clad_out + out_sign * max(15.0, reach + 4.0)
    top = max(z for (_u, z), _text in live)
    specs = [LabelSpec(text=wrap_label(text), target=target) for target, text in live]
    placed = place_column(specs, x=column, z_top=max(top, junction_z) + 1.0, step_pt=14.0,
                          height_pt=TEXT_PT, scale=scale,
                          align="left" if out_sign > 0 else "right")
    return [Leader(anchor=NamedPoint(xy=label.spec.target), at=label.at,
                   to=label.spec.target, text=label.spec.text, height_pt=label.height_pt)
            for label in dodge(placed, scale=scale)]
