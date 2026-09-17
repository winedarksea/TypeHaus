"""Reinforcing steel, in pounds — counted pieces off the laid-out bars (decision #75).

One row per ``(bar, coating, scope)``, summed over ``ResolvedModel.rebar``: the bars
``resolve/rebar`` laid out from each element's authored ``ReinforcementSpec``. ``length_ft``
is the **cut** length — placed + laps + hooks — because that is the steel a fabricator
ships; the three parts ride beside it so a reviewer can see what the laps cost.

**THE BOM BILLS ONLY WHAT A HOUSE AUTHORED, NEVER WHAT THE ENGINEERING SUITE DESIGNED.**
``engineering/`` grades the authored schedule; the layout lays out the authored schedule;
this bills the layout. A ``BASIS_VERSION`` bump cannot move the estimate, which is why this
module imports ``model`` and ``resolve`` and never ``engineering``.

A pour that authors no reinforcement contributes nothing, and that is a *hole* rather than a
zero: ``checks/structural`` reports it.

**Lengths carry their laps and hooks now**, so ``[waste]`` must not add them again —
``cli/price_file.WASTE_IN_QUANTITY`` refuses a ``reinforcement`` waste factor. Chairs,
bolsters and tie wire still ride inside the $/lb rate.
"""

from __future__ import annotations

from typing import Any

from typehaus.model.rebar import BARS

_M_TO_FT = 1.0 / 0.3048


def reinforcement_takeoff(model: Any) -> list[dict[str, object]]:
    """One row per ``(bar, coating, scope)``: cut/placed/lap/hook LF, pieces, bars, lb, tags.

    ``scope`` is the member family — "foundation wall", "footing", "pad", "slab", "column",
    "beam" — and part of the key because an estimator prices placing a mat and a cage
    differently even where the mill price is one number. ``count`` is bar RUNS (a lapped run
    is one bar in two pieces); ``pieces`` is what gets cut.
    """
    rows: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rebar_set in model.rebar:
        for bar in rebar_set.bars:
            key = (f"#{bar.bar}", bar.coating, rebar_set.scope)
            row = rows.get(key)
            if row is None:
                row = rows[key] = {"bar": key[0], "coating": bar.coating,
                                   "scope": rebar_set.scope, "length_ft": 0.0,
                                   "placed_length_ft": 0.0, "lap_length_ft": 0.0,
                                   "hook_length_ft": 0.0, "pieces": 0, "runs": set(),
                                   "tags": set()}
            _accumulate(row, bar)
            row["runs"].add(_run_key(bar))
            row["tags"].add(rebar_set.host_tag)
    return [_finish(rows[key]) for key in sorted(rows)]


def reinforcement_by_host(model: Any) -> list[dict[str, object]]:
    """The same steel, one row per ``(host, role, bar, coating)`` — the IFC's cut.

    Summed off the same pieces as :func:`reinforcement_takeoff`, so the two cannot disagree;
    ``tests/test_ifc_structural_enrichment.py`` sums these back up against the BOM.
    """
    out: list[dict[str, object]] = []
    for rebar_set in sorted(model.rebar, key=lambda s: s.host_tag):
        groups: dict[tuple[str, int, str], dict[str, Any]] = {}
        for bar in rebar_set.bars:
            key = (bar.role, bar.bar, bar.coating)
            row = groups.get(key)
            if row is None:
                size = BARS[bar.bar]
                row = groups[key] = {"tag": rebar_set.host_tag, "scope": rebar_set.scope,
                                     "role": bar.role, "bar": f"#{bar.bar}",
                                     "coating": bar.coating, "length_ft": 0.0,
                                     "placed_length_ft": 0.0, "lap_length_ft": 0.0,
                                     "hook_length_ft": 0.0, "pieces": 0,
                                     "diameter_in": size.diameter_in,
                                     "area_in2": size.area_in2}
            _accumulate(row, bar)
        for key in sorted(groups):
            row = groups[key]
            row["weight_lb"] = row["length_ft"] * BARS[int(row["bar"][1:])].weight_plf
            out.append(row)
    return out


def _accumulate(row: dict[str, Any], bar: Any) -> None:
    row["length_ft"] += bar.cut_length_m * _M_TO_FT
    row["placed_length_ft"] += bar.placed_length_m * _M_TO_FT
    row["lap_length_ft"] += bar.lap_length_m * _M_TO_FT
    row["hook_length_ft"] += bar.hook_length_m * _M_TO_FT
    row["pieces"] += 1


def _run_key(bar: Any) -> str:
    return bar.key.rsplit("-", 1)[0] if bar.pieces > 1 else bar.key


def _finish(row: dict[str, Any]) -> dict[str, object]:
    weight = BARS[int(row["bar"][1:])].weight_plf
    length = round(row["length_ft"], 1)
    return {"bar": row["bar"], "coating": row["coating"], "scope": row["scope"],
            "length_ft": length,
            "placed_length_ft": round(row["placed_length_ft"], 1),
            "lap_length_ft": round(row["lap_length_ft"], 1),
            "hook_length_ft": round(row["hook_length_ft"], 1),
            "pieces": row["pieces"], "count": len(row["runs"]),
            "weight_lb": round(length * weight, 1), "tags": sorted(row["tags"])}
