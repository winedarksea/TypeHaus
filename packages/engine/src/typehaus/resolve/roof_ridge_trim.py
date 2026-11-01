"""Derived ridge caps and their profile closures."""
import math

from typehaus.library.trim._image_ii import (
    PROFILE_VENT_CLIP_LENGTH_IN,
    PROFILE_VENT_SETBACK_IN,
)
from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.metal_skin_profiles import SHEET_24_GA_M
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_edge_geometry import abutted_run_keys, roof_ridge_run, roof_slope
from typehaus.resolve.roof_image_ii import edge_member, image_ii_cover_ring, thickened_ring
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.roof_panel_trim import (
    CLOSURE_FLANGE_M,
    panel_profile_for_layer,
    ridge_panel_closures,
)

#: The material key for the RDM p. 41 vented peak under a 7 in ridge cover (both slopes).
VENTED_PEAK_KIT = "IMAGE_II_VENTED_PEAK"
PROFILE_VENT_CONNECTION = "ridge:profile-vent"
END_CLOSURE_CONNECTION = "ridge:end-closure"

_RIDGE_CAP_HALF_WIDTH_IN = 6.0
_RIDGE_CAP_STAND_IN = 2.0
_IMAGE_II_RIDGE_SLOPE_LENGTH_IN = 7.0

# --- vented ridge cap --------------------------------------------------------------------

def ridge_vent_members(model: ResolvedModel, roof: ResolvedRoof) -> tuple[FramedMember, ...]:
    """The ridge cap along a gable's ridge — vented where the roof breathes through it.

    **Every gable with a covering gets one.** Two slopes meet at the peak in an open joint
    and something has to close it; whether that closure also VENTS is a separate question,
    answered by ``connection`` (``ridge:vented-cap`` against ``ridge:closed-cap``) and not by
    whether the piece exists — an unvented ridge must still get a cap, or an open ridge on a
    standing-seam roof goes unreported in the model and the bill.

    Vented is still the common case and the two constructions that reach it both appear on
    catlin: a vented attic (the garage — its vented soffits feed the truss space, which
    exhausts through a slot cut at the ridge), and an over-deck vent channel (the furring/
    batten gap between the foam and the standing seam runs eave to ridge and exhausts at the
    top). Either way the cap is a formed metal member riding the roofing surface, centred on
    the ridge line. A truss roof has no ridge beam, so everything keys off
    ``ResolvedRoof.ridge_z_m`` — the plane's own peak — never off a framing member.

    A roof that is neither vented NOR clad is the one case that still returns nothing, and it
    is earned rather than assumed: there is no slot to vent and no covering for a cap to
    close over, and a "ridge cap" on a bare deck would be trim on a roof nobody has finished.

    "Formed" is composed rather than swept: see ``_RIDGE_CAP_BANDS``. Every band keeps the
    ``ridge_cap`` category, the ``ridge:vented-cap`` connection and the roofing's own
    material, so the IFC covering map, the glTF skin routing and the viewer's material
    lookup all key off the cap exactly as they did when it was one box.
    """
    ridge = roof_ridge_run(roof)
    if ridge is None:
        return ()
    element = model.plan.by_tag(roof.tag)
    trim = element.eave_trim if isinstance(element, Roof) else None
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    vented_attic = trim is not None and trim.soffit_vented
    vented_over_deck = any(
        layer.function in (LayerFunction.AIRGAP, LayerFunction.FURRING) for layer in layers)
    cladding = next((layer for layer in reversed(layers)
                     if layer.function is LayerFunction.CLADDING), None)
    if not (vented_attic or vented_over_deck or cladding is not None):
        return ()
    # The cap sits on the roofing's top surface at the peak: the stack is offset
    # perpendicular to the slope, so its vertical height over the ridge is slope-corrected.
    slope_factor = math.hypot(1.0, roof_slope(roof))
    stack = sum(layer.thickness.meters for layer in layers) * slope_factor
    z0 = ridge.z_m + stack
    slope = abs(roof_slope(roof))
    length = math.hypot(ridge.p1[0] - ridge.p0[0], ridge.p1[1] - ridge.p0[1])
    material = cladding.material_ref if cladding is not None else "aluminum"
    # The cap is formed trim, so it follows the roof's trim coil when one is named — the ridge
    # is part of the same outline the rake trim draws, and a light cap inside a dark edge reads
    # as a mistake rather than as a choice.
    material = getattr(element, "edge_trim_material", None) or material
    # The plane falls away from the peak, so the cap's underside is set by its outer edges.
    bottom = z0 - inch(_RIDGE_CAP_HALF_WIDTH_IN).meters * slope
    top = z0 + inch(_RIDGE_CAP_STAND_IN).meters
    profile = panel_profile_for_layer(model, cladding)
    roof_material = model.plan.library.material(cladding.material_ref) if cladding else None
    ridge_kit = roof_material.roof_ridge_trim_profile if roof_material else None
    vented_peak = ridge_kit == VENTED_PEAK_KIT
    connection = "ridge:vented-cap" if vented_attic or vented_over_deck else "ridge:closed-cap"
    closures = ()
    cap_ring = None
    width_in = 2.0 * _RIDGE_CAP_HALF_WIDTH_IN
    if profile and (vented_peak or not (vented_attic or vented_over_deck)):
        half = inch(_RIDGE_CAP_HALF_WIDTH_IN).meters
        image_ii_cover = ridge_kit in ("IMAGE_II_RIDGE_COVER", VENTED_PEAK_KIT)
        if image_ii_cover:
            half = inch(_IMAGE_II_RIDGE_SLOPE_LENGTH_IN).meters / slope_factor
        base = sum(layer.thickness.meters for layer in layers) - cladding.thickness.meters
        if vented_peak:
            # RDM p. 41: Profile Vent and its clips stand where the closed ridge's Z-closures do.
            closures = _profile_vents(roof, ridge, z0, half, slope, slope_factor, profile)
            connection = "ridge:vented-peak"
        else:
            # Lazy: roof_panel_skin reaches emit, which reaches this resolver.
            from typehaus.resolve.roof_panel_skin import seam_anchor

            closures = ridge_panel_closures(
                roof, profile, base, material, anchor=seam_anchor(model, roof),
                offset_m=half - CLOSURE_FLANGE_M if image_ii_cover else half)
        sheet = profile.sheet_thickness_m
        if image_ii_cover:
            # The catalog cover, drawn from its section: 7 in legs at the pitch, apex on the
            # closure's crown (the sheet's top surface).
            ring = thickened_ring([(u, z + sheet) for u, z in image_ii_cover_ring(slope)])
            low = min(z for _, z in ring)
            bottom, top = z0 + low, z0 + max(z for _, z in ring)
            cap_ring = tuple((u, z - low) for u, z in ring)
            width_in = 2.0 * half / M_PER_IN
        else:
            rise = top - bottom
            cap_ring = ((-half, 0.), (0., rise), (half, 0.),
                        (half, sheet), (0., rise + sheet), (-half, sheet))
            width_in = 2.0 * half / M_PER_IN
    cap = FramedMember(
        parent_uid=roof.uid, child_key="ridge-vent-cap", category="ridge_cap",
        profile=panel_profile(width_in, (top - bottom) / M_PER_IN),
        p0=ridge.p0, p1=ridge.p1, z0_m=bottom, z1_m=top, length_m=length,
        connection=connection, material=material, section_ring=cap_ring,
    )
    return closures + (cap,) + _end_closures(model, roof, cap)


