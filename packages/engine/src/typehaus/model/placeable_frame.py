"""A generated model's pose when its mounting surface is inclined."""

from dataclasses import dataclass

Point3D = tuple[float, float, float]


@dataclass(frozen=True)
class PlaceableFrame:
    origin: Point3D
    up: Point3D

    def direction(self, x: float, y: float, z: float) -> Point3D:
        """Rotate local vertical to the mounting normal by the shortest arc."""
        up_x, up_y, up_z = self.up
        horizontal_component = x * up_x + y * up_y
        axial_component = z - horizontal_component / (1.0 + up_z)
        return (x + up_x * axial_component, y + up_y * axial_component,
                z * up_z - horizontal_component)

    def point(self, x: float, y: float, z: float) -> Point3D:
        dx, dy, dz = self.direction(x, y, z)
        return self.origin[0] + dx, self.origin[1] + dy, self.origin[2] + dz
