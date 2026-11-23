"""``haus handoff`` — one command that produces what a professional engineer needs.

The register, the calculations, the hand-worked notes behind them, the models and a seal
form, in one folder with a manifest. Before this, handing the work over meant running
``haus calcs``, running ``haus build``, finding out which notes were cited, obtaining every
fingerprint one at a time with ``haus engineering --fingerprint``, and writing the
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

import os
import sys
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
    full: bool = typer.Option(
        True, "--full/--no-appendix",
        help="Print every member's appendix tables in calcs.pdf (the default: a seal "
             "binds to the PDF, so the members' data must be in it). --no-appendix "
             "drops them; the markdown always has them."),
    drawings: bool = typer.Option(
        True, "--drawings/--no-drawings",
        help="Include drawings/: the structural sheets and a key plan, so a tag can be "
             "found on paper. --no-drawings skips the slowest drawing step."),
    engineer: str | None = typer.Option(
        None, "--engineer", help="Pre-fill the seal form's engineer (e.g. 'Jane Doe, PE')."),
    license_: str | None = typer.Option(
        None, "--license", help="Pre-fill the seal form's license (e.g. 'MN 12345')."),
    sealed_on: str | None = typer.Option(
        None, "--sealed-on", help="Pre-fill the seal form's date, YYYY-MM-DD."),
    since: Path | None = typer.Option(
        None, "--since",
        help="An earlier package folder or bundle to list what changed against "
             "(default: <house>/out/issued, if present; else 'first issue')."),
) -> None:
    """Assemble the engineering handoff bundle: calcs, notes, models and a seal form."""
    _pin_hash_seed()
    from typehaus._meta import engine_version
    from typehaus.cli.engineering_load import load_engineering
    from typehaus.engineering.scaffold import SealDefaults, scaffold_external, scaffold_register
    from typehaus.takeoff.calc_package import PackageInputs, calc_package
    from typehaus.takeoff.calc_summary import read_previous
    from typehaus.takeoff.handoff import (
        cited_notes,
        pe_readme,
        sha256_file,
        write_deterministic_zip,
        write_manifest,
    )

    if sealed_on is not None:
        from datetime import date

        try:
            date.fromisoformat(sealed_on)
        except ValueError:
            console.print(f"[red]--sealed-on must be YYYY-MM-DD, got {sealed_on!r}[/red]")
            raise typer.Exit(1) from None

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
        profile_name=load.ctx.profile.name, checklist=load.checklist,
        profile=load.ctx.profile, preferences=load.ctx.preferences,
        previous=read_previous(since if since is not None
                               else directory / "out" / "issued")))
    for relative, text in files.items():
        written.append(_write_text(root / "calcs" / relative, text, root))

    if pdf:
        from typehaus.takeoff.calc_pdf import PdfInputs, write_calc_pdf

        write_calc_pdf(files, root / "calcs.pdf", PdfInputs(
            house=load.ctx.model.plan.project.name or directory.name,
            generated=generated, engine_version=version,
            content_hash=load.loaded.content_hash,
            code_edition=load.ctx.profile.edition,
            asce_edition=getattr(load.ctx.profile, "asce_edition", ""),
            scope=f"Structural calculations for {len(load.item_ids)} engineered "
                  f"requirement(s) outside the prescriptive tables.",
            include_appendix=full))
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

    # --- drawings: the structural sheets and a key plan, to find a tag on paper ----------
    sheet_ids: list[str] = []
    key_ids: list[str] = []
    if drawings:
        from typehaus.takeoff.handoff_drawings import write_key_plan, write_structural_sheets

        sheet_ids = write_structural_sheets(
            load.ctx.model, load.ctx.preferences, load.ctx.profile, directory, load.report,
            root / "drawings" / "structural_sheets.pdf")
        written.append("drawings/structural_sheets.pdf")
        key_ids = write_key_plan(load.ctx.model, records, root / "drawings" / "key_plan.pdf")
        written.append("drawings/key_plan.pdf")

    # --- the owner's review evidence, byte for byte --------------------------------------
    from typehaus.takeoff.handoff_drawings import evidence_files

    evidence = evidence_files(directory)
    for relative, source in evidence:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        written.append(relative)

    # --- the models ----------------------------------------------------------------------
    # --- the analytical model: one graph, four files (decision #73) ----------------------
    # Built before the IFC so the structural analysis view rides INSIDE model.ifc, where its
    # IfcRelAssignsToProduct links can reach the physical members.
    from typehaus.analytical.build import build_analytical_model
    from typehaus.emit.analytical import (
        write_analysis_readme,
        write_members_csv,
        write_pynite_script,
    )
    from typehaus.emit.draw.dxf_structure import write_structure_dxf

    analytical = build_analytical_model(load.ctx)
    house_name = load.ctx.model.plan.project.name or directory.name
    for relative, writer in (("analysis/model.pynite.py", write_pynite_script),
                             ("analysis/members.csv", write_members_csv),
                             ("analysis/centreline.dxf", write_structure_dxf)):
        writer(analytical, root / relative)
        written.append(relative)
    write_analysis_readme(analytical, root / "analysis" / "README.md", house=house_name,
                          has_ifc=models)
    written.append("analysis/README.md")

    if models:
        from typehaus.emit.gltf.emitter import emit_glb
        from typehaus.emit.ifc.emitter import emit_ifc

        emit_ifc(load.ctx.model, root / "model.ifc", lod="framed", house_dir=directory,
                 engineering=load.results, register=load.register, analytical=analytical)
        written.append("model.ifc")
        emit_glb(load.ctx.model, root / "model.glb")
        written.append("model.glb")

    # --- the seal form, and the covering page --------------------------------------------
    seal = SealDefaults(
        **{key: value for key, value in (
            ("engineer", engineer), ("license", license_), ("sealed_on", sealed_on),
            ("document", "calcs.pdf" if pdf else None)) if value is not None})
    form = dict(house=directory.name, generated=generated, engine_version=version,
                content_hash=load.loaded.content_hash, defaults=seal)
    written.append(_write_text(root / "engineering.toml.draft", scaffold_register(
        records, document_sha256=sha256_file(root / "calcs.pdf") if pdf else None,
        **form), root))
    external = scaffold_external(records, **form)
    if external:
        written.append(_write_text(root / "engineering-external.toml.draft", external, root))
    written.append(_write_text(root / "README.md", pe_readme(
        house=load.ctx.model.plan.project.name or directory.name, generated=generated,
        engine_version=version, content_hash=load.loaded.content_hash,
        records=records, notes=copied, checklist=load.checklist, has_pdf=pdf,
        full_pdf=full, sheets=sheet_ids, key_plan=key_ids, evidence=len(evidence),
        has_external=bool(external)), root))

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


def _pin_hash_seed() -> None:
    """Re-exec once with ``PYTHONHASHSEED=0`` so the bundle is byte-identical run to run.

    Two emitters still depend on set order — the S-100 locating dimension chain
    (``emit/draw/structural_dimensions``) and the IFC's ``IfcRelCoversBldgElements`` GUIDs —
    and a manifest is worthless if a re-run changes a hash. Fix those and this goes away.
    """
    if os.environ.get("PYTHONHASHSEED") == "0" or "pytest" in sys.modules:
        return
    os.environ["PYTHONHASHSEED"] = "0"
    sys.stdout.flush()
    sys.stderr.flush()
    os.execv(sys.executable, [sys.executable, *sys.argv])
