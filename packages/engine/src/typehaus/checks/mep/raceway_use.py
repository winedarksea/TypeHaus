"""``mep.raceway_use`` -- where a raceway material may lie, 2026 NEC 362.12, 352.44 and 225.10.

* **ENT** (362.12): never in direct earth burial (a slab on or below grade is 362.10's own
  case and is not earth here), and exposed only where 362.10(1), (5) or (8) allows.
* **PVC** (352.44): an exposed run grows with temperature; where Table 352.44's growth over
  the exposed length reaches 1/4 in. an expansion fitting is needed. Straps are counted at
  table spacing, not placed, so the whole exposed length is read as one run (conservative).
  The swing is an assumption, ``PVC_SWING_F``: Minnesota's roughly -20 degF winter to a sun-warmed
  110 degF summer surface, 130 degF.
* **225.10**: a power branch circuit or feeder run on the outside of a building uses a
  listed method. EMT and PVC are on the list; ENT is not.

Support spacing (Tables 344.30(B), 352.30(B), 358.30) is a standing limit, not a gap: straps
are counted and billed at table spacing (``resolve/conduit_fittings.straps_for``), so nothing
is left to grade until a strap is placed by hand.
**ADVISORY**: the drawn run is a trunk, not the electrician's final routing.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, not_applicable, passed
from typehaus.checks.mep.conduit_burial import reaches
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.model.nec import NEC, cite
from typehaus.resolve.conduit_reaches import build_site, samples

_CID = "mep.raceway_use"
_STEP_FT = 0.25  # one sample per 3 in.
#: PVC growth, 3.38e-5 in/in/degF (352.44): in. per 100 ft per degF is 0.04056.
PVC_GROWTH_IN_PER_100FT_F = 0.04056
PVC_SWING_F = 130.0
_EXPANSION_LIMIT_IN = 0.25
_POWER_BRANCH = ("power_120", "power_240")


def _all_samples(model) -> dict:
    """``reaches`` skips derived runs; the floor-heat ENT leads are derived, so add them."""
    held = dict(reaches(model))
    derived = [r for r in model.conduits
               if r.derived is not None and r.material == "ent" and r.z_m is not None]
    if derived:
        site = build_site(model)
        for run in derived:
            held[run.tag] = samples(model, run, site)
    return held


@check(Tier.ADVISORY, _CID)
def raceway_use(ctx: CheckContext) -> list[Finding]:
    """ENT out of earth and exposed use, PVC expansion, and 225.10 on outdoor power runs."""
    by_tag = _all_samples(ctx.model)
    out: list[Finding] = []
    ents = pvcs = exposed_power = 0
    for run in sorted(ctx.model.conduits, key=lambda r: r.tag):
        group = by_tag.get(run.tag, [])
        kinds = {s.kind for s in group}
        open_ft = sum(1 for s in group if s.kind == "open") * _STEP_FT
        if run.material == "ent":
            ents += 1
            code = cite(NEC.ENT_NOT_PERMITTED)
            if "earth" in kinds:
                out.append(advisory(
                    _CID, f"ADVISORY - {run.tag} (ENT) lies in earth; ENT is not permitted "
                          "in direct earth burial", (run.tag,), Result.ADVISORY, code=code,
                    fix="use PVC or EMT with approved protection (358.10(B)(1))"))
            elif open_ft:
                out.append(advisory(
                    _CID, f"ADVISORY - {run.tag} (ENT) runs {open_ft:.1f} ft exposed outdoors; "
                          "ENT may be exposed only where 362.10(1), (5) or (8) allows",
                    (run.tag,), Result.ADVISORY, code=code,
                    fix="conceal it, or change the run to EMT or PVC"))
        elif run.material == "pvc" and open_ft:
            pvcs += 1
            growth = PVC_GROWTH_IN_PER_100FT_F * PVC_SWING_F * open_ft / 100
            if growth >= _EXPANSION_LIMIT_IN:
                out.append(advisory(
                    _CID, f"ADVISORY - {run.tag} (PVC) is {open_ft:.1f} ft exposed: "
                          f"{growth:.2f} in. of growth over a {PVC_SWING_F:.0f} degF swing "
                          "reaches the 1/4 in. that calls for an expansion fitting "
                          "(read as one run)", (run.tag,), Result.ADVISORY,
                    code=cite(NEC.PVC_EXPANSION), fix="add an expansion fitting"))
        if run.service in _POWER_BRANCH and open_ft:
            exposed_power += 1
            if run.material == "ent":
                out.append(advisory(
                    _CID, f"ADVISORY - {run.tag} is a power run exposed on the outside of a "
                          "building and ENT is not a 225.10 wiring method", (run.tag,),
                    Result.ADVISORY, code=cite(NEC.EXTERIOR_WIRING_METHODS)))
    if out:
        return out
    if not (ents or pvcs or exposed_power):
        return [not_applicable(_CID, "no ENT, no exposed PVC and no power raceway on the "
                               "outside of a building is authored",
                               code=cite(NEC.ENT_NOT_PERMITTED, NEC.PVC_EXPANSION,
                                         NEC.EXTERIOR_WIRING_METHODS))]
    notes = [f"{ents} ENT runs lie in walls or floors, none in earth or exposed"]
    notes.append(f"{pvcs} exposed PVC runs stay under 1/4 in. of growth" if pvcs
                 else "no PVC run is exposed")
    notes.append(f"{exposed_power} exposed power runs use a 225.10 method" if exposed_power
                 else "no power run is exposed on a building")
    return [passed(_CID, "; ".join(notes),
                   code=cite(NEC.ENT_NOT_PERMITTED, NEC.PVC_EXPANSION,
                             NEC.EXTERIOR_WIRING_METHODS))]
