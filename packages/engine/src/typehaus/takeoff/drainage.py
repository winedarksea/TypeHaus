"""Stormwater by the foot and the piece: gutters, leaders, trenches, soakaways.

Drainage was billed only as solids — cubic feet of aluminium and stone, which is not how
any of it is bought. ``takeoff/glazing.py::glazing_trim_takeoff`` records the same gap for
the extrusion family and closes it the same way; this is the rest of that sentence, for the
family whose head is a hung channel and whose tail is a hole full of rock.

One flat section rather than four, with a uniform row shape, because it is one order: an
estimator pricing drainage wants the leaders on the same page as the gutter they hang off.
``length_ft`` and ``aggregate_cubic_yards`` are both present on every row and zero where the
product is not bought that way — a trench is bought by the foot *and* by the yard.

Gutters come from two places and both belong on the order: the authored :class:`Gutter` runs
and the :class:`EaveGutter` bands a roof derives along its own eaves. An estimator buying
gutter does not care which of those the drawing happened to use.
"""

from __future__ import annotations

import math

from typehaus.quantities import M_PER_IN
from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895
_M3_TO_CY = 1.30795062


def _path_length_m(points) -> float:
    # strict=True: two slices of the same list, both one shorter than it.
    return sum(math.dist(a, b) for a, b in zip(points[:-1], points[1:], strict=True))


class _Rows:
    """Accumulator keyed on what makes two runs the same line on the order."""

    def __init__(self) -> None:
        self._rows: dict[tuple, dict[str, object]] = {}

    def add(self, category: str, product: str, size_in: float, *, tag: str,
            length_m: float = 0.0, volume_m3: float = 0.0) -> None:
        key = (category, product, round(size_in, 2))
        row = self._rows.get(key)
        if row is None:
            row = self._rows[key] = {
                "category": category, "product": product, "size_in": round(size_in, 2),
                "count": 0, "length_m": 0.0, "volume_m3": 0.0, "tags": [],
            }
        row["count"] = int(row["count"]) + 1
        row["length_m"] = float(row["length_m"]) + length_m
        row["volume_m3"] = float(row["volume_m3"]) + volume_m3
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(tag)

    def finish(self) -> list[dict[str, object]]:
        return [
            {"category": row["category"], "product": row["product"],
             "size_in": row["size_in"], "count": int(row["count"]),
             "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
             "aggregate_cubic_yards": round(float(row["volume_m3"]) * _M3_TO_CY, 2),
             "tags": sorted(row["tags"])}
            for _, row in sorted(self._rows.items(), key=lambda kv: tuple(map(str, kv[0])))
        ]


def drainage_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """The stormwater order: gutter and leader by the foot, trenches and wells by both."""
    from typehaus.model.structure import Drywell, FrenchDrain
    from typehaus.model.trim import Downspout, Gutter

    rows = _Rows()
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, Gutter):
                rows.add("gutter", element.material or "",
                         element.depth.meters / M_PER_IN, tag=element.tag,
                         length_m=_path_length_m([p.xy_m for p in element.path]))
            elif isinstance(element, Downspout):
                # A leader is billed by its drop, not by a plan run: it is one vertical
                # length of pipe between the gutter outlet and the splash block.
                rows.add("downspout", element.material or "",
                         element.diameter.meters / M_PER_IN, tag=element.tag,
                         length_m=max(element.top_elevation.meters
                                      - element.bottom_elevation.meters, 0.0))
            elif isinstance(element, FrenchDrain):
                length = _path_length_m([p.xy_m for p in element.path])
                rows.add("french_drain", element.tile.material if element.tile else "stone",
                         element.trench_width.meters / M_PER_IN, tag=element.tag,
                         length_m=length,
                         volume_m3=(length * element.trench_width.meters
                                    * element.trench_depth.meters))
            elif isinstance(element, Drywell):
                radius = element.diameter.meters / 2.0
                rows.add("drywell", element.aggregate,
                         element.diameter.meters / M_PER_IN, tag=element.tag,
                         volume_m3=math.pi * radius ** 2 * element.depth.meters)

    _add_derived_eave_gutters(model, rows)
    return rows.finish()


def _add_derived_eave_gutters(model: ResolvedModel, rows: _Rows) -> None:
    """The channels a roof hangs along its own eaves (``EaveGutter``).

    A derived channel resolves as three bands of an open U. Its *length* is one band's run —
    billing all three would treble the order — and its size is the channel height, which
    only the back sheet stands the full depth of.
    """
    for roof in model.roofs:
        by_run: dict[str, dict[str, object]] = {}
        for member in roof.members:
            if member.category != "gutter":
                continue
            run_key, _, band = member.child_key.rpartition("-")
            entry = by_run.setdefault(run_key, {"material": member.material or ""})
            if band == "bottom":
                entry["length_m"] = member.length_m
            elif band == "back":
                entry["height_m"] = member.z1_m - member.z0_m
        for run_key, entry in sorted(by_run.items()):
            length = float(entry.get("length_m", 0.0))
            if length <= 0.0:
                continue
            rows.add("gutter", str(entry["material"]),
                     float(entry.get("height_m", 0.0)) / M_PER_IN,
                     tag=f"{roof.tag}:{run_key}", length_m=length)
