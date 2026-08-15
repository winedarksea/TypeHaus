import { Fragment, useMemo, useState } from "react";
import type {
  BackupComponentRow, ConduitRow, DeviceCountRow, Electrical, BackupRuntime, PanelScheduleRow,
  ServiceLoad,
} from "../model/types";
import {
  ReaderEmpty, ReaderFilter, ReaderSection, ReaderShell, ReaderTable, TagCell, useReader,
} from "./ReaderShell";
import { Icon } from "../icons/Icon";

// "Circuits" — the third reader, and the on-screen twin of the E-601 permit sheet. Every
// number here is carried whole from model.json's `electrical` block, which is
// takeoff/electrical.py verbatim: the same six derivations that print the panel schedule
// stamped for permit and that `haus takeoff` reports. This file is presentation only, on
// purpose — a schedule the browser recomputed could disagree with the drawing, and the
// drawing is the one that gets built.

const VA_PER_KW = 1000;

function formatVa(va: number): string {
  return va >= VA_PER_KW ? `${(va / VA_PER_KW).toFixed(1)} kVA` : `${Math.round(va)} VA`;
}

// The runtime block reads as a verdict for the same reason the service-load block does:
// the question is "does this system carry the house", and the badge is the answer. Null
// means not computable from what is authored, and prints that way — never as a zero.
function hours(value: number | null): string {
  return value === null ? "not computable" : `${value.toFixed(1)} h`;
}

function BackupRuntimeCard({ runtime }: { runtime: BackupRuntime }) {
  const autonomy = runtime.autonomy!;
  const cycle = runtime.cycle_48h!;
  const peak = runtime.peak!;
  const unknown = [
    ...(runtime.tiers?.always_on.unknown_duty_cycle ?? []),
    ...(runtime.tiers?.shed.unknown_duty_cycle ?? []),
  ];
  return (
    <div className="reader-card">
      <div className="reader-card-head">
        <span className="reader-card-title">
          {autonomy.usable_kwh} kWh usable · always-on {hours(autonomy.hours_always_on_only)}
        </span>
        <span className={`badge ${runtime.complete && cycle.sustains_always_on ? "" : "confirm"}`}>
          {runtime.complete ? (cycle.sustains_always_on ? "sustains" : "does not sustain") : "incomplete"}
        </span>
        <span className="muted">estimate</span>
      </div>
      <div className="kv">
        <span className="k">Storage</span>
        <span>
          {autonomy.usable_kwh} kWh of {autonomy.nameplate_kwh} nameplate
          {" "}({Math.round(autonomy.depth_of_discharge * 100)}% DoD)
        </span>
        <span className="k">Simultaneous backup load</span>
        <span>
          {formatVa(peak.simultaneous_va)}
          {peak.inverter_kw_continuous !== null
            ? ` of ${peak.inverter_kw_continuous} kW continuous`
            : " — inverter rating not declared"}
        </span>
        <span className="k">Autonomy, both tiers</span>
        <span>{hours(autonomy.hours_all_tiers)}</span>
        <span className="k">Autonomy, always-on only</span>
        <span>{hours(autonomy.hours_always_on_only)}</span>
        <span className="k">48-hour cycle</span>
        <span>
          {cycle.array_kw} kW array · {cycle.solar_day_kwh} kWh in vs
          {" "}{cycle.two_day_load_kwh_all_tiers} kWh out ={" "}
          {cycle.net_kwh_all_tiers > 0 ? "+" : ""}{cycle.net_kwh_all_tiers} kWh
        </span>
        {unknown.length > 0 && (
          <>
            <span className="k">No authored duty cycle</span>
            <span className="reader-mono">{unknown.join(", ")}</span>
          </>
        )}
        <span className="k">Verdict</span>
        <span>{runtime.verdict}</span>
      </div>
    </div>
  );
}

