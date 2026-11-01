"""``structural.sill_bearing_on_core`` — a framed wall's sill bears on the concrete under it.

Three FAILs, graded per framed wall over every plate run it stands on:

* less than two-thirds of the sill's width over the concrete layer (the rest hangs over foam);
* a sill narrower than the studs it carries;
* a bolt-anchored sill (wider than ESR-2555's 2x4/2x6 MASAZ) with no anchor band inside BOTH
  the core (less ``MIN_BOLT_EDGE_M``) and the plate's middle third (IRC R403.1.6).

Bolts are not modelled; this grades that the allowed band exists and prints its offset, which
S-103 repeats. A strap-anchored sill carries no middle-third rule.
"""

from __future__ import annotations

from math import gcd

from typehaus.checks._authoring import failed, not_applicable, passed
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.hardware.catalog import ROLE_SILL_ANCHOR_BOLT
from typehaus.joints.sills import sill_anchor_role
from typehaus.resolve.sill_bearing import MIN_BEARING_FRACTION, SillBearing, sill_bearing

_CID = "structural.sill_bearing_on_core"
_CODE = "IRC R403.1.6"
_EPS = 1e-6


def _frac(inches: float) -> str:
    """``4.104`` -> ``4 1/8"`` (nearest 1/16)."""
    whole, sixteenths = divmod(round(inches * 16), 16)
    part = f"{sixteenths // gcd(sixteenths, 16)}/{16 // gcd(sixteenths, 16)}" if sixteenths else ""
    return f'{" ".join(str(x) for x in (whole or ("" if part else 0), part) if x != "")}"'


def problems(sb: SillBearing, bolted: bool) -> list[str]:
    out: list[str] = []
    if sb.fraction < MIN_BEARING_FRACTION - _EPS:
        out.append(f"only {_frac(sb.on_core_in)} of its {_frac(sb.sill_in)} bears on the core "
                   f"({sb.fraction:.0%}, under 2/3)")
    if sb.sill_in < sb.stud_in - _EPS:
        out.append(f"the {_frac(sb.sill_in)} plate is narrower than the {_frac(sb.stud_in)} stud")
    if bolted and sb.band is None:
        out.append("no anchor band lies inside both the core and the plate's middle third")
    return out


def anchor_note(sb: SillBearing) -> str:
    lo, hi = sb.band
    return (f"1/2\" bolts {_frac(lo)} to {_frac(hi)} in from the sill's outside edge "
            f"(nominal {_frac(sb.nominal_in)})")


@check(Tier.STRUCTURAL, _CID)
def sill_bearing_on_core(ctx: CheckContext) -> list[Finding]:
    by_wall: dict[str, list] = {}
    for ret in ctx.model.construction_returns:
        if ret.kind != "bearing_plate" or len(ret.element_tags) < 2:
            continue
        sb = sill_bearing(ctx.model, ret)
        if sb is not None:
            by_wall.setdefault(ret.element_tags[1], []).append((ret, sb))
    if not by_wall:
        return [not_applicable(_CID, "no framed wall stands on a concrete wall's core in this "
                                     "model", (), code=_CODE)]
    out: list[Finding] = []
    for tag, runs in sorted(by_wall.items()):
        worst = min(runs, key=lambda item: item[1].fraction)[1]
        bolted = any(sill_anchor_role(ret) == ROLE_SILL_ANCHOR_BOLT for ret, _ in runs)
        tags = (tag, *sorted({r.element_tags[0] for r, _ in runs}))
        bad = sorted({p for _, sb in runs for p in problems(sb, bolted)})
        if bad:
            out.append(failed(_CID, f"{tag}: the sill {'; '.join(bad)}", tags, code=_CODE,
                              fix="widen the sill (FramingSpec.sill_member) so it sits flush "
                                  "outside the studs and over the core"))
            continue
        extra = f"; {anchor_note(worst)}, middle third and core" if bolted else ""
        out.append(passed(_CID, f"{tag}: {_frac(worst.on_core_in)} of the {_frac(worst.sill_in)} "
                                f"sill bears on the core ({worst.fraction:.0%}){extra}", tags,
                          code=_CODE))
    return out


def sill_anchor_notes(model, storey: str) -> list[str]:
    """S-103's sill-anchor lines for one storey: the bolt offset the check grades."""
    seen: dict[tuple, SillBearing] = {}
    for ret in model.construction_returns:
        if (ret.kind != "bearing_plate" or ret.storey != storey
                or sill_anchor_role(ret) != ROLE_SILL_ANCHOR_BOLT):
            continue
        sb = sill_bearing(model, ret)
        if sb is not None and sb.band is not None:
            seen[(round(sb.sill_in, 3), tuple(round(v, 3) for v in sb.band))] = sb
    lines: list[str] = []
    for sb in seen.values():
        lines.append(f"SILL: {_frac(sb.sill_in)} PT PLATE FLUSH WITH THE STUD OUTSIDE FACE, "
                     f"{_frac(sb.on_core_in)} ON THE CONCRETE CORE; NOTCH ITS INSIDE EDGE 4\" "
                     "WIDE AT EACH STHD STRAP.")
        lines.append(f"SILL ANCHORS: 1/2\" BOLTS, 3\"x3\" PLATE WASHERS, {_frac(sb.band[0])} TO "
                     f"{_frac(sb.band[1])} IN FROM THE SILL'S OUTSIDE EDGE (NOMINAL "
                     f"{_frac(sb.nominal_in)}): IN THE PLATE'S MIDDLE THIRD AND THE CORE "
                     "(IRC R403.1.6).")
    return lines
