import { SceneKey } from "./timing";
import type { SubLine } from "../lib/Subtitles";
import { VOICEOVER } from "./voiceover";

// Subtitles intentionally use the exact narration cues. Enable them with
// SHOW_SUBTITLES in config/style.ts.
export const SUBTITLES = Object.fromEntries(
  (Object.keys(VOICEOVER) as SceneKey[]).map((scene) => [
    scene,
    VOICEOVER[scene].map(({ from, to, text }): SubLine => ({
      from,
      to,
      text,
    })),
  ]),
) as Record<SceneKey, SubLine[]>;
