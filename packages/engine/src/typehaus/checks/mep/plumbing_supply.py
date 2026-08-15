"""Supply-side plumbing checks — the potable water leaving the meter.

Frost-free hydrants (bury depth, and the freeze protection an envelope can substitute for
it), hot-water pipe insulation, and the house's own rule for what visible supply pipe is
made of. Nothing here grades a drain: waste and vent live in ``plumbing_dwv``, and the
cast-in-place geometry both sides share lives in ``plumbing_concrete``.
"""

from __future__ import annotations

from typehaus.checks._authoring import failed as _fail
from typehaus.checks._authoring import passed as _pass
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.mep.plumbing_common import _M_TO_FT, _advisory_fail
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding
from typehaus.model.enums import PipeAccessoryKind, PipeSystem, Service
from typehaus.quantities import M_PER_IN

# N1103.4.2's bore threshold for hot-water pipe insulation: 3/4" nominal and larger.
_INSULATION_MIN_BORE_M = 0.01905


# A frost-free hydrant's shutoff has to sit below the frost line, not merely below grade:
# the whole point of the fixture is that the valve is deep enough never to freeze and the
# barrel drains back to it. 72" is the bury this project specifies; MN frost design is 42",
# so the margin is deliberate and the check holds the authored number rather than the code
# minimum — a hydrant ordered with a 6' bury and installed at 4' is the defect.
_HYDRANT_BURY_M = 1.8288  # 72"


