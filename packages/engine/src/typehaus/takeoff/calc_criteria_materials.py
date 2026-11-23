"""The design-criteria materials schedule: every strength a calculation consumed.

Values are collected off the records' inputs (an assembly nothing was designed against never
prints). The property label and the grade or source text are written here, per input name and
per kind; an input this table does not know is NOT dropped, it prints under its own name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.emit.md_writer import table
from typehaus.takeoff.calc_criteria_loads import input_name

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs

_MIX = "the mix authored on each element's concrete spec (ACI 318-19)"
_G60 = "Grade 60 reinforcing bar (IRC Table R404.1.2(8) footnote b)"
_GLULAM = ("24F-V5M1/SP glulam, southern pine (ANSI A190.1 / APA EWS), dry reference value "
           "before adjustment")
_MAKER = "engineered lumber, the maker's published table (named in the family's section 2)"

#: input name -> (property, unit, grade / source).
_PROPERTIES: dict[str, tuple[str, str, str]] = {
    "fc": ("f'c, concrete compressive strength", "psi", _MIX),
    "wall_fc": ("f'c, concrete compressive strength", "psi", _MIX),
    "column_fc": ("f'c, concrete compressive strength", "psi", _MIX),
    "pier_fc_psi": ("f'c, concrete compressive strength", "psi", _MIX),
    "cross_fc": ("f'c, concrete compressive strength", "psi", _MIX),
    "near_line_fc": ("f'c, concrete compressive strength", "psi", _MIX),
    "slab_fc": ("f'c, slab concrete (the strut)", "psi", _MIX),
    "fy": ("f_y, reinforcement yield strength", "psi", _G60),
    "concrete_unit_weight": ("Concrete unit weight", "pcf", "conventional"),
    "unit_weight": ("Unit weight, tiered wall section", "pcf", "the wall system's section"),
    "Fb": ("F_b, bending (glulam)", "psi", _GLULAM),
    "Fv": ("F_v, shear (glulam)", "psi", _GLULAM),
    "Fc_perp": ("F_c-perp, compression perpendicular (glulam)", "psi", _GLULAM),
    "E": ("E, modulus of elasticity (glulam)", "psi", _GLULAM),
    "fb": ("F_b, bending (engineered lumber)", "psi", _MAKER),
    "fv": ("F_v, shear (engineered lumber)", "psi", _MAKER),
    "fc_perp_plate": ("F_c-perp, sawn plate", "psi", "SPF, dry (NDS 2018 Supplement Table 4A)"),
    "Fb_adjusted": ("F_b', adjusted bending design value", "psi", "NDS 2018 adjustment factors"),
    "E_adjusted": ("E', adjusted modulus of elasticity", "psi", "NDS 2018 adjustment factors"),
}


def material_rows(inputs: PackageInputs) -> list[tuple[str, float, str, str, list[str]]]:
    """``(property, value, unit, source, [item ids])`` sorted by property then value."""
    seen: dict[tuple[str, float, str, str], list[str]] = {}
    for record in inputs.records:
        for quantity in record.inputs:
            name = input_name(quantity.name)
            if name not in _PROPERTIES:
                continue
            label, unit, source = _PROPERTIES[name]
            seen.setdefault((label, round(float(quantity.value), 6), unit, source),
                            []).append(record.item_id)
    return [(label, value, unit, source, sorted(set(items)))
            for (label, value, unit, source), items in sorted(seen.items())]


def materials_block(inputs: PackageInputs) -> str:
    rows = material_rows(inputs)
    if not rows:
        return "_No calculation in this package consumed a declared material property._"
    body = table(["Property", "Value", "Unit", "Grade / source", "Items", "Used by"],
                 [[label, value, unit, source, len(items),
                   ", ".join(f"`{i}`" for i in items[:3]) + (", …" if len(items) > 3 else "")]
                  for label, value, unit, source, items in rows])
    labels = [label for label, *_ in rows]
    if len(labels) != len(set(labels)):
        body += ("\n\nA property printed at two values was designed at two values: each row "
                 "names the items that used it, and the values are not reconciled into one.")
    return body + ("\n\nConnector and fastener allowables are cited in each calculation's "
                   "section 2 references, not tabulated here.")
