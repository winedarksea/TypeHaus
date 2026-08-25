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
        out.append(replace(layer, z0_m=band_z0, z1_m=band_z1))
    return tuple(out)
