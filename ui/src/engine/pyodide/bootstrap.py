"""In-pyodide engine bootstrap for the degraded offline PWA (→ 40 WP4.2, gate outcome b).

Runs once inside the Web Worker after the engine tarball is unpacked onto sys.path. Stubs the
three wasm-hostile deps (libcst, ifcopenshell, pyproj) so importing ``typehaus.source`` (whose
package __init__ pulls writeback → libcst) succeeds; the compute path — load_plan, resolve,
model_to_dict, checks, emit_glb — needs none of them. Any code path that actually touches a
stubbed module raises ``RequiresLocalInstall``, which the worker maps to a clear UI error.
"""

from __future__ import annotations

import os
import sys
import types
from pathlib import Path
from typing import Any


class RequiresLocalInstall(RuntimeError):
    """Raised when an offline call needs a dep only available in the local `haus serve`."""


# --- Permissive libcst stub -------------------------------------------------------------
# libcst has no pyodide wheel (native Rust), but `typehaus.source` uses it at *import* time
# (e.g. `class _DialectVisitor(cst.CSTVisitor)`, `cst.metadata.PositionProvider`). A stub that
# is freely subclassable and answers any attribute access lets those modules import; the
# offline compute path never *calls* the writeback/lint parser (rebuild() imports the manifest
# directly), so a stub is enough. Actual parsing would just build inert stub nodes.


class _CstMeta(type):
    def __getattr__(cls, _name: str) -> Any:
        return _CstStub


class _CstStub(metaclass=_CstMeta):
    def __init__(self, *_a: Any, **_k: Any) -> None:
        pass

    def __getattr__(self, _name: str) -> Any:
        return _CstStub

    def __call__(self, *_a: Any, **_k: Any) -> Any:
        return _CstStub()


def _install_libcst_stub() -> None:
    if "libcst" in sys.modules:
        return
    mod = types.ModuleType("libcst")
    mod.__getattr__ = lambda _attr: _CstStub  # type: ignore[attr-defined]
    meta = types.ModuleType("libcst.metadata")
    meta.__getattr__ = lambda _attr: _CstStub  # type: ignore[attr-defined]
    mod.metadata = meta  # type: ignore[attr-defined]
    sys.modules["libcst"] = mod
    sys.modules["libcst.metadata"] = meta


def _install_blocking_stub(name: str) -> None:
    """A stub whose every use raises — for deps reached only at call time (ifc emit).

    Marked ``__typehaus_stub__`` so the optional IFC extension (``enable_ifc``) can detect that
    no real ifcopenshell has replaced it and surface a precise degradation.
    """
    if name in sys.modules:
        return
    mod = types.ModuleType(name)

    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise RequiresLocalInstall(
            f"{name} is not available in the offline PWA — run `haus serve` locally"
        )

    mod.__getattr__ = lambda _attr: _blocked  # type: ignore[attr-defined]
    mod.__typehaus_stub__ = True  # type: ignore[attr-defined]
    sys.modules[name] = mod


_install_libcst_stub()
for _dep in ("ifcopenshell", "pyproj"):
    _install_blocking_stub(_dep)
for _sub in ("ifcopenshell.api", "ifcopenshell.guid"):
    sys.modules.setdefault(_sub, sys.modules["ifcopenshell"])

# U9: the offline PWA now *edits* plan source too, via the pure-Python (ast) writeback backend
# — no libcst. Selecting it before typehaus.source is imported means every mutation entry point
# (writeback, coordinator read helpers, import sync) routes to the libcst-free path. The libcst
# stub above still lets the modules import; the py backend never calls into it.
os.environ["TYPEHAUS_WRITEBACK"] = "py"


