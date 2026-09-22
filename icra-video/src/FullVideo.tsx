import { AbsoluteFill, Series } from "remotion";
import { SUBTITLES } from "./config/subtitles";
import { COLORS, FONT, SHOW_SUBTITLES } from "./config/style";
import { FPS, SCENE_ORDER, SCENE_SECONDS, SceneKey } from "./config/timing";
import { Subtitles } from "./lib/Subtitles";
import { S01_Hook } from "./scenes/S01_Hook";
import { S02_Benchmark } from "./scenes/S02_Benchmark";
import { S02B_Taxonomy } from "./scenes/S02B_Taxonomy";
import { S03_RealMaps } from "./scenes/S03_RealMaps";
import { S04_Targeted } from "./scenes/S04_Targeted";
import { S05_Routing } from "./scenes/S05_Routing";
import { S06_Scale } from "./scenes/S06_Scale";
import { S07_Portability } from "./scenes/S07_Portability";
import { S08_Interface } from "./scenes/S08_Interface";
import { S09_Gap } from "./scenes/S09_Gap";
import { S10_FineTuning } from "./scenes/S10_FineTuning";
import { S11_Result } from "./scenes/S11_Result";
import { S12_Ablation } from "./scenes/S12_Ablation";
import { S13_Failures } from "./scenes/S13_Failures";
import { S14_End } from "./scenes/S14_End";
import { S15_Conclusion } from "./scenes/S15_Conclusion";
import { S16_Diversity } from "./scenes/S16_Diversity";

const SCENES: Record<SceneKey, React.FC> = {
  s01_hook: S01_Hook,
  s02_benchmark: S02_Benchmark,
  s02b_taxonomy: S02B_Taxonomy,
  s03_realmaps: S03_RealMaps,
  s04_targeted: S04_Targeted,
  s05_routing: S05_Routing,
  s06_scale: S06_Scale,
  s07_portability: S07_Portability,
  s08_interface: S08_Interface,
  s09_gap: S09_Gap,
  s10_architecture: S10_FineTuning,
  s11_result: S11_Result,
  s12_ablation: S12_Ablation,
  s13_failures: S13_Failures,
  s16_diversity: S16_Diversity,
  s15_conclusion: S15_Conclusion,
  s14_end: S14_End,
};

export const FullVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: COLORS.bg, fontFamily: FONT, color: COLORS.ink }}>
      <Series>
        {SCENE_ORDER.map((key) => {
          const C = SCENES[key];
          return (
            <Series.Sequence key={key} name={key} durationInFrames={SCENE_SECONDS[key] * FPS} premountFor={FPS}>
              <C />
              {SHOW_SUBTITLES && <Subtitles lines={SUBTITLES[key]} />}
            </Series.Sequence>
          );
        })}
      </Series>
    </AbsoluteFill>
  );
};
