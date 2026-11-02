"""Catlin's interior doorway floor transitions (review C5-E6, owner 2026-11-01; catalog).

Each is a design selection with a schematic section (``section_documented``), bought or
milled to suit, never supplier-confirmed: the schedule keeps them PENDING. Bound on the
doors' ``doorway=`` in the storey files. Rises are the modelled finish planes
(notes/floor_heights.md), so ``integrity.doorway_assembly`` fails one the moment its floors
move. Section x is the wall normal with +x on the HIGH floor; ``sign`` is the side of the
host wall's normal that floor is on.

Carpet meets oak and tile at a Z-bar, no reducer (owner: 3/8" cushion): the cushion stops at
the bar, the 0.62" carpet is tucked flush with the 3/4" hard floor, and the field stands
1/4" over it, within the 1/4" vertical change ICC A117.1 303.2 lets go untreated. The
7/16" cushion stood 5/16" (notes/bedroom_carpet.md).
"""

from __future__ import annotations

from typehaus import DoorwayProductSpec, DoorwaySectionPart, DoorwayTreatment, Product

_IN = 0.0254
_FLOOR_NOTE = "houses/catlin/notes/floor_heights.md"

CARPET_ZBAR = Product(
    tag="PROD-CARPET-ZBAR", brand="Generic", name="Aluminium carpet Z-bar gripper, 36 in.",
    source="Installer-supplied carpet edge (owner 2026-11-01): carpet tucked into an "
           "aluminium Z-bar fastened to the subfloor against the hard floor's edge. Brand "
           "and section to the installer; notes/bedroom_carpet.md.")
OAK_REDUCER = Product(
    tag="PROD-CATLIN-OAK-REDUCER", brand="Site-milled",
    name="Site-milled white oak reducer / saddle",
    source="Milled from the house oak (oak-floor-custom) by the floor installer, finished "
           "with the floor. D-M-BED2 takes 5/4 stock; notes/floor_heights.md.")
SCHIENE = Product(
    tag="PROD-SCHLUTER-SCHIENE", brand="Schluter", model="SCHIENE (aluminium)",
    name="Schluter-SCHIENE tile edge profile, height to the tile",
    url=("https://www.schluter.com/schluter-us/en_US/Profiles/For-Floors/"
         "Same-height-Transitions/Schluter%C2%AE-SCHIENE/p/A80"),
    source="Same-height transition: the anchoring leg sets in the tile bed and the oak "
           "butts the profile with a 1/4 in. silicone movement joint. Pick the height "
           "to the delivered tile (A80 is 5/16 in.).")
CORETEC_REDUCER = Product(
    tag="PROD-CORETEC-REDUCER", brand="COREtec", name="Quincy Oak reducer",
    source="Colour-matched reducer for the 5 mm Quincy Oak plank (lvp_flooring.md), down to "
           "the coated cap, which tops flush with the plywood since 2026-11-01 "
           "(mixed_deck_movement_joint.md; decision #111). Confirm the SKU with the dealer.")
SOLID_SURFACE_REDUCER = Product(
    tag="PROD-CATLIN-SOLID-SURFACE-REDUCER", brand="Shop-fabricated",
    name="Fabricated solid-surface reducer",
    source="D-S-PLANT reducer over the sealed vinyl water stop, cut from the 12 mm "
           "solid surface (solid-surface-fabricated); order after measuring the stack.")
RUBBER_REDUCER = Product(
    tag="PROD-RUBBER-REDUCER", brand="Generic", name="Bevelled rubber reducer edge",
    source="Rubber reducer edge, height to suit (3/4 in. stall mats, 1/8 in. sheet vinyl), "
           "glued to the substrate. Brand to the installer; confirm the height range.")

TRANSITION_PRODUCTS = (CARPET_ZBAR, OAK_REDUCER, SCHIENE, CORETEC_REDUCER,
                       SOLID_SURFACE_REDUCER, RUBBER_REDUCER)


