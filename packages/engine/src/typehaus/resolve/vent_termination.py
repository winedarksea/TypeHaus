"""Derive where a vent riser terminates above the roof it clears.

One derivation, two consumers: :mod:`typehaus.resolve.accessories` builds the exterior
riser from it, and the ``mep.vent_termination_height`` check validates any hand-authored
``VentRun.roof_termination_elevation`` against it.  Nothing else may re-derive the number —
a second copy is how the authored 33' riser drifted 6 ft above its own 4:12 roof.

IRC P3103.1 sets a 6" minimum above the roof surface; TypeHaus terminates at 12", the
cold-climate practice value that keeps the terminal clear of drifted snow at the rake.
"""

from __future__ import annotations

from shapely.geometry import Point, Polygon

from typehaus.model.mep import VentRun
from typehaus.model.refs import ToRoof
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, ResolvedRoof
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

VENT_TERMINATION_CLEARANCE_M = inch(12).meters


def chase_top_point(vent: VentRun) -> tuple[float, float]:
    """Plan location the riser rises at above its optional in-building jog.

    The chase itself when there is no jog; the jogged station when there is one. Everything
    above the jog — the wall exit,
    the exterior riser, the termination and its separation from openings — is measured from
    here rather than from the chase, because that is where the pipe actually is.
    """
    chase_x, chase_y = vent.chase_position.xy_m
    if vent.chase_offset is None or vent.chase_offset_elevation is None:
        return chase_x, chase_y
    jog_x, jog_y = vent.chase_offset.xy_m
    return chase_x + jog_x, chase_y + jog_y


def exterior_riser_point(vent: VentRun) -> tuple[float, float]:
    """Plan location of the riser leg that runs up the siding, past the roof edge."""
    top_x, top_y = chase_top_point(vent)
    offset_x, offset_y = vent.exit_offset.xy_m
    return top_x + offset_x, top_y + offset_y


def roof_cleared_by(model: ResolvedModel, vent: VentRun) -> ResolvedRoof | None:
    """The roof whose plane the riser has to clear, or ``None`` when it is not derivable.

    Preferred link is the authored ``wall_ref``: a riser clamped to a gable wall clears the
    roof that wall frames to, and — with a zero-overhang rake — that riser sits *outside*
    every roof footprint, so a plan-containment test alone would find nothing.  Walls with
    a flat top (knee walls, storeys below the roof) carry no such link, so fall back to the
    roof that actually covers the riser in plan, and only when exactly one does.
    """
    wall = model.plan.by_tag(vent.wall_ref) if vent.wall_ref is not None else None
    wall_top = getattr(wall, "top", None)
    if isinstance(wall_top, ToRoof):
        named = next((roof for roof in model.roofs if roof.tag == wall_top.roof_ref), None)
        if named is not None:
            return named
    riser = Point(exterior_riser_point(vent))
    covering = [roof for roof in model.roofs if Polygon(roof.footprint).covers(riser)]
    return covering[0] if len(covering) == 1 else None


def derived_termination_elevation(model: ResolvedModel, vent: VentRun) -> float | None:
    """Project-frame Z (m) 12" above the true roof surface at the exterior riser's point.

    ``roof_height_at`` returns the structural deck plane, not the weather surface — the
    insulation, furring and standing-seam roofing above it (``above_structure_layers``) add
    real height a riser has to clear, the same "skin" offset ``resolve/solar.py`` rides the
    PV standoff off of. ``roof_height_at`` extrapolates its rake line past the footprint
    edge, which is exactly what a riser standing proud of a zero-overhang gable needs.
    Returns ``None`` when no roof is derivable, leaving the caller to fall back to the
    authored elevation.
    """
    roof = roof_cleared_by(model, vent)
    if roof is None:
        return None
    library = getattr(model.plan, "library", None)
    assembly = library.resolve_assembly(roof.assembly) if library is not None else None
    skin_m = (sum(layer.thickness.meters for layer in above_structure_layers(assembly))
              if assembly is not None else 0.0)
    return roof_height_at(roof, exterior_riser_point(vent)) + skin_m + VENT_TERMINATION_CLEARANCE_M
