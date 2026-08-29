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

#: Every view ``--view all`` runs, in the order a reader would open them.
VIEWS = ("plan", "site", "section", "elevation", "details", "3d")


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


def render_plan(model: ResolvedModel, storey: str, path: Path, dpi: int = DEFAULT_DPI,
                underlays=(), paper=None, scale: "str | None" = None) -> Path:
    scene = build_floorplan(model, storey)
    return _write_view(model, scene, path,
                       _SheetId("PLAN", f"{storey.title()} floor plan",
                                f"plan · {storey}", north_arrow=True),
                       dpi=dpi, underlays=underlays, paper=paper, scale=scale)


def _write_view(model: ResolvedModel, scene, path: Path, sheet: _SheetId, *,
                dpi: int, underlays=(), paper=None, scale: "str | None" = None) -> Path:
    """One snapshot, on paper or not — the single place the two writers are chosen between.

    On paper the scene is given a real :class:`Frame` first (``frame_for_scene``) so the
    scale is *decided* rather than fitted, and ``compose_sheet`` places it inside the same
    border, title block and graphic scale bar the permit set prints. Off paper nothing
    changes from before: the frameless fit, which is what a quick look wants.
    """
    if paper is None:
        return write_raster(scene, path, title=sheet.caption, dpi=dpi, underlays=underlays)

    from typehaus.emit.draw.pdf_writer import _close
    from typehaus.emit.draw.sheet_writer import compose_sheet, frame_for_scene
    from typehaus.emit.draw.sheets import SheetSpec

    frame = frame_for_scene(scene, paper, scale_label=scale)
    if frame is not None:
        scene = scene.model_copy(update={"frame": frame})
    spec = SheetSpec(sheet.number, sheet.title, paper=paper,
                     north_arrow=sheet.north_arrow)
    fig = compose_sheet(scene, spec, model, size=spec.size, underlays=underlays)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=dpi)
    _close(fig)
    return path


def render_views(
    model: ResolvedModel, out_dir: Path, view: str = "plan", fmt: str = "png",
    underlays=(), dpi: "int | None" = None, paper=None, scale: "str | None" = None,
) -> list[Path]:
    """Render one view (or ``"all"``) for every storey; returns the written snapshot paths.

    ``underlays`` (drawable ``Underlay`` records, → ``resolve_underlays``) are matched to
    plans by their ``storey`` tag. This is the "*look*" half of edit → build → check → look:
    with the survey drawing behind the linework the agent can see a partition sitting a foot
    off its source, which no numeric check reports. They are reference material and belong
    to that loop only — pass none for anything anybody else will read (→ 30 §Scaled
    underlays), which is what ``haus render --no-underlay`` is for.

    ``dpi`` overrides the per-view default; ``paper`` and ``scale`` put the drawing on a
    real sheet (→ module docstring).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if view == "all":
        return [path for one in VIEWS
                for path in render_views(model, out_dir, one, fmt, underlays, dpi,
                                         paper, scale)]
    written: list[Path] = []
    storeys = [s.tag for s in sorted(model.plan.storeys, key=lambda x: x.elevation.meters)]
    page_dpi = DEFAULT_DPI if dpi is None else dpi
    # A composed sheet gets its paper in the filename, exactly as ``haus print`` does. The
    # frameless review raster and a 24x36 plot of the same storey are different artifacts
    # and must not be the same file — the last command run would silently win.
    sfx = suffix_for_size(paper)
    if view == "plan":
        for storey in storeys:
            if not any(w.storey == storey for w in model.walls):
                continue
            written.append(render_plan(
                model, storey, out_dir / f"plan_{storey}{sfx}.{fmt}", dpi=page_dpi,
                underlays=[u for u in underlays if u.storey == storey],
                paper=paper, scale=scale))
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
            dpi=page_dpi, paper=paper, scale=scale))
    elif view == "section":
        from typehaus.emit.draw.section import build_center_section

        written.append(_write_view(
            model, build_center_section(model), out_dir / f"section_house{sfx}.{fmt}",
            _SheetId("SECT", "Building section", "section · house center"),
            dpi=page_dpi, paper=paper, scale=scale))
    elif view == "elevation":
        from typehaus.emit.draw.elevation import build_elevation

        for facing in ("north", "south", "east", "west"):
            written.append(_write_view(
                model, build_elevation(model, facing), out_dir / f"elev_{facing}{sfx}.{fmt}",
                _SheetId("ELEV", f"{facing.title()} exterior elevation",
                         f"elevation · {facing}"),
                dpi=page_dpi, paper=paper, scale=scale))
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
            written.append(write_raster(scene, out_dir / f"detail_{slug}.{fmt}",
                                        title=f"detail · {detail.title or detail.tag}",
                                        dpi=detail_dpi))
        for derived in derive_detail_slices(model):
            scene, _findings = build_detail(model, derived)
            slug = derived.view.tag.replace("/", "_")
            written.append(write_raster(scene, out_dir / f"detail_{slug}.{fmt}",
                                        title=f"detail · {derived.key}", dpi=detail_dpi))
            written.extend(_note_continuations(scene, out_dir, slug, fmt,
                                               f"detail · {derived.key}", detail_dpi))
    else:
        raise ValueError(
            f"unknown view {view!r} ({'|'.join(VIEWS)}|all)")
    return written


def _note_continuations(scene, out_dir, slug: str, fmt: str, title: str,
                        dpi: int = DETAIL_DPI) -> list:
    """``detail_<slug>-2.png`` … for notes that outrun one card's band.

    Paginate, don't truncate. With lettering fixed by definition, a note column that does
    not fit has only two honest outcomes and shrinking the type is not one of them. The
    continuation carries the notes alone — the drawing is on page 1 and repeating it would
    make a reader compare two copies of the same cut.
    """
    from typehaus.emit.draw.pdf_writer import note_pages, write_raster

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
        out.append(write_raster(page, out_dir / f"detail_{slug}-{index}.{fmt}",
                                title=f"{title} — notes {index}/{len(pages)}", dpi=dpi))
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
