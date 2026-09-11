import { useState } from "react";
import type { Visit } from "../../model/scheduleTypes";
import { blockers } from "../../model/schedule";

/**
 * One page to hand a sub when they arrive, as text you can copy or print.
 *
 * Plain text on purpose. It gets pasted into a message, read off a phone in a driveway, or
 * printed and left on the tailgate, and every one of those is a place a styled card is
 * worse than a list. It states scope, exclusions, who supplies what, the open holds and the
 * inspection status — and nothing the model does not actually know.
 */
export function ArrivalBrief({ visit, sheets, contractorName }: {
  visit: Visit;
  sheets: string[];
  contractorName: string | null;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const text = briefText(visit, sheets, contractorName);

  return (
    <section className="site-section">
      <button
        className="site-section-head site-section-toggle"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        Arrival brief
        <span className="site-list-support">copy or print</span>
      </button>
      {open && (
        <>
          <div className="site-action-row">
            <button
              className="site-button"
              onClick={() => {
                void navigator.clipboard?.writeText(text)
                  .then(() => setCopied(true))
                  .catch(() => setCopied(false));
              }}
            >
              {copied ? "Copied" : "Copy"}
            </button>
            <button className="site-button" onClick={() => window.print()}>Print</button>
          </div>
          <pre className="site-brief">{text}</pre>
        </>
      )}
    </section>
  );
}

/** The brief as text. Exported so it can be tested without a DOM. */
export function briefText(visit: Visit, sheets: string[], contractorName: string | null)
: string {
  const lines: string[] = [visit.label, "=".repeat(visit.label.length), ""];
  if (contractorName) lines.push(`Sub: ${contractorName}`);
  if (visit.booked?.date) {
    lines.push(`Booked: ${visit.booked.date}${visit.booked.window
      ? ` ${visit.booked.window}` : ""}`);
  } else if (visit.planned) {
    lines.push(`Planned (not confirmed): ${visit.planned}`);
  } else {
    lines.push("Not booked yet.");
  }
  if (visit.duration_days) lines.push(`Days on site: ${visit.duration_days}`);

  lines.push("", "SCOPE");
  if (visit.rows.length) {
    lines.push(...visit.rows.map((row) => `  ${row.section}:${row.key}`));
  } else {
    lines.push("  the whole package — no rows were carved out");
  }
  if (visit.element_tags.length) {
    lines.push(`  elements: ${visit.element_tags.slice(0, 20).join(", ")}`
      + (visit.element_tags.length > 20
        ? ` (+${visit.element_tags.length - 20} more)` : ""));
  }

  // Exclusions are stated, not implied: the next arrival's work is the commonest thing a
  // sub assumes is theirs, and the commonest thing nobody wrote down.
  lines.push("", "NOT IN THIS VISIT");
  lines.push("  anything not listed under SCOPE above — ask before you start it");
  if (!visit.blocks_successors) {
    lines.push("  this visit is deliberately late in the sequence; nothing waits on it");
  }

  if (visit.checkpoints.length) {
    lines.push("", "STOPS");
    lines.push(...visit.checkpoints.map((point) =>
      `  ${point.status === "done" ? "[x]" : "[ ]"} ${point.label || point.id}`
      + (point.after.length ? ` — after ${point.after.join(", ")}` : "")
      + (point.cure_days ? ` (+${point.cure_days} day cure)` : "")));
  }

  const holds = blockers(visit);
  if (holds.length) {
    lines.push("", "OPEN BEFORE WORK STARTS");
    lines.push(...holds.map((hold) => `  - ${hold.label}`
      + (hold.owner ? ` (on ${hold.owner})` : "")));
  }

  if (visit.materials.length) {
    lines.push("", "WHO SUPPLIES WHAT");
    lines.push(...visit.materials.map((item) =>
      `  ${item.received ? "[on site]" : "[not yet]"} ${item.label || item.id}`
      + (item.source ? ` — ${item.source}` : "")));
  }

  const inspections = visit.constraints.filter((c) => c.kind === "inspection");
  if (inspections.length) {
    lines.push("", "INSPECTIONS");
    lines.push(...inspections.map((one) =>
      `  ${one.cleared ? "[passed]" : "[open]  "} ${one.label}`));
  }

  if (visit.handoff.length) {
    lines.push("", "LEAVE IN PLACE (walked afterwards)");
    lines.push(...visit.handoff.map((item) =>
      `  ${item.checked ? "[x]" : "[ ]"} ${item.label}`));
  }

  if (sheets.length) lines.push("", `SHEETS: ${sheets.join(", ")}`);
  if (visit.note) lines.push("", visit.note);
  return lines.join("\n");
}
