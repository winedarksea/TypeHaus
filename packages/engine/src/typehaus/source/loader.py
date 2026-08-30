"""Plan loader — location-independent house import + dialect lint + provenance (→ 10, → 02).

A house is *any* directory containing ``plan/manifest.py`` (+ ``brief.md``,
``preferences.toml``); the engine never assumes it sits inside the monorepo (#17).
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import json
import os
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import ValidationError

from typehaus.findings import Finding, Severity, SourceLoc
from typehaus.model.base import Element, set_construction_observer
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
    # Project-local catalog data changes resolution and must therefore invalidate the
    # same optimistic-concurrency revision as authored Python source.
    placeables = house_dir / "assets" / "placeables.json"
    if placeables.exists():
        h.update(placeables.relative_to(house_dir).as_posix().encode())
        h.update(placeables.read_bytes())
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
_SCAN_CACHE: dict[str, tuple[str, list[Finding], list[tuple[str, SourceLoc]]]] = {}


# ---------------------------------------------------------------------------------------
# Disk-backed scan cache.
#
# ``_SCAN_CACHE`` above only helps a *long-lived* process (``haus serve``). Every one-shot
# CLI invocation — build, check, fmt, takeoff, tasks — starts cold and pays the full libcst
# scan: 4.9 ms warm against up to 7.3 s cold on catlin, which was the whole of the build's
# non-IFC time. This mirrors the dict to one JSON file per house so the second invocation is
# as warm as the second rebuild.
#
# The safety argument is the in-memory one, unchanged: the key is the file's own content
# SHA, so a stale entry can never be served — an edited file simply misses. What disk adds
# is an *engine* axis. The lint rules and the provenance scanner are engine code, so a cache
# written by a different engine describes different rules; the file header pins the engine
# version plus a hash of those modules' source, and any mismatch discards the whole file.
#
# Every read and write is best-effort. A corrupt, unreadable, or unwritable cache must cost
# a full scan and nothing else — a read-only ``out/`` may never fail a build.
_CACHE_FORMAT = 1
_CACHE_RELPATH = Path("out") / ".scan-cache.json"

# What one file's scan is worth remembering: its content sha, its findings, its provenance.
ScanEntry = tuple[str, list[Finding], list[tuple[str, SourceLoc]]]


def _scanner_identity() -> str:
    """Engine version + a hash of the modules whose output is being cached.

    Version alone is too coarse during development, where the engine version does not move
    between edits to ``dialect.py``; the source hash is what actually invalidates a cache
    written by yesterday's lint rules.
    """
    from typehaus import _meta
    from typehaus.source import dialect, provenance

    h = hashlib.sha256(_meta.engine_version().encode())
    for module in (dialect, provenance):
        source = getattr(module, "__file__", None)
        if source is None:  # pragma: no cover - namespace/zip import
            return "unpinnable"
        try:
            h.update(Path(source).read_bytes())
        except OSError:  # pragma: no cover - unreadable engine source
            return "unpinnable"
    return h.hexdigest()[:16]


def _read_disk_cache(house_dir: Path) -> dict[str, ScanEntry]:
    """Load the house's persisted scan cache, or ``{}`` for any reason at all."""
    path = house_dir / _CACHE_RELPATH
    try:
        raw = json.loads(path.read_text())
    except (OSError, ValueError):
        return {}
    if not isinstance(raw, dict) or raw.get("format") != _CACHE_FORMAT:
        return {}
    if raw.get("scanner") != _scanner_identity():
        return {}
    out: dict[str, ScanEntry] = {}
    try:
        for rel, entry in raw["files"].items():
            findings = [Finding.model_validate(f) for f in entry["findings"]]
            prov = [(tag, SourceLoc.model_validate(loc)) for tag, loc in entry["provenance"]]
            out[str(house_dir / rel)] = (entry["sha"], findings, prov)
    except (KeyError, TypeError, ValidationError):
        return {}
    return out


