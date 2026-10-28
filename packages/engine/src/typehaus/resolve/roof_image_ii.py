"""Image II roof pieces drawn from their published sections (→ Residential Design Manual 5/2024).

A roof whose covering is the Image II kit takes its eave and rake from the catalog pieces'
``section_in`` (:mod:`typehaus.library.trim._image_ii`), in place of the derived drip edge and
the custom rake face. Only the **wrapped** edges qualify: an edge with a fascia board keeps the
fascia drip, because the 1-1/2 in Extended Eave face cannot hang over a 5-1/2 in board. The
gate is the roofing material's ``roof_edge_trim_kit`` (decision #57), not the roof's tag.

Each piece is a :class:`FramedMember` whose ``section_ring`` is the section thickened by the
sheet, the same primitive ``folded_section_mesh`` sweeps for the walls. It rides ``roof.members``
so the takeoff, the FORTIFIED drip grade and the IFC read it where they read every roof edge.
"""

from __future__ import annotations

import math

from typehaus.library.trim._image_ii import (
    COBRA_VENT_IN,
    IMAGE_II_EXTENDED_EAVE,
    IMAGE_II_RESIDENTIAL_RAKE,
    IMAGE_II_RIDGE_COVER,
)
from typehaus.library.trim.profile import TrimProfile
from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.model.trim import EaveTrim
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M, _inset_section
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_drip_edge import deck_top_m
from typehaus.resolve.roof_edge_geometry import (
    EdgeRun,
    abutted_run_keys,
    mating_faces,
    mitred_span,
    roof_edge_runs,
    roof_slope,
)
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

#: The roofing material's marker for the Image II eave and rake kit (``roof_edge_trim_kit``).
IMAGE_II_KIT = "IMAGE_II"
#: Crown lift of the vented ridge above the roofing: the Cobra vent block (PIM p. 20).
VENTED_RIDGE_LIFT_M = inch(COBRA_VENT_IN).meters
EAVE_KEY = "image-ii-eave"
RAKE_KEY = "image-ii-rake"
CONNECTION_EAVE = "roof:image-ii-eave"
CONNECTION_RAKE = "roof:image-ii-rake"
#: The rake's bottom sits this far below the BBD75 wall head, hiding the 3/4 in Universal Closure.
RAKE_BELOW_HEAD_M = inch(1.0).meters


def _roofing(model: ResolvedModel, roof: ResolvedRoof):
    """(layers above the structure, roofing layer, roofing material) for ``roof``."""
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    cladding = next((layer for layer in reversed(layers)
                     if layer.function is LayerFunction.CLADDING), None)
    material = model.plan.library.material(cladding.material_ref) if cladding else None
    return layers, cladding, material


def _eave_trim(model: ResolvedModel, roof: ResolvedRoof) -> EaveTrim | None:
    element = model.plan.by_tag(roof.tag)
    return element.eave_trim if isinstance(element, Roof) else None


def image_ii_covering(model: ResolvedModel, roof: ResolvedRoof) -> bool:
    _, _, material = _roofing(model, roof)
    return material is not None and material.roof_edge_trim_kit == IMAGE_II_KIT


def wrapped_image_ii_edges(model: ResolvedModel, roof: ResolvedRoof) -> frozenset[str]:
    """The fascia-free edge names of an Image II roof. An abutted run among them takes no piece."""
    if not image_ii_covering(model, roof):
        return frozenset()
    trim = _eave_trim(model, roof)
    fascia = bool(trim is not None and trim.fascia)
    return frozenset(
        run.edge_name for run in roof_edge_runs(roof)
        if not (fascia and (not trim.fascia_edges or run.edge_name in trim.fascia_edges)))


def image_ii_cover_ring(slope: float, profile=IMAGE_II_RIDGE_COVER,
                        ) -> tuple[tuple[float, float], ...]:
    """A ridge cover's section (across, up) about its crown, legs at the roof slope.

    The section's legs lie flat in ``_image_ii`` and pivot about the crown to the pitch, the
    same rotation the eave flange takes. The apex sits at the crown, so the caller offsets it.
    """
    angle = math.atan(abs(slope))
    rotated = []
    for x, y in profile.section_in:
        phi = angle if x < 0 else -angle if x > 0 else 0.0
        rotated.append(_rotate(x, y, phi))
    return tuple((u * M_PER_IN, z * M_PER_IN) for u, z in rotated)


