"""``electrical.limited_energy_wiring`` — Class 2 and data raceways, NEC 2026 Article 722.

Two readings, both ADVISORY (the model authors no cable, so neither is a permit gate):

* 722.15(A): a limited-energy raceway may not carry power conductors. ``ConduitRun.service`` is
  one value, so a run cannot say both; the one way to author a mix is a data or Class 2
  (``power_24``) run that names a power circuit, which grades ADVISORY. Spacing inside boxes
  and between cables is not modelled, and 722.15(G) (power in a raceway or NM/MC/UF) excuses
  the 2 in. in a house anyway. Read here as lifting the spacing, not the same-raceway ban.
* 722.2(B): cable in a wet location is wet-listed or metal-sheathed. A run with any stretch in
  the open outdoors (``resolve/conduit_reaches.py``) is a wet location; no cable type is
  authored, so it is UNKNOWN. A run with no authored z cannot be placed, so it is a gap.

Class 2 rating (722.140(A)(3)), PoE ampacity (Table 722.140(B)(2)), strapping to a raceway
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
    wet = tuple(sorted(r.tag for r in runs
                       if any(s.kind in _WET_KINDS for s in by_tag.get(r.tag, ()))))
    unplaced = tuple(sorted(r.tag for r in runs if r.z_m is None))
    if wet:
        out.append(unknown(
            _CID, f"{len(wet)} limited-energy raceways run outdoors, a wet location, and the "
                  "model authors no cable type: the cable must be marked \"wet location\" or "
                  "have a moisture-impervious metal sheath (722.2(B), 722.100(C))", wet,
            code=wet_code, fix="specify outdoor-rated (wet-listed) cable on these runs"))
    if unplaced:
        out.append(unknown(
            _CID, f"{len(unplaced)} limited-energy raceways author no z, so whether they leave "
                  "the building (722.2(B)) cannot be read", unplaced, code=wet_code,
            fix="author ConduitRun.elevations"))
    return out
