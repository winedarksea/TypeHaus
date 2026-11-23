"""``structural.stacked_line_ladder`` — a wall over a wall along the joists has a ladder.

Grades ``ResolvedModel.stacked_ladders`` (``resolve/stacked_ladder.py``), the record the
header walk's "on the ladder" / "assumes a ladder" reads:

* PASS — every station within a joist module of the next (half a module at the run ends)
  is carried by a member already on the plate or by a block bearing on it;
* UNKNOWN — a station where nothing fits (the line load stays in the floor framing there).
  An open-web truss deck lays no block (a solid block between trusses is no published
  detail): its line passes only where a truss or an authored rim-board strip (a
  ``JoistReinforcement``, read at its TJ-8000 vertical row) already stands on the plate.
"""

from __future__ import annotations

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result

_CID = "structural.stacked_line_ladder"
_IN = 0.0254


@check(Tier.STRUCTURAL, _CID)
def stacked_line_ladder(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for line in getattr(ctx.model, "stacked_ladders", ()):
        tags = (line.floor, *line.lowers, *line.uppers)
        what = (f"{', '.join(line.uppers)} over {', '.join(line.lowers)}, along "
                f"{line.floor}'s joists ({line.member})")
        missing = [s for s in line.stations if s.status == "missing"]
        blocks = sum(1 for s in line.stations if s.status == "block")
        carriers = sorted({s.by for s in line.stations if s.status == "carried"})
        widest, ends = 0.0, 0.0
        for lo, hi in line.runs:  # gaps are per run: two runs on one line are not one span
            at = [s.at_m for s in line.stations if lo - _IN <= s.at_m <= hi + _IN]
            if at:
                widest = max([widest, *(b - a for a, b in zip(at, at[1:], strict=False))])
                ends = max(ends, at[0] - lo, hi - at[-1])
        spacing = (f"stations at most {widest / _IN:.1f}\" apart (module "
                   f"{line.spacing_m / _IN:.0f}\"), {ends / _IN:.1f}\" from a run end")
        held = f"{blocks} block(s) laid" + (f"; carried by {', '.join(carriers)}"
                                            if carriers else "")
        rows = sorted({s.detail for s in line.stations if s.detail})
        held += f" ({'; '.join(rows)})" if rows else ""
        if missing:
            gaps = "; ".join(f"x={s.at_m / _IN:.1f}\": {s.by}" for s in missing)
            out.append(_advisory(
                _CID, f"{what}: {len(missing)} station(s) carry nothing, so the line load "
                f"stays in the floor framing there ({gaps}); {held}", tags, Result.UNKNOWN,
                ("put the bearing line on the truss designer's layout (a strip of rim board "
                 "on edge, or a truss over the wall)" if line.open_web else
                 "move the runs off the plate, block the bay by hand, or size the joist for "
                 "the line load")))
            continue
        out.append(_advisory(_CID, f"{what}: {held}; {spacing}", tags, Result.PASS))
    return out
