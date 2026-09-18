"""The routing-space diagnosis as drawing nodes, on the shared review-layer stack.

``haus route --space`` classifies the space a target would search into four classes; this
turns those into :class:`~typehaus.emit.draw.scene.Hatch` nodes on the ``Z-ROUT-*`` AIA
layers, which ``review_layers`` maps to one ``ROUTING`` group. So the picture a reviewer
switches on is the same classification the terminal printed and the JSON carried, and there
is no second derivation for them to disagree about.

**This module does not import ``routing``, and cannot.** ``routing`` is a leaf that nothing
in ``emit`` may reach for (``tests/test_package_leaves.py``), and the rule is the right one:
a drawing that could run a search would be a drawing whose content moved when a cost weight
moved. So the regions are a *parameter* — plain records with ``klass``, ``tag``, ``kind``
and a shapely footprint — and the CLI, which sits above both, is what hands them over.

That boundary is also why ``haus render --view plan`` does not draw this on its own: a
render has no target, and "the routing space" is only defined for one. The overlay is
produced by ``haus route --space <target> --svg``, which knows what it is a space *for*.
"""

from __future__ import annotations

from typing import Any

from typehaus.emit.draw.review_layers import ROUTING, layer_for
from typehaus.emit.draw.scene import Hatch

#: One AIA layer per class, all of them under the ``Z-ROUT`` prefix so the review stack
#: collapses them into one group a reviewer switches as a unit.
LAYER_BY_CLASS: dict[str, str] = {
    "green": "Z-ROUT-CLER",
    "orange": "Z-ROUT-COST",
    "red": "Z-ROUT-BLOK",
    "gray": "Z-ROUT-UNKN",
}

#: The hatch each class is drawn with. Distinct *patterns* rather than only distinct
#: colours, because a review print is marked up in pencil as often as it is read on a
#: screen, and a colour-only legend is the one that does not survive a photocopier.
PATTERN_BY_CLASS: dict[str, str] = {
    "green": "SOLID",
    "orange": "ANSI31",
    "red": "ANSI37",
    "gray": "ANSI32",
}


def _rings(geometry: Any) -> list[tuple[tuple[float, float], ...]]:
    """Exterior rings of a polygon or multipolygon, as hatch boundaries.

    Interiors are dropped, and that is a deliberate limitation rather than an oversight: a
    hatch boundary in this IR is one ring, so a hole would have to be a second node with a
    background fill — which draws a white patch over whatever is underneath it. An overlay
    that covered the plan it is about would be worse than one that over-reports slightly,
    and the JSON carries the exact geometry for anybody who needs it.
    """
    geometries = getattr(geometry, "geoms", None)
    if geometries is not None:
        return [ring for part in geometries for ring in _rings(part)]
    exterior = getattr(geometry, "exterior", None)
    if exterior is None:
        return []
    return [tuple((float(x), float(y)) for x, y in exterior.coords)]


def overlay_nodes(regions: list[Any], *, level_m: float | None = None) -> list[Hatch]:
    """Hatches for every region, or for just one level.

    Order is the order the regions come in, which ``space_view`` already sets to red first
    and green last — so green, drawn last, sits under nothing and over nothing that matters.
    """
    out: list[Hatch] = []
    for region in regions:
        if level_m is not None and abs(region.level_m - level_m) > 1e-9:
            continue
        layer = LAYER_BY_CLASS.get(region.klass)
        if layer is None:
            continue  # a class this module has no drawing for is skipped, never guessed at
        for ring in _rings(region.footprint):
            if len(ring) < 3:
                continue
            # ``uid`` rather than a tag field: ``Hatch`` forbids extras and carries uid for
            # exactly this — hit-testing and annotation provenance, which is what a reviewer
            # clicking an orange patch wants back ("this is PR-B-KITCH-DRAIN").
            out.append(Hatch(boundary=ring, pattern=PATTERN_BY_CLASS[region.klass],
                             layer=layer, uid=region.tag))
    return out


def review_group() -> str:
    """The review-layer slug every node above lands in. One assertion's worth of proof."""
    group = layer_for(next(iter(LAYER_BY_CLASS.values())))
    if group != ROUTING:
        raise AssertionError(
            f"the Z-ROUT layers no longer map to the routing review group (got {group!r}) — "
            "review_layers._PREFIXES and LAYER_BY_CLASS have drifted apart")
    return group


#: Fill and stroke per class, and the opacity that lets the plan under it stay readable.
#: Colour-blind-safe pairs (blue/orange rather than red/green as the only distinction), and
#: the pattern above carries the same information for a print that has no colour at all.
_STYLE_BY_CLASS: dict[str, tuple[str, str, float]] = {
    "green": ("#c7e9c0", "#41ab5d", 0.35),
    "orange": ("#fdd0a2", "#e6550d", 0.45),
    "red": ("#a50f15", "#67000d", 0.45),
    "gray": ("#d9d9d9", "#737373", 0.40),
}


def overlay_svg(regions: list[Any], bbox: tuple[float, float, float, float], *,
                level_m: float | None = None, width_px: float = 1600.0) -> str:
    """A standalone SVG of the overlay, grouped by class inside one ``routing`` group.

    **Standalone, and the docstring above says why**: a plan render has no target, so there
    is no space for it to draw. This is the picture for one target, carrying the same review
    group name (``routing``) and the same ``Z-ROUT-*`` layer names the grouped plan SVG would
    use — so a reviewer who has both is looking at one vocabulary.

    y is flipped, because SVG's y grows downward and a plan's grows north.
    """
    minx, miny, maxx, maxy = bbox
    span_x = max(maxx - minx, 1e-9)
    span_y = max(maxy - miny, 1e-9)
    scale = width_px / span_x
    height_px = span_y * scale

    def project(point: tuple[float, float]) -> str:
        x, y = point
        return f"{(x - minx) * scale:.2f},{(maxy - y) * scale:.2f}"

    nodes = overlay_nodes(regions, level_m=level_m)
    by_layer: dict[str, list[Hatch]] = {}
    for node in nodes:
        by_layer.setdefault(node.layer, []).append(node)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px:.0f}" '
        f'height="{height_px:.0f}" viewBox="0 0 {width_px:.0f} {height_px:.0f}">',
        f'<g id="{review_group()}">',
    ]
    class_of = {layer: klass for klass, layer in LAYER_BY_CLASS.items()}
    # Green first so it paints underneath, then gray, orange and red on top of it — the
    # reverse of the reading order, which is what puts the refusals where the eye lands.
    for klass in ("green", "gray", "orange", "red"):
        layer = LAYER_BY_CLASS[klass]
        if layer not in by_layer:
            continue
        fill, stroke, opacity = _STYLE_BY_CLASS[class_of[layer]]
        parts.append(f'<g id="{layer}" fill="{fill}" stroke="{stroke}" '
                     f'stroke-width="1" fill-opacity="{opacity}">')
        for node in by_layer[layer]:
            points = " ".join(project(p) for p in node.boundary)
            parts.append(f'<polygon points="{points}"><title>{node.uid}</title></polygon>')
        parts.append("</g>")
    parts.extend(["</g>", "</svg>"])
    return "\n".join(parts)
