"""Concrete as a HOST — which solids a run can be cast into, and where it crosses them.

Lifted whole out of ``resolve/mep_queries.py`` (622 lines, over AGENTS.md's 500) at the one
seam that was already a cluster: the concrete reading. Everything here answers a variant of
the same question — *is this z, at this plan point, inside a pour?* — and three callers now
ask it for three different reasons:

* ``mep.sleeve_coverage`` asks about a THROUGH-crossing (:func:`concrete_crossings`);
* ``mep.run_in_slab`` asks about a run lying INSIDE a band (:func:`concrete_hosts`);
* ``routing/obstacles`` asks which z bands a router may not enter (:func:`concrete_bands`).

``mep_queries`` re-exports :func:`concrete_bands` so ``routing/obstacles`` and
``tests/test_concrete_bands.py`` keep the spelling they were written with; new callers
should import from here.

Like ``mep_queries``, this is a query API and not a resolver: nothing here appends to
``ResolvedModel``, and the dependency runs resolver -> queries so the ``checks`` <->
``resolve`` cycle stays broken.
"""

from __future__ import annotations

from typehaus.model.enums import AIR_SERVICE_DUCT_SYSTEM
from typehaus.resolve.assembly_material import is_cast_beam
from typehaus.resolve.geometry import length, sub
from typehaus.resolve.model import ResolvedModel, Ring

#: The concrete a sleeve can be cast into, and the solids :func:`concrete_crossings` walks.
_CONCRETE_SOLID_CATEGORIES = ("slab", "footing")
#: How much non-concrete a solid's section needs before :func:`concrete_bands` will split
#: it. A bond break, a vapour retarder or a slip sheet is not a route for a 2" drain; the
#: 10" foam beam in an EPS deck form is.
_MIN_NON_CONCRETE_M = 0.0508  # 2 inches


def concrete_bands(model: ResolvedModel, solid) -> list[tuple[float, float]]:
    """The z bands of a concrete solid that are actually CONCRETE, top down.

    Nearly always one band, the whole prism, and that is the fallback. The exception is a
    stay-in-place foam deck form: ``SL-M-DECK`` is 14 3/8" tall and 10" of that is
    ``eps-deck-form``, a material a plumber routes a channel in with a hot knife. A run
    lying in that foam is not embedded in a pour, and reporting it as an unsleeved crossing
    says the opposite of what is true — carrying services without a cast void is what an
    EPS deck is sold for.

    A layer counts as concrete when it names a mix (``Layer.concrete``). Bands are measured
    from the solid's TOP downward, because that is the order an assembly states its layers
    in and the order ``resolve/envelope`` stacks them.

    **Three ways this refuses to split, and all three are the conservative direction**, because
    a band this function invents is a crossing ``mep.sleeve_coverage`` stops reporting:

    * no assembly, or no layer in it naming a mix — the whole prism, which is today's
      reading and right for every footing and every ordinary slab;
    * no non-concrete layer at least :data:`_MIN_NON_CONCRETE_M` thick inside the prism —
      a 1/2" bond break is not a route for a 2" drain;
    * an assembly that does not account for the solid's full depth. Catlin's footings
      resolve 1/4" taller than their own assembly states, and attributing that remainder to
      anything but concrete would exempt the bottom inch of every footing in the house.
    """
    element = model.plan.by_tag(solid.tag)
    assembly_ref = getattr(element, "assembly", None) if element is not None else None
    assembly = (model.plan.library.assembly(assembly_ref)
                if isinstance(assembly_ref, str) else None)
    whole = [(solid.z0_m, solid.z1_m)]
    if assembly is None:
        return whole

    bands: list[tuple[float, float]] = []
    gap = 0.0
    top = solid.z1_m
    for layer in assembly.layers:
        if top <= solid.z0_m + 1e-9:
            break
        bottom = max(top - layer.thickness.meters, solid.z0_m)
        if getattr(layer, "concrete", None) is not None:
            bands.append((bottom, top))
        else:
            gap += top - bottom
        top = bottom
    if not bands or gap < _MIN_NON_CONCRETE_M:
        return whole
    if top > solid.z0_m + 1e-9:
        # The layers ran out above the solid's own bottom. Whatever is left is concrete
        # until something says otherwise.
        bands.append((solid.z0_m, top))

    merged: list[tuple[float, float]] = []
    for low, high in sorted(bands):
        if merged and low <= merged[-1][1] + 1e-9:
            merged[-1] = (merged[-1][0], max(merged[-1][1], high))
        else:
            merged.append((low, high))
    return merged


