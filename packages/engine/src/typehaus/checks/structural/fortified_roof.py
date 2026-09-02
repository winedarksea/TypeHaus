"""FORTIFIED Home (High Wind & Hail) Roof-level checklist items this model can grade.

FORTIFIED Roof certification is mostly paperwork — a PE letter here, a manufacturer's UL
test report there — and this module does not pretend otherwise: every finding it emits is
``[advisory, not engineering]`` and never a hard block, the same posture
``uplift_path.py`` already carries for the same reason (the model holds no design wind
speed, so "the part is there" is a different claim from "the part is adequate"). What is
worth checking mechanically is narrower still — whether the *parts the standard asks for*
are even modeled — and that is all three sub-checks below do:

* **sealed deck (§4.4)** — is there a MEMBRANE layer with a WATER control on the roof
  assembly, on a roof steep enough for it to apply? Presence, not ASTM/tape compliance —
  that is a documentation fact, not a modeled one, so presence tops out at UNKNOWN.
* **drip edge (§4.5)** — does every footprint edge (eave *and* rake) carry a
  ``Flashing(kind=DRIP_FLASHING)``? The standard wants both; a house that only trims its
  eaves is missing half the line item.
* **continuous load path (Silver §5.5.1 / Gold §6.4-adjacent, surfaced here because the
  owner asked for it even though it sits outside Roof-level scope)** — a re-labeling of
  ``uplift_path``'s own roof-bearing findings. This does not re-derive coverage: it imports
  the same findings that check already produced and reframes the roof-tagged subset under
  this checklist's own name, so there is exactly one source of truth for uplift coverage.

Scope is the conditioned envelope, the same slice
``building_science/condensation.py::conditioned_envelope_assemblies`` already draws for
"is this roof actually part of the certified dwelling" — an unconditioned detached garage
roof is not what a FORTIFIED Roof designation on the house covers, and grading it here
would fail a structure nobody is submitting for certification.

Deck **nailing schedule** (§4.2.2) is deliberately not a sub-check here: it would need a
speculative ``nail_spacing_in`` field nothing else in the model would consume, and the
honest answer — "this deck is screwed, not nailed, and needs a PE letter" — belongs in
``notes/fortified_roof_cert.md``, not in a UNKNOWN-forever finding.
"""

from __future__ import annotations

from typehaus.checks.building_science.condensation import conditioned_envelope_assemblies
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.uplift_path import uplift_path_coverage
from typehaus.findings import Finding, Result, Severity
from typehaus.model.enums import ControlLayer, LayerFunction, RoofForm, TrimKind
from typehaus.model.spatial import Roof
from typehaus.model.trim import Flashing

_ADVISORY = "[advisory, not engineering] "

#: These two rules grade PRESENCE — is a sealed underlayment layer in the assembly, is a
#: drip flashing on record — and cannot grade FORTIFIED compliance, because the
#: gauge, the ASTM/ICC listing and the fastening schedule are documentation facts
#: no model carries; the names say PRESENT so a PASS never claims the standard was met.
#: Deliberately NOT hoisted into the engineering register: what is outstanding
#: here is a submittal document, not a calculation, and an engineer's seal is the
#: wrong instrument for it.
_CHECK_SEALED_DECK = "structural.fortified_roof_sealed_deck_present"
_CHECK_DRIP_EDGE = "structural.fortified_roof_drip_edge_present"
_CHECK_LOAD_PATH = "structural.fortified_roof_load_path"

#: FORTIFIED §4.4 applies at 2:12 and steeper; a low-slope membrane roof is a different
#: covering with its own sealed-deck answer and is not this check's business.
_MIN_SLOPE = 2.0 / 12.0
_SLOPE_TOL = 1e-9


def _conditioned_roofs(ctx: CheckContext):
    """Resolved roofs on the conditioned envelope, in ``ctx.model.roofs`` order.

    A detached, unconditioned garage roof (``RF-GARAGE`` in catlin) is excluded the same
    way ``condensation.py`` excludes it from the Glaser walk — the interior side is not
    conditioned, so a certification scoped to "the roof over living space" does not reach
    it either.
    """
    conditioned = set(conditioned_envelope_assemblies(ctx))
    return [roof for roof in ctx.model.roofs if roof.assembly in conditioned]


