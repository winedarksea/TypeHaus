"""The formed drip edge: one pitched piece of metal per roof edge (``EaveTrim.drip_edge``).

A flange lying on the deck at the roof's pitch, a bend over the deck edge, a face down over
the wall panel heads (a wrapped edge) or the metal fascia (an overhung one), and a kick out
into the gutter. Each leg is a ``FramedMember`` carrying its true ``section_ring``, so the
3D model, the IFC and every section cut draw the same shape; the box fields only bound it.

Two callers in :mod:`typehaus.resolve.roof_trim`:

* **wrapped** (continuous standing-seam skin, no fascia) — the piece REPLACES the corner
  trim on its edge, keeping that trim's face plane and leg so the gutter under it stays put;
* **fascia** (an overhung eave/rake) — the piece laps over the outermost fascia board, its
  face stopping at the gutter rim on a guttered eave.

Mitring: the flange runs corner to corner; the nose, face and kick run past the corner on
the eave and stop at the eave piece's inner face on the rake, so the two tile the corner.
"""

from __future__ import annotations

import math

from typehaus.model.enums import LayerFunction
from typehaus.model.trim import EaveDripEdge, EaveTrim
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedRoof
from typehaus.resolve.roof_edge_geometry import EdgeRun, MitredSpan, mitred_span
from typehaus.resolve.trim_bands import GUTTER_SHELL_M, Quad, formed_drip_legs

CATEGORY = "drip_edge"
CONNECTION = "roof:drip-edge"
# How far the face drops over the fascia on an edge with no gutter rim to stop at.
_DEFAULT_FACE_DROP_M = inch(1.5).meters


def drip_spec(trim: EaveTrim | None, run: EdgeRun) -> EaveDripEdge | None:
    """The drip-edge declaration covering ``run``, or ``None``."""
    spec = trim.drip_edge if trim is not None else None
    if spec is None or (spec.edges and run.edge_name not in spec.edges):
        return None
    return spec


def deck_top_m(layers, slope_factor: float) -> float:
    """Vertical height of the sheathing's top face over the roof plane (what the flange sits on)."""
    total = top = 0.0
    for layer in layers:
        total += layer.thickness.meters
        if layer.function is LayerFunction.SHEATHING:
            top = total
    return top * slope_factor


def deck_edge_m(roof: ResolvedRoof, layers, run: EdgeRun) -> float:
    """Where the deck ends, as ``u`` outboard of the footprint edge (negative = set back)."""
    names = {layer.name for layer in layers if layer.function is LayerFunction.SHEATHING}
    for entry in roof.layer_edge_setbacks or ():
        if entry.get("layer") in names:
            return -float(entry.get(run.edge_name, 0.0))
    return 0.0


def wrapped_drip_edge(
    roof: ResolvedRoof, run: EdgeRun, spec: EaveDripEdge, *, slope: float,
    deck_top: float, bend: float, nose_floor: float, face_in: float, face_bottom: float,
    shell: float, material: str | None,
) -> tuple[FramedMember, ...]:
    """The piece on a wrapped edge: face and leg where the corner trim's were."""
    legs = formed_drip_legs(
        slope=slope if run.is_eave else 0.0, deck_top_at_edge_m=deck_top,
        flange_back_m=bend - spec.flange.meters, bend_m=bend, nose_floor_m=nose_floor,
        face_in_m=face_in, face_bottom_m=face_bottom, kick_m=spec.kick.meters, shell_m=shell)
    return drip_members(roof, run, legs, spec.material or material)


def fascia_drip_edge(
    roof: ResolvedRoof, run: EdgeRun, spec: EaveDripEdge, trim: EaveTrim, *, slope: float,
    deck_top: float, bend: float, fascia_outer: float, fascia_rise: float,
    material: str | None,
) -> tuple[FramedMember, ...]:
    """The piece over an overhung edge's fascia; on a guttered eave, into the trough."""
    nose_floor = fascia_rise if trim.fascia else deck_top
    gutter = trim.gutter
    guttered = (gutter is not None and run.is_eave
                and (not gutter.edges or run.edge_name in gutter.edges))
    kick_in = None
    if guttered:
        # The face stops at the rim; the kick starts past the back sheet, which stands
        # behind the drip rather than through it.
        face_bottom = -gutter.top_drop.meters
        back = min(GUTTER_SHELL_M, gutter.thickness.meters / 3.0, gutter.depth.meters / 3.0)
        kick_in = fascia_outer + back
    else:
        drop = spec.face_drop.meters if spec.face_drop is not None else _DEFAULT_FACE_DROP_M
        face_bottom = nose_floor - drop
    legs = formed_drip_legs(
        slope=slope if run.is_eave else 0.0, deck_top_at_edge_m=deck_top,
        flange_back_m=bend - spec.flange.meters, bend_m=bend, nose_floor_m=nose_floor,
        face_in_m=fascia_outer, face_bottom_m=face_bottom, kick_m=spec.kick.meters,
        kick_in_m=kick_in)
    return drip_members(roof, run, legs, spec.material or material)


def drip_members(roof: ResolvedRoof, run: EdgeRun, legs: dict[str, Quad],
                 material: str | None) -> tuple[FramedMember, ...]:
    """The four legs as swept members, mitred so eave and rake pieces tile each corner."""
    face_in = min(u for u, _ in legs["face"])
    face_out = max(u for u, _ in legs["nose"])
    bend = min(u for u, _ in legs["nose"])
    outer = max(u for leg in ("face", "kick") for u, _ in legs[leg])
    spans = {
        "flange": mitred_span(run, 0.0, 0.0),
        "nose": mitred_span(run, -face_out, -bend),
        "face": mitred_span(run, -outer, -face_in),
        "kick": mitred_span(run, -outer, -face_in),
    }
    members: list[FramedMember] = []
    for leg, quad in legs.items():
        span = spans[leg]
        if span is not None:
            members.append(_leg_member(roof, run, leg, quad, span, material))
    return tuple(members)


def _leg_member(roof: ResolvedRoof, run: EdgeRun, leg: str, quad: Quad, span: MitredSpan,
                material: str | None) -> FramedMember:
    us = [u for u, _ in quad]
    zs = [z for _, z in quad]
    u_lo, u_hi, z_lo, z_hi = min(us), max(us), min(zs), max(zs)
    center = (u_lo + u_hi) / 2.0
    nx, ny = run.normal
    a = (span.p0[0] + nx * center, span.p0[1] + ny * center)
    b = (span.p1[0] + nx * center, span.p1[1] + ny * center)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    # The ring's frame is the run's LEFT normal; ``u`` is outward, so flip where they differ.
    sign = 1.0 if (-(b[1] - a[1]) * nx + (b[0] - a[0]) * ny) >= 0.0 else -1.0
    ring = tuple(((u - center) * sign, z - z_lo) for u, z in quad)
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-drip-edge-{leg}", category=CATEGORY,
        profile=panel_profile((u_hi - u_lo) / M_PER_IN, (z_hi - z_lo) / M_PER_IN),
        p0=a, p1=b, z0_m=span.z0_m + z_lo, z1_m=span.z0_m + z_hi, length_m=length,
        z0_end_m=span.z1_m + z_lo, z1_end_m=span.z1_m + z_hi,
        connection=CONNECTION, material=material, section_ring=ring,
    )


def flange_on_deck_m(member: FramedMember) -> float:
    """How far a flange leg's ring runs on the deck, in plan — what FORTIFIED §4.5 grades."""
    ring = member.section_ring or ()
    if not ring:
        return 0.0
    return max(s for s, _ in ring) - min(s for s, _ in ring)
