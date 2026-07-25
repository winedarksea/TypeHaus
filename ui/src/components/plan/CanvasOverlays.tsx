// The Canvas2D overlay stack: every keypad, popover and context menu the SVG floorplan
// anchors over itself. Split from components/Canvas2D.tsx — the canvas owns the gesture
// state and hands it down; this component owns the wiring from each overlay back into the
// store (patches, macros, selection) so the canvas file stays about drawing and gestures.
import { formatFtIn, openingStartFromCenter, wallLength } from "../../model/geometry";
import type { RefObject } from "react";
import type { Vec2, Wall } from "../../model/types";
import { useStore } from "../../state/store";
import { DoorSettingsPopover } from "../DoorSettingsPopover";
import { WindowSettingsPopover } from "../WindowSettingsPopover";
import { FtInKeypad } from "../FtInKeypad";
import { PlacementPopover } from "../PlacementPopover";
import { PlanWarningPopover } from "../PlanWarningPopover";
import type { PlanWarningMarker } from "../../model/planWarnings";
import { WallAssemblyPopupCard } from "./WallShapes";
import { hostStorey } from "./OpeningShapes";
import type {
  DoorPopup, LengthEntry, Pending, Placement, WallAssemblyPopup,
} from "./canvasTypes";

export function CanvasOverlays(props: {
  svgRef: RefObject<SVGSVGElement>;
  pending: Pending | null;
  setPending: (pending: Pending | null) => void;
  doorPopup: DoorPopup | null;
  setDoorPopup: (popup: DoorPopup | null) => void;
  windowPopup: DoorPopup | null;
  setWindowPopup: (popup: DoorPopup | null) => void;
  dimWall: Wall | null;
  setDimWall: (wall: Wall | null) => void;
  onCommitDim: (meters: number) => void;
  lengthEntry: LengthEntry | null;
  setLengthEntry: (entry: LengthEntry | null) => void;
  onCommitWall: (start: [number, number], end: [number, number]) => void;
  placement: Placement | null;
  setPlacement: (placement: Placement | null) => void;
  hintFile: string | undefined;
  wallAssemblyPopup: WallAssemblyPopup | null;
  setWallAssemblyPopup: (popup: WallAssemblyPopup | null) => void;
  popupWall: Wall | null;
  warningPopup: { marker: PlanWarningMarker; screen: Vec2 } | null;
  setWarningPopup: (popup: { marker: PlanWarningMarker; screen: Vec2 } | null) => void;
  ctxMenu: { x: number; y: number } | null;
  setCtxMenu: (menu: { x: number; y: number } | null) => void;
}) {
  const {
    svgRef, pending, setPending, doorPopup, setDoorPopup, windowPopup, setWindowPopup,
    dimWall, setDimWall, onCommitDim, lengthEntry, setLengthEntry, onCommitWall,
    placement, setPlacement, hintFile, wallAssemblyPopup, setWallAssemblyPopup, popupWall,
    warningPopup, setWarningPopup, ctxMenu, setCtxMenu,
  } = props;
  const model = useStore((s) => s.model)!;
  const selection = useStore((s) => s.selection);
  const select = useStore((s) => s.select);
  const selectByTag = useStore((s) => s.selectByTag);
  const activeStorey = useStore((s) => s.activeStorey);
  const applyOps = useStore((s) => s.applyOps);
  const runMacro = useStore((s) => s.runMacro);
  const deleteSelection = useStore((s) => s.deleteSelection);
  const duplicateSelection = useStore((s) => s.duplicateSelection);
  const offline = useStore((s) => s.offline);
  const toast = useStore((s) => s.toast);

  // Opening driven-dimension edit (double-click an opening).
  const commitPending = async (meters: number) => {
    if (!pending) return;
    const o = pending.opening;
    const ok = pending.field === "position"
      ? Boolean(await runMacro({ macro: "move_opening", storey: hostStorey(model, o), tag: o.tag,
        along: formatFtIn(meters) }))
      : await applyOps([{
        op: "update", type: o.is_door ? "Door" : "Window", tag: o.tag,
        fields: { sill_height: formatFtIn(meters) },
      }]);
    if (ok) toast(`${o.tag} ${pending.field} updated`);
    setPending(null);
  };

  const editPositionFor = (popup: DoorPopup, close: () => void) => () => {
    setPending({ opening: popup.opening, field: "position",
      initial: formatFtIn(openingStartFromCenter(
        popup.opening.center_along_m, popup.opening.width_m,
      )) });
    close();
  };
  const editSillHeightFor = (popup: DoorPopup, close: () => void) => () => {
    setPending({ opening: popup.opening, field: "sill_height",
      initial: formatFtIn(popup.opening.sill_m) });
    close();
  };

  return (
    <>
      {pending && (
        <FtInKeypad
          label={`${pending.opening.tag} · ${pending.field === "position" ? "start-jamb station along wall" : "sill height"}`}
          initial={pending.initial}
          onCommit={(m) => void commitPending(m)}
          onCancel={() => setPending(null)}
        />
      )}
      {doorPopup && (
        <DoorSettingsPopover
          opening={doorPopup.opening}
          screen={doorPopup.screen}
          doorTypes={model.catalog?.door_types ?? []}
          applyOps={applyOps}
          toast={toast}
          onEditPosition={editPositionFor(doorPopup, () => setDoorPopup(null))}
          onEditSillHeight={editSillHeightFor(doorPopup, () => setDoorPopup(null))}
          onClose={() => setDoorPopup(null)}
        />
      )}
      {windowPopup && (
        <WindowSettingsPopover
          opening={windowPopup.opening}
          screen={windowPopup.screen}
          windowTypes={model.catalog?.window_types ?? []}
          applyOps={applyOps}
          toast={toast}
          onEditPosition={editPositionFor(windowPopup, () => setWindowPopup(null))}
          onEditSillHeight={editSillHeightFor(windowPopup, () => setWindowPopup(null))}
          onDelete={() => {
            useStore.getState().select("opening", windowPopup.opening.uid);
            void useStore.getState().deleteSelection();
            setWindowPopup(null);
          }}
          onClose={() => setWindowPopup(null)}
        />
      )}
      {dimWall && (
        <FtInKeypad
          label={`${dimWall.tag} · length (stretches the end node)`}
          initial={formatFtIn(wallLength(dimWall))}
          onCommit={(m) => onCommitDim(m)}
          onCancel={() => setDimWall(null)}
        />
      )}
      {lengthEntry && (
        <FtInKeypad
          label="Segment length · exact distance along the current direction"
          initial={lengthEntry.initial}
          onCommit={(m) => {
            const { start, dir } = lengthEntry;
            setLengthEntry(null);
            onCommitWall(start, [start[0] + dir[0] * m, start[1] + dir[1] * m]);
          }}
          onCancel={() => setLengthEntry(null)}
        />
      )}
      {placement && (
        <PlacementPopover
          placement={placement}
          catalog={model.catalog}
          hintFile={hintFile}
          storey={activeStorey}
          runMacro={runMacro}
          selectByTag={selectByTag}
          toast={toast}
          onClose={() => setPlacement(null)}
        />
      )}
      {wallAssemblyPopup && popupWall && (
        <WallAssemblyPopupCard
          wall={popupWall}
          screen={wallAssemblyPopup.screen}
          viewport={svgRef.current?.getBoundingClientRect() ?? null}
          onClose={() => setWallAssemblyPopup(null)}
        />
      )}
      {warningPopup && (
        <PlanWarningPopover
          marker={warningPopup.marker}
          screen={warningPopup.screen}
          viewport={svgRef.current?.getBoundingClientRect() ?? null}
          onClose={() => setWarningPopup(null)}
        />
      )}
      {ctxMenu && (
        <>
          <div className="ctx-overlay" onPointerDown={() => setCtxMenu(null)} onContextMenu={(e) => { e.preventDefault(); setCtxMenu(null); }} />
          <div className="ctx-menu" style={{ left: ctxMenu.x, top: ctxMenu.y }} role="menu">
            {selection.uid ? (
              <>
                <button role="menuitem" onClick={() => { select(null, null); setCtxMenu(null); }}>Deselect</button>
                {!offline && (selection.kind === "opening" || selection.kind === "canvas_object") && (
                  <button role="menuitem" onClick={() => { void duplicateSelection(); setCtxMenu(null); }}>Duplicate</button>
                )}
                {!offline && (
                  <button role="menuitem" className="ctx-danger" onClick={() => { void deleteSelection(); setCtxMenu(null); }}>Delete</button>
                )}
              </>
            ) : (
              <button role="menuitem" disabled>Nothing selected</button>
            )}
          </div>
        </>
      )}
    </>
  );
}