def _left_normal(ridge) -> tuple[float, float]:
    dx, dy = ridge.p1[0] - ridge.p0[0], ridge.p1[1] - ridge.p0[1]
    run = math.hypot(dx, dy)
    return (-dy / run, dx / run)


def _profile_vents(roof, ridge, z0, half, slope, factor, profile) -> tuple[FramedMember, ...]:
    """Profile Vent on each slope, pan to rib top, its low edge set back of the cover's hem.

    ``z0`` is the rib top over the ridge line; the vent is notched to the ribs, so between them
    it stands the rib's depth, and the clip (1 in, ``PROFILE_VENT_CLIP_LENGTH_IN``) bears on it.
    """
    outer = half - inch(PROFILE_VENT_SETBACK_IN).meters / factor
    inner = outer - inch(PROFILE_VENT_CLIP_LENGTH_IN).meters / factor
    depth = profile.depth_m * factor
    members = []
    for side, sign in (("left", 1.0), ("right", -1.0)):
        ring = [(sign * u, z) for u, z in ((inner, -slope * inner - depth),
                                            (outer, -slope * outer - depth),
                                            (outer, -slope * outer), (inner, -slope * inner))]
        members.append(edge_member(
            roof.uid, f"ridge-vent-{side}", "ridge_closure", ridge.p0, ridge.p1, z0, z0,
            _left_normal(ridge), ring, PROFILE_VENT_CONNECTION, "roof-vent-mat"))
    return tuple(members)


def _end_closures(model, roof, cap) -> tuple[FramedMember, ...]:
    """A flat closure in each open gable end of the cover, the cover's own section filled.

    Metal Sales prints no gable-end piece (52111XX is the hip end cap), so it is field-formed
    from the cover's coil. An end another roof carries the ridge on across stays open.
    """
    if cap.section_ring is None:
        return ()
    abutted = abutted_run_keys(model, roof)
    ring = tuple(cap.section_ring[: len(cap.section_ring) // 2])
    run = math.dist(cap.p0, cap.p1)
    ux, uy = (cap.p1[0] - cap.p0[0]) / run, (cap.p1[1] - cap.p0[1]) / run
    sheet = SHEET_24_GA_M
    members = []
    for end, point, step in (("lo", cap.p0, 1.0), ("hi", cap.p1, -1.0)):
        if any(key.startswith(f"rake-{end}") for key in abutted):
            continue
        a = point
        b = (point[0] + ux * step * sheet, point[1] + uy * step * sheet)
        a, b = (a, b) if step > 0 else (b, a)
        members.append(FramedMember(
            parent_uid=roof.uid, child_key=f"ridge-end-closure-{end}", category="ridge_closure",
            profile=cap.profile, p0=a, p1=b, z0_m=cap.z0_m, z1_m=cap.z1_m, length_m=sheet,
            connection=END_CLOSURE_CONNECTION, material=cap.material, section_ring=ring))
    return tuple(members)
