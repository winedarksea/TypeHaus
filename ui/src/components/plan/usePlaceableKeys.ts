// Keyboard edits of plan objects: arrows nudge and R turns the selected canvas object, and
// under the Place tool R turns the ghost. Every edit goes through commitTransform with the
// pending pose as its base, so held or repeated presses accumulate through the queue instead
// of each re-reading a model that has not caught up.
import { useEffect } from "react";
import type { Wall } from "../../model/types";
import { useStore } from "../../state/store";
import { placeableDragBlockedReason } from "./ObjectShapes";
import { nudgeVector, rotateStep } from "./objectKeys";
import { pointOnWall, slideForNudge, stationOnWall, wallFrame } from "./wallSnap";

function isTyping(target: EventTarget | null): boolean {
  const element = target as HTMLElement | null;
  return !!element && (element.tagName === "INPUT" || element.tagName === "SELECT"
    || element.tagName === "TEXTAREA" || element.isContentEditable);
}

export function usePlaceableKeys(walls: Wall[]): void {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (isTyping(event.target) || event.metaKey || event.ctrlKey || event.altKey) return;
      const s = useStore.getState();
      const isRotate = event.key === "r" || event.key === "R";
      if (s.tool === "placeable") {
        if (!isRotate) return;
        event.preventDefault();
        s.setPlacementRotation(rotateStep(s.placementRotation, event.shiftKey));
        return;
      }
      const nudge = nudgeVector(event.key, event.shiftKey);
      if (s.tool !== "select" || s.selection.kind !== "canvas_object" || (!nudge && !isRotate)) return;
      const item = (s.model?.canvas_objects ?? []).find((candidate) => candidate.uid === s.selection.uid);
      if (!item?.position_m) return;
      event.preventDefault();
      if (s.offline) { s.toast("Editing needs the server (offline)", "error"); return; }
      const blocked = placeableDragBlockedReason(item, s.sessionEdits.created.includes(item.tag));
      if (blocked) { s.toast(blocked); return; }
      const pending = s.pendingTransforms[item.uid];
      const position = pending?.position_m ?? item.position_m;
      if (isRotate) {
        const degrees = rotateStep(pending?.rotation ?? item.rotation ?? 0, event.shiftKey);
        void s.commitTransform(item, { rotation: degrees },
          { macro: "rotate_placeable", storey: item.storey, tag: item.tag, degrees, free_rotation: true });
        return;
      }
      if (!nudge) return;
      if (item.attachment) {
        const host = walls.find((wall) => wall.tag === item.attachment!.wall);
        const frame = host ? wallFrame(host) : null;
        const slide = frame ? slideForNudge(frame, nudge) : null;
        if (!frame || slide === null) {
          s.toast(`${item.tag} is attached to ${item.attachment.wall} — it slides along it; detach in the inspector to move it off`);
          return;
        }
        const station = stationOnWall(frame, [position[0] + frame.tangent[0] * slide, position[1] + frame.tangent[1] * slide]);
        const offset = (position[0] - frame.origin[0]) * frame.left[0] + (position[1] - frame.origin[1]) * frame.left[1];
        void s.commitTransform(item, { position_m: pointOnWall(frame, station, offset) }, { macro: "slide_placeable", storey: item.storey, tag: item.tag, distance: station });
        return;
      }
      const next: [number, number] = [position[0] + nudge[0], position[1] + nudge[1]];
      void s.commitTransform(item, { position_m: next },
        { macro: "move_placeable", storey: item.storey, tag: item.tag, position: next });
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [walls]);
}
