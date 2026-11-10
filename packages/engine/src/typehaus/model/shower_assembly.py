"""Shower setout in the fixture frame; product estimates never become exact ports."""

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.enums import Service
from typehaus.model.placeables import PortCertainty, ServicePort
from typehaus.quantities import Length, inch, m


class ShowerValveDimensions(HausModel):
    """R10000 envelope estimates, separate from the published stringer requirement."""

    half_inlet_spacing: Length = inch(2)
    inlet_depth: Length = inch(1.75)
    stringer_setback: Length = inch(2.75)
    certainty: PortCertainty = PortCertainty.APPROXIMATE
    source: str = "Delta DSP-B-R10000 Rev L (scaled hubs); M&I 50353 Rev O p.3 step 1B (stringer)"


class ShowerComponent(HausModel):
    name: str
    kind: Literal["control", "temperature", "volume", "diverter",
                  "head", "handheld", "spout", "outlet"]
    # Offset along the user's left and above the finished-face valve station.
    lateral_offset: Length = m(0)
    vertical_offset: Length = m(0)
    product_ref: str | None = None
    connection: str = "valve"
    relative_to_connection: bool = False


class ShowerValvePocket(HausModel):
    """House recess behind continuous backer; foil must return around its perimeter."""

    wall_ref: str
    width: Length = inch(12)
    height: Length = inch(10)
    layer_names: tuple[str, ...] = ("liner-furring", "foil-polyiso")


class ShowerAssemblySpec(HausModel):
    """A finished-face valve station, measured from fixture base, with +normal into wall.

    Components describe geometry only: purchasing remains on FixtureType/product packages.
    Head mounting height is measured from the standing surface, independent of surround.
    """

    valve_face: tuple[Length, Length, Length]
    wall_direction: tuple[float, float]
    standing_surface_height: Length = m(0)
    head_mount_height: Length = inch(78)
    finish: Literal["chrome", "brushed-nickel"] = "brushed-nickel"
    valve_product_ref: str = "PROD-DELTA-R10000-UNBX"
    valve_dimensions: ShowerValveDimensions = ShowerValveDimensions()
    components: tuple[ShowerComponent, ...]
    valve_pocket: ShowerValvePocket | None = None

    @model_validator(mode="after")
    def validate_connections(self):
        if self.wall_direction not in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            raise ValueError("shower wall direction must be a cardinal unit vector")
        names = [component.name for component in self.components]
        if len(set(names)) != len(names) or "valve" in names:
            raise ValueError("shower component names must be unique; valve is reserved")
        for component in self.components:
            if (component.connection not in (*names, "valve")
                    or component.connection == component.name):
                raise ValueError(f"invalid shower component connection: {component.name}")
        parents = {component.name: component.connection for component in self.components}
        for name in names:
            seen = set()
            while name != "valve":
                if name in seen:
                    raise ValueError("cyclic shower component connections")
                seen.add(name)
                name = parents[name]
        return self

    def point(self, *, lateral: float = 0, depth: float = 0,
              vertical: float = 0) -> tuple[float, float, float]:
        """Metres; positive lateral is user's left, positive depth enters the wall."""
        x, y, z = (value.meters for value in self.valve_face)
        nx, ny = self.wall_direction
        return x - ny * lateral + nx * depth, y + nx * lateral + ny * depth, z + vertical

    def component_point(self, component: ShowerComponent) -> tuple[float, float, float]:
        vertical = (self.standing_surface_height.meters + self.head_mount_height.meters
                    - self.valve_face[2].meters if component.kind == "head"
                    else component.vertical_offset.meters)
        point = self.point(lateral=component.lateral_offset.meters, vertical=vertical)
        if component.relative_to_connection and component.connection != "valve":
            parent = next(item for item in self.components if item.name == component.connection)
            parent_point = self.component_point(parent)
            return tuple(a + b - c for a, b, c in
                         zip(point, parent_point, self.point(), strict=True))
        return point

    def inlet_ports(self) -> tuple[ServicePort, ...]:
        dimensions = self.valve_dimensions
        nx, ny = self.wall_direction
        return tuple(ServicePort(
            tag=tag, service=service,
            position=tuple(m(value) for value in self.point(
                lateral=side * dimensions.half_inlet_spacing.meters,
                depth=dimensions.inlet_depth.meters)),
            direction=(-side * ny, side * nx, 0), connection_size=inch(0.5),
            certainty=dimensions.certainty, notes=dimensions.source,
        ) for tag, service, side in (("VALVE-HOT", Service.WATER_HOT, 1),
                                     ("VALVE-COLD", Service.WATER_COLD, -1)))