def concrete_hosts(model: ResolvedModel) -> list[tuple[str, str, object, float, float]]:
    """Every cast band a run could be inside, as ``(tag, category, footprint, z0, z1)``.

    The host list :func:`concrete_crossings` used to build inline. It is public because
    ``mep.run_in_slab`` asks a DIFFERENT question of the same list — not "where does this
    run pass through" but "how much of this run lies inside" — and two callers deriving
    their own host set is how a run comes to be embedded according to one check and clear
    according to the other.

    Three kinds of host, and the category names which: a slab or footing walked BAND BY
    BAND (so an EPS deck form's foam is not a pour), a cast beam as one prism, and a
    foundation wall's ``structure`` layer. ``footprint`` is a shapely ``Polygon``; shapely
    is imported here rather than at module scope for the same reason it always is in this
    package — the import costs more than most calls save.
    """
    from shapely.geometry import Polygon

    hosts: list[tuple[str, str, object, float, float]] = [
        (s.tag, s.category, Polygon(s.outline), z0, z1)
        for s in model.solids
        if s.category in _CONCRETE_SOLID_CATEGORIES and len(s.outline) >= 3
        for z0, z1 in concrete_bands(model, s)]
    hosts.extend((s.tag, "beam", Polygon(s.outline), s.z0_m, s.z1_m)
                 for s in model.solids
                 if s.category == "beam" and len(s.outline) >= 3
                 and is_cast_beam(model.plan, model.plan.by_tag(s.tag)))
    for wall in model.walls:
        if not wall.is_foundation:
            continue
        structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
        if structure is not None and len(structure.polygon) >= 3:
            hosts.append((wall.tag, "wall", Polygon(structure.polygon),
                          wall.z0_m, wall.z1_m))
    return hosts


def concrete_crossings(model: ResolvedModel) -> list[dict]:
    """Every point where a routed pipe, raceway or duct passes through concrete — the pour-day list.

    Walks each resolved run with vertical information against every concrete solid
    (slab/footing/cast beam) and foundation wall. A solid is walked band by band rather than as one
    prism — see :func:`concrete_bands`, which is what keeps a run lying in an EPS deck
    form's foam from reading as embedded in the pour. Returns plain dicts: run, host,
    host_category,
    point (plan), z_m, matched sleeve tag or None. A run with no z information cannot be
    walked and is skipped — the check reports those runs as UNKNOWN, never silently.

    Conduit is walked alongside pipe because the defect is identical and does not care which
    trade caused it: a raceway crossing a deck that cured without a sleeve gets cored just the
    same. Leaving conduit out is why ``CD-B-ATTIC-RISER`` and ``CD-B-KITCHEN`` punched through
    catlin's 9" ``SL-M-DECK`` unsleeved and unnoticed."""
    # Local, and the cycle is why: ``mep_queries`` re-exports :func:`concrete_bands`
    # from here, so a module-scope import back the other way would not resolve.
    from shapely.geometry import LineString, Point

    from typehaus.resolve.mep_queries import conduit_vertical_profile

    hosts = concrete_hosts(model)

    # (tag, system label, outside diameter, path, per-vertex z) for both trades. A raceway's
    # "diameter" is its trade size, which is what a sleeve has to be sized around.
    walkable: list[tuple[str, str, float, Ring, list[float]]] = [
        (run.tag, run.system, run.diameter_m, run.path, run.z_m)
        for run in model.pipe_runs if run.z_m is not None
    ]
    for conduit in model.conduits:
        profile = conduit_vertical_profile(conduit)
        if profile is None:
            continue
        path, z = profile
        walkable.append((conduit.tag, conduit.service or "spare",
                         conduit.trade_size_m, path, z))
    # Ducts, labelled by the ``Service`` their air is so a sleeve's ``purpose`` can name it.
    # A duct's hole is cast just like a pipe's; walking pipe only left one ungraded.
    for duct in model.ducts:
        service = _DUCT_SLEEVE_SERVICE.get(duct.system)
        if service is None or len(duct.z_m) != len(duct.path):
            continue
        walkable.append((duct.tag, service,
                         duct.diameter_m or max(duct.width_m, duct.depth_m),
                         duct.path, list(duct.z_m)))

    crossings: list[dict] = []
    for tag, system, diameter_m, path, z_m in walkable:
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            za, zb = z_m[i], z_m[i + 1]
            for host_tag, category, footprint, hz0, hz1 in hosts:
                hit = _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1,
                                            LineString, Point)
                if hit is None:
                    continue
                point, z_at = hit
                sleeve = _matching_sleeve(model, host_tag, system, point, z_at)
                crossings.append(dict(
                    run=tag, system=system, diameter_m=diameter_m,
                    host=host_tag, host_category=category, point=point, z_m=z_at,
                    sleeve=sleeve))
    return crossings