def _write_disk_cache(house_dir: Path, entries: dict[str, ScanEntry]) -> None:
    """Persist the house's scan results. Silent on every failure — this is a cache."""
    path = house_dir / _CACHE_RELPATH
    payload = {
        "format": _CACHE_FORMAT,
        "scanner": _scanner_identity(),
        "files": {
            Path(key).relative_to(house_dir).as_posix(): {
                "sha": sha,
                "findings": [f.model_dump(mode="json") for f in findings],
                "provenance": [[tag, loc.model_dump(mode="json")] for tag, loc in prov],
            }
            for key, (sha, findings, prov) in entries.items()
        },
    }
    # Write-and-rename so a concurrent reader never sees a half-written file, and a crash
    # mid-write leaves the previous cache intact rather than a corrupt one. The pid in the
    # temp name keeps two houses (or two workers) from clobbering each other's rename.
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(json.dumps(payload))
        tmp.replace(path)
    except (OSError, ValueError, TypeError):
        with contextlib.suppress(OSError):
            tmp.unlink(missing_ok=True)


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


@contextmanager
def _capture_authorship(house_dir: Path) -> Iterator[dict[str, SourceLoc]]:
    """Runtime authorship capture: while active, every :class:`Element` constructed
    records the innermost house-local stack frame — exact ``file:line`` even for tags
    built from f-strings/variables in loops, which no static scan can see. The captures
    become *read-only* provenance (``Provenance.add_generated``): shown in the UI as
    "defined in params/… — edit in code", never a writeback destination (the coordinator
    routes exclusively through ``editable_files()``).

    Uses the module-global observer in ``typehaus.model.base`` — the same class of
    process-wide global as this module's ``sys.path`` mutation; rebuilds are serialized,
    so a single active capture is the operating assumption.
    """
    captured: dict[str, SourceLoc] = {}
    # co_filename → house-relative posix path (or None if outside); resolved once per file.
    rel_cache: dict[str, str | None] = {}

    def _rel(co_filename: str) -> str | None:
        if co_filename not in rel_cache:
            p = Path(co_filename)
            if not p.is_absolute():
                rel_cache[co_filename] = None
            else:
                if not p.is_relative_to(house_dir):
                    p = p.resolve()
                rel_cache[co_filename] = (
                    p.relative_to(house_dir).as_posix()
                    if p.is_relative_to(house_dir) else None
                )
        return rel_cache[co_filename]

    def observer(el: Element) -> None:
        if not el.tag:
            return
        depth = 1
        while True:
            try:
                frame = sys._getframe(depth)
            except ValueError:
                return
            rel = _rel(frame.f_code.co_filename)
            if rel is not None:
                captured[el.tag] = SourceLoc(file=rel, line=frame.f_lineno)
                return
            depth += 1

    set_construction_observer(observer)
    try:
        yield captured
    finally:
        set_construction_observer(None)


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
    # The in-process dict stays in front of the disk file: ``haus serve`` rebuilds on every
    # keystroke-ish save and must not read JSON each time. Disk is consulted only for keys
    # this process has not already scanned, which for a one-shot CLI run is all of them.
    on_disk: dict[str, ScanEntry] | None = None
    scanned_any = False
    for f in editable_files(house_dir):
        rel = f.relative_to(house_dir).as_posix()
        src = f.read_text()
        key = str(f)
        live_keys.add(key)
        sha = hashlib.sha256(src.encode()).hexdigest()
        cached = _SCAN_CACHE.get(key)
        if cached is None or cached[0] != sha:
            if on_disk is None:
                on_disk = _read_disk_cache(house_dir)
            from_disk = on_disk.get(key)
            cached = from_disk if from_disk is not None and from_disk[0] == sha else None
        if cached is not None:
            file_findings, prov_pairs = cached[1], cached[2]
        else:
            file_findings, prov_pairs = _scan_file(rel, src)
            scanned_any = True
        _SCAN_CACHE[key] = (sha, file_findings, prov_pairs)
        findings.extend(file_findings)
        for tag, loc in prov_pairs:
            prov.add(tag, loc)
    # Evict entries for files that no longer exist (renames/deletes) to bound the cache.
    house_entries = {k: v for k, v in _SCAN_CACHE.items() if k in live_keys}
    for stale in [k for k in _SCAN_CACHE if k not in live_keys and k.startswith(str(house_dir))]:
        del _SCAN_CACHE[stale]
    # Rewrite only when the file on disk is actually out of date: something re-scanned, or
    # the house gained/lost a file. A cold run over an unchanged house reads the cache and
    # writes nothing, and a warm ``haus serve`` rebuild touches disk at all only when a save
    # invalidated an entry.
    if scanned_any or (on_disk is not None and set(on_disk) != set(house_entries)):
        _write_disk_cache(house_dir, house_entries)
    timings["lint_provenance"] = (time.perf_counter() - t0) * 1000.0

    if any(f.severity is Severity.ERROR for f in findings):
        return LoadResult(plan=None, findings=findings, provenance=prov, timings=timings)

    t0 = time.perf_counter()
    # Capture covers only the manifest import — furniture/placeable loaders below build
    # engine-side wrappers whose authorship is the JSON/GLB asset, not a stack frame.
    with _capture_authorship(house_dir) as captured:
        plan = _import_manifest(house_dir, findings)
    for tag, loc in captured.items():
        prov.add_generated(tag, loc)
    if plan is not None:
        from typehaus.source.imported_furniture import load_imported_furniture
        from typehaus.source.placeables import load_project_placeables

        plan = load_imported_furniture(house_dir, plan, findings)
        plan = load_project_placeables(house_dir, plan, findings)
    timings["import"] = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    content_hash = _content_hash(house_dir)
    timings["content_hash"] = (time.perf_counter() - t0) * 1000.0

    result = LoadResult(
        plan=plan, findings=findings, provenance=prov, content_hash=content_hash,
        timings=timings,
    )
    if plan is not None:
        _consistency_check(plan, prov, findings, house_dir)
    return result


