"""Regroup a matplotlib SVG into named review layers, without changing what it looks like.

matplotlib writes one ``<g id="th-<slug>-<n>">`` per tagged artist (→ artist_tags) and
nothing above them: a vector editor opening the file sees a few thousand anonymous siblings.
This pass gathers those siblings into a handful of named groups an editor will show as
layers — Inkscape reads ``inkscape:groupmode``/``inkscape:label``, everything else at least
gets a named, selectable group and a ``data-typehaus-layer`` attribute to key off.

**It moves nothing across the tree, and it reorders nothing.** Groups are built from
*contiguous runs* of tagged siblings and re-inserted at the position the run started, inside
the run's own parent. That matters twice over: a matplotlib ``<g id="axes_1">`` carries the
clip path its children depend on, so lifting elements out of it would visibly change the
drawing; and document order is paint order, so a restack would too. Contiguity is not luck —
``ArtistTagger`` bands z-order by review layer, so matplotlib has already emitted the layers
in order and each one in a single run.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

from typehaus.emit.draw.review_layers import BY_SLUG, OTHER

_SVG_NS = "http://www.w3.org/2000/svg"
_INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape"
_SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd"

#: ``th-<slug>-<ordinal>``, optionally with the ``a`` suffix an annotation's arrow carries.
_TAG_ID = re.compile(r"^th-([a-z]+)-(\d+)a?$")


def _slug_of(element: ET.Element) -> str | None:
    match = _TAG_ID.match(element.get("id", ""))
    if match is None:
        return None
    slug = match.group(1)
    return slug if slug in BY_SLUG else OTHER


def regroup_svg(svg_text: str) -> str:
    """Return ``svg_text`` with its tagged artists gathered into named review-layer groups.

    Idempotent and total: an SVG with no tagged artists comes back unchanged apart from
    namespace declarations, and any tagged artist whose slug is unknown lands in ``other``
    rather than being dropped.
    """
    ET.register_namespace("", _SVG_NS)
    ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    ET.register_namespace("inkscape", _INKSCAPE_NS)
    ET.register_namespace("sodipodi", _SODIPODI_NS)
    root = ET.fromstring(svg_text)
    counts: dict[str, int] = {}
    _regroup(root, counts)
    # Declared on the root or a serialized document repeats them on every layer group.
    root.set(f"{{{_SODIPODI_NS}}}docname", "typehaus-review")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def _regroup(parent: ET.Element, counts: dict[str, int]) -> None:
    """Gather each contiguous run of tagged children of ``parent`` into one layer group."""
    children = list(parent)
    slugs = [_slug_of(child) for child in children]
    if not any(slugs):
        for child in children:
            _regroup(child, counts)
        return
    rebuilt: list[ET.Element] = []
    index = 0
    while index < len(children):
        slug = slugs[index]
        if slug is None:
            # Untagged chrome — matplotlib's figure/axes background patches. Left exactly
            # where it was, so the ground under the drawing stays under the drawing.
            _regroup(children[index], counts)
            rebuilt.append(children[index])
            index += 1
            continue
        stop = index
        while stop < len(children) and slugs[stop] == slug:
            stop += 1
        rebuilt.append(_layer_group(slug, children[index:stop], counts))
        index = stop
    for child in children:
        parent.remove(child)
    parent.extend(rebuilt)


def _layer_group(slug: str, members: list[ET.Element], counts: dict[str, int]) -> ET.Element:
    layer = BY_SLUG[slug]
    counts[slug] = counts.get(slug, 0) + 1
    # A slug should yield one run per drawing, but a framed sheet has two axes and the same
    # layer can legitimately appear in both. Suffixing keeps every id unique rather than
    # merging runs across parents, which is the one thing that would reorder the drawing.
    suffix = "" if counts[slug] == 1 else f"-{counts[slug]}"
    group = ET.Element(f"{{{_SVG_NS}}}g", {
        "id": f"typehaus-{slug}{suffix}",
        "data-typehaus-layer": slug,
        f"{{{_INKSCAPE_NS}}}groupmode": "layer",
        f"{{{_INKSCAPE_NS}}}label": layer.name,
    })
    group.extend(members)
    return group