def _source_roof(ctx: CheckContext, tag: str) -> Roof | None:
    for element in ctx.plan.all_elements():
        if isinstance(element, Roof) and element.tag == tag:
            return element
    return None


# --- §4.4 sealed roof deck --------------------------------------------------------------


@check(Tier.STRUCTURAL, _CHECK_SEALED_DECK)
def fortified_roof_sealed_deck(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    for roof in _conditioned_roofs(ctx):
        source = _source_roof(ctx, roof.tag)
        if source is None or source.pitch.slope < _MIN_SLOPE - _SLOPE_TOL:
            continue  # unresolvable pitch, or shallow enough that §4.4 does not apply
        assembly = ctx.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_SEALED_DECK, result=Result.UNKNOWN,
                message=(f"{_ADVISORY}{roof.tag} names assembly {roof.assembly}, which the "
                         "library does not define, so its deck cannot be graded"),
                element_tags=(roof.tag,)))
            continue
        sealed = [layer for layer in assembly.layers
                  if layer.function is LayerFunction.MEMBRANE
                  and ControlLayer.WATER in (layer.control or frozenset())]
        if not sealed:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_SEALED_DECK, result=Result.FAIL,
                message=(f"{_ADVISORY}{roof.tag}'s assembly {assembly.tag} carries no sealed "
                         "underlayment (a MEMBRANE layer with a WATER control) and its pitch "
                         f"({source.pitch.rise:g}:{source.pitch.run:g}) is at or above "
                         "FORTIFIED §4.4's 2:12 threshold for a sealed roof deck"),
                element_tags=(roof.tag,),
                fix_hint=("add a MEMBRANE layer with control={ControlLayer.WATER} citing "
                          "the underlayment's ASTM D226/ICC AC188 listing and its fastening "
                          "schedule")))
        else:
            out.append(Finding(
                severity=Severity.WARN, check_id=_CHECK_SEALED_DECK, result=Result.PASS,
                message=(f"{_ADVISORY}{roof.tag}'s assembly {assembly.tag} carries a sealed "
                         f"underlayment layer ('{sealed[0].name}') — presence only; ASTM/ICC "
                         "compliance and the tape/fastening schedule are documentation facts "
                         "this model does not carry"),
                element_tags=(roof.tag,)))
    return out


# --- §4.5 drip edge, eaves AND rakes -----------------------------------------------------


def _centroid(footprint) -> tuple[float, float]:
    n = len(footprint)
    return (sum(p[0] for p in footprint) / n, sum(p[1] for p in footprint) / n)


def _flashing_side(flashing: Flashing, centroid: tuple[float, float]) -> str:
    """Which footprint edge a drip-flashing run sits on: "N"/"S"/"E"/"W".

    A run that travels mostly north-south sits on a west or east (eave-or-rake) edge; one
    that travels mostly east-west sits on a north or south edge. Which side of the centroid
    the run's midpoint falls on names it exactly, the same reasoning ``roof_trim.py``'s own
    ``_eave_water`` uses to pick a run's ``back_side``.
    """
    p0, p1 = flashing.path[0], flashing.path[-1]
    dx = abs(p1.x.meters - p0.x.meters)
    dy = abs(p1.y.meters - p0.y.meters)
    mid_x = (p0.x.meters + p1.x.meters) / 2.0
    mid_y = (p0.y.meters + p1.y.meters) / 2.0
    if dy >= dx:
        return "W" if mid_x < centroid[0] else "E"
    return "S" if mid_y < centroid[1] else "N"


def _eave_rake_sides(ridge_direction: str) -> tuple[frozenset[str], frozenset[str]]:
    """``(eave sides, rake sides)`` — eaves run parallel to the ridge, rakes perpendicular."""
    if ridge_direction == "y":
        return frozenset({"W", "E"}), frozenset({"N", "S"})
    return frozenset({"N", "S"}), frozenset({"W", "E"})


