"""``IfcPipeFitting`` and ``IfcDuctFitting`` — the parts at the turns, as records.

The IFC export drew every run as a chain of segments and nothing at the corners, so a model
opened in a BIM tool held a drain that changed direction by itself. A fitting is a real
element with a real position, and a schedule that cannot see one cannot order it.

**A fitting here carries a placement and no body, deliberately.** What this repo knows about
a fitting is *where it is*, *what it turns*, and *which catalogued pattern it is* — all of
which are in the pset below. What it does not know is the laying length, because no
manufacturer submittal has been read into ``library/fittings.py``
(→ :mod:`typehaus.resolve.mep_fittings`). Emitting a plausible elbow solid would put a
dimension in the IFC that nothing in this repo can source, and an importer would have no way
to tell it from a measured one. So the element is placed, propertied, and left unrepresented,
and ``TypeHaus_Fitting.gap`` says in words why — the same coverage gap
``mep.fitting_pattern`` reports.

Its own module rather than a fifth section of :mod:`typehaus.emit.ifc.mep`, which is already
over the 500-line budget and says so in its own docstring.
"""

from __future__ import annotations

from typing import Any

from typehaus._meta import PSET_SOURCE
from typehaus.emit.ifc import lowlevel as ll
from typehaus.model.ids import derive_child_guid
from typehaus.resolve.mep_fittings import FAMILY_DUCT, FittingRecord, fitting_records
from typehaus.resolve.model import ResolvedModel

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


def emit_fittings(f: Any, model: ResolvedModel, storeys: dict[str, Any],
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
