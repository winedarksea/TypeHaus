"""Check the stock data carried by resolved cladding trim pieces."""

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed
from typehaus.library.trim.catalog import PROFILES, SUPPLIES

_CHECK = "integrity.cladding_trim_stock"
_INCH_M = 0.0254


@check(Tier.INTEGRITY, _CHECK)
def cladding_trim_stock(ctx: CheckContext) -> list:
    pieces = [solid for solid in ctx.model.solids if solid.category == "cladding_trim"]
    if not pieces:
        return [not_applicable(_CHECK, "no catalog cladding trim pieces resolved")]
    findings = []
    for piece in pieces:
        if piece.product in SUPPLIES or piece.product == "EPDM_BASE_ISOLATION":
            if piece.trim_length_m is None or piece.trim_length_m <= 0:
                findings.append(failed(_CHECK, f"{piece.tag} has no installed supply length",
                                       (piece.tag,)))
            continue
        profile = PROFILES.get(piece.product or "")
        stock = piece.trim_stock_length_in
        length = piece.trim_length_m
        stock_lengths = profile.stock_lengths_in if profile else ()
        if piece.product == "RAINSCREEN_BASE_Z":
            wall = ctx.model.wall(piece.host_ref)
            assembly = ctx.model.plan.library.resolve_assembly(wall.assembly) if wall else None
            spec = assembly.rainscreen_base_flashing if assembly else None
            stock_lengths = (round(spec.stock_length.meters / _INCH_M, 6),) if spec else ()
        if (profile is None or stock is None or length is None or length <= 0
                or stock not in stock_lengths or length > stock * _INCH_M + 1e-9):
            findings.append(failed(_CHECK, f"{piece.tag} has invalid profile or stock length",
                                   (piece.tag,), fix="resolve a catalog stock length for this cut"))
    return findings or [passed(_CHECK, f"all {len(pieces)} cladding trim cuts fit their stock")]
