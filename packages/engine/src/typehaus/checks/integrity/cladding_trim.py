"""Check the stock data carried by resolved cladding trim pieces."""

from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import failed, not_applicable, passed
from typehaus.library.trim.metal_sales import PROFILES

_CHECK = "integrity.cladding_trim_stock"
_INCH_M = 0.0254


@check(Tier.INTEGRITY, _CHECK)
def cladding_trim_stock(ctx: CheckContext) -> list:
    pieces = [solid for solid in ctx.model.solids if solid.category == "cladding_trim"]
    if not pieces:
        return [not_applicable(_CHECK, "no catalog cladding trim pieces resolved")]
    findings = []
    for piece in pieces:
        profile = PROFILES.get(piece.product or "")
        stock = piece.trim_stock_length_in
        length = piece.trim_length_m
        if (profile is None or stock is None or length is None or length <= 0
                or stock not in profile.stock_lengths_in or length > stock * _INCH_M + 1e-9):
            findings.append(failed(_CHECK, f"{piece.tag} has invalid profile or stock length",
                                   (piece.tag,), fix="resolve a catalog stock length for this cut"))
    return findings or [passed(_CHECK, f"all {len(pieces)} cladding trim cuts fit their stock")]