// The service-load block reads as a verdict, not a table: the last two lines are the whole
// question ("does this house fit its service?"), so they carry the badge.
function ServiceLoadCard({ load }: { load: ServiceLoad }) {
  return (
    <div className="reader-card">
      <div className="reader-card-head">
        <span className="reader-card-title">Demand {load.demand_amps} A</span>
        <span className={`badge ${load.within_service ? "" : "confirm"}`}>
          {load.within_service ? "within service" : "over service"}
        </span>
        <span className="muted">{load.method}</span>
      </div>
      <div className="kv">
        <span className="k">Conditioned area</span>
        <span>{Math.round(load.floor_area_ft2).toLocaleString()} sf</span>
        <span className="k">General lighting + small appliance</span>
        <span>{formatVa(load.general_lighting_va)}</span>
        <span className="k">Fixed appliances</span>
        <span>{formatVa(load.fixed_appliance_va)}</span>
        <span className="k">Heating / cooling</span>
        <span>{formatVa(load.hvac_va)}</span>
        <span className="k">EV charging</span>
        <span>{formatVa(load.ev_va)}</span>
        <span className="k">Calculated demand</span>
        <span>{formatVa(load.demand_va)} · {load.demand_amps} A</span>
        <span className="k">Service / panel</span>
        <span>{load.service_amps} A service · {load.panel_rating_amps} A panel</span>
      </div>
    </div>
  );
}

