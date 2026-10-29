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

from shapely.geometry import Polygon, box

from typehaus.library.trim._image_ii import (
    COBRA_VENT_IN,
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
from typehaus.resolve.roof_edge_geometry import (
    EdgeRun,
    MitredSpan,
    abutted_run_keys,
    mating_faces,
    mitred_span,
    roof_edge_runs,
    roof_slope,
)
from typehaus.resolve.roof_image_ii_eave import LAP_GAP_M, eave_stack
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

#: The roofing material's marker for the Image II eave and rake kit (``roof_edge_trim_kit``).
IMAGE_II_KIT = "IMAGE_II"
#: Crown lift of the vented ridge above the roofing: the Cobra vent block (PIM p. 20).
VENTED_RIDGE_LIFT_M = inch(COBRA_VENT_IN).meters
EAVE_KEY = "image-ii-eave"
RAKE_KEY = "image-ii-rake"
CONNECTION_EAVE = "roof:image-ii-eave"
CONNECTION_RAKE = "roof:image-ii-rake"
RAKE_FOOT_KEY = "image-ii-rake-foot"
CONNECTION_RAKE_FOOT = "roof:image-ii-rake-foot"
STRIP_KEY = "eave-strip-in"
CONNECTION_STRIP = "roof:eave-strip-in"
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


def _section_points(profile: TrimProfile, origin_u: float,
                    origin_z: float) -> list[tuple[float, float]]:
    """A section placed as drawn: x outboard of ``origin_u``, z up from ``origin_z``."""
    return [(origin_u + x * M_PER_IN, origin_z + y * M_PER_IN) for x, y in profile.section_in]


def thickened_ring(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """The open section as a closed ring: its centreline, then the sheet's inner face back."""
    inset = _inset_section(points, SHEET_24_GA_M)
    return [*points, *reversed(inset)]


def edge_member(parent_uid: str, child_key: str, category: str, a, b, z_a: float, z_b: float,
                normal: tuple[float, float], ring, connection: str,
                material: str | None) -> FramedMember:
    """A ring swept from ``a`` to ``b``: ``u`` along ``normal`` from that line, ``z`` above
    ``z_a``/``z_b``. The box fields bound the ring, centred on it."""
    us = [u for u, _ in ring]
    zs = [z for _, z in ring]
    u_lo, u_hi, z_lo, z_hi = min(us), max(us), min(zs), max(zs)
    center = (u_lo + u_hi) / 2.0
    nx, ny = normal
    a = (a[0] + nx * center, a[1] + ny * center)
    b = (b[0] + nx * center, b[1] + ny * center)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    # The ring's frame is the run's LEFT normal; ``u`` runs along ``normal``: flip if they differ.
    sign = 1.0 if (-(b[1] - a[1]) * nx + (b[0] - a[0]) * ny) >= 0.0 else -1.0
    return FramedMember(
        parent_uid=parent_uid, child_key=child_key, category=category,
        profile=panel_profile((u_hi - u_lo) / M_PER_IN, (z_hi - z_lo) / M_PER_IN),
        p0=a, p1=b, z0_m=z_a + z_lo, z1_m=z_a + z_hi, length_m=length,
        z0_end_m=z_b + z_lo, z1_end_m=z_b + z_hi,
        connection=connection, material=material,
        section_ring=tuple(((u - center) * sign, z - z_lo) for u, z in ring),
    )


def _piece_member(roof: ResolvedRoof, run: EdgeRun, span, ring, key: str, connection: str,
                  material: str | None) -> FramedMember:
    """A catalog piece on ``run``: its ring in the run's (outward, up) frame, cut at ``span``."""
    return edge_member(roof.uid, f"{run.key}-{key}", "drip_edge", span.p0, span.p1,
                       span.z0_m, span.z1_m, run.normal, ring, connection, material)


def _along_run(run: EdgeRun, d0: float, d1: float) -> MitredSpan:
    """The stretch of ``run`` between ``d0`` and ``d1`` measured inboard from its corner end."""
    dx, dy = run.p1[0] - run.p0[0], run.p1[1] - run.p0[1]
    length = math.hypot(dx, dy)

    def at(distance: float):
        f = distance / length if run.corner_at_p0 else 1.0 - distance / length
        return ((run.p0[0] + dx * f, run.p0[1] + dy * f), run.z0_m + (run.z1_m - run.z0_m) * f)

    (p0, z0), (p1, z1) = at(d0), at(d1)
    if not run.corner_at_p0:
        (p0, z0), (p1, z1) = (p1, z1), (p0, z0)
    return MitredSpan(p0, z0, p1, z1)


def _rake_foot_ring(ring, floor_z: float) -> list[tuple[float, float]] | None:
    """The rake's section above ``floor_z``: what stands over the eave leg at the corner."""
    clipped = Polygon(ring).buffer(0).intersection(box(-1.0, floor_z, 1.0, 1.0))
    if clipped.is_empty or clipped.geom_type != "Polygon":
        return None
    return [(float(u), float(z)) for u, z in list(clipped.exterior.coords)[:-1]]


def image_ii_members(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    """The Extended Eave and strip-in on each wrapped eave, the Residential Rake on each rake.

    At a corner the eave runs through to the rake's outer face, and the rake stops on top of
    the eave's leg (a foot over the leg, the full rake upslope of its hem), so the rake sheds
    onto the eave rather than mitring against an unlike section.
    """
    edges = wrapped_image_ii_edges(model, roof)
    if not edges:
        return ()
    abutted = abutted_run_keys(model, roof)
    layers, cladding, _ = _roofing(model, roof)
    element = model.plan.by_tag(roof.tag)
    coil = getattr(element, "edge_trim_material", None) or cladding.material_ref
    stack = eave_stack(model, roof)
    factor = math.hypot(1.0, roof_slope(roof))
    head = mating_faces(layers).cladding_under * factor
    runs = [run for run in roof_edge_runs(roof)
            if run.edge_name in edges and run.key not in abutted]
    # The rake's leg stands its own sheet clear of the gable panel, like the eave's face.
    rake = thickened_ring(_section_points(IMAGE_II_RESIDENTIAL_RAKE, LAP_GAP_M + SHEET_24_GA_M,
                                          head - RAKE_BELOW_HEAD_M))
    eave = thickened_ring(stack.eave_section())
    rakes = any(not run.is_eave for run in runs)
    eaves = any(run.is_eave for run in runs)
    members: list[FramedMember] = []
    for run in runs:
        if run.is_eave:
            reach = max(u for u, _ in (rake if rakes else eave))
            span = mitred_span(run, -reach, -min(u for u, _ in eave))
            if span is None:
                continue
            members.append(_piece_member(roof, run, span, eave, EAVE_KEY, CONNECTION_EAVE, coil))
            strip = _strip_span(roof, run, stack.strip_layer)
            if strip is not None and stack.strip_thickness_m > 0.0:
                members.append(edge_member(
                    roof.uid, f"{run.key}-{STRIP_KEY}", "membrane", strip.p0, strip.p1,
                    strip.z0_m, strip.z1_m, run.normal, stack.strip_ring(), CONNECTION_STRIP,
                    stack.strip_material))
            continue
        if not eaves:
            span = mitred_span(run, -max(u for u, _ in rake), -min(u for u, _ in rake))
            if span is not None:
                members.append(_piece_member(roof, run, span, rake, RAKE_KEY, CONNECTION_RAKE,
                                             coil))
            continue
        # Upslope of the eave's hem the full section; over the leg, only what clears it.
        clear = -min(u for u, _ in eave) + LAP_GAP_M
        length = math.hypot(run.p1[0] - run.p0[0], run.p1[1] - run.p0[1])
        if clear >= length:
            continue
        main = _along_run(run, clear, length)
        members.append(_piece_member(roof, run, main, rake, RAKE_KEY, CONNECTION_RAKE, coil))
        foot = _rake_foot_ring(rake, (stack.eave_top_w + LAP_GAP_M) * factor)
        if foot is not None:
            span = _along_run(run, -max(u for u, _ in eave), clear)
            members.append(_piece_member(roof, run, span, foot, RAKE_FOOT_KEY,
                                         CONNECTION_RAKE_FOOT, coil))
    return tuple(members)


def _strip_span(roof: ResolvedRoof, run: EdgeRun, layer: str | None):
    """The strip-in's run along the eave: the field membrane's own extent at each rake."""
    setbacks = {entry["layer"]: entry for entry in (roof.layer_edge_setbacks or ())}
    membrane = setbacks.get(layer)
    if membrane is None:
        return mitred_span(run, 0.0, 0.0)
    rake_names = {"north", "south"} if roof.ridge_direction == "y" else {"east", "west"}
    inset = max(float(membrane.get(name, 0.0)) for name in rake_names)
    return mitred_span(run, inset, inset)
