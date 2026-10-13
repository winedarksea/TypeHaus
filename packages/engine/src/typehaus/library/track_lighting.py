"""Orderable magnetic and integral-driver H-track assemblies.

Dimensions describe housings, not a photometric simulation. Adapter/pivot geometry is
schematic where manufacturers do not dimension the hinge; aiming uses that same modeled
pivot and lens in every output. Product data is fixed 3000K, with no selectable CCT.
"""

from __future__ import annotations

import math

from typehaus.model import (
    ElectricalDeviceType,
    Footprint2D,
    LuminaireForm,
    LuminaireType,
    Product,
    Service,
    ServicePort,
    TrackHeadProduct,
    TrackHeadSpec,
    TrackLightingSpec,
)
from typehaus.model.placeable_symbols._track_lighting import (
    head_pivot,
    track_bounds,
    track_dimensions,
)
from typehaus.quantities import Length, inch, m, pt

PUREEDGE_RAIL_SOURCE = "https://www.pureedgelighting.com/edge/specs/PureEdge_TS24M_Surface_Suspended_MagneticTrack_2C.pdf"
PUREEDGE_HEAD_SOURCE = "https://www.pureedgelighting.com/pure/specs/PureEdge_T24M_Radiant_Medium.pdf"
WAC_RAIL_SOURCE = "https://waclighting.com/product/h-track/"
WAC_HEAD_SOURCE = "https://www.waclighting.com/storage/waclighting-images/specsheet_pdf/2010-HJL_SPSHT.pdf"
POWER_120 = (ServicePort(tag="power", service=Service.POWER_120,
                         position=(m(0), m(0), m(0))),)


def radiant_medium(finish: str = "white") -> TrackHeadProduct:
    suffix = _finish_suffix(finish, "WH", "BK")
    return TrackHeadProduct(
        product_ref=f"PROD-PUREEDGE-T24M-2C-RADM-FL-30K-{suffix}", system="magnetic_24v",
        body_length=inch(3.94), body_diameter=inch(2.36), adapter_length=inch(3.5),
        adapter_width=inch(0.94), adapter_height=inch(0.67), pivot_drop=inch(2.29),
        watts=11, lumens=660, cct_k=3000, cri=93, beam_options=(45, 20, 35, 60),
        optic_product_refs={20: "PROD-PUREEDGE-LEN-RADM-SP-SW",
                            35: "PROD-PUREEDGE-LEN-RADM-NF-SW",
                            60: "PROD-PUREEDGE-LEN-RADM-WF-SW"},
        max_tilt_degrees=90, max_azimuth_degrees=360, damp_rated=True,
        source=PUREEDGE_HEAD_SOURCE)


def silo_x10(finish: str = "white") -> TrackHeadProduct:
    suffix = _finish_suffix(finish, "WT", "BK")
    return TrackHeadProduct(
        product_ref=f"PROD-WAC-H-2010-930-{suffix}", system="h_track_120v",
        body_length=inch(5), body_diameter=inch(2), adapter_length=inch(2),
        adapter_width=inch(1.375), adapter_height=inch(0.875), pivot_drop=inch(1.5),
        watts=10, lumens=790, cct_k=3000, cri=90, beam_options=(35, 25),
        lumens_by_beam={35: 790, 25: 790},
        max_tilt_degrees=90, max_azimuth_degrees=350, source=WAC_HEAD_SOURCE)


def _finish_suffix(finish: str, white: str, black: str) -> str:
    if finish not in ("white", "black"):
        raise ValueError("track finish must be white or black")
    return white if finish == "white" else black


def _default_heads(product: TrackHeadProduct) -> tuple[TrackHeadSpec, ...]:
    return tuple(TrackHeadSpec(product=product, offset=inch(offset), azimuth_degrees=270,
                               tilt_degrees=15, beam_degrees=product.beam_options[0])
                 for offset in (-12, 12))


def magnetic_track_spec(*, rail_length: Length | None = None, finish: str = "white",
                        heads: tuple[TrackHeadSpec, ...] | None = None) -> TrackLightingSpec:
    suffix = _finish_suffix(finish, "WH", "BK")
    return TrackLightingSpec(
        system="magnetic_24v", feed_system="magnetic_24v",
        rail_product_ref=f"PROD-PUREEDGE-TS24M-2C-4FT-{suffix}",
        feed_product_ref=f"PROD-PUREEDGE-TS24M-2C-EP-{suffix}",
        rail_length=rail_length if rail_length is not None else inch(36),
        stock_length=inch(48), rail_width=inch(0.94),
        rail_height=inch(0.94), feed_length=inch(6), feed_width=inch(4.6),
        feed_height=inch(0.94), finish=finish,
        heads=heads if heads is not None else _default_heads(radiant_medium(finish)),
        source=PUREEDGE_RAIL_SOURCE)


def standard_track_spec(*, rail_length: Length | None = None, finish: str = "white",
                        heads: tuple[TrackHeadSpec, ...] | None = None) -> TrackLightingSpec:
    suffix = _finish_suffix(finish, "WT", "BK")
    return TrackLightingSpec(
        system="h_track_120v", feed_system="h_track_120v",
        rail_product_ref=f"PROD-WAC-HT4-{suffix}", feed_product_ref=f"PROD-WAC-HLE-{suffix}",
        rail_length=rail_length if rail_length is not None else inch(48),
        stock_length=inch(48), rail_width=inch(1.375),
        rail_height=inch(0.75), feed_length=inch(4.25), feed_width=inch(1.375),
        feed_height=inch(0.75), finish=finish,
        heads=heads if heads is not None else _default_heads(silo_x10(finish)),
        source=WAC_RAIL_SOURCE)


