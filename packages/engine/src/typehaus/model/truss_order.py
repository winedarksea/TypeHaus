"""What a truss ORDER asks for: reactions the house specifies, loads a floor truss carries.

A fabricator's sealed drawing publishes reactions (``PublishedReaction``); this module is the
other half, the criteria the order states BEFORE any drawing exists. The supporting structure
is graded against them now ("supporting structure closed"); the supplier's design is checked
against them when it arrives ("component confirmed"), and until then that status is open.
"""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class SpecifiedReaction(HausModel):
    """One bearing's reaction the order SPECIFIES, never a supplier's published number.

    ``Roof.specified_reactions`` carries these. The heel connector named is graded against
    ``uplift_lb`` from the hardware catalog, so the allowable is stated once, in the library.
    """

    #: A truss key (``truss-001``) or ``"*"`` for every truss of the roof.
    member: str
    #: The wall or beam tag the heel bears on.
    bearing: str
    #: Maximum net uplift at the heel, ASD (0.6 W - 0.6 D), pounds.
    uplift_lb: float
    #: Where the number comes from, in the house's own words.
    basis: str
    #: The heel connector's catalog model.
    connector: str | None = None
    #: The truss's species (the supplier's; the order states it). The connector's capacity
    #: column is the WEAKER member's, so an SPF truss on an SP header reads the SPF column.
    truss_species: str | None = None
    #: The connector's catalog row for ``truss_species`` with every truss-side nail landing in
    #: the truss (pounds): what ``uplift_lb`` rests on. Never above the catalog's own value.
    capacity_lb: float | None = None
    #: The catalog's reduced row when fewer nails land in the truss (Simpson C-C-2021 p.277
    #: fn. 14: three nails into a 2x4 bottom chord), pounds. Until ``heel_condition`` is
    #: confirmed the heel is graded at THIS row against ``design_uplift_lb``.
    reduced_capacity_lb: float | None = None
    #: The net design uplift at the heel the house derives, pounds (the load the reduced row
    #: has to carry while the condition is unconfirmed).
    design_uplift_lb: float | None = None
    #: What the supplier's drawing must show for ``capacity_lb`` to stand.
    heel_condition: str = ""
    #: The dead load on the bottom chord the order carries here, psf (a ceiling), if any.
    bottom_chord_dead_psf: float | None = None
    #: Deflection limits the order states, e.g. ``("L/240 snow", "L/180 total")``.
    deflection: tuple[str, ...] = ()


class TrussAppliedLoad(HausModel):
    """A load beyond the published row's uniform one, on one truss line of a floor deck.

    ``load_lb`` is the TOTAL over ``x0``..``x1`` along the span (equal stations are a point
    load), carried by the ``plies`` trusses of the line (a doubled pair is two).
    """

    #: The line's station across the span (project plan axis perpendicular to the trusses).
    line: Length
    x0: Length
    x1: Length
    load_lb: float
    source: str
    plies: int = Field(default=1, ge=1)


class TrussOrder(HausModel):
    """A floor-truss order's loads, bearing centres and requests.

    ``bearings`` are the two bearing centres along the span (project plan axis along the
    trusses): the span the point-load statics read. ``live_psf`` / ``dead_psf`` are the uniform
    loads the order is for (the published row's own dead column may be higher).
    ``max_reaction_lb`` is the maker's published maximum reaction at the bearing used, where
    one is printed. ``requests`` are lines the order prints verbatim (what to confirm).
    """

    bearings: tuple[Length, Length]
    live_psf: float
    dead_psf: float
    loads: tuple[TrussAppliedLoad, ...] = ()
    max_reaction_lb: float | None = None
    deflection: tuple[str, ...] = ()
    requests: tuple[str, ...] = ()
