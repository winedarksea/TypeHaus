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


def derived_termination_elevation(model: ResolvedModel, vent: VentRun,
                                  at: tuple[float, float] | None = None) -> float | None:
    """Project-frame Z (m) 12" above the true roof surface at the exterior riser's point.

    ``roof_height_at`` returns the structural deck plane, not the weather surface — the
    insulation, furring and standing-seam roofing above it (``above_structure_layers``) add
    real height a riser has to clear, the same "skin" offset ``resolve/solar.py`` rides the
    PV standoff off of. ``roof_height_at`` extrapolates its rake line past the footprint
    edge, which is exactly what a riser standing proud of a zero-overhang gable needs.
    Returns ``None`` when no roof is derivable, leaving the caller to fall back to the
    authored elevation. ``at`` measures at one bundled pipe instead of the bundle's centre:
    on a rake the pair stands at two roof heights.
    """
    roof = roof_cleared_by(model, vent)
    if roof is None:
        return None
    library = getattr(model.plan, "library", None)
    assembly = library.resolve_assembly(roof.assembly) if library is not None else None
    skin_m = (sum(layer.thickness.meters for layer in above_structure_layers(assembly))
              if assembly is not None else 0.0)
    point = at if at is not None else exterior_riser_point(vent)
    return roof_height_at(roof, point) + skin_m + VENT_TERMINATION_CLEARANCE_M


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
    centre_top = derived_termination_elevation(model, vent)
    if centre_top is None and vent.roof_termination_elevation is None:
        return []

    # Parallel risers, one per bundled system. **Each horizontal leg spreads the pair across
    # ITSELF**, and at the turn each pipe's corner is where its two offset lines meet — two
    # lanes round a bend, never crossing. A single spread axis cannot do this: catlin jogs
    # east and exits north, and one axis put the pair on ONE line for whichever leg lost —
    # first 8'-7 1/2" through joist webs, then the exit, where the two pipes shared a bore
    # through W-A-N2 and stood one behind the other on the siding, reading as one.
    jog = (top[0] - chase[0], top[1] - chase[1])
    has_jog = max(abs(jog[0]), abs(jog[1])) > 1e-9
    has_exit = max(abs(offset_x), abs(offset_y)) > 1e-9
    lead = jog if has_jog else (offset_x, offset_y)
    # The lead leg's spread axis keeps its historical sign (+x or +y) so index 0 stays where
    # the house authored it; the exit's normal follows with the same handedness.
    n1 = (1.0, 0.0) if abs(lead[1]) >= abs(lead[0]) else (0.0, 1.0)
    n2, corner_t = n1, 0.0
    if has_jog and has_exit:
        d1, d2 = _unit(jog), _unit((offset_x, offset_y))
        hand = 1.0 if d1[0] * n1[1] - d1[1] * n1[0] > 0 else -1.0   # n1 left (+1) or right
        n2 = (-d2[1] * hand, d2[0] * hand)
        along = d1[0] * n2[0] + d1[1] * n2[1]
        if abs(along) > 1e-9:
            # corner = top + s*n1 + t*d1, on the exit's offset line: t = s(1 - n1.n2)/(d1.n2)
            corner_t = (1.0 - (n1[0] * n2[0] + n1[1] * n2[1])) / along
        else:
            n2 = n1   # the exit carries straight on (or doubles back) — the offset holds
    count = max(len(vent.systems), 1)
    out = []
    pitch = (vent.bundle_spacing.meters if vent.bundle_spacing is not None
             else vent.diameter.meters * PIPE_BUNDLE_SPACING)
    for index, system in enumerate(vent.systems or (None,)):
        s = (index - (count - 1) / 2.0) * pitch
        here = (chase[0] + s * n1[0], chase[1] + s * n1[1])
        if has_jog:
            d1 = _unit(jog)
            there = (top[0] + s * (n1[0] + corner_t * d1[0]),
                     top[1] + s * (n1[1] + corner_t * d1[1]))
        else:
            there = here
        out_there = (exit_point[0] + s * n2[0], exit_point[1] + s * n2[1])
        own_top = derived_termination_elevation(model, vent, at=out_there)
        z_top = own_top if own_top is not None else vent.roof_termination_elevation.meters
        name = system.value if system is not None else "vent"
        path = (here, here, there, there, out_there, out_there)
        z = (z_start, z_jog, z_jog, z_exit, z_exit, z_top)
        out.append((f"{vent.tag}-{name}", path, z))
    return out


def _unit(vector: tuple[float, float]) -> tuple[float, float]:
    length = (vector[0] ** 2 + vector[1] ** 2) ** 0.5
    return vector[0] / length, vector[1] / length
