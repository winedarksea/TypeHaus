"""Body-mesh mounting parts retaining their parent railing's ownership."""

from shapely.geometry import MultiPoint

from typehaus.resolve.model import ResolvedSolid


def mounting_solid(model, railing, storey, suffix, mesh, material, product=None):
    outline = tuple(MultiPoint([p[:2] for p in mesh.positions]).convex_hull.exterior.coords)[:-1]
    model.solids.append(ResolvedSolid(
        uid=f"{railing.uid}-{suffix.lower()}", tag=f"{railing.tag}-{suffix}",
        storey=storey, category="railing", outline=outline,
        z0_m=min(p[2] for p in mesh.positions), z1_m=max(p[2] for p in mesh.positions),
        assembly=railing.assembly, material=material, product=product, body_mesh=mesh,
    ))

