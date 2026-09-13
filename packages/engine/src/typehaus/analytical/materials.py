"""What E the analytical model uses for a member, and where that number came from.

Two sources, in this order and no third:

1. **A record that actually computed one.** ``EngineeringRecord.inputs`` carries
   ``E_adjusted`` where the calculation adjusted a published modulus for its own service
   conditions (wet use, duration). Publishing a dry-use E beside a calculation that used a
   wet one would put two answers in one file — the same rule ``emit/ifc/profiles`` states
   for the physical IFC's ``Pset_MaterialMechanical``.
2. **A named assumption**, keyed by material and listed once in
   :attr:`AnalyticalModel.assumptions`. A reviewer is entitled to reject it; what they may
   not be asked to do is guess which one was used.

There is no third case: a material this table does not name reports its absence rather than
borrowing a neighbour's number.

**The material vocabulary is ``emit/ifc/profiles.material_name``'s, restated here.** This
package is a leaf and may not import ``emit``; the parse is seven suffixes and a fallback,
and the duplication is deliberate and small. If one moves, move the other — the two must
name the same material for the same size string or the physical IFC and the analytical
model will disagree about what a member is made of.
"""

from __future__ import annotations

import math

#: psi -> Pa. The graph is SI throughout; every psi in this module converts here and nowhere
#: else.
PSI_TO_PA = 6894.757293168361

#: Size-string suffix -> material name. Longest match wins, as in ``emit/ifc/profiles``.
_ENGINEERED = (
    ("24f-v5m1", "structural glulam 24F-V5M1/SP"),
    ("glb", "structural glulam"),
    ("lvl", "laminated veneer lumber"),
    ("psl", "parallel strand lumber"),
    ("lsl", "laminated strand lumber"),
    ("tji", "wood I-joist"),
    ("i-joist", "wood I-joist"),
)

#: A member with no product suffix. NOT a species and not a grade — this engine authors
#: neither, and inventing one in a file a PE reads would be a claim nobody checked.
_SAWN = "sawn lumber"

#: material -> (E psi, the citation the assumption is made under). Reference values, and
#: every one of them lands in ``assumptions`` the first time it is used.
_ASSUMED_E_PSI: dict[str, tuple[float, str]] = {
    "structural glulam 24F-V5M1/SP": (1.8e6, "APA/AWC 24F glulam, E 1.8e6 psi"),
    "structural glulam": (1.8e6, "APA/AWC 24F glulam, E 1.8e6 psi"),
    "laminated veneer lumber": (2.0e6, "LVL, E 2.0e6 psi (typical published grade)"),
    "parallel strand lumber": (2.0e6, "PSL, E 2.0e6 psi (typical published grade)"),
    "laminated strand lumber": (1.55e6, "LSL, E 1.55e6 psi (typical published grade)"),
    "wood I-joist": (1.55e6, "wood I-joist flange, E 1.55e6 psi"),
    _SAWN: (1.4e6, "NDS Supplement Table 4A, SPF No.2, E 1.4e6 psi — species is not "
                   "authored in this model, so the softest common framing species is taken"),
}


def material_name(profile: str, concrete_fc_psi: float | None = None) -> str:
    """The material a reviewer should see, from what the model actually says."""
    if concrete_fc_psi:
        return f"concrete f'c {concrete_fc_psi:,.0f} psi"
    text = (profile or "").lower()
    for token, name in _ENGINEERED:
        if token in text:
            return name
    return _SAWN


def adjusted_moduli(engineering: object) -> dict[str, float]:
    """``element tag -> E_adjusted psi``, from the records that actually computed one.

    The same lookup ``emit/ifc/profiles._adjusted_moduli`` does, for the same reason: only
    a record may publish an E, because only a record knows the service conditions it was
    adjusted for.
    """
    moduli: dict[str, float] = {}
    if engineering is None:
        return moduli
    for item_id in sorted(engineering):  # type: ignore[call-overload]
        record = engineering[item_id]  # type: ignore[index]
        value = next((q.value for q in record.inputs if q.name == "E_adjusted"), None)
        if value:
            for tag in record.element_tags:
                moduli.setdefault(tag, float(value))
    return moduli


def modulus_for(material: str, *, record_e_psi: float | None = None,
                record_item: str = "", concrete_fc_psi: float | None = None,
                ) -> tuple[float, str, str | None]:
    """``(E in Pa, the basis line for the member, the assumption to register)``.

    The third element is ``None`` where the number came off a record — a computed E is not
    an assumption and must not be printed as one.
    """
    if record_e_psi:
        return (record_e_psi * PSI_TO_PA,
                f"record {record_item} E_adjusted {record_e_psi:,.0f} psi", None)
    if concrete_fc_psi:
        # ACI 318-19 19.2.2.1 for normalweight concrete. A modulus, not a strength: it is
        # the only term in this table that is derived rather than looked up.
        e_psi = 57000.0 * math.sqrt(concrete_fc_psi)
        basis = (f"assumed: ACI 318-19 19.2.2.1, 57000*sqrt(f'c) at f'c "
                 f"{concrete_fc_psi:,.0f} psi = {e_psi:,.0f} psi")
        return e_psi * PSI_TO_PA, basis, f"E: {basis[len('assumed: '):]}"
    entry = _ASSUMED_E_PSI.get(material)
    if entry is None:
        return 0.0, f"no modulus for {material!r}", None
    e_psi, citation = entry
    return e_psi * PSI_TO_PA, f"assumed: {citation}", f"E: {citation}"