@check(Tier.STRUCTURAL, _CHECK_DRIP_EDGE)
def fortified_roof_drip_edge(ctx: CheckContext) -> list[Finding]:
    out: list[Finding] = []
    flashings = [e for e in ctx.plan.all_elements()
                 if isinstance(e, Flashing) and e.kind is TrimKind.DRIP_FLASHING]
    for roof in _conditioned_roofs(ctx):
        hosted = [f for f in flashings if f.host_ref == roof.tag]
        if roof.form != RoofForm.GABLE.value:
            # A shed/other form has no rake-vs-eave pair to name individually; grade only
            # whether the roof carries a drip edge at all rather than inventing a 4-edge
            # scheme a shed roof does not have.
            if hosted:
                out.append(Finding(
                    severity=Severity.WARN, check_id=_CHECK_DRIP_EDGE, result=Result.PASS,
                    message=(f"{_ADVISORY}{roof.tag} carries {len(hosted)} drip flashing(s) "
                             "on record — presence only; gauge and fastener spacing are "
                             "documentation facts this model does not carry"),
                    element_tags=(roof.tag,)))
            else:
                out.append(Finding(
                    severity=Severity.WARN, check_id=_CHECK_DRIP_EDGE, result=Result.FAIL,
                    message=(f"{_ADVISORY}{roof.tag} carries no Flashing(kind=DRIP_FLASHING) "
                             "on record — FORTIFIED §4.5 wants a drip edge at every roof edge"),
                    element_tags=(roof.tag,),
                    fix_hint="author a Flashing(kind=TrimKind.DRIP_FLASHING, host_ref=...)"))
            continue
        centroid = _centroid(roof.footprint)
        covered = {_flashing_side(f, centroid) for f in hosted}
        eave_sides, rake_sides = _eave_rake_sides(roof.ridge_direction)
        for side in ("N", "S", "E", "W"):
            label = "eave" if side in eave_sides else "rake"
            if side in covered:
                out.append(Finding(
                    severity=Severity.WARN, check_id=_CHECK_DRIP_EDGE, result=Result.PASS,
                    message=(f"{_ADVISORY}{roof.tag}'s {side} {label} edge carries a drip "
                             "flashing — presence only; gauge and fastener spacing are "
                             "documentation facts this model does not carry"),
                    element_tags=(roof.tag,)))
            else:
                out.append(Finding(
                    severity=Severity.WARN, check_id=_CHECK_DRIP_EDGE, result=Result.FAIL,
                    message=(f"{_ADVISORY}{roof.tag}'s {side} {label} edge has no "
                             "Flashing(kind=DRIP_FLASHING) on record — FORTIFIED §4.5 wants "
                             "a drip edge at eaves AND rakes"),
                    element_tags=(roof.tag,),
                    fix_hint=("author a Flashing(kind=TrimKind.DRIP_FLASHING, "
                              f"host_ref=\"{roof.tag}\") along the {side} edge")))
    return out


# --- Continuous load path, re-labeled from uplift_path -----------------------------------


def _relabel(finding: Finding) -> Finding:
    body = finding.message[len(_ADVISORY):] if finding.message.startswith(_ADVISORY) \
        else finding.message
    return finding.model_copy(update={
        "check_id": _CHECK_LOAD_PATH,
        "message": (f"{_ADVISORY}FORTIFIED roof-to-wall/foundation continuous load path — "
                    f"{body}"),
    })


@check(Tier.STRUCTURAL, _CHECK_LOAD_PATH)
def fortified_roof_load_path(ctx: CheckContext) -> list[Finding]:
    """The roof-bearing subset of ``uplift_path``'s findings, reframed under this checklist.

    Not a re-derivation: ``uplift_path_coverage`` already walks every roof's seated members
    against its declared bearings, and a second opinion here would drift from it within a
    month exactly the way ``uplift_path``'s own docstring warns against for its own inputs.
    """
    roof_tags = {roof.tag for roof in ctx.model.roofs}
    return [_relabel(finding) for finding in uplift_path_coverage(ctx)
            if finding.element_tags[:1] and finding.element_tags[0] in roof_tags]
