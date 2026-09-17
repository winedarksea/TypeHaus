// The agent handoff names what changed, what the edits left for review, and what is red.
import type { Model } from "./types";
import { buildHandoff } from "./handoff";
import { emptySessionEdits } from "../state/sessionEdits";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runHandoffTests(): void {
  const model = {
    revision: "abc", rooms: [], findings: [
      { severity: "error", code: "integrity.stack_ambiguous", message: "x", result: "fail" },
      { severity: "warn", code: "mep.fixture_drain_reach", message: "y", result: "fail" },
      { severity: "info", code: "code.R303_1", message: "z", result: "unknown" },
    ],
  } as unknown as Model;
  const edits = {
    ...emptySessionEdits(), created: ["F-2"], changed: ["FX-1"],
    impacts: { "FX-1": [
      { tag: "PR-1", kind: "carried" as const, reason: "drain follows" },
      { tag: "FX-1", kind: "left_behind" as const, reason: "attachment to W-3 dropped" },
    ] },
  };
  const text = buildHandoff(model, edits, { name: "starter", houseDir: null }, "main");
  assert(text.includes("# Type:Haus handoff — starter"), "titled with the project name");
  assert(text.includes("Active storey: main"), "names the active storey");
  assert(text.includes("Created: `F-2`") && text.includes("Changed: `FX-1`"), "lists created and changed tags");
  assert(text.includes("`FX-1` left behind: attachment to W-3 dropped"), "left-behind impacts carry their reason");
  assert(!text.includes("drain follows"), "carried impacts are not attention items");
  assert(text.includes("ERROR 1 · FAIL 2 · UNKNOWN 1"), "counts ERROR / FAIL / UNKNOWN");
  assert(text.includes("ERROR checks: `integrity.stack_ambiguous`"), "names the ERROR check ids");
  assert(text.includes("haus route . --unconnected"), "an unconnected fixture suggests the router");
  assert(text.includes("/add-room"), "a storey with no rooms suggests adding one");

  const quiet = buildHandoff({ ...model, findings: [], rooms: [{ storey: "main" }] } as unknown as Model,
    emptySessionEdits(), { name: "catlin", houseDir: "houses/catlin" }, "main");
  assert(quiet.includes("No edits this session.") && quiet.includes("`houses/catlin`"), "an idle session says so");
  assert(quiet.includes("haus check houses/catlin") && !quiet.includes("--unconnected") && !quiet.includes("/add-room"),
    "suggestions follow the house's actual state");

  console.log("Agent handoff tests passed.");
}