@check(Tier.CODE, "mep.hydrant_freeze_depth")
def hydrant_freeze_depth(ctx: CheckContext) -> list[Finding]:
    """A frost-free hydrant's supply must stay below frost for its whole buried length.

    Three things make a hydrant frost-free, and this check reports honestly on all three
    rather than passing silently on the two it cannot see:

    1. **Bury depth at the shutoff** — geometric, and a hard FAIL. The valve is at the deep
       end of the supply run; if that end is shallower than the specified bury, the fixture
       is not frost-free no matter what was ordered.
    2. **No high point along the run** — also geometric, also a FAIL. This is the failure
       people actually get: a supply routed up into the building and back down freezes at
       the high point even though both ends are deep. A run whose shallowest point is above
       frost has a freeze there.
    3. **The interior shutoff and the outlet's vacuum breaker** — now real elements
       (``PipeAccessory``), so this reports what is authored rather than the UNKNOWN it used
       to emit because "the model has no valve or backflow-preventer element".

    Points 1 and 2 are about a *yard* hydrant, which is the only kind that has a bury depth.
    A wall hydrant's seat is inside the conditioned envelope, so it has none at all, and
    holding it to 72" would be grading it against a protection strategy it does not use.
    Those are exempted here — declared by a PENETRATION_SEAL naming the hydrant — and graded
    by ``mep.exterior_hydrant_protection`` on the things that do keep them from freezing.
    """
    cid = "mep.hydrant_freeze_depth"
    types = {t.tag: t for t in ctx.plan.library.fixture_types}
    hydrants = [
        element for storey in ctx.plan.storeys
        for element in ctx.plan.storey_elements(storey.tag)
        if element.element_kind == "Fixture"
        and (types.get(element.type_ref) is not None
             and Service.WATER_COLD in types[element.type_ref].needs
             and (types[element.type_ref].plan_symbol == "hydrant"))
    ]
    if not hydrants:
        return []

    grade = ctx.plan.project.site.grade.meters
    supply = [run for run in ctx.model.pipe_runs if run.system == PipeSystem.WATER_COLD.value]
    envelope_protected = _envelope_protected_hydrants(ctx)
    out: list[Finding] = []
    for hydrant in hydrants:
        if hydrant.tag in envelope_protected:
            seals = ", ".join(sorted(s.tag for s in envelope_protected[hydrant.tag]))
            out.append(_pass(
                cid, f"{hydrant.tag} is a wall hydrant: its seat is inside the conditioned "
                     f"envelope (sealed at {seals}), so it has no bury depth to grade — "
                     "see mep.exterior_hydrant_protection",
                (hydrant.tag,)))
            continue
        feeds = [run for run in supply if hydrant.tag in run.serves]
        if not feeds:
            out.append(_fail(cid, f"hydrant {hydrant.tag} has no WATER_COLD supply run "
                                  "serving it — nothing carries water to it, and nothing "
                                  "records how deep its shutoff sits",
                             (hydrant.tag,)))
            continue
        for run in feeds:
            if run.z_m is not None and len(run.z_m) >= 2:
                # Walk every vertex, not just the endpoints — a routed run freezes at its
                # shallowest point anywhere along it. The terminal standpipe (a repeated
                # final plan point rising through the slab) is the hydrant's own barrel,
                # which self-drains to the buried shutoff: it is exempt by design.
                #
                # Exactly one vertex, which is why this is an `if` and not the `while` it
                # was until 2026-08-15. The condition tests fixed indices — `run.path[-1]`
                # and `[-2]` — so a loop never advances past the standpipe it is meant to
                # drop; it just keeps eating whatever rising tail the run has, exempting
                # the very high point rule 2 exists to catch. It went unnoticed while
                # PR-G-HYDRANT-CW had four buried vertices to hide behind. Straightening
                # that run to (entry → hydrant → rise) left the tail one vertex long and
                # the bug graded a run surfacing to -1'-0" as frost-protected.
                elevations = list(run.z_m)
                if (len(elevations) >= 2 and len(run.path) >= 2
                        and run.path[-1] == run.path[-2]
                        and elevations[-1] > elevations[-2] + 1e-9):
                    elevations.pop()
            else:
                elevations = [z for z in (run.z_start_m, run.z_end_m) if z is not None]
            if not elevations:
                out.append(_unknown(cid, f"supply run {run.tag} authors no elevations, so "
                                         "its bury depth cannot be evaluated",
                                    (hydrant.tag, run.tag)))
                continue
            deepest = grade - min(elevations)
            shallowest = grade - max(elevations)
            if deepest + 1e-9 < _HYDRANT_BURY_M:
                out.append(_fail(
                    cid, f"hydrant {hydrant.tag}'s shutoff is buried "
                         f"{deepest / M_PER_IN:.0f}\" on {run.tag}, under the "
                         f"{_HYDRANT_BURY_M / M_PER_IN:.0f}\" this fixture is specified for",
                    (hydrant.tag, run.tag)))
            elif shallowest + 1e-9 < _HYDRANT_BURY_M:
                out.append(_fail(
                    cid, f"supply run {run.tag} rises to {shallowest / M_PER_IN:.0f}\" "
                         f"below grade — above the {_HYDRANT_BURY_M / M_PER_IN:.0f}\" bury "
                         f"{hydrant.tag} needs. A supply line freezes at its high point, "
                         "not at its ends",
                    (hydrant.tag, run.tag)))
            else:
                out.append(_pass(
                    cid, f"{hydrant.tag} is fed by {run.tag} at "
                         f"{deepest / M_PER_IN:.0f}\" below grade over its whole length",
                    (hydrant.tag, run.tag)))
        # The penetration the supply comes up through: a hydrant whose sleeve is missing or
        # filed as a drain will be cored after the pour.
        sleeves = [s for s in ctx.model.sleeves if s.serves_fixture == hydrant.tag]
        if not sleeves:
            out.append(_fail(cid, f"hydrant {hydrant.tag} has no sleeve serving it — its "
                                  "supply has no pre-poured way through the slab",
                             (hydrant.tag,)))
        else:
            out.append(_pass(cid, f"{hydrant.tag} rises through {sleeves[0].tag}",
                             (hydrant.tag, sleeves[0].tag)))
        # Was an UNKNOWN reading "the model has no valve or backflow-preventer element, so
        # neither can be evaluated here". It has one now, so this reports what is actually
        # authored: a hydrant with both devices passes, and one missing either is named.
        # (The vacuum breaker's own code question is `mep.backflow_prevention`'s; what this
        # line answers is the pair the fixture type's `source` used to carry in prose.)
        shutoffs = [a for a in _hydrant_accessories(ctx, hydrant.tag)
                    if a.kind in (PipeAccessoryKind.SHUTOFF.value,
                                  PipeAccessoryKind.MAIN_SHUTOFF.value)]
        breakers = [a for a in _hydrant_accessories(ctx, hydrant.tag)
                    if a.kind == PipeAccessoryKind.VACUUM_BREAKER.value]
        if shutoffs and breakers:
            out.append(_pass(
                cid, f"{hydrant.tag} has an interior shutoff ({shutoffs[0].tag}) and a "
                     f"hose-bib vacuum breaker ({breakers[0].tag})",
                (hydrant.tag, shutoffs[0].tag, breakers[0].tag)))
        else:
            missing = ", ".join(
                label for label, found in (("an interior shutoff", shutoffs),
                                           ("a hose-bib vacuum breaker", breakers))
                if not found)
            out.append(_advisory_fail(
                cid, f"{hydrant.tag} has no {missing} authored as a PipeAccessory — it can "
                     "neither be isolated nor scheduled",
                (hydrant.tag,)))
    return out


