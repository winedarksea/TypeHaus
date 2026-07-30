import { Fragment, useMemo, useState } from "react";
import { useStore } from "../state/store";
import { uidByTag } from "../model/tagIndex";
import type { HvacRegisterRow, HvacZoneRow } from "../model/types";
import { ReaderSection, ReaderShell } from "./ReaderShell";

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
        <button className="reader-tag" onClick={() => onZoom(zone.equipment_tag)}
          disabled={!index.has(zone.equipment_tag)} title="Zoom to the outdoor unit">
          <span className="reader-mono">{zone.equipment_tag}</span>
        </button>
        <span className={`badge ${badge.className}`}>{badge.label}</span>
        <span className="muted">{zone.type_tag ?? "no type"}</span>
      </div>
      <div className="kv">
        <span className="k">Heating load at design</span>
        <span>{btuh(zone.heating_load_btu_per_hour)}</span>
        <span className="k">At-design capacity</span>
        <span>{btuh(zone.heating_capacity_at_design_btuh)}</span>
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
            <button key={tag} className="reader-tag" onClick={() => onZoom(tag)}
              disabled={!index.has(tag)} title="Zoom to the indoor unit">
              {tag}
            </button>
          ))}
        </div>
      )}
      <div className="reader-tag-cloud">
        {zone.rooms.map((tag) => (
          <button key={tag} className="reader-tag" onClick={() => onZoom(tag)}
            disabled={!index.has(tag)} title="Zoom to room">
            {tag}
          </button>
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
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Terminal</th><th>Storey</th><th>System</th><th>Style</th>
            <th>Room</th><th>Duct</th><th>Product</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.tag}>
              <td>
                <button className="reader-tag" onClick={() => onZoom(row.tag)}
                  disabled={!index.has(row.tag)} title="Zoom to terminal">
                  <span className="reader-mono">{row.tag}</span>
                </button>
              </td>
              <td className="reader-mono">{row.storey}</td>
              <td className="reader-mono">{row.kind}</td>
              <td>
                <span className="reader-chip">
                  {row.ventilation_terminal ? "ventilation" : "conditioned air"}
                </span>
              </td>
              <td className="reader-mono">{row.room ?? "—"}</td>
              <td className="reader-mono muted">{row.duct_ref ?? "—"}</td>
              <td>{row.type_name || <span className="muted">{row.type_ref ?? "—"}</span>}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function HvacView() {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [filter, setFilter] = useState("");

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const hvac = model?.hvac ?? null;

  const needle = filter.trim().toLowerCase();
  const equipment = useMemo(() => {
    const rows = hvac?.equipment ?? [];
    return needle
      ? rows.filter((row) =>
          `${row.tag} ${row.kind} ${row.name ?? ""} ${row.type_ref ?? ""} ${row.room ?? ""}`
            .toLowerCase().includes(needle))
      : rows;
  }, [hvac, needle]);

  if (!model) return null;

  // Same jump contract as the other readers: zoom the plan, then get out of its way.
  const jump = (tag: string) => {
    const uid = index.get(tag);
    if (uid) {
      zoomToUid(uid);
      setDetailView("none");
    }
  };

  if (!hvac) {
    return (
      <ReaderShell title="HVAC" subtitle="no HVAC data" onClose={() => setDetailView("none")}>
        <div className="muted">
          This model carries no HVAC take-off. The zone rows are block loads, so they need the
          envelope preferences — rebuild with a current engine and a preferences.toml.
        </div>
      </ReaderShell>
    );
  }

  const { zones, ducts, registers, ventilation, unclaimed_conditioned_rooms: unclaimed } = hvac;
  const vent = ventilation;

  return (
    <ReaderShell
      title="HVAC"
      subtitle={`${zones.length} zone${zones.length === 1 ? "" : "s"} · ${hvac.equipment.length} units · ${ducts.length} duct runs`}
      onClose={() => setDetailView("none")}
      toolbar={
        <input
          value={filter}
          placeholder="Filter equipment…"
          onChange={(event) => setFilter(event.target.value)}
          aria-label="Filter HVAC equipment"
          style={{ padding: "5px 7px", minWidth: 180 }}
        />
      }
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
                <button key={tag} className="reader-tag" onClick={() => jump(tag)}
                  disabled={!index.has(tag)} title="Zoom to room">
                  {tag}
                </button>
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
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>Tag</th><th>Kind</th><th>Product</th><th>Storey</th><th>Room</th>
                <th className="num-col">Heating @47</th><th className="num-col">@ design</th>
                <th className="num-col">Cooling</th><th className="num-col">Min °F</th>
                <th>Pairs with</th><th>Circuit</th>
              </tr>
            </thead>
            <tbody>
              {equipment.map((row) => (
                <tr key={row.tag}>
                  <td>
                    <button className="reader-tag" onClick={() => jump(row.tag)}
                      disabled={!index.has(row.tag)} title="Zoom to unit">
                      <span className="reader-mono">{row.tag}</span>
                    </button>
                  </td>
                  <td className="reader-mono">{row.kind}</td>
                  <td>{row.name || <span className="muted">{row.type_ref ?? "—"}</span>}</td>
                  <td className="reader-mono">{row.storey}</td>
                  <td className="reader-mono">{row.room ?? "—"}</td>
                  <td className="num-col">{btuh(row.heating_capacity_btuh)}</td>
                  <td className="num-col">{btuh(row.heating_capacity_at_design_btuh)}</td>
                  <td className="num-col">{btuh(row.cooling_capacity_btuh)}</td>
                  <td className="num-col">{row.min_operating_temp_f ?? "—"}</td>
                  <td className="reader-mono muted">{row.outdoor_ref ?? "—"}</td>
                  <td className="reader-mono">{row.circuit ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </ReaderSection>

      <ReaderSection
        title="Duct runs"
        note="Authored routing, never solved: length is the developed plan run and design_cfm is the intent the run was drawn for. CHASE/SOFFIT runs are exempt from the joist-bay geometry checks because they are not in a joist bay."
        count={ducts.length}
      >
        <div className="reader-table-scroll">
          <table className="reader-table">
            <thead>
              <tr>
                <th>Run</th><th>Storey</th><th>System</th><th>Routing</th>
                <th className="num-col">Section</th><th className="num-col">Length</th>
                <th className="num-col">Design</th><th>Floor</th>
              </tr>
            </thead>
            <tbody>
              {ducts.map((row) => (
                <tr key={row.tag}>
                  <td>
                    <button className="reader-tag" onClick={() => jump(row.tag)}
                      disabled={!index.has(row.tag)} title="Zoom to duct run">
                      <span className="reader-mono">{row.tag}</span>
                    </button>
                  </td>
                  <td className="reader-mono">{row.storey}</td>
                  <td className="reader-mono">{row.system}</td>
                  <td className="reader-mono">{row.routing}</td>
                  <td className="num-col">{row.width_in}" × {row.depth_in}"</td>
                  <td className="num-col">{row.length_ft} lf</td>
                  <td className="num-col">
                    {row.design_cfm === null ? <span className="muted">—</span> : `${row.design_cfm} cfm`}
                  </td>
                  <td className="reader-mono muted">{row.floor_ref ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
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
