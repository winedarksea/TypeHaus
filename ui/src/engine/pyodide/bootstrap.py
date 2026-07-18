"""In-pyodide engine bootstrap for the degraded offline PWA (→ 40 WP4.2, gate outcome b).

Runs once inside the Web Worker after the engine tarball is unpacked onto sys.path. Stubs the
three wasm-hostile deps (libcst, ifcopenshell, pyproj) so importing ``typehaus.source`` (whose
package __init__ pulls writeback → libcst) succeeds; the compute path — load_plan, resolve,
model_to_dict, checks, emit_glb — needs none of them. Any code path that actually touches a
stubbed module raises ``RequiresLocalInstall``, which the worker maps to a clear UI error.
"""

from __future__ import annotations

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
    """A stub whose every use raises — for deps reached only at call time (ifc emit)."""
    if name in sys.modules:
        return
    mod = types.ModuleType(name)

    def _blocked(*_a: Any, **_k: Any) -> Any:
        raise RequiresLocalInstall(
            f"{name} is not available in the offline PWA — run `haus serve` locally"
        )

    mod.__getattr__ = lambda _attr: _blocked  # type: ignore[attr-defined]
    sys.modules[name] = mod


_install_libcst_stub()
for _dep in ("ifcopenshell", "pyproj"):
    _install_blocking_stub(_dep)
for _sub in ("ifcopenshell.api", "ifcopenshell.guid"):
    sys.modules.setdefault(_sub, sys.modules["ifcopenshell"])


class OfflineEngine:
    """One loaded house + its resolved model, recomputed on each loadHouse (→ server/state.py)."""

    def __init__(self) -> None:
        self.house_dir: Path | None = None
        self.model: Any = None
        self.findings: list[Any] = []
        self.provenance: Any = None
        self.ok: bool = False
        self._revision: str = "0"

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
        return self.rebuild()

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
        self._revision = _revision_of(self.house_dir)
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
        from typehaus.server.model_json import model_to_dict

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
        )
        payload["ok"] = self.ok
        return payload

    def findings_json(self) -> list[dict[str, Any]]:
        return [f.model_dump(mode="json") for f in self.findings]

    def glb_bytes(self) -> bytes:
        from typehaus.emit.gltf.emitter import emit_glb

        if self.model is None:
            raise RequiresLocalInstall("model does not resolve — nothing to render")
        out = Path("/tmp/offline_model.glb")
        emit_glb(self.model, out)
        return out.read_bytes()


def _revision_of(house_dir: Path) -> str:
    import hashlib

    h = hashlib.sha256()
    for p in sorted(house_dir.rglob("*")):
        if p.is_file():
            h.update(p.relative_to(house_dir).as_posix().encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


ENGINE = OfflineEngine()
