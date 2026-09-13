"""The generated PyNite script must run, agree with the in-process solve, and stand alone."""

from __future__ import annotations

import re
import subprocess
import sys

import pytest
from analytical_fixtures import (
    EXPECTED_BASE_MOMENT_NM,
    EXPECTED_BASE_SHEAR_N,
    EXPECTED_BASE_VERTICAL_N,
    portal_frame,
)

from typehaus.emit.analytical.pynite_script import write_pynite_script

_SI_ROW = re.compile(
    r"^SI\s+(\S+)\s+" + r"\s+".join([r"(-?\d+\.\d+)"] * 6) + r"\s*$", re.MULTILINE
)
_COMBO = re.compile(r"^== REACTIONS\s+combo (\S+)", re.MULTILINE)


@pytest.fixture(scope="module")
def script(tmp_path_factory):
    return write_pynite_script(portal_frame(), tmp_path_factory.mktemp("pynite") / "m.py")


def _si_reactions(text: str) -> dict[tuple[str, str], tuple[float, ...]]:
    """Parse the script's own printed SI rows, keyed by (node, combo)."""
    out: dict[tuple[str, str], tuple[float, ...]] = {}
    combo = ""
    for line in text.splitlines():
        if match := _COMBO.match(line):
            combo = match.group(1)
        elif match := _SI_ROW.match(line):
            out[(match.group(1), combo)] = tuple(float(g) for g in match.groups()[1:])
    return out


def test_script_runs_and_reproduces_the_hand_solved_reactions(script):
    run = subprocess.run([sys.executable, str(script)], capture_output=True, text=True,
                         check=False)
    assert run.returncode == 0, run.stderr
    reactions = _si_reactions(run.stdout)
    assert set(reactions) == {(n, c) for n in ("N-W-BASE", "N-E-BASE")
                              for c in ("dead", "wind")}
    for node in ("N-W-BASE", "N-E-BASE"):
        fx, _fy, fz, _mx, my, _mz = reactions[(node, "dead")]
        assert fz == pytest.approx(EXPECTED_BASE_VERTICAL_N, rel=0.005)
        assert abs(my) < 0.01
        fx, _fy, fz, _mx, my, _mz = reactions[(node, "wind")]
        assert fx == pytest.approx(-EXPECTED_BASE_SHEAR_N, rel=0.005)
        assert abs(my) == pytest.approx(EXPECTED_BASE_MOMENT_NM, rel=0.005)


def test_script_is_self_contained(script):
    text = script.read_text(encoding="utf-8")
    assert "typehaus" not in text.lower().replace("type:haus", "")
    assert "from Pynite import FEModel3D" in text
    # No timestamp, no absolute path: those are the two things that break determinism.
    assert not re.search(r"\d{4}-\d\d-\d\dT\d\d:", text)
    assert "/Users/" not in text and "tmp" not in text


def test_script_carries_the_assumptions_and_gaps(script):
    text = script.read_text(encoding="utf-8")
    assert "# ASSUMPTIONS" in text
    assert "#   - fixture: beam bears on the column tops, both moments released" in text
    assert "# GAPS — what this model does NOT carry" in text
    assert "deck_post/PT-W" in text          # the scope, in the header docstring
    assert "Z up" in text or "Z UP" in text or "**Z up**" in text


def test_two_writes_are_byte_identical(tmp_path):
    model = portal_frame()
    first = write_pynite_script(model, tmp_path / "a.py").read_bytes()
    second = write_pynite_script(model, tmp_path / "b.py").read_bytes()
    assert first == second
