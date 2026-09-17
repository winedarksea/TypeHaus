"""A ``ReinforcementSpec`` the layout engine can lay out, and one it did.

Six questions of every authored schedule (decision #75):

* exactly one of ``spacing`` / ``count`` — claimed in ``BarSpec``'s docstring, enforced here
  (``dowels`` take neither: they follow the host's verticals);
* the role belongs on this kind of host;
* a ``rib`` or rib ``stirrups`` role on a slab needs ``ReinforcementSpec.ribs``;
* every role placed at least one bar (a dowel with no base, a mat narrower than its cover);
* the section is thick enough for cover on both faces plus the bars between them;
* a bar hooked into the pour below (a dowel, a continuous vertical) reaches ldh into it,
  ACI 318-19 §25.4.3.1 — the layout records both lengths on the bar.

The first three are ERRORs — the layout cannot honour them. The last three are WARN-severity
FAILs: the steel is authored, and the drawing, the BOM or the anchorage is short of it.
"""

from __future__ import annotations

from collections import Counter

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, Severity, advisory, failed, passed
from typehaus.model.rebar import BARS
from typehaus.resolve.assembly_material import is_cast_beam
from typehaus.resolve.concrete import concrete_spec_for
from typehaus.resolve.rebar.build import DEFAULT_COVER_IN

_CHECK_ID = "integrity.reinforcement_layout"
_MAT = {"top-x", "top-y", "bottom-x", "bottom-y"}
_BEAM = {"top-y", "bottom-y", "ties", "stirrups", "horizontal"}
_ALLOWED: dict[str, set[str]] = {
    "FoundationWall": {"vertical", "horizontal", "dowels"} | _BEAM,
    "Wall": {"vertical", "horizontal", "dowels"} | _BEAM,
    "Footing": _MAT,
    "Pad": _MAT,
    "Slab": _MAT | {"rib", "stirrups"},
    "Post": {"vertical", "ties", "dowels"},
    "Beam": _BEAM,
}


@check(Tier.INTEGRITY, _CHECK_ID)
def reinforcement_layout(ctx: CheckContext) -> list[Finding]:
    placed: dict[str, Counter] = {s.host_tag: Counter(b.role for b in s.bars)
                                  for s in ctx.model.rebar}
    bars = {s.host_tag: s.bars for s in ctx.model.rebar}
    out: list[Finding] = []
    for element in ctx.plan.all_elements():
        spec = getattr(element, "reinforcement", None)
        if spec is None:
            continue
        tag, kind = element.tag, element.element_kind
        errors = list(_schema_errors(ctx, element, spec))
        for message in errors:
            out.append(failed(_CHECK_ID, f"{tag}: {message}", (tag,),
                              fix="correct the ReinforcementSpec — the layout cannot honour it"))
        if errors:
            continue
        counts = placed.get(tag, Counter())
        warnings = [f"{tag}: role {e.role} #{e.bar} placed no bars"
                    + (" — no footing, pad or wall found under it to dowel into"
                       if e.role == "dowels" else "")
                    for e in spec.bars if counts[e.role] == 0]
        thin = _too_thin(ctx, element, spec)
        if thin:
            warnings.append(f"{tag}: {thin}")
        short = _short_anchorage(bars.get(tag, ()))
        if short:
            warnings.append(f"{tag}: {short}")
        for message in warnings:
            out.append(advisory(_CHECK_ID, message, (tag,), Result.FAIL,
                                severity=Severity.WARN))
        if not warnings:
            out.append(passed(_CHECK_ID, f"{tag} ({kind}): {sum(counts.values())} bars "
                              f"laid out from {len(spec.bars)} role(s)", (tag,)))
    return out


def _schema_errors(ctx: CheckContext, element, spec):
    kind = element.element_kind
    allowed = _ALLOWED.get(kind, set())
    if kind == "Beam" and not is_cast_beam(ctx.plan, element):
        yield "carries reinforcement but is not a cast beam"
    for e in spec.bars:
        if e.bar not in BARS:
            yield f"#{e.bar} is not a bar size this engine knows"
        if e.role not in allowed:
            yield f"role {e.role!r} does not belong on a {kind}"
        if e.role != "dowels" and (e.spacing is None) == (e.count is None):
            yield f"role {e.role} must state exactly one of spacing or count"
        if spec.ribs is None and (e.role == "rib" or (kind == "Slab" and e.role == "stirrups")):
            yield f"role {e.role} needs ReinforcementSpec.ribs"
        if e.zone is not None and e.role not in ("ties", "stirrups"):
            yield f"role {e.role} cannot take a zone"


def _too_thin(ctx: CheckContext, element, spec) -> str | None:
    """Cover each face plus the bars stacked between — for walls and mats only."""
    kind = element.element_kind
    mix = concrete_spec_for(ctx.plan, element)
    cover = (spec.cover.inches if spec.cover is not None
             else mix.cover.inches if mix is not None and mix.cover is not None
             else DEFAULT_COVER_IN)
    d = {e.role: BARS[e.bar].diameter_in * max(1, e.layers) for e in spec.bars
         if e.bar in BARS}
    if kind in ("FoundationWall", "Wall"):
        assembly = ctx.plan.library.resolve_assembly(getattr(element, "assembly", "") or "")
        layer = next((ly for ly in assembly.layers if ly.concrete is not None), None) \
            if assembly else None
        if layer is None or d.keys() & {"top-y", "bottom-y", "ties", "stirrups"}:
            return None
        need = 2 * cover + d.get("vertical", 0.0) + d.get("horizontal", 0.0)
        have = layer.thickness.inches
    elif kind in ("Footing", "Pad"):
        have = element.depth.inches if kind == "Footing" else element.thickness.inches
        need = 2 * cover + sum(d.get(r, 0.0) for r in _MAT)
    else:
        return None
    if have + 1e-6 >= need:
        return None
    return (f"{have:.2f}\" of concrete cannot hold {cover:.2f}\" cover each face and "
            f"{need - 2 * cover:.2f}\" of bar ({need:.2f}\" needed)")


def _short_anchorage(bars) -> str | None:
    """The worst hooked bar whose embedment into the pour below is under its ldh."""
    worst = None
    for b in bars:
        if b.embedment_m is None or b.development_m is None:
            continue
        gap = b.development_m - b.embedment_m
        if gap > 1e-4 and (worst is None or gap > worst[0]):
            worst = (gap, b)
    if worst is None:
        return None
    b = worst[1]
    count = sum(1 for x in bars if x.embedment_m is not None and x.development_m is not None
                and x.development_m - x.embedment_m > 1e-4)
    return (f"{count} {b.role} #{b.bar} hooked {b.embedment_m / 0.0254:.2f}\" into the pour "
            f"below, short of ldh {b.development_m / 0.0254:.2f}\" (ACI 318-19 §25.4.3.1)")
