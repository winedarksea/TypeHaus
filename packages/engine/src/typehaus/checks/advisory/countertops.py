"""Is any engineered-stone countertop cantilevered further than a fabricator will warrant?

ADVISORY, not code. No IRC section governs how far a slab may hang past its cabinet — the
limit is a MATERIAL limit the slab manufacturers publish and the fabricators warrant to, and
a house that exceeds it does not fail an inspection, it loses its warranty and eventually
its top. That is precisely the finding shape ``advisory`` exists for: WARN severity paired
with a FAIL result, so the overhang shows up as a failure in ``haus check`` without tripping
``permit.py``'s gate, which keys off ERROR severity alone. Grading it as code would claim an
authority no section gives it; grading it PASS-only would say nothing.

The rule, as Caesarstone publishes it for engineered quartz and the industry applies it
across brands: an unsupported overhang may not exceed **1/3 of the top's depth** and may not
exceed **15"** whatever the depth, and of that, **14"** is the most that may hang with no
support under it in 3 cm material (10" in 2 cm). The three are cumulative, not alternatives.

Support changes the question rather than raising the limit. A corbel, a bracket or a steel
plate is what carries the load, and a carried overhang is not a cantilever at all — so a top
that declares one passes on the strength of the support, and the finding names it, because
"there is steel in there" is exactly the fact a future reader needs and cannot see.

What makes the rule gradeable at all is ``FurnitureType.carcass_depth``: a peninsula draws
as one rectangle and is box for only part of it, and without that split a 39" top on a 24"
box reads as fully supported. See the reference house's own peninsula for the case.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result, not_applicable, passed
from typehaus.takeoff.stone_pieces import FabricatedPiece, fabricated_pieces

_M_TO_IN = 39.37007874

_CHECK_ID = "advisory.countertop_overhang"

#: The fraction of the finished top depth an unsupported overhang may occupy.
_MAX_OVERHANG_FRACTION = 1.0 / 3.0
#: The absolute cap, whatever the depth.
_MAX_OVERHANG_IN = 15.0
#: Slab thickness (inches) -> the most that may hang with nothing under it, thickest first.
#: 3 cm is 1.181"; 2 cm is 0.787". A top thinner than the thinnest row gets that row's limit,
#: which is the conservative direction.
_UNSUPPORTED_LIMIT_IN: tuple[tuple[float, float], ...] = ((1.18, 14.0), (0.0, 10.0))


@check(Tier.ADVISORY, _CHECK_ID)
def countertop_overhang(ctx: CheckContext) -> list[Finding]:
    """Every engineered-stone top's cantilever, against the published fabrication limits."""
    materials = {material.tag: material for material in ctx.plan.library.materials}
    tops = sorted(ctx.model.countertops, key=lambda top: top.tag)
    stone = [top for top in tops
             if getattr(materials.get(top.material_ref), "engineered_stone", False)]
    if not stone:
        # Earned, not assumed: either this plan models no countertop at all, or every top it
        # models is a material this rule does not reach.
        return [not_applicable(_CHECK_ID, (
            "no countertop in this plan is engineered stone"
            if tops else "this plan models no countertop"))]
    return [_grade(top) for top in stone]


