"""The review-layer vocabulary — one semantic stack, three readers (SVG, PSD, and the tags).

An AIA layer name says which *trade* drew a line. That is the right vocabulary for a plotter
and the wrong one for a person holding an iPad: nobody marking up a plan wants eighty-five
switches, they want "hide the services, draw on top of the shell". This module is the one
place that collapse is spelled out, so the grouped SVG and the layered PSD cannot disagree
about what a layer is or what order it sits in.

The order is bottom-to-top, i.e. painting order: the last entry covers the first. It is also
very nearly the order matplotlib already draws in (fills, then linework, then lettering), so
regrouping an SVG into it is a re-parenting and not a restack.

``ROUTING`` is the one group that is not a trade: it is the routing-space diagnosis — what
is clear, what is priced, what refuses and what is ungraded — drawn over everything else so
a reviewer can switch it on beside the plan it is about. It sits above ``NOTES`` because it
is an overlay somebody reads the plan *through*, and below ``OTHER`` so the escape hatch
stays the last real group.

``BACKGROUND`` and ``MARKUP`` carry no drawing nodes — they exist only in the PSD, as the
white ground underneath and the empty sheet a reviewer draws on. ``OTHER`` is the escape
hatch and it is deliberate: an unmapped layer must come out somewhere visible, because a
line that silently disappears from a review print is worse than a line in the wrong group.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReviewLayer:
    """One semantic group: its slug, what a human calls it, and where it sits in the stack."""

    slug: str
    name: str
    order: int
    #: True for the two groups that hold no drawing node — the PSD's ground and markup sheet.
    synthetic: bool = False


BACKGROUND = "background"
UNDERLAY = "underlay"
SITE = "site"
SHELL = "shell"
STRUCTURE = "structure"
OPENINGS = "openings"
STAIRS = "stairs"
SERVICES = "services"
FIXTURES = "fixtures"
FURNITURE = "furniture"
ROOMS = "rooms"
DIMENSIONS = "dimensions"
NOTES = "notes"
ROUTING = "routing"
OTHER = "other"
MARKUP = "markup"

#: The stack, bottom to top. Index is the order; nothing else may define one.
REVIEW_LAYERS: tuple[ReviewLayer, ...] = tuple(
    ReviewLayer(slug, name, i, synthetic)
    for i, (slug, name, synthetic) in enumerate((
        (BACKGROUND, "Background", True),
        (UNDERLAY, "Reference Underlay", False),
        (SITE, "Site / Context", False),
        (SHELL, "Building Shell", False),
        (STRUCTURE, "Structure", False),
        (OPENINGS, "Openings", False),
        (STAIRS, "Stairs / Rails", False),
        (SERVICES, "Building Services", False),
        (FIXTURES, "Fixtures / Equipment", False),
        (FURNITURE, "Furniture", False),
        (ROOMS, "Rooms", False),
        (DIMENSIONS, "Dimensions", False),
        (NOTES, "Notes / Symbols", False),
        (ROUTING, "Routing Space", False),
        (OTHER, "Other", False),
        (MARKUP, "Review Markup", True),
    ))
)

BY_SLUG: dict[str, ReviewLayer] = {layer.slug: layer for layer in REVIEW_LAYERS}

#: Layers whose name alone does not place them. Checked before the prefix ladder.
#:
#: Most of these are a discipline letter pointing at the wrong group. ``M-EQPT`` and
#: ``M-HVAC-EQPM`` are the air handler and the ERV — equipment a reviewer thinks of beside
#: the plumbing fixtures, not beside the duct runs that serve them. ``A-FLR-HEAT`` is the
#: radiant mat: an A- layer that is unambiguously a building service.
_EXACT: dict[str, str] = {
    "A-AREA-IDEN": ROOMS,
    "A-ANNO-DIMS": DIMENSIONS,
    "A-FLR-HEAT": SERVICES,
    "A-FIXT": FIXTURES,
    "M-EQPT": FIXTURES,
    "M-HVAC-EQPM": FIXTURES,
    "A-FURN": FURNITURE,
    "A-STAIR": STAIRS,
    "A-RAIL": STAIRS,
    "A-SLAB": SHELL,
    # A hole in a deck is a hole in the SHELL, beside the slab it perforates — not an
    # opening in the ``A-DOOR``/``A-GLAZ`` sense, which is a leaf in a wall.
    "A-FLOR-OPEN": SHELL,
    "L-SITE-GRAD": SITE,
}

#: Prefix ladder, longest prefix first so ``A-SITE-ANNO`` beats ``A-SITE``. Order within a
#: length does not matter: no two entries of equal length can both match one name.
_PREFIXES: tuple[tuple[str, str], ...] = tuple(sorted((
    ("A-SITE-ANNO", NOTES),
    ("A-SITE", SITE),
    ("A-ANNO", NOTES),
    ("A-DETL", NOTES),
    ("A-WALL", SHELL),
    ("A-ROOF", SHELL),
    ("A-DOOR", OPENINGS),
    ("A-GLAZ", OPENINGS),
    ("S-FRAM-OPEN", OPENINGS),
    ("C-ANNO", NOTES),
    # The routing-space overlay (→ ``emit/draw/routing_overlay.py``). Its own discipline
    # letter because it is not a trade's drawing at all: it is a diagnosis ABOUT the space
    # the trades share, and a reviewer switches it as one thing.
    ("Z-ROUT", ROUTING),
    ("S-", STRUCTURE),
    ("P-", SERVICES),
    ("M-", SERVICES),
    ("E-", SERVICES),
    ("C-", SITE),
    ("L-", SITE),
), key=lambda item: -len(item[0])))


def layer_for(aia_layer: str | None) -> str:
    """The review slug an AIA layer name belongs to. Never raises; unknowns land in ``other``.

    A ``None`` layer is a node the IR did not attribute — it is drawn, so it is grouped, and
    ``other`` is where it goes.
    """
    if not aia_layer:
        return OTHER
    name = aia_layer.strip().upper()
    if name in _EXACT:
        return _EXACT[name]
    for prefix, slug in _PREFIXES:
        if name.startswith(prefix):
            return slug
    return OTHER


def ordered_slugs(include_synthetic: bool = True) -> tuple[str, ...]:
    """Every slug bottom-to-top, optionally without the two PSD-only groups."""
    return tuple(layer.slug for layer in REVIEW_LAYERS
                 if include_synthetic or not layer.synthetic)
