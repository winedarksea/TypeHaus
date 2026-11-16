"""``IfcPipeFitting`` and ``IfcDuctFitting`` — the parts at the turns, as records.

The IFC export drew every run as a chain of segments and nothing at the corners, so a model
opened in a BIM tool held a drain that changed direction by itself. A fitting is a real
element with a real position, and a schedule that cannot see one cannot order it.

**A pipe fitting carries a placement and no body, deliberately.** What this repo knows about
a pipe fitting is *where it is*, *what it turns*, and *which catalogued pattern it is* — all
of which are in the pset below. What it does not know is the laying length, because no
manufacturer submittal has been read into ``library/fittings.py``
(→ :mod:`typehaus.resolve.mep_fittings`). Emitting a plausible elbow solid would put a
dimension in the IFC that nothing in this repo can source, and an importer would have no way
to tell it from a measured one, so ``TypeHaus_Fitting.gap`` says in words why.

**A duct elbow with a part draws the one the model draws** (``resolve/duct_fabrication.py``):
the tangent-polygon arc of its bought radius, with the run's section, as the ``{uid}-elbow-NN``
piece hosted on the run. A round one is an ``IfcSweptDiskSolid`` over that polyline, a
rectangular one a mitred faceted brep (a straight extrusion cannot turn). The body is in the
world frame, placed at the origin like every other solid (``test_ifc_placement_parity``); an
unrepresented fitting is located by an absolute placement at its vertex. A gap or a junction
stays bodiless.

Its own module rather than a fifth section of :mod:`typehaus.emit.ifc.mep`, which is already
over the 500-line budget and says so in its own docstring.
"""

from __future__ import annotations

import math
from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.emit.ifc.duct_segments import is_elbow_piece, run_pieces
from typehaus.model.ids import derive_child_guid
from typehaus.resolve.mep_fittings import FAMILY_DUCT, FittingRecord, fitting_records
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.sweep import clean_path, is_round_profile, profile_radius_m, sweep_legs

#: The IFC class for each family. ``IfcPipeFitting`` and ``IfcDuctFitting`` are IFC4's own
#: distinction and it is the same one the take-off makes, so no mapping table is needed
#: beyond this pair.
_IFC_CLASS = {"pipe": "IfcPipeFitting", FAMILY_DUCT: "IfcDuctFitting"}

#: IFC4 predefined types. A wye and a tee are both ``JUNCTION`` to IFC — the enumeration has
#: no separate wye — so the pattern's own ``kind`` stays in the pset where it is not lossy.
_PREDEFINED = {"elbow": "BEND", "wye": "JUNCTION", "tee": "JUNCTION"}


def _child_key(record: FittingRecord) -> str:
    """A stable, collision-free child key for the GUID derivation.

    Vertex-keyed for an elbow so the GUID survives a run being re-priced or re-sized;
    **child-keyed** for a junction, which has no vertex of its own on either polyline. A bare
    ``fit-branch`` was the first spelling and it was wrong: a main takes one junction per
    branch that arrives on it, and catlin's ``PR-B-MAIN-DRAIN`` takes several — which the
    IFC validator caught as a duplicate ``GlobalId`` rather than as a missing fitting.
    """
    if record.index is not None:
        return f"fit-{record.index:02d}"
    return f"fit-branch-{record.branch_tag}"


def _off_line(point: tuple, a: tuple, b: tuple) -> float:
    """Distance from ``point`` to the infinite line through ``a`` and ``b``."""
    ab = tuple(b[k] - a[k] for k in range(3))
    ap = tuple(point[k] - a[k] for k in range(3))
    cross = (ab[1] * ap[2] - ab[2] * ap[1], ab[2] * ap[0] - ab[0] * ap[2],
             ab[0] * ap[1] - ab[1] * ap[0])
    return math.sqrt(sum(c * c for c in cross)) / (math.sqrt(sum(c * c for c in ab)) or 1.0)


def _elbow_piece(record: FittingRecord, pieces: list[Any]) -> Any | None:
    """The run's elbow solid whose first and last chords both pass through the record's vertex
    (the arc is tangent to the legs either side of it)."""
    for piece in pieces:
        path = clean_path(piece.sweep.path)
        if (is_elbow_piece(piece) and len(path) >= 2
                and _off_line(record.point, path[0], path[1]) < 1e-3
                and _off_line(record.point, path[-2], path[-1]) < 1e-3
                and math.dist(path[0], record.point) > 1e-4):
            return piece
    return None


