"""The calculation package's design-criteria page — sections 1 to 6 of ``01-...md``.

Split out of ``calc_package`` when the load-combination section landed. Every value on the
page is **derived from the model or from the calculation that consumed it**; a criteria
sheet that can drift from the calculations it fronts is worse than none, which is why none
of these blocks reads an assembly a calculation never looked at.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from typehaus.emit.md_writer import document, heading, table
from typehaus.engineering.item import Status

if TYPE_CHECKING:  # pragma: no cover — typing only
    from typehaus.takeoff.calc_package import PackageInputs


def _criteria(inputs: PackageInputs) -> str:
    from typehaus import wind
    from typehaus.engineering import soil as soil_module

    site = getattr(getattr(inputs.model, "plan", None), "project", None)
    site = getattr(site, "site", None)
    blocks = [
        heading(f"Design criteria — {inputs.house}"),
        "Every value on this page is **derived from the model**, not typed here. A criteria "
        "sheet that can drift from the calculations it fronts is worse than none.",
        heading("1. Wind", 2),
        _wind_block(wind, site, inputs),
        heading("2. Snow", 2),
        _snow_block(site),
        heading("3. Ground", 2),
        _soil_block(soil_module, site),
        heading("4. Materials", 2),
        _materials_block(inputs),
        heading("5. Service conditions", 2),
        _service_block(inputs),
        heading("6. Load combinations", 2),
        _combinations_block(inputs),
    ]
    return document(*blocks)


#: ``kind -> (named combination, the standard it is cited from)``.
#:
#: Every entry is read off the calculation module that applies it — ``pier_basis``'s
#: ``DEAD_LOAD_FACTOR``/``LIVE_LOAD_FACTOR``, ``retaining_basis``'s
#: ``EARTH_PRESSURE_LOAD_FACTOR``, ``wall_panel``'s 0.6W — not chosen here. A kind absent
#: from this table prints "not stated", which is the honest answer for a kind whose
#: arithmetic combines nothing: a numbered combination beside a demand that was never
#: combined is a claim the arithmetic does not support (see ``LimitState.combination``).
#:
#: A sealed residential package identifies the governing combination BY NUMBER at each
#: member, because "the wind case" is not checkable and a numbered combination is.
LOAD_COMBINATIONS: dict[str, tuple[str, str]] = {
    "deck_post": ("1.2D + 1.6L", "ASCE 7-16 §2.3.1(2) / IBC 2018 §1605.2 Eq. 16-2"),
    "retaining_wall": ("1.6H (flexure and shear); service loads, FS >= 1.5 (stability)",
                       "ASCE 7-16 §2.3.1(6) / IBC 2018 §1605.2; IBC §1807.2.3"),
    "retaining_system": ("service loads, FS >= 1.5", "IBC 2018 §1807.2.3"),
    "wall_panel": ("0.6W", "ASCE 7-16 §2.4.1(7), C&C pressures per §30.3"),
    "post_bearing": ("D + L, allowable stress design",
                     "AWC NDS 2018 §3.10; IRC R507.1 loads"),
    "spread_footing": ("D + L, allowable stress design against presumptive bearing",
                       "IBC 2018 Table 1806.2; IRC R507.3.1"),
    # ``glulam_beam`` sums DECK_DEAD_LOAD_PSF and DECK_LIVE_LOAD_PSF for bending and shear,
    # and checks deflection against the live term alone (IRC Table R301.7).
    "deck_beam": ("D + L, allowable stress design; L alone for deflection",
                  "AWC NDS 2018 Ch. 3 and 5; IRC Table R301.5 / R301.7"),
}


def _combinations_block(inputs: PackageInputs) -> str:
    """The named load combination each kind in THIS package was computed at.

    A reviewer reproducing a number needs the factors, and "the wind case" is not a
    reproducible statement. Where a limit state records its own combination that is what
    prints, because the record is closer to the arithmetic than any table here; otherwise
    the kind's declared combination does. A kind that combines nothing — every deferred
    kind, where the responsible designer's own combination governs — says so.
    """
    kinds = sorted({record.kind for record in inputs.records})
    if not kinds:
        return "_This package contains no engineered item._"
    rows = []
    for kind in kinds:
        records = [r for r in inputs.records if r.kind == kind]
        stated = sorted({state.combination for r in records
                         for state in r.limit_states if state.combination})
        declared, citation = LOAD_COMBINATIONS.get(kind, ("", ""))
        if stated:
            combination, citation = "; ".join(stated), "recorded on the limit state"
        elif declared:
            combination = declared
        elif all(r.status is Status.NO_CALC for r in records):
            combination = "deferred — the responsible designer's combination governs"
            citation = "see `03-open-items.md`"
        else:
            combination = "not stated"
            citation = "this kind's arithmetic combines no cases"
        rows.append([f"`{kind}`", len(records), combination, citation or "—"])
    return table(["Kind", "Items", "Combination", "From"], rows) + (
        "\n\nA combination is printed only where the arithmetic really applied it. "
        "\"not stated\" is not a missing factor — it is a calculation that took one case "
        "and combined nothing, and inventing a number beside it would be a claim about "
        "arithmetic this package did not do.")


def _wind_block(wind: Any, site: Any, inputs: PackageInputs) -> str:
    basis = wind.wind_basis(site) if site is not None else None
    if basis is None:
        return ("This model carries no complete wind basis (a speed, an exposure and a risk "
                "category are all required). Every wind-driven item reports it as a missing "
                "input rather than assuming one.")
    heights = sorted({round(float(q.value), 2) for record in inputs.records
                      for q in record.inputs if q.name == "mean_roof_height"})
    rows = [
        ["V_ult, basic wind speed", basis.speed_mph, "mph",
         "ASCE 7-16 Fig. 26.5-1 via MN Rules 1309.0301 (115 mph statewide)"],
        ["Exposure category", basis.exposure, "", "ASCE 7-16 §26.7.3 — surface roughness "
         "determined for this site"],
        ["Risk category", basis.risk_category, "", "ASCE 7-16 Table 1.5-1 — a dwelling is II"],
        ["K_d, directionality", wind.K_D_BUILDINGS, "", "ASCE 7-16 Table 26.6-1"],
        ["K_zt, topographic factor", wind.K_ZT_FLAT, "", "ASCE 7-16 §26.8.2 — none of the "
         "three conditions of §26.8.1 is met"],
        ["K_e, ground elevation factor", 1.0, "", "ASCE 7-16 §26.9 — permitted at all "
         "elevations; the conservative side of a 3 % effect at this site"],
        ["ASD wind factor", wind.ASD_WIND_FACTOR, "", "ASCE 7-16 §2.4.1 combination 5/6 — "
         "every capacity cited in this package is an ASD allowable"],
    ]
    for height in heights:
        rows.append([f"q_z at {height:g} ft (mean roof height)",
                     wind.velocity_pressure_psf(basis, height), "psf",
                     "ASCE 7-16 eq. 26.10-1, strength level"])
    return table(["Quantity", "Value", "Unit", "Source"], rows)


def _snow_block(site: Any) -> str:
    ground = getattr(site, "ground_snow_load_psf", None) if site is not None else None
    if ground is None:
        return ("This model carries no ground snow load. Every snow-driven item reports it "
                "as a missing input.")
    return table(["Quantity", "Value", "Unit", "Source"],
                 [["p_g, ground snow load", ground, "psf",
                   "IRC Table R301.2(1) — a jurisdictional figure, authored on the site, "
                   "not derived"]])


def _soil_block(soil_module: Any, site: Any) -> str:
    soil_class = getattr(site, "soil_class", None) if site is not None else None
    presumptive = soil_module.presumptive(soil_class)
    if presumptive is None:
        return (f"This model declares no usable soil group (`soil_class` = "
                f"{soil_class!r}). No lateral pressure, bearing value or base friction is "
                f"presumed: a calculation that needs one reports it as a missing input, "
                f"because guessing the ground is the one assumption a retaining wall "
                f"cannot survive.")
    bed = soil_module.aggregate_bed()
    rows = [
        ["Declared soil group", presumptive.soil_class, "", "IRC Table R405.1 / Unified"],
        ["IBC presumptive class", presumptive.ibc_class, "", presumptive.citation],
        ["Active equivalent fluid pressure", presumptive.active_efp_psf_per_ft, "psf/ft",
         "IBC Table 1610.1"],
        ["At-rest equivalent fluid pressure", presumptive.at_rest_efp_psf_per_ft, "psf/ft",
         "IBC Table 1610.1 — used where the wall is restrained against rotation"],
        ["Allowable bearing", presumptive.allowable_bearing_psf, "psf",
         "IBC Table 1806.2"],
        ["Lateral bearing", presumptive.lateral_bearing_psf_per_ft, "psf/ft",
         "IBC Table 1806.2"],
        ["Base friction coefficient (native)", presumptive.friction_coefficient, "",
         "IBC Table 1806.2"],
        ["Base friction coefficient (on washed stone)", bed.friction_coefficient, "",
         f"{bed.citation} — a footing bearing on a replacement stone section slides on "
         f"stone, not on the retained soil behind the wall"],
        ["Soil unit weight band", f"{soil_module.SOIL_UNIT_WEIGHT_BAND_PCF[0]:g}–"
         f"{soil_module.SOIL_UNIT_WEIGHT_BAND_PCF[1]:g}", "pcf",
         "not a code value — loose-to-medium silty gravel through well compacted"],
        ["Concrete unit weight", soil_module.CONCRETE_UNIT_WEIGHT_PCF, "pcf",
         "conventional, and not in dispute"],
    ]
    return table(["Quantity", "Value", "Unit", "Source"], rows)


#: Input names that describe a *material*, and the row each becomes. Derived from what the
#: calculations actually consumed, so a material nothing is designed against never appears.
_MATERIAL_INPUTS = {
    "fc": ("f'c, specified concrete compressive strength", "psi"),
    "fy": ("f_y, specified yield strength of reinforcement", "psi"),
    "Fb_adjusted": ("F_b', adjusted bending design value", "psi"),
    "E_adjusted": ("E', adjusted modulus of elasticity", "psi"),
    "concrete_unit_weight": ("Concrete unit weight", "pcf"),
}


def _materials_block(inputs: PackageInputs) -> str:
    """Material properties, collected from the values the calculations actually consumed.

    Not read off the assemblies: an assembly a calculation never looked at would then be
    printed as a design criterion, which is precisely the drift this page exists to
    prevent. Where one calc used 3,000 psi and another 5,000, both appear, with the items
    that used each — that disagreement is a fact a reviewer needs, not a thing to average.
    """
    seen: dict[tuple[str, float], list[str]] = {}
    for record in inputs.records:
        for quantity in record.inputs:
            if quantity.name in _MATERIAL_INPUTS:
                seen.setdefault((quantity.name, round(float(quantity.value), 6)),
                                []).append(record.item_id)
    if not seen:
        return "_No calculation in this package consumed a declared material property._"
    rows = []
    for (name, value), items in sorted(seen.items()):
        label, unit = _MATERIAL_INPUTS[name]
        rows.append([label, value, unit, len(items),
                     ", ".join(f"`{i}`" for i in sorted(items)[:4])
                     + (", …" if len(items) > 4 else "")])
    return table(["Property", "Value", "Unit", "Items", "Used by"], rows) + \
        "\n\nWhere one value appears twice, two calculations were run against two different " \
        "strengths. That is reported and not reconciled."


def _service_block(inputs: PackageInputs) -> str:
    """The distinct bases the package rests on — one row per standard actually cited."""
    bases: dict[str, list[str]] = {}
    for record in inputs.records:
        if record.basis:
            bases.setdefault(record.basis, []).append(record.item_id)
    if not bases:
        return "_No basis is recorded on any item._"
    rows = [[basis, len(items), ", ".join(sorted({i.split("/")[0] for i in items}))]
            for basis, items in sorted(bases.items())]
    return table(["Basis", "Items", "Kinds"], rows)
