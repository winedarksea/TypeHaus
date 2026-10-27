"""Catlin's provisional Quincy Oak selection; shared library defaults stay generic."""

from params.flooring import LVP_THICKNESS_IN

from typehaus import Material, Product

QUINCY_OAK_PRODUCT = Product(
    tag="PROD-CORETEC-QUINCY-OAK", brand="COREtec", model="VV017-01018",
    name="Pro Classics Quincy Oak click-lock SPC luxury vinyl plank",
    url="https://coretecfloors.com/en-us/products/coretec-pro-classics/quincy-oak-vv017-01018",
    source='Provisional owner selection 2026-10-26. Nominal 7 x 48 in.; 5 mm total '
           'including attached cork; 20 mil wear layer, UV acrylic finish, microbeveled '
           'edges. Floating installation on the framed plywood; no separate acoustic mat. '
           '28.84 SF/carton. Manufacturer lists $5.69/SF, read 2026-10-26; obtain local '
           'delivered quote and physical sample. See notes/lvp_flooring.md.',
)

# Central half of COREtec's vv017_01018_1to1 plank image, read 2026-10-26.
# A photographic color approximation; procedural oak figure is not the product's print.
QUINCY_OAK_COLOR = "#bfb6ad"
QUINCY_OAK_LVP = Material(
    tag="lvp", name="COREtec Pro Classics Quincy Oak click-lock LVP, 5 mm with cork",
    hatch="lumber", color=QUINCY_OAK_COLOR, finish="lvp-plank",
    finish_thickness_in=LVP_THICKNESS_IN, product_ref=QUINCY_OAK_PRODUCT.tag,
    floor_companion_refs=(),
    source='5 mm total including attached cork, not 5 mm plus pad. Pale oak appearance '
           'approximates the manufacturer swatch with the existing low-sheen 7 x 48 in. '
           'microbeveled procedural plank recipe; its grain and six-print repeat are '
           'schematic, not verified product artwork. No separate acoustic mat or assumed '
           'pad compression. Verify installed sample and concrete coating at the joint; '
           'notes/lvp_flooring.md.',
)


def with_selected_flooring(materials):
    """Replace the house's LVP row without appending a duplicate material tag."""
    return tuple(QUINCY_OAK_LVP if material.tag == "lvp" else material
                 for material in materials)
