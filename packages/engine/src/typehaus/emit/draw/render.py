"""``haus render`` backend — headless plan/section snapshots for the agent eyes loop (#52).

The loop is edit → build → check → *look* → fix. This module turns a ``ResolvedModel`` into
PNG/SVG snapshots Claude reads natively (→ 20 §Agent eyes). Plan and section come straight
from the drawing IR; 3D is the offscreen glTF path (M-later) and degrades gracefully here.

Two paths, and the difference is what decides the scale
------------------------------------------------------
Without ``paper`` a scene goes to ``pdf_writer.write_raster``, which fits the figure to its
content: fast, frameless, and the drawn scale is a consequence of how much there happened to
be to draw. That is the right trade for a snapshot nobody prints.

With ``paper`` the scene is placed on a real sheet through ``sheet_writer.compose_sheet`` —
border, title block, graphic scale bar, north arrow, and a scale *chosen* from the standard
ladder by ``frame_for_scene`` rather than fallen out of a fit. The image is then a true
scaled drawing: measured against its own bar, it is the same drawing the permit set prints.

Resolution, once: the permit PDF is **vector** and is the real large-format deliverable — it
has no dpi and plots at the plotter's. A raster only approximates it, and matching an ARCH D
sheet at plate quality takes ``--dpi 300`` (36 x 24 in → 10800 x 7200 px). ``DEFAULT_DPI``
stays 110 because the agent-eyes loop reads snapshots on a screen, where 300 buys nothing
and costs seconds; details are the exception (→ ``DETAIL_DPI``).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typehaus.emit.draw.floorplan import build_floorplan
from typehaus.emit.draw.paper import suffix_for_size
from typehaus.emit.draw.pdf_writer import Underlay, write_raster
from typehaus.resolve.model import ResolvedModel

#: Screen resolution for the look-at-it loop; ``--dpi`` overrides it per invocation.
DEFAULT_DPI = 110
#: Details carry the finest hatch and lettering in the whole set, and 110 dpi smears both
#: into grey. Every path that renders a detail card uses this — ``haus render --view
#: details`` and ``haus explain --detail`` alike, or the same drawing looks like two.
DETAIL_DPI = 300

#: Longest edge, in pixels, when neither ``--dpi`` nor ``--long-edge`` is given. A raster
#: sized by dpi is sized by accident: a frameless figure's inch dimensions fall out of how
#: much there happened to be to draw, so "110 dpi" names no pixel count a reader can rely
#: on. 4096 is chosen to be legible under a pencil on a tablet and to sit inside Procreate's
#: canvas budget on the hardware that budget is tightest on.
DEFAULT_LONG_EDGE = 4096

#: Every view ``--view all`` runs, in the order a reader would open them.
VIEWS = ("plan", "site", "section", "elevation", "details", "3d")

#: What ``--fmt`` accepts. ``psd`` is the layered review artifact (→ psd_writer); ``svg`` is
#: vector and ignores every raster sizing option.
FORMATS = ("png", "svg", "psd")


@dataclass(frozen=True)
class _SheetId:
    """What a snapshot calls itself: caption for the frameless path, title block for the sheet.

    ``number`` is deliberately not a permit-set sheet number. A render is not a page of a
    set — it has no index, no revision and no order — and stamping "A-101" on one would
    invite a reader to file it as though it were. The series word says what the drawing is
    and claims nothing about where it sits.
    """

    number: str
    title: str
    caption: str
    north_arrow: bool = False


def resolve_underlays(house_dir: Path, reference_underlays) -> list[Underlay]:
    """Turn preferences ``ReferenceUnderlay`` records into drawable ``Underlay`` rectangles.

    ``path`` is house-relative (the same convention the server's sandboxed ``/underlay``
    route uses), so this is where it becomes an absolute image on disk.
    """
    return [Underlay(image_path=(house_dir / item.path).resolve(),
                     origin_x_m=item.origin_x_m, origin_y_m=item.origin_y_m,
                     width_m=item.width_m, height_m=item.height_m,
                     opacity=item.opacity, storey=item.storey)
            for item in reference_underlays]


def resolve_size(dpi: int | None, long_edge: int | None) -> tuple[int, int | None]:
    """``(dpi, long_edge)`` for a raster, from the two options a caller may pass.

    One rule, so every entry point agrees: they are mutually exclusive, and given neither
    the output is sized by ``DEFAULT_LONG_EDGE``. ``render_plan`` and ``render_views``
    quietly disagreeing about that default is how two renders of the same storey came out at
    two different sizes.
    """
    if dpi is not None and long_edge is not None:
        raise ValueError("--dpi and --long-edge both size the raster; pass one")
    if dpi is None and long_edge is None:
        return DEFAULT_DPI, DEFAULT_LONG_EDGE
    return (DEFAULT_DPI if dpi is None else dpi), long_edge


def render_plan(model: ResolvedModel, storey: str, path: Path, dpi: int | None = None,
                underlays=(), paper=None, scale: str | None = None,
                long_edge: int | None = None) -> Path:
    dpi, long_edge = resolve_size(dpi, long_edge)
    scene = build_floorplan(model, storey)
    return _write_view(model, scene, path,
                       _SheetId("PLAN", f"{storey.title()} floor plan",
                                f"plan · {storey}", north_arrow=True),
                       dpi=dpi, underlays=underlays, paper=paper, scale=scale,
                       long_edge=long_edge)


def _write_view(model: ResolvedModel, scene, path: Path, sheet: _SheetId, *,
                dpi: int, underlays=(), paper=None, scale: str | None = None,
                long_edge: int | None = None) -> Path:
    """One snapshot, on paper or not — the single place the two writers are chosen between.

    On paper the scene is given a real :class:`Frame` first (``frame_for_scene``) so the
    scale is *decided* rather than fitted, and ``compose_sheet`` places it inside the same
    border, title block and graphic scale bar the permit set prints. Off paper nothing
    changes from before: the frameless fit, which is what a quick look wants.
    """
    if paper is None:
        return write_scene(scene, path, sheet.caption, dpi, long_edge, underlays)

    from typehaus.emit.draw.artist_tags import ArtistTagger
    from typehaus.emit.draw.pdf_writer import _close, dpi_for_long_edge
    from typehaus.emit.draw.sheet_writer import compose_sheet, frame_for_scene
    from typehaus.emit.draw.sheets import SheetSpec

    frame = frame_for_scene(scene, paper, scale_label=scale)
    if frame is not None:
        scene = scene.model_copy(update={"frame": frame})
    spec = SheetSpec(sheet.number, sheet.title, paper=paper,
                     north_arrow=sheet.north_arrow)
    tagger = ArtistTagger.detached()
    fig = compose_sheet(scene, spec, model, size=spec.size, underlays=underlays,
                        tagger=tagger)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix.lower() == ".psd":
        # A composed sheet has chosen its paper, so the whole sheet is the crop and its
        # longest edge is a real inch dimension rather than a fitted one.
        return _finish_psd(fig, tagger, path, None, max(spec.size), long_edge)
    if path.suffix.lower() == ".svg":
        import io

        from typehaus.emit.draw.svg_layers import regroup_svg

        buffer = io.StringIO()
        fig.savefig(buffer, format="svg")
        _close(fig)
        path.write_text(regroup_svg(buffer.getvalue()), encoding="utf-8")
        return path
    out_dpi = dpi_for_long_edge(long_edge, max(spec.size)) if long_edge else dpi
    fig.savefig(path, dpi=out_dpi)
    _close(fig)
    return path


def write_scene(scene, path: Path, title: str, dpi: int,
                long_edge: int | None = None, underlays=()) -> Path:
    """A frameless scene to PNG, SVG or PSD, chosen by ``path``'s suffix.

    The one door for every snapshot that has not chosen a sheet — the plan/section/elevation
    views and the detail cards alike — so a format added here is a format all of them get.
    """
    from typehaus.emit.draw.pdf_writer import figure_for, save_box

    if path.suffix.lower() != ".psd":
        return write_raster(scene, path, title=title, dpi=dpi, underlays=underlays,
                            long_edge=long_edge)
    fig, tagger = figure_for(scene, title, underlays)
    box, long_in = save_box(fig, scene)
    return _finish_psd(fig, tagger, path, box, long_in, long_edge)


def _finish_psd(fig, tagger, path: Path, box, long_in: float,
                long_edge: int | None) -> Path:
    from typehaus.emit.draw.pdf_writer import _close
    from typehaus.emit.draw.psd_writer import write_psd

    try:
        return write_psd(fig, tagger, path, box=box, long_in=long_in,
                         long_edge=long_edge or DEFAULT_LONG_EDGE)
    finally:
        _close(fig)


def render_views(
    model: ResolvedModel, out_dir: Path, view: str = "plan", fmt: str = "png",
    underlays=(), dpi: int | None = None, paper=None, scale: str | None = None,
    long_edge: int | None = None,
) -> list[Path]:
    """Render one view (or ``"all"``) for every storey; returns the written snapshot paths.

    ``underlays`` (drawable ``Underlay`` records, → ``resolve_underlays``) are matched to
    plans by their ``storey`` tag. This is the "*look*" half of edit → build → check → look:
    with the survey drawing behind the linework the agent can see a partition sitting a foot
    off its source, which no numeric check reports. They are reference material and belong
    to that loop only — pass none for anything anybody else will read (→ 30 §Scaled
    underlays), which is what ``haus render --no-underlay`` is for.

    ``dpi`` and ``long_edge`` are the two ways to size a raster and they are mutually
    exclusive — one names a physical resolution, the other a pixel count, and an output can
    only honour one. Given neither, the longest edge is ``DEFAULT_LONG_EDGE``: sizing by dpi
    alone leaves the pixel count to whatever the drawing's fitted inch size happened to be.
    ``paper`` and ``scale`` put the drawing on a real sheet (→ module docstring).
    """
    if fmt not in FORMATS:
        raise ValueError(f"unknown format {fmt!r} ({'|'.join(FORMATS)})")
    page_dpi, long_edge = resolve_size(dpi, long_edge)
    # What to hand on to anything that resolves again (the recursion, ``render_plan``):
    # ``resolve_size`` fills one of the pair in, and passing both back would trip its own
    # mutual-exclusion guard.
    call_dpi = None if long_edge else page_dpi
    out_dir.mkdir(parents=True, exist_ok=True)
    if view == "all":
        return [path for one in VIEWS
                for path in render_views(model, out_dir, one, fmt, underlays, call_dpi,
                                         paper, scale, long_edge)]
    written: list[Path] = []
    storeys = [s.tag for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)]
    # A composed sheet gets its paper in the filename, exactly as ``haus print`` does. The
    # frameless review raster and a 24x36 plot of the same storey are different artifacts
    # and must not be the same file — the last command run would silently win.
    sfx = suffix_for_size(paper)
    if view == "plan":
        for storey in storeys:
            if not any(w.storey == storey for w in model.walls):
                continue
            written.append(render_plan(
                model, storey, out_dir / f"plan_{storey}{sfx}.{fmt}", dpi=call_dpi,
                underlays=[u for u in underlays if u.storey == storey],
                paper=paper, scale=scale, long_edge=long_edge))
    elif view == "3d":
        # 3D is the offscreen glTF artifact (#51): emit a self-contained .glb the UI panel
        # and a glTF viewer both read. A raster snapshot needs an offscreen GL context (M3);
        # the .glb is the durable artifact the agent-eyes loop and UI share. Paper and dpi
        # mean nothing to it — a .glb has neither.
        from typehaus.emit.gltf import emit_glb

        lod = "framed" if any(w.members for w in model.walls) else "core"
        written.append(emit_glb(model, out_dir / "model.glb", lod=lod))
    elif view == "site":
        from typehaus.emit.draw.siteplan import build_site_plan

        written.append(_write_view(
            model, build_site_plan(model), out_dir / f"site_plan{sfx}.{fmt}",
            _SheetId("SITE", "Site plan", "site · C-101", north_arrow=True),
            dpi=page_dpi, paper=paper, scale=scale, long_edge=long_edge))
    elif view == "section":
        from typehaus.emit.draw.section import build_center_section

        written.append(_write_view(
            model, build_center_section(model), out_dir / f"section_house{sfx}.{fmt}",
            _SheetId("SECT", "Building section", "section · house center"),
            dpi=page_dpi, paper=paper, scale=scale, long_edge=long_edge))
    elif view == "elevation":
        from typehaus.emit.draw.elevation import build_elevation

        for facing in ("north", "south", "east", "west"):
            written.append(_write_view(
                model, build_elevation(model, facing), out_dir / f"elev_{facing}{sfx}.{fmt}",
                _SheetId("ELEV", f"{facing.title()} exterior elevation",
                         f"elevation · {facing}"),
                dpi=page_dpi, paper=paper, scale=scale, long_edge=long_edge))
    elif view == "details":
        from typehaus.emit.draw.details import (
            build_authored_detail_scene,
            build_detail,
            derive_detail_slices,
        )

        # A detail already chose its own paper before it was cut (``detail_card``), and that
        # card *is* the true-scale sheet ``--paper`` exists to produce elsewhere — so the
        # sheet paper is deliberately not applied here. Only the dpi is: at DETAIL_DPI by
        # default, because the hatch and lettering are the finest content in the set.
        detail_dpi = DETAIL_DPI if dpi is None else dpi
        for detail in model.plan.elements_of_kind("Slice"):
            if detail.kind.value != "detail":
                continue
            scene = build_authored_detail_scene(model, detail)
            slug = detail.tag.replace("/", "_")
            written.append(write_scene(scene, out_dir / f"detail_{slug}.{fmt}",
                                       f"detail · {detail.title or detail.tag}",
                                       detail_dpi, long_edge))
        for derived in derive_detail_slices(model):
            scene, _findings = build_detail(model, derived)
            slug = derived.view.tag.replace("/", "_")
            written.append(write_scene(scene, out_dir / f"detail_{slug}.{fmt}",
                                       f"detail · {derived.key}", detail_dpi, long_edge))
            written.extend(_note_continuations(scene, out_dir, slug, fmt,
                                               f"detail · {derived.key}", detail_dpi,
                                               long_edge))
    else:
        raise ValueError(
            f"unknown view {view!r} ({'|'.join(VIEWS)}|all)")
    return written


def _note_continuations(scene, out_dir, slug: str, fmt: str, title: str,
                        dpi: int = DETAIL_DPI, long_edge: int | None = None) -> list:
    """``detail_<slug>-2.png`` … for notes that outrun one card's band.

    Paginate, don't truncate. With lettering fixed by definition, a note column that does
    not fit has only two honest outcomes and shrinking the type is not one of them. The
    continuation carries the notes alone — the drawing is on page 1 and repeating it would
    make a reader compare two copies of the same cut.
    """
    from typehaus.emit.draw.pdf_writer import note_pages

    frame = getattr(scene, "frame", None)
    if frame is None or not scene.notes:
        return []
    band = frame.bands.get("notes")
    if band is None:
        return []
    # A notes-only card: same paper, no geometry, the band grown across the whole sheet
    # because there is no drawing beside it to make room for. Pagination is done against
    # *both* bands at once, so a continuation's wider column is what its share of the notes
    # is measured into rather than the first page's narrow one.
    wide = _notes_only_frame(frame)
    pages = note_pages(scene.notes, band, wide.bands["notes"])
    out = []
    for index, columns in enumerate(pages[1:], start=2):
        page = scene.model_copy(update={
            "nodes": (),
            "notes": tuple(line for column in columns for line in column),
            "frame": wide})
        out.append(write_scene(page, out_dir / f"detail_{slug}-{index}.{fmt}",
                               f"{title} — notes {index}/{len(pages)}", dpi, long_edge))
    # Notes shrink as well as grow. A continuation left over from a longer run reads as a
    # page of the current set, so the ones this render did not write are removed.
    for stale in out_dir.glob(f"detail_{slug}-*.{fmt}"):
        if stale not in out:
            stale.unlink()
    return out


def _notes_only_frame(frame):
    """``frame`` with its notes band grown across the whole sheet, geometry removed."""
    from typehaus.emit.draw.detail_card import MARGIN_IN, TITLE_H_IN

    paper_w, paper_h = frame.paper
    band = (MARGIN_IN, MARGIN_IN, paper_w - 2 * MARGIN_IN,
            paper_h - 2 * MARGIN_IN - TITLE_H_IN)
    return frame.model_copy(update={
        "viewport": (MARGIN_IN, MARGIN_IN, 0.01, 0.01),
        "bands": {**frame.bands, "notes": band, "legend": (0.0, 0.0, 0.0, 0.0)},
    })
