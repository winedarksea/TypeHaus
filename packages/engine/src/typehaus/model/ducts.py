"""Duct construction, declared once (decision #114): the ``BoxStandard`` pattern for air.

A ``DuctRun`` states a section and a route. What is installed along it — sheet gauge,
sealing, elbows, take-offs, reducers, collar dampers, boots, the equipment's port kit and
the hangers — is the house's construction standard, authored here once and derived per run
by ``resolve/duct_parts.py`` and ``resolve/duct_supports.py``. Products are named by
``*_product_ref`` (identity only); the published numbers sit on the rows with ``source``.
An unread number is ``None`` and grades UNKNOWN downstream, never a default.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import M_PER_IN, Length, ft

#: Kinds a ``DuctPartRow`` (and a derived ``ResolvedDuctPart``) may be.
#: ``takeoff``: a branch off the side of a larger main; ``tee``: off an equal one;
#: ``reducer``: one section end to end into another; ``collar_damper``: the start collar on a
#: plenum with its balancing damper; ``boot``: duct to a terminal neck; ``transition`` and
#: ``flex``: an equipment port kit; ``connector``: a vibration connector at an air handler.
DuctPartKind = Literal["takeoff", "tee", "reducer", "collar_damper", "boot", "transition",
                       "flex", "connector"]


def duct_size_text(diameter_m: float | None, width_m: float = 0.0, depth_m: float = 0.0) -> str:
    """A section as ordered: ``4in`` round, ``18x8`` rectangular (width x depth)."""
    if diameter_m:
        return f"{round(diameter_m / M_PER_IN, 2):g}in"
    return f"{round(width_m / M_PER_IN, 2):g}x{round(depth_m / M_PER_IN, 2):g}"


class RoundGaugeRow(HausModel):
    """IMC Table 603.4 at the standard's pressure class: round duct to ``max_diameter``."""

    max_diameter: Length
    gauge: int
    thickness: Length
    material: str = "galvanized"
    seam: str = "snap-lock"
    source: str | None = None


class DuctElbowRow(HausModel):
    """The round elbow bought at one size. An adjustable elbow is ordered at one of
    ``angles`` and set in the field; ``center_to_face`` is its laying length at 90 degrees."""

    diameter: Length
    product_ref: str
    kind: Literal["adjustable", "stamped", "gored", "pleated"] = "adjustable"
    angles: tuple[float, ...] = (90.0, 45.0)
    center_to_face: Length | None = None
    #: Dynamic loss coefficient at 90 degrees, as the source publishes it.
    loss_c: float | None = None
    source: str | None = None


class DuctPartRow(HausModel):
    """One purchased (or shop-fabricated) part for a size pair.

    ``size`` is the main or duct section (``duct_size_text``); ``branch`` the branch for a
    take-off/tee, the outlet for a reducer or transition, the neck face (``12x6``) for a
    boot (``none`` for a terminal with no neck), or None where the part fits any.
    ``integral`` means the terminal or equipment's own collar takes the duct: matched,
    nothing bought. ``length``/``width``/``height`` are
    the published envelope the part is drawn at.
    """

    kind: DuctPartKind
    size: str | None = None
    branch: str | None = None
    product_ref: str | None = None
    fabricated: bool = False
    integral: bool = False
    length: Length | None = None
    width: Length | None = None
    height: Length | None = None
    loss_c: float | None = None
    source: str | None = None


class DuctSupportRow(HausModel):
    """Hanger spacing and kind for duct up to ``max_size``: the diameter, or a rectangular
    duct's half-perimeter (SMACNA Table 4-1)."""

    section: Literal["round", "rectangular", "flex"] = "round"
    max_size: Length
    spacing: Length
    hanger: Literal["strap", "rod_trapeze", "saddle"] = "strap"
    product_ref: str | None = None
    #: The strap or rod as published: width x thickness, or rod diameter in ``width``.
    width: Length | None = None
    thickness: Length | None = None
    source: str | None = None


