import { writeFileSync } from "node:fs";
import { launchChromium, attachToPage, evaluate, navigate, setViewport, captureScreenshot } from "./lib/cdp.mjs";
const out = process.argv[2];
const browser = await launchChromium({ port: 9337 });
const session = await attachToPage(9337);
try {
  await setViewport(session, { width: 1400, height: 900 });
  await navigate(session, "http://127.0.0.1:8793/");
  await evaluate(session, `
    const d = Date.now() + 90000;
    while (Date.now() < d) { if (window.__haus?.store?.getState?.()?.model?.rooms?.length) return 1;
      await new Promise(r => setTimeout(r, 200)); }
    throw new Error("model never arrived");`);
  for (const [storey, uid, name] of [["attic", "CAR401AAAA", "studio"], ["second", "CSR401AAAA", "plant"]]) {
    for (const surface of ["nordic", "schematic"]) {
      const r = await evaluate(session, `
        const st = window.__haus.store;
        st.getState().setActiveStorey(${JSON.stringify(storey)});
        st.getState().zoomToUid?.(${JSON.stringify(uid)});
        st.getState().setViewMode("3d");
        st.getState().showOnlyTrades(["flooring"]);
        if (st.getState().setSurface) st.getState().setSurface(${JSON.stringify(surface)});
        await new Promise(r => setTimeout(r, 7000));
        return { storey: st.getState().activeStorey, surface: st.getState().surface ?? null };`);
      console.log(name, surface, JSON.stringify(r));
      writeFileSync(`${out}/${name}-${surface}.png`, await captureScreenshot(session));
      if (name === "plant") break;
    }
  }
} finally { browser.kill?.(); }