def _rotate(x: float, y: float, phi: float) -> tuple[float, float]:
    return (x * math.cos(phi) - y * math.sin(phi), x * math.sin(phi) + y * math.cos(phi))


def _section_points(profile: TrimProfile, origin_u: float, origin_z: float,
                    pitch: float) -> list[tuple[float, float]]:
    """The section placed on the edge: x outboard of ``origin_u``, z up from ``origin_z``.

    An eave flange (the block inboard of the bend) pivots to the roof's pitch; a rake section
    is vertical, so ``pitch`` is zero for it.
    """
    points = []
    for x, y in profile.section_in:
        if x < 0.0 and pitch:
            x, y = _rotate(x, y, -pitch)
        points.append((origin_u + x * M_PER_IN, origin_z + y * M_PER_IN))
    return points


def thickened_ring(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The open section as a closed ring: its centreline, then the sheet's inner face back."""
    inset = _inset_section(points, SHEET_24_GA_M)
    return [*points, *reversed(inset)]


def _piece_member(roof: ResolvedRoof, run: EdgeRun, span, ring, key: str, connection: str,
                  material: str | None) -> FramedMember:
    """A catalog piece on ``run``: its ring in the run's (outward, up) frame, mitred at ``span``."""
    us = [u for u, _ in ring]
    zs = [z for _, z in ring]
    u_lo, u_hi, z_lo, z_hi = min(us), max(us), min(zs), max(zs)
    center = (u_lo + u_hi) / 2.0
    nx, ny = run.normal
    a = (span.p0[0] + nx * center, span.p0[1] + ny * center)
    b = (span.p1[0] + nx * center, span.p1[1] + ny * center)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    # The ring's frame is the run's LEFT normal; ``u`` is outward, so flip where they differ.
    sign = 1.0 if (-(b[1] - a[1]) * nx + (b[0] - a[0]) * ny) >= 0.0 else -1.0
    return FramedMember(
        parent_uid=roof.uid, child_key=f"{run.key}-{key}", category="drip_edge",
        profile=panel_profile((u_hi - u_lo) / M_PER_IN, (z_hi - z_lo) / M_PER_IN),
        p0=a, p1=b, z0_m=span.z0_m + z_lo, z1_m=span.z0_m + z_hi, length_m=length,
        z0_end_m=span.z1_m + z_lo, z1_end_m=span.z1_m + z_hi,
        connection=connection, material=material,
        section_ring=tuple(((u - center) * sign, z - z_lo) for u, z in ring),
    )


def image_ii_members(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    """The Extended Eave on each wrapped eave and the Residential Rake on each wrapped rake."""
    edges = wrapped_image_ii_edges(model, roof)
    if not edges:
        return ()
    abutted = abutted_run_keys(model, roof)
    layers, cladding, material = _roofing(model, roof)
    element = model.plan.by_tag(roof.tag)
    coil = getattr(element, "edge_trim_material", None) or cladding.material_ref
    slope = roof_slope(roof)
    factor = math.hypot(1.0, slope)
    head = mating_faces(layers).cladding_under * factor
    deck_top = deck_top_m(layers, factor)
    members: list[FramedMember] = []
    for run in roof_edge_runs(roof):
        if run.edge_name not in edges or run.key in abutted:
            continue
        # The bend and the rake leg sit on the roof edge, outside the deck's setback; the
        # flange runs inboard over the deck.
        origin_u = 0.0
        if run.is_eave:
            # The flange lies on the deck (its bend at the deck top); the face hangs over the head.
            points = _section_points(IMAGE_II_EXTENDED_EAVE, origin_u, deck_top,
                                     math.atan(abs(slope)))
            key, connection = EAVE_KEY, CONNECTION_EAVE
        else:
            # Anchored at the wall head, not the roof: the bottom sits RAKE_BELOW_HEAD_M under it.
            points = _section_points(IMAGE_II_RESIDENTIAL_RAKE, origin_u,
                                     head - RAKE_BELOW_HEAD_M, 0.0)
            key, connection = RAKE_KEY, CONNECTION_RAKE
        ring = thickened_ring(points)
        us = [u for u, _ in ring]
        span = mitred_span(run, -max(us), -min(us))
        if span is None:
            continue
        members.append(_piece_member(roof, run, span, ring, key, connection, coil))
    return tuple(members)
