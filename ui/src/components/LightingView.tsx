import { Fragment, useMemo, useState } from "react";
import { useStore } from "../state/store";
import { uidByTag } from "../model/tagIndex";
import type {
  LightingControlRow,
  LightingLoad,
  LightRunTakeoff,
  LuminaireScheduleRow,
} from "../model/types";
import { ReaderSection, ReaderShell } from "./ReaderShell";

// "Lighting" — the on-screen twin of the E-602 permit sheet, beside Circuits rather than
// inside it. Both read model.json's `electrical` block, which is the engine take-off
// verbatim; this file is presentation only for the same reason CircuitsView is. A schedule
// the browser recomputed could disagree with the drawing, and the drawing gets built.
//
// The split is not arbitrary. Circuits answers "does this house fit its service"; this
// answers "what hangs where, what colour is it, and can I turn it off" — and the second
// question is asked by someone who does not care about breaker poles.

const DASH = "—";

function num(value: number | null, suffix = "", digits = 0): string {
  return value === null || value === undefined ? DASH : `${value.toLocaleString(undefined, {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  })}${suffix}`;
}

// A wet/damp listing is the one column here that is a compliance fact rather than a
// preference, so it gets a chip and the rest stay plain text.
function RatingChip({ rating }: { rating: string }) {
  if (rating === "dry") return <span className="muted">dry</span>;
  return <span className="reader-chip">{rating}</span>;
}

