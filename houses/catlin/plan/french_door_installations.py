"""Catalog coordination for the patio and study; no ordered-assembly claims.

Dimensions are evidence-backed envelopes. Outstanding connection and installation
sections remain UNKNOWN in the engine and in notes/french_door_catalog_installation.md.
"""
import json
from pathlib import Path

from typehaus import ExteriorDoorCatalogInstallation, ExteriorDoorInstallation, inch

_OUTLINE_PATH = Path(__file__).resolve().parents[1] / 'notes/assets/endura-zai4565fn-outline.json'
_OUTLINE = json.loads(_OUTLINE_PATH.read_text())


def catalog_installation(**overrides):
    """The study's timber outriggers by default; the patio passes its foam bed."""
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


# ** THE PATIO TREAD IS ONE TREX BOARD ON 40 PSI XPS (owner, 2026-11-03). ** The AridDek
# boards, both cross bearers and the 7-strip concrete cantilever are gone. One Enhance Basics
# board (0.94 x 5 1/2, Tide Pool) runs the reveal, laid continuously on the curb's foam, whose
# top course is cut down and replaced in 40 psi XPS; nothing fastens it to W-SG-BRKBM, so
# nothing metal crosses from the house into the court. A PVC sheet under it laps under the
# SureSill pan's lip. Its 1/2" south gap at the beam's arris is the drain slot. Graded as
# 300 lb over a square of its own width against 40/3 psi (notes/french_door_catalog_
# installation.md §6). Off Trex's published install (joists at 16", air under): a warranty
# exposure the owner accepted, not a code one.
_PATIO_TREAD = dict(
    independent_landing_flashing=False,
    support_kind='foam_bed', support_ref='W-B-S3', support_material_ref='xps-40',
    support_width=inch(5.5), support_depth=inch(4.06), foam_rated_psi=40.0,
    approach_material_ref='trex-enhance-basics', approach_thickness=inch(0.94),
    approach_board_width=inch(5.5),
    approach_source_url='https://www.trex.com/professionals/products/decking/',
    apron_material_ref='pvc-door-water-sheet')


PATIO_INSTALLATION = ExteriorDoorInstallation(
    factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
    # The box sides: Trex Tide Pool fascia ripped ~6" deep, frame to the brick's back,
    # sealed to the brick, so they close the cavity at the reveal (replaced Captivate).
    exterior_material_ref='trex-tide-pool-fascia', exterior_return_to_reveal_back=True,
    exterior_return_thickness=inch(0.56),
    exterior_opening_ref='AO-B-BRICK-DOOR',
    seat_opening_ref='AO-B-PATIO-SEAT',
    landing_search=inch(12),
    catalog_installation=catalog_installation(**_PATIO_TREAD))
STUDY_INSTALLATION = ExteriorDoorInstallation(
    factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
    exterior_material_ref='captivate-sheet', catalog_installation=catalog_installation())


def with_catalog_installations(elements):
    installations = {'D-B-PATIO': PATIO_INSTALLATION, 'D-S-DECK-E': STUDY_INSTALLATION}
    return tuple(element.model_copy(update={'exterior_installation': installations[element.tag]})
                 if element.tag in installations else element for element in elements)
