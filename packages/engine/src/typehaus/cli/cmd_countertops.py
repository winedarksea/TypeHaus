"""`haus countertops` — a fabricator's package per countertop material.

Per material: one DXF per piece (inches, true arcs), a PDF shop drawing set, and the piece
list as CSV and Markdown (``docs/countertop-fabrication-format.md``). A view, like
``haus millwork``: every square foot is billed in the takeoff's countertop rows.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import _print_findings, _resolve_house, app, console
from typehaus.findings import Severity

PIECE_COLUMNS = ("tag", "kind", "material", "product", "thickness_in", "length_in",
                 "depth_in", "gross_area_sqft", "profile", "finished_edge_in",
                 "corner_radii", "cutouts", "holes", "narrowest_web_in", "location",
                 "support", "holds", "uid")


def piece_row(piece) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """One flat row per piece, shared by the CSV, the Markdown and ``--json``."""
    from typehaus.takeoff.stone_pieces import inches_text

    return {
        "tag": piece.tag, "kind": piece.kind, "material": piece.material_ref,
        "product": piece.product, "thickness_in": round(piece.thickness_in, 3),
        "length_in": round(piece.length_in, 3), "depth_in": round(piece.depth_in, 3),
        "gross_area_sqft": piece.area_sqft, "profile": piece.profile_words,
        "finished_edge_in": round(piece.edge_length_in("finished"), 2),
        "corner_radii": ", ".join(sorted({inches_text(r) for r in piece.radii_in if r > 0})),
        "cutouts": "; ".join(cut.label for cut in piece.cutouts),
        "holes": "; ".join(f"{inches_text(h.diameter_in)} {h.purpose} at "
                           f"({h.center[0]:.3f}, {h.center[1]:.3f})" for h in piece.holes),
        "narrowest_web_in": (round(min(web.distance_in for web in piece.webs), 3)
                             if piece.webs else ""),
        "location": piece.location, "support": piece.support,
        "holds": " | ".join(piece.holds), "uid": piece.uid,
    }


def material_block(model, ref: str, pieces) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """What the cover page says about the stock."""
    from typehaus.takeoff.stone_pieces import inches_text

    material = next((item for item in model.plan.library.materials if item.tag == ref), None)
    product = model.plan.library.product(getattr(material, "product_ref", None) or "")
    slab = getattr(material, "slab_size_in", None)
    return {
        "Material": getattr(material, "name", ref),
        "Tag": ref,
        "Product": (f"{product.brand} {product.model}".strip() if product else "not named"),
        "Description": product.name if product is not None else "",
        "Thickness": ", ".join(sorted({inches_text(p.thickness_in) for p in pieces})),
        "Finish": str(getattr(material, "finish", None) or "not stated"),
        "Edge profile": "; ".join(sorted({p.profile_words for p in pieces})),
        "Slab size": (f'{slab[0]:g}" × {slab[1]:g}" (house-authored; confirm at order)'
                      if slab else "not authored — no fits-a-slab check"),
    }


@app.command()
def countertops(
    house: Path | None = typer.Argument(None),
    material: str | None = typer.Option(None, "--material",
                                        help="Only this material tag."),
    out: Path = typer.Option(Path("out/countertops"), "--out",
                             help="Package root; one folder per material."),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """Write fabricator packages: per-piece DXF, a PDF shop drawing set and a piece list."""
    import json

    from typehaus.emit.csv_writer import write_csv
    from typehaus.emit.fabrication.stone_dxf import write_piece_dxf
    from typehaus.emit.fabrication.stone_pdf import write_stone_pdf
    from typehaus.emit.md_writer import bullets, document, heading, kv_block, table
    from typehaus.resolve import resolve
    from typehaus.source import load_plan
    from typehaus.takeoff.stone_pieces import FabricatedPiece, fabricated_pieces

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    model, findings = resolve(loaded.plan)
    if any(finding.severity is Severity.ERROR for finding in findings):
        _print_findings(findings)
        raise typer.Exit(1)

    pieces = fabricated_pieces(model, material)
    if not pieces:
        console.print("[yellow]no fabricated countertop pieces"
                      + (f" in {material!r}" if material else "") + "[/yellow]")
        raise typer.Exit(0 if material is None else 1)
    by_material: dict[str, list[FabricatedPiece]] = {}
    for piece in pieces:
        by_material.setdefault(piece.material_ref, []).append(piece)

    summary: dict[str, object] = {}
    for ref, group in sorted(by_material.items()):
        folder = out / ref
        block = material_block(model, ref, group)
        rows = [piece_row(piece) for piece in group]
        for piece in group:
            write_piece_dxf(piece, folder / f"{piece.tag}.dxf")
        write_stone_pdf(folder / "shop-drawings.pdf", directory.name, block, group)
        write_csv(folder / "pieces.csv", PIECE_COLUMNS, rows)
        (folder / "pieces.md").write_text(document(
            heading(f"Countertop pieces — {block['Material']}"), kv_block(block.items()),
            table(list(PIECE_COLUMNS[:-2]), [[row[c] for c in PIECE_COLUMNS[:-2]]
                                             for row in rows]),
            heading("Holds", 2),
            bullets(sorted({hold for piece in group for hold in piece.holds}))),
            encoding="utf-8")
        summary[ref] = {"folder": str(folder), "material": block, "pieces": rows}
        if not as_json:
            gross = sum(piece.area_sqft for piece in group)
            console.print(f"[bold]{block['Material']}[/bold]  {len(group)} pieces, "
                          f"{gross:.2f} SF gross -> {folder}", soft_wrap=True)
            for row in rows:
                console.print(f"  {row['tag']:<22} {row['kind']:<5} "
                              f"{row['length_in']:>8.3f} x {row['depth_in']:<7.3f} "
                              f"R {row['corner_radii'] or '-':<10} {row['holes'] or ''}",
                              soft_wrap=True)
            for hold in sorted({hold for piece in group for hold in piece.holds}):
                console.print(f"    [dim]hold: {hold}[/dim]", soft_wrap=True)
    if as_json:
        console.print_json(json.dumps(summary))