function ScheduleTable({ rows, onZoomRoom }: {
  rows: LuminaireScheduleRow[];
  onZoomRoom: (tag: string) => void;
}) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Mark</th>
            <th>Description</th>
            <th>Lamp</th>
            <th className="num-col">Watts</th>
            <th className="num-col">Lumens</th>
            <th className="num-col">CCT</th>
            <th className="num-col">CRI</th>
            <th className="num-col">Volts</th>
            <th>Mount</th>
            <th>Control</th>
            <th>Listing</th>
            <th className="num-col">Qty</th>
            <th>Locations</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.type}>
              <td className="reader-mono">{row.mark}</td>
              <td>{row.description}</td>
              <td className="muted">{row.lamp || DASH}</td>
              {/* A linear type has no per-fixture wattage — it has watts per foot. Showing
                  one in the other's column would misprice the order. */}
              <td className="num-col">
                {row.watts !== null ? num(row.watts, " W")
                  : row.watts_per_ft !== null ? `${row.watts_per_ft} W/ft` : DASH}
              </td>
              <td className="num-col">{num(row.lumens)}</td>
              <td className="num-col">{row.cct_k ? `${row.cct_k}K` : DASH}</td>
              <td className="num-col">{row.cri ?? DASH}</td>
              <td className="num-col">{row.volts}</td>
              <td className="muted">{row.mount}</td>
              <td className="muted">{row.dimming}</td>
              <td><RatingChip rating={row.rating} /></td>
              <td className="num-col">
                {row.count > 0 ? row.count : `${Math.round(row.length_ft ?? 0)} lf`}
              </td>
              <td>
                <div className="reader-tag-cloud">
                  {row.rooms.map((room) => (
                    <button key={room} className="reader-tag" onClick={() => onZoomRoom(room)}
                      title="Zoom to room">
                      {room}
                    </button>
                  ))}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ControlsTable({ rows, index, onZoom }: {
  rows: LightingControlRow[];
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Load</th>
            <th>Mark</th>
            <th>Room</th>
            <th>Fed from</th>
            <th>Switched by</th>
            <th>Control</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.tag}>
              <td>
                <button className="reader-tag" onClick={() => onZoom(row.tag)}
                  disabled={!index.has(row.tag)} title="Zoom to fixture">
                  {row.tag}
                </button>
              </td>
              <td className="reader-mono">{row.mark || DASH}</td>
              <td className="muted">{row.room || DASH}</td>
              {/* A 24V run has no branch circuit of its own; its supply does. Saying
                  "via ED-…-PSU" is the honest answer, not a blank. */}
              <td className="reader-mono">
                {row.circuit || (row.psu ? <span className="muted">via {row.psu}</span> : DASH)}
              </td>
              <td>
                {row.switches.length > 0 ? (
                  <div className="reader-tag-cloud">
                    {row.switches.map((tag) => (
                      <button key={tag} className="reader-tag" onClick={() => onZoom(tag)}
                        disabled={!index.has(tag)} title="Zoom to switch">
                        {tag}
                      </button>
                    ))}
                  </div>
                ) : row.integral_switch ? (
                  <span className="muted">switch on fixture</span>
                ) : (
                  <span className="muted">{DASH}</span>
                )}
              </td>
              <td>
                {Array.from(new Set(row.controls)).map((control) => (
                  <span key={control} className="reader-chip">{control}</span>
                ))}
                {row.ways > 1 && <span className="reader-chip">{row.ways}-way</span>}
                {/* NEC 210.7: two circuits in one box need a simultaneous disconnect.
                    Worth seeing; the engine reports it as advisory, not as a failure. */}
                {row.cross_circuit.length > 0 && (
                  <span className="badge confirm" title={`Switched from another circuit: ${row.cross_circuit.join(", ")}`}>
                    cross-circuit
                  </span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SupplyCards({ runs, index, onZoom }: {
  runs: LightRunTakeoff;
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  const byPsu = useMemo(() => {
    const map = new Map<string, typeof runs.runs>();
    for (const run of runs.runs) {
      const key = run.psu ?? "(line voltage)";
      map.set(key, [...(map.get(key) ?? []), run]);
    }
    return map;
  }, [runs]);

  return (
    <Fragment>
      {runs.supplies.map((supply) => (
        <div key={supply.psu} className="reader-card">
          <div className="reader-card-head">
            <button className="reader-tag reader-card-title" onClick={() => onZoom(supply.psu)}
              disabled={!index.has(supply.psu)} title="Zoom to supply">
              {supply.psu}
            </button>
            {/* The verdict is the reason this card exists: a driver run at its nameplate
                does not last, so the sizing shown is 125% of connected, not connected. */}
            <span className={`badge ${supply.adequate === false ? "confirm" : ""}`}>
              {supply.adequate === null ? "rating unstated"
                : supply.adequate ? "adequately sized" : "undersized"}
            </span>
            <span className="muted">{supply.type ?? DASH}</span>
          </div>
          <div className="kv">
            <span className="k">Tape driven</span>
            <span>{supply.length_ft} lf · {num(supply.connected_watts, " W")}</span>
            <span className="k">Required at 125%</span>
            <span>{num(supply.required_watts, " W")}</span>
            <span className="k">Supply rating</span>
            <span>{num(supply.rated_watts, " W")}</span>
          </div>
          <div className="reader-tag-cloud">
            {(byPsu.get(supply.psu) ?? []).map((run) => (
              <button key={run.tag} className="reader-tag" onClick={() => onZoom(run.tag)}
                disabled={!index.has(run.tag)} title="Zoom to run">
                {run.tag} · {run.length_ft} lf
              </button>
            ))}
          </div>
        </div>
      ))}
    </Fragment>
  );
}

function LoadCard({ load }: { load: LightingLoad }) {
  const share = load.allowance_va > 0
    ? Math.round((load.total_connected_va / load.allowance_va) * 100) : 0;
  return (
    <div className="reader-card">
      <div className="reader-card-head">
        <span className="reader-card-title">
          {Math.round(load.total_connected_va).toLocaleString()} VA connected
        </span>
        <span className="badge">{share}% of the allowance</span>
      </div>
      <div className="kv">
        <span className="k">Conditioned area</span>
        <span>{Math.round(load.conditioned_area_ft2).toLocaleString()} sf</span>
        <span className="k">NEC 220.82 allowance</span>
        <span>
          {Math.round(load.allowance_va).toLocaleString()} VA
          {" "}at {load.allowance_va_per_ft2} VA/sf
        </span>
        {load.per_circuit.map((row) => (
          <Fragment key={row.circuit}>
            <span className="k">{row.circuit}</span>
            <span>{row.fixtures} fixtures · {Math.round(row.connected_va).toLocaleString()} VA</span>
          </Fragment>
        ))}
      </div>
      <div className="muted" style={{ marginTop: 6 }}>{load.basis}</div>
    </div>
  );
}

export function LightingView() {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);
  const [filter, setFilter] = useState("");

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const lighting = model?.electrical?.lighting ?? null;

  const needle = filter.trim().toLowerCase();
  const schedule = useMemo(() => {
    const rows = lighting?.schedule ?? [];
    return needle
      ? rows.filter((row) => `${row.mark} ${row.description} ${row.type} ${row.rooms.join(" ")}`
        .toLowerCase().includes(needle))
      : rows;
  }, [lighting, needle]);
  const controls = useMemo(() => {
    const rows = lighting?.controls ?? [];
    return needle
      ? rows.filter((row) => `${row.tag} ${row.mark} ${row.room ?? ""} ${row.switches.join(" ")}`
        .toLowerCase().includes(needle))
      : rows;
  }, [lighting, needle]);

  if (!model) return null;

  // Same jump contract as every other reader: zoom the plan, then get out of its way.
  const jump = (tag: string) => {
    const uid = index.get(tag);
    if (uid) {
      zoomToUid(uid);
      setDetailView("none");
    }
  };

  if (!lighting || lighting.schedule.length === 0) {
    return (
      <ReaderShell title="Lighting" subtitle="no luminaires modeled"
        onClose={() => setDetailView("none")}>
        <div className="muted">
          This model carries no lighting take-off — either nothing is lit yet, or it was
          built with an engine older than the lighting plan.
        </div>
      </ReaderShell>
    );
  }

  const fixtures = lighting.schedule.reduce((total, row) => total + row.count, 0);
  const uncontrolled = lighting.controls.filter(
    (row) => row.switches.length === 0 && !row.integral_switch).length;

  return (
    <ReaderShell
      title="Lighting"
      subtitle={`${lighting.schedule.length} marks · ${fixtures} fixtures · ${lighting.runs.total_length_ft} lf of tape`}
      onClose={() => setDetailView("none")}
      toolbar={
        <input
          value={filter}
          placeholder="Filter marks, rooms, fixtures…"
          onChange={(event) => setFilter(event.target.value)}
          aria-label="Filter lighting"
          style={{ padding: "5px 7px", minWidth: 200 }}
        />
      }
    >
      <ReaderSection
        title="Luminaire schedule"
        note="One row per installed type, keyed by the schedule mark the E-2xx plans label fixtures with. Blank photometrics are unstated in the catalog, not zero."
        count={schedule.length}
      >
        <ScheduleTable rows={schedule} onZoomRoom={jump} />
      </ReaderSection>

      <ReaderSection
        title="Controls"
        note={
          uncontrolled > 0
            ? `${uncontrolled} load(s) name no switch and carry none on the fixture.`
            : "Every load names a switch that exists, or carries one on the fixture. Switch legs are stated here; the plans draw them as dashed lines."
        }
        count={controls.length}
      >
        <ControlsTable rows={controls} index={index} onZoom={jump} />
      </ReaderSection>

      <ReaderSection
        title="LED runs and 24V supplies"
        note="Cove and railing tape is priced by the lineal foot off the type's watts per foot; each supply is sized at 125% of the tape it drives, summed across every run on it."
        count={lighting.runs.supplies.length}
      >
        <SupplyCards runs={lighting.runs} index={index} onZoom={jump} />
      </ReaderSection>

      <ReaderSection
        title="Connected lighting load"
        note="What is actually connected, beside the area allowance the service calculation uses. The two are different questions and the sheet prints both."
        count={1}
      >
        <LoadCard load={lighting.connected_va} />
      </ReaderSection>
    </ReaderShell>
  );
}
