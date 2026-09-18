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


#: The five legs of a riser, in order, as ``(uid suffix, tag suffix, is horizontal)``. The
#: polyline :func:`riser_polylines` returns has one segment per entry, and a leg the vent
#: does not have — the jog, on a riser that authors none — is degenerate rather than absent,
#: so the roles line up by index whatever the vent looks like.
RISER_LEGS = (("riser", "CHASE", False), ("jog", "JOG", True),
              ("riser2", "CHASE2", False), ("out", "OUT", True),
              ("term", "TERM", False))


def riser_polylines(model: ResolvedModel, vent: VentRun
                    ) -> list[tuple[str, tuple[tuple[float, float], ...], tuple[float, ...]]]:
    """Each bundled system's riser as ``(tag, plan path, per-vertex z)``.

    **One derivation, two readers.** :func:`typehaus.resolve.accessories._resolve_vent`
    builds its ``ResolvedSolid``s from this and ``resolve/mep_envelopes`` builds the
    envelope from it, so what the viewer draws and what an interference check or a router
    obstacle sees are the same pipe. They were not: a ``VentRun`` resolved only to solids,
    so ``mep.run_interference`` could not grade it and ``routing/obstacles`` would happily
    lane a duct through the radon riser.

    The tag is ``{vent tag}-{system}``, which is the stem the solids already carry, so a
    finding names what the viewer shows.

    Six vertices, five segments, in :data:`RISER_LEGS` order: up the chase, the optional
    in-building jog, the rest of the rise at the jogged station, out through the wall, and
    up the siding to 12" above the roof. Returns ``[]`` when no termination is derivable —
    a riser whose top is unknown is not a placed run, and guessing one would put a solid
    where the building has none.
    """
    from typehaus.resolve.round_solids import PIPE_BUNDLE_SPACING

    chase = vent.chase_position.xy_m
    top = chase_top_point(vent)
    exit_point = exterior_riser_point(vent)
    offset_x, offset_y = vent.exit_offset.xy_m
    z_start, z_exit = vent.start_elevation.meters, vent.exit_elevation.meters
    z_jog = (vent.chase_offset_elevation.meters
             if vent.chase_offset is not None and vent.chase_offset_elevation is not None
             else z_exit)
    derived_top = derived_termination_elevation(model, vent)
    z_top = (derived_top if derived_top is not None
             else vent.roof_termination_elevation.meters
             if vent.roof_termination_elevation is not None else None)
    if z_top is None:
        return []

    # Parallel risers, one per bundled system, spread perpendicular to the LONGEST
    # horizontal leg — the in-building jog where there is one, the wall exit otherwise.
    #
    # **It used to be perpendicular to the wall exit always, and on catlin that put two 3"
    # pipes on ONE line for 8'-7 1/2".** The riser jogs east and exits north, so no single
    # axis is perpendicular to both legs and one of them must lose; losing the short one is
    # the only defensible choice. Two pipes cannot share a bore through a joist web, and the
    # jog is the leg that crosses them. It also drove the pair 2 2/5" east of its own
    # station and into W-A-BA-E's studs — a 3" bore in a 2x4, which is what
    # ``mep.run_through_stud`` reported the moment a VentRun gained an envelope.
    #
    # The short leg's two risers are still collinear, and ``mep.run_interference`` exempts
    # them as one authored element rather than pretending otherwise.
    jog_x, jog_y = top[0] - chase[0], top[1] - chase[1]
    lead_x, lead_y = ((jog_x, jog_y) if max(abs(jog_x), abs(jog_y)) > 1e-9
                      else (offset_x, offset_y))
    perp_x = abs(lead_y) >= abs(lead_x)
    count = max(len(vent.systems), 1)
    out = []
    for index, system in enumerate(vent.systems or (None,)):
        spread = (index - (count - 1) / 2.0) * vent.diameter.meters * PIPE_BUNDLE_SPACING
        dx, dy = (spread, 0.0) if perp_x else (0.0, spread)
        here, there, out_there = ((chase[0] + dx, chase[1] + dy),
                                  (top[0] + dx, top[1] + dy),
                                  (exit_point[0] + dx, exit_point[1] + dy))
        name = system.value if system is not None else "vent"
        path = (here, here, there, there, out_there, out_there)
        z = (z_start, z_jog, z_jog, z_exit, z_exit, z_top)
        out.append((f"{vent.tag}-{name}", path, z))
    return out