def _hydrant_accessories(ctx: CheckContext, hydrant_tag: str) -> list:
    """Accessories that name this hydrant, or that sit on a run serving it."""
    feeds = {run.tag for run in ctx.model.pipe_runs if hydrant_tag in run.serves}
    return [a for a in ctx.model.pipe_accessories
            if hydrant_tag in a.serves or (a.pipe_ref in feeds and not a.serves)]


@check(Tier.CODE, "mep.hot_water_insulation")
def hot_water_insulation(ctx: CheckContext) -> list[Finding]:
    """IRC N1103.4.2 — R-3 insulation on hot-water piping 3/4" and larger.

    The bore threshold is the code's, not a house rule: below 3/4" the standing loss is
    small enough that the code does not ask, and insulating a 1/2" branch to a single
    lavatory buys almost nothing. A run at or above it must *say* what it is wrapped in;
    an unstated spec reads as bare pipe, because on site that is what it becomes.
    """
    cid = "mep.hot_water_insulation"
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system != PipeSystem.WATER_HOT.value:
            continue
        if run.diameter_m + 1e-9 < _INSULATION_MIN_BORE_M:
            continue
        if run.insulation:
            out.append(_pass(
                cid, f"hot run {run.tag} ({run.diameter_m / M_PER_IN:.2f}\") is insulated "
                     f"with {run.insulation} over {run.length_m * _M_TO_FT:.0f}'",
                (run.tag,)))
        else:
            out.append(_fail(
                cid, f"hot run {run.tag} is {run.diameter_m / M_PER_IN:.2f}\" and authors "
                     "no insulation — N1103.4.2 requires R-3 on hot-water piping 3/4\" and "
                     "larger", (run.tag,)))
    return out


def _is_concrete_assembly(ctx: CheckContext, assembly_ref: str | None) -> bool:
    """True when the named assembly has a concrete layer
    (``resolve/construction_assemblies.py``)."""
    if not assembly_ref:
        return False
    assembly = next((a for a in ctx.plan.library.assemblies if a.tag == assembly_ref), None)
    if assembly is None:
        return False
    return any(layer.material_ref == "concrete" for layer in assembly.layers)


