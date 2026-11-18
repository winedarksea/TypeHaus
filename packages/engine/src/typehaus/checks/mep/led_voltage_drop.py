"""``electrical.led_voltage_drop``: a 24 V run is fed within its drop budget (#137).

FAIL when the run's derived leads (``resolve/led_leads.py``) drop more than the
``LedStandard``'s ``max_drop_pct``, when no stocked cable keeps a leg in budget, or when the
run is longer than its tape's single-feed ``max_feed_length``. UNKNOWN with no standard, or
where the tape's feed limit is unread.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.mep.led_gear_access import led_standard
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.resolve.led_leads import lead_drop_pct

_CID = "electrical.led_voltage_drop"
_FT = 0.3048


@check(Tier.ADVISORY, _CID)
def led_voltage_drop(ctx: CheckContext) -> list[Finding]:
    standard = led_standard(ctx.plan)
    if standard is None:
        return [unknown(_CID, "no LedStandard: the house states no 24 V cable or drop limit")]
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    fed = {lead.run_ref: lead for lead in ctx.model.led_leads if lead.leg == "feed"}
    out: list[Finding] = []
    graded = 0
    for run in ctx.model.light_runs:
        lead = fed.get(run.tag)
        if lead is None:
            continue
        strip = types[run.type_ref].strip
        drop = lead_drop_pct(ctx.model, run.tag)
        if lead.awg is None or drop is None:
            out.append(advisory(_CID, f"{run.tag}: no stocked cable keeps its "
                                      f"{lead.length_m / _FT:.0f}' lead within "
                                      f"{standard.max_drop_pct:g}% at {lead.current_a:.2f} A",
                                (run.tag,), Result.FAIL))
            continue
        if drop > standard.max_drop_pct + 1e-6:
            out.append(advisory(_CID, f"{run.tag}: its leads drop {drop:.2f}%, over "
                                      f"{standard.max_drop_pct:g}%", (run.tag,), Result.FAIL))
            continue
        if strip.max_feed_length is None:
            out.append(unknown(_CID, f"{run.tag}: leads drop {drop:.2f}%, but the tape's "
                                     "single-feed length is unread", (run.tag,)))
            continue
        if run.length_m > strip.max_feed_length.meters + 1e-6:
            out.append(advisory(_CID, (
                f"{run.tag} is {run.length_m / _FT:.1f}' from one feed, past the tape's "
                f"{strip.max_feed_length.meters / _FT:.1f}': feed it from both ends"),
                (run.tag,), Result.FAIL))
            continue
        graded += 1
    if graded and not any(f.result is Result.FAIL for f in out):
        out.append(passed(_CID, f"{graded} runs are fed within {standard.max_drop_pct:g}% "
                                "and their tape's single-feed length"))
    if not out:
        out.append(unknown(_CID, "no derived 24 V leads"))
    return out
