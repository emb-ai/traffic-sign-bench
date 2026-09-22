import type { SceneKey } from "./timing";
import voiceoverData from "./voiceover.json";

export type VoiceoverCue = {
  id: string;
  from: number;
  to: number;
  text: string;
  tts?: string;
};

export const VOICEOVER = voiceoverData.cues as Record<
  SceneKey,
  VoiceoverCue[]
>;

export const VOICEOVER_VOLUME = 1;
