"""``haus handoff`` — one command that produces what a professional engineer needs.

The register, the calculations, the hand-worked notes behind them, the models and a seal
form, in one folder with a manifest. Before this, handing the work over meant running
``haus calcs``, running ``haus build``, finding out which notes were cited, obtaining forty
fingerprints one at a time with ``haus engineering --fingerprint``, and writing the
covering page by hand — which nobody did twice the same way.

**It writes a DRAFT seal file and never the real one.** ``out/handoff/engineering.toml.draft``
is a form: every field a person must supply is a visible ``<<blank>>``, and
``engineering/register.py`` refuses to load a file that still holds one. Copying it into the
house after a PE has actually stamped something is a deliberate human act, which is what
decision #65 requires and what this command is careful not to erode.

**Byte-deterministic.** Two runs over an unchanged model produce identical files, which is
the only thing that makes the manifest worth having: a changed sha256 is then a changed
model rather than a re-run. Set ``SOURCE_DATE_EPOCH`` to pin the generation date too.
"""

from __future__ import annotations

from pathlib import Path

import typer

from typehaus.cli._shared import app, console, generation_date


@app.command()
def handoff(
    house: Path | None = typer.Argument(None, help="House directory (default: cwd)"),
    out: Path | None = typer.Option(
        None, "--out", help="Where to write the bundle (default: <house>/out/handoff)."),
    profile: str | None = typer.Option(
        None, "--profile", help="Jurisdiction profile (default: preferences.toml)."),
    zip_: bool = typer.Option(
        False, "--zip", help="Also write <bundle>.zip — the file you actually send."),
    pdf: bool = typer.Option(
        True, "--pdf/--no-pdf",
        help="Flatten the calculations to calcs.pdf. This is the file a seal binds to; "
             "--no-pdf is for a fast regeneration while iterating."),
    models: bool = typer.Option(
        True, "--models/--no-models",
        help="Include model.ifc and model.glb. --no-models skips the slowest step."),
) -> None:
    """Assemble the engineering handoff bundle: calcs, notes, models and a seal form."""
    from typehaus._meta import engine_version
    from typehaus.cli.engineering_load import load_engineering
    from typehaus.engineering.scaffold import scaffold_register
    from typehaus.takeoff.calc_package import PackageInputs, calc_package
    from typehaus.takeoff.handoff import (
        cited_notes,
        pe_readme,
        write_deterministic_zip,
        write_manifest,
    )

    load = load_engineering(house, profile)
    directory = load.directory
    root = out if out is not None else directory / "out" / "handoff"
    root.mkdir(parents=True, exist_ok=True)
    generated = generation_date()
    version = engine_version()
    records = load.records()
    written: list[str] = []

    # --- the calculations, verbatim from `haus calcs` ------------------------------------
    # Reused rather than reimplemented: the bundle and the standalone package must be the
    # same document, or a reviewer marking up one is marking up something the owner cannot
    # regenerate.
    files = calc_package(PackageInputs(
        house=directory.name, model=load.ctx.model, item_ids=load.item_ids,
        results=load.results, register=load.register, generated=generated,
        engine_version=version, content_hash=load.loaded.content_hash,
        profile_name=load.ctx.profile.name, checklist=load.checklist))
    for relative, text in files.items():
        written.append(_write_text(root / "calcs" / relative, text, root))

    if pdf:
        from typehaus.takeoff.calc_pdf import PdfInputs, write_calc_pdf

        write_calc_pdf(files, root / "calcs.pdf", PdfInputs(
            house=load.ctx.model.plan.project.name or directory.name,
            generated=generated, engine_version=version,
            content_hash=load.loaded.content_hash,
            code_edition=load.ctx.profile.edition,
            scope=f"Structural calculations for {len(load.item_ids)} engineered "
                  f"requirement(s) outside the prescriptive tables."))
        written.append("calcs.pdf")

    # --- only the notes these records are actually checked against -----------------------
    # A notes folder holding the whole house's design log buries the four that verify these
    # calculations. Each sheet's section 8 names its own; this copies exactly those.
    notes = cited_notes(records)
    copied: list[str] = []
    for name in notes:
        source = directory / "notes" / name
        if not source.is_file():
            console.print(f"[yellow]cited note not on disk, skipped: {name}[/yellow]")
            continue
        written.append(_write_text(root / "notes" / name,
                                   source.read_text(encoding="utf-8"), root))
        copied.append(name)

    # --- the models ----------------------------------------------------------------------
    if models:
        from typehaus.emit.gltf.emitter import emit_glb
        from typehaus.emit.ifc.emitter import emit_ifc

        emit_ifc(load.ctx.model, root / "model.ifc", lod="framed", house_dir=directory,
                 engineering=load.results, register=load.register)
        written.append("model.ifc")
        emit_glb(load.ctx.model, root / "model.glb")
        written.append("model.glb")

    # --- the seal form, and the covering page --------------------------------------------
    written.append(_write_text(root / "engineering.toml.draft", scaffold_register(
        records, house=directory.name, generated=generated, engine_version=version,
        content_hash=load.loaded.content_hash), root))
    written.append(_write_text(root / "README.md", pe_readme(
        house=load.ctx.model.plan.project.name or directory.name, generated=generated,
        engine_version=version, content_hash=load.loaded.content_hash,
        records=records, notes=copied, checklist=load.checklist, has_pdf=pdf), root))

    digests = write_manifest(root, written)
    console.print(f"wrote {root} ({len(digests)} files, {len(load.item_ids)} item(s), "
                  f"{len(copied)} note(s))", soft_wrap=True)
    if zip_:
        archive = write_deterministic_zip(
            root.with_suffix(".zip"), root, [*digests, "MANIFEST.json"])
        console.print(f"wrote {archive}")

    unresolved = [i for i in load.item_ids if load.results[i].status.value != "ok"]
    if unresolved:
        console.print(f"[yellow]{len(unresolved)} item(s) are not finished — the bundle says "
                      f"so on its own cover and in 03-open-items.md[/yellow]", soft_wrap=True)


def _write_text(path: Path, text: str, root: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")
    return path.relative_to(root).as_posix()