def _part(name, material, points_in):
    return DoorwaySectionPart(name=name, material_ref=material,
                              polygon_m=tuple((x * _IN, z * _IN) for x, z in points_in))


def _spec(product, variant, installation, *, sign, rise_in, max_in, pairs, edges_in, parts,
          min_in=0.0, url=_FLOOR_NOTE, drawing="schematic design section, "
          "notes/floor_heights.md; supplier section pending", purchase="separate"):
    return DoorwayProductSpec(
        product_ref=product.tag, variant=variant, role="transition", source_url=url,
        source_drawing=drawing, installation=installation, parts=parts,
        section_documented=True, datum="lower_floor", positive_normal_sign=sign,
        higher_floor_side=1, floor_contact_heights_m=(0.0, rise_in * _IN),
        minimum_floor_difference_m=min_in * _IN, maximum_floor_difference_m=max_in * _IN,
        compatible_finish_pairs=pairs, purchase=purchase,
        floor_finish_edges_m=(edges_in[0] * _IN, edges_in[1] * _IN))


def _zbar(sign):
    # The bar's web against the hard floor's edge, its tooth flange under the tucked carpet.
    return _spec(CARPET_ZBAR, "carpet tucked flush with the hard floor; 1/4 in. field rise",
                 "Fasten to the subfloor against the oak/tile edge; cushion stops at the bar",
                 sign=sign, rise_in=0.25, max_in=0.25,
                 pairs=(("catlin-carpet-raised", "oak-floor-custom"),
                        ("catlin-carpet-raised", "catlin-tile-opera-blue")),
                 edges_in=(0.0, 0.0),
                 parts=(_part("z-bar", "aluminum-extrusion",
                              ((0, -0.25), (0.0625, -0.25), (0.0625, -0.0625), (0.75, -0.0625),
                               (0.75, 0), (0, 0))),))


def _bevel(product, variant, installation, material, *, sign, rise_in, run_in, depth_in,
           land_in, max_in, pairs, min_in=0.0):
    """A reducer seated ``depth_in`` below the low floor, bevelled ``run_in`` down to it."""
    return _spec(product, variant, installation, sign=sign, rise_in=rise_in, max_in=max_in,
                 min_in=min_in, pairs=pairs, edges_in=(-run_in, land_in),
                 parts=(_part("reducer", material,
                              ((-run_in, -depth_in), (land_in, -depth_in), (land_in, rise_in),
                               (0, rise_in), (-run_in, 0))),))


# Carpet on the -normal side at D-S-BED1/2/3 and D-M-BATH2.
BEDROOM_ZBAR = DoorwayTreatment(transition=_zbar(-1))

# 0.80315" from the hall LVP up to the carpet: a 1" (5/4) oak saddle on the subfloor, top on
# the carpet plane under the leaf, bevelled 2" down to the plank. Carpet on +normal.
D_M_BED2_SADDLE = DoorwayTreatment(transition=_bevel(
    OAK_REDUCER, "5/4 white oak saddle, 1 3/4 in. flat under the leaf, 2 in. bevel",
    "On the subfloor; LVP floats to its low edge, carpet tucks at its high edge; the "
    "automatic door bottom seals on the flat", "oak-floor-custom", sign=1, rise_in=0.80315,
    run_in=2.0, depth_in=0.19685, land_in=1.75, min_in=0.75, max_in=0.8125,
    pairs=(("lvp", "catlin-carpet-raised"),)))

# Oak and tile at one plane (D-S-SUITEBATH, D-S-BATH1).
TILE_EDGE_FLUSH = DoorwayTreatment(transition=_spec(
    SCHIENE, "aluminium, height to the tile", "Anchoring leg in the tile bed under the "
    "door; oak butts it over a 1/4 in. silicone joint", sign=1, rise_in=0.0, max_in=0.0625,
    pairs=(("oak-floor-custom", "catlin-tile-kaleo-brick"),
           ("oak-floor-custom", "catlin-tile-carrara"),
           ("oak-floor-custom", "catlin-tile-agua-linda")),
    edges_in=(0.0, 0.0625), url=SCHIENE.url, drawing="Schluter-SCHIENE product page; "
    "profile height to the delivered tile",
    parts=(_part("profile", "aluminum-extrusion",
                 ((0, -0.3125), (0.0625, -0.3125), (0.0625, 0), (0, 0))),)))

