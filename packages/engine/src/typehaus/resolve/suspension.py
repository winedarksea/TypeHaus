"""A hung luminaire's cable: from the top of its body to the surface plumb above it.

A pendant's type ``height`` is its body — or, by the older convention, the whole assembly
with the stem folded in, which reads here as a cable of ~0. Only a fixture hung lower than
its type reaches leaves air between its top and the ceiling, and without this that air was
drawn as nothing: a chandelier floating in a double-height well. The cable is resolved once
here and drawn by the viewer and the glTF, and `electrical.suspension_reach` grades it against
what the product ships.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from typehaus.model.electrical import luminaire_types
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


def hung_type(types: dict[str, Any], item: Any) -> Any | None:
    """The item's ``LuminaireType`` when it is a hung fixture on a ceiling mount, else None."""
    mount = getattr(item, "mount", None)
    if mount is None or mount.kind.value != "ceiling" or mount.recessed_into_host_surface:
        return None
    product = types.get(item.type_ref or "")
    form = getattr(getattr(product, "form", None), "value", None)
    if form not in HUNG_FORMS or getattr(product, "height", None) is None:
        return None
    return product


def resolve_suspensions(model: ResolvedModel) -> None:
    """Set ``suspension_m`` / ``suspended_from`` on every hung luminaire.

    Probed above the body's BASE, not its top, so a body that runs up through its ceiling
    finds that ceiling and reads a negative cable rather than the floor above it.
    """
    types = luminaire_types(model.plan.library)
    index: OverheadIndex | None = None
    for position, item in enumerate(model.canvas_objects):
        product = hung_type(types, item)
        if product is None:
            continue
        index = index or OverheadIndex(model, finishes=True)
        over = index.lowest_above(*item.position, item.z_m)
        if over is None:
            continue
        model.canvas_objects[position] = replace(
            item, suspension_m=over.z_m - (item.z_m + product.height.meters),
            suspended_from=over.tag)


def suspension_draw(item: Any, product: Any) -> SuspensionDraw | None:
    """The cable and canopy to draw over ``item``, or None when its canopy is seated."""
    cable = getattr(item, "suspension_m", None)
    if cable is None or cable <= FLUSH_M or getattr(product, "height", None) is None:
        return None
    top = item.z_m + product.height.meters
    canopy = getattr(product, "canopy_diameter", None)
    return SuspensionDraw(z0_m=top, z1_m=top + cable, cable_m=CABLE_DRAWN_M,
                          canopy_m=canopy.meters if canopy is not None else CANOPY_DEFAULT_M)
