"""House-roof eave closure trim — fascia, box gutter, drip edge (Tier 2, WP roof-eave).

The RF-HOUSE eave edges (ridge runs N-S, so the eaves are the WEST and EAST footprint
edges) get the closure the golden reference details (`roof_wall_eave_detail_ifc.py` +
`notes/roof_wall_eave_detail.md`):

- a FASCIA band closing the exposed strip between the deck+membrane top and just past
  the knee-wall top plate (the reference closes this band with extended wall sheathing;
  the fascia is the 3D stand-in, and it also approximates the flat-topped wall foam +
  spray-foam wedge the reference draws at the foam interface);
- a 6" BOX GUTTER (angled-fascia style, reference gutter block) hung at the wall plane
  with its top just below the roof-furring underside;
- a DRIP EDGE flashing along the metal-roof eave that empties into the gutter.

RF-HOUSE has zero authored overhang, so no soffit exists or is needed. Garage trim is
deferred with the garage/truss roof.

Not `# haus: editable`: trim runs are not UI-movable elements (only params-generated
geometry lives here), so the editable-writeback rule does not apply.

Geometry facts this module derives from (see plan/storeys/attic.py + plan/assemblies.py):
- sheathing-ext datum plane at x = 0 / 36'; wall stack outboard of it =
  wrb 0.02" + polyiso 2" + eps 2" + furring 0.5" + cladding 0.5" = 5.02" (cladding face
  == roof footprint edge, where eave_z_m is defined);
- knee-wall plate top at 25'; deck plane (eave_z_m) rides the I-joist rise above it:
  11.875" - 3.5" x 4/12 birdsmouth = 10.7083";
- roof stack above the deck (perpendicular): deck 0.75" + membrane 0.25" -> foam 6" ->
  roof membrane 0.25" (furring underside at 7.25") -> batten 0.75" -> metal 0.5".
"""

from __future__ import annotations

from typehaus import Fascia, Flashing, Gutter, TrimKind, ft, inch, pt

_HOUSE_FT = 36.0
# Wall layers outboard of the sheathing-ext datum -> the cladding outer face, which is
# exactly the roof footprint edge (the zero-overhang roof laps the cladding).
_WALL_OUTBOARD_IN = 0.02 + 2.0 + 2.0 + 0.5 + 0.5  # 5.02"
_EAVE_X_W = ft(0) - inch(_WALL_OUTBOARD_IN)
_EAVE_X_E = ft(_HOUSE_FT) + inch(_WALL_OUTBOARD_IN)

_PLATE_TOP = ft(25)  # attic elevation 20' + 5' knee walls
_DECK_RISE_IN = 11.875 - 3.5 * (4.0 / 12.0)  # I-joist depth - birdsmouth = 10.7083"
_EAVE_DECK = _PLATE_TOP + inch(_DECK_RISE_IN)  # deck plane at the eave edge (eave_z_m)
_DECK_MEM_IN = 0.75 + 0.25  # roof deck + membrane band the fascia tops out at
_FURRING_UNDERSIDE_IN = _DECK_MEM_IN + 2.0 + 4.0 + 0.25  # 7.25" above the deck

# Cross-sections (reference gutter block: 5" tall x ~6" deep box, top 1.2" below the
# roof furring underside; drip edge is the smallest primitive).
_FASCIA_THICK_IN = 1.0
_FASCIA_DEPTH = inch(_DECK_MEM_IN + _DECK_RISE_IN + 2.0)  # down past the plate ~2"
_GUTTER_DEPTH = inch(5)
_GUTTER_THICK_IN = 6.0
_DRIP_DEPTH = inch(3)
_DRIP_THICK = inch(0.75)


def _run(x, y0_ft: float = 0.0, y1_ft: float = _HOUSE_FT):
    return (pt(x, ft(y0_ft)), pt(x, ft(y1_ft)))


def _eave_trim(side: str, index: int, eave_x, outward: float):
    """One eave edge's fascia + gutter + drip edge; ``outward`` is -1 west / +1 east."""

    def out(inches_val: float):
        offset = inch(inches_val)
        return eave_x + offset if outward > 0 else eave_x - offset

    fascia_center = out(_FASCIA_THICK_IN / 2.0)
    gutter_center = out(_FASCIA_THICK_IN + _GUTTER_THICK_IN / 2.0)
    fascia = Fascia(
        uid=f"RTFC0{index}AAAA", tag=f"TR-RF-FASCIA-{side}", kind=TrimKind.FASCIA,
        path=_run(fascia_center),
        top_elevation=_EAVE_DECK + inch(_DECK_MEM_IN), depth=_FASCIA_DEPTH,
        thickness=inch(_FASCIA_THICK_IN), material="aluminum", host_ref="RF-HOUSE")
    gutter = Gutter(
        uid=f"RTGT0{index}AAAA", tag=f"TR-RF-GUTTER-{side}", kind=TrimKind.GUTTER,
        path=_run(gutter_center),
        top_elevation=_EAVE_DECK + inch(_FURRING_UNDERSIDE_IN - 1.2), depth=_GUTTER_DEPTH,
        thickness=inch(_GUTTER_THICK_IN), material="aluminum", host_ref=f"TR-RF-FASCIA-{side}",
        slope='1/16 in/ft to downspout')
    drip = Flashing(
        uid=f"RTFF0{index}AAAA", tag=f"TR-RF-DRIP-{side}", kind=TrimKind.DRIP_FLASHING,
        path=_run(fascia_center),
        top_elevation=_EAVE_DECK + inch(_FURRING_UNDERSIDE_IN + 1.75), depth=_DRIP_DEPTH,
        thickness=_DRIP_THICK, material="aluminum", host_ref=f"TR-RF-GUTTER-{side}")
    return [fascia, gutter, drip]


ATTIC_ELEMENTS = [*_eave_trim("W", 1, _EAVE_X_W, -1.0), *_eave_trim("E", 2, _EAVE_X_E, 1.0)]