def _elbow_body(f: Any, body: Any, piece: Any) -> Any:
    """``piece``'s arc as a world-frame Body."""
    profile = tuple(piece.sweep.profile)
    if is_round_profile(profile):
        return ll.add_swept_disk(f, body, points_m=list(clean_path(piece.sweep.path)),
                                 radius_m=profile_radius_m(profile))
    faces: list[list[Any]] = []
    legs = sweep_legs(piece.sweep)
    for i, (start, end) in enumerate(legs):
        n = len(start)
        faces += [[start[j], start[(j + 1) % n], end[(j + 1) % n], end[j]] for j in range(n)]
        if i == 0:
            faces.append(list(reversed(start)))
        joined = i + 1 < len(legs) and all(
            math.dist(a, b) < 1e-6 for a, b in zip(end, legs[i + 1][0], strict=True))
        if i + 1 == len(legs) or not joined:
            faces.append(list(end))
        if i + 1 < len(legs) and not joined:
            faces.append(list(reversed(legs[i + 1][0])))
    if not faces:
        return None
    return ll.add_faceted_solids(f, body, [faces])


def emit_fittings(f: Any, body: Any, model: ResolvedModel, storeys: dict[str, Any],
                  project_uuid: Any) -> dict[str, list]:
    """Every fitting on every run, grouped by the system its run belongs to.

    The return is keyed on the run's own ``system`` so the caller can fold the fittings into
    the same ``IfcDistributionSystem`` as the segments they sit between — a bend filed
    outside its system is the loose proxy this emitter exists to stop producing.
    """
    storey_of = {run.tag: run.storey for run in model.pipe_runs}
    storey_of.update({duct.tag: duct.storey for duct in model.ducts})
    uid_of = {run.tag: run.uid for run in model.pipe_runs}
    uid_of.update({duct.tag: duct.uid for duct in model.ducts})

    pieces = run_pieces(model)
    out: dict[str, list] = {}
    for record in sorted(fitting_records(model),
                         key=lambda r: (r.run_tag, r.index if r.index is not None else -1)):
        uid = uid_of.get(record.run_tag)
        storey = storeys.get(storey_of.get(record.run_tag, ""))
        if uid is None or storey is None:
            continue  # a run the emitter never placed cannot carry a placed fitting
        element = ll.create_entity(
            f, _IFC_CLASS.get(record.family, "IfcPipeFitting"),
            name=f"{record.run_tag}/{_child_key(record)}")
        element.GlobalId = derive_child_guid(project_uuid, uid, _child_key(record))
        element.PredefinedType = _PREDEFINED.get(record.kind, "NOTDEFINED")
        piece = (_elbow_piece(record, pieces.get(record.run_tag, []))
                 if record.family == FAMILY_DUCT and record.kind == "elbow"
                 and record.gap is None else None)
        representation = _elbow_body(f, body, piece) if piece is not None else None
        if representation is not None:
            ll.assign_representation(f, element, representation)  # placed at the origin
        else:
            origin = f.createIfcCartesianPoint(tuple(float(c) for c in record.point))
            element.ObjectPlacement = f.createIfcLocalPlacement(
                None, f.createIfcAxis2Placement3D(origin, None, None))
        ll.ensure_pset(f, element, PSET_SOURCE, {"uid": uid, "tag": record.run_tag})
        ll.ensure_pset(f, element, "TypeHaus_Fitting", {
            "kind": record.kind,
            # The run's own system, under the key the segment and the accessory psets both
            # use: a distribution system's members are checked for exactly this, and a
            # member whose pset does not carry it reads as a foreign one.
            "system": record.system,
            "service": record.service,
            "branch_tag": record.branch_tag or "",
            "angle_deg": round(record.angle_deg, 2),
            "nominal_in": record.nominal_in,
            # Blank rather than absent where unset, the convention ``TypeHaus_Pipe`` already
            # follows: a pset key that comes and goes makes a schedule column that does too.
            "branch_in": record.branch_in if record.branch_in is not None else 0.0,
            "order_key": record.order_key,
            "catalog": record.spec.tag if record.spec is not None else "",
            "catalog_name": record.spec.name if record.spec is not None else "",
            "source": (record.spec.source or "") if record.spec is not None else "",
            "gap": record.gap or "",
        })
        ll.assign_container(f, element, storey)
        out.setdefault(record.system, []).append(element)
    return out