def _ceiling_above(ctx: CheckContext, point: tuple[float, float],
                   z: float) -> tuple[str, bool] | None:
    """What is directly overhead at ``point``: ``(tag, is_concrete)``, or None.

    "Directly overhead" is the *lowest* thing above the pipe whose plan outline contains it —
    a cast deck or a framed floor. That is what makes this rule survive a change it has to
    survive: swap ``SL-M-DECK`` for wood joists and every run under it stops being a run on
    concrete, with nothing here or in the plan source to edit.
    """
    from shapely.geometry import Point, Polygon

    probe = Point(point)
    best: tuple[float, str, bool] | None = None
    for solid in ctx.model.solids:
        if solid.category != "slab" or solid.z0_m <= z + 1e-6 or not solid.outline:
            continue
        if not Polygon(solid.outline).contains(probe):
            continue
        if best is None or solid.z0_m < best[0]:
            best = (solid.z0_m, solid.tag, _is_concrete_assembly(ctx, solid.assembly))
    for floor in ctx.model.floors:
        if floor.deck_z0_m <= z + 1e-6 or len(floor.deck_outline) < 3:
            continue
        if not Polygon(floor.deck_outline).contains(probe):
            continue
        if best is None or floor.deck_z0_m < best[0]:
            best = (floor.deck_z0_m, floor.tag, False)  # a framed deck is never concrete
    return (best[1], best[2]) if best is not None else None


@check(Tier.ADVISORY, "mep.pipe_material_preference")
def pipe_material_preference(ctx: CheckContext) -> list[Finding]:
    """The house's rule for what visible supply pipe is made of (``preferences.toml``).

    ADVISORY, deliberately: copper and PEX are both listed for potable water, so nothing
    here is a code question. It is a finish decision — lacquered copper reads as part of the
    room where the ceiling is a cast concrete deck and the pipe is simply *there* — and the
    reason it is a check rather than a comment is that a reroute would otherwise silently
    undo it.

    The rule is geometric, not a list of run tags: a basement supply run is "visible" when
    what is directly above it is concrete rather than a framed floor, and when it is not
    buried under the slab. Both halves matter. Change the deck to joists and the rule stops
    applying by itself; run a new trunk along the same ceiling and it applies to that too.
    """
    cid = "mep.pipe_material_preference"
    prefs = ctx.preferences.plumbing
    want_material = prefs.visible_basement_material
    if not want_material:
        return []  # the house states no rule; nothing to hold it to
    want_finish = prefs.visible_basement_finish
    out: list[Finding] = []
    for run in ctx.model.pipe_runs:
        if run.system not in (PipeSystem.WATER_COLD.value, PipeSystem.WATER_HOT.value):
            continue
        if run.storey != "basement" or run.z_m is None:
            continue
        exposed: list[str] = []
        for index in range(len(run.path) - 1):
            a, b = run.path[index], run.path[index + 1]
            if a == b:
                continue  # a vertical drop has no ceiling of its own
            if run.wall_refs and index < len(run.wall_refs) and run.wall_refs[index]:
                continue  # inside a stud cavity: covered, whatever it is made of
            mid = ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)
            z = (run.z_m[index] + run.z_m[index + 1]) / 2.0
            above = _ceiling_above(ctx, mid, z)
            if above is not None and above[1]:
                exposed.append(above[0])
        if not exposed:
            continue
        host = sorted(set(exposed))[0]
        # The *finish* half of the rule only applies to a pipe you can see. A run carrying
        # insulation is inside a jacket, and lacquering a surface nobody will ever look at
        # is paying for a finish twice — so an insulated run owes the material and not the
        # coating. The material still applies: it is what the insulation is clamped to, and
        # a hot trunk in copper is what the rest of the ceiling is made of.
        finish_applies = not run.insulation
        material_ok = run.material == want_material
        finish_ok = (not finish_applies) or (not want_finish) or run.finish == want_finish
        if material_ok and finish_ok:
            how = f"{(run.finish + ' ') if run.finish else ''}{run.material}"
            jacket = " (jacketed, so the finish rule does not apply)" if run.insulation else ""
            out.append(_pass(
                cid, f"{run.tag} runs exposed under {host} and is {how}{jacket}",
                (run.tag,)))
        else:
            have = f"{(run.finish + ' ') if run.finish else ''}{run.material or 'unstated'}"
            want = want_material if not finish_applies else (
                f"{(want_finish + ' ') if want_finish else ''}{want_material}")
            out.append(_advisory_fail(
                cid, f"{run.tag} runs exposed under the cast deck {host} and is {have}; "
                     f"the house's rule for supply pipe on concrete is {want} "
                     "(preferences.toml [plumbing])",
                (run.tag,)))
    return out