# Importing a house mutates process-global state — ``sys.path`` and the ``plan``/``params``
# entries of ``sys.modules``, which are purged wholesale below. Two loads running at once
# (the server's background rebuild alongside a check job, or two ProjectStates in one
# process) would tear each other's module tree down mid-import, surfacing as a spurious
# ``loader.import_error`` KeyError on a half-imported submodule. Serialize the whole import.
_IMPORT_LOCK = threading.RLock()


def _import_manifest(house_dir: Path, findings: list[Finding]) -> PlanModel | None:
    """Import ``plan/manifest.py`` and read its module-level ``PLAN: PlanModel``."""
    with _IMPORT_LOCK:
        return _import_manifest_locked(house_dir, findings)


def _import_manifest_locked(house_dir: Path, findings: list[Finding]) -> PlanModel | None:
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
        # Drop both house-local module trees: a cached ``params`` module would not only go
        # stale across edits, its module-level elements would never be re-constructed on a
        # rebuild — silently starving the runtime authorship capture above.
        # ``library`` is purged with them: it is a *house-visible* package too (plans do
        # `from library import ...`), and a cached copy meant an edit to a shared catalog
        # was invisible until the process restarted — the same stale-edit hazard the
        # plan/params purge exists to prevent.
        for mod in [m for m in sys.modules
                    if m in ("plan", "params", "library")
                    or m.startswith(("plan.", "params.", "library."))]:
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
                fix_hint=_import_error_hint(exc),
            )
        )
        return None
    finally:
        if inserted:
            sys.path.remove(added)
        if lib_added and lib_root is not None:
            sys.path.remove(str(lib_root))


