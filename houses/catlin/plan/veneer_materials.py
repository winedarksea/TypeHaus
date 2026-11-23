# haus: editable
# Materials the brick veneer's flashing and its isolation use (2026-11-23, owner: stainless).
#
# The base bond break, the lintel head flashing and the door's wythe all stand in a court that
# drains only to its own soakaway and carries road salt, so the sheet is Type 316 stainless
# (the house's SS316 standoff shims and 316 gasketed screws make the same call). Stainless and
# galvanized stay out of one joint: the head flashing sits on an EPDM strip over each HDG angle
# lintel (FL-B-BRICK-*-ISOL), never on the zinc, and its upstand is fixed with 316 screws.
# notes/sunken_garden_veneer_beam.md §6n.

from typehaus import Material

VENEER_MATERIALS = (
    Material(tag="stainless-steel-flashing", name="Type 316 stainless steel sheet flashing, brake-formed",
             hatch="metal", color="#b4b9bd", vapor_permeance_perms=0.0,
             source="AISI Type 316 stainless sheet (ASTM A666 / A240, the sheet Hohmann & Barnard list beside Type 304 for its anchors and flashing-class accessories); thickness stated when the sheet is bought, never in contact with the HDG lintel or with mortar-bonded carbon steel"),
)
