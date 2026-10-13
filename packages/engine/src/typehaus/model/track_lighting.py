"""Authored straight-track assemblies and movable, aimable LED heads.

Offsets are measured along the rail's local x axis from its midpoint. Azimuth is
counterclockwise from +x; tilt is measured from vertically down. The assembly's
placement remains one ordinary ElectricalDevice, with its heads configured on its type.
"""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length

TrackSystem = Literal["magnetic_24v", "h_track_120v"]
DIMENSION_TOLERANCE_M = 1e-9
# Generated m(...) quantities serialize to six significant figures.
ASSEMBLY_DIMENSION_TOLERANCE_M = 1e-6
ASSEMBLY_DIMENSION_RELATIVE_TOLERANCE = 1e-5


class TrackHeadProduct(HausModel):
    """Published head dimensions and electrical/optical performance."""

    product_ref: str
    system: TrackSystem
    body_length: Length
    body_diameter: Length
    adapter_length: Length
    adapter_width: Length
    adapter_height: Length
    pivot_drop: Length
    watts: float = Field(gt=0, allow_inf_nan=False)
    lumens: float = Field(gt=0, allow_inf_nan=False)
    cct_k: int = Field(gt=0)
    cri: int = Field(ge=0, le=100)
    beam_options: tuple[float, ...]
    optic_product_refs: dict[float, str] = Field(default_factory=dict)
    lumens_by_beam: dict[float, float] = Field(default_factory=dict)
    max_tilt_degrees: float = Field(ge=0, le=90, allow_inf_nan=False)
    max_azimuth_degrees: float = Field(gt=0, le=360, allow_inf_nan=False)
    damp_rated: bool = False
    source: str

    @model_validator(mode="after")
    def validate_product_dimensions(self):
        for name in ("body_length", "body_diameter", "adapter_length", "adapter_width",
                     "adapter_height", "pivot_drop"):
            value = getattr(self, name).meters
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a finite positive length")
        if not self.beam_options or any(not math.isfinite(v) or not 0 < v < 180
                                        for v in self.beam_options):
            raise ValueError("beam_options must contain finite angles between 0 and 180")
        if self.pivot_drop < self.adapter_height:
            raise ValueError("head pivot must be below the adapter")
        if any(beam not in self.beam_options or not ref
               for beam, ref in self.optic_product_refs.items()):
            raise ValueError("optic product references must name supported beam angles")
        if any(beam not in self.beam_options or not math.isfinite(lumens) or lumens <= 0
               for beam, lumens in self.lumens_by_beam.items()):
            raise ValueError("optic photometry must be positive, finite and supported")
        return self


class TrackHeadSpec(HausModel):
    product: TrackHeadProduct
    offset: Length
    azimuth_degrees: float = Field(ge=0, lt=360, allow_inf_nan=False)
    tilt_degrees: float = Field(ge=0, le=90, allow_inf_nan=False)
    beam_degrees: float = Field(gt=0, lt=180, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_aim_and_optic(self):
        if not math.isfinite(self.offset.meters):
            raise ValueError("head offset must be finite")
        if self.tilt_degrees > self.product.max_tilt_degrees:
            raise ValueError("head tilt exceeds the manufacturer's aiming limit")
        if self.azimuth_degrees > self.product.max_azimuth_degrees:
            raise ValueError("head azimuth exceeds the manufacturer's aiming limit")
        if self.beam_degrees not in self.product.beam_options:
            raise ValueError("head optic is not supported by this product")
        return self


class TrackLightingSpec(HausModel):
    system: TrackSystem
    rail_product_ref: str
    feed_product_ref: str
    feed_system: TrackSystem
    channel: int = Field(default=1, ge=1, le=2)
    rail_length: Length
    stock_length: Length
    rail_width: Length
    rail_height: Length
    feed_length: Length
    feed_width: Length
    feed_height: Length
    finish: Literal["white", "black"] = "white"
    feed_end: Literal["west", "east"] = "west"
    heads: tuple[TrackHeadSpec, ...]
    source: str

    @model_validator(mode="after")
    def validate_assembly(self):
        for name in ("rail_length", "stock_length", "rail_width", "rail_height",
                     "feed_length", "feed_width", "feed_height"):
            value = getattr(self, name).meters
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be a finite positive length")
        if self.rail_length > self.stock_length:
            raise ValueError("installed rail cannot exceed purchased stock length")
        if self.feed_system != self.system:
            raise ValueError("feed and rail systems are incompatible")
        if self.system == "h_track_120v" and self.channel != 1:
            raise ValueError("standard H track has one channel")
        if not self.heads:
            raise ValueError("a track luminaire needs at least one head")
        for head in self.heads:
            if head.product.system != self.system:
                raise ValueError("head and rail systems are incompatible")
            if abs(head.offset.meters) + head.product.adapter_length.meters / 2 \
                    > self.rail_length.meters / 2 + DIMENSION_TOLERANCE_M:
                raise ValueError("head adapter must fit wholly within the rail")
        intervals = sorted((h.offset.meters - h.product.adapter_length.meters / 2,
                            h.offset.meters + h.product.adapter_length.meters / 2)
                           for h in self.heads)
        if any(a[1] > b[0] + DIMENSION_TOLERANCE_M
               for a, b in zip(intervals, intervals[1:], strict=False)):
            raise ValueError("track head adapters overlap")
        if len({(h.product.cct_k, h.product.cri) for h in self.heads}) != 1:
            raise ValueError("one scheduled assembly must have one CCT and CRI")
        return self

    @property
    def head_count(self) -> int:
        return len(self.heads)

    @property
    def watts(self) -> float:
        return sum(head.product.watts for head in self.heads)

    @property
    def lumens(self) -> float | None:
        # Published lumens are for the catalog optic; do not invent another optic's output.
        values = [head.product.lumens_by_beam.get(
            head.beam_degrees, head.product.lumens
            if head.beam_degrees == head.product.beam_options[0] else None)
            for head in self.heads]
        if any(value is None for value in values):
            return None
        return sum(value for value in values if value is not None)


for _constructor in (TrackHeadProduct, TrackHeadSpec, TrackLightingSpec):
    register_constructor(_constructor.__name__, _constructor)