def _import_error_hint(exc: BaseException) -> str | None:
    """Name the plan-source cause behind pydantic failures whose message hides it.

    The one that matters: a tuple-typed field handed a bare element instead of a 1-tuple.
    pydantic iterates the model looking for members, so **every field of that element**
    comes back as its own ``model_type`` error with an ``('a', 1)`` input value, and the
    actual cause — a single missing trailing comma — appears nowhere in the N-error wall of
    text. The editable dialect cannot catch it (it does not know field types), so the hint
    lands here, where the exception is.
    """
    errors = getattr(exc, "errors", None)
    if not callable(errors):
        return None
    try:
        rows = list(errors())
    except Exception:  # noqa: BLE001 - a hint is never worth raising over
        return None
    if len(rows) < 2 or any(r.get("type") != "model_type" for r in rows):
        return None
    locs = {r["loc"][0] for r in rows if len(r.get("loc", ())) >= 2}
    indices = {r["loc"][1] for r in rows if len(r.get("loc", ())) >= 2}
    if len(locs) != 1 or not all(isinstance(i, int) for i in indices):
        return None
    field = next(iter(locs))
    return (f"'{field}' is a tuple-typed field given one bare element — a 1-tuple needs its "
            f"trailing comma: {field}=(X(...),). The {len(rows)} errors above are its "
            f"fields, not {len(rows)} separate problems.")


def _find_library_root(house_dir: Path) -> Path | None:
    """Walk up from ``house_dir`` to find the directory *containing* a ``library`` package.

    Returns the parent that should go on ``sys.path`` so ``import library`` resolves, or
    ``None`` if no checkout-local ``library/`` exists (a pip-installed one needs no help).
    """
    for parent in [house_dir, *house_dir.parents]:
        if (parent / "library" / "__init__.py").is_file():
            return parent
    # Installed from a wheel there is no checkout to walk: `library` ships beside
    # `typehaus` in site-packages, so it is already importable and needs no sys.path help.
    # Confirm it really is, so a broken install fails here rather than inside the house's
    # own `from library import ...`.
    try:
        import importlib.resources

        if importlib.resources.files("library").joinpath("__init__.py").is_file():
            return None
    except (ImportError, ModuleNotFoundError, TypeError):
        pass
    return None


# Element kinds the UI can move/edit (drag, rehost, retype, delete). Their edits POST a
# writeback op, which the coordinator can only apply to a `# haus: editable` source file
# (loader.editable_files). If such an instance is authored in a non-editable module, the
# edit fails at commit with no source change — the silent "move didn't save" bug. We make
# that a hard load-time ERROR so the house can never contain an un-editable movable element.
_UI_EDITABLE_KINDS = frozenset({
    "Furniture", "Fixture", "Appliance", "Equipment", "Register", "ElectricalDevice",
    "Door", "Window", "RoughOpening", "Wall", "Room", "Node", "Stair", "Railing",
    # Not dragged directly, but written by the same path: a fixture drag emits follower
    # patches for the sleeve and drain run under its flange (`macros._drain_follower_ops`),
    # so authoring either in a non-editable module breaks the *fixture's* move too.
    "SleevePenetration", "PipeRun",
})


def _noneditable_authored(house_dir: Path, kind: str, tag: str) -> bool:
    """True if a `kind`/`tag` constructor is written literally in a non-editable plan
    module (excluding manifest.py). Distinguishes an element *authored* in a file that
    forgot the `# haus: editable` header (the writeback-breaking bug) from one *generated*
    by a params/ math module (legitimately sourceless — no constructor to write back to)."""
    from typehaus.source.writeback import read_element_fields
    plan_dir = house_dir / "plan"
    if not plan_dir.is_dir():
        return False
    for p in plan_dir.rglob("*.py"):
        if p.name == "manifest.py":
            continue
        src = p.read_text()
        if is_editable(src):
            continue
        if read_element_fields(src, kind, tag) is not None:
            return True
    return False


