"""Can a hung luminaire's product actually reach where it is drawn?

A pendant authored by ``elevation`` hangs wherever someone typed, and nothing tied that to
the product: a stairwell chandelier drew 8' below the rafters on a fixture whose cable was
never that long. This grades the resolved hang (body plus the cable over it, →
resolve/suspension.py) against the type's ``max_overall_height``. Advisory, like the rest of
the lighting family: WARN severity, so it shows red without tripping the permit gate.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks._authoring import not_applicable as _na
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.electrical import luminaire_types
from typehaus.resolve.suspension import FLUSH_M, hung_type

CID = "electrical.suspension_reach"
#: Slack on the product's own maximum, for rounding in a catalog's inch figure.
REACH_TOL_M = 0.003


def _inches(meters: float) -> str:
    return f'{meters / 0.0254:.1f}"'


@check(Tier.ADVISORY, CID)
def suspension_reach(ctx: CheckContext) -> list[Finding]:
    """Every hung luminaire's hang, canopy to body bottom, is one its product ships."""
    types = luminaire_types(ctx.plan.library)
    hung = [(item, product) for item in ctx.model.canvas_objects
            if (product := hung_type(types, item)) is not None]
    if not hung:
        return [_na(CID, "no pendant or chandelier on a ceiling mount in this building")]
    out: list[Finding] = []
    for item, product in hung:
        tags = (item.tag, product.tag)
        cable, host = item.suspension_m, item.suspended_from
        if cable is None:
            out.append(_unknown(CID, f"{item.tag}: nothing resolved plumb over it to hang "
                                "from", tags))
            continue
        if cable < -FLUSH_M:
            out.append(advisory(CID, f"{item.tag}: its {product.tag} body runs "
                                f"{_inches(-cable)} up through {host}", tags, Result.FAIL,
                                fix="lower the mount elevation, or shorten the type"))
            continue
        if cable <= FLUSH_M:
            out.append(_pass(CID, f"{item.tag}: canopy seated on {host} "
                             f"({_inches(cable)} off it)", tags))
            continue
        overall = cable + product.height.meters
        limit = getattr(product, "max_overall_height", None)
        if limit is None:
            out.append(_unknown(CID, f"{item.tag}: hangs {_inches(overall)} from {host} on "
                                f"{_inches(cable)} of cable, and {product.tag} states no "
                                "max_overall_height to hold it to", tags,
                                fix="author max_overall_height from the product sheet"))
        elif overall > limit.meters + REACH_TOL_M:
            out.append(advisory(CID, f"{item.tag}: needs {_inches(overall)} from {host} to "
                                f"its lowest point; {product.tag} ships "
                                f"{_inches(limit.meters)} at most", tags, Result.FAIL,
                                fix="raise the mount elevation, or pick a longer-drop unit"))
        else:
            out.append(_pass(CID, f"{item.tag}: hangs {_inches(overall)} from {host} "
                             f"({_inches(cable)} of cable), within {product.tag}'s "
                             f"{_inches(limit.meters)}", tags))
    return out
