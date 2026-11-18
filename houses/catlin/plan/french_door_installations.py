"""Catalog coordination for the exterior swing doors; no ordered-assembly claims.

Dimensions are evidence-backed envelopes. Outstanding connection and installation
sections remain UNKNOWN in the engine and in notes/french_door_catalog_installation.md.
"""
import json
from pathlib import Path

from typehaus import (ApproachBearing, ExteriorDoorCatalogInstallation,
                      ExteriorDoorInstallation, Material, inch)

_ASSETS = Path(__file__).resolve().parents[1] / 'notes/assets'
_OUTLINE = json.loads((_ASSETS / 'endura-zai4565fn-outline.json').read_text())
# The 5-5/8" sill, the only Z-Series width Endura publishes the 6-3/8" XXXXW for.
_OUTLINE_5625 = json.loads((_ASSETS / 'endura-zai5625fn-outline.json').read_text())


def catalog_installation(**overrides):
    """The ZAI4565FN coordination outline; each door passes its own support."""
    # No sill extender (owner, 2026-11-01).
    fields = dict(
        source_url=_OUTLINE['source_url'], source_drawing=_OUTLINE['source_drawing'],
        frame_material_ref='composite-door-frame', head_material_ref='pvc-opening-flashing',
        pan_material_ref='impermeable-door-flashing', transition_material_ref='silicone-transition',
        sill_outline_m=tuple(tuple(point) for point in _OUTLINE['polygon_m']),
        independent_landing_flashing=True,
        support_kind='timber_outriggers', support_ref='FS-S-EAST',
        support_width=inch(1.5), support_depth=inch(5.5), support_material_ref='kdat')
    return ExteriorDoorCatalogInstallation(**{**fields, **overrides})


# ** THE SUNKEN-GARDEN TREAD IS ONE TREX BOARD ON 40 PSI XPS (owner, 2026-11-03). ** The AridDek
# boards, both cross bearers and the 7-strip concrete cantilever are gone. One Enhance Basics
# board (0.94 x 5 1/2, Tide Pool) runs the reveal, laid continuously on the curb's foam, whose
# top course is cut down and replaced in 40 psi XPS; nothing fastens it to W-SG-BRKBM, so
# nothing metal crosses from the house into the court. A PVC sheet under it runs back under the
# SureSill pan (the pan laps over it) and stops at the tread's outer face. Its 1/2" south gap
# at the beam's arris is the drain slot, into the isolation joint below. Graded as
# 300 lb over a square of its own width against 40/3 psi (notes/french_door_catalog_
# installation.md §6). Off Trex's published install (joists at 16", air under): a warranty
# exposure the owner accepted, not a code one. Since 2026-11-17 a 1/4" FRP plate under the
# scalloped board spreads it over its whole footprint, on 60 psi XPS thinned by the plate, so
# the tread top holds (notes/exterior_door_sill_beam.md §5).
_SUNKEN_TREAD = dict(
    # The sheltered self-supporting veneer arch has no face-mounted head flashing.
    stock_head_flashing=False,
    independent_landing_flashing=False,
    support_kind='foam_bed', support_ref='W-B-S3', support_material_ref='xps-60',
    support_width=inch(5.5), support_depth=inch(4.06), foam_rated_psi=60.0,
    bearing_plate_material_ref='frp-bearing-plate', bearing_plate_thickness=inch(0.25),
    approach_profiled_underside=True,
    approach_material_ref='trex-enhance-basics', approach_thickness=inch(0.94),
    approach_board_width=inch(5.5),
    approach_source_url='https://www.trex.com/professionals/products/decking/',
    apron_material_ref='pvc-door-water-sheet',
    # The slot drains down the house/court isolation joint (owner, 2026-11-13): W-SG-BRKBM's
    # 2" XPS break is cut across the reveal (AO-SG-BRKBM-TREAD-BED) and refilled with a
    # drainage board onto FB-SG-BRKBM's stone. The door is under the porch roof, so this is a
    # weep for incidental water, not a gutter.
    joint_drain_wall_ref='W-SG-BRKBM', joint_drain_material_ref='xps-drainage-board',
    joint_drain_bed_ref='FB-SG-BRKBM',
    box_side_sealant_ref='box-side-sealant', box_side_joint_width=inch(0.5))


SUNKEN_DOOR_INSTALLATION = ExteriorDoorInstallation(
    factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
    # The box sides: Trex Tide Pool fascia ripped ~6" deep, frame to the brick's back,
    # sealed to the brick, so they close the cavity at the reveal (replaced Captivate).
    exterior_material_ref='trex-tide-pool-fascia', exterior_return_to_reveal_back=True,
    exterior_return_thickness=inch(0.56),
    exterior_opening_ref='AO-B-BRICK-DOOR',
    seat_opening_ref='AO-B-SUNKEN-SEAT',
    landing_search=inch(12),
    catalog_installation=catalog_installation(**_SUNKEN_TREAD))