@check(Tier.ADVISORY, "mep.exterior_hydrant_protection")
def exterior_hydrant_protection(ctx: CheckContext) -> list[Finding]:
    """A hydrant protected by the envelope rather than by bury depth.

    There are two ways to keep a frost-free hydrant from freezing, and the house uses both.
    A *yard* hydrant puts its seat below the frost line and self-drains down to it — that is
    ``mep.hydrant_freeze_depth``'s question. A *wall* hydrant puts its seat inside the
    conditioned envelope and self-drains outward through the barrel, and its bury depth is
    zero because it has none; grading it against 72" would be asking the wrong question.

    What a wall hydrant is judged on instead is the penetration. The barrel is a cold metal
    tube through the assembly, so it wants the transition to PEX inside (thermal bridging),
    the exterior leg insulated, and the hole itself sealed — the gasket, the bracket and the
    closed-cell foam that ``PipeAccessory.install_parts`` carries. ADVISORY because these
    are detailing quality, not a code minimum; the code question a wall hydrant does have to
    answer is its vacuum breaker, and ``mep.backflow_prevention`` asks that one.
    """
    cid = "mep.exterior_hydrant_protection"
    out: list[Finding] = []
    for hydrant, seals in _envelope_protected_hydrants(ctx).items():
        feeds = [run for run in ctx.model.pipe_runs if hydrant in run.serves]
        insulated = [run.tag for run in feeds if run.insulation]
        if not insulated:
            out.append(_advisory_fail(
                cid, f"wall hydrant {hydrant} crosses the envelope at "
                     f"{', '.join(sorted(s.tag for s in seals))} and no run serving it "
                     "authors insulation — an uninsulated metal barrel through the "
                     "assembly is a thermal bridge that condenses on the cold side",
                (hydrant, *sorted(s.tag for s in seals))))
            continue
        kit = sorted({part for seal in seals for part in seal.install_parts})
        if not kit:
            out.append(_advisory_fail(
                cid, f"wall hydrant {hydrant}'s penetration seal "
                     f"{sorted(s.tag for s in seals)[0]} lists no install parts — the "
                     "gasket, mounting bracket and closed-cell foam are what make the "
                     "penetration airtight, and each is bought separately",
                (hydrant,)))
            continue
        out.append(_pass(
            cid, f"wall hydrant {hydrant} is envelope-protected: insulated on "
                 f"{', '.join(sorted(insulated))}, sealed with {', '.join(kit)}",
            (hydrant, *sorted(s.tag for s in seals))))
    return out


def _envelope_protected_hydrants(ctx: CheckContext) -> dict[str, list]:
    """Hydrant tag → the PENETRATION_SEAL accessories that carry it through the envelope.

    A seal names the hydrant in ``serves``. That naming is the whole discriminator between
    the two hydrant families, and it is deliberately explicit rather than derived from
    elevation: "this hydrant is protected by the envelope, and here is the sealed hole that
    says so" is a claim an author makes, not one geometry can infer — a yard hydrant's line
    also crosses a wall.
    """
    out: dict[str, list] = {}
    for accessory in ctx.model.pipe_accessories:
        if accessory.kind != PipeAccessoryKind.PENETRATION_SEAL.value:
            continue
        for served in accessory.serves:
            out.setdefault(served, []).append(accessory)
    return out
