"""``mep.conduit_bend_total`` — bend degrees between pull points, against NEC's 360°.

Every raceway article (358.26 EMT, 352.26 PVC, 344.26 RMC, 342.26 IMC, 362.26 ENT) caps
the bends between pull points at the equivalent of four quarter bends. The measurement is
``resolve/conduit_pulls.py``; this module only grades it.

**ADVISORY, PASS-with-a-prefix**, the way ``mep.vent_grade_margin`` reports a thin grade
and ``hvac_sizing`` an over-sized unit: this model draws trunks, not the electrician's
final bends, so an over-limit section is a design prompt (add a box, straighten the run)
and never a permit line.
"""

from __future__ import annotations

from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.resolve.conduit_pulls import MAX_BEND_DEG_BETWEEN_PULLS, PullSection, pull_sections

_CID = "mep.conduit_bend_total"
# Every raceway bills as EMT (resolve/pipe_sections.py); the siblings say the same thing.
_CODE = "NEC 358.26 (EMT; also 342.26/344.26/352.26/362.26)"
_ADVISORY = "ADVISORY — "


def _describe(section: PullSection) -> str:
    runs = " + ".join(section.run_tags)
    bends = ", ".join(f"{bend.degrees:.0f}°" for bend in section.bends) or "no bends"
    return (f"raceway {runs} from {section.starts_at} to {section.ends_at}: "
            f"{section.total_deg:.1f}° of bends ({bends})")


@check(Tier.ADVISORY, _CID)
def conduit_bend_total(ctx: CheckContext) -> list[Finding]:
    """No more than 360° of bends between pull points, per pull-to-pull section."""
    runs = list(ctx.model.conduits)
    if not runs:
        return [_na(_CID, "this model draws no conduit, so no raceway has bends to count",
                    code=_CODE)]
    out: list[Finding] = []
    for section in pull_sections(runs):
        if not section.gradable:
            out.append(_unknown(
                _CID, f"raceway {' + '.join(section.run_tags)} has no authored per-vertex "
                      f"elevations on {', '.join(section.schematic_tags)} — its bends in z "
                      "are a drawing convention, not a measurement",
                section.run_tags, code=_CODE,
                fix="author ConduitRun.elevations, one per path vertex"))
            continue
        if section.total_deg <= MAX_BEND_DEG_BETWEEN_PULLS + 1e-6:
            out.append(_pass(_CID, _describe(section) + f", within the "
                                   f"{MAX_BEND_DEG_BETWEEN_PULLS:.0f}° between pull points",
                             section.run_tags, code=_CODE))
            continue
        out.append(_pass(
            _CID, _ADVISORY + _describe(section) + f" — over the "
            f"{MAX_BEND_DEG_BETWEEN_PULLS:.0f}° (four quarter bends) allowed between pull "
            "points; add a pull box/conduit body (ConduitRun.pull_points) or re-route",
            section.run_tags, code=_CODE))
    return out