def _segment_concrete_hit(a, b, za, zb, footprint, hz0, hz1, LineString, Point):
    """Where (if anywhere) segment a→b at inverts za→zb passes through the host band."""
    plan_len = length(sub(a, b))
    lo, hi = sorted((za, zb))
    if hi < hz0 - 1e-6 or lo > hz1 + 1e-6:
        return None  # z ranges never meet
    if plan_len < 1e-6:
        # Vertical drop: crossing iff the drop spans the band and the point is inside.
        if lo <= hz0 + 1e-6 and hi >= hz1 - 1e-6 and footprint.buffer(1e-6).contains(Point(a)):
            return a, (hz0 + hz1) / 2.0
        return None
    # Sloped/horizontal: find where the invert crosses the band's mid-plane; a segment
    # running entirely inside the band (embedded in the pour) also counts at its midpoint
    # if the plan line enters the footprint.
    mid = (hz0 + hz1) / 2.0
    if abs(zb - za) > 1e-9 and min(za, zb) - 1e-6 <= mid <= max(za, zb) + 1e-6:
        t = (mid - za) / (zb - za)
        point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        if footprint.buffer(1e-6).contains(Point(point)):
            return point, mid
        return None
    if lo >= hz0 - 1e-6 and hi <= hz1 + 1e-6:
        line = LineString((a, b))
        if line.intersects(footprint):
            inter = line.intersection(footprint)
            # Grazing a face is not a crossing: a run laid tight against a wall touches
            # its boundary with (near-)zero embedded length and casts no sleeve.
            if getattr(inter, "length", 0.0) < 0.02:
                return None
            c = inter.centroid
            if not c.is_empty:
                # Invert *at the crossing*, not the segment mean — a sloped drain's
                # invert at the wall is what the cast sleeve is set to.
                t = line.project(c) / max(line.length, 1e-9)
                return (c.x, c.y), za + t * (zb - za)
    return None


_SLEEVE_MATCH_TOL_M = 0.1  # a cast-in sleeve within 4" of the crossing claims it


#: Which ``SleevePenetration.purpose`` values a crossing of each system may claim. Proximity
#: alone is not enough: a 1" power raceway that happens to pass within 4" of a 3" drain
#: sleeve is not threading it, and letting it match reported a false PASS on the raceway
#: *and* stole the sleeve from the drain that really goes through it (which is how
#: ``mep.sewer_exit_invert`` came to grade CD-B-SPA as a drain). Systems are the ``PipeSystem``
#: values plus, for conduit, the ``Service`` the raceway carries or "spare" for a capped one.
_SLEEVE_PURPOSES_BY_SYSTEM = {
    "water_cold": {"water_cold"}, "water_hot": {"water_hot"},
    "drain": {"drain"}, "vent": {"vent"}, "radon": {"vent", "drain"}, "gas": {"gas"},
    # A raceway may share a sleeve with another raceway of any voltage — they are all
    # electrical work — but never with a plumbing one. A spare pipe is electrical too: it is
    # in the electrician's rough-in, whatever eventually goes through it.
    "power_120": {"power_120", "power_240"}, "power_240": {"power_120", "power_240"},
    "data": {"data"}, "spare": {"power_120", "power_240", "data"},
    # Air shares a sleeve with nothing else: one duct, one hole, sealed round it.
    **{service: {service} for service in
       ("supply_air", "return_air", "exhaust_air", "outdoor_air")},
}

#: ``DuctSystem`` value -> the ``Service`` a sleeve for it names. A dryer is exhaust air;
#: a transfer grille is not a duct and casts nothing.
_DUCT_SLEEVE_SERVICE = {
    **{system.value: service.value for service, system in AIR_SERVICE_DUCT_SYSTEM.items()},
    "dryer": "exhaust_air",
}


def _matching_sleeve(model: ResolvedModel, host_tag: str, system: str,
                     point: tuple[float, float], z_at: float) -> str | None:
    allowed = _SLEEVE_PURPOSES_BY_SYSTEM.get(system)
    best: tuple[float, str] | None = None
    for sleeve in model.sleeves:
        if sleeve.host_slab != host_tag:
            continue
        if allowed is not None and sleeve.purpose not in allowed:
            continue
        d = length(sub(sleeve.center, point))
        if d <= _SLEEVE_MATCH_TOL_M and (best is None or d < best[0]):
            best = (d, sleeve.tag)
    return best[1] if best is not None else None
