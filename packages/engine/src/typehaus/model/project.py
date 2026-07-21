"""Project / Site / Building / Storey containers (→ 10 §Element model)."""

from __future__ import annotations

import uuid

from typehaus.model.base import Element, HausModel
from typehaus.model.refs import FaceRef, face
from typehaus.model.registry import register_constructor, register_element
from typehaus.model.site import SetbackSpec, SpotElevation, UtilityLine
from typehaus.quantities import Angle, Length, Point2D, Temperature, deg


class Site(HausModel):
    """Georeferencing + design-day boundary conditions (#11, #41)."""

    lat: float
    lon: float
    elevation: Length
    crs: str = "EPSG:26915"  # UTM 15N (Minnesota)
    true_north: Angle = deg(0)  # project-north deviation from true north (→ 02)
    grade: Length | None = None
    parcel_refs: tuple[str, ...] = ()
    design_temp_heating: Temperature | None = None  # 99% heating design temp
    design_temp_cooling: Temperature | None = None  # 1% cooling design temp
    parcel: tuple[Point2D, ...] = ()  # closed CCW ring, plan frame
    setbacks: tuple[SetbackSpec, ...] = ()
    spot_elevations: tuple[SpotElevation, ...] = ()
    utilities: tuple[UtilityLine, ...] = ()


@register_element
class Storey(Element):
    """A building level. Resolves in the shared project-north plan frame (→ 02)."""

    elevation: Length
    default_ceiling_height: Length
    vertical_datum: FaceRef = face("sheathing-ext")  # #43 default


class Building(HausModel):
    name: str = "Building"


class Project(HausModel):
    """The plan root. ``project_uuid`` is generated once by ``haus new`` (→ 10 §IDs)."""

    name: str
    project_uuid: uuid.UUID
    site: Site
    building: Building = Building()
    format_version: int = 1
    requires_engine: str = ">=0.1,<0.2"
    active_code_profile: str | None = None


for _name, _obj in (
    ("Site", Site),
    ("Storey", Storey),
    ("Building", Building),
    ("Project", Project),
    ("face", face),
    ("FaceRef", FaceRef),
):
    register_constructor(_name, _obj)
