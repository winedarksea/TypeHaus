"""Plan loader — location-independent house import + dialect lint + provenance (→ 10, → 02).

A house is *any* directory containing ``plan/manifest.py`` (+ ``brief.md``,
``preferences.toml``); the engine never assumes it sits inside the monorepo (#17).
"""

from __future__ import annotations

import ast
import hashlib
import importlib.util
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from typehaus.findings import Finding, Severity, SourceLoc
from typehaus.model.plan import PlanModel
from typehaus.source.dialect import (
    is_editable,
    lint_source,
    missing_uid_findings,
)
from typehaus.source.provenance import Provenance, scan_provenance


@dataclass
class PlanMeta:
    """Manifest metadata readable via the dialect path *without importing* (#31)."""

    format_version: int
    requires_engine: str


@dataclass
class LoadResult:
    plan: PlanModel | None
    findings: list[Finding] = field(default_factory=list)
    provenance: Provenance = field(default_factory=Provenance)
    content_hash: str = ""
    # Sub-stage timings in milliseconds (Phase 0 instrumentation): lint, import, hash.
    timings: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.plan is not None and not any(
            f.severity is Severity.ERROR for f in self.findings
        )


def editable_files(house_dir: Path) -> list[Path]:
    plan_dir = house_dir / "plan"
    return sorted(
        p for p in plan_dir.rglob("*.py")
        if p.name != "manifest.py" and is_editable(p.read_text())
    )


def read_meta(house_dir: Path) -> PlanMeta:
    """Read format_version / requires_engine from manifest.py via AST — no import (#31)."""
    manifest = house_dir / "plan" / "manifest.py"
    tree = ast.parse(manifest.read_text(), filename=str(manifest))
    fmt = 1
    req = ">=0,<1"
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and isinstance(node.value, ast.Constant):
                if target.id == "format_version" and isinstance(node.value.value, int):
                    fmt = node.value.value
                elif target.id == "requires_engine" and isinstance(node.value.value, str):
                    req = node.value.value
    return PlanMeta(format_version=fmt, requires_engine=req)


