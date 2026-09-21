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
    """Two runs, one model, identical hashes. Without this the manifest proves nothing.

    ** THE PDF IS IN IT SINCE 2026-09-18, AND IT WAS EXCLUDED BEFORE. ** This ran
    ``--no-pdf``, so the one file in the bundle most likely to carry a wall-clock timestamp
    was the one file the determinism test did not look at — and the manifest's whole claim
    is that a changed hash is a changed model rather than a re-run. ``rl_config.invariant``
    fixes reportlab's producer string, dates and document id; this is what says so.
    """
    first, second = tmp_path / "a", tmp_path / "b"
    for out in (first, second):
        assert _run(CATLIN, out, "--no-models").returncode == 0
    left = json.loads((first / "MANIFEST.json").read_text())["files"]
    right = json.loads((second / "MANIFEST.json").read_text())["files"]
    assert "calcs.pdf" in left, "the artefact a seal binds to has to be in the manifest"
    assert left == right


# --- the seal form -----------------------------------------------------------------------

def test_one_signoff_block_per_kind_and_a_deferred_one_asks_for_the_designers_document(
        bundle):
    """A PE stamps a SCOPE. Forty separate stamps is both wrong and expensive.

    ** A DEFERRED BLOCK IS LIVE NOW, AND IT USED TO BE COMMENTED OUT. ** The old reasoning
    was sound as far as it went — a `NO_CALC` item has nothing to fingerprint, so a live
    block invited a stamp that could never satisfy `--require-seal`. The conclusion it
    reached was that a correctly handled deferral is indistinguishable from an unsealed one
    forever. A trussed roof IS designed, by its fabricator, and what gets pinned is that
    designer's paper: `[signoff.external]` takes the document, its revision, its sha256 and
    the envelope it was issued for, and the item reads ACCEPTED.

    An OVER item — one this engine computed and failed — is still commented out, and that
    is the line this test now guards instead.
    """
    draft = (bundle / "engineering.toml.draft").read_text()
    live = re.findall(r"^\[\[signoff\]\]$", draft, re.MULTILINE)
    assert live, "no signoff blocks at all"
    # `rafter` is deferred for good (the fabricator seals it): a live block, with the
    # external-acceptance form in it. It was `column_support` until that kind was computed.
    assert 'id = "rafter"' in draft
    assert "DEFERRED" in draft
    assert '[signoff.external."rafter/RF-GARAGE"]' in draft
    for key in ("document", "revision", "sha256", "envelope"):
        assert f"{key} = \"<<" in draft, key


def _fill_external(text: str) -> str:
    """Fill the ``[signoff.external]`` blanks a deferred block now carries.

    Separate from the four fields every block has, because these are the ones a person can
    only answer by holding the outside designer's document — which is the whole point of
    them being required.
    """
    for placeholder, value in (
            ("<<supplier's revision marking, e.g. Rev C 2026-08-14>>", "Rev C, 2026-08-14"),
            ("<<sha256 of that document, lowercase hex>>", "0" * 64),
            ("<<the spans, loads and conditions the document was issued for>>",
             "as scheduled on the sealed drawing")):
        text = text.replace(placeholder, value)
    return text


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


