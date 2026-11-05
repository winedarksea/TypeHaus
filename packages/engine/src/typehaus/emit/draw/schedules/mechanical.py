"""M-601 — duct construction, the duct and air-terminal schedules, and the duct parts (#114).

Views of the house's ``DuctStandard`` and the take-off: the spec block reads the standard's
rows, the duct schedule ``takeoff/hvac.duct_schedule``, the terminals ``register_schedule``
and the parts ``takeoff/duct_parts``. Nothing is summed here.
"""

from __future__ import annotations

from typehaus.emit.draw.schedules.paged_tables import PagedTable, wrap_cells
from typehaus.emit.draw.schedules.structural import _write_paged
from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_DASH = "—"


def has_mechanical_schedule(model: ResolvedModel) -> bool:
    return bool(model.ducts)


def _label(library, ref: str | None) -> str:
    from typehaus.takeoff.product_labels import product_label

    product = library.product(ref) if ref else None
    return product_label(product) if product is not None else (ref or _DASH)


def _inches(length) -> str:
    return f"{length.meters / M_PER_IN:g}\"" if length is not None else "not read"


def spec_rows(model: ResolvedModel) -> tuple[tuple[str, str, str], ...]:
    """(item, specification, basis) for the duct construction block."""
    from typehaus.resolve.duct_standard import duct_standard

    standard, _ = duct_standard(model.plan)
    library = model.plan.library
    rect = [(f"rectangular to {_inches(r.max_side)} side", f"{r.gauge} ga "
             f"({r.thickness.meters / M_PER_IN:.3f}\")" if r.thickness else f"{r.gauge} ga",
             r.source or "")
            for r in sorted((r for r in library.duct_product_types if r.section == "rectangular"),
                            key=lambda r: r.max_side.meters)]
    if standard is None:
        return (("Duct standard", "none declared — round gauge, sealing, supports and parts "
                 "are unspecified", ""), *rect)
    rows: list[tuple[str, str, str]] = [
        ("Pressure class", f"{standard.pressure_class_in_wg:g} in. w.g. static",
         "; ".join(standard.citations))]
    rows += [(f"Round {g.material} to {_inches(g.max_diameter)}",
              f"{g.gauge} ga ({g.thickness.meters / M_PER_IN:.3f}\"), {g.seam} seam",
              g.source or "") for g in standard.round_gauges]
    rows += rect
    sealant = _label(library, standard.sealant_product_ref)
    rows.append(("Sealing", f"{standard.seal_class}: {sealant}; "
                 f"{_label(library, standard.tape_product_ref)}", "every joint and seam"))
    rows += [(f"Elbow {_inches(e.diameter)}", f"{_label(library, e.product_ref)}, {e.kind}, "
              f"bought at {'/'.join(f'{a:g}' for a in e.angles)} deg, centre-to-face "
              f"{_inches(e.center_to_face)}, C {e.loss_c if e.loss_c is not None else 'not read'}",
              e.source or "") for e in standard.elbows]
    for part in standard.parts:
        size = " x ".join(s for s in (part.size, part.branch) if s) or "any"
        what = ("integral to the terminal" if part.integral else "shop-fabricated"
                if part.fabricated and not part.product_ref else _label(library, part.product_ref))
        rows.append((f"{part.kind.replace('_', ' ').capitalize()} {size}", what,
                     part.source or ""))
    rows += [(f"Supports, {s.section} to {_inches(s.max_size)}",
              f"{s.hanger.replace('_', ' ')} at {s.spacing.meters / M_PER_IN / 12:g}' o.c. "
              f"max, {_label(library, s.product_ref)}; one within "
              f"{standard.support_near_fitting.meters / M_PER_IN:g}\" of each fitting",
              s.source or "") for s in standard.supports]
    rows += [(f"Port kit {k.type_ref}", ", ".join(x for x in (
        k.transition_product_ref and f"{_label(library, k.transition_product_ref)} transition",
        k.flex_product_ref and f"{_inches(k.flex_length)} {_label(library, k.flex_product_ref)}")
        if x), k.source or "") for k in standard.port_kits]
    if standard.insulation_product_ref:
        rows.append(("Insulation (OA/EA)", _label(library, standard.insulation_product_ref),
                     "see duct schedule"))
    return tuple(rows)


