// Live report navigation, refresh races, Retry, summary states, and responsive screenshots.
// Run after building and serving: node scripts/reports-check.mjs [http://127.0.0.1:8877]
import { mkdir, writeFile } from "node:fs/promises";
import { attachToPage, captureScreenshot, evaluate, launchChromium, navigate, setViewport } from "./lib/cdp.mjs";

const url = process.argv[2] ?? "http://127.0.0.1:8877";
const browser = await launchChromium({ port: 9237 });
const session = await attachToPage(browser.port);
const assert = (condition, message) => { if (!condition) throw new Error(message); };
const wait = async (predicate) => evaluate(session, `
  const deadline = Date.now() + 60000;
  while (Date.now() < deadline) {
    if (${predicate}) return true;
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error("Report check timed out: " + ${JSON.stringify(predicate)});
`);
const pose = (body) => evaluate(session, `const store = window.__haus.store; ${body}`);

try {
  await navigate(session, url);
  await wait("(window.__haus?.store.getState().engineReady && window.__haus.store.getState().model?.walls?.length) || window.__haus?.store.getState().error");
  const boot = await pose("return { ready: store.getState().engineReady, error: store.getState().error };");
  assert(boot.ready, `engine boot failed: ${boot.error}`);
  await mkdir(".shots/reports", { recursive: true });
  for (const viewport of [{ id: "desktop", width: 1600, height: 1000 },
    { id: "phone", width: 390, height: 844, mobile: true }]) {
    await setViewport(session, viewport);
    for (const theme of ["light", "dark"]) {
      await session.send("Emulation.setEmulatedMedia", {
        features: [{ name: "prefers-color-scheme", value: theme }],
      });
      await pose(`localStorage.setItem("typehaus.theme-preference", "system");
        document.documentElement.dataset.theme = ${JSON.stringify(theme)};
        store.getState().openDocuments("reports");`);
      await wait("document.querySelectorAll('.doc-card').length > 3");
      const cards = await evaluate(session, "return [...document.querySelectorAll('.doc-card')].map((card) => card.textContent);");
      for (const label of ["Engineering calculations", "Building science", "Space & dimensions"]) {
        assert(cards.some((card) => card.includes(label)), `missing ${label} card`);
      }
      for (const [id, label, ready] of [
        ["engineering", "Engineering calculations", "document.querySelector('.doc-detail .md-body h1')"],
        ["building-science", "Building science", "document.querySelectorAll('.reader-section').length === 3"],
        ["space", "Space & dimensions", "document.querySelectorAll('.reader-section').length === 3"],
      ]) {
        await pose(`store.getState().setReaderOrigin("documents"); store.getState().setDetailView(${JSON.stringify(id)});`);
        await wait(`document.querySelector('.workbench')?.getAttribute('aria-label') === ${JSON.stringify(label)} && (${ready})`);
        if (id === "engineering" && viewport.mobile) {
          assert(await evaluate(session, "return !document.querySelector('.calculation-index').open;"),
            "phone index should start collapsed so the report is immediately visible");
        }
        const layout = await evaluate(session, `
          const reader = document.querySelector('.workbench');
          const bar = reader.querySelector('.workbench-bread');
          return { page: document.documentElement.scrollWidth, viewport: innerWidth,
            bar: bar.scrollWidth, barWidth: bar.clientWidth };
        `);
        assert(layout.page <= layout.viewport + 1 && layout.bar <= layout.barWidth + 1,
          `${viewport.id}/${theme}/${id} overflow: ${JSON.stringify(layout)}`);
        console.log(`${viewport.id}/${theme}/${id} rendered`);
        await writeFile(`.shots/reports/${viewport.id}-${theme}-${id}.png`, await captureScreenshot(session));
        await evaluate(session, "document.querySelector('.workbench-bread button').click();");
        await wait("window.__haus.store.getState().detailView === 'documents'");
      }
    }
  }
  await pose(`store.getState().setDetailView("none"); store.getState().setDetailView("space");`);
  await wait("document.querySelector('.workbench')?.getAttribute('aria-label') === 'Space & dimensions'");
  await evaluate(session, "document.querySelector('.workbench-bread button').click();");
  await wait("window.__haus.store.getState().detailView === 'none'");

  await setViewport(session, { width: 1600, height: 1000 });
  // Keep delayed requests in the page so the old result can arrive after the new one.
  await pose(`
    window.__reportOriginal = { model: store.getState().model, client: store.getState().client };
    window.__reportRequests = [];
    const fake = new Proxy(window.__reportOriginal.client, { get(target, key) {
      if (key === "getEngineeringCalculations") return () => new Promise((resolve, reject) => {
        window.__reportRequests.push({ resolve, reject });
      });
      const value = Reflect.get(target, key);
      return typeof value === "function" ? value.bind(target) : value;
    }});
    store.setState({ client: fake, model: { ...window.__reportOriginal.model, revision: "test-old" },
      detailView: "engineering", readerOrigin: "canvas" });
  `);
  await wait("window.__reportRequests.length === 1");
  await pose(`store.setState({ model: { ...store.getState().model, revision: "test-new" } });`);
  await wait("window.__reportRequests.length === 2");
  await evaluate(session, `window.__reportRequests[1].resolve({ revision: "test-new", families: [],
    files: { "00-cover.md": "# New calculation", "01-design-criteria.md": "# Selected criteria" } });`);
  await wait("document.querySelector('.md-body')?.textContent.includes('New calculation')");
  await evaluate(session, `window.__reportRequests[0].resolve({ revision: "test-old", families: [],
    files: { "00-cover.md": "# Superseded calculation" } });`);
  await pose(`await new Promise((resolve) => setTimeout(resolve, 200));
    if (document.querySelector('.md-body').textContent.includes("Superseded")) throw new Error("stale result painted");
    [...document.querySelectorAll('.doc-list-item')].find((button) => button.textContent.includes("Selected criteria")).click();`);
  await wait("document.querySelector('.md-body')?.textContent.includes('Selected criteria')");
  await pose(`store.setState({ model: { ...store.getState().model, revision: "test-next" } });`);
  await wait("window.__reportRequests.length === 3");
  await evaluate(session, `window.__reportRequests[2].reject(new Error("Calculation test failure"));`);
  await wait("document.querySelector('[role=alert]')?.textContent.includes('Calculation test failure')");
  await evaluate(session, "[...document.querySelectorAll('button')].find((button) => button.textContent === 'Retry').click();");
  await wait("window.__reportRequests.length === 4");
  await evaluate(session, `window.__reportRequests[3].resolve({ revision: "test-next", families: [],
    files: { "00-cover.md": "# Next calculation", "01-design-criteria.md": "# Selected criteria refreshed" } });`);
  await wait("document.querySelector('.md-body')?.textContent.includes('Selected criteria refreshed')");

  await setViewport(session, { width: 640, height: 900 });
  await wait("!document.querySelector('.calculation-index').open");
  assert(await evaluate(session, "return getComputedStyle(document.querySelector('.calculation-index > summary')).display !== 'none';"),
    "the compact index toggle must remain visible at 640px");
  await evaluate(session, "document.querySelector('.calculation-index > summary').click();");
  await wait("document.querySelector('.calculation-index').open");
  await evaluate(session, `const input = document.querySelector('[aria-label="Filter calculations"]');
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value").set.call(input, "no-such-member");
    input.dispatchEvent(new Event("input", { bubbles: true }));`);
  await wait("document.querySelector('.doc-list')?.textContent.includes('No calculation matches')");
  await pose(`store.setState({ ...window.__reportOriginal, detailView: "building-science" });`);
  await wait("document.querySelector('.workbench')?.getAttribute('aria-label') === 'Building science'");
  await pose(`const science = store.getState().model.building_science;
    store.setState({ model: { ...store.getState().model, building_science: { ...science,
      condensation: [{ assembly: "Unknown assembly", status: "unknown", crossing_layer: null,
        crossing_fraction: null, unknown_materials: ["Missing permeance"], points: [] }] } } });`);
  await wait("document.querySelector('details summary')?.textContent.includes('unknown')");
  await evaluate(session, "document.querySelector('details').open = true;");
  assert(await evaluate(session, "return document.querySelector('.workbench-body').textContent.includes('Missing permeance');"),
    "unknown material is not shown");
  await pose(`store.setState({ model: { ...store.getState().model, building_science: null } });`);
  await wait("document.querySelector('.workbench-body')?.textContent.includes('unavailable')");
  await pose(`store.setState({ model: { ...store.getState().model, space_summary: undefined,
    building_height_summary: undefined }, detailView: "space" });`);
  await wait("document.querySelector('.workbench-body')?.textContent.includes('summaries are unavailable')");
  await pose(`store.setState({ ...window.__reportOriginal, detailView: "none", activePanel: "project" });`);
  await wait("document.querySelector('.project-drawer')");
  const project = await evaluate(session, "return document.querySelector('.project-drawer').textContent;");
  assert(!project.includes("Building science") && !project.includes("Space"), "summaries remain in Project");
  assert(project.includes("Assemblies") && project.includes("Roof"), "Project editing tools missing");
  console.log("Reports browser checks passed; desktop/phone screenshots in ui/.shots/reports.");
} finally {
  session.close();
  await browser.close();
}
