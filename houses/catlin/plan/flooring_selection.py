"""Catlin's Cotton Oak selection; shared library defaults stay generic."""

from params.flooring import LVP_THICKNESS_IN

from typehaus import Material, Product

COTTON_OAK_PRODUCT = Product(
    tag="PROD-KARNDEAN-COTTON-OAK", brand="Karndean", model="AKP-RL38",
    name="Art Select Rigid Core Cotton Oak click-lock luxury vinyl plank",
    url="https://www.karndean.com/en-us/floors/products/cotton-oak-akp-rl38",
    source='Owner selection 2026-11-01, replacing Quincy Oak. Nominal 48 x 7 in.; 7.0 mm '
           'product thickness (the page does not split out the sound-absorbing backing, so '
           'no separate pad is added); 30 mil wear layer; bevelled edge; 23.51 SF/box. '
           'Floating on the plywood subfloor; the rigid-core guide recommends no separate '
           'underlay. No price is published; obtain a local quote and a sample. Guide: '
           'karndean.com/globalassets/karndean/b2c-blocks/b2c-document-listing-block/usa/'
           'installation-guides/karndean-rigid-core_plank-and-tile-installation-guide-usa.pdf. '
           'See notes/lvp_flooring.md.',
)

# Central half of Karndean's cotton-oak--akp-rl38--oh_cm overhead image
# (https://www.karndean.com/globalassets/products/art-select/overheads/cotton-oak--akp-rl38--oh_cm.jpg),
# mean sRGB, read 2026-11-01.
COTTON_OAK_COLOR = "#d6cebb"
COTTON_OAK_LVP = Material(
    tag="lvp", name="Karndean Art Select Rigid Core Cotton Oak AKP-RL38 click-lock LVP, 7 mm",
    hatch="lumber", color=COTTON_OAK_COLOR, finish="lvp-limed-oak",
    finish_thickness_in=LVP_THICKNESS_IN, product_ref=COTTON_OAK_PRODUCT.tag,
    floor_companion_refs=(), floating=True,
    source='7.0 mm product thickness as published; no extra pad or underlay. Floating: '
           '3/16 in. (5 mm) perimeter and fixed-object gap, 5/16 in. past 1000 SF; fixed '
           'cabinets stand on the subfloor, never on the plank. Grain and print repeat are '
           'schematic, not verified product artwork. notes/lvp_flooring.md.',
)


def with_selected_flooring(materials):
    """Replace the house's LVP row without appending a duplicate material tag."""
    return tuple(COTTON_OAK_LVP if material.tag == "lvp" else material
                 for material in materials)
