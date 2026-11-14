"""NEC 702.4(A) — an automatic standby source covers the load it carries (advisory).

Catlin's EG4 backup is read as both Article 702 (optional standby: the backup panel on the
inverter's load port) and Article 705 (the grid-interactive and island-mode side): 702.5(D)
sends parallel operation to 705. See ``docs/code-notes/nec-2026-paraphrase-702-705-island.md``.
Graded: the inverter's continuous output against all backup circuits at once (702.4(A)(2)(a))
and against the largest single one ((A)(3)). UNKNOWN: whether the inverter is listed as a PCS
(``EquipmentType.pcs_listed``), the PCS control setting and nonautomatic reconnection.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed, not_applicable, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.nec import NEC, cite

CID = "electrical.standby_capacity"


@check(Tier.ADVISORY, CID)
def standby_capacity(ctx: CheckContext) -> list[Finding]:
    from typehaus.takeoff.backup_calc import backup_runtime_summary

    code = cite(NEC.STANDBY_FULL_LOAD, NEC.STANDBY_MULTIMODE)
    summary = backup_runtime_summary(ctx.model)
    rows = [r for tier in (summary.get("tiers") or {}).values() for r in tier["circuits"]]
    if not summary.get("modeled") or not rows:
        return [not_applicable(CID, "no circuit is on a backup source, so there is no standby "
                                    "load to size a source against", (), code)]
    peak = summary["peak"]
    kw = peak["inverter_kw_continuous"]
    tags = tuple(sorted(str(r["circuit"]) for r in rows))
    if kw is None:
        return [unknown(CID, "backup circuits exist but no inverter declares "
                        "inverter_kw_continuous, so the source's capacity is unknown", tags, code,
                        "declare inverter_kw_continuous on the inverter's type")]
    capacity = kw * 1000.0
    total = float(peak["simultaneous_va"])
    top = max(rows, key=lambda r: float(r["connected_va"]))
    head = (f"{kw:g} kW continuous against {len(rows)} backup circuits at once ({total:,.0f} VA) "
            f"and the largest, {top['circuit']} ({float(top['connected_va']):,.0f} VA)")
    out: list[Finding] = []
    if capacity + 1e-9 >= total:
        out.append(passed(CID, head + ": covers the full connected load", tags, code))
    elif capacity + 1e-9 >= float(top["connected_va"]):
        out.append(unknown(CID, head + ": short of the full load, so only a PCS-listed "
                           "multimode inverter (702.4(A)(3)) can carry it", tags, code,
                           "declare pcs_listed on the inverter type, or shed load"))
    else:
        out.append(failed(CID, head + ": cannot carry the largest single load", tags, code,
                          fix="a larger inverter, or move that load off the backup panel"))
    types = {t.tag: t for t in ctx.plan.library.equipment_types}
    listed = [getattr(t, "pcs_listed", None) for t in types.values()
              if getattr(t, "inverter_kw_continuous", None)]
    if True in listed:
        what = ("the inverter is declared PCS-listed, but its control setting and "
                "nonautomatic reconnection after an overload shutdown are not authored")
    elif False in listed:
        what = "the inverter is declared not PCS-listed, so 702.4(A)(2) alone applies"
    else:
        what = ("whether the inverter is listed as a PCS, its control setting (capacity must "
                "be at least that) and nonautomatic reconnection after an overload shutdown "
                "are not authored")
    if False not in listed:
        out.append(unknown(CID, f"702.4(A)(3): {what}", tags, cite(NEC.STANDBY_MULTIMODE),
                           "author pcs_listed on the inverter type from its listing"))
    return out
