"""The load cases, taken from what the records actually consumed.

**Never a second derivation where a record already has the number.** A ``roof_beam``
record computed a ``uniform_load`` in plf and graded a bending ratio against it; the line
load here is that number, split into its DEAD and SNOW halves by the record's own
``design_dead`` and ``design_snow``. A ``deck_post`` record computed a base moment from a
storey shear; the node load here is the shear that reproduces that moment over that
column's own height. A load case that disagreed with the sheet beside it in the same
handover would be worse than no load case at all.

The one load derived rather than read back is the deck's own gravity, and it is derived the
way ``engineering/pier_basis`` derives it — the same joist-span strip, the same IRC Table
R301.5 numbers — because the pier record holds a total in pounds and a graph needs it as a
line load on the beams. A solve's column reaction then reproduces the record's
``dead_load + live_load``, which is what makes the two checkable against each other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from typehaus.analytical.graph import Combination, LoadCase, LoadCaseKind, MemberLoad, NodeLoad

#: lbf -> N, and lbf/ft -> N/m. SI in the graph, US practice in the records.
LB_TO_N = 4.4482216152605
PLF_TO_N_M = LB_TO_N / 0.3048


@dataclass
class LoadSet:
    cases: list[LoadCase] = field(default_factory=list)
    member_loads: list[MemberLoad] = field(default_factory=list)
    node_loads: list[NodeLoad] = field(default_factory=list)
    combinations: list[Combination] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)

    def case(self, kind: LoadCaseKind, description: str) -> None:
        if not any(existing.kind is kind for existing in self.cases):
            self.cases.append(LoadCase(kind, description))


def derive_loads(ctx: Any, scope: Any, graph: Any) -> LoadSet:
    """Every load this graph carries, each naming the item and quantity it came from."""
    loads = LoadSet()
    _roof_beam_loads(ctx, scope, graph, loads)
    _deck_gravity(ctx, scope, graph, loads)
    _lateral_column_loads(ctx, scope, graph, loads)
    _combinations(ctx, scope, loads)
    loads.assumptions.append(
        "self weight is NOT a load in this graph. The graph carries a section and a "
        "modulus, not a density, so a member's own weight is the solver's to add — and "
        "engineering/pier_basis's dead_load already includes each cast column's 150 pcf, "
        "so a reaction compared against it must have self weight put back")
    loads.cases.sort(key=lambda case: case.kind.value)
    loads.member_loads.sort(key=lambda load: (load.case.value, load.member, load.direction))
    loads.node_loads.sort(key=lambda load: (load.case.value, load.node, load.source))
    return loads


def _quantity(record: Any, name: str) -> float | None:
    return next((q.value for q in record.inputs if q.name == name), None)


def _roof_beam_loads(ctx: Any, scope: Any, graph: Any, loads: LoadSet) -> None:
    """A ``roof_beam``'s own ``uniform_load``, split DEAD/SNOW by its own two pressures."""
    for item in scope.item_ids:
        record = ctx.engineering[item]
        if record.kind != "roof_beam":
            continue
        w_plf = _quantity(record, "uniform_load")
        if not w_plf:
            continue
        dead_psf = _quantity(record, "design_dead") or 0.0
        snow_psf = _quantity(record, "design_snow") or 0.0
        total = dead_psf + snow_psf
        shares = ((LoadCaseKind.DEAD, dead_psf / total), (LoadCaseKind.SNOW, snow_psf / total)) \
            if total > 0 else ((LoadCaseKind.DEAD, 1.0),)
        for tag in sorted(set(record.element_tags) & set(graph.beam_spans)):
            for kind, share in shares:
                if share <= 0.0:
                    continue
                w_n_m = -w_plf * share * PLF_TO_N_M
                loads.case(kind, _CASE_TEXT[kind])
                for member in graph.beam_spans[tag]:
                    loads.member_loads.append(MemberLoad(
                        case=kind, member=member, direction="GZ", w0_n_m=w_n_m,
                        w1_n_m=w_n_m,
                        source=(f"{item} uniform_load {w_plf:,.1f} plf x "
                                f"{kind.value} {share:.3f} share of "
                                f"{total:,.1f} psf")))


