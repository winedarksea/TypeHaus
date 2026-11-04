"""A-604 — the paint schedule: one row per specified paint system (decision #113).

Read off each coating ``Material.paint`` and its ``Product`` plus ``Product.equals``, so the
schedule names the same products the BOM and the paint RFQ print. A-603 cites the marks.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.tables import _add_table
from typehaus.emit.draw.sheet_writer import schedule_sheet, section
from typehaus.resolve.model import ResolvedModel


def paint_mark(library, ref: str) -> str | None:
    """The schedule mark of the paint system ``ref`` names, or None."""
    material = library.material(ref) if ref else None
    spec = getattr(material, "paint", None)
    return spec.mark if spec is not None else None


def painted_materials(library) -> list:
    return sorted((m for m in library.materials if m.paint is not None),
                  key=lambda m: (m.paint.mark or "~", m.tag))


def has_paint_schedule(model: ResolvedModel) -> bool:
    return bool(painted_materials(model.plan.library))


def _product_text(library, tag: str | None) -> str:
    from typehaus.takeoff.product_labels import product_label

    product = library.product(tag) if tag else None
    return product_label(product) if product is not None else "—"


def paint_rows(library) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    """Header and rows: mark, use, sheen, colour, primer, then each accepted line."""
    materials = painted_materials(library)
    lines = max((len(getattr(library.product(m.product_ref or ""), "equals", ()) or ())
                 for m in materials), default=0)
    header = ("Mark", "Use", "Sheen", "Colour", "Primer", "Basis of design",
              *(f"Or equal {i + 1}" for i in range(lines)))
    rows = []
    for material in materials:
        spec = material.paint
        product = library.product(material.product_ref or "")
        equals = tuple(getattr(product, "equals", ()) or ())
        coats = f"{spec.coats} coat{'s' if spec.coats != 1 else ''}"
        rows.append((spec.mark or material.tag, spec.use or material.name,
                     f"{spec.sheen}, {coats}", spec.colour,
                     paint_mark(library, spec.primer_ref or "") or spec.primer_ref or "—",
                     _product_text(library, material.product_ref),
                     *(_product_text(library, equals[i] if i < len(equals) else None)
                       for i in range(lines))))
    return header, rows


def write_paint_schedule(pdf, model: ResolvedModel, number: str, name: str) -> None:
    header, rows = paint_rows(model.plan.library)
    with schedule_sheet(pdf, model, number, name) as fig:
        section(fig, 0.04, 0.93, "PAINT SCHEDULE")
        _add_table(fig, rows, header, bbox=(0.04, 0.45, 0.92, 0.46))
