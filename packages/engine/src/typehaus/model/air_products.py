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
      no friction: nothing in the engine computes a rectangular duct's pressure drop.
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
    #: Round: absolute roughness ε, in metres, as the authoring note reads it off ASHRAE.
    roughness_m: float | None = None
    #: Round: the most air the product is used for at the velocity the house designs to.
    #: Advisory: ``mep.erv_static_budget`` grades each radial's ``design_cfm`` against it.
    max_cfm: float | None = None
    #: Round: equivalent length of one 90-degree bend — authored, not derived.
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
