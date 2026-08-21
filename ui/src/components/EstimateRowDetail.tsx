// The panel under an expanded estimate row: everything the payload knows about one line.
//
// Why it exists: the ranked table answers "what moves the number", and it earns that by
// showing eight columns out of the eighteen fields a row carries. The other ten — the
// material/labour split, the waste treatment, whether tax was already paid, the NAHB and CSI
// accounts — were in the payload, typed in EngineClient.ts, and rendered nowhere, which made
// `haus takeoff --csv` a strictly richer breakdown than this page. This closes that.
//
// Read-only, like the rest of the Estimate reader: prices.toml carries four research passes of
// hand-written provenance in its comments, and a writeback path from a browser table is how
// that gets quietly flattened.

import type { EngineEstimateRow, EngineEstimateSection } from "../engine/EngineClient";
import { rowBasisShares, rowDetailFacts, type DetailFact } from "../model/estimateRowDetail";

/** The row's own material/labour/merged proportions, in the Basis block's colours. */
function BasisBar({ row }: { row: EngineEstimateRow }) {
  const shares = rowBasisShares(row);
  if (!shares.length) return null;
  return (
    <div className="estimate-detail-bar" role="presentation">
      {shares.map((slice) => (
        <span
          key={slice.key}
          className={`estimate-basis-slice is-${slice.key}`}
          style={{ width: `${slice.share * 100}%` }}
        />
      ))}
    </div>
  );
}

function Fact({ fact }: { fact: DetailFact }) {
  return (
    <div className={fact.flag ? "estimate-fact is-flagged" : "estimate-fact"}>
      <dt>{fact.label}</dt>
      <dd>
        <span className={fact.basisPart ? "reader-mono" : undefined}>{fact.text}</span>
        {fact.note && <span className="muted estimate-fact-note">{fact.note}</span>}
      </dd>
    </div>
  );
}

/**
 * `section` is the row's block from the payload — the basis note and the waste treatment live
 * there, and the row cannot answer for either on its own.
 */
export function EstimateRowDetail({ row, section, sectionName }: {
  row: EngineEstimateRow;
  section?: EngineEstimateSection;
  sectionName: string;
}) {
  const facts = rowDetailFacts(row, section);
  return (
    <div className="estimate-detail">
      <BasisBar row={row} />
      <dl className="estimate-facts">
        {facts.map((fact) => <Fact key={fact.key} fact={fact} />)}
        <div className="estimate-fact">
          <dt>Authored in</dt>
          <dd>
            <span className="reader-mono">[{sectionName}]</span>
            <span className="muted estimate-fact-note">
              the prices.toml block to open to change this row
            </span>
          </dd>
        </div>
      </dl>
    </div>
  );
}
