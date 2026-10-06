import type { SpaceSummaryRow } from "../../model/types";
import { ReaderEmpty, ReaderSection, ReaderShell, ReaderTable, useReader, type ReaderColumn } from "../ReaderShell";

const formatMetersAsFeet = (meters: number) => `${(meters / 0.3048).toFixed(1)} ft`;
const formatSquareFeet = (value: number) => value.toLocaleString(undefined, { maximumFractionDigits: 0 });

const areaColumns: ReaderColumn<SpaceSummaryRow>[] = [
  { key: "storey", header: "Storey", cell: (row) => row.storey ?? "Overall" },
  { key: "conditioned", header: "Conditioned (sf)", num: true, cell: (row) => formatSquareFeet(row.conditioned_sf) },
  { key: "unconditioned", header: "Unconditioned (sf)", num: true, cell: (row) => formatSquareFeet(row.unconditioned_sf) },
  { key: "usable", header: "Usable (sf)", num: true, cell: (row) => formatSquareFeet(row.usable_sf) },
  { key: "low-head", header: "Under 5′ head (sf)", num: true, cell: (row) => formatSquareFeet(row.low_head_sf) },
  { key: "storage", header: "Storage (sf)", num: true, cell: (row) => formatSquareFeet(row.storage_sf) },
  { key: "storage-ratio", header: "Storage ratio", num: true, cell: (row) => `${(row.storage_ratio * 100).toFixed(1)}%` },
];

export function SpaceDimensionsView() {
  const { model, close } = useReader((model) => model.space_summary);
  if (!model) return null;
  const summary = model.space_summary;
  const dimensions = model.building_height_summary;
  if (!summary && !dimensions) return <ReaderEmpty title="Space & dimensions" subtitle={model.project.name} onClose={close}>
    Space and dimension summaries are unavailable for this model.
  </ReaderEmpty>;
  return <ReaderShell className="report-reader" wide title="Space & dimensions" subtitle={model.project.name} onClose={close}>
    <ReaderSection title="Areas & storage" note="Engine-derived areas. Usable area excludes the portion below 5′ of clear headroom." count={summary ? summary.storeys.length + 1 : 0}>
      {summary && <ReaderTable rows={[summary.overall, ...summary.storeys]}
        rowKey={(row) => row.storey ?? "overall"} columns={areaColumns} />}
    </ReaderSection>
    <ReaderSection title="Height above average grade" note={dimensions
      ? `Average ground grade: ${formatMetersAsFeet(dimensions.average_ground_grade_m)} relative to the model datum.`
      : "Height data is unavailable."} count={dimensions?.roofs.length ?? 0}>
      {dimensions && <ReaderTable rows={dimensions.roofs} rowKey={(row) => row.roof_tag} columns={[
        { key: "roof", header: "Roof", cell: (row) => row.roof_tag },
        { key: "midpoint", header: "Midpoint above grade", num: true, cell: (row) => formatMetersAsFeet(row.midpoint_above_grade_m) },
        { key: "peak", header: "Peak above grade", num: true, cell: (row) => formatMetersAsFeet(row.peak_above_grade_m) },
      ]} />}
    </ReaderSection>
    <ReaderSection title="Exterior footprint" note="Dimensions from exterior cladding to exterior cladding." count={dimensions?.footprint.length ?? 0}>
      {dimensions && <ReaderTable rows={dimensions.footprint} rowKey={(row) => row.storey} columns={[
        { key: "storey", header: "Storey", cell: (row) => row.storey },
        { key: "width", header: "Width", num: true, cell: (row) => formatMetersAsFeet(row.width_m) },
        { key: "depth", header: "Depth", num: true, cell: (row) => formatMetersAsFeet(row.depth_m) },
      ]} />}
    </ReaderSection>
  </ReaderShell>;
}
