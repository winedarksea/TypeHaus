"""R311.7.5.2 / R311.7.5.3: tread depth and nosing projection, measured off the built nosings.

``code.R311_7_stair_geometry`` grades the going the resolver was asked for. This grades what
it built: each straight tread's depth is its leading edge to the next one's — the last to the
landing or floor nosing it meets, or to the head riser's face where that edge has none — and
each nosing's projection is its leading edge to the finished riser face below it. A head riser
set in front of the framing it faced once made every last tread 3/4" short and nothing saw it.

Winder treads are graded at the walkline by their own rule; this reads straight runs only.
Oracle: ``houses/catlin/notes/stair_nosing_basis.md``.
"""

from __future__ import annotations

from collections import defaultdict

from typehaus.checks.code.mn_residential._common import _fail, _pass, _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, not_applicable
from typehaus.quantities import inch
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedStair
from typehaus.resolve.stairs.common import _ascent

CHECK_ID = "code.R311_7_5_2_tread_depth"
_CODE = "R311.7.5.2"
_MIN_DEPTH_M = inch(10).meters
_NO_NOSING_DEPTH_M = inch(11).meters
_SPREAD_M = inch(0.375).meters
_MIN_NOSE_M, _MAX_NOSE_M = inch(0.75).meters, inch(1.25).meters
_TOL_M = 0.001


def _along(points, u) -> list[float]:
    return [x * u[0] + y * u[1] for x, y in points]


def runs(stair: ResolvedStair) -> list[tuple[list[float], list[float]]]:
    """Per straight run, ``(tread depths, nosing projections)`` in ascent order, the end
    landing or floor nosing's projection included where it has one."""
    groups: dict[str, list] = defaultdict(list)
    for member in stair.members:
        if member.category == "tread" and member.riser_line is not None:
            groups[member.child_key.rsplit("-", 1)[0]].append(member)
    risers = [m for m in stair.members if m.category == "riser" and m.orient is not None]
    lips = [p for p in stair.finish_parts if p.role == "landing-nosing"]
    out = []
    for treads in groups.values():
        treads.sort(key=lambda m: m.z1_m)
        u = _ascent(treads[0])
        noses = [min(_along(member_footprint(t)[0], u)) for t in treads]

        def face_under(z: float, u=u) -> float | None:
            """Finished face of the riser whose top meets a walking board at ``z``."""
            for r in risers:
                if abs(r.orient[0] - u[0]) + abs(r.orient[1] - u[1]) > 1e-6:
                    continue
                if abs(r.z1_m - z) <= _TOL_M:
                    front = min(_along((r.p0, r.p1), u))
                    return front - cross_section(r.profile).width_m / 2 \
                        - stair.finish_thickness_m
            return None

        faces = [face_under(t.z0_m) for t in treads]
        projections = [f - n for f, n in zip(faces, noses, strict=True) if f is not None]
        top = treads[-1].z1_m + stair.finish_thickness_m + stair.riser_height_m
        lo, hi = (min(_along(treads[-1].riser_line, (-u[1], u[0]))),
                  max(_along(treads[-1].riser_line, (-u[1], u[0]))))
        end_lip = next((p for p in lips if abs(p.z1_m - top) <= _TOL_M
                        and min(_along(p.outline, (-u[1], u[0]))) < hi - _TOL_M
                        and max(_along(p.outline, (-u[1], u[0]))) > lo + _TOL_M), None)
        end_face = face_under(end_lip.z0_m if end_lip is not None
                              else top - _board(stair) - stair.finish_thickness_m)
        if end_lip is not None:
            end_nose = min(_along(end_lip.outline, u))
            if end_face is not None:
                projections.append(end_face - end_nose)
        else:
            end_nose = end_face
        depths = [b - a for a, b in zip(noses, noses[1:], strict=False)]
        if end_nose is not None:
            depths.append(end_nose - noses[-1])
        out.append((depths, projections))
    return out


def _board(stair: ResolvedStair) -> float:
    """The walking board's own depth, read off a tread (the head riser tops out under it)."""
    tread = next(m for m in stair.members if m.category == "tread")
    return tread.z1_m - tread.z0_m


@check(Tier.CODE, CHECK_ID)
def tread_depth(ctx: CheckContext) -> list[Finding]:
    if not ctx.model.stairs:
        return [_unknown(CHECK_ID, "no resolved stairs", (), _CODE)]
    out: list[Finding] = []
    for stair in ctx.model.stairs:
        tags = (stair.tag,)
        measured = runs(stair)
        depths = [d for run, _ in measured for d in run]
        noses = [p for _, run in measured for p in run]
        if not depths:
            out.append(not_applicable(CHECK_ID, f"{stair.tag} has no straight tread to "
                                      "measure", tags, _CODE))
            continue
        spread = max(depths) - min(depths)
        problems = []
        if min(depths) < _MIN_DEPTH_M - _TOL_M:
            problems.append(f"shallowest tread {min(depths) / .0254:.3f}\" < 10\" "
                            "(R311.7.5.2)")
        if spread > _SPREAD_M + _TOL_M:
            problems.append(f"tread depths {min(depths) / .0254:.3f}\"-"
                            f"{max(depths) / .0254:.3f}\" differ by "
                            f"{spread / .0254:.3f}\" > 3/8\" (R311.7.5.2.1)")
        if noses and max(noses) - min(noses) > _SPREAD_M + _TOL_M:
            problems.append(f"nosing projections {min(noses) / .0254:.3f}\"-"
                            f"{max(noses) / .0254:.3f}\" differ by more than 3/8\", floor "
                            "and landing nosings included (R311.7.5.3)")
        if min(depths) < _NO_NOSING_DEPTH_M - _TOL_M and noses and (
                min(noses) < _MIN_NOSE_M - _TOL_M or max(noses) > _MAX_NOSE_M + _TOL_M):
            problems.append("treads under 11\" need a 3/4\"-1 1/4\" nosing projection "
                            f"(R311.7.5.3); built {min(noses) / .0254:.3f}\"-"
                            f"{max(noses) / .0254:.3f}\"")
        if problems:
            out.append(_fail(CHECK_ID, f"{stair.tag}: " + "; ".join(problems), tags, _CODE))
        else:
            out.append(_pass(CHECK_ID, f"{stair.tag}: {len(depths)} tread depths "
                             f"{min(depths) / .0254:.3f}\"-{max(depths) / .0254:.3f}\", "
                             f"{len(noses)} nosings projecting "
                             + (f"{min(noses) / .0254:.3f}\"-{max(noses) / .0254:.3f}\""
                                if noses else "none"), _CODE))
    return out