# Study oak 0.38" over the plant vinyl: the owner's sloped reducer over the vinyl's sealed
# upturn, ~4 1/2" of run. Oak on -normal.
D_S_PLANT_REDUCER = DoorwayTreatment(transition=_bevel(
    SOLID_SURFACE_REDUCER, "12 mm solid surface, 4 1/2 in. slope to the vinyl",
    "Vinyl turns up and seals to the water-stop riser beneath; anchor from the dry side; "
    "seal both ends to the jamb returns", "solid-surface-fabricated", sign=-1,
    rise_in=0.38, run_in=4.5, depth_in=0.12, land_in=0.75, min_in=0.3, max_in=0.4,
    pairs=(("oak-floor-custom", "catlin-plant-vinyl-raised"),)))

# The plank 5 mm (0.19685") over the coated cap, which tops flush with the plywood: a low
# reducer glued to the cap, its lip over the plank's expansion gap. LVP on +normal.
D_M_STUDY_REDUCER = DoorwayTreatment(transition=_bevel(
    CORETEC_REDUCER, "5 mm reducer, plank down to the cap", "Glued to the cap; the plank "
    "keeps its expansion gap under the lip", "aluminum-extrusion", sign=1,
    rise_in=0.19685, run_in=1.0, depth_in=0.0, land_in=0.75, min_in=0.125, max_in=0.25,
    pairs=(("coated-concrete", "lvp"),)))

# The gym's 3/4" stall mats down to the theater carpet (mat on -normal) and to the sauna's
# sealed slab (mat on +normal).
D_B_PLAY_MAT_REDUCER = DoorwayTreatment(transition=_bevel(
    RUBBER_REDUCER, "bevelled rubber edge, 1/4 in. to the carpet", "Glued to the slab at the "
    "mat edge; carpet tucks against its low edge", "rubber", sign=-1, rise_in=0.25,
    run_in=1.0, depth_in=0.5, land_in=1.0, max_in=0.75,
    pairs=(("catlin-rubber-stall-mat", "carpet"),)))
D_B_SAUNA_MAT_REDUCER = DoorwayTreatment(transition=_bevel(
    RUBBER_REDUCER, "bevelled rubber edge for 3/4 in. mats", "Glued to the slab at the mat "
    "edge, outside the sauna's sealed concrete", "rubber", sign=1, rise_in=0.75,
    run_in=2.0, depth_in=0.0, land_in=1.0, min_in=0.5, max_in=0.75,
    pairs=(("sealed-concrete", "catlin-rubber-stall-mat"),)))

# The basement bath's sheet vinyl down to the sealed stair slab (vinyl on -normal).
D_B_BATH_VINYL_REDUCER = DoorwayTreatment(transition=_bevel(
    RUBBER_REDUCER, "rubber reducer for 1/8 in. sheet vinyl", "Glued to the slab; vinyl "
    "tucks under its high lip, sealed", "rubber", sign=-1, rise_in=0.12, run_in=1.0,
    depth_in=0.0, land_in=0.5, max_in=0.125,
    pairs=(("vinyl-sheet", "sealed-concrete"),)))

# Attic study oak 0.63" over the studio's sheet vinyl (oak on -normal).
D_A_HALVES_OAK_REDUCER = DoorwayTreatment(transition=_bevel(
    OAK_REDUCER, "3/4 in. oak reducer, 2 in. bevel to the vinyl", "Rabbeted over the oak's "
    "end, glued and pinned to the subfloor; vinyl stops at its low edge, sealed",
    "oak-floor-custom", sign=-1, rise_in=0.63, run_in=2.0, depth_in=0.12, land_in=0.75,
    min_in=0.5, max_in=0.75, pairs=(("oak-floor-custom", "vinyl-sheet"),)))
