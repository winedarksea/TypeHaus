import type { Impact } from "./EngineClient";

// GET /project, POST /storeys, POST /project/new (server/storeys_api.py).
export interface ProjectInfo {
  house_dir: string | null; // null offline: no path to publish
  name: string;
  revision: string;
  templates: string[];
  // Macro names plus "add_storey", "project_new", "saved_events".
  capabilities: string[];
}
export interface AddStoreyRequest {
  tag: string;
  elevation: string | number; // ft-in string or meters
  ceiling_height: string | number;
  copy_from?: string;
}
export interface AddStoreyResult {
  tag: string;
  revision: string;
  ok: boolean;
  // Present only when a layout was copied.
  undo?: number;
  redo?: number;
  impacts?: Impact[];
}
export interface NewProjectRequest {
  directory: string;
  name?: string;
  template?: string;
}
export interface NewProjectResult {
  house_dir: string;
  written: string[];
  command: string; // `haus serve <dir>`
}