def _deck_gravity(ctx: Any, scope: Any, graph: Any, loads: LoadSet) -> None:
    """A deck as a line load on each beam under it, on ``pier_basis``'s own strip rule."""
    from typehaus.engineering.glulam_beam import _joist_span_ft
    from typehaus.engineering.pier_basis import DECK_DEAD_LOAD_PSF, DECK_LIVE_LOAD_PSF
    from typehaus.model.floors import FloorSystem

    for tag in scope.decks:
        deck = ctx.plan.by_tag(tag)
        if not isinstance(deck, FloorSystem) or deck.service != "deck":
            continue
        strip_ft = _joist_span_ft(ctx, deck)
        beams = sorted(set(deck.joists.bearing_refs or ()) & set(graph.beam_spans))
        if not beams:
            continue
        if strip_ft is None:
            loads.assumptions.append(
                f"{tag}: no joist span resolves, so this deck contributes no line load — "
                f"the members under it are unloaded in this graph")
            continue
        loads.assumptions.append(
            f"{tag}: carried as a line load on {', '.join(beams)} rather than as its "
            f"joists, on engineering/pier_basis's own rule — each beam takes the deck's "
            f"full {strip_ft:.2f} ft joist span, so overlapping strips are counted twice "
            f"and the columns' reactions are the conservative side of the split")
        for kind, psf, citation in (
                (LoadCaseKind.DEAD, DECK_DEAD_LOAD_PSF, "pier_basis.DECK_DEAD_LOAD_PSF"),
                (LoadCaseKind.LIVE, DECK_LIVE_LOAD_PSF, "IRC Table R301.5 deck live")):
            w_n_m = -strip_ft * psf * PLF_TO_N_M
            loads.case(kind, _CASE_TEXT[kind])
            for beam in beams:
                for member in graph.beam_spans[beam]:
                    loads.member_loads.append(MemberLoad(
                        case=kind, member=member, direction="GZ", w0_n_m=w_n_m,
                        w1_n_m=w_n_m,
                        source=(f"{tag} {psf:.0f} psf x {strip_ft:.2f} ft joist span "
                                f"({citation})")))


def _lateral_column_loads(ctx: Any, scope: Any, graph: Any, loads: LoadSet) -> None:
    """The storey shear and the guard load on a fixed-base column, at its top node.

    Both are applied so that the base moment this graph produces is the base moment the
    ``deck_post`` record graded: ``V x h`` for the wind, and for the guard a 200 lb push
    plus the moment its lever above the column top contributes. Reproducing the record's
    own arithmetic is the point — a shear derived a second way would be a second answer.
    """
    from typehaus.engineering.pier_basis import cast_piers

    for pier in cast_piers(ctx):
        node = graph.post_top.get(pier.tag)
        if node is None or not pier.lateral_system or pier.height_in <= 0:
            continue
        item = next((i for i in scope.items_for(pier.tag) if i.startswith("deck_post/")),
                    f"deck_post/{pier.tag}")
        height_ft = pier.height_in / 12.0
        axis = "GX" if pier.moment_basis.startswith("E-W") else "GY"
        if pier.wind_base_moment_lb_ft:
            shear_n = pier.wind_base_moment_lb_ft / height_ft * LB_TO_N
            loads.case(LoadCaseKind.WIND, _CASE_TEXT[LoadCaseKind.WIND])
            loads.node_loads.append(_horizontal(
                LoadCaseKind.WIND, node, axis, shear_n, 0.0,
                source=(f"{item} wind_base_moment {pier.wind_base_moment_lb_ft:,.0f} lb-ft "
                        f"/ {height_ft:.2f} ft column = {shear_n / LB_TO_N:,.0f} lb at the "
                        f"column top, {axis}")))
        if pier.guard_base_moment_lb_ft:
            # IRC R301.5's 200 lb acts at the top of the GUARD, above the column top; the
            # extra lever rides as a node moment so the base moment matches the record.
            guard_arm_ft = pier.guard_base_moment_lb_ft / 200.0
            extra_ft = max(guard_arm_ft - height_ft, 0.0)
            force_n = 200.0 * LB_TO_N
            loads.case(LoadCaseKind.GUARD, _CASE_TEXT[LoadCaseKind.GUARD])
            loads.node_loads.append(_horizontal(
                LoadCaseKind.GUARD, node, axis, force_n, force_n * extra_ft * 0.3048,
                source=(f"{item} guard_base_moment {pier.guard_base_moment_lb_ft:,.0f} "
                        f"lb-ft: 200 lb at the column top plus its {extra_ft:.2f} ft of "
                        f"guard above, as a node moment")))


