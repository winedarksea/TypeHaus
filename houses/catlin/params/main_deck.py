"""The basement's ceiling — the main floor's structure, mixed wood and concrete.

Until 2026-08-21 this was one element: ``SL-M-DECK``, a 1,233 SF x 9" cast suspended
concrete deck. It was the most expensive line in the model (34.26 cy on shored plywood
formwork, whose commercial shoring mobilisation floor alone is $25-40k — see
``plans/cost-options.md``), and it forced eight interior 12" concrete cross walls with
strip footings and drain tile under them, because it was designed to span between them.

Two facts change that. Wood I-joists already cross the same 18' bays on both storeys above
(``FS-SECOND``, ``FS-ATTIC``), and EPS stay-in-place deck forms — LiteDeck, BuildDeck,
Insul-Deck — span 18' one-way with far less concrete and no shored formwork at all. Tune
the EPS deck's total depth to the wood floor's and the two become interchangeable bay by
bay: same soffit plane, same finished-floor plane, same 18' span to the x=18' bearing line.
Concrete then goes only where it is actually wanted.

    WOOD BAY                              EPS DECK BAY
      finish (LVP / tile)                   finish (or the cap itself)
      3/4" plywood subfloor      0'-0" FFE  4 5/8" concrete cap
      11 7/8" I-joist @ 16" o.c.            8" EPS form, ribs @ 24" o.c.
      ---------------- 12 5/8" ------------------------------------------
      5/8" gypsum on joists                 5/8" gypsum on the steel rib
      ---------------- 13 1/4" to the basement ceiling -------------------

Both planes land together. Against the old 9" slab the soffit drops 4 1/4", which is why
the house rose 4" the same day (``params/foundations.py::SITE_GRADE``, and the basement
storey with it) and the basement kept its headroom at ~8'-2 3/4".

**Why this is a params module and not ``plan/storeys/main.py``.** The depth wants to be one
constant, so that swapping the 8"+4 5/8" build-up for the 10"+3" one — same depth class,
~21% less concrete, R-31 — is a one-line edit. Editable-dialect files may hold only
literals and cannot import from ``params/``, so a file that holds the arithmetic cannot be
the file the UI writes back to. The elements here are not UI-movable, so nothing is lost.

**Why two FloorSystems and not one.** ``FloorSystem.outline`` scopes only the
*perpendicular* extent; span boundaries come from the bearing refs' axis midpoints
(``resolve/floors.py``). One system naming all three bearing lines would frame joists
across the full 36' of the house, straight through the concrete band. So the west half and
the east half's wood bay are separate systems, each naming only the two lines it spans.

**Bearing-ref trap.** Do not name ``W-B-CS`` as a bearing ref here. It carries
``alignment=face("concrete-ext", offset=inch(-6))``, and an alignment offset can put its
axis coordinate at 17.5' or 18.5' rather than 18.0' — which injects a third span boundary
and produces a bay of stub joists. ``W-B-CS2`` and ``W-B-CN`` sit on the x=18' node line
and are the safe refs.

Quantities, from the manufacturers' published tables:

* BuildDeck's 8" form spans 20' clear at a 4" cap (4,000 psi, 60 ksi rebar, 15 psf dead +
  40 psf live). This span is 18'-0". R-25 through the finished section.
* Concrete at 8" form + 4 5/8" cap is 0.01774 cy/SF, so the 414 SF band is 7.35 cy —
  against 34.26 cy for the whole 9" slab it replaces.

Sources: LiteDeck SRS installation manual (liteform.com), BuildDeck brochure
(buildblock.com), Insul-Deck technical summary, ICF Builder's foam-decking comparison.
"""

from typehaus import (
    DeckLayer,
    FloorSystem,
    JoistSpec,
    Point2D,
    Slab,
    ft,
    inch,
    pt,
)

