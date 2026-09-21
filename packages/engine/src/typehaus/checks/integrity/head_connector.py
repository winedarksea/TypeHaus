"""``Post.head_connector`` must quote the catalog's own numbers for the part it names.

``engineering/column_head_joint`` grades against values the house quotes, because
``engineering/`` may not read ``hardware/catalog``. Two places for one fact drift, so every
quoted number is compared with the catalog row here, at ERROR — the
``integrity.reinforcement_spec_agrees`` severity, for the same reason: the calculation reads
one spelling and the order buys the other.

The lateral figure quoted is the LOWER of the row's two directions (F1, F2): a value that
holds for one sign of the load only is not a capacity (``library/hardware.py``, HGAM10).
A ``set_rated`` connector quotes the catalog row as is: that row already records the set.
"""

from __future__ import annotations

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity

_CHECK_ID = "integrity.head_connector_agrees"
_TOLERANCE_LB = 0.5


def _catalog_lateral(allowable: object) -> float | None:
    values = [v for v in (getattr(allowable, "lateral_f1_lb", None),
                          getattr(allowable, "lateral_f2_lb", None)) if v is not None]
    return min(values) if values else None


def _differ(quoted: float | None, published: float | None) -> bool:
    if quoted is None or published is None:
        return quoted is not published
    return abs(quoted - published) > _TOLERANCE_LB


@check(Tier.INTEGRITY, _CHECK_ID)
def head_connector_agrees(ctx: CheckContext) -> list[Finding]:
    from typehaus.hardware.catalog import allowable_for_model, hardware_by_model

    findings: list[Finding] = []
    for post in ctx.plan.all_elements():
        head = getattr(post, "head_connector", None)
        if head is None:
            continue
        allowable = allowable_for_model(head.tie)
        if allowable is None:
            findings.append(_finding(
                post.tag, f"{post.tag}'s head_connector quotes {head.tie!r}, which has no "
                          "published-allowables record in the hardware catalog, so nothing "
                          "can confirm the numbers quoted for it",
                "catalog the part with its allowables, or name the part the catalog has"))
            continue
        pairs = (("uplift_lb", head.uplift_lb, getattr(allowable, "uplift_lb", None)),
                 ("lateral_lb", head.lateral_lb, _catalog_lateral(allowable)),
                 ("load_duration_factor", head.load_duration_factor,
                  getattr(allowable, "load_duration_factor", None)))
        for field, quoted, published in pairs:
            if _differ(quoted, published):
                findings.append(_finding(
                    post.tag, f"{post.tag}'s head_connector.{field} is {quoted!r} but the "
                              f"catalog's {head.tie} row publishes {published!r}",
                    "re-read the row and quote the catalog's value, or correct the catalog"))
        if head.bearing and hardware_by_model(head.bearing) is None:
            findings.append(_finding(
                post.tag, f"{post.tag}'s head_connector names bearing part {head.bearing!r}, "
                          "which the hardware catalog does not hold",
                "name the catalogued bearing part"))
    return findings


def _finding(tag: str, message: str, hint: str) -> Finding:
    return Finding(severity=Severity.ERROR, check_id=_CHECK_ID, message=message,
                   element_tags=(tag,), fix_hint=hint, result=Result.FAIL)