class PortKit(HausModel):
    """What connects a duct to an equipment type's ports (Broan: 6->8 transition + flex)."""

    type_ref: str
    ports: tuple[str, ...] = ()  # empty: every air port
    transition_product_ref: str | None = None
    transition_length: Length | None = None
    #: The transition's loss coefficient on the smaller section's velocity pressure.
    transition_loss_c: float | None = None
    flex_product_ref: str | None = None
    flex_length: Length | None = None
    #: The flexible part is an air handler's vibration connector, not a flex duct.
    connector: bool = False
    source: str | None = None


@register_element
class DuctStandard(Element):
    """The house's duct construction, one per plan (``integrity.duct_standard``)."""

    pressure_class_in_wg: float
    seal_class: str
    sealant_product_ref: str | None = None
    tape_product_ref: str | None = None
    #: LF of seam one sealant container covers, and the tape's roll length.
    sealant_coverage_lf: float | None = None
    tape_roll_length: Length | None = None
    #: Seam LF per joint of round duct: one girth joint per ``joint_length`` plus the
    #: longitudinal seam; the straight stock length a run is joined from.
    joint_length: Length = ft(5)
    insulation_product_ref: str | None = None
    round_gauges: tuple[RoundGaugeRow, ...] = ()
    elbows: tuple[DuctElbowRow, ...] = ()
    parts: tuple[DuctPartRow, ...] = ()
    supports: tuple[DuctSupportRow, ...] = ()
    #: A support within this of each elbow and branch (SMACNA).
    support_near_fitting: Length = ft(2)
    port_kits: tuple[PortKit, ...] = ()
    citations: tuple[str, ...] = ()

    def gauge_for(self, diameter_m: float, material: str = "galvanized") -> RoundGaugeRow | None:
        rows = sorted((r for r in self.round_gauges if r.material == material),
                      key=lambda r: r.max_diameter.meters)
        return next((r for r in rows if diameter_m <= r.max_diameter.meters + 1e-6), None)

    def elbow_for(self, diameter_m: float) -> DuctElbowRow | None:
        return next((r for r in self.elbows
                     if abs(r.diameter.meters - diameter_m) < 1e-4), None)

    def part(self, kind: str, size: str | None,
             branch: str | None = None) -> DuctPartRow | None:
        """The row for ``kind`` at (size, branch): an exact pair first, then a wildcard."""
        rows = [r for r in self.parts if r.kind == kind]
        for want in ((size, branch), (size, None), (None, branch), (None, None)):
            hit = next((r for r in rows if (r.size, r.branch) == want), None)
            if hit is not None:
                return hit
        return None

    def support_for(self, section: str, size_m: float) -> DuctSupportRow | None:
        rows = sorted((r for r in self.supports if r.section == section),
                      key=lambda r: r.max_size.meters)
        return next((r for r in rows if size_m <= r.max_size.meters + 1e-6), None)

    def port_kit(self, type_ref: str | None, port: str | None) -> PortKit | None:
        return next((k for k in self.port_kits if k.type_ref == type_ref
                     and (not k.ports or port in k.ports)), None)

    def product_refs(self) -> tuple[str, ...]:
        refs = [self.sealant_product_ref, self.tape_product_ref, self.insulation_product_ref,
                *(r.product_ref for r in self.elbows), *(r.product_ref for r in self.parts),
                *(r.product_ref for r in self.supports),
                *(ref for k in self.port_kits
                  for ref in (k.transition_product_ref, k.flex_product_ref))]
        return tuple(dict.fromkeys(ref for ref in refs if ref))


for _name, _cls in (("DuctStandard", DuctStandard), ("RoundGaugeRow", RoundGaugeRow),
                    ("DuctElbowRow", DuctElbowRow), ("DuctPartRow", DuctPartRow),
                    ("DuctSupportRow", DuctSupportRow), ("PortKit", PortKit)):
    register_constructor(_name, _cls)