def _content_hash(house_dir: Path) -> str:
    h = hashlib.sha256()
    for p in sorted((house_dir / "plan").rglob("*.py")):
        h.update(p.relative_to(house_dir).as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()[:16]


def lint_only(house_dir: Path) -> list[Finding]:
    """Parse-only inspect path (``haus build --inspect``): never imports params/ (#17)."""
    findings: list[Finding] = []
    for f in editable_files(house_dir):
        rel = f.relative_to(house_dir).as_posix()
        src = f.read_text()
        findings.extend(lint_source(rel, src))
        findings.extend(missing_uid_findings(rel, src))
    return findings


# Per-file scan cache: absolute path → (content sha, lint+uid findings, provenance pairs).
# The libcst lint + provenance scan is ~98% of rebuild cost (Phase 0) and depends *only* on
# that file's exact bytes, so a rebuild after a one-file edit re-scans just the changed file
# and replays the rest from cache. Source stays the ground truth — the cache key is the file
# content itself, so a stale entry can never be served.
_SCAN_CACHE: dict[str, tuple[str, list[Finding], list[tuple[str, "SourceLoc"]]]] = {}


def _scan_file(rel: str, src: str) -> tuple[list[Finding], list[tuple[str, SourceLoc]]]:
    import libcst as cst

    # Parse + wrap once; the three scans share the resolved PositionProvider (Phase 0).
    wrapper = cst.MetadataWrapper(cst.parse_module(src))
    findings: list[Finding] = []
    findings.extend(lint_source(rel, src, wrapper))
    findings.extend(missing_uid_findings(rel, src, wrapper))
    file_prov = Provenance()
    scan_provenance(rel, src, file_prov, wrapper)
    return findings, file_prov.items()


def load_plan(house_dir: Path) -> LoadResult:
    """Full load: dialect lint (all editable files) → import manifest → PlanModel.

    Import runs the plan package normally (fast path); the libcst path builds the
    provenance map. A consistency check asserts both views agree on tag set.
    """
    house_dir = house_dir.resolve()
    findings: list[Finding] = []
    prov = Provenance()
    timings: dict[str, float] = {}

    t0 = time.perf_counter()
    live_keys: set[str] = set()
    for f in editable_files(house_dir):
        rel = f.relative_to(house_dir).as_posix()
        src = f.read_text()
        key = str(f)
        live_keys.add(key)
        sha = hashlib.sha256(src.encode()).hexdigest()
        cached = _SCAN_CACHE.get(key)
        if cached is not None and cached[0] == sha:
            file_findings, prov_pairs = cached[1], cached[2]
        else:
            file_findings, prov_pairs = _scan_file(rel, src)
            _SCAN_CACHE[key] = (sha, file_findings, prov_pairs)
        findings.extend(file_findings)
        for tag, loc in prov_pairs:
            prov.add(tag, loc)
    # Evict entries for files that no longer exist (renames/deletes) to bound the cache.
    for stale in [k for k in _SCAN_CACHE if k not in live_keys and k.startswith(str(house_dir))]:
        del _SCAN_CACHE[stale]
    timings["lint_provenance"] = (time.perf_counter() - t0) * 1000.0

    if any(f.severity is Severity.ERROR for f in findings):
        return LoadResult(plan=None, findings=findings, provenance=prov, timings=timings)

    t0 = time.perf_counter()
    plan = _import_manifest(house_dir, findings)
    if plan is not None:
        from typehaus.source.imported_furniture import load_imported_furniture

        plan = load_imported_furniture(house_dir, plan, findings)
    timings["import"] = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    content_hash = _content_hash(house_dir)
    timings["content_hash"] = (time.perf_counter() - t0) * 1000.0

    result = LoadResult(
        plan=plan, findings=findings, provenance=prov, content_hash=content_hash,
        timings=timings,
    )
    if plan is not None:
        _consistency_check(plan, prov, findings)
    return result


def _import_manifest(house_dir: Path, findings: list[Finding]) -> PlanModel | None:
    """Import ``plan/manifest.py`` and read its module-level ``PLAN: PlanModel``."""
    manifest = house_dir / "plan" / "manifest.py"
    if not manifest.exists():
        findings.append(
            Finding(
                severity=Severity.ERROR,
                check_id="loader.no_manifest",
                message=f"no plan/manifest.py under {house_dir}",
                source_loc=SourceLoc(file="plan/manifest.py", line=1),
            )
        )
        return None
    # Make the house dir importable so `plan` and `params` resolve.
    added = str(house_dir)
    inserted = added not in sys.path
    if inserted:
        sys.path.insert(0, added)
    # A plan may reference the shared ``library`` package (the community seam). In a
    # pip-installed setup it is already importable; in the monorepo (or any checkout that
    # keeps houses beside a ``library/``) it sits at a directory above the house. Discover
    # it by walking up without assuming the engine lives in the monorepo (#17).
    lib_root = _find_library_root(house_dir)
    lib_added = lib_root is not None and str(lib_root) not in sys.path
    if lib_added:
        sys.path.insert(0, str(lib_root))
    try:
        for mod in [m for m in sys.modules if m == "plan" or m.startswith("plan.")]:
            del sys.modules[mod]
        spec = importlib.util.spec_from_file_location("plan.manifest", manifest)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules["plan.manifest"] = module
        spec.loader.exec_module(module)
        plan = getattr(module, "PLAN", None)
        if not isinstance(plan, PlanModel):
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    check_id="loader.no_plan",
                    message="manifest.py must define PLAN: PlanModel at module level",
                    source_loc=SourceLoc(file="plan/manifest.py", line=1),
                )
            )
            return None
        return plan
    except Exception as exc:  # noqa: BLE001 - surfaced as a finding
        findings.append(
            Finding(
                severity=Severity.ERROR,
                check_id="loader.import_error",
                message=f"error importing plan: {exc}",
                source_loc=SourceLoc(file="plan/manifest.py", line=1),
            )
        )
        return None
    finally:
        if inserted:
            sys.path.remove(added)
        if lib_added and lib_root is not None:
            sys.path.remove(str(lib_root))


def _find_library_root(house_dir: Path) -> Path | None:
    """Walk up from ``house_dir`` to find the directory *containing* a ``library`` package.

    Returns the parent that should go on ``sys.path`` so ``import library`` resolves, or
    ``None`` if no checkout-local ``library/`` exists (a pip-installed one needs no help).
    """
    for parent in [house_dir, *house_dir.parents]:
        if (parent / "library" / "__init__.py").is_file():
            return parent
    return None


def _consistency_check(plan: PlanModel, prov: Provenance, findings: list[Finding]) -> None:
    """Assert the import view and the libcst view agree on the authored tag set."""
    import_tags = {el.tag for el in plan.all_elements()}
    # Provenance may legitimately hold library/storey tags too; only warn on plan
    # elements the libcst path never saw (params/-generated ones are exempt).
    prov_tags = prov.tags()
    missing = import_tags - prov_tags
    generated = _params_generated_tags(plan)
    for tag in sorted(missing - generated):
        findings.append(
            Finding(
                severity=Severity.WARN,
                check_id="loader.provenance_gap",
                message=f"element {tag} has no editable-source location (params-generated?)",
                element_tags=(tag,),
            )
        )


def _params_generated_tags(plan: PlanModel) -> set[str]:
    # Elements with forked_from or produced by params carry no editable location;
    # M1 treats any element not found in provenance as generated (warn only).
    return set()