class OfflineEngine:
    """One loaded house + its resolved model, recomputed on each loadHouse (→ server/state.py)."""

    def __init__(self) -> None:
        self.house_dir: Path | None = None
        self.model: Any = None
        self.findings: list[Any] = []
        self.provenance: Any = None
        self.ok: bool = False
        self._revision: str = "0"
        self._coord: Any = None  # lazily-built ProjectCoordinator (owns the undo journal)

    def load_house(self, root: str, files: dict[str, str]) -> dict[str, Any]:
        base = Path(root)
        # Wipe any prior tree so deletes propagate.
        import shutil

        if base.exists():
            shutil.rmtree(base)
        for rel, content in files.items():
            dest = base / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
        self.house_dir = base
        self._coord = None  # a new house resets the mutation journal
        return self.rebuild()

    def coordinator(self) -> Any:
        """The mutation coordinator for the loaded house (built once, keeps the journal)."""
        from typehaus.source.coordinator import ProjectCoordinator

        assert self.house_dir is not None
        if self._coord is None:
            self._coord = ProjectCoordinator(self.house_dir)
        return self._coord

    # --- mutation surface (libcst-free, U9) --------------------------------------------
    def patch(self, ops_json: list[dict[str, Any]], expected_revision: str | None) -> dict[str, Any]:
        from typehaus.source.ops import PatchOp

        ops = [
            PatchOp(
                op=o["op"], type=o["type"], tag=o["tag"],
                fields=dict(o.get("fields") or {}),
                hint_file=o.get("hint_file"), hint_list=o.get("hint_list"),
            )
            for o in ops_json
        ]
        result = self.coordinator().apply_patch(ops, expected_revision)
        self.rebuild()
        return {
            "revision": result.revision, "minted": dict(result.minted_uids),
            "undo": result.undo_depth, "redo": result.redo_depth,
        }

    def undo(self) -> dict[str, Any]:
        result = self.coordinator().undo()
        self.rebuild()
        return {"revision": result.revision, "undo": result.undo_depth, "redo": result.redo_depth}

    def redo(self) -> dict[str, Any]:
        result = self.coordinator().redo()
        self.rebuild()
        return {"revision": result.revision, "undo": result.undo_depth, "redo": result.redo_depth}

    def rebuild(self) -> dict[str, Any]:
        # Offline load path (→ 40 gate b): import the manifest directly (pure `exec`, no
        # libcst) instead of load_plan(), whose dialect-lint + provenance steps are the
        # libcst-gated parts. We reuse the engine's own _import_manifest so library-root
        # discovery and error-as-finding behaviour match the server. Provenance is empty
        # offline — source-location links degrade gracefully; the model itself is identical.
        from typehaus.findings import Severity
        from typehaus.resolve import resolve
        from typehaus.source import loader
        from typehaus.source.provenance import Provenance

        assert self.house_dir is not None
        self.provenance = Provenance()
        self.findings = []
        # Use the loader's content hash so the model revision the UI echoes back on a patch
        # matches the coordinator's optimistic-concurrency revision (both are _content_hash).
        self._revision = loader._content_hash(self.house_dir)
        plan = loader._import_manifest(self.house_dir, self.findings)
        if plan is None:
            self.model = None
            self.ok = False
        else:
            model, rfindings = resolve(plan)
            self.findings.extend(rfindings)
            self.model = model
            self.ok = not any(f.severity is Severity.ERROR for f in self.findings)
        return {"ok": self.ok, "revision": self._revision, "findings": self.findings_json()}

    def model_json(self) -> dict[str, Any]:
        from typehaus.checks import load_preferences
        from typehaus.server.model_json import load_variant_catalog, model_to_dict

        if self.model is None:
            return {
                "revision": self._revision,
                "units": "imperial",
                "projectNorth": 0.0,
                "findings": [f.model_dump(mode="json") for f in self.findings],
                "ok": False,
            }
        payload = model_to_dict(
            self.model,
            revision=self._revision,
            provenance=self.provenance,
            findings=self.findings,
            preferences=load_preferences(self.house_dir),
            # Offline PWA: a house bundle without variants.toml (or one whose catalog fails
            # to parse in-worker) degrades to an empty variant list, never a worker error.
            variants=load_variant_catalog(self.house_dir),
        )
        payload["ok"] = self.ok
        return payload

    def findings_json(self) -> list[dict[str, Any]]:
        return [f.model_dump(mode="json") for f in self.findings]

    def bom_json(self) -> dict[str, Any]:
        """The bill of materials, offline. Mirrors the served ``/bom`` endpoint so the
        browser reads the same one implementation either way."""
        from typehaus.takeoff.bom import bill_of_materials

        if self.model is None:
            return {}
        return bill_of_materials(self.model)

    def costs_json(self) -> dict[str, Any]:
        """The cost-tracking payload, offline. Mirrors the served ``GET /costs`` — the
        worker's house snapshot carries prices.toml/costs.toml when the house has them, so
        the offline view shows the same join/estimate/check-off state. Read-only: edits go
        through the server (``PyodideEngineClient.patchCosts`` rejects)."""
        from typehaus.cli.prices import load_prices
        from typehaus.server.space_summary import build_space_summary
        from typehaus.takeoff.bom import bill_of_materials
        from typehaus.takeoff.costs import CostsState, costs_payload, load_costs

        if self.model is None:
            return {}
        try:
            prices = load_prices(self.house_dir)
            state = load_costs(self.house_dir)
        except ValueError:
            # A malformed hand-edited file degrades to the empty state offline; the server
            # path is where the loud 400 with the offending key lives.
            prices, state = None, CostsState()
        # Same $/sf denominators as the served path (server/costs_api.py) — the offline
        # surface must not show a different estimate from the same house.
        summary = build_space_summary(self.model)["overall"]
        areas = {"conditioned": summary["conditioned_sf"], "gross": summary["gross_sf"]}
        return costs_payload(bill_of_materials(self.model), prices, state, areas)

    def detail_index(self) -> list[dict[str, Any]]:
        from typehaus.emit.draw.details import detail_index

        if self.model is None:
            return []
        return detail_index(self.model)

    def detail_payload(self, key: str) -> dict[str, Any] | None:
        from typehaus.emit.draw.details import detail_payload

        if self.model is None:
            return None
        return detail_payload(self.model, key)

    def glb_bytes(self) -> bytes:
        from typehaus.emit.gltf.emitter import emit_glb

        if self.model is None:
            raise RequiresLocalInstall("model does not resolve — nothing to render")
        out = Path("/tmp/offline_model.glb")
        emit_glb(self.model, out)
        return out.read_bytes()

    # --- optional IFC extension (loaded on demand from the packaged ext tarball) -----------
    def enable_ifc(self) -> None:
        """Assert a *real* ifcopenshell is importable before an IFC export is attempted.

        The worker unpacks ``typehaus-ifc-ext.tar`` (the ``typehaus/emit/ifc`` sources excluded
        from the core bundle) onto sys.path and, when configured, installs an ifcopenshell-wasm
        wheel — which then replaces the blocking stub in ``sys.modules``. If no real module is
        present we raise a precise, documented degradation rather than letting the stub raise a
        generic error deep inside the emitter."""
        mod = sys.modules.get("ifcopenshell")
        if mod is None or getattr(mod, "__typehaus_stub__", False):
            raise RequiresLocalInstall(
                "IFC export needs the ifcopenshell-wasm module, which is not bundled in this "
                "build. The engine's IFC emitter sources are unpacked and ready — supply an "
                "ifcopenshell-wasm wheel (ifcWasmUrl) or run `haus serve` locally for IFC export."
            )

    def ifc_bytes(self, lod: str = "core") -> bytes:
        from typehaus.emit.ifc import emit_ifc

        if self.model is None:
            raise RequiresLocalInstall("model does not resolve — nothing to export")
        out = Path("/tmp/offline_model.ifc")
        emit_ifc(self.model, out, lod=lod)
        return out.read_bytes()


ENGINE = OfflineEngine()
