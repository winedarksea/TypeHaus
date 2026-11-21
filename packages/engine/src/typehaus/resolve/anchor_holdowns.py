"""Where each authored hold-down anchor (an SSTB) sits in its concrete: what its stem-wall row
is read at. One reader for ``resolve/rebar/strap_bars.py`` (the #4 bar p. 43 requires) and
``checks/structural/anchor_rod_hold_down.py``.

A site quacks like a ``StrapSite`` where the bar code reads one: ``strap`` carries the
along/across axes, ``centre_xy`` is the core's mid-thickness at the rod, and each end's
distance runs from the rod centre (``half_width_in`` 0).
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.hardware.anchor_holdowns import CORNER_RETURN_IN, SSTB_STEM
from typehaus.model.enums import ConnectorKind
from typehaus.quantities import M_PER_IN
from typehaus.resolve.strap_holdowns import EndSide, _cast_with, _core, _footing_bottom, ends_at


@dataclass(frozen=True)
class AnchorRef:
    tag: str
    part: str
    core_tag: str
    framed_tag: str | None
    point_xy: tuple
    line_z_m: float
    along_xy: tuple
    spoon_xy: tuple          # across the core: what the bar code calls the spoon


@dataclass(frozen=True)
class AnchorSite:
    strap: AnchorRef
    top_z_m: float
    pour_bottom_z_m: float
    behind_in: float         # rod centre to the face on -spoon
    ahead_in: float          # rod centre to the face on +spoon
    centre_xy: tuple
    ends: tuple[EndSide, EndSide]
    core: tuple
    le_in: float
    corner_leg_in: float = CORNER_RETURN_IN
    half_width_in: float = 0.0
    bar_kind: str = "sstb"


def _axis(core, point) -> tuple[tuple, tuple]:
    """``(along, across)`` unit vectors: along is the core polygon's longer extent."""
    xs, ys = [p[0] for p in core], [p[1] for p in core]
    if max(xs) - min(xs) >= max(ys) - min(ys):
        return (1.0, 0.0), (0.0, 1.0)
    return (0.0, 1.0), (1.0, 0.0)


def anchor_site(model, element) -> AnchorSite | None:
    row = SSTB_STEM.get(element.size or "")
    core_tag = next((t for t in element.connects
                     if (w := model.wall(t)) is not None and w.is_foundation), None)
    if row is None or core_tag is None or element.position is None:
        return None
    wall, core = model.wall(core_tag), _core(model, core_tag)
    if core is None:
        return None
    point = element.position.xy_m
    along, across = _axis(core, point)
    offs = [(p[0] - point[0]) * across[0] + (p[1] - point[1]) * across[1] for p in core]
    lo, hi = min(offs), max(offs)
    mid = (lo + hi) / 2.0
    centre = (point[0] + across[0] * mid, point[1] + across[1] * mid)
    top = wall.z1_m
    footing = _cast_with(model, core_tag)
    bottom = wall.z0_m
    if footing is not None and (fb := _footing_bottom(model, footing)) is not None:
        bottom = min(bottom, fb)
    framed = next((t for t in element.connects if t != core_tag
                   and (w := model.wall(t)) is not None and not w.is_foundation), None)
    line = element.elevation.meters if element.elevation is not None else top
    ref = AnchorRef(element.tag, element.size, core_tag, framed, point, line, along, across)
    return AnchorSite(ref, top, bottom, -lo / M_PER_IN, hi / M_PER_IN, centre,
                      ends_at(model, core_tag, centre, across, along, hi - lo, top, 0.0),
                      core, row.le_in)


def anchor_sites(model) -> list[AnchorSite]:
    plan = getattr(model, "plan", None)
    if plan is None:
        return []
    return [site for el in plan.all_elements()
            if getattr(el, "kind", None) is ConnectorKind.ANCHOR_BOLT
            and (site := anchor_site(model, el)) is not None]
