"""Layered PSD — the same drawing, one raster layer per review layer, for markup on a tablet.

The reason this exists: Procreate does not read SVG, and a flat PNG is a photograph of a
drawing — you can scribble on it, but you cannot turn the dimensions off to see what is
underneath. A PSD opened *from the Procreate Gallery* keeps its layers (inserting one into an
existing canvas flattens it), so it is the one format that carries the review stack onto the
iPad intact.

**How the passes are made, and why they line up.** One figure is drawn, once. Each pass
hides every artist except the layer's own and saves the figure again against a **pinned**
bounding box (→ ``pdf_writer.save_box``); ``bbox_inches="tight"`` would re-crop each pass to
whatever was left visible and no two layers would register. Because ``ArtistTagger`` bands
z-order by review layer, stacking the passes back up reproduces the PNG rather than merely
resembling it — the residual difference is antialiasing at the few places two layers' ink
overlaps, where a transparent edge is composited twice instead of drawn once.

**Chrome goes on the Background.** Anything the figure drew that no IR node claimed — the
white ground, the caption, a sheet's border and title block — is unclaimed by definition and
would otherwise print into all fifteen passes. It is rendered once, opaquely, as the bottom
layer. Nothing else is opaque, so every layer above it composites cleanly.

Layers ship **unlocked**. psd-tools exposes no layer-protection API, and a lock hand-patched
into the record structures is a thing that breaks quietly on the next psd-tools release —
worse than no lock at all, because a reviewer would trust it.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

from typehaus.emit.draw.review_layers import BACKGROUND, BY_SLUG, MARKUP, REVIEW_LAYERS

#: Figure-level artist containers. A sheet's title block and scale bar are ``fig.text``
#: calls, which live here and on no axes — miss them and they print on every layer.
_FIG_CONTAINERS = ("texts", "patches", "lines", "artists", "images", "legends")
#: Per-axes containers, mirroring ``artist_tags._CONTAINERS``.
_AX_CONTAINERS = ("lines", "patches", "texts", "images", "collections", "artists")


def _every_artist(fig: Any) -> list[Any]:
    out: list[Any] = []
    for name in _FIG_CONTAINERS:
        out.extend(getattr(fig, name, []) or [])
    for ax in fig.axes:
        for name in _AX_CONTAINERS:
            out.extend(getattr(ax, name, []) or [])
        title = getattr(ax, "title", None)
        if title is not None:
            out.append(title)
    return out


def _render_pass(fig: Any, box: Any, dpi: float, transparent: bool) -> Any:
    from PIL import Image

    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=dpi, bbox_inches=box, pad_inches=0.0,
                transparent=transparent)
    buffer.seek(0)
    with Image.open(buffer) as image:
        return image.convert("RGBA")


def write_psd(fig: Any, tagger: Any, path: Path, *, box: Any, long_in: float,
              long_edge: int) -> Path:
    """Write ``fig`` as a layered PSD, one layer per non-empty review layer.

    ``fig``/``tagger`` come from ``pdf_writer.figure_for`` (or ``sheet_writer.compose_sheet``
    with a tagger passed in); ``box``/``long_in`` are exactly what ``pdf_writer.save_box``
    returned for that figure, so the PSD is the same crop and pixel size as the PNG beside it.
    """
    from psd_tools import PSDImage

    from typehaus.emit.draw.pdf_writer import dpi_for_long_edge

    by_slug = tagger.by_slug
    claimed = {id(artist) for artists in by_slug.values() for artist in artists}
    chrome = [a for a in _every_artist(fig) if id(a) not in claimed]
    dpi = dpi_for_long_edge(long_edge, long_in)

    visibility = {id(a): a.get_visible() for a in _every_artist(fig)}

    def show(only: list[Any]) -> None:
        keep = {id(a) for a in only}
        for artist in _every_artist(fig):
            artist.set_visible(id(artist) in keep and visibility.get(id(artist), True))

    try:
        show(chrome)
        background = _render_pass(fig, box, dpi, transparent=False)
        passes: list[tuple[str, Any]] = [(BACKGROUND, background)]
        for layer in REVIEW_LAYERS:
            artists = by_slug.get(layer.slug)
            if not artists:
                continue
            show(artists)
            passes.append((layer.slug, _render_pass(fig, box, dpi, transparent=True)))
    finally:
        for artist in _every_artist(fig):
            artist.set_visible(visibility.get(id(artist), True))

    from PIL import Image as _Image

    width, height = background.size
    psd = PSDImage.new(mode="RGB", size=(width, height), depth=8)
    for slug, image in passes:  # append order is bottom-to-top in the PSD record
        # Cropped to its own ink. A PSD layer carries an offset, so a 4096px canvas whose
        # dimensions occupy one band down the side stores that band and not four thousand
        # rows of nothing — on catlin's main plan the file goes from 56 MB to a fraction of
        # it, which is the difference between a drawing an iPad opens and one it refuses.
        # The Background is the ground and stays whole.
        box = None if slug == BACKGROUND else image.getbbox()
        if box is None and slug != BACKGROUND:
            continue  # claimed artists that drew no visible ink — an empty layer is noise
        cropped = image if box is None else image.crop(box)
        psd.create_pixel_layer(cropped, name=BY_SLUG[slug].name,
                               top=0 if box is None else box[1],
                               left=0 if box is None else box[0])
    # The sheet the reviewer actually draws on. Fully transparent, full canvas so a stroke
    # lands wherever the pencil goes, and on top so the first one is not inside the drawing.
    psd.create_pixel_layer(_Image.new("RGBA", (width, height), (0, 0, 0, 0)),
                           name=BY_SLUG[MARKUP].name, top=0, left=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    psd.save(str(path))
    return path
