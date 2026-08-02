import { useMemo } from "react";
import { useStore } from "../state/store";
import { uidByTag } from "../model/tagIndex";
import type { DataDeviceRow, DataRacewayRow, PoeBudget } from "../model/types";
import { ReaderSection, ReaderShell } from "./ReaderShell";

// "Data" — the on-screen twin of the E-603 permit sheet, and the fourth reader over
// model.json's `electrical` block beside Circuits and Lighting. Presentation only for the
// same reason those two are: a schedule the browser recomputed could disagree with the
// drawing, and the drawing is the one that gets built (→ takeoff/data.py).
//
// It is a separate page rather than a section of Circuits because the trades are separate
// on site — comms conductors may not share a raceway with power (NEC 800.133, 725) — and
// because the questions differ: Circuits asks whether the house fits its service, this asks
// what reaches each room and whether the switch can still feed one more thing.

const DASH = "—";

function num(value: number | null | undefined, suffix = "", digits = 0): string {
  return value === null || value === undefined ? DASH : `${value.toLocaleString(undefined, {
    minimumFractionDigits: digits, maximumFractionDigits: digits,
  })}${suffix}`;
}

function DeviceTable({ rows, onZoom }: {
  rows: DataDeviceRow[];
  onZoom: (tag: string) => void;
}) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th>Tag</th>
            <th>Product</th>
            <th>Room</th>
            <th>Mount</th>
            <th className="num-col">Elev</th>
            <th className="num-col">PoE</th>
            <th>Power</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.tag}>
              <td>
                <button className="linkish reader-mono" onClick={() => onZoom(row.tag)}
                        title="Show in plan">{row.tag}</button>
              </td>
              <td>{row.type_name || row.type_ref || DASH}</td>
              <td className="muted">{row.room || DASH}</td>
              <td className="muted">{row.mount}</td>
              <td className="num-col">{num(row.mount_elevation_ft, "'", 1)}</td>
              <td className="num-col">{num(row.poe_watts, " W")}</td>
              {/* A device with no circuit is not unassigned — it is powered over its data
                  cable, which is a different fact and reads as one. */}
              <td className="muted">
                {row.circuit ? row.circuit : <span className="reader-chip">PoE</span>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function RacewayTable({ rows }: { rows: DataRacewayRow[] }) {
  return (
    <div className="reader-table-scroll">
      <table className="reader-table">
        <thead>
          <tr>
            <th className="num-col">Trade size</th>
            <th>Carries</th>
            <th className="num-col">Runs</th>
            <th className="num-col">LF</th>
            <th>Tags</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.trade_size_in}-${row.service}`}>
              <td className="num-col reader-mono">{row.trade_size_in}"</td>
              <td>
                {row.service === "spare"
                  ? <span className="reader-chip">spare · capped</span>
                  : row.service}
              </td>
              <td className="num-col">{row.runs}</td>
              <td className="num-col">{num(row.length_ft, "", 1)}</td>
              <td className="muted">{row.tags.join(", ")}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PoeCard({ budget }: { budget: PoeBudget }) {
  const unknown = budget.unknown_devices ?? 0;
  return (
    <div className="reader-card">
      <div className="reader-card-head">
        <span className="reader-card-title">
          {num(budget.connected_watts, " W")} connected over {budget.powered_devices ?? 0} port
          {(budget.powered_devices ?? 0) === 1 ? "" : "s"}
        </span>
        {/* An unrated device is the one thing that can make a comfortable budget wrong, so
            it gets the warning treatment rather than being folded into the total. */}
        {unknown > 0 && <span className="badge confirm">{unknown} unrated</span>}
      </div>
      <div className="kv">
        <span className="k">Low-voltage devices</span>
        <span>{budget.devices ?? 0}</span>
        <span className="k">Powered over ethernet</span>
        <span>{budget.powered_devices ?? 0}</span>
        {unknown > 0 && (
          <>
            <span className="k">PoE draw not stated</span>
            <span>{unknown} — the total below is a floor, not a total</span>
          </>
        )}
        <span className="k">Connected PoE load</span>
        <span>{num(budget.connected_watts, " W")}</span>
      </div>
      <p className="muted reader-section-note">
        This load lands on the switch, not on the panel schedule — a PoE device names no
        branch circuit. The switch's own draw is on its circuit like any other appliance.
      </p>
    </div>
  );
}

export function DataView() {
  const model = useStore((s) => s.model);
  const setDetailView = useStore((s) => s.setDetailView);
  const zoomToUid = useStore((s) => s.zoomToUid);

  const index = useMemo(() => (model ? uidByTag(model) : new Map<string, string>()), [model]);
  const data = model?.electrical?.data ?? null;

  if (!model) return null;

  // Same jump contract as the other readers: zoom the plan, then get out of its way.
  const jump = (tag: string) => {
    const uid = index.get(tag);
    if (uid) {
      zoomToUid(uid);
      setDetailView("none");
    }
  };

  if (!data) {
    return (
      <ReaderShell title="Data" subtitle="no low-voltage take-off"
                   onClose={() => setDetailView("none")}>
        <div className="muted">
          This model carries no structured cabling — rebuild with a current engine, or author
          a data device and a raceway to reach it.
        </div>
      </ReaderShell>
    );
  }

  const devices = data.devices ?? [];
  const raceways = data.raceways ?? [];
  const budget = data.poe_budget ?? {};

  return (
    <ReaderShell
      title="Data"
      subtitle={`${devices.length} device${devices.length === 1 ? "" : "s"} · E-603`}
      onClose={() => setDetailView("none")}
    >
      <ReaderSection
        title="Low-voltage devices"
        note="Every structured-cabling endpoint: the head-end enclosure, the access points, and any jack or camera on them."
        count={devices.length}
      >
        <DeviceTable rows={devices} onZoom={jump} />
      </ReaderSection>

      <ReaderSection
        title="Data and spare raceways"
        note="Comms pipe, billed apart from the power conduit because it is a separate order pulled by a separate trade. A capped spare is listed with them — it is what can still be pulled."
        count={raceways.length}
      >
        <RacewayTable rows={raceways} />
      </ReaderSection>

      <ReaderSection
        title="PoE budget"
        note="Connected load on the switch, which is the number that decides when the next device needs a bigger one."
        count={devices.length ? 1 : 0}
      >
        <PoeCard budget={budget} />
      </ReaderSection>
    </ReaderShell>
  );
}
