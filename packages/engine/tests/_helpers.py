"""Shared test helpers (→ AGENTS.md §3: factor setup used in 3+ files).

Import these instead of re-deriving them: the catlin path constant alone was duplicated
byte-for-byte in 61 test files, each spelling out its own ``parents[3]`` walk.
"""

from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HOUSES = REPO_ROOT / "houses"
STARTER = HOUSES / "starter"
CATLIN = HOUSES / "catlin"

# A house sandbox needs the authored plan, never the build output. ``houses/catlin`` is 65 MB of
# which ``out/`` is 64 MB (renders, glb, ifc, model.json), so an unfiltered copy costs seconds and
# the suite builds 25 sandboxes. ``out/`` is gitignored, so CI never had it and never paid this —
# it was a purely local tax, and the handful of sites that already passed an ignore list ran an
# order of magnitude faster than the ones that did not.
HOUSE_IGNORE = shutil.ignore_patterns("out", "__pycache__", ".claude", ".DS_Store", ".git")


#: Every ``FramedMember`` category ``framing/solver.py::frame_wall`` emits from a wall's
#: STRUCTURE layer. It is the member-side witness for "this wall framed rather than poured",
#: and the partition the two wall-structure BOM sections make (→ takeoff/wall_structure.py).
#:
#: Not just ``"stud"``, which is what it was until 2026-08-25: a wall short enough to be
#: almost entirely rough opening frames a jamb pack and no module stud at all — W-M-N3 is
#: 4'-0" long and 3'-2" of that is D-M-ENTRY, leaving 3-3/4" of wall at each end that the
#: king and jack fill between them. Its spf reaches the cut list as kings, jacks, cripples,
#: a header and three plates; only the proxy was blind to it. It became reachable when the
#: seam studs went (``solver.continuation_roles``), because those 3-3/4" ends were exactly
#: where a segment used to frame its own end stud.
FRAMED_STRUCTURE_CATEGORIES = frozenset({
    "stud", "plate", "raked_plate", "corner", "king", "jack", "cripple", "header", "sill",
})


def frames_structure(wall) -> bool:
    """Did this wall's STRUCTURE layer resolve to sticks of lumber?"""
    return any(member.category in FRAMED_STRUCTURE_CATEGORIES for member in wall.members)


def copy_house(src: Path, dst: Path) -> Path:
    """Copy an authored house into a sandbox, leaving build output behind."""
    shutil.copytree(src, dst, ignore=HOUSE_IGNORE)
    return dst


def check_context(plan=None, model=None, *, preferences=None, profile="mn-2024",
                  resolve_findings=None):
    """A ``CheckContext`` from a plan, a model, or both.

    Ten test modules hand-rolled this, and the bodies differed only in which profile they
    named and whether they resolved for you — which meant the "did resolve emit errors?"
    assertion was present in some and absent in others, so a test could quietly be
    checking a broken model.

    Pass a ``plan`` and it resolves (asserting no ERROR findings) and threads the findings
    through as ``resolve_findings`` — several checks read them. Pass a ``model`` and it
    takes ``model.plan``. ``profile`` accepts a jurisdiction name, ``None`` for the
    profile-independent checks, or an already-resolved profile object.
    """
    from typehaus.checks.code.mn_residential.profile import get_profile
    from typehaus.checks.registry import CheckContext, Preferences
    from typehaus.resolve import resolve

    if plan is None:
        assert model is not None, "check_context needs a plan or a model"
        plan = model.plan
    if model is None:
        model, findings = resolve(plan)
        errors = [f for f in findings if f.severity.value == "error"]
        assert not errors, [f.message for f in errors]
        if resolve_findings is None:
            resolve_findings = list(findings)
    return CheckContext(
        plan=plan, model=model,
        preferences=preferences if preferences is not None else Preferences(),
        profile=get_profile(profile) if isinstance(profile, str) else profile,
        resolve_findings=list(resolve_findings or ()),
    )

