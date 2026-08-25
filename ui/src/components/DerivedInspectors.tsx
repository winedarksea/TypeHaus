// Inspectors for *derived* geometry — the records the resolver computes rather than the
// designer authors: solids (slabs, footings, posts, beams, rails, gutters, flashings…), a
// footing's gravel bedding, a roof, and a framed floor. All four became selectable in 3D with
// B7, so each needs a panel that answers "what is this, what is it made of, how big is it, and
// where did it come from?" — none of them is editable in place; the edit lives on the element
// or rule that produced it, which `Provenance` points at.
import type {
  FootingBedding, Floor, LightRun, Model, Roof, Solid, SolarPanel, Vec2,
} from "../model/types";
import { formatFtIn } from "../model/geometry";
import type { LocatedMember } from "../model/memberIdentity";
import { solidCategoryLabel } from "../model/solidLabels";
import { useStore } from "../state/store";
import { Provenance } from "./Provenance";
import { ProductRows } from "./ProductRows";
import { productForMaterial } from "../model/products";

// NB: construction returns (ConstructionRule laps) used to arrive here as solids with a
// "return:" category prefix. They no longer produce solids at all — the resolver records them
// on `Model.construction_returns`, and nothing in 3D draws them, so there is no selection to
// inspect. Nothing left to strip from a solid's category.

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
  const model = useStore((s) => s.model);
  return <div>
    <h3>{solidCategoryLabel(solid.category)} · {solid.tag}</h3>
    <div className="kv">
      {/* Heading is the human name; the raw category stays on the row beneath it, because
          it is the key every palette, trade table and take-off is written against and a
          reader chasing one needs to see it spelled the way the code spells it. */}
      <span className="k">Category</span><span>{solid.category}</span>
      <span className="k">Assembly</span><span>{solid.assembly ?? "—"}</span>
      {/* The trim-run family (gutters, fascia, soffits, ridge caps, edge cladding, railing
          parts) names a material DIRECTLY instead of an assembly — the resolver sets it and
          the viewer has been colouring from it since 2026-08-01, but this panel printed
          only "Assembly —" and left the reader with nothing. Raw tag, matching
          MemberInspector: it is the key the palette, the trade table and the take-off are
          all written against. */}
      <span className="k">Material</span><span>{solid.material ?? "—"}</span>
      <ProductRows product={productForMaterial(model, solid.material)} />
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

export function SolarPanelInspector({ panel }: { panel: SolarPanel }) {
  const zs = panel.corners_bottom.map((corner) => corner[2]);
  return <div>
    <h3>Solar panel · {panel.tag}</h3>
    <div className="kv">
      <span className="k">Product</span><span>{panel.product || "—"}</span>
      <span className="k">Rating</span><span>{panel.watts.toFixed(0)} W</span>
      <span className="k">On roof</span><span>{panel.roof_ref}</span>
      <span className="k">Plan extent</span><PlanExtent points={panel.corners_bottom.map((c) => [c[0], c[1]])} />
      <span className="k">Elevation</span><span>{formatFtIn(Math.min(...zs))} → {formatFtIn(Math.max(...zs))}</span>
      <span className="k">Storey</span><span>{panel.storey}</span>
      <span className="k">uid</span><span className="prov">{panel.uid}</span>
    </div>
    <Provenance p={panel.provenance} />
    <DerivedNote source="its SolarPanel element and the roof plane it rides" />
  </div>;
}

