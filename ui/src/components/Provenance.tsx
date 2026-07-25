// "Where does this come from?" badge, shared by every inspector panel. A resolved record either
// traces back to a file:line in the house's plan source (the loader captured it) or it does not,
// in which case the only way to change it is to edit the code that generates it.
import type { Provenance as ProvenanceRecord } from "../model/types";

export function Provenance({ p }: { p: ProvenanceRecord | null }) {
  if (!p) return <span className="badge">edit in code</span>;
  if (p.editable === false) {
    // Runtime-captured (params-generated) authorship: show where it's defined, but the
    // only way to change it is still the generating code.
    return (
      <span className="prov">
        {p.file}:{p.line} <span className="badge">edit in code</span>
      </span>
    );
  }
  return (
    <span className="prov">
      {p.file}:{p.line}
    </span>
  );
}
