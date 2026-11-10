// A detector picked in 3D: what it is, where it is, what powers it. Read-only; its source
// is the Provenance link.
import type { Alarm } from "../../model/types";
import { formatFtIn } from "../../model/geometry";
import { Provenance } from "../Provenance";

const KIND_LABEL: Record<Alarm["kind"], string> = {
  smoke: "Smoke alarm",
  co: "CO alarm",
  combo: "Smoke/CO alarm",
  heat: "Heat alarm",
  leak: "Leak sensor",
  freeze: "Freeze sensor",
};

export function AlarmInspector({ alarm }: { alarm: Alarm }) {
  return <div>
    <h3>{KIND_LABEL[alarm.kind]} · {alarm.tag}</h3>
    <div className="kv">
      <span className="k">Room</span><span>{alarm.room ?? "—"}</span>
      <span className="k">Storey</span><span>{alarm.storey}</span>
      <span className="k">Circuit</span><span>{alarm.circuit ?? "—"}</span>
      <span className="k">Mounted on</span><span>{alarm.mount}</span>
      <span className="k">Position</span>
      <span>{alarm.x != null && alarm.y != null ? `${formatFtIn(alarm.x)}, ${formatFtIn(alarm.y)}` : "—"}</span>
      <span className="k">Elevation</span><span>{alarm.z != null ? formatFtIn(alarm.z) : "—"}</span>
      <span className="k">uid</span><span className="prov">{alarm.uid}</span>
    </div>
    <Provenance p={alarm.provenance} />
  </div>;
}
