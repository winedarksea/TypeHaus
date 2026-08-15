"""`haus doctor` — the environment facts a session should not have to rediscover.

Six memory files existed only because one of these was silently wrong: which interpreter,
whether `typehaus` resolves to the checkout or a stale copy, whether the UI is built, and —
the one that has actually shipped a broken commit here — whether a `.gitignore` pattern is
swallowing a source tree.
"""

from __future__ import annotations

from typer.testing import CliRunner

from typehaus.cli.app import app
from typehaus.cli.cmd_doctor import _SOURCE_TREES, _gitignore_row, _repo_root

from _helpers import REPO_ROOT

runner = CliRunner()


def test_doctor_reports_every_row() -> None:
    result = runner.invoke(app, ["doctor"])
    for row in ("python", "typehaus", "engine", "ui/dist", "serve", "gitignore"):
        assert row in result.output


def test_doctor_finds_the_checkout_and_the_editable_install() -> None:
    result = runner.invoke(app, ["doctor"])
    assert "editable ->" in result.output, result.output


def test_no_source_tree_is_gitignored() -> None:
    """The regression guard for the unanchored-pattern bug class.

    `build/`, `lib/`, `dist/`, `parts/`, `var/`, `target/` and `cover/` all arrive from the
    github Python template unanchored, so they match at *any* depth: `ui/src/three/build/`
    was swallowed once and the commit shipped importing five modules git never took, with a
    clean `git status` throughout. Anchoring them is the fix; this is what keeps it fixed.
    """
    row, hits = _gitignore_row(REPO_ROOT)
    assert not hits, hits
    assert row.status == "ok"


def test_the_trees_it_guards_actually_exist() -> None:
    """A check over a directory that is not there passes for the wrong reason."""
    assert [t for t in _SOURCE_TREES if (REPO_ROOT / t).is_dir()] == list(_SOURCE_TREES)


def test_repo_root_is_this_checkout() -> None:
    assert _repo_root() == REPO_ROOT


def test_a_negation_rule_does_not_read_as_ignored() -> None:
    """`git check-ignore -v` prints its matching rule and exits 0 for a `!` negation exactly
    as it does for an exclusion. .gitignore carries several protective negations over source
    trees, so without this the check would report every one of them as ignored — the exact
    opposite of what it is there to detect."""
    from typehaus.cli.cmd_doctor import _is_negation

    assert _is_negation(".gitignore:213:!packages/*/src/**\tpackages/engine/src/x.py")
    assert not _is_negation(".gitignore:11:build/\tui/src/three/build")
    assert not _is_negation(".gitignore:199:**/out/\thouses/catlin/out")
