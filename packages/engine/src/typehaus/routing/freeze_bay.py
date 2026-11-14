"""Where in an exterior insulated bay a supply pipe is warm enough: the router's reading.

``mep.supply_freeze_exposure`` walks the resolved layers from the room to the design outdoor
air and grades the pipe's OUTBOARD face at ``T = T_in - (T_in - T_out) * R_in / R_total``
against freezing plus its margin; a bay with no continuous insulation outboard fails outright.
Routing may not import checks, so this restates that walk for a centreline anywhere in the
stud bay: the only depth-dependent R there is the bay's ``CavityFill``, so ``R_in`` is linear
in depth. Layers outboard of a back-vented rainscreen cavity are dropped, as ``glaser_layers``
does. Basis: ``houses/catlin/notes/supply_freeze_basis.md``; the hand-worked split is in
``tests/test_routing_supply.py``. Kept to the check's verdict by hand: change one, change both.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typehaus.quantities import M_PER_IN, rsi

#: The check's films (ISO 13788 Rsi 0.25, Rse 0.04 m2K/W, via ``glaser``).
_FILM_IN = rsi(0.25).r_us
_FILM_OUT = rsi(0.04).r_us
#: Water's 32 F plus the check's 10 F margin (``FreezeAdvisory``).
THRESHOLD_F = 42.0
#: The check's default ``interior_setpoint_f``; catlin pins the same 70.
INDOOR_F = 70.0
_WETTABLE = ("structure", "sheathing", "insulation")
_VENTED = ("airgap", "furring")


@dataclass(frozen=True)
class FreezeBay:
    """One exterior wall's bay, read across its depth.

    ``t`` is a plan point's coordinate along ``outward``; the bay spans ``inner_t..outer_t``.
    Each layer row is ``(z0, z1, side, R, continuous)``: side ``-1`` inboard, ``+1`` outboard
    (R total), ``0`` the bay's fill (R per metre of depth); ``continuous`` marks outboard
    non-cavity insulation, without which the bay is cold whatever the number.
    """

    outward: tuple[float, float]
    inner_t: float
    outer_t: float
    rows: tuple[tuple[float, float, int, float, bool], ...]
    outdoor_f: float

    def depth_t(self, x: float, y: float) -> float:
        return x * self.outward[0] + y * self.outward[1]

    def cold(self, t: float, z: float, radius_m: float) -> bool:
        """Whether a centreline at ``t``, height ``z``, reads cold (or bare) to the check."""
        r_in, r_out, per_m, cont = _FILM_IN, _FILM_OUT, 0.0, 0.0
        for z0, z1, side, r, continuous in self.rows:
            if not z0 - 1e-6 <= z <= z1 + 1e-6:
                continue
            if side < 0:
                r_in += r
            elif side > 0:
                r_out += r
                cont += r if continuous else 0.0
            else:
                per_m += r
        if cont <= 0.0:
            return True
        depth = min(max(t + radius_m, self.inner_t), self.outer_t) - self.inner_t
        r_in += per_m * depth
        r_out += per_m * (self.outer_t - self.inner_t - depth)
        temp = INDOOR_F - (INDOOR_F - self.outdoor_f) * r_in / (r_in + r_out)
        return temp < THRESHOLD_F


def freeze_bay(model: Any, wall: Any) -> FreezeBay | None:
    """The bay reading for one exterior wall; None without a framed bay or a design temp."""
    from shapely.geometry import Polygon

    heating = getattr(model.plan.project.site, "design_temp_heating", None)
    layers = [ly for ly in wall.layers if len(ly.polygon) >= 3]
    index = next((i for i, ly in enumerate(layers) if ly.function == "structure"), None)
    if heating is None or index is None or not layers[index].framed or len(wall.axis) < 2:
        return None
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    run = ((bx - ax) ** 2 + (by - ay) ** 2) ** 0.5
    if run < 1e-9:
        return None
    normal = (-(by - ay) / run, (bx - ax) / run)
    solid = [ly for ly in layers if ly.thickness_m > 0]  # ``wall_frame``'s orientation
    first, last = Polygon(solid[0].polygon).centroid, Polygon(solid[-1].polygon).centroid
    if (last.x - first.x) * normal[0] + (last.y - first.y) * normal[1] < 0:
        normal = (-normal[0], -normal[1])
    structure = layers[index]
    ts = [p[0] * normal[0] + p[1] * normal[1] for p in structure.polygon]
    library = model.plan.library
    rows = []
    for i, layer in enumerate(_vent_trimmed(layers)):
        if layer.thickness_m <= 0 or (layer.framed and not layer.is_cavity):
            continue  # the bay path: a framed layer carries R only through its fill
        material = library.material(layer.material_ref)
        r_per_in = getattr(material, "r_per_inch", None) or 0.0
        z0, z1 = layer.band(wall)
        if layer.is_cavity and layer.cavity_host == structure.name:
            rows.append((z0, z1, 0, r_per_in / M_PER_IN, False))
            continue
        side = -1 if i < index else 1
        rows.append((z0, z1, side, r_per_in * layer.thickness_m / M_PER_IN,
                     side > 0 and layer.function == "insulation" and not layer.is_cavity))
    return FreezeBay(normal, min(ts), max(ts), tuple(rows), heating.fahrenheit)


def _vent_trimmed(layers: list) -> list:
    """Layers up to a back-vented cavity: ``glaser_layers``' rule on resolved layers."""
    for i, layer in enumerate(layers):
        if layer.function not in _VENTED or layer.is_cavity or not any(
                inner.function in _WETTABLE for inner in layers[:i]):
            continue
        fill = sum(o.thickness_m for o in layers if o.is_cavity and o.cavity_host == layer.name)
        if fill <= 0:
            return layers[:i]
        if fill < layer.thickness_m - 1e-9:
            return [*layers[:i + 1], *(o for o in layers[i + 1:]
                                       if o.is_cavity and o.cavity_host == layer.name)]
    return layers