def _grade(top) -> Finding:
    overhang = top.unsupported_overhang_m * _M_TO_IN
    depth = top.depth_m * _M_TO_IN
    thickness = top.thickness_m * _M_TO_IN
    where = f"{top.tag} ({top.material_ref}, {depth:.0f}\" deep over {', '.join(top.hosts)})"
    if overhang <= 0.0:
        return passed(_CHECK_ID, f"{where} stops at the carcass face and cantilevers nothing",
                      (top.tag,))
    if top.support != "none":
        return passed(_CHECK_ID, (
            f"{where} cantilevers {overhang:.2f}\", carried on {top.support} — a supported "
            "overhang is not a cantilever and the slab limits do not govern it"), (top.tag,))

    unsupported_limit = next(limit for floor, limit in _UNSUPPORTED_LIMIT_IN
                             if thickness >= floor)
    fraction = overhang / depth if depth > 0.0 else 1.0
    broken = []
    if fraction > _MAX_OVERHANG_FRACTION:
        broken.append(f"{fraction * 100:.0f}% of the {depth:.0f}\" depth against a "
                      f"{_MAX_OVERHANG_FRACTION * 100:.0f}% maximum")
    if overhang > _MAX_OVERHANG_IN:
        broken.append(f"past the {_MAX_OVERHANG_IN:.0f}\" absolute cap")
    if overhang > unsupported_limit:
        broken.append(f"past the {unsupported_limit:.0f}\" that may hang unsupported in "
                      f"{thickness:.2f}\" stone")
    if not broken:
        return passed(_CHECK_ID, (
            f"{where} cantilevers {overhang:.2f}\" unsupported — "
            f"{fraction * 100:.0f}% of its depth, inside every published limit"), (top.tag,))
    return advisory(_CHECK_ID, (
        f"{where} cantilevers {overhang:.2f}\" with nothing under it: "
        + "; ".join(broken) + ". Outside the fabricators' limits and outside the warranty"),
        (top.tag,), Result.FAIL,
        fix="carry the overhang on brackets, corbels or a steel plate (set "
            "Countertop.support), shorten it, or put a material that spans it on the "
            "cantilever and meet the stone at the carcass face")


_FAB_ID = "advisory.countertop_fabrication"


@check(Tier.ADVISORY, _FAB_ID)
def countertop_fabrication(ctx: CheckContext) -> list[Finding]:
    """Hard geometric facts a slab yard cannot cut: an oversize piece, a clamped radius.

    Graded off ``haus countertops``' own pieces (``takeoff/stone_pieces.py``). Web minimums
    are dimensioned there and not graded: no published number covers them.
    """
    pieces = fabricated_pieces(ctx.model)
    if not pieces:
        return [not_applicable(_FAB_ID, "this plan has no fabricated countertop or stool")]
    materials = {material.tag: material for material in ctx.plan.library.materials}
    return [_grade_piece(piece, getattr(materials.get(piece.material_ref),
                                        "slab_size_in", None)) for piece in pieces]


def _grade_piece(piece: FabricatedPiece, slab: tuple[float, float] | None) -> Finding:
    size = f'{piece.length_in:.3f}" x {piece.depth_in:.3f}"'
    where = f"{piece.tag} ({piece.material_ref}, {size})"
    broken = []
    if slab is not None:
        length, width = max(slab), min(slab)
        if not (max(piece.length_in, piece.depth_in) <= length
                and min(piece.length_in, piece.depth_in) <= width):
            broken.append(f'does not fit the authored {slab[0]:g}" x {slab[1]:g}" slab in '
                          "either orientation: it needs a seam or a jumbo slab")
    for index in piece.clamped_corners:
        fillet = next(f for f in piece.fillets if f.index == index)
        broken.append(f'corner {index} asks R{fillet.requested_m:.3f}" but its edges leave '
                      f'room for R{fillet.radius_m:.3f}"')
    if broken:
        return advisory(_FAB_ID, f"{where}: " + "; ".join(broken), (piece.tag,), Result.FAIL,
                        fix="seam the piece (split the Countertop's hosts), author a larger "
                            "slab_size_in on the material, or reduce corner_radius")
    if piece.mixed_edges:
        return advisory(_FAB_ID, (
            f"{where}: edge(s) {', '.join(map(str, piece.mixed_edges))} meet a wall, seam or "
            "tall neighbour for under an inch; the drawing labels the whole edge by its "
            "majority"), (piece.tag,), Result.UNKNOWN,
            fix="square the neighbour to the slab, or move the slab end clear of it")
    if slab is None:
        return advisory(_FAB_ID, f"{where}: material authors no slab_size_in, so no "
                        "fits-a-slab check", (piece.tag,), Result.UNKNOWN,
                        fix="author Material.slab_size_in from the slab maker's sheet")
    return passed(_FAB_ID, f'{where} fits the {slab[0]:g}" x {slab[1]:g}" slab; every '
                  "corner radius fits its edges", (piece.tag,))
