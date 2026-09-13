"""A suspended slab's span, graded against the row its manufacturer publishes.

**Nothing graded a suspended concrete deck before this.** There is no ``engineering/`` kind
for one, and no ``checks/structural/`` module read a slab's span — so a stay-in-place-form
deck sat outside both gates, neither a prescriptive read nor an engineered item, and the
model simply did not have an opinion about the thing holding the floor up.

It does not need an engineered one. EPS deck-form manufacturers publish allowable-live-load
tables indexed by section depth, cap thickness and beam reinforcement, and reading the row is
the same act as reading IRC Table R602.7(1): a reviewer opens the document, finds the row, and
the question is closed. So this reuses ``checks/structural/published.py`` exactly as
``structural.header_prescriptive`` does, and the refusals come with it — a retyped section, a
deeper cap or a demand past the row's own load basis takes the finding to UNKNOWN naming the
mismatch rather than printing a PASS off a quotation that stopped describing the building.

**The scope is narrow and the N/A is earned.** Only a slab that *spans* is graded: one on the
storey's structure datum with a ceiling hung under it, i.e. with a room underneath. A
slab-on-grade bears on the ground along its whole area and has no span for a table to answer;
a house built entirely of those gets NOT_APPLICABLE with that evidence, never ``[]``.

**The span is the SHORT side of the outline's minimum rotated rectangle**, because a one-way
deck form spans the short way unless somebody deliberately turns it. That assumption is stated
on every finding: a deck framed the long way has to be authored, not derived, and today
nothing in the schema can say so.
"""

from __future__ import annotations

from fractions import Fraction

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.checks.structural.published import graded_against_published
from typehaus.findings import Finding, not_applicable
from typehaus.model.enums import LayerFunction

_CHECK_ID = "structural.slab_published_span"

#: The uniform live load the row is asked to carry: IRC Table R301.5, "rooms other than
#: sleeping rooms". A published row below this is refused by the drift guard, which is what
#: makes a future occupancy change (a sleeping room at 30 psf, an assembly use at 100) show up
#: here instead of passing quietly off a row that never contemplated it.
_LIVE_LOAD_PSF = 40.0


@check(Tier.STRUCTURAL, _CHECK_ID)
def slab_published_span(ctx: CheckContext) -> list[Finding]:
    """Every suspended slab, graded against the ``published_span`` authored on it."""
    from typehaus.model.floors import Slab

    suspended = [el for el in ctx.plan.all_elements()
                 if isinstance(el, Slab) and _is_suspended(el)]
    if not suspended:
        return [not_applicable(
            _CHECK_ID,
            "no slab in this building is suspended — every pour here bears on the ground "
            "along its whole area (none sits on a structure datum with a ceiling hung "
            "under it), and a slab-on-grade has no span for a table to answer")]

    out: list[Finding] = []
    for slab in sorted(suspended, key=lambda item: item.tag):
        span_ft = _short_side_ft(slab.outline)
        if span_ft is None:
            continue  # a degenerate outline is integrity's complaint, not this check's
        out.append(graded_against_published(
            _CHECK_ID,
            f"suspended slab {slab.tag} (one-way, derived across the short side of its "
            f"outline — a deck turned to span the LONG way has to be authored, not derived)",
            (slab.tag,), span_ft,
            slab.published_span, _model_member(ctx, slab),
            demand_psf=_LIVE_LOAD_PSF,
            fix="author Slab.published_span with the deck-form manufacturer's "
                "allowable-load row that covers this section, cap and span — or, where no "
                "table publishes it, leave the deck to an engineered design"))
    return out


def _is_suspended(slab) -> bool:
    """A slab spans only where something occupied is under it.

    ``ceiling_below`` is the model's own statement of that (``Slab``'s docstring: meaningful
    only where a room sits under it), and ``datum == "structure"`` says the slab IS the floor
    structure rather than decking laid over somebody else's joists.

    ``top_elevation`` is deliberately NOT a third test. A deck pinned off its storey datum
    sets it and a deck content with the datum does not, and neither says anything about what
    is underneath — requiring it would drop a genuinely suspended slab out of scope, which is
    the one failure mode this check cannot have.
    """
    return slab.datum == "structure" and bool(slab.ceiling_below)


def _short_side_ft(outline) -> float | None:
    """The short side of the outline's minimum rotated rectangle, in feet.

    Rotating calipers, by hand rather than through ``shapely.minimum_rotated_rectangle``:
    GEOS's ``oriented_envelope`` divides by zero on an axis-aligned rectangle and prints a
    RuntimeWarning into every check run, and the whole computation is one loop. The minimum
    rotated rectangle's short side is the smallest width the outline has over any direction
    normal to one of its edges, which is what this measures directly.

    Candidate directions come from the outline's own edges rather than its convex hull, so a
    re-entrant outline can report a width LARGER than the true minimum — never smaller. That
    errs toward a longer span, which is the safe direction for a check that FAILs past a
    published maximum.
    """
    points = [point.xy_m for point in outline]
    if len(points) < 3:
        return None
    best: float | None = None
    for i, (x0, y0) in enumerate(points):
        x1, y1 = points[(i + 1) % len(points)]
        length = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if length < 1e-9:
            continue  # a duplicated vertex names no direction
        nx, ny = -(y1 - y0) / length, (x1 - x0) / length
        offsets = [px * nx + py * ny for px, py in points]
        width = max(offsets) - min(offsets)
        if best is None or width < best:
            best = width
    return None if best is None else best / 0.3048


def _model_member(ctx: CheckContext, slab) -> str | None:
    """What the model says this deck IS, spelled so a quoted row can be compared to it.

    A deck-form section is two numbers and a product: the form depth, the cast cap over it,
    and whose form it is. All three come out of the named assembly — the INSULATION layer's
    thickness and material name, and the STRUCTURE layer's thickness — so retyping the form,
    deepening the cap or swapping the product all move this string, and a row read at the old
    one stops matching. That IS the drift guard; there is no separate field to keep in step.

    ``None`` where the assembly says nothing (an unresolved or single-layer stack), which
    makes ``published.py`` skip the member comparison rather than invent a mismatch.
    """
    if not slab.assembly:
        return None
    resolved = ctx.plan.library.resolve_assembly(slab.assembly)
    if resolved is None:
        return None
    form = next((layer for layer in resolved.layers
                 if layer.function == LayerFunction.INSULATION), None)
    cap = next((layer for layer in resolved.layers
                if layer.function == LayerFunction.STRUCTURE), None)
    if form is None or cap is None:
        return None
    material = ctx.plan.library.material(form.material_ref)
    name = material.name if material is not None else form.material_ref
    return (f"{_inches(form.thickness.inches)} {name} under a "
            f"{_inches(cap.thickness.inches)} cast cap")


def _inches(value: float) -> str:
    """``10.0`` -> ``10"``, ``4.375`` -> ``4 3/8"``."""
    whole = int(value)
    part = Fraction(value - whole).limit_denominator(16)
    text = f"{whole}" if whole or not part else ""
    if part:
        text = f"{text} {part}".strip()
    return f'{text}"'
