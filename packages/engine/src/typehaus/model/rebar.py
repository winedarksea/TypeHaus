"""ASTM A615 deformed bar sizes — pure data, imported by both ``engineering/`` and ``takeoff/``.

This table is the one place the engine states what a ``#5`` *is*. It lives in ``model/``
rather than in either consumer because both need it and neither may import the other:
``takeoff/`` billing a bar has to weigh it, ``engineering/`` sizing one has to know its area
and diameter, and a BOM that reached into ``engineering/`` for the number would move every
time a calc's ``BASIS_VERSION`` moved. Quantities are the product; a record is not.

Weights are the nominal ASTM A615 unit masses (lb/ft), which is what steel is bought and
billed by. They are the *bare* bar: a galvanizing coating adds roughly 0.5-1% of mass and
is inside the coated bar's $/lb rate, not a separate quantity.
"""

from __future__ import annotations

from typing import Literal, NamedTuple

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class Bar(NamedTuple):
    """One ASTM A615 bar size: area in², nominal diameter in, unit weight lb/ft."""

    area_in2: float
    diameter_in: float
    weight_plf: float


#: Keyed on the bar designation number (``#5`` -> ``5``). ASTM A615/A615M Table 1.
BARS: dict[int, Bar] = {
    3: Bar(0.11, 0.375, 0.376),
    4: Bar(0.20, 0.500, 0.668),
    5: Bar(0.31, 0.625, 1.043),
    6: Bar(0.44, 0.750, 1.502),
    7: Bar(0.60, 0.875, 2.044),
    8: Bar(0.79, 1.000, 2.670),
    9: Bar(1.00, 1.128, 3.400),
    10: Bar(1.27, 1.270, 4.303),
    11: Bar(1.56, 1.410, 5.313),
}


def bar(number: int) -> Bar | None:
    """``BARS`` lookup that answers ``None`` rather than raising on an unknown size.

    Every caller here reads a bar number out of house-authored text or an authored spec, so
    an unrecognised size is a modelling fact to report, not an engine bug to crash on.
    """
    return BARS.get(number)


#: The bar designations this engine knows, ascending — for a finding that has to say so.
KNOWN_BARS: tuple[int, ...] = tuple(sorted(BARS))


class BarSpec(HausModel):
    """One role of bar in a cage or a mat: what size, how it is laid out, how it is coated.

    ``spacing`` and ``count`` are the two shapes reinforcement comes in and they are not
    interchangeable. A **wall or a slab** is reinforced by a bar every so often — the
    quantity is a spacing, and the member's length decides how many there are. A **column
    or a pier cage** is reinforced by a stated number of bars around a circle — the quantity
    is a count, and the member's length decides nothing. Authoring a spacing where a count
    belongs turns "(4) #5 vertical" into a per-foot rate; authoring a count where a spacing
    belongs makes a 40'-0" wall and a 4'-0" one carry the same steel. Exactly one of the two
    is required, and ``integrity`` says so rather than guessing.

    ``role`` is what this bar DOES, because that is what a limit state asks for: flexure
    wants the bar on the tension face and nothing else, and a tie is not a flexural bar at
    any spacing. ``dowels`` is the lap into the pour below, which is a length of bar the BOM
    must carry and no limit state grades.
    """

    role: Literal["vertical", "horizontal", "top-x", "top-y", "bottom-x", "bottom-y",
                  "ties", "dowels"]
    #: Bar designation number: 5 for a ``#5``. Unknown sizes report rather than crash.
    bar: int
    #: Centre-to-centre spacing — the wall-and-slab shape. Exclusive with ``count``.
    spacing: Length | None = None
    #: How many bars — the cage shape. Exclusive with ``spacing``.
    count: int | None = None
    #: How many layers of this role, e.g. a mat top AND bottom authored as one row. The
    #: quantity multiplies; the flexural lever arm does not, which is why a two-layer mat
    #: still gets its ``d`` from the cover and not from this.
    layers: int = 1
    #: Overrides the pour's ``ConcreteSpec.bar_coating`` for this role alone. Rare, and real:
    #: a cage whose ties are black inside a galvanized vertical bar is a false economy, but
    #: a dowel lapped into a black-bar pour below is not.
    coating: str | None = None
    #: Prose the struct cannot hold — a hook, a stagger, a "top of footing to 6\" below
    #: grade". For the drawing; nothing grades it.
    note: str | None = None


class ReinforcementSpec(HausModel):
    """The steel a pour actually contains — authored on the ELEMENT, not on its type.

    On the element because a stem's steel follows *its* height and a footing's follows *its*
    width: two walls sharing one ``Assembly`` do not share one bar schedule. The mix is the
    opposite — one ticket from one plant — which is why :class:`~typehaus.model.assembly.
    ConcreteSpec` lives on the assembly's layer and this lives here. The engineering records
    key on element tags for the same reason.

    ``cover`` here overrides the pour's ``ConcreteSpec.cover`` for this element only, and
    exists because the two faces of a retaining stem genuinely differ: the earth face is
    cast against a form with spacers and the exposed face is not, and ACI's 3" is written
    for concrete cast against *earth*. A single number per element is the honest limit of
    what this schema says; where the two faces need different cover, that is a drawing note
    and a ``BarSpec.note``, not a number this type can carry.

    **This does not replace the free-text ``vertical_reinforcement`` fields.** Both may be
    authored; the struct governs every graded number and the string stays for the drawing.
    ``integrity.reinforcement_spec_agrees`` raises an ERROR where both exist and disagree,
    which is what makes keeping both safe rather than merely convenient.
    """

    bars: tuple[BarSpec, ...]
    cover: Length | None = None
    #: ACI 318-19 §25.5.2.1 splice class. ``"B"`` is the ordinary answer wherever every bar
    #: is spliced at one section, which a column base always is.
    lap_class: Literal["A", "B"] | None = None
    source: str | None = None


for _name, _obj in (("BarSpec", BarSpec), ("ReinforcementSpec", ReinforcementSpec)):
    register_constructor(_name, _obj)