def track_luminaire(tag: str, spec: TrackLightingSpec, *, type_mark: str | None = None,
                    name: str | None = None) -> LuminaireType:
    width, depth, height = track_dimensions(spec)
    x0, y0, _z0, x1, y1, _z1 = track_bounds(spec)
    magnetic = spec.system == "magnetic_24v"
    return LuminaireType(
        tag=tag, type_mark=type_mark, name=name or f"{spec.system} adjustable track",
        form=LuminaireForm.TRACK, track_lighting=spec,
        footprint=(m(width), m(depth)), height=m(height), plan_symbol="track-light",
        footprint_shape=Footprint2D(points=tuple(pt(m(x), m(y))
                                                for x, y in ((x0, y0), (x1, y0),
                                                             (x1, y1), (x0, y1)))),
        lamp=f"{spec.head_count} replaceable LED heads", watts=spec.watts, lumens=spec.lumens,
        cct_k=spec.heads[0].product.cct_k, cri=spec.heads[0].product.cri,
        voltage=24 if magnetic else 120, dimmable=True,
        damp_rated=all(head.product.damp_rated for head in spec.heads),
        needs=frozenset() if magnetic else frozenset({Service.POWER_120}),
        ports=() if magnetic else POWER_120, load_va=None if magnetic else spec.watts,
        product_ref=spec.rail_product_ref, source=spec.source)


def aim_head_at(spec: TrackLightingSpec, head: TrackHeadSpec,
                target_from_rail_ceiling_m: tuple[float, float, float]) -> TrackHeadSpec:
    """Aim the optical axis through a task target; lens and pivot are collinear."""
    pivot = head_pivot(spec, head)
    dx, dy, dz = (target - origin for target, origin
                  in zip(target_from_rail_ceiling_m, pivot, strict=True))
    if not all(math.isfinite(v) for v in (dx, dy, dz)) or dz >= 0:
        raise ValueError("task target must be finite and below the modeled pivot")
    return TrackHeadSpec(product=head.product, offset=head.offset, beam_degrees=head.beam_degrees,
                         azimuth_degrees=math.degrees(math.atan2(dy, dx)) % 360,
                         tilt_degrees=math.degrees(math.atan2(math.hypot(dx, dy), -dz)))


PUREEDGE_SUPPLY = ElectricalDeviceType(
    tag="ED-T-LT-PSU-PUREEDGE-40", name="PureEdge accessible 40W 24V supply enclosure",
    footprint=(inch(15.65), inch(3.43)), height=inch(6.37), plan_symbol="junction-box",
    load_va=40, output_voltage=24, ports=POWER_120,
    product_ref="PROD-PUREEDGE-PSB-40W-UNI-24VDC-T", source=PUREEDGE_RAIL_SOURCE)


def _product(tag: str, brand: str, model: str, name: str, url: str) -> Product:
    return Product(tag=tag, brand=brand, model=model, name=name, url=url,
                   source="Manufacturer specification; pricing quote required. " + url)


MAGNETIC_TRACK_PRODUCTS = (
    *(_product(f"PROD-PUREEDGE-LEN-RADM-{optic}-SW", "PureEdge", f"LEN-RADM-{optic}-SW",
               "Field-changeable Radiant Medium static-white optic", PUREEDGE_HEAD_SOURCE)
      for optic in ("SP", "NF", "WF")),
    _product("PROD-PUREEDGE-TS24M-2C-4FT-WH", "PureEdge", "TS24M-2C-4FT-WH",
             '48" magnetic rail stock, field cut; includes caps, covers, anchors and screws',
             PUREEDGE_RAIL_SOURCE),
    _product("PROD-PUREEDGE-TS24M-2C-EP-WH", "PureEdge", "TS24M-2C-EP-WH",
             "White magnetic-track end feed", PUREEDGE_RAIL_SOURCE),
    _product("PROD-PUREEDGE-T24M-2C-RADM-FL-30K-WH", "PureEdge", "T24M-2C-RADM-FL-30K-WH",
             "Radiant Medium head, 11W / 660lm / fixed 3000K / CRI93 / 45°", PUREEDGE_HEAD_SOURCE),
    _product("PROD-PUREEDGE-PSB-40W-UNI-24VDC-T", "PureEdge", "PSB-40W-UNI-24VDC-T",
             "40W universal 24V DC supply in accessible surface enclosure", PUREEDGE_RAIL_SOURCE),
)
STANDARD_TRACK_PRODUCTS = (
    _product("PROD-WAC-HT4-WT", "WAC", "HT4-WT", '48" white H-track', WAC_RAIL_SOURCE),
    _product("PROD-WAC-HLE-WT", "WAC", "HLE-WT", "White H-track live end", WAC_RAIL_SOURCE),
    _product("PROD-WAC-H-2010-930-WT", "WAC", "H-2010-930-WT",
             "Silo X10 integral-driver head, 10W / 790lm / fixed 3000K", WAC_HEAD_SOURCE),
)