def duct_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    from typehaus.model.ducts import duct_size_text
    from typehaus.resolve.duct_sizing import rectangular_row
    from typehaus.resolve.duct_standard import duct_standard
    from typehaus.takeoff.hvac import duct_schedule

    standard, _ = duct_standard(model.plan)
    by_tag = {d.tag: d for d in model.ducts}
    rows = []
    for row in duct_schedule(model):
        duct = by_tag[str(row["tag"])]
        if duct.diameter_m is not None:
            gauge = standard.gauge_for(duct.diameter_m) if standard is not None else None
        else:
            gauge = rectangular_row(model.plan.library, duct.material, duct.width_m,
                                    duct.depth_m)
        host = row["floor_ref"] or row["soffit_ref"] or str(row["routing"])
        cfm = row["design_cfm"]
        rows.append((str(row["tag"]), str(row["system"]).replace("_", " "),
                     duct_size_text(duct.diameter_m, duct.width_m, duct.depth_m),
                     f"{gauge.gauge} ga" if gauge is not None and gauge.gauge else _DASH,
                     str(row["material"] or _DASH), str(host), f"{row['length_ft']}",
                     f"{cfm:g}" if cfm is not None else _DASH,
                     str(row["insulation"] or _DASH)))
    return tuple(rows)


def terminal_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    from typehaus.takeoff.hvac import register_schedule

    library = model.plan.library
    types = {t.tag: t for t in library.register_types}
    boots = {p.other: p for p in model.duct_parts if p.kind == "boot"}
    cfm = {el.tag: el.design_cfm for el in model.plan.all_elements()
           if el.element_kind == "Register"}
    rows = []
    for row in register_schedule(model):
        rtype = types.get(row["type_ref"])
        neck = getattr(rtype, "neck", None)
        boot = boots.get(row["tag"])
        boot_text = (_DASH if boot is None else "integral" if boot.integral
                     else "shop-fabricated" if boot.product_ref is None and boot.fabricated
                     else _label(library, boot.product_ref) if boot.product_ref
                     else f"UNKNOWN ({boot.size} to {boot.branch})")
        flow = cfm.get(row["tag"])
        rows.append((str(row["tag"]), str(row["kind"]), str(row["room"] or _DASH),
                     str(row["type_ref"] or _DASH),
                     _label(library, getattr(rtype, "product_ref", None)),
                     getattr(neck, "part", None) or _DASH, boot_text,
                     str(row["duct_ref"] or _DASH), f"{flow:g}" if flow is not None else _DASH))
    return tuple(rows)


def part_rows(model: ResolvedModel) -> tuple[tuple[str, ...], ...]:
    from typehaus.takeoff.duct_parts import duct_part_takeoff, duct_support_takeoff

    library = model.plan.library
    rows = [(str(r["kind"]).replace("_", " "), str(r["size"]),
             _label(library, r["product"]) if r["product"] else str(r["source"]),
             f"{r['count']}") for r in duct_part_takeoff(model)]
    rows += [(f"hanger ({r['hanger']})", str(r["size"]),
              _label(library, r["product"]) if r["product"] else _DASH, f"{r['count']}")
             for r in duct_support_takeoff(model)]
    return tuple(rows)


def mechanical_tables(model: ResolvedModel) -> list[PagedTable]:
    tables = [
        PagedTable("DUCT CONSTRUCTION", ("Item", "Specification", "Basis"),
                   wrap_cells(spec_rows(model), {1: 70, 2: 60})),
        PagedTable("DUCT SCHEDULE", ("Tag", "System", "Size", "Gauge", "Material", "Host",
                                     "LF", "CFM", "Insulation"),
                   wrap_cells(duct_rows(model), {8: 30})),
        PagedTable("AIR TERMINAL SCHEDULE", ("Tag", "Kind", "Room", "Type", "Product", "Neck",
                                             "Boot", "Duct", "CFM"),
                   wrap_cells(terminal_rows(model), {5: 34, 6: 28})),
    ]
    parts = part_rows(model)
    if parts:
        tables.append(PagedTable("DUCT PARTS AND SUPPORTS", ("Part", "Size", "Product", "Qty"),
                                 parts))
    return tables


def write_mechanical_schedule(pdf, model: ResolvedModel, number: str, name: str, *,
                              page: int = 0) -> None:
    _write_paged(pdf, model, number, name, mechanical_tables(model), page)