# --- the one number the whole exercise turns on -----------------------------------
#
# 8" + 4 5/8" = 12 5/8", which is FS-SECOND's 11 7/8" I-joist plus its 3/4" plywood. The
# documented alternative is EPS_FORM_DEPTH = inch(10.0) / EPS_CAP = inch(3.0): 13" exactly,
# 3/8" proud of the wood bays, ~21% less concrete (0.01396 cy/SF) and R-31. Changing these
# two lines means changing CATLIN_DECK_EPS_INT's two structural layers to match —
# ``integrity.slab_thickness`` fails the build if they drift apart.
EPS_FORM_DEPTH = inch(8.0)      # BuildDeck / LiteDeck base section
EPS_CAP = inch(4.625)           # the cast structural topping
DECK_DEPTH = inch(EPS_FORM_DEPTH.inches + EPS_CAP.inches)

# The wood bays' build-up, matched to FS-SECOND so the two storeys frame alike.
_JOIST = "11.875 I-joist"
_JOIST_OC = inch(16)

# The concrete/wood boundary. Concrete keeps the east half north of y=13' — the dining
# radiant zone (FH-M-DINING, x 22'-11"..30'-11", y 13'-9"..21'-0") sits wholly inside it,
# with its thinset bed over the cured cap exactly as before. Everything else is wood.
# Re-apportioning the ceiling later is a matter of moving this one line and the two
# outlines it cuts.
#
# It is also a movement joint, and the finish has to say so: the two systems match in depth
# but not in stiffness, and an I-joist bay's 1/2" of live-load deflection against a slab that
# barely moves is a hinge under whatever runs across it. The detail — break the LVP, break
# the ceiling board, keep tile off the line entirely — is
# ``houses/catlin/notes/mixed_deck_movement_joint.md``. Nothing in the engine can bind it to
# geometry (a Transition needs a derived boundary condition and there is none for "two decks
# meet in plan"), which is recorded there and in plans/TODO.md.
_BAND_Y = ft(13)
_CENTRE_X = ft(18)
_HOUSE = ft(36)
_ZERO = ft(0)


def _rect(x0: object, y0: object, x1: object, y1: object) -> tuple[Point2D, ...]:
    return (pt(x0, y0), pt(x1, y0), pt(x1, y1), pt(x0, y1))


# The west half, wall to centre line, full 36' north-south. FO-M-STAIR lives in this bay
# and is a real framed opening now that the deck under it is joists rather than a pour.
WEST_FLOOR = FloorSystem(
    uid="CMFS01AAAA", tag="FS-M-WEST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-W2", "W-B-CS2")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
    # The basement's ceiling. R316.4 wants gypsum over the EPS in the concrete band; the
    # owner's decision was to drywall the whole ceiling rather than stop the board at the
    # boundary, which is also what retires the old "visible copper in the basement"
    # preference (houses/catlin/preferences.toml).
    ceiling_below=DeckLayer(material_ref="gwb", thickness=inch(0.625)),
    outline=_rect(_ZERO, _ZERO, _CENTRE_X, _HOUSE),
    openings=("FO-M-STAIR",),
    source="catlin main floor, west half — 11 7/8\" I-joists at 16\" o.c. spanning 18'-0\" "
           "east-west from W-B-W2 to the x=18' bearing line",
)

# The east half's wood bay: the gym's ceiling, south of the concrete band.
EAST_FLOOR = FloorSystem(
    uid="CMFS02AAAA", tag="FS-M-EAST",
    joists=JoistSpec(member=_JOIST, spacing=_JOIST_OC, direction="x",
                     bearing_refs=("W-B-CS2", "W-B-E1")),
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=inch(0.75)),
    ceiling_below=DeckLayer(material_ref="gwb", thickness=inch(0.625)),
    outline=_rect(_CENTRE_X, _ZERO, _HOUSE, _BAND_Y),
    source="catlin main floor, east half south of y=13' — same joists as FS-M-WEST, "
           "spanning 18'-0\" from the x=18' bearing line to W-B-E1",
)

# What is left of the concrete: 414 SF over the dining end. Same tag and same uid as the
# 1,233 SF slab it replaces, so the IFC GlobalId survives (decision #16).
DECK = Slab(
    uid="CMS501AAAA", tag="SL-M-DECK",
    outline=_rect(_CENTRE_X, _BAND_Y, _HOUSE, _HOUSE),
    thickness=DECK_DEPTH, assembly="CATLIN_DECK_EPS_INT",
)

MAIN_ELEMENTS = [WEST_FLOOR, EAST_FLOOR, DECK]
