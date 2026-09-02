"""IRC / MSRC R806.5 — unvented attic and unvented enclosed rafter assemblies.

The section every "hot roof" is built under. Its subject is the assembly with **no
ventilated airspace between the insulation and the roof sheathing**: the condition R806.2's
1/150 net-free-area ratio explicitly does not govern
(``code.R806_2_attic_ventilation`` scope-passes naming this section by number), so this
module grades what R806.5 itself requires.

What R806.5 actually asks, and what this module grades:

* the assembly is inside the building thermal envelope (item 1);
* **no interior Class I vapour retarder on the ceiling side** (item 2) — a poly sheet or a
  vapour-barrier primer under the drywall is what turns a sealed deck into a cavity that
  cannot dry in either direction, which is why the code forbids it here and permits it
  almost everywhere else;
* in climate zones 5-8, any air-impermeable insulation is itself **at least a Class II
  vapour retarder** (item 4);
* and the insulation is placed by one of the three arrangements in item 5, each with its own
  arithmetic:

  ===========  ==========================================================================
  item 5.1     air-permeable insulation in the bay ONLY, with rigid board or air-
               impermeable insulation ABOVE the deck at the Table R806.5 R-value
  item 5.2     air-impermeable insulation only, in direct contact with the underside of
               the sheathing
  item 5.3     BOTH — the air-impermeable layer against the sheathing at the Table R806.5
               R-value, the air-permeable insulation directly under it. Flash-and-batt.
  ===========  ==========================================================================

Table R806.5 is a *condensation-control* minimum, not an energy one: it is the R needed
above (or against) the sheathing to hold the first condensing surface above the dew point
for the zone, and it is why the same 5" of foam that is generous in zone 5 is marginal in
zone 8. The whole point of items 5.1 and 5.3 is that meeting it makes outward drying
unnecessary — which is the reading :mod:`typehaus.checks.building_science.condensation`
defers to, because a steady-state Glaser walk cannot grade an assembly sealed on its cold
side by an impermeable metal panel (see ``r806_5_compliance`` and its caller there).

The zone is hard-coded to 6, exactly as ``checks/code/mn_energy.py`` hard-codes its
prescriptive envelope table to zone 6: this is the MN 2024 rule set, and no ``Site`` field
carries a climate zone. The finding states the assumption and reports the zone-7 row
alongside it, because Minnesota holds both and the difference (R-25 vs R-30) is the whole
AHJ conversation on a roof designed near the line.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.code.mn_residential._common import _fail, _na, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.energy import _storey_is_conditioned
from typehaus.findings import Finding
from typehaus.model.assembly import Assembly, Layer
from typehaus.model.enums import LayerFunction
from typehaus.model.plan import Library

CHECK_ID = "code.R806_5_unvented_roof"
CODE = "R806.5"

#: Table R806.5, "Insulation for Condensation Control" — the minimum R-value of rigid board
#: or air-impermeable insulation, by climate zone. The values are a dew-point calculation
#: reduced to a table: enough R outboard of (or against) the sheathing that the first
#: condensing surface stays above the interior dew point through the heating season.
TABLE_R806_5: dict[str, float] = {
    "1": 5.0, "2": 5.0, "3": 5.0, "4C": 10.0, "4A": 15.0, "4B": 15.0,
    "5": 20.0, "6": 25.0, "7": 30.0, "8": 35.0,
}

#: Minnesota is zones 6 and 7; the MN 2024 residential rule set this package implements is
#: written for 6, which is where the metro sits. Same hard-coding, same reason, as
#: ``mn_energy.MN_ZONE_6`` — and the finding always prints the zone-7 row beside it so a
#: roof designed for a zone-6 minimum cannot quietly move north.
CLIMATE_ZONE = "6"
NEIGHBOURING_ZONE = "7"

#: IRC R702.7.1 Class I is <= 0.1 perm; Class II is <= 1.0 perm. Item 4 asks the air-
#: impermeable insulation to be Class II *or tighter*, and item 2 forbids a Class I layer on
#: the ceiling side.
CLASS_I_MAX_PERMS = 0.1
CLASS_II_MAX_PERMS = 1.0


@dataclass(frozen=True)
class R806_5_Result:
    """What R806.5 makes of one roof assembly.

    ``item`` names the arrangement of item 5 the assembly is built to ("5.1", "5.2", "5.3")
    or is ``None`` when it matches none of them. ``deck_contact_r`` is the R of the air-
    impermeable insulation the table governs — above the deck for 5.1, against its underside
    for 5.2/5.3 — and ``None`` when there is none to measure.
    """

    item: str | None
    required_r: float
    deck_contact_r: float | None
    #: Class of the tightest air-impermeable insulation ("I"/"II"), or None when unrated.
    air_impermeable_class: str | None
    #: The ceiling-side Class I retarder item 2 forbids, named — or None where there is none.
    interior_class_i_layer: str | None
    #: Inputs the library could not supply, by material name. Non-empty means UNKNOWN.
    missing: tuple[str, ...]

    @property
    def meets_table(self) -> bool:
        return self.deck_contact_r is not None and self.deck_contact_r + 1e-6 >= self.required_r

    @property
    def complies(self) -> bool:
        """Every condition of R806.5 this module can grade, together."""
        return (not self.missing and self.item is not None and self.meets_table
                and self.interior_class_i_layer is None
                and (self.item == "5.1" or self.air_impermeable_class in {"I", "II"}))

    @property
    def deck_contact_insulation(self) -> bool:
        """Item 5.2/5.3 — the air-impermeable layer is against the sheathing, not above it.

        This is the property :mod:`~typehaus.checks.building_science.condensation` keys on:
        it is the arrangement in which the code says outward drying is not required, so a
        Glaser walk demanding one is grading a criterion the section replaced.
        """
        return self.item in {"5.2", "5.3"}


def _outermost_structure(layers: list[Layer]) -> int | None:
    """Index of the last STRUCTURE layer — the rafter bay, in an interior->exterior stack."""
    found = None
    for index, layer in enumerate(layers):
        if layer.function is LayerFunction.STRUCTURE:
            found = index
    return found


def _permeance(material_ref: str, thickness_in: float, library: Library,
               missing: list[str]) -> float | None:
    material = library.material(material_ref)
    if material is None:
        missing.append(material_ref)
        return None
    permeance = material.vapor_permeance_at(thickness_in)
    if permeance is None:
        missing.append(material.name)
    return permeance


def _retarder_class(permeance: float | None) -> str | None:
    if permeance is None or permeance < 0.0:
        return None
    if permeance <= CLASS_I_MAX_PERMS:
        return "I"
    if permeance <= CLASS_II_MAX_PERMS:
        return "II"
    return None


def r806_5_compliance(assembly: Assembly, library: Library,
                      zone: str = CLIMATE_ZONE) -> R806_5_Result:
    """Grade one roof assembly against R806.5 — pure, and shared with the condensation gate.

    Interior -> exterior throughout, which is the order both ``default_lining`` and
    ``layers`` are authored in. "Direct contact with the underside of the structural roof
    sheathing" is read literally: the bay's fills must reach the top of the bay, because a
    partly-filled bay leaves an air space between the last fill and the deck and the phrase
    then describes something the assembly does not have. That is not a technicality —
    crediting an unfilled remainder as "direct contact" would double-count the same depth as
    both insulation and condensation margin.
    """
    missing: list[str] = []
    required = TABLE_R806_5.get(zone, TABLE_R806_5[CLIMATE_ZONE])
    layers = list(assembly.default_lining) + list(assembly.layers)
    structure_index = _outermost_structure(layers)

    # Item 2: a Class I retarder anywhere on the ceiling side of the assembly — every layer
    # inboard of the rafter bay, which is the lining plus any interior board.
    interior_class_i: str | None = None
    for layer in layers[:structure_index if structure_index is not None else 0]:
        if _retarder_class(_permeance(layer.material_ref, layer.thickness.inches,
                                      library, missing)) == "I":
            interior_class_i = layer.name
            break

    bay_air_impermeable_r = 0.0
    bay_air_permeable_r = 0.0
    tightest_class: str | None = None
    deck_contact = False
    if structure_index is not None:
        bay = layers[structure_index]
        fills = bay.cavity_fills
        deck_contact = bool(fills) and (
            bay.cavity_filled_thickness.inches + 1e-6 >= bay.thickness.inches)
        for position, fill in enumerate(fills):
            material = library.material(fill.material_ref)
            thickness_in = bay.cavity_thickness(fill).inches
            if material is None or material.r_per_inch is None:
                missing.append(fill.material_ref)
                continue
            r_value = material.r_per_inch * thickness_in
            if not material.air_impermeable:
                bay_air_permeable_r += r_value
                continue
            # Only the OUTERMOST fill can be the one in contact with the sheathing; an
            # air-impermeable layer buried behind a batt is insulation, not the deck's
            # condensation control, and crediting it would read a stack inside out.
            if position == len(fills) - 1 and deck_contact:
                bay_air_impermeable_r += r_value
                tightest_class = _retarder_class(
                    _permeance(fill.material_ref, thickness_in, library, missing))

    # Item 5.1: rigid board / air-impermeable insulation ABOVE the deck. Everything outboard
    # of the last STRUCTURE layer that is an INSULATION layer of an air-impermeable material.
    above_deck_r = 0.0
    for layer in layers[(structure_index + 1) if structure_index is not None else 0:]:
        if layer.function is not LayerFunction.INSULATION:
            continue
        material = library.material(layer.material_ref)
        if material is None or material.r_per_inch is None:
            missing.append(layer.material_ref)
            continue
        if material.air_impermeable:
            above_deck_r += material.r_per_inch * layer.thickness.inches

    if bay_air_impermeable_r > 0.0:
        item = "5.3" if bay_air_permeable_r > 0.0 else "5.2"
        governing: float | None = bay_air_impermeable_r
    elif above_deck_r > 0.0:
        item, governing = "5.1", above_deck_r
    else:
        item, governing = None, None
    return R806_5_Result(
        item=item, required_r=required, deck_contact_r=governing,
        air_impermeable_class=tightest_class, interior_class_i_layer=interior_class_i,
        missing=tuple(dict.fromkeys(missing)),
    )


def _vented_eave_authored(ctx: CheckContext) -> bool:
    """Does the plan author a vented eave? Then R806.2, not R806.5, is the governing path.

    The same signal ``code.R806_2_attic_ventilation`` splits on, read the same way, so the
    two rules partition the roofs between them instead of both claiming one or neither.
    """
    from typehaus.model.trim import EaveSoffit, EaveTrim

    return any(
        (isinstance(element, EaveSoffit) and element.vented)
        or (isinstance(element, EaveTrim) and element.soffit_vented)
        for element in ctx.plan.all_elements()
    )


@check(Tier.CODE, CHECK_ID)
def unvented_roof_insulation(ctx: CheckContext) -> list[Finding]:
    """R806.5 — an unvented rafter assembly's insulation, placement and vapour retarders."""
    if _vented_eave_authored(ctx):
        return [_na(CHECK_ID, "the roof is vented (a vented eave is authored), so R806.2's "
                    "net-free-area path governs and R806.5 does not apply", (), CODE)]

    conditioned = {storey.tag for storey in ctx.plan.storeys
                   if _storey_is_conditioned(ctx.plan, storey.tag)}
    graded: dict[str, list[str]] = {}
    for roof in ctx.model.roofs:
        if getattr(roof, "storey", None) not in conditioned:
            continue
        graded.setdefault(roof.assembly, []).append(roof.tag)
    if not graded:
        return [_na(CHECK_ID, "no roof bounds conditioned space, so no assembly has an "
                    "interior side for R806.5 to govern", (), CODE)]

    out: list[Finding] = []
    for assembly_tag, roof_tags in graded.items():
        assembly = ctx.plan.library.resolve_assembly(assembly_tag)
        tags = tuple(roof_tags)
        if assembly is None:
            out.append(_unknown(CHECK_ID, f"roof assembly {assembly_tag!r} does not resolve",
                                tags, CODE))
            continue
        result = r806_5_compliance(assembly, ctx.plan.library)
        out.append(_finding(assembly_tag, tags, result))
    return out


