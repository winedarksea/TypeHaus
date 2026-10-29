"""A door's four widths: leaf, unit, rough opening and clear passage (plans/door-sizing.md).

``DoorType.width``/``height`` is the NOMINAL leaf (decision 1). The RO is the product's
published one, else derived from the leaf and the house's ``TrimStandard`` (decision 2),
unless the opening holds its current framing (decision 6). One equation both derives an RO
and checks that a leaf fits one:

    rough_w = leaf_w + 2(a + g)            (+ g at a pair's meeting stiles)
    rough_h = finish + undercut + leaf_h + g + a      (from the subfloor)

A pure function of its arguments: no model, no house load.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.enums import DoorOperation

_IN = 0.0254
# Therma-Tru 2026 Arch 1.29-1.30 "Hinged Clear Opening": a flat 2-11/16" under the slab at
# every single-leaf size (2/8 -> 29-5/16", 3/0 -> 33-5/16"); a pair loses it per leaf.
CLEAR_DEDUCTION_M = (2 + 11 / 16) * _IN
CLEAR_DEDUCTION_BASIS = "estimated: Therma-Tru deduction (2026 Arch 1.29-1.30)"
# A prehung unit's shim space, per side, that a published RO must leave around it.
PREHUNG_SHIM_M = 0.25 * _IN
_FIT_TOLERANCE_M = 1e-5


@dataclass(frozen=True)
class CasedDoorDefaults:
    jamb_allowance_m: float = 0.0254  # 3/4-inch board plus 1/4-inch shim
    jamb_thickness_m: float = 0.01905
    casing_reveal_m: float = 0.0047625
    leaf_gap_m: float = 0.003
    leaf_thickness_m: float = 0.045
    stop_projection_m: float = 0.013
    stop_depth_m: float = 0.0095
    undercut_m: float = 0.010
    pocket_slot_gap_m: float = 0.003
    track_height_m: float = 0.020
    track_depth_m: float = 0.025
    room_probe_m: float = 0.15
    raised_sill_m: float = 0.05


CASED_DOOR_DEFAULTS = CasedDoorDefaults()


@dataclass(frozen=True)
class DoorSizing:
    """Every dimension in metres. ``ResolvedOpening.width_m`` is ``passage_w_m`` and its
    ``height_m`` is ``rough_h_m``; for every door but a pocket ``passage_w_m`` IS the RO."""

    nominal_w_m: float  # as ordered (DoorType.width)
    nominal_h_m: float
    leaf_w_m: float  # the leaf drawn: nominal, or inferred from a held RO
    leaf_h_m: float
    unit_w_m: float | None  # published prehung unit
    unit_h_m: float | None
    rough_w_m: float  # framed RO; a pocket's is its whole cassette
    rough_h_m: float
    passage_w_m: float  # the modelled void
    clear_w_m: float | None  # R311.2 clear width; None for a door that does not swing
    clear_h_m: float | None
    # The RO the nominal leaf needs: equals ``rough_*`` unless the opening is held.
    required_w_m: float
    required_h_m: float
    required_basis: str
    jamb_allowance_m: float
    leaf_gap_m: float
    floor_finish_m: float
    held: bool
    fits: bool  # the unit (or leaf) fits a published RO; a held RO is exempt
    basis: tuple[tuple[str, str], ...]

    @property
    def installed_unit(self) -> tuple[float, float] | None:
        """The published unit, unless a held RO (smaller than it) stands in its place."""
        if self.unit_w_m is None or self.unit_h_m is None or self.held:
            return None
        return self.unit_w_m, self.unit_h_m

    @property
    def frame_w_m(self) -> float:
        return self.rough_w_m

    @property
    def pocket_run_m(self) -> float:
        return self.rough_w_m - self.passage_w_m

    def basis_of(self, name: str) -> str:
        return dict(self.basis).get(name, "")


def _inches(value_m: float) -> str:
    return f'{value_m / _IN:g}"'


def _clear_width(door, door_type, leaf_w: float) -> tuple[float | None, str]:
    operation = door_type.operation
    pair = operation == DoorOperation.DOUBLE_SWING
    if operation not in (DoorOperation.SWING, DoorOperation.DOUBLE_SWING):
        return None, "does not swing"
    catalog = door_type.catalog_dimensions
    bookcase = door_type.bookcase_door
    leaves = 1 if (not pair or door_type.center_post) else 2
    single = leaf_w / 2 if pair else leaf_w
    if door_type.clear_passage is not None:
        clear, basis = door_type.clear_passage.meters, "authored"
    elif bookcase is not None and bookcase.clear_passage_width is not None:
        clear, basis = bookcase.clear_passage_width.meters, "authored: bookcase product"
    elif catalog is not None and catalog.clear_width_90 is not None:
        clear, basis = catalog.clear_width_90.meters, "published"
        if pair and door_type.center_post:
            clear, basis = clear / 2, "published, active leaf only (centre post)"
    else:
        clear, basis = leaves * (single - CLEAR_DEDUCTION_M), CLEAR_DEDUCTION_BASIS
    # A leaf stopped short of 90 degrees still crosses the opening by leaf * cos(angle).
    angle = float(getattr(door, "maximum_opening_degrees", 90.0) or 90.0)
    if angle < 90.0:
        clear -= leaves * single * math.cos(math.radians(angle))
        basis += f", at its {angle:g} degree stop"
    return clear, basis


def _clear_height(door, door_type, rough_h: float, a: float,
                  floor_finish: float) -> tuple[float | None, str]:
    operation = door_type.operation
    if operation not in (DoorOperation.SWING, DoorOperation.DOUBLE_SWING):
        return None, "does not swing"
    catalog = door_type.catalog_dimensions
    if catalog is not None and catalog.clear_height is not None:
        return catalog.clear_height.meters, "published"
    installation = getattr(door, "exterior_installation", None)
    sill = getattr(installation, "sill_design", None) if installation else None
    threshold = sill.threshold_height.meters if sill is not None else 0.0
    floor = max(threshold, floor_finish)
    what = "threshold" if threshold >= floor_finish and threshold > 0 else "finished floor"
    return rough_h - a - floor, f"computed: {what} to head jamb"


def door_sizing(door, door_type, trim_standard=None, kit=None,
                floor_finish_m: float = 0.0) -> DoorSizing:
    """Size one door. ``door`` is the authored ``Door``; ``kit`` a pocket frame kit
    (``StructuralHardware``) or None; ``floor_finish_m`` the floor build-up over the subfloor
    at this opening, the higher side."""
    d = CASED_DOOR_DEFAULTS
    if trim_standard is not None:
        a = trim_standard.jamb_allowance.meters
        derived = f"derived: {_inches(a)} jamb allowance"
    else:
        a = d.jamb_allowance_m
        derived = f"derived: {_inches(a)} default jamb allowance (no TrimStandard)"
    g = d.leaf_gap_m
    operation = door_type.operation
    pair = operation == DoorOperation.DOUBLE_SWING
    side = 2 * (a + g) + (g if pair else 0.0)
    head = floor_finish_m + d.undercut_m + g + a
    nominal_w, nominal_h = door_type.width.meters, door_type.height.meters
    catalog = door_type.catalog_dimensions
    unit_w = catalog.unit_width.meters if catalog else None
    unit_h = catalog.unit_height.meters if catalog else None
    published = door_type.rough_opening
    pocket = operation == DoorOperation.POCKET
    basis: dict[str, str] = {"leaf": "nominal"}
    if unit_w is not None:
        basis["unit"] = "published"

    # The RO this nominal leaf needs, before any hold.
    passage = nominal_w
    if operation == DoorOperation.OVERHEAD:
        rough_w, rough_h = nominal_w, nominal_h
        basis["rough"] = "ordered by opening"
    elif published is not None:
        rough_w, rough_h = published.width.meters, published.height.meters
        basis["rough"] = "published RO"
    elif pocket:
        rough_w, rough_h, basis["rough"] = _pocket_rough(nominal_w, nominal_h, kit, head,
                                                        floor_finish_m, derived)
    else:
        rough_w, rough_h = nominal_w + side, nominal_h + head
        generic = operation in (DoorOperation.SLIDE, DoorOperation.BIFOLD)
        basis["rough"] = derived + (" (generic: no sourced track)" if generic else "")
    if not pocket:
        passage = rough_w
    required_w, required_h, required_basis = rough_w, rough_h, basis["rough"]
    leaf_w, leaf_h = nominal_w, nominal_h

    held = getattr(door, "held_rough_opening", None)
    if held is not None and operation != DoorOperation.OVERHEAD:
        # The hold keeps today's void; the leaf drawn is what fits it.
        passage, rough_h = held.width.meters, held.height.meters
        if pocket:
            rough_w = passage + _pocket_run(passage, kit)
            leaf_w = passage - 2 * (a + g)
        else:
            rough_w = passage
            leaf_w = passage - side
        leaf_h = rough_h - head
        basis["rough"] = "held"
        basis["leaf"] = "inferred from the held RO"

    fits = True
    if held is None and published is not None:
        need_w = (unit_w if unit_w is not None else leaf_w) + 2 * PREHUNG_SHIM_M
        need_h = (unit_h if unit_h is not None else leaf_h) + PREHUNG_SHIM_M
        fits = (need_w <= rough_w + _FIT_TOLERANCE_M and need_h <= rough_h + _FIT_TOLERANCE_M)

    clear_w, basis["clear_w"] = _clear_width(door, door_type, leaf_w)
    clear_h, basis["clear_h"] = _clear_height(door, door_type, rough_h, a, floor_finish_m)
    return DoorSizing(
        nominal_w_m=nominal_w, nominal_h_m=nominal_h, leaf_w_m=leaf_w, leaf_h_m=leaf_h,
        unit_w_m=unit_w, unit_h_m=unit_h, rough_w_m=rough_w, rough_h_m=rough_h,
        passage_w_m=passage, clear_w_m=clear_w, clear_h_m=clear_h,
        required_w_m=required_w, required_h_m=required_h, required_basis=required_basis,
        jamb_allowance_m=a,
        leaf_gap_m=g, floor_finish_m=floor_finish_m, held=held is not None, fits=fits,
        basis=tuple(basis.items()))


def _pocket_run(passage_m: float, kit) -> float:
    """How far the cassette runs past the passage: the kit's published RO, else 2W + 1"."""
    published = None
    if kit is not None:
        published = kit.rough_opening_in_by_length_in.get(round(passage_m / _IN))
    if published is not None:
        return published * _IN - passage_m
    return passage_m + 1.0 * _IN


def _pocket_rough(leaf_w: float, leaf_h: float, kit, head: float, floor_finish: float,
                  derived: str) -> tuple[float, float, str]:
    rough_w = leaf_w + _pocket_run(leaf_w, kit)
    over = getattr(kit, "rough_opening_head_over_leaf_in", None) if kit else None
    if over is not None:
        return rough_w, floor_finish + leaf_h + over * _IN, f"pocket kit {kit.model}"
    basis = f"pocket kit {kit.model}, height {derived}" if kit else f"pocket 2W + 1\", {derived}"
    return rough_w, leaf_h + head, basis
