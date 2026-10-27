"""Build door sections with explicit provenance in the host wall's signed frame."""

from dataclasses import dataclass


@dataclass(frozen=True)
class DoorInstallationSection:
    name: str
    polygon_m: tuple[tuple[float, float], ...]  # signed wall normal, absolute elevation
    span_m: float
    along_m: float
    material_ref: str
    material_key: str
    purchase: str = "site"
    source_url: str | None = None
    geometry_status: str = "PROJECT_DESIGN"


class DoorSectionBuilder:
    def __init__(self, outward_sign, default_span_m):
        self.outward_sign = outward_sign
        self.default_span_m = default_span_m
        self.sections = []

    def section(
        self,
        name,
        profile,
        material,
        key,
        span=None,
        along=0,
        purchase="site",
        source_url=None,
        geometry_status="COORDINATION_ENVELOPE",
    ):
        self.sections.append(
            DoorInstallationSection(
                name,
                tuple((self.outward_sign * x, z) for x, z in profile),
                self.default_span_m if span is None else span,
                along,
                material,
                key,
                purchase,
                source_url,
                geometry_status,
            )
        )

    def rectangle(self, name, x0, x1, z0, z1, material, key, **kwargs):
        if x1 <= x0 or z1 <= z0:
            raise ValueError(f"nonpositive catalog installation part {name}")
        self.section(name, ((x0, z0), (x1, z0), (x1, z1), (x0, z1)), material, key, **kwargs)
