"""NEC 690.12(C)(1)(b) — a dwelling's rapid-shutdown initiation device is outdoors.

Paraphrase and what else the printed 690.12 asks:
``docs/code-notes/nec-2026-paraphrase-690-705-710.md``.
The device is the ``ElectricalDeviceType.rsd_initiator`` one; "outdoors" is the position
covered by no room's axis cell, the same test ``code.NEC_250_94_ibt`` uses for entering data.
Not graded here: readily accessible, the (C)(1)(a) device kinds and the (D) labels.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite
from typehaus.resolve.room_lookup import room_owning

CID = "code.NEC_690_12_initiation"


@check(Tier.CODE, CID)
def rsd_initiation_outdoors(ctx: CheckContext) -> list[Finding]:
    """690.12(C)(1)(b) — initiation devices of a one- or two-family dwelling are outdoors.

    No PV module, or no dwelling among the buildings, is N/A. A dwelling with PV and no
    device typed ``rsd_initiator`` is UNKNOWN: the initiator may be the service disconnect,
    which 690.12(C)(1)(a) allows when the equipment's instructions name it.
    """
    code = cite(NEC.RAPID_SHUTDOWN_DWELLING)
    if not ctx.model.solar_panels:
        return [not_applicable(CID, "no PV module is modeled, so there is no rapid shutdown "
                                    "function to initiate", code=code)]
    buildings = ctx.plan.project.buildings
    if buildings and not any(b.kind == "dwelling" for b in buildings):
        return [not_applicable(CID, "no building is a dwelling; the outdoor-location rule is "
                                    "for one- and two-family dwellings", code=code)]
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    found = sorted((o for o in ctx.model.canvas_objects
                    if getattr(types.get(o.type_ref or ""), "rsd_initiator", False)),
                   key=lambda o: o.tag)
    if not found:
        return [unknown(CID, "PV is modeled but no device is typed rsd_initiator, so the "
                        "initiation device and its location are not known", (), code,
                        fix="type the initiation switch with rsd_initiator=True, or say the "
                            "service disconnect initiates (it is outdoors on a dwelling)")]
    out: list[Finding] = []
    for obj in found:
        if room_owning(ctx.model, obj.storey, obj.position) is None:
            out.append(passed(CID, f"{obj.tag} initiates rapid shutdown from outdoors", (obj.tag,),
                              code))
        else:
            out.append(failed(CID, f"{obj.tag} stands inside a room, but a dwelling's rapid "
                              "shutdown initiation device goes outdoors", (obj.tag,), code,
                              fix="move it to an exterior wall face, outside"))
    return out
