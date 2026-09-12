"""``haus handoff`` — the bundle a PE gets, and the seal form that comes back.

Three assertions here are doing unusual work:

* :func:`test_the_scaffold_is_refused_until_a_person_fills_it_in` is the whole safety
  property. The engine generates a file shaped exactly like a seal register; the only thing
  stopping a copy of it from reading as forty stamps is that the loader refuses a
  placeholder, and it has to refuse naming the field.
* :func:`test_a_filled_scaffold_seals_every_computed_item` is the other half: the form has
  to actually work once filled, with fingerprints that match what the CLI prints, or the
  scaffold is an elaborate way to waste a professional's afternoon.
* :func:`test_the_bundle_is_byte_deterministic` is what makes the manifest mean anything. A
  changed sha256 has to be a changed model rather than a re-run.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest
from _helpers import CATLIN

REPO = Path(__file__).resolve().parents[3]

pytestmark = pytest.mark.slow


def _run(house: Path, out: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(REPO / ".venv" / "bin" / "haus"), "handoff", str(house),
         "--out", str(out), *extra],
        capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "SOURCE_DATE_EPOCH": "1700000000",
             "HOME": str(out.parent)})


@pytest.fixture(scope="module")
def bundle(tmp_path_factory):
    """The real bundle, once. Slow — it resolves the house and writes a PDF."""
    out = tmp_path_factory.mktemp("handoff") / "bundle"
    result = _run(CATLIN, out, "--no-models")
    assert result.returncode == 0, result.stdout + result.stderr
    return out


# --- the shape of it ---------------------------------------------------------------------

def test_the_bundle_carries_the_five_things_a_reviewer_needs(bundle):
    assert (bundle / "README.md").is_file()
    assert (bundle / "MANIFEST.json").is_file()
    assert (bundle / "engineering.toml.draft").is_file()
    assert (bundle / "calcs" / "00-cover.md").is_file()
    assert (bundle / "calcs.pdf").is_file()
    assert list((bundle / "notes").glob("*.md"))


def test_only_the_notes_these_calculations_cite_are_copied(bundle):
    """A notes folder holding the whole design log buries the ones that verify the calcs."""
    copied = {path.name for path in (bundle / "notes").glob("*.md")}
    everything = {path.name for path in (CATLIN / "notes").glob("*.md")}
    assert copied < everything, "the whole notes folder was copied"
    assert "board_batten_girt_span.md" in copied
    # A note about a design decision, oracling nothing, must not be in a calc bundle.
    assert "interior_selections.md" not in copied


def test_the_readme_says_not_for_construction_and_names_the_model(bundle):
    readme = (bundle / "README.md").read_text()
    assert "NOT FOR CONSTRUCTION" in readme
    assert "Five minutes, in order" in readme
    # The content hash is the only thing that says WHICH model this is a calculation for.
    manifest = json.loads((bundle / "MANIFEST.json").read_text())
    assert manifest["files"]
    assert re.search(r"Model content hash \| `[0-9a-f]{8,}`", readme)


def test_the_manifest_hashes_every_file_it_ships(bundle):
    import hashlib

    manifest = json.loads((bundle / "MANIFEST.json").read_text())["files"]
    for name, digest in manifest.items():
        path = bundle / name
        assert path.is_file(), name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    assert "README.md" in manifest and "engineering.toml.draft" in manifest


def test_the_bundle_is_byte_deterministic(tmp_path):
    """Two runs, one model, identical hashes. Without this the manifest proves nothing."""
    first, second = tmp_path / "a", tmp_path / "b"
    for out in (first, second):
        assert _run(CATLIN, out, "--no-models", "--no-pdf").returncode == 0
    left = json.loads((first / "MANIFEST.json").read_text())["files"]
    right = json.loads((second / "MANIFEST.json").read_text())["files"]
    assert left == right


# --- the seal form -----------------------------------------------------------------------

def test_one_signoff_block_per_kind_and_deferred_ones_are_comments(bundle):
    """A PE stamps a SCOPE. Forty separate stamps is both wrong and expensive."""
    draft = (bundle / "engineering.toml.draft").read_text()
    live = re.findall(r"^\[\[signoff\]\]$", draft, re.MULTILINE)
    commented = re.findall(r"^# \[\[signoff\]\]$", draft, re.MULTILINE)
    assert live, "no signoff blocks at all"
    assert commented, "the deferred kinds must be written out but commented"
    # `column_support` is deferred: nothing to fingerprint, so nothing to pin, so a live
    # block would invite a stamp that can never satisfy --require-seal.
    assert "# id = \"column_support\"" in draft
    assert "DEFERRED" in draft


def test_the_scaffold_is_refused_until_a_person_fills_it_in(bundle, tmp_path):
    """The one safety property: an unedited form must not read as a register of seals."""
    from typehaus.engineering.register import load_register

    house = tmp_path / "house"
    house.mkdir()
    (house / "engineering.toml").write_text(
        (bundle / "engineering.toml.draft").read_text())
    with pytest.raises(ValueError) as excinfo:
        load_register(house)
    message = str(excinfo.value)
    assert "placeholder" in message
    # It must name the FIELD. Failing on `sealed_on`'s date parse instead would send the
    # reader to fix the wrong thing.
    assert "engineer" in message


def test_a_filled_scaffold_seals_every_computed_item(bundle, tmp_path):
    """The other half: filled in, the form works, and its fingerprints are the live ones."""
    from typehaus.engineering import Freshness
    from typehaus.engineering.register import load_register

    filled = (bundle / "engineering.toml.draft").read_text()
    filled = filled.replace("<<ENGINEER NAME, PE>>", "A. Engineer, PE")
    filled = filled.replace("<<STATE 00000>>", "MN 12345")
    filled = filled.replace("<<YYYY-MM-DD>>", "2026-09-11")
    filled = filled.replace("<<path/to/sealed.pdf>>", "sealed.pdf")
    house = tmp_path / "house"
    house.mkdir()
    (house / "engineering.toml").write_text(filled)
    register = load_register(house)
    assert register.signoffs

    from typehaus.checks import build_context, run_checks
    from typehaus.source import load_plan

    loaded = load_plan(CATLIN)
    ctx, _ = build_context(loaded.plan, CATLIN)
    report = run_checks(ctx)
    named = {f.engineering_item for f in report.findings if f.engineering_item}
    computed = [ctx.engineering[i] for i in sorted(named | set(ctx.engineering))
                if ctx.engineering[i].inputs]
    assert computed
    for record in computed:
        state, signoff = register.freshness(record)
        assert state is Freshness.FRESH, f"{record.item_id}: {state}"
        assert signoff is not None


def test_a_deferred_item_stays_unsealed_even_with_the_form_filled(bundle, tmp_path):
    """Its block is commented out, so filling the form cannot accidentally stamp it."""
    from typehaus.engineering import Freshness
    from typehaus.engineering.register import load_register

    filled = (bundle / "engineering.toml.draft").read_text()
    for placeholder, value in (("<<ENGINEER NAME, PE>>", "A. Engineer, PE"),
                               ("<<STATE 00000>>", "MN 12345"),
                               ("<<YYYY-MM-DD>>", "2026-09-11"),
                               ("<<path/to/sealed.pdf>>", "sealed.pdf")):
        filled = filled.replace(placeholder, value)
    house = tmp_path / "house"
    house.mkdir()
    (house / "engineering.toml").write_text(filled)
    register = load_register(house)

    from typehaus.checks import build_context, run_checks
    from typehaus.source import load_plan

    loaded = load_plan(CATLIN)
    ctx, _ = build_context(loaded.plan, CATLIN)
    run_checks(ctx)
    deferred = ctx.engineering["column_support/W-SG-W1"]
    state, _ = register.freshness(deferred)
    assert state is not Freshness.FRESH


def test_the_fingerprints_in_the_form_are_the_ones_the_cli_prints(bundle):
    from typehaus.checks import build_context, run_checks
    from typehaus.engineering.fingerprint import fingerprint
    from typehaus.source import load_plan

    draft = (bundle / "engineering.toml.draft").read_text()
    loaded = load_plan(CATLIN)
    ctx, _ = build_context(loaded.plan, CATLIN)
    run_checks(ctx)
    pinned = dict(re.findall(r'^"([^"]+)" = "([0-9a-f]+)"$', draft, re.MULTILINE))
    assert pinned
    for item_id, digest in pinned.items():
        assert fingerprint(ctx.engineering[item_id]) == digest, item_id


# --- the pruning defect this shares with `haus calcs` -------------------------------------

def test_a_stale_file_from_a_previous_run_is_removed(tmp_path):
    """A sheet for an item the model no longer has reads as a calculation somebody did."""
    out = tmp_path / "bundle"
    assert _run(CATLIN, out, "--no-models", "--no-pdf").returncode == 0
    orphan = out / "calcs" / "deck_beam__BM-GONE.md"
    orphan.write_text("# a calculation for an item that no longer exists\n")
    manifest = json.loads((out / "MANIFEST.json").read_text())
    manifest["files"]["calcs/deck_beam__BM-GONE.md"] = "0" * 64
    (out / "MANIFEST.json").write_text(json.dumps(manifest))

    assert _run(CATLIN, out, "--no-models", "--no-pdf").returncode == 0
    assert not orphan.exists()


def test_the_command_is_registered(tmp_path):
    from typehaus.cli.app import app

    names = {c.name or c.callback.__name__ for c in app.registered_commands}
    assert "handoff" in names
