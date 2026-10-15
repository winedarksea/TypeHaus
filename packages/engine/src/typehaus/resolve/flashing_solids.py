"""Identity and bounds for thin sheet geometry shared by all emitters."""

from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.model import ResolvedSolid


def flashing_solid(*, uid: str, tag: str, storey: str, category: str, mesh: GMesh,
                   material: str, host_ref: str | None = None,
                   billed_elsewhere: bool = True) -> ResolvedSolid:
    if not mesh.positions:
        raise ValueError(f"flashing {tag} has no sheet geometry")
    xs, ys, zs = zip(*mesh.positions, strict=True)
    return ResolvedSolid(
        uid=uid, tag=tag, storey=storey, category=category,
        outline=[(min(xs), min(ys)), (max(xs), min(ys)),
                 (max(xs), max(ys)), (min(xs), max(ys))],
        z0_m=min(zs), z1_m=max(zs), material=material, body_mesh=mesh,
        host_ref=host_ref, derived=billed_elsewhere)