def _identity_check(authored: list, findings: list[Finding]) -> None:
    """uid and tag uniqueness, enforced at load time as hard errors.

    `haus build` never runs the checks tier, so `integrity.uid_unique` — until now the only
    uniqueness rule in the engine — was invisible on the build path: a hand-minted colliding
    uid built green and shipped two elements sharing one derived IFC GlobalId. Tags had no
    rule at all; the dict comprehension below this call silently kept the last of a
    duplicate pair, so half the collision simply vanished from every downstream view.
    Both are ERROR here, and the checks-tier rule stays as the mirror.
    """
    by_uid: dict[str, list[str]] = {}
    by_tag: dict[str, int] = {}
    for el in authored:
        by_tag[el.tag] = by_tag.get(el.tag, 0) + 1
        if el.uid:
            by_uid.setdefault(el.uid, []).append(el.tag)
    for uid, tags in sorted(by_uid.items()):
        if len(tags) > 1:
            findings.append(Finding(
                severity=Severity.ERROR,
                check_id="loader.uid_unique",
                message=(f"uid {uid!r} is authored on {len(tags)} elements "
                         f"({', '.join(sorted(tags))})"),
                element_tags=tuple(sorted(tags)),
                fix_hint="never hand-write a uid — delete the duplicate and run `haus fmt` "
                         "to mint a fresh one",
            ))
    for tag, count in sorted(by_tag.items()):
        if count > 1:
            findings.append(Finding(
                severity=Severity.ERROR,
                check_id="loader.tag_unique",
                message=f"tag {tag!r} is authored on {count} elements",
                element_tags=(tag,),
                fix_hint="tags are the plan's addressing scheme; rename one of them",
            ))


def _consistency_check(
    plan: PlanModel, prov: Provenance, findings: list[Finding], house_dir: Path
) -> None:
    """Assert the import view and the libcst view agree on the authored tag set."""
    authored = list(plan.all_elements())
    _identity_check(authored, findings)
    elements = {el.tag: el for el in authored}
    # Provenance may legitimately hold library/storey tags too; only flag plan
    # elements the libcst path never saw. Runtime capture (add_generated) supplies a
    # read-only location for params-generated ones — those are fine, not findings.
    missing = set(elements) - prov.editable_tags()
    for tag in sorted(missing):
        el = elements[tag]
        # MRO walk: a FoundationWall(Wall) is as UI-movable as its base kind.
        movable = any(c.__name__ in _UI_EDITABLE_KINDS for c in type(el).__mro__)
        gen_loc = prov.location(tag)
        under_plan = gen_loc is not None and gen_loc.file.startswith("plan/")
        # A UI-movable element authored in a non-editable plan module is a hard error:
        # its drag/edit POSTs a writeback op the coordinator can't apply, so the move
        # silently fails to persist. Gate the rglob walk on the capture pointing under
        # plan/ (or being absent — e.g. a model_copy that bypassed capture).
        if (movable and (under_plan or gen_loc is None)
                and _noneditable_authored(house_dir, el.element_kind, tag)):
            findings.append(
                Finding(
                    severity=Severity.ERROR,
                    check_id="loader.uneditable_movable_element",
                    message=(
                        f"{el.element_kind} {tag} is UI-movable but authored in a non-editable "
                        f"source file; add the '# haus: editable' header to its module (or "
                        f"move the declaration into one) so edits can be written back"
                    ),
                    element_tags=(tag,),
                )
            )
        elif gen_loc is not None:
            # Captured authorship (params/ math, plan/views.py …): read-only provenance,
            # surfaced in the UI as "defined in <file> — edit in code". No finding.
            continue
        else:
            findings.append(
                Finding(
                    severity=Severity.WARN,
                    check_id="loader.provenance_gap",
                    message=f"element {tag} has no editable-source location (params-generated?)",
                    element_tags=(tag,),
                )
            )