def _zone_note(result: R806_5_Result) -> str:
    """The zone assumption, spelled out, with the zone-7 row beside it."""
    other = TABLE_R806_5[NEIGHBOURING_ZONE]
    clears = ("also clears" if result.deck_contact_r is not None
              and result.deck_contact_r + 1e-6 >= other else "does NOT clear")
    return (f"Table R806.5 zone {CLIMATE_ZONE} = R-{result.required_r:.0f} "
            f"({clears} the zone-{NEIGHBOURING_ZONE} row, R-{other:.0f})")


def _finding(assembly_tag: str, tags: tuple[str, ...], result: R806_5_Result) -> Finding:
    if result.missing:
        return _unknown(CHECK_ID, f"{assembly_tag}: missing R-value or permeance for "
                        + ", ".join(result.missing), tags, CODE)
    if result.item is None:
        return _fail(CHECK_ID, f"{assembly_tag}: unvented roof with no insulation in any "
                     "R806.5 item-5 arrangement — no air-impermeable insulation above the "
                     "deck (5.1) and none against its underside (5.2/5.3)", tags, CODE)
    if result.interior_class_i_layer is not None:
        return _fail(CHECK_ID, f"{assembly_tag}: item 2 — a Class I vapour retarder "
                     f"({result.interior_class_i_layer}) is installed on the ceiling side of "
                     "an unvented assembly, which seals the bay on both faces", tags, CODE)
    assert result.deck_contact_r is not None
    where = ("above the deck" if result.item == "5.1"
             else "in direct contact with the sheathing underside")
    if not result.meets_table:
        return _fail(CHECK_ID, f"{assembly_tag}: item {result.item} — R-"
                     f"{result.deck_contact_r:.1f} of air-impermeable insulation {where}, "
                     f"below the {_zone_note(result)}", tags, CODE)
    if result.item != "5.1" and result.air_impermeable_class not in {"I", "II"}:
        return _fail(CHECK_ID, f"{assembly_tag}: item 4 — in climate zone {CLIMATE_ZONE} the "
                     "air-impermeable insulation must itself be a Class II vapour retarder; "
                     "this one is not rated as one", tags, CODE)
    return _pass(CHECK_ID, f"{assembly_tag}: item {result.item} — R-"
                 f"{result.deck_contact_r:.1f} of air-impermeable insulation {where}"
                 + (f", rated Class {result.air_impermeable_class}"
                    if result.air_impermeable_class else "")
                 + f"; {_zone_note(result)}; no ceiling-side Class I retarder (item 2)",
                 CODE)
