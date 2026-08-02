"""Edge trim by the lineal foot — the fascia/soffit/flashing family the solids sweep hides.

``glazing_trim_takeoff`` records the gap this closes for its own extrusions: the engine had
no lineal-foot section for trim at all, so the fascia/gutter family was only ever billed as
solids — cubic feet of PVC and aluminium, which is not how a fascia board or a drip edge is
bought. ``drainage_takeoff`` closed the gap for the stormwater half (gutter, leader); this
section is the rest of the family: the boards and formed metal along a deck or roof edge.

Two sources, exactly like the gutters:

* **authored edge runs** — :class:`~typehaus.model.trim.Fascia`, ``EaveSoffit`` and
  ``Flashing`` elements, billed along the path they are authored on. (``Gutter`` and
  ``Downspout`` belong to ``drainage``; ``GlazingTrim`` to ``glazing_trim``.)
* **derived roof trim** — the fascia boards, soffit panels, formed corner/rake trim,
  drip-edge band and vented ridge cap :mod:`typehaus.resolve.roof_trim` hangs off a resolved
  roof plane. The derived *gutter* members are deliberately absent here — ``drainage``
  already bills them, and one channel must not appear on two orders.

Mirror flags, following ``wood_surfaces``' convention: an authored run also resolves as
solids (counted by ``structural_solids``) and a derived member is a ``FramedMember`` under
``all_members()`` (counted by ``framing``), so every row says which other section sees the
same material — the primary *lineal-foot* billing lives here either way.
"""

from __future__ import annotations

import math

from typehaus.resolve.model import ResolvedModel

_M_TO_FT = 3.280839895013123
_M_TO_IN = 39.37007874015748

#: Derived roof-trim member categories billed here by the foot. ``gutter`` is excluded on
#: purpose (``drainage`` bills it); everything else the roof derives along an edge is trim
#: somebody orders in sticks or brake-formed lengths.
_DERIVED_CATEGORIES = frozenset({"fascia", "soffit", "cladding", "corner_trim", "ridge_cap"})

#: Banded derived categories resolve one run as several thin bands sharing a span; billing
#: every band would multiply the order. Per run, only the named band's length is counted —
#: the same dedupe ``takeoff/drainage.py::_add_derived_eave_gutters`` does with ``bottom``.
_BANDED_MEASURE = {"corner_trim": "face"}


class _Rows:
    """Accumulator keyed on what makes two runs the same line on the order."""

    def __init__(self) -> None:
        self._rows: dict[tuple, dict[str, object]] = {}

    def add(self, category: str, profile: str, material: str, *, tag: str,
            length_m: float, mirror: str) -> None:
        key = (category, material, profile)
        row = self._rows.get(key)
        if row is None:
            row = self._rows[key] = {
                "category": category, "profile": profile, "material": material,
                "count": 0, "length_m": 0.0, "mirror": mirror, "tags": [],
            }
        row["count"] = int(row["count"]) + 1
        row["length_m"] = float(row["length_m"]) + length_m
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(tag)

    def finish(self) -> list[dict[str, object]]:
        out: list[dict[str, object]] = []
        for key in sorted(self._rows, key=lambda k: tuple(map(str, k))):
            row = self._rows[key]
            out.append({
                "category": row["category"], "profile": row["profile"],
                "material": row["material"], "count": int(row["count"]),
                "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1),
                # Which other section sees the same material (→ module docstring): solids
                # for an authored run, the framing cut list for a derived member.
                "also_in_structural_solids": row["mirror"] == "structural_solids",
                "also_in_framing": row["mirror"] == "framing",
                "tags": sorted(row["tags"]),
            })
        return out


def _path_length_m(points) -> float:
    return sum(math.dist(a, b) for a, b in zip(points[:-1], points[1:]))


def _section_profile(depth_m: float, thickness_m: float) -> str:
    """The authored run's cross-section as an orderable name, face × thickness in inches."""
    return f'{depth_m * _M_TO_IN:g}" x {thickness_m * _M_TO_IN:g}"'


def edge_trim_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Lineal feet of edge trim, grouped by category, material and cross-section."""
    from typehaus.model.trim import EaveSoffit, Fascia, Flashing

    rows = _Rows()
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if not isinstance(element, (Fascia, EaveSoffit, Flashing)):
                continue
            rows.add(element.kind.value,
                     _section_profile(element.depth.meters, element.thickness.meters),
                     element.material or "", tag=element.tag,
                     length_m=_path_length_m([p.xy_m for p in element.path]),
                     mirror="structural_solids")
    _add_derived_roof_trim(model, rows)
    return rows.finish()


def _add_derived_roof_trim(model: ResolvedModel, rows: _Rows) -> None:
    """The trim a roof derives along its own edges (→ resolve/roof_trim.py).

    The drip-edge band member carries category ``cladding`` (it closes the stack edge in
    the roof's own cladding metal); it is renamed ``edge_cladding`` on the order so it
    cannot be read as a wall-cladding row.
    """
    for roof in model.roofs:
        for member in roof.members:
            category = member.category
            if category not in _DERIVED_CATEGORIES:
                continue
            band = _BANDED_MEASURE.get(category)
            # One band per run reaches the order: the composed piece mitres as one.
            if band is not None and member.child_key.rpartition("-")[2] != band:
                continue
            billed = "edge_cladding" if category == "cladding" else category
            rows.add(billed, member.profile, member.material or "",
                     tag=f"{roof.tag}:{member.child_key}", length_m=member.length_m,
                     mirror="framing")
