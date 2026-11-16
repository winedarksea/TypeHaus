"""Air-side product rows: the duct a run is made of, and the part of a terminal in the cavity.

Split out of ``model/types.py`` for size; ``types`` re-exports both names.
"""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class DuctProductType(HausModel):
    """The duct itself as a purchased product: what a run is made of, and how it resists.

    A ``DuctRun`` states a *material* and a *section* and nothing else about the pipe —
    which is right, because those are what an estimator orders on and are exactly what
    ``prices.toml``'s ``[ducts]`` qualifies its rows by. This row is the value, matched by
    key, the same join the price uses; a run whose key names no row is UNKNOWN, never given
    a default.

    **Two sections, two keys.**

    * ``round`` (the default) matches ``(material, nominal_diameter)`` and carries the
      friction physics a pressure calculation needs — the **bore** (4" snap-lock is 4.0"
      inside; 4" semi-rigid is not) and the **roughness**. Darcy-Weisbach is the engine's
      (``resolve/duct_sizing.py``); the coefficients are the house's, read off ASHRAE.
    * ``rectangular`` is a **gauge band**: a run of this ``material`` matches the row with
      the smallest ``max_side`` at or above its larger side (IRC Table M1601.1.1 is written
      that way). It carries the sheet ``gauge`` and ``thickness`` the schedule prints, and
      optionally the friction pair: ``roughness_m`` (ε) and ``bend_equivalent_length``.
      ``mep.erv_static_budget`` grades a rectangular run in the ventilator's network at
      its Huebscher equivalent diameter and this ε; a row without ε is a gap by (material, W x D).
    """

    tag: str
    name: str
    #: Matches ``DuctRun.material`` exactly (``"galvanized"``, ``"semi_rigid"``, ``"flex"``).
    material: str
    section: Literal["round", "rectangular"] = "round"
    #: Round: matches ``DuctRun.diameter`` — the size the run is drawn and ordered at.
    nominal_diameter: Length | None = None
    #: Round: the actual inside diameter. Friction goes as roughly the fifth power of it, so
    #: the nominal size is not close enough to stand in.
    bore_diameter: Length | None = None
    #: Absolute roughness ε, in metres, as the authoring note reads it off ASHRAE (rectangular:
    #: optional, see above).
    roughness_m: float | None = None
    #: Round: the most air the product is used for at the velocity the house designs to.
    #: Advisory: ``mep.erv_static_budget`` grades each radial's ``design_cfm`` against it.
    max_cfm: float | None = None
    #: Equivalent length of one 90-degree bend — authored, not derived (rectangular: optional).
    bend_equivalent_length: Length | None = None
    #: Rectangular: the largest side this gauge band covers.
    max_side: Length | None = None
    #: Sheet gauge as ordered (e.g. 26), and its nominal thickness as the code table states.
    gauge: int | None = None
    thickness: Length | None = None
    product_ref: str | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _section_fields(self) -> DuctProductType:
        if self.section == "round":
            missing = [name for name in ("nominal_diameter", "bore_diameter", "roughness_m")
                       if getattr(self, name) is None]
            if missing:
                raise ValueError(f"{self.tag}: a round duct row needs {', '.join(missing)}")
        elif self.max_side is None or self.gauge is None:
            raise ValueError(f"{self.tag}: a rectangular duct row is a gauge band and needs "
                             "max_side and gauge")
        return self


class TerminalNeckComponent(HausModel):
    """A ceiling assembly part; offset is its centre in plan and its bottom above the face.

    Clearance-only boxes describe blade travel or service space and are never emitted or
    purchased. Product quantities belong to RegisterType.parts, not to these fit envelopes.
    """

    tag: str
    width: Length
    height: Length
    depth: Length
    offset: tuple[Length, Length, Length]
    part: str
    product_ref: str | None = None
    #: Actuators and service covers are solid envelopes, rather than air passages.
    body_style: Literal["shell", "solid"] = "shell"
    clearance_only: bool = False
    receives_duct: bool = False

    @model_validator(mode="after")
    def _positive_dimensions(self) -> TerminalNeckComponent:
        if min(self.width.meters, self.height.meters, self.depth.meters) <= 0:
            raise ValueError("terminal component dimensions must be positive")
        return self


class TerminalNeckInlet(HausModel):
    """Inlet centre in ceiling-plan or wall-back coordinates; normal points to the duct.

    A round wall inlet beyond the neck box's depth draws a projecting metal collar
    back to the box; its projection is not an extension of the rectangular envelope.
    """

    # Ceiling: local plan XY and height above face. Wall: across, into host, height
    # above face centre; the origin is the grille's back face.
    position: tuple[Length, Length, Length]
    section: Literal["rectangular", "round"] = "rectangular"
    width: Length
    height: Length
    normal: tuple[float, float]
    #: Level approach inside the authored final leg, so a pitched offset ends square.
    straight_length: Length | None = None

    @model_validator(mode="after")
    def _valid_inlet(self) -> TerminalNeckInlet:
        if self.section == "round" and abs(self.width.meters - self.height.meters) > 1e-6:
            raise ValueError("round terminal inlet width and height must match its diameter")
        if self.straight_length is not None and self.straight_length.meters <= 0:
            raise ValueError("terminal inlet straight length must be positive")
        if self.width.meters <= 0 or self.height.meters <= 0:
            raise ValueError("terminal inlet dimensions must be positive")
        if abs(sum(v * v for v in self.normal) - 1.0) > 1e-6:
            raise ValueError("terminal inlet normal must be a unit vector")
        return self


class TerminalNeck(HausModel):
    """The part of an air terminal that is IN the cavity: boot, valve spigot, inline damper.

    A ``RegisterType``'s ``footprint``/``height`` is the FACE — what shows in the room — and
    a face is an inch deep. Behind it a 6" side boot fills most of a 2x6 bay, a disc valve's
    collar reaches 2" up past the board, and a motorised damper hangs its actuator off the
    side. ``resolve/terminal_necks.py`` draws this box behind the face (up from a ceiling
    face, down from a floor face, into the wall from a wall face) and
    ``mep.terminal_neck_fit`` grades it against the framing and the other runs.

    ``width`` lies along the face's own x, ``height`` along the face's other dimension, and
    ``depth`` is the reach into the cavity from the face plane.
    """

    width: Length
    height: Length
    depth: Length
    #: What occupies the box, as a reader would name it ("6in stamped side boot").
    part: str
    product_ref: str | None = None

    #: Physical drawing shape; None retains the legacy box. Fit envelopes stay rectangular.
    section: Literal["round", "rectangular"] | None = None
    #: Multipart geometry currently uses ceiling-face coordinates only. Legacy single-box
    #: necks retain their wall, ceiling and floor placement conventions.
    components: tuple[TerminalNeckComponent, ...] = ()
    inlet: TerminalNeckInlet | None = None
    #: The box is only the damper behind the face: the duct's ``boot`` part is drawn
    #: between the run and the box's back (``resolve/duct_part_solids``).
    separate_boot: bool = False
    #: The face the duct joins the neck on (None = today's: the box's back). A WALL neck
    #: entered ``bottom`` or ``top`` is a stack head: the run arrives vertically in the cavity.
    entry: Literal["back", "bottom", "top", "left", "right"] | None = None

    @model_validator(mode="after")
    def _unique_components(self) -> TerminalNeck:
        if self.section == "round" and abs(self.width.meters - self.height.meters) > 1e-6:
            raise ValueError("round terminal neck width and height must match")
        tags = [component.tag for component in self.components]
        if len(tags) != len(set(tags)):
            raise ValueError("terminal neck component tags must be unique")
        return self
