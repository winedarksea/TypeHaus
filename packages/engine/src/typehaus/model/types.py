"""Library types: DoorType, WindowType, FurnitureType, FixtureType (→ 10 §Element model)."""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.enums import Service
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length, UFactor


class DoorType(HausModel):
    """A door product type. Drives schedules and energy checks."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    operation: str = "swing"  # swing | double_swing | slide | pocket | bifold
    exterior: bool = False
    source: str | None = None


class WindowType(HausModel):
    """A window product type. Carries SHGC and VT (#41) for the M5 load estimator."""

    tag: str
    width: Length
    height: Length
    u_factor: UFactor | None = None
    shgc: float | None = None  # solar heat gain coefficient
    vt: float | None = None  # visible transmittance
    operation: str = "fixed"  # fixed | casement | double_hung | slider | awning
    source: str | None = None


class MeshRef(HausModel):
    """Reference to a .glb sidecar under the house dir (written by `haus import`, #49)."""

    path: str


class FurnitureType(HausModel):
    """An IKEA-scale design-reference type (#49). Footprint/height derived from mesh."""

    tag: str
    name: str
    footprint: tuple[Length, Length]  # (width, depth)
    height: Length
    storage: bool = False
    clearance: tuple[Length, Length, Length, Length] | None = None  # front/back/L/R
    mesh: MeshRef | None = None
    source: str | None = None


class FixtureType(HausModel):
    """A plumbing/equipment fixture type — needs services, has clearances (M3)."""

    tag: str
    name: str
    footprint: tuple[Length, Length]
    height: Length
    needs: frozenset[Service] = frozenset()
    clearance: tuple[Length, Length, Length, Length] | None = None
    source: str | None = None


for _name, _obj in (
    ("DoorType", DoorType),
    ("WindowType", WindowType),
    ("FurnitureType", FurnitureType),
    ("FixtureType", FixtureType),
    ("MeshRef", MeshRef),
):
    register_constructor(_name, _obj)
