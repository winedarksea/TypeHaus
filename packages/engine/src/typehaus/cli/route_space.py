"""``haus route --space <target>``: the routing space classified, printed and as JSON.

The CLI half of :mod:`typehaus.routing.space_view`. It builds exactly the space the search
for that target would build — same radius, same margin, same ``--avoid``, same levels — and
classifies it instead of searching it. Same space, or the picture would be of a different
question from the refusal it is meant to explain.
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

console = Console()

#: How the terminal colours each class. The four words are the vocabulary
#: ``routing/space_view`` declares; this only says what they look like.
_STYLE = {"green": "green", "orange": "yellow", "red": "red", "gray": "bright_black"}

#: How many regions of one class one level prints before it stops listing and starts
#: counting. A reader needs the worst few and the total, not four hundred polygons.
_MAX_LISTED = 6


def print_space_view(model: Any, target: str, *, margin_ft: float,
                     band: tuple[float, float] | None, avoid: frozenset[str],
                     cost: Any, as_json: bool, svg_path: Any = None) -> int:
    """Classify and print. Returns the process exit code.

    Exit 0 whether or not the space is congested: this reports, it does not grade. A space
    full of red is a fact about a house, and ``haus check`` is what has opinions about it.
    """
    from typehaus.cli.route_support import _endpoints
    from typehaus.routing.graph import candidate_levels
    from typehaus.routing.space import build_space
    from typehaus.routing.space_view import space_view, summary

    problems: list[str] = []
    ends = _endpoints(model, target, "run", problems)
    if ends is None:
        for line in problems:
            console.print(f"[red]{line}[/red]")
        return 1

    terminals = [ends.origin, ends.root]
    space = build_space(model, radius_m=ends.radius_m, terminals=terminals,
                        margin_ft=margin_ft, avoid=avoid, touch=ends.touch, cost=cost,
                        z_band=band)
    levels = candidate_levels(space, terminals)
    regions = space_view(space, levels)

    if as_json:
        console.print_json(json.dumps({
            "target": target,
            "radius_m": ends.radius_m,
            "margin_ft": margin_ft,
            "levels_m": levels,
            "summary": summary(regions),
            "regions": [region.payload() for region in regions],
        }))
        return 0

    if svg_path is not None:
        from typehaus.emit.draw.routing_overlay import overlay_svg

        # One SVG per level, named by the level: a plan is one elevation, and stacking
        # eleven of them into one picture is a picture of nothing.
        svg_path.mkdir(parents=True, exist_ok=True)
        for index, level in enumerate(levels):
            body = overlay_svg(regions, space.bbox, level_m=level)
            (svg_path / f"{target}-z{index:02d}.svg").write_text(body + "\n")
        console.print(f"[dim]wrote {len(levels)} overlay(s) to {svg_path}[/dim]")

    console.print(f"[bold]{target}[/bold]: {len(levels)} level(s), "
                  f"{len(regions)} classified region(s)")
    for level in levels:
        here = [r for r in regions if r.level_m == level]
        console.print(f"\n[bold]z = {level / 0.3048:.2f} ft[/bold]")
        for klass in ("red", "orange", "gray", "green"):
            rows = [r for r in here if r.klass == klass]
            if not rows:
                continue
            style = _STYLE[klass]
            console.print(f"  [{style}]{klass}[/{style}]: {len(rows)} region(s), "
                          f"{sum(r.footprint.area for r in rows) / 0.09290304:.1f} sq ft")
            for region in rows[:_MAX_LISTED]:
                console.print(f"    [{style}]{region.tag}[/{style}] ({region.kind}) — "
                              f"{region.action}")
            if len(rows) > _MAX_LISTED:
                console.print(f"    [dim]+{len(rows) - _MAX_LISTED} more[/dim]")
    return 0
