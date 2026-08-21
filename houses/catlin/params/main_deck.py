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
      finish (LVP)                          the cap itself, polished
   +3/4" ------------- FINISHED FLOOR ---------------------------------
      3/4" plywood subfloor                 4 5/8" concrete cap
    0'-0" ------------- STOREY DATUM (top of joists) --------------------
      11 7/8" I-joist @ 16" o.c.            8" EPS form, ribs @ 24" o.c.
 -11 7/8" ------------- STRUCTURE BOTTOM ----------------------------------
      5/8" gypsum on joists                 1/2" steel rib + 5/8" gypsum
      -12 1/2" ceiling                      -13" ceiling  (the rib's 1/2" step)

**The datum is the top of joists, not the walking surface.** Walls bear there and the
subfloor rides above it, so a wood bay's finished floor is +3/4" while the datum is 0'-0".
That is why ``DECK`` carries an explicit ``top_elevation``: a ``datum="structure"`` slab
pins its TOP to the datum whatever its thickness, so the depth-matching arithmetic below —
which is right — never reached the elevation on its own. Until 2026-08-21 it did not, and
both planes resolved 3/4" low against a paragraph claiming they matched. They match now:
walking surface +3/4" on both, structure bottom -11 7/8" on both.

The one plane that does NOT match is the basement ceiling, and it cannot: the board screws
to the form's integral steel rib on the concrete side and straight to the joists on the
wood side, so the two gypsum faces sit 1/2" apart at the boundary. That is a real step in a
real ceiling, and ``notes/mixed_deck_movement_joint.md`` carries how it is trimmed.

Against the old 9" slab the soffit drops 3 1/2", which is why the house rose 4" the same
day (``params/foundations.py::SITE_GRADE``, and the basement storey with it) and the
basement kept its headroom — 8'-3" clear to the lower of the two ceiling planes.

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

from params.second_deck import _DEPTH as _JOIST_DEPTH
from params.second_deck import _SUBFLOOR

# --- the wood bay this deck has to match, top and bottom --------------------------
#
# The second floor's build-up, repeated on this storey. The depth and subfloor thickness
# are imported from ``params/second_deck.py`` rather than restated: since 2026-08-21 that
# deck is split truss/I-joist at x=18', and both members share this one depth precisely so
# the concrete band below can keep matching a single number instead of two. Everything
# below derives from them rather than restating them.
_JOIST = "11.875 I-joist"
_JOIST_OC = inch(16)

# The storey datum is the TOP OF JOISTS, not the walking surface — walls bear there and the
# subfloor rides above it (``Slab.datum``'s own docstring, and W-S-E2 starting at exactly
# 10'-0" on FS-SECOND's joist tops). So the finished floor of a wood bay is _SUBFLOOR
# *above* the datum, and anything claiming to share that plane has to be pinned there
# explicitly. ``plan/manifest.py`` takes the main storey's elevation from MAIN_DATUM, so
# the two cannot disagree.
MAIN_DATUM = ft(0)
MAIN_FINISHED_FLOOR = inch(MAIN_DATUM.inches + _SUBFLOOR.inches)

# --- the one number the whole exercise turns on -----------------------------------
#
# The deck's total depth is not a free choice: it is the wood bay's, or the soffit steps and
# the floor steps with it. 11 7/8" + 3/4" = 12 5/8". Derived rather than authored, so
# re-speccing the joist or the subfloor takes the concrete with it instead of silently
# leaving a step — which is exactly the failure this file spent 2026-08-21 fixing.
DECK_DEPTH = inch(_JOIST_DEPTH.inches + _SUBFLOOR.inches)

# How that depth splits between stay-in-place form and cast cap. The rule, not a snapshot:
# at 13" or more take the 10" form (~21% less concrete — 0.01396 cy/SF — and R-31); below
# 13" stay on the 8" LiteDeck/BuildDeck section and let the cap make up the difference.
# Today that is 8" + 4 5/8"; at 13" it would be 10" + 3" exactly.
#
# Two constraints this arithmetic does NOT enforce, and a human must:
#   * BuildDeck's table wants at least a 4" cap on the 8" form at this 18'-0" clear span, so
#     a total under 12" needs the span re-checked rather than just a thinner pour.
#   * ``plan/assemblies.py`` is editable-dialect — literals only, no imports from params —
#     so CATLIN_DECK_EPS_INT's two structural layers cannot read these and must be edited to
#     match. ``integrity.slab_thickness`` fails the build if they drift apart.
EPS_FORM_DEPTH = inch(10.0) if DECK_DEPTH.inches >= 13.0 else inch(8.0)
EPS_CAP = inch(DECK_DEPTH.inches - EPS_FORM_DEPTH.inches)

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
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
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
    subfloor=DeckLayer(material_ref="plywood-subfloor", thickness=_SUBFLOOR),
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
    # The cap's own top is the finished floor: a cream polish, no covering, no subfloor.
    # Every room that sits on this outline resolves a derived finish zone from it
    # (``resolve/rooms.py``), so RM-M-LIVING keeps LVP as its FIELD finish over the wood
    # bays and the band bills as polished concrete. Move _BAND_Y and the finish moves too —
    # the boundary is stated once, here. Spec in notes/mixed_deck_movement_joint.md.
    floor_finish="polished-concrete",
    # And the cap top has to BE that plane, which is _SUBFLOOR above the storey datum, not
    # the datum itself. ``top_elevation`` is absolute and wins over ``datum`` outright
    # (``resolve/envelope.py::_slab_elevations``), which is the only way to say it: a
    # ``datum="structure"`` slab hangs its thickness below the datum whatever its thickness
    # is, so the depth-matching arithmetic above never reached the elevation. Until
    # 2026-08-21 it did not, and BOTH planes resolved 3/4" low — the polish 3/4" under the
    # plank it is supposed to meet, and the soffit 3/4" under the joists beside it — against
    # a module docstring claiming they matched. Derived, never a literal 0.75: a thicker
    # subfloor lifts the cap with it. SL-G-FLOOR pins itself the same way.
    top_elevation=MAIN_FINISHED_FLOOR,
)

MAIN_ELEMENTS = [WEST_FLOOR, EAST_FLOOR, DECK]
