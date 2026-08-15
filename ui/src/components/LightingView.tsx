import { Fragment, useMemo } from "react";
import type {
  Lighting,
  LightingControlRow,
  LightingLoad,
  LightRunTakeoff,
  LuminaireScheduleRow,
} from "../model/types";
import {
  ReaderEmpty, ReaderFilter, ReaderSection, ReaderShell, ReaderTable, TagCell, useReader,
} from "./ReaderShell";

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
    <ReaderTable<LuminaireScheduleRow> rows={rows} rowKey={(row) => row.type} columns={[
      { key: "mark", header: "Mark", cellClass: "reader-mono", cell: (r) => r.mark },
      { key: "description", header: "Description", cell: (r) => r.description },
      { key: "lamp", header: "Lamp", cellClass: "muted", cell: (r) => r.lamp || DASH },
      // A linear type has no per-fixture wattage — it has watts per foot. Showing one in the
      // other's column would misprice the order.
      { key: "watts", header: "Watts", num: true, cell: (r) => r.watts !== null ? num(r.watts, " W")
        : r.watts_per_ft !== null ? `${r.watts_per_ft} W/ft` : DASH },
      { key: "lumens", header: "Lumens", num: true, cell: (r) => num(r.lumens) },
      { key: "cct", header: "CCT", num: true, cell: (r) => r.cct_k ? `${r.cct_k}K` : DASH },
      { key: "cri", header: "CRI", num: true, cell: (r) => r.cri ?? DASH },
      { key: "volts", header: "Volts", num: true, cell: (r) => r.volts },
      { key: "mount", header: "Mount", cellClass: "muted", cell: (r) => r.mount },
      { key: "control", header: "Control", cellClass: "muted", cell: (r) => r.dimming },
      { key: "listing", header: "Listing", cell: (r) => <RatingChip rating={r.rating} /> },
      { key: "qty", header: "Qty", num: true,
        cell: (r) => r.count > 0 ? r.count : `${Math.round(r.length_ft ?? 0)} lf` },
      { key: "locations", header: "Locations", cell: (r) => (
        <div className="reader-tag-cloud">
          {r.rooms.map((room) => (
            // Rooms are not in the tag index (a room is claimed, not placed), so this one
            // stays a plain button rather than a TagCell that would always read disabled.
            <button key={room} className="reader-tag" onClick={() => onZoomRoom(room)}
              title="Zoom to room">
              {room}
            </button>
          ))}
        </div>
      ) },
    ]} />
  );
}

function ControlsTable({ rows, index, onZoom }: {
  rows: LightingControlRow[];
  index: Map<string, string>;
  onZoom: (tag: string) => void;
}) {
  return (
    <ReaderTable<LightingControlRow> rows={rows} rowKey={(row) => row.tag} columns={[
      { key: "load", header: "Load", cell: (r) =>
        <TagCell tag={r.tag} index={index} onJump={onZoom} title="Zoom to fixture" /> },
      { key: "mark", header: "Mark", cellClass: "reader-mono", cell: (r) => r.mark || DASH },
      { key: "room", header: "Room", cellClass: "muted", cell: (r) => r.room || DASH },
      // A 24V run has no branch circuit of its own; its supply does. Saying "via ED-…-PSU" is
      // the honest answer, not a blank.
      { key: "fed", header: "Fed from", cellClass: "reader-mono",
        cell: (r) => r.circuit || (r.psu ? <span className="muted">via {r.psu}</span> : DASH) },
      { key: "switched", header: "Switched by", cell: (r) => r.switches.length > 0 ? (
        <div className="reader-tag-cloud">
          {r.switches.map((tag) => (
            <TagCell key={tag} tag={tag} index={index} onJump={onZoom} title="Zoom to switch" />
          ))}
        </div>
      ) : r.integral_switch ? (
        <span className="muted">switch on fixture</span>
      ) : (
        <span className="muted">{DASH}</span>
      ) },
      { key: "control", header: "Control", cell: (r) => <>
        {Array.from(new Set(r.controls)).map((control) => (
          <span key={control} className="reader-chip">{control}</span>
        ))}
        {r.ways > 1 && <span className="reader-chip">{r.ways}-way</span>}
        {/* NEC 210.7: two circuits in one box need a simultaneous disconnect. Worth seeing;
            the engine reports it as advisory, not as a failure. */}
        {r.cross_circuit.length > 0 && (
          <span className="badge confirm" title={`Switched from another circuit: ${r.cross_circuit.join(", ")}`}>
            cross-circuit
          </span>
        )}
      </> },
    ]} />
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
            <TagCell tag={supply.psu} index={index} onJump={onZoom} title="Zoom to supply"
              className="reader-card-title" />
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
              <TagCell key={run.tag} tag={run.tag} index={index} onJump={onZoom} title="Zoom to run">
                {run.tag} · {run.length_ft} lf
              </TagCell>
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
  const { model, data: lighting, index, filter, setFilter, needle, jump, close } =
    useReader<Lighting>((m) => m.electrical?.lighting);
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

  if (!lighting || lighting.schedule.length === 0) {
    return (
      <ReaderEmpty title="Lighting" subtitle="no luminaires modeled" onClose={close}>
        This model carries no lighting take-off — either nothing is lit yet, or it was
        built with an engine older than the lighting plan.
      </ReaderEmpty>
    );
  }

  const fixtures = lighting.schedule.reduce((total, row) => total + row.count, 0);
  const uncontrolled = lighting.controls.filter(
    (row) => row.switches.length === 0 && !row.integral_switch).length;

  return (
    <ReaderShell
      title="Lighting"
      subtitle={`${lighting.schedule.length} marks · ${fixtures} fixtures · ${lighting.runs.total_length_ft} lf of tape`}
      onClose={close}
      toolbar={<ReaderFilter value={filter} onChange={setFilter}
        placeholder="Filter marks, rooms, fixtures…" label="Filter lighting" />}
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
