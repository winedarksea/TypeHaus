import { createServer } from "vite";

const server = await createServer({
  configFile: false,
  server: { middlewareMode: true },
  appType: "custom",
});

try {
  const { runPlanGeometryTests } = await server.ssrLoadModule("/src/three/planGeometry.test.ts");
  const { runArchGeometryTests, runCanvasObjectGeometryTests, runCanvasObjectPartsTests, runOpeningGeometryTests, runEarthGeometryTests, runFootingBeddingGeometryTests, runWholeHouseGlbTests, runSolidMaterialTests, runSelectionRegistrationTests, runViewFramingTests } = await server.ssrLoadModule("/src/components/Panel3D.test.ts");
  const { runModelGeometryTests } = await server.ssrLoadModule("/src/model/geometry.test.ts");
  const { runMemberFootprintTests } = await server.ssrLoadModule("/src/model/memberFootprint.test.ts");
  const { runVisibilityTests } = await server.ssrLoadModule("/src/model/visibility.test.ts");
  const { runEngineBomTests } = await server.ssrLoadModule("/src/model/engineBom.test.ts");
  const { runEngineCostsTests } = await server.ssrLoadModule("/src/model/engineCosts.test.ts");
  const { runEngineEstimateTests } = await server.ssrLoadModule("/src/model/engineEstimate.test.ts");
  const { runPlanWarningTests, runSpaceLabelTests } = await server.ssrLoadModule("/src/model/planWarnings.test.ts");
  const { runTransitionTests } = await server.ssrLoadModule("/src/model/transitions.test.ts");
  const { runTagIndexTests } = await server.ssrLoadModule("/src/model/tagIndex.test.ts");
  const { runDetailStarTests } = await server.ssrLoadModule("/src/model/detailStar.test.ts");
  const { runVaporTests } = await server.ssrLoadModule("/src/model/vapor.test.ts");
  const { runOpenHouseTests } = await server.ssrLoadModule("/src/engine/openHouse.test.ts");
  const { runDoorSymbolTests, runWindowSymbolTests } = await server.ssrLoadModule("/src/model/doorSymbols.test.ts");
  const { runRoofGeometryTests } = await server.ssrLoadModule("/src/three/roofGeometry.test.ts");
  const { runMaterialGeometryTests, runMemberColorTests } = await server.ssrLoadModule("/src/three/materials.test.ts");
  const { runDetailAnnotationTests } = await server.ssrLoadModule("/src/components/DetailCanvas.test.ts");
  const { runMemberPickingTests } = await server.ssrLoadModule("/src/three/memberPicking.test.ts");
  const { runRoomFloorTests } = await server.ssrLoadModule("/src/three/builders/roomFloor.test.ts");
  const { runArchRingTests } = await server.ssrLoadModule("/src/three/builders/archRing.test.ts");
  const { runWallBandShapeTests } = await server.ssrLoadModule("/src/three/builders/wallBandShape.test.ts");
  const { runToolDispatchTests } = await server.ssrLoadModule("/src/components/plan/toolDispatch.test.ts");
  const { runPlaceableDragTests, runObjectDragMathTests } = await server.ssrLoadModule("/src/components/plan/objectDrag.test.ts");
  const { runStoreEventTests } = await server.ssrLoadModule("/src/state/storeEvents.test.ts");
  runPlanGeometryTests();
  runOpeningGeometryTests();
  runArchGeometryTests();
  runEarthGeometryTests();
  runFootingBeddingGeometryTests();
  runCanvasObjectGeometryTests();
  runCanvasObjectPartsTests();
  runWholeHouseGlbTests();
  runSolidMaterialTests();
  runSelectionRegistrationTests();
  runViewFramingTests();
  runVisibilityTests();
  runEngineBomTests();
  runEngineCostsTests();
  runEngineEstimateTests();
  runPlanWarningTests();
  runSpaceLabelTests();
  runTransitionTests();
  runTagIndexTests();
  runDetailStarTests();
  runVaporTests();
  runOpenHouseTests();
  runModelGeometryTests();
  runMemberFootprintTests();
  runDoorSymbolTests();
  runWindowSymbolTests();
  runRoofGeometryTests();
  runMaterialGeometryTests();
  runMemberColorTests();
  runDetailAnnotationTests();
  runMemberPickingTests();
  runRoomFloorTests();
  runArchRingTests();
  runWallBandShapeTests();
  runToolDispatchTests();
  runPlaceableDragTests();
  runObjectDragMathTests();
  runStoreEventTests();
  console.log("Plan geometry tests passed.");
} finally {
  await server.close();
}
