import { AbsoluteFill, Series } from "remotion";
import { COLORS, FONT } from "./config/style";
import { FPS, SCENE_SECONDS } from "./config/timing";
import { S01_Hook } from "./scenes/S01_Hook";
import { S02_Benchmark } from "./scenes/S02_Benchmark";
import { S02B_Taxonomy } from "./scenes/S02B_Taxonomy";
import { S07_Portability } from "./scenes/S07_Portability";

const INTRO_SCENES = [
  ["Problem", "s01_hook", S01_Hook],
  ["Benchmark", "s02_benchmark", S02_Benchmark],
  ["Taxonomy", "s02b_taxonomy", S02B_Taxonomy],
  ["Portability", "s07_portability", S07_Portability],
] as const;

export const INTRO_FRAMES = INTRO_SCENES.reduce(
  (total, [, key]) => total + SCENE_SECONDS[key] * FPS,
  0,
);

export const IntroVideo: React.FC = () => (
  <AbsoluteFill style={{ backgroundColor: COLORS.bg, color: COLORS.ink, fontFamily: FONT }}>
    <Series>
      {INTRO_SCENES.map(([name, key, Component]) => (
        <Series.Sequence
          key={key}
          name={name}
          durationInFrames={SCENE_SECONDS[key] * FPS}
          premountFor={FPS}
        >
          <Component />
        </Series.Sequence>
      ))}
    </Series>
  </AbsoluteFill>
);
