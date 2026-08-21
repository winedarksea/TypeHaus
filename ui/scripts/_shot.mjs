import { writeFileSync } from "node:fs";
import { launchChromium, attachToPage, evaluate, navigate, setViewport, captureScreenshot } from "./lib/cdp.mjs";
const wait = (ms) => new Promise((r) => setTimeout(r, ms));
const chrome = await launchChromium({ port: 9333 });
try {
  const session = await attachToPage(9333);
  await setViewport(session, { width: 1600, height: 1000, deviceScaleFactor: 2 });
  await navigate(session, "http://127.0.0.1:8799/");
  await wait(9000);
  console.log(await evaluate(session, `
    const s = window.__haus.store, m = s.getState().model;
    if (!m) return "no model";
    const wall = m.walls.find(w => w.tag === "W-B-BRICK");
    const ops = m.openings.filter(o => o.host === wall.uid || o.host === wall.tag);
    const blanked = {};
    for (const [k, v] of Object.entries(m)) if (Array.isArray(v)) blanked[k] = [];
    s.setState({ model: { ...m, ...blanked, walls: [wall], openings: ops } });
    s.getState().showEverything?.();
    s.getState().setViewMode("3d");
    await new Promise(r => setTimeout(r, 2500));
    s.getState().select(null, null);
    return "ok";
  `));
  await wait(4000);
  writeFileSync(process.argv[2], await captureScreenshot(session));
} finally { await chrome.close(); }
process.exit(0);
