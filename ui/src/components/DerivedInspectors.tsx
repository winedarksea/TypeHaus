// Inspectors for *derived* geometry — the records the resolver computes rather than the
// designer authors: solids (slabs, footings, posts, beams, rails, gutters, flashings…), a
// footing's gravel bedding, a roof, and a framed floor. All four became selectable in 3D with
// B7, so each needs a panel that answers "what is this, what is it made of, how big is it, and
// where did it come from?" — none of them is editable in place; the edit lives on the element
// or rule that produced it, which `Provenance` points at.
import type { FootingBedding, Floor, Model, Roof, Solid, Vec2 } from "../model/types";
import { formatFtIn } from "../model/geometry";
import { Provenance } from "./Provenance";

// A construction return ("return:pt-sill-plate") is geometry a library rule added, not an
// element; strip the prefix so the panel reads as the rule's take-off category.
function solidCategoryLabel(category: string): string {
  return category.startsWith("return:") ? `${category.slice("return:".length)} (construction return)` : category;
}

function ringSpan(points: readonly Vec2[]): [number, number] | null {
  if (points.length < 2) return null;
  const xs = points.map(([x]) => x);
  const ys = points.map(([, y]) => y);
  return [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
}

function PlanExtent({ points }: { points: readonly Vec2[] }) {
  const span = ringSpan(points);
  return <span>{span ? `${formatFtIn(span[0])} × ${formatFtIn(span[1])}` : "—"}</span>;
}

// Shared trailer: derived geometry cannot be deleted or moved from the Inspector, so say what
// to edit instead rather than offering controls that would silently do nothing.
function DerivedNote({ source }: { source: string }) {
  return <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
    Derived geometry — resolved from {source}. Edit the source to change it.
  </p>;
}

export function SolidInspector({ solid }: { solid: Solid }) {
  return <div>
    <h3>{solidCategoryLabel(solid.category)} · {solid.tag}</h3>
    <div className="kv">
      <span className="k">Category</span><span>{solid.category}</span>
      <span className="k">Assembly</span><span>{solid.assembly ?? "—"}</span>
      <span className="k">Plan extent</span><PlanExtent points={solid.outline} />
      <span className="k">Thickness</span><span>{formatFtIn(solid.z1_m - solid.z0_m)}</span>
      <span className="k">Elevation</span><span>{formatFtIn(solid.z0_m)} → {formatFtIn(solid.z1_m)}</span>
      <span className="k">Storey</span><span>{solid.storey}</span>
      <span className="k">Voids</span><span>{solid.voids?.length ?? 0}</span>
      <span className="k">uid</span><span className="prov">{solid.uid}</span>
    </div>
    <Provenance p={solid.provenance} />
    <DerivedNote source="its authored element or construction rule" />
  </div>;
}

export function FootingBeddingInspector({ bedding }: { bedding: FootingBedding }) {
  return <div>
    <h3>Footing bedding · {bedding.tag}</h3>
    <div className="kv">
      <span className="k">Under footing</span><span>{bedding.host_footing}</span>
      <span className="k">Aggregate</span><span>{bedding.aggregate}</span>
      <span className="k">Geotextile</span><span>{bedding.geotextile ? "yes" : "no"}</span>
      <span className="k">Drain tile</span><span>{bedding.drain_tile ? "yes" : "no"}</span>
      <span className="k">Plan extent</span><PlanExtent points={bedding.outline} />
      <span className="k">Depth</span><span>{formatFtIn(bedding.z1_m - bedding.z0_m)}</span>
      <span className="k">Elevation</span><span>{formatFtIn(bedding.z0_m)} → {formatFtIn(bedding.z1_m)}</span>
      <span className="k">Storey</span><span>{bedding.storey}</span>
      <span className="k">uid</span><span className="prov">{bedding.uid}</span>
    </div>
    <Provenance p={bedding.provenance} />
    <DerivedNote source="its FootingBedding element" />
  </div>;
}

export function RoofInspector({ model, roof }: { model: Model; roof: Roof }) {
  const assembly = model.catalog?.assemblies.find((candidate) => candidate.tag === roof.assembly);
  const pitchRise = roof.ridge_z_m - roof.eave_z_m;
  return <div>
    <h3>Roof · {roof.tag}</h3>
    <div className="kv">
      <span className="k">Form</span><span>{roof.form}</span>
      <span className="k">Assembly</span><span>{roof.assembly}</span>
      <span className="k">Layers</span><span>{assembly?.layers.length ?? 0}</span>
      <span className="k">Ridge runs</span><span>{roof.ridge_direction}</span>
      <span className="k">Eave → ridge</span>
      <span>{formatFtIn(roof.eave_z_m)} → {formatFtIn(roof.ridge_z_m)} (rise {formatFtIn(pitchRise)})</span>
      <span className="k">Surface area</span><span>{(roof.surface_area_m2 * 10.7639).toFixed(0)} sf</span>
      <span className="k">Plan extent</span><PlanExtent points={roof.footprint} />
      <span className="k">Members</span><span>{roof.members.length}</span>
      <span className="k">Storey</span><span>{roof.storey}</span>
      <span className="k">uid</span><span className="prov">{roof.uid}</span>
    </div>
    <Provenance p={roof.provenance} />
    <DerivedNote source="its Roof element and bearing walls" />
  </div>;
}

export function FloorInspector({ floor }: { floor: Floor }) {
  const points = floor.members.flatMap((member) => [member.p0, member.p1]);
  const depths = floor.members.map((member) => member.z1_m - member.z0_m);
  return <div>
    <h3>Floor · {floor.tag}</h3>
    <div className="kv">
      <span className="k">Joists run</span><span>{floor.direction}</span>
      <span className="k">Members</span><span>{floor.members.length}</span>
      <span className="k">Joist depth</span>
      <span>{depths.length ? formatFtIn(Math.max(...depths)) : "—"}</span>
      <span className="k">Subfloor</span>
      <span>{floor.subfloor ? `${floor.subfloor.material} · ${formatFtIn(floor.subfloor.thickness_m)}` : "none"}</span>
      <span className="k">Deck extent</span><PlanExtent points={points} />
      <span className="k">Openings</span><span>{floor.openings.length}</span>
      <span className="k">Storey</span><span>{floor.storey}</span>
      <span className="k">uid</span><span className="prov">{floor.uid}</span>
    </div>
    <Provenance p={floor.provenance} />
    <DerivedNote source="its FloorSystem / JoistSpec" />
  </div>;
}
