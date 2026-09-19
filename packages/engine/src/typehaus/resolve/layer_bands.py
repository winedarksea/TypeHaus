"""Resolving a ``Layer.extent`` to a wall's absolute elevations.

Split out of ``topology.py`` — which is 850 lines before anything is added to it — because
this stopped being one nested helper the moment a second pass needed it. ``platform.py``
grows a wall *after* ``resolve_storey_walls`` has frozen every band into absolute numbers,
so it has to re-resolve them; keeping the *recipe* (``BandSpec``) beside the answer is what
lets it, without reaching back through the plan for the ``Assembly``.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any

from typehaus.model.assembly import LayerBound
from typehaus.model.enums import LayerDatum
from typehaus.resolve.model import ResolvedLayer

if TYPE_CHECKING:  # only for the annotation; importing it would be a cycle
    from typehaus.resolve.model import ResolvedWall


# One end of a ``LayerExtent``, flattened to ``(datum value, offset in meters)`` — the
# recipe, not the answer. ``None`` on either end is "the wall's own end".
BandSpec = tuple[tuple[str, float] | None, tuple[str, float] | None]


def band_spec(layer: object) -> BandSpec | None:
    """``Layer.extent`` as a plain ``BandSpec``, or ``None`` for a full-height layer.

    Flattened out of the pydantic model so a consumer can re-resolve a band without
    reaching back through the plan for the ``Assembly`` — which is what ``platform.py``
    needs after it grows a wall (→ :func:`reband`).
    """
    extent = getattr(layer, "extent", None)
    if extent is None:
        return None

    def _flat(bound: LayerBound | None) -> tuple[str, float] | None:
        return None if bound is None else (bound.datum.value, bound.offset.meters)

    return (_flat(extent.bottom), _flat(extent.top))


def band_datums(z0: float, z1: float, grade_m: float,
                line: Any | None = None) -> dict[str, float]:
    """What each :class:`LayerDatum` measures from, for one wall.

    ``line`` is the wall's :class:`~typehaus.resolve.layout_lines.ResolvedLayoutLine`, which
    is what LINE_BASE/LINE_TOP measure from. Without one — a wall on no derived line, or a
    caller that has not got one to hand — both fall back to the wall's own ends, so a
    single-wall line and a missing line resolve identically and nothing can silently float.
    """
    return {LayerDatum.WALL_BASE.value: z0,
            LayerDatum.WALL_TOP.value: z1,
            LayerDatum.GRADE.value: grade_m,
            LayerDatum.LINE_BASE.value: z0 if line is None else line.base_z_m,
            LayerDatum.LINE_TOP.value: z1 if line is None else line.top_z_m}


def band_ends_on_wall(band_z0: float | None, band_z1: float | None,
                      z0: float, z1: float, tol: float = 1e-9
                      ) -> tuple[float | None, float | None]:
    """Drop a band end that lands on the wall's own end, reporting it as ``None``.

    ``ResolvedLayer.is_banded`` asks whether a layer runs the whole wall, and until this
    it answered "does the layer STATE an extent", which is a different question. A band is
    clamped to its host (:func:`resolve_band_spec`), so a stated extent reaching past the
    wall resolves to exactly the wall — full height, nothing vertically compound about it —
    and still reported as banded. That cost real output: the IFC exporter pulled such a
    layer out of the ``IfcMaterialLayerSet`` and re-emitted it as an aggregated
    ``IfcBuildingElementPart``, so a wall whose layer set should sum to its full depth did
    not, over a band that trims nothing.

    catlin's sauna is the case. One ceiling band on the liner serves all four walls that
    carry it; on the two partitions that already stop AT the 7'-6" ceiling it is a no-op,
    and only the two that run past it are actually compound.

    ``band()`` falls back to the wall's own ends, so a dropped end resolves to the same
    elevation it did before — this changes what a layer SAYS about itself, not where it is.
    """
    return (None if band_z0 is not None and abs(band_z0 - z0) <= tol else band_z0,
            None if band_z1 is not None and abs(band_z1 - z1) <= tol else band_z1)


def resolve_band_spec(spec: BandSpec | None, z0: float, z1: float,
                      datums: dict[str, float]) -> tuple[float | None, float | None]:
    """A ``BandSpec``'s absolute vertical extent, or ``(None, None)`` for a full-height layer.

    ``Layer.extent`` states its ends against a *datum* rather than an elevation, because an
    ``Assembly`` is a type shared by many walls and knows none of their z. Resolving it is
    this function: the wall supplies WALL_BASE/WALL_TOP, the site supplies GRADE.

    A band is clamped to the wall — a panel whose top runs past the wall top is simply the
    wall top, not a layer floating above the wall. That pre-clamp is load-bearing: the glTF
    builder, the IFC part emitter and ``three/builders/walls.ts`` all re-clamp to the host
    wall, so a band that leaked past it here would be silently trimmed downstream instead of
    reported.
    """
    if spec is None:
        return None, None
    bottom_spec, top_spec = spec
    bottom = None if bottom_spec is None else datums[bottom_spec[0]] + bottom_spec[1]
    top = None if top_spec is None else datums[top_spec[0]] + top_spec[1]
    bottom = z0 if bottom is None else min(max(bottom, z0), z1)
    top = z1 if top is None else min(max(top, z0), z1)
    return bottom, top


def reband(wall: ResolvedWall, z0: float, z1: float, grade_m: float,
           line: Any | None = None) -> tuple[ResolvedLayer, ...]:
    """``wall``'s layers re-banded against a new ``(z0, z1)``.

    ``ResolvedLayer.z0_m``/``z1_m`` are absolute, so they go stale the moment the wall's own
    extent moves — and a wall's extent does move, after its layers are resolved:
    ``extend_walls_to_platform`` grows a stacked wall up to the platform above it. Without
    this, every band on a lifted wall stayed pinned to the pre-lift top, including a
    ``top=None`` band that means "run it out to the wall top". Layers with no
    ``band_spec`` are returned untouched.
    """
    datums = band_datums(z0, z1, grade_m, line)
    out: list[ResolvedLayer] = []
    for layer in wall.layers:
        if layer.band_spec is None:
            out.append(layer)
            continue
        band_z0, band_z1 = resolve_band_spec(layer.band_spec, z0, z1, datums)
        band_z0, band_z1 = band_ends_on_wall(band_z0, band_z1, z0, z1)
        out.append(replace(layer, z0_m=band_z0, z1_m=band_z1))
    return tuple(out)


# A layer function that only makes sense on the *weather* side of the structure: it is
# there to close the building, so on a lifted wall it is exactly what must keep running
# through the joist band to lap the rim. Anything else outboard of the stud (furring under
# a cladding, exterior insulation) is carried by the same test through its neighbours.
_WEATHER_FUNCTIONS = frozenset({"cladding", "sheathing", "membrane", "drainage", "airgap"})


def has_weather_skin(layers: tuple[ResolvedLayer, ...]) -> bool:
    """Is this stack an envelope — does anything weatherproof sit outboard of the studs?

    Deliberately **not** ``platform._is_clad``, which asks only for a CLADDING layer.
    catlin's ``GARDEN_FRAMED_2X6`` and ``SAUNA_LINER_ON_GARDEN_FRAMED`` stand inside the
    sunken garden behind a brick wythe: sheathing, waterproofing and XPS, no cladding at
    all. Calling those partitions and stopping their whole body at the plate would delete
    the rim lap that is the only reason the lift exists.

    Read off the **last** STRUCTURE layer, where :func:`clamp_to_plates` reads off the
    first. The two differ only on a multi-STRUCTURE stack (``Layer.slot`` brick wythes),
    and each wants the end of the run it is asking about.
    """
    structure = [i for i, layer in enumerate(layers) if layer.function == "structure"]
    if not structure:
        return False
    return any(layer.function in _WEATHER_FUNCTIONS for layer in layers[structure[-1] + 1:])


def clamp_to_plates(layers: tuple[ResolvedLayer, ...], *, wall_z0: float, wall_z1: float,
                    plate_top: float | None, plate_base: float | None,
                    clad: bool) -> tuple[ResolvedLayer, ...]:
    """Stop the layers that have no business in a lifted wall's joist band.

    ``extend_walls_to_platform`` grows a wall up to the platform above it so it spans
    floor-to-floor (#43), and ``extend_walls_to_foundation`` does the mirror below. The
    *framing* stays put — ``plate_top_z_m``/``plate_base_z_m`` record the real plates — but
    every layer with no band of its own was dragged through the band with the solid, which
    put interior drywall in the joist bay and 1,520 sf of gypsum and paint on the bill.

    What stops at the plate:

    * the **interior side** of an envelope wall — ``layers[:i]`` for the first STRUCTURE
      layer ``i``. ``ResolvedWall.body_layers`` is ordered interior→exterior, and
      ``Wall.interior_room`` only scales the offsets handed to ``rect_between``; it never
      reverses the stack. Everything from the studs out keeps lapping the rim, which is
      what the lift is for;
    * a **partition**'s whole body (``clad`` False). There is no rim to close and the
      framing already stops at the plate.

    No STRUCTURE layer → nothing is trimmed: interior and exterior are not distinguishable,
    and on a monolithic lifted wall the pour *is* what closes the rim.

    The trim is a ``min`` at the top and a ``max`` at the base against each layer's
    **current** band, so an author's lower band (catlin's 7'-6" sauna ceiling) always wins
    and a band is never widened. ``band_spec`` is left alone: the trim is a fact about this
    wall instance, not a recipe the ``Assembly`` stated — and a ``None`` spec is also what
    stops a later :func:`reband` from re-widening the layer.

    A ``Layer.slot`` region lying wholly inside the joist band collapses to a non-positive
    height and is dropped by the ``z1 - z0 <= 1e-9`` guards every consumer already carries.
    That is the right outcome: such a region was authored into a bay with no wall in it.
    """
    top = wall_z1 if plate_top is None else plate_top
    base = wall_z0 if plate_base is None else plate_base
    if top >= wall_z1 - 1e-9 and base <= wall_z0 + 1e-9:
        return tuple(layers)
    structure = [i for i, layer in enumerate(layers) if layer.function == "structure"]
    if not structure:
        return tuple(layers)
    trimmed = set(range(len(layers))) if not clad else set(range(structure[0]))

    out: list[ResolvedLayer] = []
    for index, layer in enumerate(layers):
        # Cavity fill is never trimmed on its own; it takes its host's band below, so it
        # can never claim more batt than the stud bay it fills.
        if index not in trimmed or layer.is_cavity:
            out.append(layer)
            continue
        z0 = wall_z0 if layer.z0_m is None else layer.z0_m
        z1 = wall_z1 if layer.z1_m is None else layer.z1_m
        band_z0, band_z1 = band_ends_on_wall(max(z0, base), min(z1, top), wall_z0, wall_z1)
        out.append(replace(layer, z0_m=band_z0, z1_m=band_z1))

    bands = {layer.name: (layer.z0_m, layer.z1_m) for layer in out}
    return tuple(
        replace(layer, z0_m=bands[layer.cavity_host][0], z1_m=bands[layer.cavity_host][1])
        if layer.is_cavity and layer.cavity_host in bands else layer
        for layer in out
    )


def reband_for_platform(wall: ResolvedWall, z0: float, z1: float, grade_m: float,
                        line: Any | None = None, *, plate_top: float | None = None,
                        plate_base: float | None = None) -> tuple[ResolvedLayer, ...]:
    """:func:`reband`, then :func:`clamp_to_plates`. One entry point because the order is.

    ``reband`` re-resolves a ``top=None`` band against the *new* ``z1``, so the clamp has to
    run strictly after it — and every wall ``extend_walls_to_foundation`` drops is also one
    ``extend_walls_to_platform`` lifted, so the second pass's own ``reband`` would silently
    re-widen a trim the first pass wrote. Applying this twice is a fixed point.
    """
    layers = reband(wall, z0, z1, grade_m, line)
    return clamp_to_plates(layers, wall_z0=z0, wall_z1=z1, plate_top=plate_top,
                           plate_base=plate_base, clad=has_weather_skin(layers))


def wall_body_band(wall: ResolvedWall) -> tuple[float, float]:
    """The ``(z0, z1)`` the wall's BODY actually occupies — its TALLEST body layer's band.

    A lifted partition has every body layer stopped at the plate, so extruding its solid
    from ``z0_m`` to ``z1_m`` would draw the joist band the trim just emptied.

    The tallest layer's own band, deliberately, rather than the union of every layer's: the
    union need be no layer's band at all (one layer trimmed at the top, another at the
    base), and the IFC emitter extrudes the layers that sit AT this band as the wall's body.
    A band no layer holds would leave that set empty, and an ``IfcShapeRepresentation`` with
    no ``Items`` is invalid IFC4. Falls back to the wall's own extent when it has no body
    layers at all.
    """
    bands = [layer.band(wall) for layer in wall.body_layers()]
    if not bands:
        return (wall.z0_m, wall.z1_m)
    return max(bands, key=lambda band: band[1] - band[0])


def at_body_band(layer: ResolvedLayer, wall: ResolvedWall) -> bool:
    """Does ``layer`` stand at :func:`wall_body_band` — is it part of the wall's solid?

    The one predicate the IFC emitter, its part emitter and the diff adapter share. A layer
    standing shorter than the body exports as an ``IfcBuildingElementPart``, so a consumer
    that measured a different set from the one that is drawn would report every trimmed
    wall as RESIZED on a self-diff.
    """
    z0, z1 = layer.band(wall)
    band_z0, band_z1 = wall_body_band(wall)
    return abs(z0 - band_z0) <= 1e-9 and abs(z1 - band_z1) <= 1e-9
