import { Fragment, useMemo } from "react";
import type { Hvac, HvacDuctRow, HvacEquipmentRow, HvacRegisterRow, HvacZoneRow } from "../model/types";
import {
  ReaderEmpty, ReaderFilter, ReaderSection, ReaderShell, ReaderTable, TagCell, useReader,
} from "./ReaderShell";

// "HVAC" — the fifth reader: the heat-pump systems, their zones, the ducts and the terminals.
// Presentation only, like the circuits reader beside it. Every number is carried whole from
// model.json's `hvac` block, which is takeoff/hvac.py verbatim — and the zone load/capacity
// rows here are the *same* call `mep.heating_capacity` makes, so the reader and the finding
// cannot drift apart. Nothing is recomputed in the browser, and nothing absent is filled in:
// a capacity the datasheet has not been checked against reads "—", not zero.

function btuh(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return `${Math.round(value).toLocaleString()} Btu/h`;
}

function signedBtuh(value: number | null | undefined): string {
  if (value === null || value === undefined) return "—";
  const rounded = Math.round(value);
  return `${rounded >= 0 ? "+" : "−"}${Math.abs(rounded).toLocaleString()} Btu/h`;
}

// A zone's margin is the whole question the sheet asks, so it carries the badge. Three
// states, not two: an unknown input is not a pass, and pretending otherwise is exactly what
// the engine's tri-state findings exist to prevent.
function marginBadge(zone: HvacZoneRow): { label: string; className: string } {
  if (zone.unknown_inputs.length > 0) return { label: "unknown inputs", className: "confirm" };
  if (zone.heating_capacity_at_design_btuh === null) return { label: "no rating", className: "confirm" };
  const margin = zone.heating_margin_btuh ?? 0;
  if (margin < 0) return { label: "undersized at design", className: "confirm" };
  const ratio = margin / Math.max(1, zone.heating_load_btu_per_hour);
  // A 10% cushion at the 99% design hour is thin but real; below that the reader should say
  // so rather than print the same green badge as a 60% cushion.
  return ratio < 0.1
    ? { label: "thin margin", className: "confirm" }
    : { label: "covered at design", className: "" };
}

