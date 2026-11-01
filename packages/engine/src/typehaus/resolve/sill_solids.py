"""The sill plate and its gasket, drawn where nothing else draws them (C3-E17).

A framed wall standing on a pour frames its own bottom plate there, so that return needs no
solid. Where the wall above frames higher (a main-storey wall over the rim band, a bearing
partition over a centre pour) or only joists bear, the plate and gasket existed as a
construction return and nowhere else, and the 1 9/16" under the joists was empty in every
section and in 3D. The return still bills and exports them; these solids only draw them.
"""

from __future__ import annotations

from typehaus.resolve.model import ResolvedModel, ResolvedSolid
from typehaus.resolve.solid_categories import is_pour_slab

_SILL_RETURN = "wall:framed_on_concrete"
_TOL_M = 0.001
GASKET_MATERIAL = "sill-seal"


def _framed_on_the_pour(model: ResolvedModel, ret) -> bool:
    """Does a wall over this return frame its own bottom plate at the pour top?"""
    walls = (model.wall(tag) for tag in ret.element_tags[1:])
    return any(w is not None and w.frame_base_z_m <= ret.z0_m + _TOL_M for w in walls)


def _clear_of_pours(model: ResolvedModel, ret):
    """The return's outline less any pour slab cast in its height; None if nothing is left.

    A return anchored on a framed wall's stud band can straddle a deck cast on the same
    wall top (W-M-C5 over SL-M-DECK); the plate is only where the concrete is not.
    """
    from shapely.geometry import Polygon

    from typehaus.resolve.overlay import difference

    ring = Polygon(ret.outline)
    for slab in model.solids:
        if (is_pour_slab(slab.category) and len(slab.outline) >= 3
                and slab.z0_m < ret.z1_m - _TOL_M and slab.z1_m > ret.z0_m + _TOL_M):
            ring = difference(ring, Polygon(slab.outline))
    if ring.is_empty or ring.geom_type != "Polygon" or ring.area < 1e-6:
        return None
    return tuple(ring.exterior.coords[:-1])


def sill_solids(model: ResolvedModel) -> list[ResolvedSolid]:
    """One gasket and one plate solid per sill return no framed wall draws."""
    out: list[ResolvedSolid] = []
    for ret in model.construction_returns:
        if ret.applies_to != _SILL_RETURN or _framed_on_the_pour(model, ret):
            continue
        outline = _clear_of_pours(model, ret)
        if outline is None:
            continue
        gasket = ret.gasket_thickness_m or 0.0
        piece = ret.uid.rsplit("-sill", 1)[-1]
        tag = f"{ret.element_tags[0]}-SILL{piece}"
        if gasket > 0.0:
            out.append(ResolvedSolid(f"{ret.uid}-gasket", f"{tag}-GASKET", ret.storey,
                                     "sill_gasket", outline, ret.z0_m, ret.z0_m + gasket,
                                     material=GASKET_MATERIAL, product=ret.gasket_product,
                                     host_ref=ret.element_tags[0]))
        out.append(ResolvedSolid(f"{ret.uid}-plate", tag, ret.storey, "sill_plate",
                                 outline, ret.z0_m + gasket, ret.z1_m + gasket,
                                 material=ret.material_ref, host_ref=ret.element_tags[0]))
    return out
