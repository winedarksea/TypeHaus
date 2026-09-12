"""``haus calcs`` — the calculation package, as a folder of Markdown a PE can mark up.

Its own command rather than a flag on ``haus engineering`` for the same reason ``haus
millwork`` is not a section of ``haus takeoff --csv``: this is a *deliverable*, not a view.
``haus engineering`` answers "where does this house stand" at a glance and is meant to be
read in a terminal; a calculation package is forty-odd sheets somebody opens in an editor,
diffs against last week's, and sends to a licensed professional.

Markdown is the source of truth. ``--pdf`` flattens the same sheets through
``takeoff/calc_pdf`` for the file a seal actually binds to — a jurisdiction accepts no
Markdown — but the pagination there is derived from these files and never edited beside
them. The permit set keeps S-105 as its engineering page; this is what stands behind it.

The folder is *regenerated*, never maintained. ``MANIFEST.json`` records what this run
produced, and the next run deletes anything the previous manifest listed and this one did
not: a sheet for an item the model no longer has reads as a calculation somebody did.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import (
    _print_findings, _resolve_house, app, console, generation_date)


@app.command()
def calcs(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    out: Path | None = typer.Option(
        None, "--out", help="Where to write the package (default: <house>/out/calcs)."),
    item: str | None = typer.Option(
        None, "--item", help="Write the sheet for one item only, plus the front matter."),
    profile: str | None = typer.Option(
        None, "--profile", help="Jurisdiction profile (default: preferences.toml)."),
    pdf: bool = typer.Option(
        False, "--pdf",
        help="Also write a flattened, page-anchored PDF beside the markdown. No "
             "jurisdiction accepts Markdown, and a seal has to bind to a flattened file."),
) -> None:
    """Emit the engineering calculation package: cover, criteria, register, and one sheet
    per engineered item.

    The output is byte-deterministic — two runs over an unchanged model produce identical
    files — so the package is regenerated rather than maintained, and a diff between two
    runs is a real change in the model or in a calculation.
    """
    from typehaus._meta import engine_version
    from typehaus.checks import build_context, evaluate_permit_checklist, run_checks
    from typehaus.source import load_plan
    from typehaus.takeoff.calc_package import PackageInputs, calc_package
    from typehaus.takeoff.handoff import MANIFEST, prune_unlisted, write_manifest

    directory = _resolve_house(house)
    loaded = load_plan(directory)
    if loaded.plan is None:
        _print_findings(loaded.findings)
        raise typer.Exit(1)
    ctx, _ = build_context(loaded.plan, directory, profile)
    report = run_checks(ctx)
    # The item list is the checks' conclusion, unioned with any kind that enumerates its own
    # keys — the same derivation ``haus engineering`` uses, and deliberately not a second
    # one. See ``cli/cmd_engineering.py::_load``.
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    item_ids = tuple(sorted(named | set(ctx.engineering)))
    if item is not None and item not in item_ids:
        console.print(f"[red]{item}: no such engineering item in this house[/red]")
        console.print("[dim]run `haus engineering` for the list[/dim]")
        raise typer.Exit(1)

    checklist = evaluate_permit_checklist(report, ctx.profile)
    files = calc_package(PackageInputs(
        house=directory.name,
        model=ctx.model,
        item_ids=item_ids,
        results=ctx.engineering,
        register=ctx.engineering_register,
        generated=generation_date(),
        engine_version=engine_version(),
        content_hash=loaded.content_hash,
        profile_name=ctx.profile.name,
        checklist=checklist,
    ), only=item)

    root = out if out is not None else directory / "out" / "calcs"
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="")

    # `--item` writes one sheet plus the front matter, so "absent now" means "not asked
    # for" and nothing may be pruned against it.
    full_run = item is None
    if full_run and not (root / MANIFEST).is_file():
        # A tree written before manifests existed: the sheets folder is the one place this
        # run fully determines, so it is the only place swept without a manifest to diff.
        for orphan in prune_unlisted(root, files, subdir="calcs"):
            console.print(f"[dim]removed orphan {orphan}[/dim]", soft_wrap=True)
    write_manifest(root, files, prune=full_run)
    console.print(f"wrote {root} ({len(files)} files, {len(item_ids)} engineered item(s))",
                  soft_wrap=True)
    if pdf:
        # Markdown stays the source of truth — see ``takeoff/calc_pdf`` for why this
        # exists at all, and ``docs/calc-package-format.md`` for why the markdown does.
        from typehaus.takeoff.calc_pdf import PdfInputs, paginate, write_calc_pdf

        target = root.with_suffix(".pdf") if root.suffix else root.parent / "calcs.pdf"
        pages = write_calc_pdf(files, target, PdfInputs(
            house=ctx.model.plan.project.name or directory.name,
            generated=generation_date(),
            engine_version=engine_version(),
            content_hash=loaded.content_hash,
            code_edition=ctx.profile.edition,
            scope=f"Structural calculations for {len(item_ids)} engineered requirement(s) "
                  f"outside the prescriptive tables.",
        ))
        console.print(f"wrote {pages} ({len(paginate(files)) + 1} pages)", soft_wrap=True)
    unresolved = [i for i in item_ids if ctx.engineering[i].status.value != "ok"]
    if unresolved:
        console.print(f"[yellow]{len(unresolved)} item(s) are not finished — see "
                      f"03-open-items.md[/yellow]", soft_wrap=True)