def test_a_filled_scaffold_seals_every_computed_item(bundle, tmp_path, catlin_ctx,
                                                     catlin_check_report):
    """The other half: filled in, the form works, and its fingerprints are the live ones.

    ** EVERY COMPUTED ITEM, AND THE "OVER" EXCLUSION IS STILL THE POINT EVEN WITH NOTHING
    IN IT. ** `engineering/scaffold.py` writes one block per KIND, because a professional
    stamps a scope and not a line item — and it writes the whole block out COMMENTED where
    any item in that scope is over capacity. From 2026-09-18 to 2026-09-20 that meant
    `column_base/PT-BW-E` and `-W`, which check out perfectly well, were unsealable: they
    share a scope with `PT-BW-RE` and `-RNE`, whose embedment did not. That was correct — a
    PE does not stamp "the fixed column bases" while two of the six fail.

    `notes/entry_column_base_fixity.md` §6a closed both canopy columns on 2026-09-20, so the
    set is empty again and the whole register is sealable. **`refused` is asserted EMPTY
    rather than deleted**: the commenting-out behaviour is what this test is about, and an
    assertion that only ever ran while the house happened to be red would stop guarding it.
    """
    from typehaus.engineering import Freshness
    from typehaus.engineering.register import load_register

    filled = (bundle / "engineering.toml.draft").read_text()
    filled = filled.replace("<<ENGINEER NAME, PE>>", "A. Engineer, PE")
    filled = filled.replace("<<STATE 00000>>", "MN 12345")
    filled = filled.replace("<<YYYY-MM-DD>>", "2026-09-11")
    filled = _fill_external(filled.replace("<<path/to/sealed.pdf>>", "sealed.pdf"))
    house = tmp_path / "house"
    house.mkdir()
    (house / "engineering.toml").write_text(filled)
    register = load_register(house)
    assert register.signoffs

    # `catlin_check_report()` is `run_checks(catlin_ctx)`, which is what populates
    # `ctx.engineering` — the map this test reads.
    ctx = catlin_ctx
    report = catlin_check_report()
    from typehaus.engineering.item import Status

    named = {f.engineering_item for f in report.findings if f.engineering_item}
    every = sorted(named | set(ctx.engineering))
    # A kind with any OVER item has its whole block commented out — see the docstring.
    refused = {ctx.engineering[i].kind for i in every
               if ctx.engineering[i].status is Status.OVER}
    # ** NOT EMPTY SINCE 2026-09-20, AND ON PURPOSE: the SRW apron is computed and OVER
    # (`tiered_retaining`, notes/raised_garden_srw.md). Its block MUST be commented out —
    # no PE stamps a wall at sliding FS 0.38 — and so must `deck_tie`'s, the landing's tie
    # to the garage stem at d/c 1.82 (notes/north_entry_piers.md §10). `base_rotation` left
    # this set on 2026-09-21: the tie took PT-BW-GW out of it. Every other kind stays
    # sealable. **
    assert refused == {"tiered_retaining", "deck_tie"}, (
        "a kind went over capacity — the scaffold will comment its whole block out, which is "
        "correct, but this test then stops exercising the sealing path for it", refused)
    assert register.covering("tiered_retaining/W-RG-BLOCK") is None
    assert register.covering("deck_tie/FS-BW-FLOOR") is None
    computed = [ctx.engineering[i] for i in every
                if ctx.engineering[i].inputs and ctx.engineering[i].kind not in refused]
    assert computed
    for record in computed:
        state, signoff = register.freshness(record)
        assert state is Freshness.FRESH, f"{record.item_id}: {state}"
        assert signoff is not None


def test_a_deferred_item_reads_accepted_and_never_fresh_when_the_form_is_filled(
        bundle, tmp_path, catlin_ctx, catlin_check_report):
    """Filled in, a deferred item is ACCEPTED — never FRESH, because nothing was checked.

    The distinction is the whole design. ``FRESH`` means a fingerprint over this engine's
    own inputs still matches; there is no such fingerprint here and there never can be.
    ``ACCEPTED`` means an outside designer's document covers it, pinned to that document's
    own revision and digest, with the envelope it was issued for written out for a reviewer
    to compare by hand. Both open the final gate; only one of them is about this model.
    """
    from typehaus.engineering import SETTLED, Freshness
    from typehaus.engineering.register import load_register

    filled = (bundle / "engineering.toml.draft").read_text()
    for placeholder, value in (("<<ENGINEER NAME, PE>>", "A. Engineer, PE"),
                               ("<<STATE 00000>>", "MN 12345"),
                               ("<<YYYY-MM-DD>>", "2026-09-11"),
                               ("<<path/to/sealed.pdf>>", "sealed.pdf")):
        filled = filled.replace(placeholder, value)
    filled = _fill_external(filled)
    house = tmp_path / "house"
    house.mkdir()
    (house / "engineering.toml").write_text(filled)
    register = load_register(house)

    ctx = catlin_ctx
    catlin_check_report()
    deferred = ctx.engineering["rafter/RF-GARAGE"]
    state, signoff = register.freshness(deferred)
    assert state is Freshness.ACCEPTED
    assert state is not Freshness.FRESH
    assert state in SETTLED, "a correctly handled deferral has to be able to finish"
    accepted = signoff.external[deferred.item_id]
    assert accepted.revision and accepted.sha256 and accepted.envelope


def test_the_fingerprints_in_the_form_are_the_ones_the_cli_prints(bundle, catlin_ctx,
                                                                 catlin_check_report):
    from typehaus.engineering.fingerprint import fingerprint

    draft = (bundle / "engineering.toml.draft").read_text()
    ctx = catlin_ctx
    catlin_check_report()
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
