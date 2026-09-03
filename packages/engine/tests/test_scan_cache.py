"""The libcst scan cache, persisted to disk (``loader._read_disk_cache`` / ``_write_disk_cache``).

The in-process ``_SCAN_CACHE`` only ever helped ``haus serve``. Every one-shot CLI run —
build, check, fmt, takeoff, tasks — started cold and paid the full libcst scan of every
editable file, which on catlin was the whole of the build's non-IFC time. Persisting it to
``<house>/out/.scan-cache.json`` makes the second invocation as warm as the second rebuild.

What has to hold for that to be safe is what this module pins: the cache is keyed on file
*content*, so an edit can never be served a stale entry; it is keyed on the *engine* too,
so yesterday's lint rules cannot be replayed by today's; and every failure to read or write
it costs a re-scan and nothing more — a read-only ``out/`` must never fail a build.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from _helpers import HOUSE_IGNORE, STARTER

from typehaus.source import loader


@pytest.fixture
def house(tmp_path: Path) -> Path:
    """A sandbox copy of the starter house — small, and safe to edit."""
    import shutil

    dest = tmp_path / "starter"
    shutil.copytree(STARTER, dest, ignore=HOUSE_IGNORE)
    return dest


@pytest.fixture(autouse=True)
def _cold_process():
    """Clear the in-process dict so each test exercises the *disk* path, not the memory one."""
    loader._SCAN_CACHE.clear()
    yield
    loader._SCAN_CACHE.clear()


def _cache_file(house: Path) -> Path:
    return house / loader._CACHE_RELPATH


def _load(house: Path):
    loader._SCAN_CACHE.clear()
    return loader.load_plan(house)


def test_the_first_load_writes_a_cache_the_second_reads(house: Path):
    first = _load(house)
    assert first.plan is not None
    assert _cache_file(house).exists(), "a successful load persists its scan"

    second = _load(house)
    assert second.plan is not None
    # Same findings, same provenance — the cache is transparent, not merely fast.
    assert [f.model_dump() for f in second.findings] == [f.model_dump() for f in first.findings]
    assert second.provenance.items() == first.provenance.items()


def test_an_edit_is_never_served_a_stale_entry(house: Path):
    """The safety argument, exercised: the key is the content sha, so edited bytes miss."""
    _load(house)
    target = next(f for f in loader.editable_files(house))
    target.write_text(target.read_text() + "\n# a comment the cache has never seen\n")

    after = _load(house)
    assert after.plan is not None
    entry = json.loads(_cache_file(house).read_text())["files"][
        target.relative_to(house).as_posix()]
    import hashlib

    assert entry["sha"] == hashlib.sha256(target.read_text().encode()).hexdigest()


def test_a_cache_from_a_different_engine_is_ignored_whole(house: Path):
    """Lint rules and the provenance scanner are engine code — a cache written by different
    ones describes different rules, and replaying it would report yesterday's findings."""
    _load(house)
    raw = json.loads(_cache_file(house).read_text())
    raw["scanner"] = "not-this-engine"
    _cache_file(house).write_text(json.dumps(raw))

    assert loader._read_disk_cache(house) == {}
    result = _load(house)  # still correct, just cold
    assert result.plan is not None
    # And the stale file is replaced rather than left to be re-rejected forever.
    assert json.loads(_cache_file(house).read_text())["scanner"] == loader._scanner_identity()


def test_a_format_bump_is_ignored_whole(house: Path):
    _load(house)
    raw = json.loads(_cache_file(house).read_text())
    raw["format"] = loader._CACHE_FORMAT + 1
    _cache_file(house).write_text(json.dumps(raw))
    assert loader._read_disk_cache(house) == {}


@pytest.mark.parametrize("content", ["", "{", "null", "[]", '{"format": 1}',
                                     '{"format": 1, "scanner": "x", "files": "notadict"}'])
def test_a_corrupt_cache_costs_a_rescan_and_nothing_else(house: Path, content: str):
    """Best-effort in both directions: garbage on disk must degrade to a full scan."""
    _cache_file(house).parent.mkdir(parents=True, exist_ok=True)
    _cache_file(house).write_text(content)

    assert loader._read_disk_cache(house) == {}
    result = _load(house)
    assert result.plan is not None


def test_an_unwritable_out_directory_does_not_fail_the_load(house: Path, monkeypatch):
    """A read-only checkout, a full disk, a sandbox with no write permission — a cache is a
    cache. This is the failure mode that would otherwise turn an optimisation into an
    outage."""
    def _boom(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(Path, "write_text", _boom)
    result = loader.load_plan(house)
    assert result.plan is not None
    assert not _cache_file(house).exists()


def test_a_deleted_file_is_evicted_from_the_cache(house: Path):
    """Renames and deletes must not accumulate: the persisted set is the live set."""
    _load(house)
    files = list(loader.editable_files(house))
    doomed = next(f for f in files if f.name != "manifest.py")
    relative = doomed.relative_to(house).as_posix()
    assert relative in json.loads(_cache_file(house).read_text())["files"]

    doomed.unlink()
    _load(house)
    assert relative not in json.loads(_cache_file(house).read_text())["files"]


def test_the_scanner_identity_moves_with_the_lint_rules(monkeypatch):
    """Engine *version* alone is too coarse — it does not move between edits to dialect.py,
    which is exactly when a cache most needs discarding."""
    before = loader._scanner_identity()
    from typehaus.source import dialect

    monkeypatch.setattr(dialect, "__file__", str(Path(dialect.__file__).with_name("provenance.py")))
    assert loader._scanner_identity() != before


def test_the_scanner_identity_moves_with_the_constructor_allowlist(monkeypatch):
    """Registering a new model type must discard the cache — and once did not.

    ``dialect.lint_source`` rejects any call whose name is not in
    ``model.registry.constructor_names()``, but the identity hashed only ``dialect.py`` and
    ``provenance.py``. So adding ``ConcreteSpec`` to the registry changed what the linter
    accepts WITHOUT changing this identity, and the cache went on serving
    ``'ConcreteSpec' is not a registered element/quantity/library constructor`` against
    source that was by then perfectly legal.

    What made it expensive to diagnose: ``haus build --inspect`` lints fresh and passed on
    the very same file, while ``haus check`` failed on it, with correct line numbers.
    """
    from typehaus.model.registry import _CONSTRUCTORS

    before = loader._scanner_identity()
    _CONSTRUCTORS["_TestOnlySpec"] = object
    try:
        assert loader._scanner_identity() != before
    finally:
        del _CONSTRUCTORS["_TestOnlySpec"]
    assert loader._scanner_identity() == before
