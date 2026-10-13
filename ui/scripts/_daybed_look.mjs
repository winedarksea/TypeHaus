import { launchChromium, attachToPage, evaluate, navigate, setViewport, captureScreenshot } from "./lib/cdp.mjs";
import { writeFileSync } from "node:fs";
const out = process.argv[2];
const browser = await launchChromium({ port: 9337 });
const session = await attachToPage(9337);
try {
  await setViewport(session, { width: 1400, height: 900 });
  await navigate(session, "http://127.0.0.1:8797/");
  await evaluate(session, `
    const d = Date.now() + 90000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.walls?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);
  const info = await evaluate(session, `
    const st = window.__haus.store; const m = st.getState().model;
    const bed = (m.canvas_objects || []).find(o => o.tag === "FURN-SG-DAYBED");
    return JSON.stringify({uid: bed?.uid, susp: bed?.suspension, trades: Object.keys(st.getState().visibleTrades)});`);
  console.log(info);
  const { uid } = JSON.parse(info);
  for (const [label, pose] of [
    ["all", `st.getState().showEverything()`],
    ["framing", `st.getState().showOnlyTrades(["framing","furniture"])`],
  ]) {
    await evaluate(session, `
      const st = window.__haus.store;
      st.getState().zoomToUid("${uid}");
      st.getState().setViewMode("3d");
      ${pose};
      const d = Date.now() + 40000; let c = null;
      while (Date.now() < d) { c = document.querySelector("canvas");
        if (c && c.getBoundingClientRect().width > 100) break; await new Promise(r => setTimeout(r, 200)); }
      await new Promise(r => setTimeout(r, 6000)); return 1;`);
    const png = await captureScreenshot(session);
    writeFileSync(`${out}/daybed_${label}.png`, Buffer.from(png, "base64"));
  }
} finally { session.close(); await browser.close(); }
