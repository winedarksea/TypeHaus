"""Derived ridge caps and their profile closures."""
import math

from typehaus.model.enums import LayerFunction
from typehaus.model.spatial import Roof
from typehaus.quantities import M_PER_IN, inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_edge_geometry import roof_ridge_run, roof_slope
from typehaus.resolve.roof_layer_setbacks import above_structure_layers
from typehaus.resolve.roof_panel_trim import (
    CLOSURE_FLANGE_M,
    panel_profile_for_layer,
    ridge_panel_closures,
)

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
    closures = ()
    cap_ring = None
    if profile and not (vented_attic or vented_over_deck):
        roof_material = model.plan.library.material(cladding.material_ref)
        image_ii_cover = (roof_material is not None and
                          roof_material.roof_ridge_trim_profile == "IMAGE_II_RIDGE_COVER")
        half = inch(_RIDGE_CAP_HALF_WIDTH_IN).meters
        if image_ii_cover:
            half = inch(_IMAGE_II_RIDGE_SLOPE_LENGTH_IN).meters / slope_factor
        closures = ridge_panel_closures(roof, profile,
                    sum(layer.thickness.meters for layer in layers)-cladding.thickness.meters,
                    material, offset_m=(half - CLOSURE_FLANGE_M
                                        if image_ii_cover else half))
        sheet = profile.sheet_thickness_m
        if image_ii_cover:
            # The catalog's 7 inches measures along each pitched side, not in plan.
            # Seat the cover on the profile-cut closure's crown at either side.
            bottom = z0 - half * slope
            top = z0 + sheet
        rise = (z0 if image_ii_cover else top) - bottom
        cap_ring = ((-half, 0.), (0., rise), (half, 0.),
                    (half, sheet), (0., rise + sheet), (-half, sheet))
    return closures + (FramedMember(
        parent_uid=roof.uid, child_key="ridge-vent-cap", category="ridge_cap",
        profile=panel_profile((2.0 * half / M_PER_IN if cap_ring else
                               2.0 * _RIDGE_CAP_HALF_WIDTH_IN), (top - bottom) / M_PER_IN),
        p0=ridge.p0, p1=ridge.p1, z0_m=bottom, z1_m=top, length_m=length,
        connection=("ridge:vented-cap" if vented_attic or vented_over_deck
                    else "ridge:closed-cap"),
        material=material, section_ring=cap_ring,
    ),)
