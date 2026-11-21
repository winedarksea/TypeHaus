"""Slab-on-grade and concrete decks: ``Slab`` and its edge ``SlabThermalBreak`` (→ 11 §Floors).

Split from ``model/floors.py``, which re-exports both.
"""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from typehaus.model.assembly import Layer
from typehaus.model.base import Element, HausModel
from typehaus.model.rebar import ReinforcementSpec
from typehaus.model.refs import PublishedSpan
from typehaus.model.registry import register_element
from typehaus.model.slab_fall import DrainDish, SlabFall
from typehaus.quantities import Length, Point2D


class SlabThermalBreak(HausModel):
    """Vertical rigid-insulation break between a slab edge and whatever abuts it
    (stem wall, foundation wall) — the thermal cut that stops the slab conducting
    straight into the frost-depth concrete. Minimal by design: a material, its
    horizontal ``thickness`` in the joint, and how far ``depth`` runs down the slab
    edge (None = the slab's full thickness)."""

    material_ref: str
    thickness: Length  # horizontal insulation thickness in the edge joint
    depth: Length | None = None  # vertical extent down the slab edge; None = full slab
    #: The board's published compressive rating and the sheet it is read off — the
    #: ``IsolationBoard`` vocabulary. Unstated, a thrust through the edge is graded at the
    #: lowest ASTM C578 type of ``material_ref`` (``thermal_break_board.rated``).
    psi: float | None = None
    modulus_psi: float | None = None
    modulus_estimated: bool = False
    source: str | None = None
    #: The sheet's sustained-load rule as a fraction of ``psi`` (Owens Corning: dead load
    #: <= 1/3). Graded beside a thrust row as its own limit state (free body §11k).
    sustained_load_fraction: float | None = None

    @model_validator(mode="after")
    def _rating_names_its_sheet(self) -> SlabThermalBreak:
        if (self.psi is not None or self.modulus_psi is not None) and not self.source:
            raise ValueError("SlabThermalBreak: a psi or modulus_psi needs the `source` it "
                             "is read off")
        return self


@register_element
class Slab(Element):
    """Slab-on-grade or structural concrete deck (instead of a FloorSystem).

    Like a FloorSystem it may own FloorOpenings (the catlin main deck is a 9"
    slab with a stair hole, → 30 WP3.1)."""

    outline: tuple[Point2D, ...]
    thickness: Length
    assembly: str | None = None
    #: The steel this pour actually contains. Unset means this model does not say — which
    #: for a footing is the ordinary case and a legal one: ACI 318-19 §14.1.4 permits PLAIN
    #: concrete in a footing (unlike §14.1.5 for a column), so a missing spec grades as plain
    #: and reports OK or OVER rather than INCOMPLETE.
    reinforcement: ReinforcementSpec | None = None
    openings: tuple[str, ...] = ()  # FloorOpening tags
    # Which side of the storey datum (= top of floor structure) this slab occupies.
    # "structure" — the slab *is* the floor structure, so it hangs its thickness below the
    # datum. This is the default and covers every slab-on-grade and structural concrete deck.
    # "walking_surface" — decking laid over a FloorSystem whose joists already top out at the
    # datum, so it rides on top instead, exactly like that FloorSystem's own subfloor sheet.
    # Authoring this explicitly rather than inferring it from a shared footprint keeps two
    # coincidentally-congruent elements (a patio slab under a deck, say) from silently
    # swapping conventions.
    datum: Literal["structure", "walking_surface"] = "structure"
    # Absolute top-of-slab elevation, in the project frame, when this slab does not sit on
    # its storey's datum at all — a garage slab left at grade while the house floor above it
    # stays at 0'-0", say. Mirrors ``FoundationWall.top_elevation``. When set it wins over
    # the storey datum outright and ``datum`` no longer applies: the slab hangs its
    # thickness below this elevation. Leave it None (the norm) and the storey datum plus
    # ``datum`` decide. Authoring it is what lets a slab be filed on the storey it belongs
    # to rather than on whichever storey happens to sit at its elevation.
    top_elevation: Length | None = None
    # Slab-on-grade only: rigid-insulation edge break against the abutting stem/foundation
    # wall. None = slab edge pours directly against the concrete it meets.
    perimeter_thermal_break: SlabThermalBreak | None = None
    # This slab's own top face is the finished floor wherever a room sits on it — a
    # polished or sealed cap, not a deck waiting for a covering. Where set, `resolve/rooms.py`
    # intersects this outline with each room's clear face and emits the result as a
    # ResolvedFinishZone, so the room's own `floor_finish` stays the FIELD finish and the
    # concrete bills, draws and prices as its own area. Leave it None (the norm) and a slab
    # is structure only. Not on FloorSystem: a joisted deck's top is a subfloor sheet, and
    # what goes over it is the room's decision, never the deck's.
    floor_finish: str | None = None
    # The ceiling hung under this slab, room side first, meaningful only where a room sits
    # under it (``datum == "structure"``): a slab-on-grade with no occupied space below
    # authors none. Same convention as ``FloorSystem.ceiling_below``.
    ceiling_below: tuple[Layer, ...] = ()
    # The published table row that answers this deck's span, where one does. A
    # manufacturer's table is a PRESCRIPTIVE read — a reviewer opens the document and the
    # question is closed — so authoring one here takes the requirement out of the
    # engineering register rather than into it. See ``model/refs.PublishedSpan``, which
    # carries the drift guards that stop a quotation outliving the model it was read for,
    # and ``checks/structural/slab_span.py``, which grades it. Only a SUSPENDED slab
    # (a room underneath) spans anything; a slab-on-grade authors none.
    published_span: PublishedSpan | None = None
    # What this sheet IS: a cast ``pour``, a laid ``deck``, a wall-carried ``platform`` or a
    # ground ``band`` (sod, frost-wing foam). ``None`` derives it (``resolve/slab_kind.py``);
    # authored, ``integrity.slab_kind_matches_assembly`` holds it to the derivation.
    kind: Literal["pour", "deck", "platform", "band"] | None = None
    # A pour that falls to drain (``model/slab_fall.py``): its plane, constant thickness;
    # ``top_elevation`` is its low edge.
    fall: SlabFall | None = None
    # Local dishes to floor drains inside a level rim (``model/slab_fall.DrainDish``, #148).
    drain_dishes: tuple[DrainDish, ...] = ()

    @model_validator(mode="after")
    def _fall_needs_a_pour_at_an_elevation(self) -> Slab:
        if self.fall is not None and (self.kind != "pour" or self.top_elevation is None):
            raise ValueError(f"{self.tag}: a fall needs kind=\"pour\" and a top_elevation")
        if self.drain_dishes and self.kind != "pour":
            raise ValueError(f"{self.tag}: a drain dish needs kind=\"pour\"")
        if self.drain_dishes and self.fall is not None:
            raise ValueError(f"{self.tag}: a fall and a drain dish on one slab are not supported")
        return self