function PanelSchedule({ rows, expanded, onExpand, index, onZoom }: {
  rows: PanelScheduleRow[];
  expanded: string | null;
  onExpand: (circuit: string | null) => void;
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Circuit</th>
            <th>Description</th>
            <th className="num-col">Breaker</th>
            <th className="num-col">Volts</th>
            <th>NEMA</th>
            <th>Protection</th>
            <th className="num-col">Connected</th>
            <th className="num-col">Devices</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const open = expanded === row.circuit;
            return (
              <Fragment key={row.circuit}>
                <tr>
                  {/* A circuit with nothing on it yet (a spare) is still a real circuit — it
                      gets a plain label rather than a disabled control, which would read as
                      "this circuit is disabled". */}
                  <td>
                    {row.devices.length > 0 ? (
                      <button className="reader-tag" title={open ? "Hide devices" : "Show the devices on this circuit"}
                        onClick={() => onExpand(open ? null : row.circuit)}>
                        <Icon name={open ? "chevron-down" : "chevron-right"} size={14} /> <span className="reader-mono">{row.circuit}</span>
                      </button>
                    ) : (
                      <span className="reader-mono" style={{ paddingLeft: 12 }}>{row.circuit}</span>
                    )}
                  </td>
                  <td>{row.description}</td>
                  <td className="num-col">{row.breaker_amps} A / {row.poles}P</td>
                  <td className="num-col">{row.volts}</td>
                  <td className="reader-mono">{row.nema || "—"}</td>
                  <td>
                    {row.gfci && <span className="reader-chip">GFCI</span>}
                    {row.backup_tier === "always_on" && <span className="reader-chip">always-on</span>}
                    {row.backup_tier === "shed" && <span className="reader-chip">shed</span>}
                    {row.source && <span className="reader-chip">source</span>}
                    {!row.gfci && !row.backup && !row.source && <span className="muted">—</span>}
                  </td>
                  {/* A circuit with neither an authored load nor typed consumers reports 0 —
                      the engine's honest state, shown as such rather than as an estimate. */}
                  <td className="num-col">
                    {row.connected_va > 0 ? formatVa(row.connected_va) : <span className="muted">—</span>}
                  </td>
                  <td className="num-col">{row.devices.length || "—"}</td>
                </tr>
                {open && (
                  <tr>
                    <td colSpan={8}>
                      <div className="reader-tag-cloud">
                        {row.devices.map((tag) => (
                          <TagCell key={tag} tag={tag} index={index} onJump={onZoom}
                            title="Zoom to device" />
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export function CircuitsView() {
  const { model, data: electrical, index, filter, setFilter, needle, jump, close } =
    useReader<Electrical>((m) => m.electrical);
  const [expanded, setExpanded] = useState<string | null>(null);
  const schedule = useMemo(() => {
    const rows = electrical?.panel_schedule ?? [];
    return needle
      ? rows.filter((row) => `${row.circuit} ${row.description} ${row.nema}`.toLowerCase().includes(needle))
      : rows;
  }, [electrical, needle]);

  if (!model) return null;

  if (!electrical) {
    return (
      <ReaderEmpty title="Circuits" subtitle="no electrical data" onClose={close}>
        This model carries no electrical take-off — rebuild with a current engine.
      </ReaderEmpty>
    );
  }

  const { service_load: load, conduit, devices, solar, backup_components: backup } = electrical;
  const runtime = electrical.backup_runtime;
  const kw = (solar.total_watts / VA_PER_KW).toFixed(2);

  return (
    <ReaderShell
      title="Circuits"
      subtitle={`${electrical.panel_schedule.length} circuits${load ? ` · ${load.demand_amps} A demand on a ${load.service_amps} A service` : ""}`}
      onClose={close}
      toolbar={<ReaderFilter value={filter} onChange={setFilter}
        placeholder="Filter circuits…" label="Filter circuits" />}
    >
      <ReaderSection
        title="Service load"
        note="NEC 220.82 optional-method estimate against the service: general lighting from resolved conditioned floor area, appliances from the authored circuits, PV excluded as a source rather than a load."
        count={load ? 1 : 0}
      >
        {load && <ServiceLoadCard load={load} />}
      </ReaderSection>

      <ReaderSection
        title="Panel schedule"
        note="Every authored circuit in panel order. Connected VA prefers the circuit's own authored load and otherwise sums its devices' typed loads. Expand a circuit to zoom to what it feeds."
        count={schedule.length}
      >
        <PanelSchedule rows={schedule} expanded={expanded} onExpand={setExpanded}
          index={index} onZoom={jump} />
      </ReaderSection>

      <ReaderSection
        title="Backup microgrid"
        note="Derived twice over: the storage and conversion rows from the placed ESS equipment, the switching gear from the shed-tier circuits — never a hand-typed parts list."
        count={backup.length}
      >
        <ReaderTable<BackupComponentRow> rows={backup} rowKey={(row) => row.component} columns={[
          { key: "component", header: "Component", cell: (r) => r.component },
          { key: "count", header: "Count", num: true, cell: (r) => r.count },
          { key: "basis", header: "Basis", cellClass: "muted", cell: (r) => r.basis },
        ]} />
      </ReaderSection>

      {runtime?.modeled && runtime.autonomy && runtime.cycle_48h && (
        <ReaderSection
          title="Backup runtime"
          note="An estimate, not a guarantee: tier draw is connected VA times an authored duty cycle, and the 48-hour cycle assumes one strong solar day in two. A circuit with no authored duty cycle is listed as unknown, never counted as zero."
          count={1}
        >
          <BackupRuntimeCard runtime={runtime} />
        </ReaderSection>
      )}

      <ReaderSection
        title="Conduit"
        note="EMT trunks by trade size, in developed length — plan run plus riser, the way it is ordered."
        count={conduit.length}
      >
        <ReaderTable<ConduitRow> rows={conduit} rowKey={(row) => String(row.trade_size_in)} columns={[
          { key: "size", header: "Trade size", num: true, cell: (r) => `${r.trade_size_in}"` },
          { key: "runs", header: "Runs", num: true, cell: (r) => r.runs },
          { key: "length", header: "Length", num: true, cell: (r) => `${r.length_ft} lf` },
          { key: "tags", header: "Tags", cellClass: "reader-mono muted",
            cell: (r) => r.tags.join(" · ") },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="Devices"
        note="What the electrician's order reads: every modeled device counted by kind and product type."
        count={devices.length}
      >
        <ReaderTable<DeviceCountRow> rows={devices} rowKey={(row) => `${row.kind}·${row.type}`} columns={[
          { key: "kind", header: "Kind", cellClass: "reader-mono", cell: (r) => r.kind },
          { key: "type", header: "Type", cellClass: "reader-mono", cell: (r) => r.type },
          { key: "product", header: "Product",
            cell: (r) => r.name || <span className="muted">—</span> },
          { key: "nema", header: "NEMA", cellClass: "reader-mono", cell: (r) => r.nema || "—" },
          { key: "count", header: "Count", num: true, cell: (r) => r.count },
        ]} />
      </ReaderSection>

      <ReaderSection
        title="PV array"
        note={`${solar.panels} modules · ${kw} kW installed DC. Watts are summed from the resolved modules, never a hand-typed total.`}
        count={solar.by_product.length}
      >
        {solar.by_product.map((row) => (
          <div key={row.product} className="reader-card">
            <div className="reader-card-head">
              <span className="reader-card-title">{row.product}</span>
              <span className="muted">
                {row.panels} × {Math.round(row.watts / row.panels)} W = {(row.watts / VA_PER_KW).toFixed(2)} kW
              </span>
            </div>
            <div className="reader-tag-cloud">
              {row.tags.map((tag) => (
                <TagCell key={tag} tag={tag} index={index} onJump={jump} title="Zoom to module" />
              ))}
            </div>
          </div>
        ))}
      </ReaderSection>
    </ReaderShell>
  );
}
