// The agent handoff: a Markdown brief of what this session changed and what is still red, to
// paste into an agent chat so it can pick the house up where the UI left it. Pure.
import type { Finding, Model } from "./types";
import type { SessionEdits } from "../state/sessionEdits";

export interface HandoffProjectInfo {
  name: string;
  // The house directory, once the server publishes it (GET /project); null until then.
  houseDir: string | null;
}

const MAX_LISTED_CHECKS = 12;
// Checks whose FAIL the router can propose a fix for (`haus route --unconnected`).
const ROUTABLE_CHECKS = ["mep.fixture_drain_reach"];

function checkId(finding: Finding): string {
  return finding.code ?? (typeof finding.check_id === "string" ? finding.check_id : "");
}

function tagList(tags: string[]): string {
  return tags.length ? tags.map((tag) => `\`${tag}\``).join(", ") : "—";
}

export function buildHandoff(
  model: Model, edits: SessionEdits, project: HandoffProjectInfo, activeStorey: string | null,
): string {
  const houseArg = project.houseDir ?? ".";
  const lines: string[] = [
    `# Type:Haus handoff — ${project.name}`,
    "",
    `- House: ${project.houseDir ? `\`${project.houseDir}\`` : `${project.name} (path not published by this server)`}`,
    `- Active storey: ${activeStorey ?? "—"}`,
    `- Model revision: \`${model.revision}\``,
    "",
    "## Edited in the UI this session",
  ];
  if (!edits.created.length && !edits.changed.length && !edits.deleted.length) {
    lines.push("", "No edits this session.");
  } else {
    lines.push("", `- Created: ${tagList(edits.created)}`, `- Changed: ${tagList(edits.changed)}`,
      `- Deleted: ${tagList(edits.deleted)}`);
  }

  const attention = Object.entries(edits.impacts).flatMap(([edited, impacts]) => impacts
    .filter((impact) => impact.kind !== "carried")
    .map((impact) => `- \`${impact.tag}\` ${impact.kind === "left_behind" ? "left behind" : "needs review"}`
      + `${impact.tag === edited ? "" : ` (after editing \`${edited}\`)`}: ${impact.reason}`));
  if (attention.length) lines.push("", "## Needs attention", "", ...attention);

  const errors = model.findings.filter((f) => f.severity === "error");
  const fails = model.findings.filter((f) => f.result === "fail");
  const unknowns = model.findings.filter((f) => f.result === "unknown");
  const errorIds = [...new Set(errors.map(checkId).filter(Boolean))].sort();
  lines.push("", "## Checks", "", `- ERROR ${errors.length} · FAIL ${fails.length} · UNKNOWN ${unknowns.length}`);
  if (errorIds.length) {
    const shown = errorIds.slice(0, MAX_LISTED_CHECKS).map((id) => `\`${id}\``).join(", ");
    const more = errorIds.length > MAX_LISTED_CHECKS ? ` and ${errorIds.length - MAX_LISTED_CHECKS} more` : "";
    lines.push(`- ERROR checks: ${shown}${more}`);
  }

  const steps = [`- \`haus check ${houseArg}\` — confirm the reds above and fix them in plan source`];
  if (fails.some((f) => ROUTABLE_CHECKS.includes(checkId(f)))) {
    steps.push(`- \`haus route ${houseArg} --unconnected\` — propose drains for unconnected fixtures`);
  }
  if (activeStorey && !model.rooms.some((room) => room.storey === activeStorey)) {
    steps.push(`- \`/add-room\` — ${activeStorey} has no rooms yet`);
  }
  lines.push("", "## Suggested next step", "", ...steps, "");
  return lines.join("\n");
}
