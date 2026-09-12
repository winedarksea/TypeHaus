// The trade toggles in the LIVE 3D viewer, end to end (→ model/tradeVisibility.ts).
//
//     .venv/bin/haus serve houses/catlin --port 8791     # in another shell
//     cd ui && npm run build && node scripts/trade-check.mjs
//
// Unit tests prove a band is tagged with its trade set and that `applyTradeVisibility`
// flips it; only a real render proves the scene the camera sees changes with the chips.
// Screenshot PNG size is the proxy: an isolated trade is a far simpler picture than the
// whole house, and every trade off is the emptiest of all. Chromium runs headless with
// swiftshader; `--disable-gpu` blanks Panel3D with no error.
import { launchChromium, attachToPage, evaluate, navigate, setViewport, captureScreenshot } from "./lib/cdp.mjs";

const browser = await launchChromium({ port: 9334 });
const session = await attachToPage(9334);
try {
  await setViewport(session, { width: 1400, height: 900 });
  await navigate(session, process.env.HAUS_URL ?? "http://127.0.0.1:8791/");
  await evaluate(session, `
    const d = Date.now() + 60000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.walls?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);
  await evaluate(session, `
    const st = window.__haus.store;
    st.getState().setViewMode("3d");
    st.getState().showEverything();
    const d = Date.now() + 40000; let c = null;
    while (Date.now() < d) { c = document.querySelector("canvas");
      if (c && c.getBoundingClientRect().width > 100) break; await new Promise(r => setTimeout(r, 200)); }
    if (!c) throw new Error("3D canvas never mounted");
    await new Promise(r => setTimeout(r, 5000));
    return 1;`);

  const shot = async (label, pose) => {
    await evaluate(session, `const st = window.__haus.store; ${pose}; await new Promise(r => setTimeout(r, 1500)); return 1;`);
    const png = await captureScreenshot(session);
    const bytes = png.length;
    const state = await evaluate(session, `
      const v = window.__haus.store.getState().visibleTrades;
      return Object.keys(v).filter((t) => v[t]).length;`);
    console.log(`${label.padEnd(22)} ${String(bytes).padStart(8)} bytes, ${state} trades on`);
    return bytes;
  };
  const allOn = await shot("everything", `st.getState().showEverything()`);
  const wallsOff = await shot("walls group off",
    `st.getState().showEverything(); st.getState().setTradesVisible(["siding","insulation","drywall","paint"], false)`);
  const concreteOnly = await shot("only concrete", `st.getState().showOnlyTrades(["concrete"])`);
  const drainageOnly = await shot("only drainage", `st.getState().showOnlyTrades(["drainage"])`);
  const nothing = await shot("nothing", `st.getState().showOnlyTrades([])`);
  const back = await shot("everything again", `st.getState().showEverything()`);

  const fail = (m) => { throw new Error(m); };
  if (!(wallsOff < allOn)) fail("hiding the Walls group did not simplify the picture");
  if (!(concreteOnly < wallsOff)) fail("only-concrete is not simpler than walls-off");
  if (!(nothing < concreteOnly)) fail("only-concrete drew nothing beyond the empty scene");
  if (!(nothing < drainageOnly)) fail("only-drainage drew nothing (bedding/leaders/tile should show)");
  if (Math.abs(back - allOn) > allOn * 0.02) fail("restoring every trade did not restore the picture");
  console.log("trade toggles drive the 3D scene: OK");
} finally { session.close(); await browser.close(); }
