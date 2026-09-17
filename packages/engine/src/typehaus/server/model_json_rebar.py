"""The rebar payloads: a per-host summary in model.json, the bars behind ``GET /model/rebar``.

**Lazy, and measured into it** (decision #75): catlin's ~1,180 bars serialize to ~690 KB,
over the ~400 KB a model.json poll may grow by, and the Rebar chip is off by default. So
``model.json`` carries one summary row per reinforced host and the viewer fetches the bars
the first time the chip turns on (``/model/rebar`` served, ``rebar`` in the Pyodide worker).

Each bar is member-compatible — ``key``/``parent_uid``/``category``/``profile``/``shape``/
``width_m``/``p0``/``p1``/``z0_m``/``z1_m``/``length_m`` read the way a framed member's do, so
picking and identity code need no special case — plus its ``path`` (metres, rounded to the
millimetre), ``closed``, and a ``rebar`` block with what the Inspector shows.

Numbers are rounded here and nowhere else: 1,200 bars at full float precision is most of a
megabyte of digits nobody can see.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus.model.rebar import BARS
from typehaus.resolve.model import ResolvedModel
from typehaus.server.model_json_shared import _provenance
from typehaus.source.provenance import Provenance

_FT = 0.3048


def _mm(value: float) -> float:
    return round(value, 3)


def _bar_json(host_uid: str, bar) -> dict[str, Any]:
    path = [[_mm(x), _mm(y), _mm(z)] for x, y, z in bar.path]
    zs = [p[2] for p in path]
    geometric = sum(math.dist(bar.path[i], bar.path[i + 1]) for i in range(len(bar.path) - 1))
    return {
        "key": bar.key, "parent_uid": host_uid, "category": "rebar",
        "profile": f"#{bar.bar}", "shape": "bar",
        "width_m": _mm(bar.diameter_m), "depth_m": _mm(bar.diameter_m),
        "p0": path[0][:2], "p1": path[-1][:2], "z0_m": min(zs), "z1_m": max(zs),
        "length_m": _mm(geometric),
        "path": path, "closed": bar.closed,
        "rebar": {
            "role": bar.role, "bar": bar.bar, "coating": bar.coating,
            "spacing_in": bar.spacing_in, "piece": bar.piece, "pieces": bar.pieces,
            "placed_m": _mm(bar.placed_length_m), "lap_m": _mm(bar.lap_length_m),
            "hook_m": _mm(bar.hook_length_m), "cut_m": _mm(bar.cut_length_m),
            "hook_kinds": list(bar.hook_kinds),
            "weight_lb": round(bar.cut_length_m / _FT * BARS[bar.bar].weight_plf, 2),
            "note": bar.note,
        },
    }


def rebar_summary_json(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """model.json's ``rebar``: who carries steel, and how many pieces — no geometry."""
    return {
        "rebar": [
            {**_host_json(rebar_set, provenance), "bar_count": len(rebar_set.bars),
             "weight_lb": round(sum(b.cut_length_m / _FT * BARS[b.bar].weight_plf
                                    for b in rebar_set.bars), 1)}
            for rebar_set in sorted(model.rebar, key=lambda s: s.host_uid)
        ],
    }


def rebar_bars_json(model: ResolvedModel, provenance: Provenance | None) -> dict[str, Any]:
    """``GET /model/rebar``: every bar, filed under its host."""
    return {
        "rebar": [
            {**_host_json(rebar_set, provenance),
             "members": [_bar_json(rebar_set.host_uid, bar) for bar in rebar_set.bars]}
            for rebar_set in sorted(model.rebar, key=lambda s: s.host_uid)
        ],
    }


def _host_json(rebar_set, provenance: Provenance | None) -> dict[str, Any]:
    return {"uid": rebar_set.host_uid, "tag": rebar_set.host_tag, "storey": rebar_set.storey,
            "host_kind": rebar_set.host_kind, "scope": rebar_set.scope,
            "trades": ["concrete"], "provenance": _provenance(provenance, rebar_set.host_tag)}