# ** ONE SILL PACKAGE AT THE THREE FRAMED-FLOOR DOORS (owner, 2026-11-17). ** A ZAI5625FN on the
# 4 9/16" jamb with the full 6 3/8" XXXXW, on a self-adhered membrane pan on the subfloor. The
# nose bears on the girt sill beam, outboard of the girt band with its face at the nose, seated
# at its ends (envelope_walls.py); the pan wraps the beam face to a drip past the cladding.
# Nothing is fastened across the house/landing joint. notes/exterior_door_sill_beam.md.
_MEMBRANE_PAN = dict(
    pan_height=inch(1 / 16),
    pan_product='Impermeable self-adhered membrane pan (AAMA 711) with a back dam; the sill '
                'bears on the subfloor',
    pan_source_url='notes/opening_flashing_spec.md')
_XXXXW_URL = ('https://resources.enduraproducts.com/hubfs/OMRSv3%20-%20Line%20Drawings/Sill%20'
              'Extenders/Sill%20Width%20Extender%20Release_final.pdf')


def framed_floor_installation(support_ref, bearing, **door):
    """The shared package on the girt sill beam; each door passes its trim and landing."""
    return ExteriorDoorInstallation(
        factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
        approach_bearing=bearing, **door,
        catalog_installation=catalog_installation(
            source_url=_OUTLINE_5625['source_url'], source_drawing=_OUTLINE_5625['source_drawing'],
            sill_outline_m=tuple(tuple(point) for point in _OUTLINE_5625['polygon_m']),
            sill_extender_ref='XXXXW', sill_extender_source_url=_XXXXW_URL,
            sill_extender_depth=inch(6.375), sill_extender_height=inch(17 / 32),
            support_kind='girt_bridge', support_ref=support_ref, **_MEMBRANE_PAN))


# The planks reach FS-SG-BALCONY's north sister: the joint (~1" off the beam face) is too narrow
# for a cover with its seat and range (notes/exterior_door_sill_beam.md §4), so it stays open.
STUDY_INSTALLATION = framed_floor_installation(
    'W-S-S2', ApproachBearing(landing_ref='FS-SG-BALCONY', landing='gap'),
    exterior_material_ref='captivate-sheet')
# A removable gritted cover over the ~2 1/8" joint: fixed on FS-SG-PORCH's north joist, sliding
# on a ledge on the beam face below the drip; water drops through to TR-SG-SLOT.
PORCH_INSTALLATION = framed_floor_installation(
    'W-M-S2', ApproachBearing(landing_ref='FS-SG-PORCH', landing='cover',
                              cover_material_ref='frp-joint-cover', cover_seat=inch(1.5625),
                              cover_discharge_ref='TR-SG-SLOT'),
    exterior_wrap_material_ref='metal-dark-exterior')
# FS-BW-FLOOR's rim and deck edge stand under 1/2" off the nose (params/breezeway.py): no cover.
ENTRY_INSTALLATION = framed_floor_installation(
    'W-M-N3', ApproachBearing(landing_ref='FS-BW-FLOOR', landing='gap'),
    exterior_wrap_material_ref='metal-dark-exterior')


def with_catalog_installations(elements):
    installations = {'D-B-SUNKEN': SUNKEN_DOOR_INSTALLATION, 'D-S-BALCONY': STUDY_INSTALLATION,
                     'D-M-PORCH': PORCH_INSTALLATION, 'D-M-ENTRY': ENTRY_INSTALLATION}
    return tuple(element.model_copy(update={'exterior_installation': installations[element.tag]})
                 if element.tag in installations else element for element in elements)


# Performance specifications, no product selected: graded geometry, supplier-held products.
DOOR_INSTALLATION_MATERIALS = (
    Material(tag="uhmw-slip-pad", name="UHMW polyethylene slip pad",
             color="#f4f4f0", hatch="rigid",
             source="Where a door approach rests on its landing deck: free to slide the 1/4 in "
                    "reserved house/landing movement, never fastened across the joint."),
    Material(tag="xps-drainage-board", name="XPS drainage board, 2 in, grooved, filter-fabric faced",
             r_per_inch=5.0, perm_rating=1.1, hatch="rigid", color="#c9a3ad", foam_plastic=True,
             source="ASTM C578 XPS with vertical drainage channels and a bonded filter fabric; "
                    "replaces W-SG-BRKBM's isolation board under D-B-SUNKEN's drain slot, foot "
                    "on FB-SG-BRKBM's stone (owner 2026-11-13). Product not selected."),
    Material(tag="frp-joint-cover", name="Gritted FRP joint cover, cut to the door width",
             color="#6f7a6a", hatch="rigid",
             source="Removable cover over D-M-PORCH's walking joint (owner 2026-11-17): molded or "
                    "pultruded FRP, gritted top, open to drain, its thickness the deck's; fixed "
                    "on the landing joist, sliding on a KDAT ledge. Product not selected."),
    Material(tag="frp-bearing-plate", name="FRP bearing plate, 1/4 in, under D-B-SUNKEN's tread",
             color="#d8d4c8", hatch="rigid",
             source="Flat 1/4 in FRP (or cellular PVC) sheet spreading the scalloped Trex tread "
                    "over its full footprint on the 60 psi XPS (owner 2026-11-17). Trex "
                    "compatibility is a supplier hold. Product not selected."),
    Material(tag="box-side-sealant", name="Silicone sealant joint on closed-cell backer rod",
             color="#8a8a8a",
             source="ASTM C920 Class 50 or better, 1/2 in wide: the Trex box sides (house) to "
                    "the court's brick, 1/4 in movement reserved each way. Product not selected."),
)
