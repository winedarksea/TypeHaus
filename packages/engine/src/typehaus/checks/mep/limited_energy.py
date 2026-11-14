"""``electrical.limited_energy_wiring`` — Class 2 and data raceways, NEC 2026 Article 722.

Two readings, both ADVISORY (the model authors no cable, so neither is a permit gate):

* 722.15(A): a limited-energy raceway may not carry power conductors. ``ConduitRun.service`` is
  one value, so a run cannot say both; the one way to author a mix is a data or Class 2
  (``power_24``) run that names a power circuit, which grades ADVISORY. Spacing inside boxes
  and between cables is not modelled, and 722.15(G) (power in a raceway or NM/MC/UF) excuses
  the 2 in. in a house anyway. Read here as lifting the spacing, not the same-raceway ban.
* 722.2(B): cable in a wet location is wet-listed or metal-sheathed. A run with any stretch in
  the open outdoors (``resolve/conduit_reaches.py``) is a wet location. It passes where every
  ``ConduitRun.cables`` entry is datasheet wet-listed; with no cables authored it is UNKNOWN,
  and a cable that is not wet-listed is ADVISORY. A run with no authored z is a gap.
* 722.131(L): limited-use cable (a type ending in X) only under 1/4 in. in a dwelling.

Class 2 cable rating (722.140(A)(3)) and source marking (721.30, unread), PoE ampacity
(Table 722.140(B)(2)), strapping to a raceway
(722.133(C), 722.135(B)) and the 5 ft pool zone (722.135(B), 680.11) are not graded: no cable,
bundle, support or spa shell is modelled (``docs/nec-2026-paraphrase-722.md``).
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable, passed, unknown
from typehaus.checks.mep.conduit_burial import reaches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite

_CID = "electrical.limited_energy_wiring"
_LIMITED = ("data", "power_24")  # structured cabling; Class 2 DC lighting and RSD feeds
_WET_KINDS = ("open", "earth")  # outdoors above grade, or buried
_LIMITED_USE_MAX_M = 0.25 * 0.0254  # 722.131(L), read as 1/4 in.


@check(Tier.ADVISORY, _CID)
def limited_energy_wiring(ctx: CheckContext) -> list[Finding]:
    runs = [r for r in ctx.model.conduits if r.derived is None and r.service in _LIMITED]
    if not runs:
        return [not_applicable(_CID, "no data or Class 2 raceway is modelled",
                               code=cite(NEC.LIMITED_ENERGY_SEPARATION))]
    sep = cite(NEC.LIMITED_ENERGY_SEPARATION, NEC.LIMITED_ENERGY_IN_RACEWAY)
    wet_code = cite(NEC.LIMITED_ENERGY_WET)
    out: list[Finding] = []
    mixed = [r for r in runs if r.circuits]
    for run in mixed:
        out.append(advisory(
            _CID, f"ADVISORY — {run.tag} is a {run.service} raceway that names power circuit(s) "
                  f"{', '.join(run.circuits)}: limited-energy cable may not share a raceway with "
                  "power conductors (722.15(A)) unless a barrier, or power solely for the "
                  "equipment at 1/4 in. (722.15(B), (D))", (run.tag,), Result.ADVISORY,
            code=sep, fix="give the power circuit its own raceway"))
    clean = tuple(sorted(r.tag for r in runs if not r.circuits))
    if clean:
        out.append(passed(
            _CID, f"{len(clean)} data / Class 2 raceways each carry one service and name no power "
                  "circuit, so none shares a raceway with power (722.15(A)); spacing in boxes "
                  "and between cables is not modelled", clean, code=sep))
    by_tag = reaches(ctx.model)
    cables = {r.tag: getattr(ctx.plan.by_tag(r.tag), "cables", ()) for r in runs}
    wet = sorted(r.tag for r in runs if any(s.kind in _WET_KINDS for s in by_tag.get(r.tag, ())))
    unplaced = tuple(sorted(r.tag for r in runs if r.z_m is None))
    bare = tuple(t for t in wet if not cables[t])
    listed = tuple(t for t in wet if cables[t] and all(c.wet_location for c in cables[t]))
    dry = tuple(t for t in wet if cables[t] and t not in listed)
    if listed:
        names = sorted({c.source.split(";")[0] if c.source else (c.cable_type or "cable")
                        for t in listed for c in cables[t]})
        out.append(passed(
            _CID, f"{len(listed)} limited-energy raceways run outdoors, a wet location, and "
                  "every cable in them is listed for wet locations by its datasheet "
                  f"(722.2(B)): {'; '.join(names)}", listed, code=wet_code))
    if dry:
        out.append(advisory(
            _CID, f"ADVISORY — {', '.join(dry)} run outdoors and carry cable not listed for "
                  "wet locations (722.2(B))", dry, Result.ADVISORY, code=wet_code,
            fix="use wet-listed or metal-sheathed cable"))
    if bare:
        out.append(unknown(
            _CID, f"{len(bare)} limited-energy raceways run outdoors, a wet location, and the "
                  "model authors no cable type: the cable must be marked \"wet location\" or "
                  "have a moisture-impervious metal sheath (722.2(B), 722.100(C))", bare,
            code=wet_code, fix="author ConduitRun.cables"))
    wide_x = tuple(sorted(t for t in cables for c in cables[t]
                          if (c.cable_type or "").upper().endswith("X")
                          and c.outside_diameter is not None
                          and c.outside_diameter.meters > _LIMITED_USE_MAX_M))
    if wide_x:
        out.append(advisory(
            _CID, f"ADVISORY — {', '.join(wide_x)} carry limited-use (X) cable 1/4 in. or more "
                  "in diameter, which a dwelling does not permit (722.131(L))", wide_x,
            Result.ADVISORY, code=cite(NEC.COMMS_DWELLING), fix="use CM, CMR or CMP cable"))
    if unplaced:
        out.append(unknown(
            _CID, f"{len(unplaced)} limited-energy raceways author no z, so whether they leave "
                  "the building (722.2(B)) cannot be read", unplaced, code=wet_code,
            fix="author ConduitRun.elevations"))
    return out
