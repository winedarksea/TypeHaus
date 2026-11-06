"""S-601's wall backing table: the authored ``WallBacking`` bands, grouped for the framer.

Grouped by stock, material and use (owner, 2026-11-05) with the band count and total LF; the
band-by-band list is the model's (``houses/<name>/plan``) and the takeoff's, where every
piece already bills as blocking. Pieces and LF are the resolved members, not the authored
runs: a band is cut at every stud and broken at openings (``framing/backing_panels.py``).
"""

from __future__ import annotations

import re

from typehaus.emit.draw.schedules.paged_tables import PagedTable
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 1.0 / 0.3048

#: Use classes read off the band's authored ``purpose`` words, first match wins. A reading
#: aid only: generic carpentry words, never a product or house tag; the rest is OTHER.
_USES = (
    ("GRAB BAR", r"grab bar"),
    ("HANDRAIL", r"handrail"),
    ("ACCESS PANEL", r"access panel"),
    ("TOWEL / TP / HOOK", r"towel|\btp\b|robe|\bpegs?\b|hook"),
    ("MIRROR / LIGHT / BOX", r"mirror|sconce|\bbox\b|backplate"),
    ("PLUMBING FIXTURE", r"sink|basin|\blav|hydrant|flange|\btub\b|shower"),
    ("SHELF / ROD", r"shel(f|ves)|\brod\b|clips?\b|\brack\b"),
    ("CASEWORK / RAIL", r"cabinet|\bcab\b|rail|restraint|ledger|frame|bracket|fixing|"
                        r"anchor|\bstand\b"),
    ("EQUIPMENT / MANTEL", r"mount|mantel|hood"),
)


def backing_use(purpose: str) -> str:
    for label, pattern in _USES:
        if re.search(pattern, purpose, re.IGNORECASE):
            return label
    return "OTHER"


def backing_table(model: ResolvedModel) -> PagedTable:
    """One row per (stock, material, use): bands, walls, resolved pieces and their LF."""
    from typehaus.resolve.framing.backing_panels import backing_bands

    bands = backing_bands(model.plan)
    groups: dict[tuple[str, str, str], dict] = {}
    for wall in model.walls:
        # The band ↔ member join ``resolve/backing_datum`` uses: ``backing-{ordinal}-``.
        ordered = sorted(bands.get(wall.tag, ()), key=lambda b: (b.elevation_m, b.tag))
        for ordinal, band in enumerate(ordered):
            prefix = f"backing-{ordinal}-"
            pieces = [m for m in wall.members if m.child_key.startswith(prefix)]
            if not pieces:
                continue  # clipped away entirely; advisory.backing reports the body
            row = groups.setdefault((band.profile, band.material_ref, backing_use(band.purpose)),
                                    {"bands": 0, "walls": set(), "pieces": 0, "lf": 0.0})
            row["bands"] += 1
            row["walls"].add(wall.tag)
            row["pieces"] += len(pieces)
            row["lf"] += sum(m.length_m for m in pieces) * _M_TO_FT
    rows = [(profile, material, use, str(row["bands"]), str(len(row["walls"])),
             str(row["pieces"]), f"{row['lf']:,.0f}")
            for (profile, material, use), row in sorted(groups.items())]
    if rows:
        rows.append(("TOTAL", "", "", str(sum(r["bands"] for r in groups.values())),
                     str(len(set().union(*(r["walls"] for r in groups.values())))),
                     str(sum(r["pieces"] for r in groups.values())),
                     f"{sum(r['lf'] for r in groups.values()):,.0f}"))
    return PagedTable("WALL BACKING — BY STOCK, MATERIAL AND USE",
                      ("Stock", "Material", "Use", "Bands", "Walls", "Pieces", "LF"),
                      tuple(rows))