function ZoneCard({ zone, index, onZoom }: {
  zone: HvacZoneRow;
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  const badge = marginBadge(zone);
  return (
    <div className="reader-card">
      <div className="reader-card-head">
        <TagCell tag={zone.equipment_tag} index={index} onJump={onZoom}
          title="Zoom to the outdoor unit" mono />
        <span className={`badge ${badge.className}`}>{badge.label}</span>
        <span className="muted">{zone.type_tag ?? "no type"}</span>
      </div>
      <div className="kv">
        <span className="k">Heating load at design</span>
        <span>{btuh(zone.heating_load_btu_per_hour)}</span>
        <span className="k">At-design capacity</span>
        <span>{btuh(zone.heating_capacity_at_design_btuh)}</span>
        {zone.supplemental_tags.length > 0 && <>
          <span className="k">Supplemental heat</span>
          <span>{btuh(zone.supplemental_btuh)} · {zone.supplemental_tags.join(", ")}</span>
        </>}
        <span className="k">Heating margin</span>
        <span>{signedBtuh(zone.heating_margin_btuh)}</span>
        <span className="k">Sensible cooling load</span>
        <span>{btuh(zone.cooling_load_btu_per_hour)}</span>
        <span className="k">Rated cooling</span>
        <span>{btuh(zone.cooling_capacity_btuh)}</span>
        <span className="k">Rated to</span>
        <span>
          {zone.min_operating_temp_f === null
            ? "—"
            : `${zone.min_operating_temp_f}°F outdoor`}
        </span>
      </div>
      {zone.indoor_tags.length > 0 && (
        <div className="reader-tag-cloud">
          {zone.indoor_tags.map((tag) => (
            <TagCell key={tag} tag={tag} index={index} onJump={onZoom}
              title="Zoom to the indoor unit" />
          ))}
        </div>
      )}
      <div className="reader-tag-cloud">
        {zone.rooms.map((tag) => (
          <TagCell key={tag} tag={tag} index={index} onJump={onZoom} title="Zoom to room" />
        ))}
      </div>
      {zone.unknown_inputs.length > 0 && (
        <div className="muted">Block-load inputs missing: {zone.unknown_inputs.join(", ")}</div>
      )}
    </div>
  );
}

function RegisterTable({ rows, index, onZoom }: {
  rows: HvacRegisterRow[];
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  return (
    <ReaderTable<HvacRegisterRow> rows={rows} rowKey={(row) => row.tag} columns={[
      { key: "tag", header: "Terminal", cell: (r) =>
        <TagCell tag={r.tag} index={index} onJump={onZoom} title="Zoom to terminal" mono /> },
      { key: "storey", header: "Storey", cellClass: "reader-mono", cell: (r) => r.storey },
      { key: "system", header: "System", cellClass: "reader-mono", cell: (r) => r.kind },
      { key: "style", header: "Style", cell: (r) => (
        <span className="reader-chip">
          {r.ventilation_terminal ? "ventilation" : "conditioned air"}
        </span>
      ) },
      { key: "room", header: "Room", cellClass: "reader-mono", cell: (r) => r.room ?? "—" },
      { key: "duct", header: "Duct", cellClass: "reader-mono muted", cell: (r) => r.duct_ref ?? "—" },
      { key: "product", header: "Product",
        cell: (r) => r.type_name || <span className="muted">{r.type_ref ?? "—"}</span> },
    ]} />
  );
}

export function HvacView() {
  const { model, data: hvac, index, filter, setFilter, needle, jump, close } =
    useReader<Hvac>((m) => m.hvac);
  const equipment = useMemo(() => {
    const rows = hvac?.equipment ?? [];
    return needle
      ? rows.filter((row) =>
          `${row.tag} ${row.kind} ${row.name ?? ""} ${row.type_ref ?? ""} ${row.room ?? ""}`
            .toLowerCase().includes(needle))
      : rows;
  }, [hvac, needle]);

  if (!model) return null;

  if (!hvac) {
    return (
      <ReaderEmpty title="HVAC" subtitle="no HVAC data" onClose={close}>
        This model carries no HVAC take-off. The zone rows are block loads, so they need the
        envelope preferences — rebuild with a current engine and a preferences.toml.
      </ReaderEmpty>
    );
  }

  const { zones, ducts, registers, ventilation, unclaimed_conditioned_rooms: unclaimed } = hvac;
  const vent = ventilation;

  return (
    <ReaderShell
      title="HVAC"
      subtitle={`${zones.length} zone${zones.length === 1 ? "" : "s"} · ${hvac.equipment.length} units · ${ducts.length} duct runs`}
      onClose={close}
      toolbar={<ReaderFilter value={filter} onChange={setFilter}
        placeholder="Filter equipment…" label="Filter HVAC equipment" />}
    >
      <ReaderSection
        title="Systems"
        note="One card per rated unit: the block load of exactly the rooms its indoor units serve, against the capacity the datasheet claims at the site heating design temperature. Room-scoped loads are approximate by design — envelope area is attributed by plan overlap and air loads by volume share — so this is a sizing screen, not a Manual J."
        count={zones.length}
      >
        {zones.map((zone) => (
          <ZoneCard key={zone.equipment_tag} zone={zone} index={index} onZoom={jump} />
        ))}
        {unclaimed.length > 0 && (
          <div className="reader-card">
            <div className="reader-card-head">
              <span className="reader-card-title">Rooms in no zone</span>
              <span className="badge confirm">{unclaimed.length} unclaimed</span>
            </div>
            <div className="muted">
              Conditioned rooms that no unit's zone_rooms claims. Nothing is guessed for them —
              they are named here and reported by mep.heating_capacity.
            </div>
            <div className="reader-tag-cloud">
              {unclaimed.map((tag) => (
                <TagCell key={tag} tag={tag} index={index} onJump={jump} title="Zoom to room" />
              ))}
            </div>
          </div>
        )}
      </ReaderSection>

      <ReaderSection
        title="Ventilation"
        note="The ERV side, separate from heat: continuous balanced airflow and the sensible recovery the block load's ventilation term turns on."
        count={vent.units.length}
      >
        <div className="reader-card">
          <div className="reader-card-head">
            <span className="reader-card-title">
              {vent.total_ventilation_cfm === null ? "Airflow unknown" : `${vent.total_ventilation_cfm} cfm continuous`}
            </span>
            <span className="muted">{vent.terminal_count} ventilation terminals</span>
          </div>
          <div className="kv">
            <span className="k">Fresh-air terminals</span>
            <span>{vent.supply_terminals}</span>
            <span className="k">Stale-air terminals</span>
            <span>{vent.stale_terminals}</span>
            {vent.units.map((unit) => (
              <Fragment key={unit.tag}>
                <span className="k">{unit.tag}</span>
                <span>
                  {unit.ventilation_cfm === null ? "— cfm" : `${unit.ventilation_cfm} cfm`}
                  {" · "}
                  {unit.sensible_recovery_effectiveness === null
                    ? "SRE unknown"
                    : `${Math.round(unit.sensible_recovery_effectiveness * 100)}% SRE`}
                </span>
              </Fragment>
            ))}
          </div>
        </div>
      </ReaderSection>

      <ReaderSection
        title="Equipment"
        note="Every modeled unit and the ratings its product type carries. A blank capacity means the datasheet has not been authored — not that the unit makes no heat."
        count={equipment.length}
      >
        <ReaderTable<HvacEquipmentRow> rows={equipment} rowKey={(row) => row.tag} columns={[
          { key: "tag", header: "Tag", cell: (r) =>
            <TagCell tag={r.tag} index={index} onJump={jump} title="Zoom to unit" mono /> },
          { key: "kind", header: "Kind", cellClass: "reader-mono", cell: (r) => r.kind },
          { key: "product", header: "Product",
            cell: (r) => r.name || <span className="muted">{r.type_ref ?? "—"}</span> },
          { key: "storey", header: "Storey", cellClass: "reader-mono", cell: (r) => r.storey },
          { key: "room", header: "Room", cellClass: "reader-mono", cell: (r) => r.room ?? "—" },
          { key: "heat47", header: "Heating @47", num: true,
            cell: (r) => btuh(r.heating_capacity_btuh) },
          { key: "heatdesign", header: "@ design", num: true,
            cell: (r) => btuh(r.heating_capacity_at_design_btuh) },
          { key: "cool", header: "Cooling", num: true, cell: (r) => btuh(r.cooling_capacity_btuh) },
          { key: "mintemp", header: "Min °F", num: true, cell: (r) => r.min_operating_temp_f ?? "—" },
          { key: "pairs", header: "Pairs with", cellClass: "reader-mono muted",
            cell: (r) => r.outdoor_ref ?? "—" },
          { key: "circuit", header: "Circuit", cellClass: "reader-mono", cell: (r) => r.circuit ?? "—" },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Duct runs"
        note="Authored routing, never solved: length is the developed plan run and design_cfm is the intent the run was drawn for. CHASE/SOFFIT runs are exempt from the joist-bay geometry checks because they are not in a joist bay."
        count={ducts.length}
      >
        <ReaderTable<HvacDuctRow> rows={ducts} rowKey={(row) => row.tag} columns={[
          { key: "tag", header: "Run", cell: (r) =>
            <TagCell tag={r.tag} index={index} onJump={jump} title="Zoom to duct run" mono /> },
          { key: "storey", header: "Storey", cellClass: "reader-mono", cell: (r) => r.storey },
          { key: "system", header: "System", cellClass: "reader-mono", cell: (r) => r.system },
          { key: "routing", header: "Routing", cellClass: "reader-mono", cell: (r) => r.routing },
          { key: "section", header: "Section", num: true,
            cell: (r) => <>{r.width_in}" × {r.depth_in}"</> },
          { key: "length", header: "Length", num: true, cell: (r) => `${r.length_ft} lf` },
          { key: "design", header: "Design", num: true, cell: (r) =>
            r.design_cfm === null ? <span className="muted">—</span> : `${r.design_cfm} cfm` },
          { key: "floor", header: "Floor", cellClass: "reader-mono muted",
            cell: (r) => r.floor_ref ?? "—" },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Terminals"
        note="Both families in one list, because a plan reader has to be able to tell them apart: a ventilation diffuser is sized for the whole-house rate, a register for a heating CFM."
        count={registers.length}
      >
        <RegisterTable rows={registers} index={index} onZoom={jump} />
      </ReaderSection>
    </ReaderShell>
  );
}
