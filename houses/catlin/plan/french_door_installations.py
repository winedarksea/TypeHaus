"""Catalog coordination for the patio and study; no ordered-assembly claims.

Dimensions are evidence-backed envelopes. Outstanding connection and installation
sections remain UNKNOWN in the engine and in notes/french_door_catalog_installation.md.
"""
import json
from pathlib import Path

from typehaus import ExteriorDoorCatalogInstallation, ExteriorDoorInstallation, inch

_OUTLINE = json.loads((Path(__file__).resolve().parents[1] / 'notes/assets/endura-zai4565fn-outline.json').read_text())


def catalog_installation(*, concrete=False):
    return ExteriorDoorCatalogInstallation(
        source_url=_OUTLINE['source_url'], source_drawing=_OUTLINE['source_drawing'],
        frame_material_ref='composite-door-frame', head_material_ref='pvc-opening-flashing',
        pan_material_ref='impermeable-door-flashing', transition_material_ref='silicone-transition',
        sill_outline_m=tuple(tuple(point) for point in _OUTLINE['polygon_m']),
        support_kind='concrete_cantilever' if concrete else 'timber_outriggers',
        support_ref='W-B-S3' if concrete else 'FS-S-EAST',
        support_width=inch(12) if concrete else inch(1.5),
        support_depth=inch(6) if concrete else inch(5.5),
        support_material_ref='concrete' if concrete else 'kdat')


PATIO_INSTALLATION = ExteriorDoorInstallation(
    factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
    exterior_material_ref='composite-door-frame', exterior_opening_ref='AO-B-BRICK-DOOR',
    seat_opening_ref='AO-B-PATIO-SEAT', landing_search=inch(12),
    catalog_installation=catalog_installation(concrete=True))
STUDY_INSTALLATION = ExteriorDoorInstallation(
    factory_frame_depth=inch(4.5625), interior_material_ref='pine-fj-base',
    exterior_material_ref='composite-door-frame', catalog_installation=catalog_installation())


def with_catalog_installations(elements):
    installations = {'D-B-PATIO': PATIO_INSTALLATION, 'D-S-DECK-E': STUDY_INSTALLATION}
    return tuple(element.model_copy(update={'exterior_installation': installations[element.tag]})
                 if element.tag in installations else element for element in elements)
