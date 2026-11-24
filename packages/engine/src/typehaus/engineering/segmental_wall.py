"""A segmental (SRW) wall's section, read off the model.

``tiered_retaining`` is RETIRED (2026-11-23, owner decision 4): IRC R404.4 does not engage on a
wall retaining <= 48" with no added load, and every raised-garden leg is drawn to Allan Block's
published gravity row (Table 1.3), graded by ``structural.srw_gravity_chart``
(``srw_chart``, the ``wall_panel`` precedent). No engineered item, no oracle, no record: what
stays is this reading, which the chart check and ``tier_surcharge`` (the apron's weight on the
court) both share, and ``srw_gravity``'s NCMA free body as the hand-oracled arithmetic
(``notes/raised_garden_srw.md`` §2-§8, ``tests/test_segmental_wall.py``).

Oracle for the reading: ``notes/raised_garden_srw.md`` §1, §4, §10.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.engineering.registry import EngineeringContext
from typehaus.engineering.retaining_basis import _base_interface
from typehaus.engineering.soil import presumptive
from typehaus.engineering.srw_chart import published_refusal
from typehaus.engineering.srw_gravity import FreeBody, Section, analyse
from typehaus.engineering.srw_tiers import TIER_FACTOR, Tier, lower_tiers

__all__ = ["TIER_FACTOR", "FreeBody", "Reading", "Section", "Tier", "analyse", "lower_tiers",
           "published_refusal", "reading", "segmental_walls"]

_M_PER_FT = 0.3048
_KG_M3_PER_PCF = 16.018463


# --- scope ----------------------------------------------------------------------------------

def _footingless_walls(ctx: EngineeringContext) -> list:
    from typehaus.model.structure import Footing, FoundationWall

    hosted = {f.under for f in ctx.plan.all_elements() if isinstance(f, Footing)}
    return [w for w in ctx.plan.all_elements()
            if isinstance(w, FoundationWall) and w.tag not in hosted]


def segmental_walls(ctx: EngineeringContext) -> list:
    """Retains fill, declares no restraint, has no footing — disjoint from
    ``retaining_wall``'s ``lateral_support`` scope by construction. The court
    reads each one's weight (``tier_surcharge``); none is a register item."""
    out = []
    for wall in _footingless_walls(ctx):
        if getattr(wall, "lateral_support", None) is not None:
            continue
        fill = getattr(wall, "unbalanced_fill", None)
        if fill is not None and fill.meters > 0.0:
            out.append(wall)
    return sorted(out, key=lambda w: w.tag)


# --- geometry off the model ----------------------------------------------------------------

def _embedment_ft(ctx: EngineeringContext, wall) -> tuple[float, str]:  # type: ignore[no-untyped-def]
    """Yard above the base, from the nearest grade station (else ``Site.grade``)."""
    from shapely.geometry import Point

    from typehaus.resolve.site_earth import nearest_grade_station, site_grade_elevation_m

    resolved = next((w for w in ctx.model.walls if w.tag == wall.tag), None)
    grade, label = site_grade_elevation_m(ctx.model), "Site.grade"
    if resolved is not None:
        (ax, ay), (bx, by) = resolved.axis
        station = nearest_grade_station(ctx.model, Point((ax + bx) / 2.0, (ay + by) / 2.0))
        if station is not None:
            label, grade = station
    return (grade - wall.bottom_elevation.meters) / _M_PER_FT, label


def _structure_layer(ctx: EngineeringContext, wall):  # type: ignore[no-untyped-def]
    from typehaus.model.enums import LayerFunction

    assembly = ctx.plan.library.resolve_assembly(wall.assembly)
    for layer in (assembly.layers if assembly is not None else ()):
        if layer.function is LayerFunction.STRUCTURE:
            return layer
    return None


@dataclass(frozen=True)
class Reading:
    """The wall as read off the model; ``tier_surcharge`` shares it rather than re-reading."""

    section: Section
    soil: object
    base: object
    yard_ft: float            # yard above the base, uncapped (>= 0)
    grade_from: str
    wall_ft: float
    weight_authored: bool
    pad_phi_deg: float | None = None
    pad_tag: str | None = None

    @property
    def weight_plf(self) -> float:
        """The whole unit on its pad: its own height, not the free body's."""
        return self.section.unit_weight_pcf * self.section.unit_depth_ft * self.wall_ft


def _pad(ctx: EngineeringContext, wall) -> tuple[float | None, str | None]:  # type: ignore[no-untyped-def]
    """The levelling pad's authored φ, and the bedding that states it."""
    from typehaus.model.structure import FootingBedding

    for bed in ctx.plan.all_elements():
        if (isinstance(bed, FootingBedding) and bed.host_ref == wall.tag
                and bed.friction_angle_deg is not None):
            return bed.friction_angle_deg, bed.tag
    return None, None


def reading(ctx: EngineeringContext, wall) -> tuple[Reading | None, list[str]]:  # type: ignore[no-untyped-def]
    tag = wall.tag
    spec = getattr(wall, "srw", None)
    missing: list[str] = []
    soil = presumptive(getattr(ctx, "soil_class", None),
                       basis=getattr(ctx, "soil_basis", None))
    if soil is None:
        missing.append("a declared soil class (Site/profile soil_class)")
    if wall.top_elevation is None or wall.bottom_elevation is None:
        missing.append(f"top_elevation/bottom_elevation on {tag}")
    layer = _structure_layer(ctx, wall)
    if layer is None and (spec is None or spec.unit_depth is None):
        missing.append(f"a STRUCTURE layer on {wall.assembly}, or srw.unit_depth")
    material = ctx.plan.library.material(layer.material_ref) if layer is not None else None
    density = getattr(material, "density", None)
    if (spec is None or spec.unit_weight_pcf is None) and not density:
        missing.append(f"srw.unit_weight_pcf on {tag} (its material carries no density)")
    if missing:
        return None, missing

    # Unit weight: the product's, else the material's density — a solid-unit UPPER bound on
    # resistance, so a FAIL on it is robust and a PASS on it is not (see the status below).
    weight_authored = spec is not None and spec.unit_weight_pcf is not None
    unit_pcf = spec.unit_weight_pcf if weight_authored else density / _KG_M3_PER_PCF
    depth_ft = (spec.unit_depth.feet if spec is not None and spec.unit_depth is not None
                else round(layer.thickness.inches * 2.0) / 24.0)
    batter = spec.batter_deg if spec is not None and spec.batter_deg is not None else 0.0
    coursing = getattr(getattr(layer, "masonry", None), "coursing", None)
    embedment, grade_from = _embedment_ft(ctx, wall)
    embedment = max(embedment, 0.0)
    retained = wall.unbalanced_fill.meters / _M_PER_FT
    wall_ft = (wall.top_elevation.meters - wall.bottom_elevation.meters) / _M_PER_FT
    section = Section(retained_ft=retained, unit_depth_ft=depth_ft, unit_weight_pcf=unit_pcf,
                      embedment_ft=min(embedment, max(wall_ft - retained, 0.0)),
                      batter_deg=batter, course_ft=coursing.feet if coursing is not None else 0.5)
    pad_phi, pad_tag = _pad(ctx, wall)
    return Reading(section, soil, _base_interface(ctx, wall) or soil, embedment, grade_from,
                   wall_ft, weight_authored, pad_phi, pad_tag), []


