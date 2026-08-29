"""Paper sizes and the architectural scale ladder — *what sheet, at what scale*.

Split out of ``sheet_writer`` so the two questions stay separable: this module answers
"how big is the sheet and what scale fits on it", ``sheet_writer`` answers "where does the
drawing, the border, the title block and the scale bar go on it". Both the permit set
(``sheets``) and the render cards (``detail_card``) read the ladder from here, and neither
should have to import a whole composer to ask how big 1/4" = 1'-0" is.

Print resolution, once, because it is the fact everyone asks twice: the permit PDF is
**vector**, so it carries no dpi at all and is the real large-format deliverable — an
ARCH D page plots at the printer's resolution, not at ours. A raster only ever
*approximates* it: matching an ARCH D sheet at plate quality means ``--dpi 300``
(36 x 24 in → 10800 x 7200 px, ~40 MB of PNG). 110 dpi is the default because the
agent-eyes loop reads snapshots on screen, where 300 buys nothing and costs seconds.
"""

from __future__ import annotations

# Paper presets, landscape (width, height) in inches.
LEDGER = (17.0, 11.0)
ARCH_D = (36.0, 24.0)
# E-602 carries four stacked tables (22 luminaire types, ~120 control rows in two columns,
# the 24V runs and the connected load) — more vertical content than an 11x17 landscape sheet
# holds at a legible type size. It prints portrait rather than shrinking the control schedule
# to unreadable. Every other table sheet is landscape; this is the one deliberate exception,
# and it still gets the same border and title block.
PORTRAIT_LEDGER = (11.0, 17.0)

#: The papers a whole set can be printed on, by CLI name, with the filename suffix that
#: keeps two printings of the same house side by side. Ledger takes the bare name because
#: it is the default and renaming the file every set already in someone's inbox is worse
#: than an asymmetric table.
PAPERS: "dict[str, tuple[float, float]]" = {"ledger": LEDGER, "arch-d": ARCH_D}
PAPER_SUFFIX: "dict[str, str]" = {"ledger": "", "arch-d": "_24x36"}


def suffix_for_size(size: "tuple[float, float] | None") -> str:
    """The filename suffix for a paper *size*, the inverse of :data:`PAPER_SUFFIX`.

    ``haus print`` names its output by the paper it composed (``permit_set_24x36.pdf``) so a
    ledger set and a large-format set can sit side by side. ``haus render`` writes fixed
    stems, so without this a 24x36 sheet and the frameless review raster of the same storey
    are the same file and the last command run silently wins — which is a nasty way to lose a
    plot. Orientation is ignored: a portrait sheet is the same paper.
    """
    if size is None:
        return ""
    normalised = (max(size), min(size))
    for name, preset in PAPERS.items():
        if (max(preset), min(preset)) == normalised:
            return PAPER_SUFFIX[name]
    return ""


def resolve_paper(name: str) -> "tuple[float, float]":
    """``"arch-d"`` → ``ARCH_D``; raises ``ValueError`` naming the known papers."""
    try:
        return PAPERS[name]
    except KeyError:
        raise ValueError(
            f"unknown paper {name!r} (choose from {', '.join(sorted(PAPERS))})") from None


def paper_for(paper: "tuple[float, float]", portrait: bool = False,
              ) -> "tuple[float, float]":
    """``paper`` turned to the requested orientation, whatever orientation it arrived in.

    The one sheet that prints portrait (E-602) has to stay portrait on *every* paper the
    set can be printed on, so the exception is expressed as an orientation rather than as
    a second hard-coded preset per paper.
    """
    short, long = min(paper), max(paper)
    return (short, long) if portrait else (long, short)


# Standard architectural scales as (sheet inches per model foot, printed label),
# largest first so "first that fits" is "largest that fits".
ARCH_SCALES = (
    (3.0, "3\" = 1'-0\""),
    (1.5, "1-1/2\" = 1'-0\""),
    (1.0, "1\" = 1'-0\""),
    (0.75, "3/4\" = 1'-0\""),
    (0.5, "1/2\" = 1'-0\""),
    (0.375, "3/8\" = 1'-0\""),
    (0.25, "1/4\" = 1'-0\""),
    (0.1875, "3/16\" = 1'-0\""),
    (0.125, "1/8\" = 1'-0\""),
    (0.09375, "3/32\" = 1'-0\""),
    (0.0625, "1/16\" = 1'-0\""),
)
# Civil/engineering scales, tried only after the architectural ladder is exhausted —
# a parcel-scale site plan is the sheet that needs them (1" = 20' is the residential norm).
ENG_SCALES = (
    (0.05, "1\" = 20'"),
    (1.0 / 30.0, "1\" = 30'"),
    (0.025, "1\" = 40'"),
    (0.02, "1\" = 50'"),
    (1.0 / 60.0, "1\" = 60'"),
    (0.01, "1\" = 100'"),
)
NTS_LABEL = "N.T.S."
#: The label ``--scale`` takes to mean "choose nothing, just fill the viewport".
FIT_LABEL = "fit"


def select_scale(span_u_in: float, span_z_in: float, view_w_in: float,
                 view_h_in: float) -> "tuple[float | None, str]":
    """Largest standard scale whose printed drawing fits the viewport.

    Spans are model-space inches; the viewport is paper inches. At scale ``s`` (sheet
    inches per model foot) a model span of ``x`` inches prints ``x / 12 * s`` inches.
    Architectural scales are preferred; engineering scales only continue the ladder below
    1/16" = 1'-0" for parcel-scale drawings. Returns ``(None, "N.T.S.")`` when nothing
    fits — the caller then fits-to-page and must label the sheet not-to-scale.
    """
    for s, label in (*ARCH_SCALES, *ENG_SCALES):
        if span_u_in / 12.0 * s <= view_w_in and span_z_in / 12.0 * s <= view_h_in:
            return s, label
    return None, NTS_LABEL


def fit_scale(span_u_in: float, span_z_in: float, view_w_in: float, view_h_in: float,
              pad: float = 1.0) -> float:
    """The non-standard scale that just fills the viewport — only ever used under N.T.S.

    ``pad`` > 1 shrinks the drawing by that factor so linework clears the border. A caller
    that draws inside its own gutters (the detail card) needs no pad and passes 1.0.
    """
    if span_u_in <= 0.0 or span_z_in <= 0.0:
        return ARCH_SCALES[-1][0]
    return min(view_w_in * 12.0 / span_u_in, view_h_in * 12.0 / span_z_in) / pad


def scale_for_label(label: str) -> "tuple[float, str] | None":
    """A typed scale label → its ``(scale, canonical label)`` entry, or ``None``.

    Whitespace-insensitive, because nobody types ``1/4" = 1'-0"`` with the spaces in when
    they are also fighting a shell about the quotes.
    """
    wanted = "".join(label.split())
    for scale, name in (*ARCH_SCALES, *ENG_SCALES):
        if "".join(name.split()) == wanted:
            return scale, name
    return None
