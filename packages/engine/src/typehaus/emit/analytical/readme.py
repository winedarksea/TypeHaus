"""`analysis/README.md` — which file opens in which tool, and every claim the model makes.

The four files beside it are the same graph four ways. This page is the one a reviewer
reads first: it tells them which to open, states the fixity, release and load claims in
prose (the `basis` and `source` strings the graph carries), and prints the gaps. Byte-
deterministic: no dates, sorted everywhere.
"""

from __future__ import annotations

from pathlib import Path

from typehaus.analytical.graph import AnalyticalModel, Fixity


def analysis_readme(model: AnalyticalModel, *, house: str, has_ifc: bool = True) -> str:
    fixed = sorted(s.element_tag or s.node for s in model.supports if s.fixity is Fixity.FIXED)
    pinned = sorted(s.element_tag or s.node for s in model.supports if s.fixity is Fixity.PINNED)
    lines = [
        f"# {house} — the analytical model",
        "",
        "The engineered items and their load path as nodes, members, supports and load cases,",
        "written four ways from one graph so the files cannot disagree with each other. Open",
        "the one your software reads:",
        "",
        "| Your software | Open | How |",
        "|---|---|---|",
    ]
    if has_ifc:
        lines.append("| SAP2000, ETABS | `../model.ifc` | *File > Import > IFC*; choose the "
                     "**structural analysis view**, not the coordination view, or every member "
                     "arrives twice |")
        lines.append("| Bonsai (Blender) | `../model.ifc` | load the project; the structural "
                     "panel lists the analysis model, its members, connections and load cases |")
    lines += [
        "| RISA-3D | `centreline.dxf` | *File > Import > DXF*: units **inches**, rotate so "
        "**Y is up** (the file is Z-up), and tick *translate layer names to section sets* — "
        "each layer is one section |",
        "| ForteWEB, WoodWorks Sizer, Enercalc | `members.csv` | one row per member: span, "
        "section, ends, releases, and the line and point loads per case, to type from |",
        "| Anything with Python | `model.pynite.py` | `pip install PyNiteFEA` then run it; it "
        "rebuilds the model, solves it and prints reactions per case |",
        "",
        "## What the model claims",
        "",
        "Every support, release and load below is a statement this engine makes and owns. A",
        "reviewer is entitled to disagree with any of them; each names its basis so the",
        "disagreement can be specific.",
        "",
        f"**Scope** — {len(model.members)} members, {len(model.nodes)} nodes, "
        f"{len(model.supports)} supports, from {len(model.scope)} engineered item(s):",
        "",
    ]
    lines += [f"- `{item}`" for item in model.scope]
    lines += ["", "**Supports**", ""]
    if fixed:
        lines.append(f"- FIXED ({len(fixed)}): {', '.join(f'`{t}`' for t in fixed)}")
    if pinned:
        lines.append(f"- PINNED ({len(pinned)}): {', '.join(f'`{t}`' for t in pinned)}")
    for support in sorted(model.supports, key=lambda s: (s.fixity.value, s.element_tag, s.node)):
        who = support.element_tag or support.node
        item = f" ({support.item_id})" if support.item_id else ""
        lines.append(f"  - `{who}` {support.fixity.value}{item}: {support.basis}")
    lines += ["", "**Load cases**", ""]
    for case in sorted(model.cases, key=lambda c: c.kind.value):
        member_n = sum(1 for load in model.member_loads if load.case is case.kind)
        point_n = sum(1 for load in model.member_point_loads if load.case is case.kind)
        node_n = sum(1 for load in model.node_loads if load.case is case.kind)
        lines.append(f"- `{case.name}` — {case.description}; {member_n} line, {point_n} point, "
                     f"{node_n} nodal load(s)")
    sources = sorted({load.source for load in (*model.member_loads, *model.member_point_loads,
                                                *model.node_loads) if load.source})
    if sources:
        lines += ["", "Where each load came from:", ""]
        lines += [f"- {source}" for source in sources]
    if model.combinations:
        lines += ["", "**Combinations** (only those a record graded against)", ""]
        for combo in sorted(model.combinations, key=lambda c: c.name):
            factors = ", ".join(f"{f:g} {k.value}" for k, f in sorted(combo.factors.items(),
                                                                       key=lambda kv: kv[0].value))
            lines.append(f"- `{combo.name}`: {factors} — {combo.source}")
    lines += ["", "**Assumptions**", ""]
    lines += [f"- {line}" for line in model.assumptions] or ["- none recorded"]
    lines += ["", "**Not modelled** (gaps, stated rather than defaulted)", ""]
    lines += [f"- {line}" for line in model.gaps] or ["- none"]
    lines += [
        "",
        "## Units and axes",
        "",
        "The IFC is in metres and newtons (SI, like the rest of the project file). The DXF is",
        "in inches. `members.csv` and the PyNite script are in pounds and inches. **Z is up** in",
        "every file; RISA and PyNite's plots default to Y-up, so rotate on import rather than",
        "re-reading the coordinates.",
        "",
    ]
    return "\n".join(lines)


def write_analysis_readme(model: AnalyticalModel, path: Path, *, house: str,
                          has_ifc: bool = True) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(analysis_readme(model, house=house, has_ifc=has_ifc),
                    encoding="utf-8", newline="")
    return path