def _horizontal(kind: LoadCaseKind, node: str, axis: str, force_n: float,
                extra_moment_nm: float, source: str) -> NodeLoad:
    """A push at a column top, with the lever above the node carried as a moment.

    Signs: a +X force at height h gives a base moment ``+F*h`` about Y, and a +Y force
    gives ``-F*h`` about X. The added moment follows the same sense so it adds to the base
    moment rather than cancelling part of it.
    """
    if axis == "GX":
        return NodeLoad(kind, node, fx_n=force_n, my_nm=extra_moment_nm, source=source)
    return NodeLoad(kind, node, fy_n=force_n, mx_nm=-extra_moment_nm, source=source)


def _combinations(ctx: Any, scope: Any, loads: LoadSet) -> None:
    """Only combinations a record actually named, and only where the factors parse."""
    seen: set[str] = set()
    for item in scope.item_ids:
        record = ctx.engineering[item]
        for state in record.limit_states:
            text = (state.combination or "").strip()
            if not text or text in seen:
                continue
            seen.add(text)
            factors = _parse_factors(text)
            if factors:
                loads.combinations.append(Combination(
                    name=text, factors=factors, source=f"{item} {state.name}"))
    loads.combinations.sort(key=lambda combination: combination.name)


#: The letter every standard uses for a case, so a combination string can be read back.
_LETTERS = {"D": LoadCaseKind.DEAD, "L": LoadCaseKind.LIVE, "S": LoadCaseKind.SNOW,
            "W": LoadCaseKind.WIND, "H": LoadCaseKind.EARTH}


def _parse_factors(text: str) -> dict[LoadCaseKind, float]:
    """``"D + 0.75L + 0.75(0.6W)"`` -> factors. Empty where the string will not parse —
    a combination guessed at is a claim about arithmetic nobody ran."""
    body = text.split("—")[-1].strip()
    factors: dict[LoadCaseKind, float] = {}
    for term in body.split("+"):
        token = term.strip().replace("(", "").replace(")", "")
        if not token:
            return {}
        letter = token[-1].upper()
        kind = _LETTERS.get(letter)
        if kind is None:
            return {}
        head = token[:-1].strip() or "1.0"
        try:
            value = 1.0
            for part in head.split("*"):
                value *= float(part)
        except ValueError:
            return {}
        factors[kind] = factors.get(kind, 0.0) + value
    return factors


_CASE_TEXT = {
    LoadCaseKind.DEAD: "dead: the self weight and finishes the records consumed",
    LoadCaseKind.LIVE: "live: IRC Table R301.5 occupancy load",
    LoadCaseKind.SNOW: "snow: the design snow each roof record was graded at",
    LoadCaseKind.WIND: "wind: the ASD storey shear the deck_post records were graded at",
    LoadCaseKind.GUARD: "guard: IRC R301.5's 200 lb, its own case — never combined with wind",
    LoadCaseKind.EARTH: "earth: lateral soil pressure",
}
