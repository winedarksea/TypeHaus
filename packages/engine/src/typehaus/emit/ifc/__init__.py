"""IFC4 emission — lowlevel 0.8 adapter + resolved-model emitter (→ 12).

Optional extension (U9): IFC export depends on ifcopenshell (+ pyproj), which have no standard
pyodide wheels, so this package is **excluded from the core offline PWA bundle**
(ui/scripts/build-pwa-assets.mjs ships it as a separate ``typehaus-ifc-ext.tar`` instead). Nothing
on the offline compute path imports it — every ``emit_ifc`` caller imports it lazily, only when
actually writing IFC — so its absence never affects load/resolve/model.json/glb. A future
browser IFC extension unpacks this tar plus the experimental ifcopenshell wasm build onto the
worker's sys.path, with no change to the core bundle.
"""

from __future__ import annotations

from typehaus.emit.ifc.emitter import emit_ifc

__all__ = ["emit_ifc"]
