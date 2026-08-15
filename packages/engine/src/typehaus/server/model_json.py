"""model.json — the UI contract (→ 20 §model.json). Emitted from the ResolvedModel.

Carries resolved wall layer polygons, framed members, rooms, openings, and derived
conditions in canonical SI meters; element uid/tag ride along for pick → provenance.

This module is the import surface, not the implementation: the payload is assembled in
:mod:`typehaus.server.model_json_document` from one serializer per domain
(``model_json_fabric``, ``model_json_placeables``, ``model_json_systems``,
``model_json_spaces``, ``model_json_catalog``, over the shared shapes in
``model_json_shared``). Every caller — the server, the CLI, the offline PWA bootstrap —
keeps importing it from here.
"""

from __future__ import annotations

from typehaus.server.model_json_catalog import load_variant_catalog
from typehaus.server.model_json_document import (
    model_to_dict,
    preview_to_dict,
    write_model_json,
)

__all__ = [
    "load_variant_catalog",
    "model_to_dict",
    "preview_to_dict",
    "write_model_json",
]
