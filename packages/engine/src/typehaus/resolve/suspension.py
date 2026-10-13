"""A hung body's cable: from the top of a luminaire or a hung seat to the surface above it,
one per hang point for a seat on several ropes.

A pendant's type ``height`` is its body — or, by the older convention, the whole assembly
with the stem folded in, which reads here as a cable of ~0. Only a fixture hung lower than
its type reaches leaves air between its top and the ceiling, and without this that air was
drawn as nothing: a chandelier floating in a double-height well. The cable is resolved once
here and drawn by the viewer and the glTF, and `electrical.suspension_reach` grades it against
what the product ships.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from typehaus.model.electrical import luminaire_types
from typehaus.model.suspension import HangingSeatType
from typehaus.resolve.overhead import OverheadIndex

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

#: The luminaire forms that hang on a cable or stem rather than sitting on their surface.
HUNG_FORMS = frozenset({"pendant", "chandelier"})
#: Within this either way the canopy is seated on its ceiling: a stem is cut to fit on
#: site, and a ``drop`` hangs off the storey's nominal ceiling plane, not the finished one.
FLUSH_M = 0.0508
#: Drawn, not specified: a 1/4" cable reads at viewing distance where a real 1/16" one
#: would not. The canopy defaults to a 5" round where the type states none.
CABLE_DRAWN_M = 0.00635
CANOPY_DEFAULT_M = 0.127
CANOPY_THICKNESS_M = 0.0254


@dataclass(frozen=True)
class SuspensionDraw:
    """What the viewer and the glTF draw over a hung body: a cable, and a canopy on top."""

    z0_m: float  # top of the body
    z1_m: float  # the surface it hangs from
    cable_m: float
    canopy_m: float
    canopy_thickness_m: float = CANOPY_THICKNESS_M
    #: Several ropes: ``(x, y, z1_m)`` per hang point, x/y in the item's frame. Empty: one
    #: cable at the item's centre up to ``z1_m``.
    points: tuple[tuple[float, float, float], ...] = ()


def hung_types(library: Any) -> dict[str, Any]:
    """Every type that can hang on a cable: the luminaires and the hung seats."""
    return {**luminaire_types(library),
            **{t.tag: t for t in library.furniture_types if isinstance(t, HangingSeatType)}}


def hung_type(types: dict[str, Any], item: Any) -> Any | None:
    """The item's type when it is a hung fixture or seat on a ceiling mount, else None."""
    mount = getattr(item, "mount", None)
    if mount is None or mount.kind.value != "ceiling" or mount.recessed_into_host_surface:
        return None
    product = types.get(item.type_ref or "")
    form = getattr(getattr(product, "form", None), "value", None)
    hung = form in HUNG_FORMS or isinstance(product, HangingSeatType)
    if not hung or getattr(product, "height", None) is None:
        return None
    return product


def resolve_suspensions(model: ResolvedModel) -> None:
    """Set ``suspension_m`` / ``suspended_from`` on every hung luminaire and seat, and a
    seat's cable at each of its hang points.

    Probed above the body's BASE, not its top, so a body that runs up through its ceiling
    finds that ceiling and reads a negative cable rather than the floor above it.
    """
    types = hung_types(model.plan.library)
    index: OverheadIndex | None = None
    for position, item in enumerate(model.canvas_objects):
        product = hung_type(types, item)
        if product is None:
            continue
        index = index or OverheadIndex(model, finishes=True)
        top = item.z_m + product.height.meters
        points = [p.xy_m for p in getattr(product, "hang_points", ())]
        if len(points) <= 1 and all(abs(v) < 1e-9 for p in points for v in p):
            over = index.lowest_above(*item.position, item.z_m)
            if over is not None:
                model.canvas_objects[position] = replace(
                    item, suspension_m=over.z_m - top, suspended_from=over.tag)
            continue
        turn = math.radians(item.rotation_degrees)
        cables, host = [], None
        for dx, dy in points:
            x = item.position[0] + dx * math.cos(turn) - dy * math.sin(turn)
            y = item.position[1] + dx * math.sin(turn) + dy * math.cos(turn)
            over = index.lowest_above(x, y, item.z_m)
            if over is None:
                break
            cables.append((dx, dy, over.z_m - top))
            host = host or over.tag
        else:
            model.canvas_objects[position] = replace(
                item, suspension_m=min(c for _, _, c in cables), suspended_from=host,
                suspension_points=tuple(cables))


def suspension_draw(item: Any, product: Any) -> SuspensionDraw | None:
    """The cables and canopy to draw over ``item``, or None when its canopy is seated."""
    cable = getattr(item, "suspension_m", None)
    if cable is None or cable <= FLUSH_M or getattr(product, "height", None) is None:
        return None
    top = item.z_m + product.height.meters
    canopy = getattr(product, "canopy_diameter", None)
    points = tuple((x, y, top + c) for x, y, c in getattr(item, "suspension_points", ()))
    return SuspensionDraw(z0_m=top, z1_m=top + cable, cable_m=CABLE_DRAWN_M,
                          canopy_m=canopy.meters if canopy is not None else CANOPY_DEFAULT_M,
                          points=points)
