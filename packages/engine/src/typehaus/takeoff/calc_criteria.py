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
        _snow_block(site, inputs),
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
#: ``kind`` -> which design method its CAPACITIES are stated in.
#:
#: ** THE COVER USED TO ASSERT ONE METHOD FOR THE WHOLE PACKAGE, AND IT WAS THE WRONG ONE. **
#: "Every capacity cited in this package is an ASD allowable" sat in the wind block until
#: 2026-09-18, on a package whose every concrete item is LRFD — phi 0.65 on a tied column,
#: phi 0.90 on a tension-controlled section, demands factored at ASCE 7-16 §2.3.1. Mixing
#: the two silently is the classic way a reviewer compares a strength capacity against a
#: service demand, so it is stated per kind and beside the combination it goes with.
DESIGN_METHOD: dict[str, str] = {
    "deck_post": "LRFD (ACI 318-19 strength design, phi factors per Table 21.2.2)",
    "column_base": "ASD (IBC §1806.2 presumptive lateral bearing is an allowable)",
    "retaining_wall": "MIXED — LRFD for section strength (ACI 318-19 flexure and shear at "
                      "1.6H), ASD for stability (IBC §1807.2.3 safety factors on service "
                      "loads). The two are different questions on one wall and the sheet "
                      "labels each state.",
    "retaining_system": "ASD (IBC §1807.2.3 safety factors on service loads)",
    "wall_panel": "ASD (a published panel allowable against a 0.6W demand)",
    "girt_screw": "ASD (published withdrawal and pull-through allowables)",
    "post_bearing": "ASD (AWC NDS 2018 reference design values)",
    "glulam_beam": "ASD (AWC NDS 2018 reference design values x C_M, C_D, C_V)",
    "spread_footing": "MIXED — ASD against presumptive bearing, LRFD for the bell's own "
                      "flexure and shear (ACI 318-19 plain-concrete phi 0.60)",
    "roof_beam": "ASD (published beam allowables against a service demand)",
    "veneer_beam": "LRFD (ACI 318-19 strength design at 1.4D); deflection at service loads "
                   "(Table 24.2.2)",
}

LOAD_COMBINATIONS: dict[str, tuple[str, str]] = {
    "deck_post": ("1.2D + 1.6L", "ASCE 7-16 §2.3.1(2) / IBC 2018 §1605.2 Eq. 16-2"),
    "retaining_wall": ("1.6H (flexure and shear); service loads, FS >= 1.5 (stability)",
                       "ASCE 7-16 §2.3.1(6) / IBC 2018 §1605.2; IBC §1807.2.3"),
    "retaining_system": ("service loads, FS >= 1.5", "IBC 2018 §1807.2.3"),
    "wall_panel": ("0.6W", "ASCE 7-16 §2.4.1(7), C&C pressures per §30.3"),
    "girt_screw": ("0.6W", "ASCE 7-16 §2.4.1(7), C&C pressures per §30.3"),
    "post_bearing": ("D + L, allowable stress design",
                     "AWC NDS 2018 §3.10; IRC R507.1 loads"),
    "spread_footing": ("D + L, allowable stress design against presumptive bearing",
                       "IBC 2018 Table 1806.2; IRC R507.3.1"),
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
        method = DESIGN_METHOD.get(kind) or (
            "deferred — the responsible designer's method governs"
            if all(r.status is Status.NO_CALC for r in records) else "not declared")
        rows.append([f"`{kind}`", len(records), combination, method, citation or "—"])
    return table(["Kind", "Items", "Combination", "Design method", "From"], rows) + (
        "\n\nA combination is printed only where the arithmetic really applied it. "
        "\"not stated\" is not a missing factor — it is a calculation that took one case "
        "and combined nothing, and inventing a number beside it would be a claim about "
        "arithmetic this package did not do."
        "\n\n**The design method is per kind, and this package uses both.** Reading one "
        "method across the whole set is how a strength capacity gets compared against a "
        "service demand: every concrete item here is LRFD and every wood and presumptive-"
        "bearing item is ASD, and two kinds are genuinely mixed because they answer two "
        "different questions about one member.")


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
        # ** THE OLD WORDING WAS "every capacity cited in this package is an ASD allowable",
        # AND IT WAS FLATLY FALSE. ** Every concrete item in this package is LRFD —
        # `PHI_COMPRESSION_TIED` 0.65, `phi` 0.90 on a tension-controlled section, demands
        # factored at ASCE 7-16 §2.3.1 — and a reviewer taking that sentence at face value
        # would compare a strength capacity against a service demand on every retaining
        # wall and cast column here. What the factor actually is: the number the WIND
        # demand is divided back out by where a calculation grades at strength. Which
        # method each kind uses is the "Design method" column beside the combinations.
        ["ASD wind factor", wind.ASD_WIND_FACTOR, "", "ASCE 7-16 §2.4.1 combination 5/6 — "
         "the factor an ASD wind demand carries; see the design-method column above for "
         "which kinds are ASD and which are LRFD"],
    ]
    for height in heights:
        rows.append([f"q_z at {height:g} ft (mean roof height)",
                     wind.velocity_pressure_psf(basis, height), "psf",
                     "ASCE 7-16 eq. 26.10-1, strength level"])
    return table(["Quantity", "Value", "Unit", "Source"], rows)


def _snow_block(site: Any, inputs: PackageInputs) -> str:
    """Ground snow AND the design snow the records were actually computed at.

    ** IT PRINTED ``p_g`` ALONE, WHICH IS NOT WHAT ANY SNOW-DRIVEN RECORD USED. ** The
    wind block has taken ``inputs`` since it was written, so a reviewer can see the
    velocity pressure at each mean roof height the package actually contains; the snow
    block printed one jurisdictional number and stopped. On this house the governing case
    is an ASCE 7 §7.7 roof-step drift the engine derives no part of — the house AUTHORS it
    — and every roof beam and every pier under one is designed at that figure and not at
    ``p_g``. A cover page that shows 50 psf beside records computed at 73.7 invites exactly
    one conclusion, and it is the wrong one.
    """
    ground = getattr(site, "ground_snow_load_psf", None) if site is not None else None
    design = sorted({round(float(q.value), 2) for record in inputs.records
                     for q in record.inputs if q.name in ("roof_snow", "design_snow")})
    if ground is None and not design:
        return ("This model carries no ground snow load. Every snow-driven item reports it "
                "as a missing input.")
    rows = []
    if ground is not None:
        rows.append(["p_g, ground snow load", ground, "psf",
                     "IRC Table R301.2(1) — a jurisdictional figure, authored on the site, "
                     "not derived"])
    for value in design:
        rows.append([
            "Design roof snow, as computed", value, "psf",
            "the figure the records below were actually graded at" + (
                " — the house's authored drift case, NOT p_g (see the note under this "
                "table)" if ground is not None and abs(value - float(ground)) > 0.01
                else " — equal to p_g here")])
    body = table(["Quantity", "Value", "Unit", "Source"], rows)
    if any(ground is not None and abs(value - float(ground)) > 0.01 for value in design):
        body += ("\n\n**The design snow is not p_g, and the difference is authored rather "
                 "than derived.** This engine computes no part of drift, unbalanced or "
                 "sliding snow: where a roof's governing case is one of those, the house "
                 "states the figure (`preferences.toml [structural] roof_beam_snow_psf`) "
                 "and every member under that roof is graded at it. A reviewer disagreeing "
                 "with the drift magnitude is disagreeing with an input, not with a "
                 "calculation — which is exactly why it is on this page.")
    return body


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
