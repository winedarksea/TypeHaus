import { createServer } from "vite";

const server = await createServer({
  configFile: false,
  server: { middlewareMode: true },
  appType: "custom",
});

try {
  const { runPlanGeometryTests } = await server.ssrLoadModule("/src/three/planGeometry.test.ts");
  const { runModelGeometryTests } = await server.ssrLoadModule("/src/model/geometry.test.ts");
  runPlanGeometryTests();
  runModelGeometryTests();
  console.log("Plan geometry tests passed.");
} finally {
  await server.close();
}
