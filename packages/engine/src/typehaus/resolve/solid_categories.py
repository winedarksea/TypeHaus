"""The ``SolidCategory`` registry: one row per ``ResolvedSolid.category`` and IR element kind.

A category is user-facing text (the 3D Inspector heading) AND a routing key read by the trade
axis, the IFC emitter, the elevations, the finish vocabulary, the bid packages and the
concrete-interference check. Those used to be seven hand-written tables, four of which failed
silently on a new category. They are derived from :mod:`.solid_category_table` now, and
:func:`solid_category` raises on a name nobody registered.

Leaf module: imports nothing from ``emit``.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SolidCategory:
    name: str
    #: The viewer/BOM trade before any material override. ``None``: not in the solid trade
    #: table (a non-solid IR kind, or a category that takes the fallback trade).
    trade: str | None = None
    #: What the generic IFC solid loop emits it as. ``None``: never reaches that loop (a
    #: routed run, a pipe accessory, a non-solid kind) and raises if it does.
    ifc_class: str | None = None
    ifc_predefined: str | None = None
    ifc_object_type: str | None = None
    #: The exterior-elevation drawing family; ``None`` is not drawn.
    elevation_family: str | None = None
    #: ``"element"`` / ``"accessory"`` in ``emit/finishes.py``'s key vocabulary, else ``None``.
    finish_group: str | None = None
    #: The product is billed in a dedicated BOM section; bid packages drop the solid's volume.
    billed_elsewhere: bool = False
    #: ``"cast"`` (a concrete material makes it a pour), ``"laid"`` (a non-concrete material
    #: says it is not one) or ``"layer"`` (the material's own trade, a slab base course).
    material_refile: str | None = None
    #: A pour, for ``checks/structural/concrete_interference.py``.
    is_pour: bool = False
    # Reserved for the Slab.kind and placeable-collision phases.
    slab_family: str | None = None
    supports_on_top: bool = False
    collision: bool = False
    #: A geometry-IR element kind that is not a ``ResolvedSolid`` category.
    non_solid: bool = False


def _registry() -> dict[str, SolidCategory]:
    from typehaus.resolve.solid_category_table import ROWS

    out: dict[str, SolidCategory] = {}
    for row in ROWS:
        if row.name in out:
            raise ValueError(f"solid category {row.name!r} registered twice")
        out[row.name] = row
    return out


SOLID_CATEGORIES: dict[str, SolidCategory] = _registry()


def solid_category(name: str) -> SolidCategory:
    """The registered row for ``name``; raises ``KeyError`` on an unregistered category."""
    try:
        return SOLID_CATEGORIES[name]
    except KeyError:
        raise KeyError(f"unregistered solid category {name!r}: add a row to "
                       "resolve/solid_category_table.py") from None


def categories_where(**match: object) -> frozenset[str]:
    """Names of every row whose fields equal ``match``."""
    return frozenset(row.name for row in SOLID_CATEGORIES.values()
                     if all(getattr(row, key) == value for key, value in match.items()))
