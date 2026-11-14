"""``electrical.label_inputs`` — every derived NEC label can be printed from what is authored.

The labels are derived (``resolve/electrical_labels.py``); this grades only that each one has
what it prints. A house input it needs and the model lacks (705.10's emergency phone on the
``LabelStandard``, a battery's nominal voltage for 480.7(F)) is UNKNOWN, never defaulted.
Whether the label is installed is the inspector's walk, not a model fact.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import cite

_CID = "electrical.label_inputs"


@check(Tier.ADVISORY, _CID)
def label_inputs(ctx: CheckContext) -> list[Finding]:
    labels = list(ctx.model.electrical_labels)
    if not labels:
        return [not_applicable(_CID, "no PV, power source, battery, service, heating cable or "
                                     "remote EVSE breaker is modeled, so no NEC label is derived")]
    out: list[Finding] = []
    for label in labels:
        if label.missing:
            tags = (label.host_ref,) if label.host_ref else ()
            out.append(unknown(_CID, f"the {label.section} label at {label.host_ref} prints "
                                     f"{', '.join(label.missing)}, which is not authored", tags,
                               cite(label.section, *label.also),
                               fix="author it in the house; the engine holds no default"))
    complete = [lbl for lbl in labels if not lbl.missing]
    if complete:
        count = sum(lbl.quantity for lbl in complete)
        out.append(passed(_CID, f"{count} derived labels over {len(complete)} records have every "
                                "input they print (E-605)", (),
                          cite(*sorted({lbl.section for lbl in complete}))))
    return out