export function LightRunInspector({ run }: { run: LightRun }) {
  return <div>
    <h3>Cove/LED run · {run.tag}</h3>
    <div className="kv">
      <span className="k">Type</span><span>{run.type}</span>
      <span className="k">Length</span><span>{formatFtIn(run.length_m)}</span>
      <span className="k">Mounted at</span><span>{formatFtIn(run.z_m)}</span>
      <span className="k">Room</span><span>{run.room ?? "—"}</span>
      <span className="k">Circuit</span><span>{run.circuit ?? "—"}</span>
      <span className="k">PSU</span><span>{run.psu_ref ?? "—"}</span>
      <span className="k">Controlled by</span><span>{run.controlled_by.join(", ") || "—"}</span>
      <span className="k">Storey</span><span>{run.storey}</span>
      <span className="k">uid</span><span className="prov">{run.uid}</span>
    </div>
    <Provenance p={run.provenance} />
    <DerivedNote source="its authored LightRun element" />
  </div>;
}

export function FootingBeddingInspector({ bedding }: { bedding: FootingBedding }) {
  return <div>
    <h3>Footing bedding · {bedding.tag}</h3>
    <div className="kv">
      <span className="k">Under</span><span>{bedding.host}</span>
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

// The i-joist section the engine pre-resolved, or the plain nominal one. Never re-parses
// `profile` — server/model_json.py already did that once for every consumer.
function sectionSummary(located: LocatedMember): string {
  const { member } = located;
  if (member.shape === "i_joist" && member.flange_width_m != null) {
    return `I-joist ${formatFtIn(member.flange_width_m)} flange × ${formatFtIn(member.z1_m - member.z0_m)}`;
  }
  if (member.shape === "floor_truss" && member.flange_thickness_m != null) {
    const opening = member.depth_m - 2 * member.flange_thickness_m;
    return `Floor truss ${formatFtIn(member.depth_m)} deep, ${formatFtIn(opening)} chord-to-chord opening`;
  }
  const plies = member.plies > 1 ? ` (${member.plies} ply)` : "";
  return `${formatFtIn(member.width_m)} × ${formatFtIn(member.depth_m)}${plies}`;
}

// One framing member, picked out of a shared instanced/merged draw call in 3D (→
// three/memberPicking.ts). It is the most derived thing the UI can select: the resolver frames
// it from the wall/roof/floor/stair's assembly, so there is nothing here to edit — the answer
// to "make this stud different" is always the parent's assembly or spacing rule.
export function MemberInspector({ located }: { located: LocatedMember }) {
  const select = useStore((s) => s.select);
  const model = useStore((s) => s.model);
  const { member, ownerKind, ownerTag, ownerUid } = located;
  const raked = member.z0_end_m != null || member.z1_end_m != null;
  return <div>
    <h3>{member.category} · {member.key}</h3>
    <div className="kv">
      <span className="k">Category</span><span>{member.category}</span>
      <span className="k">Profile</span><span>{member.profile}</span>
      <span className="k">Section</span><span>{sectionSummary(located)}</span>
      <span className="k">Length</span><span>{formatFtIn(member.length_m)}</span>
      <span className="k">Elevation</span>
      <span>{formatFtIn(member.z0_m)} → {formatFtIn(member.z1_m)}{raked ? " (raked)" : ""}</span>
      <span className="k">Material</span><span>{member.material ?? "lumber"}</span>
      <ProductRows product={productForMaterial(model, member.material)} />
      {/* Only shown when the resolver actually overrode the category default — otherwise the
          trade is whatever the category implies and repeating it here is noise. */}
      {member.trade && <><span className="k">Trade</span><span>{member.trade}</span></>}
      {member.connection && <><span className="k">Connection</span><span>{member.connection}</span></>}
      <span className="k">Framed for</span><span>{ownerKind} {ownerTag}</span>
      <span className="k">Storey</span><span>{located.storey ?? "—"}</span>
    </div>
    {/* A stair (and a roof's framing) is nothing but members, so a click in 3D can only land
        on a stick. This is how you get back up to the thing that is actually editable. */}
    <button className="btn" style={{ marginTop: 8 }} onClick={() => select(ownerKind, ownerUid)}>
      Select the {ownerKind} ({ownerTag})
    </button>
    <DerivedNote source={`the ${ownerKind} ${ownerTag} it frames`} />
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
