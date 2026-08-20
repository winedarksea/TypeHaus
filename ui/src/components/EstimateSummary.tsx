// The Estimate page's summary blocks: what the total is, what it rests on, and how it is
// built up. Split out of EstimateView so both stay inside the repo's 500-line rule.
//
// Every number here is read straight off the `/costs` payload — the same `estimate_costs`
// payload `haus takeoff` prints — and nothing is recomputed in the browser. Where a figure
// looks surprising (a tax line smaller than rate × total, a markup stage at zero) the block
// says why rather than smoothing it over: an estimate you cannot check is not reviewable.

import type { EngineEstimate, EnginePerSf } from "../engine/EngineClient";
import { formatRange } from "../model/engineCosts";
import {
  basisSlices,
  formatPerSf,
  ladderStages,
} from "../model/engineEstimate";
import { ReaderSection } from "./ReaderShell";

function Money({ value, className }: {
  value: Parameters<typeof formatRange>[0];
  className?: string;
}) {
  return <span className={className ? `reader-mono ${className}` : "reader-mono"}>
    {formatRange(value) ?? "—"}
  </span>;
}

/** The $/sf pair for one total, each chip naming the denominator it used. A $/sf with no
 *  denominator on its face is the number people quote at each other and mean two different
 *  things by — conditioned area is what the energy code grades, gross is what a builder
 *  means by "$/sf", and here they are 15% apart. */
function PerSf({ per, areas }: {
  per: EnginePerSf | undefined;
  areas: Record<string, number> | undefined;
}) {
  if (!per) return null;
  return (
    <span className="estimate-persf">
      {(["conditioned", "gross"] as const).map((name) => {
        const text = formatPerSf(per, name, name === "gross" ? "gross sf" : "cond. sf");
        if (!text) return null;
        const area = areas?.[name];
        return (
          <span key={name} className="reader-chip estimate-persf-chip">
            {text}{area ? ` (${Math.round(area).toLocaleString()} sf)` : ""}
          </span>
        );
      })}
    </span>
  );
}

/** Construction total, furnishings beside it, grand total, each with its own $/sf. */
export function TotalsBlock({ estimate }: { estimate: EngineEstimate }) {
  const perSf = estimate.per_sf;
  const areas = estimate.areas;
  const bid = estimate.bid;
  const excluded = estimate.excluded_total;
  return (
    <ReaderSection
      title="Totals"
      note="The construction total is what the build costs. Furnishings sit beside it, never
        folded in — the payload says they are not part of it."
      count={1}
    >
      <div className="estimate-totals">
        <div className="estimate-total-card">
          <span className="muted">Construction total (net of the ladder)</span>
          <Money value={estimate.total} className="estimate-total-figure" />
          <PerSf per={perSf?.total} areas={areas} />
        </div>
        {bid && (
          <div className="estimate-total-card">
            <span className="muted">Bid total (after waste, contingency, markup, tax)</span>
            <Money value={bid.total} className="estimate-total-figure" />
            <PerSf per={perSf?.bid_total} areas={areas} />
          </div>
        )}
        {excluded && excluded.high > 0 && (
          <div className="estimate-total-card">
            <span className="muted">+ furnishings (beside the total)</span>
            <Money value={excluded} />
          </div>
        )}
        {estimate.grand_total && (
          <div className="estimate-total-card">
            <span className="muted">Grand total (build + furnishings)</span>
            <Money value={estimate.grand_total} />
          </div>
        )}
      </div>
    </ReaderSection>
  );
}

/** material / labour / merged, as three numbers and one proportional bar. */
export function BasisBlock({ estimate }: { estimate: EngineEstimate }) {
  const slices = basisSlices(estimate);
  return (
    <ReaderSection
      title="Basis"
      note="What the construction total is made of. A merged figure is an installed price
        whose material/labour split nobody declared — it is reported whole and never divided."
      count={slices.length}
    >
      {estimate.basis_declared === false && (
        <p className="estimate-warn">
          This house declares no <span className="reader-mono">[basis]</span> table, so the
          split below is a default rather than a statement about these prices.
        </p>
      )}
      <div className="estimate-basis-bar" role="presentation">
        {slices.map((slice) => (
          <span
            key={slice.key}
            className={`estimate-basis-slice is-${slice.key}`}
            style={{ width: `${slice.share * 100}%` }}
            title={`${slice.label}: ${formatRange(slice.value)}`}
          />
        ))}
      </div>
      <ul className="estimate-basis-legend">
        {slices.map((slice) => (
          <li key={slice.key}>
            <span className={`estimate-basis-swatch is-${slice.key}`} aria-hidden="true" />
            <span>{slice.label}</span>
            <Money value={slice.value} />
            <span className="muted">{Math.round(slice.share * 100)}%</span>
          </li>
        ))}
      </ul>
    </ReaderSection>
  );
}

/** The eight rungs of the ladder, zeros included and marked as such. */
export function LadderBlock({ estimate }: { estimate: EngineEstimate }) {
  const stages = ladderStages(estimate);
  const bid = estimate.bid;
  return (
    <ReaderSection
      title="Bid ladder"
      note="net → waste → ordered → contingency → overhead → profit → tax → total. A stage at
        zero is shown off rather than hidden: what this estimate leaves out is part of what
        it says."
      count={stages.length}
    >
      <ul className="estimate-ladder">
        {stages.map((stage) => (
          <li
            key={stage.key}
            className={[
              "estimate-ladder-row",
              stage.emphasis ? "is-emphasis" : "",
              stage.off ? "is-off" : "",
            ].filter(Boolean).join(" ")}
          >
            <span className="estimate-ladder-label">{stage.label}</span>
            {stage.rate !== null && (
              <span className="reader-mono muted estimate-ladder-rate">{stage.rate}</span>
            )}
            {stage.off && <span className="estimate-off-chip">off</span>}
            <Money value={stage.value} className="estimate-ladder-value" />
          </li>
        ))}
      </ul>
      {bid && (
        <p className="muted estimate-ladder-note">
          Sales tax rides on material only. It could not reach{" "}
          <span className="reader-mono">{formatRange(bid.untaxed_merged)}</span> of merged
          material+labour, and skipped{" "}
          <span className="reader-mono">{formatRange(bid.material_tax_already_paid)}</span>{" "}
          of material whose authored price already carries tax — which is why the tax line is
          smaller than the rate times the total.
        </p>
      )}
    </ReaderSection>
  );
}

/** The rows the price file has nothing to say about — this page's to-do list. */
export function UnpricedBlock({ estimate }: { estimate: EngineEstimate }) {
  const unpriced = estimate.unpriced;
  return (
    <ReaderSection
      title="Unpriced"
      note="Quantities the model resolved that prices.toml does not price. They are absent
        from every total above — honestly unpriced, never priced at zero."
      count={unpriced.length}
    >
      <div className="reader-table-scroll estimate-unpriced">
        <table className="reader-table">
          <thead>
            <tr>
              <th>section</th>
              <th>key</th>
              <th className="num-col">quantity</th>
              <th>unit</th>
            </tr>
          </thead>
          <tbody>
            {unpriced.map((row, index) => (
              <tr key={`${row.section}:${row.key}:${index}`}>
                <td className="reader-mono muted">{row.section}</td>
                <td className="reader-mono">{row.key}</td>
                <td className="num-col">{row.quantity.toLocaleString()}</td>
                <td className="muted">{row.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </ReaderSection>
  );
}
