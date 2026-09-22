import { Composition, Folder } from "remotion";
import { FPS, TOTAL_FRAMES } from "./config/timing";
import { FullVideo } from "./FullVideo";
import { INTRO_FRAMES, IntroVideo } from "./IntroVideo";
import { Prototype } from "./prototype_v1/Prototype";
import { PrototypeV2 } from "./v2/PrototypeV2";
import { AbsoluteFill } from "remotion";
import { FT_SCENE } from "./config/fineTuningScene";
import { FONT } from "./config/style";
import { S10_FineTuning } from "./scenes/S10_FineTuning";
import { S02B_Taxonomy } from "./scenes/S02B_Taxonomy";
import { S07_Portability } from "./scenes/S07_Portability";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="ICRA-Full" component={FullVideo} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />
      <Composition id="ICRA-Intro" component={IntroVideo} durationInFrames={INTRO_FRAMES} fps={FPS} width={1920} height={1080} />
      <Composition id="FineTuning-Preview" component={FineTuningPreview} defaultProps={{ selectionScene: FT_SCENE.selection.scene }} durationInFrames={Math.ceil(FT_SCENE.durationSec * FPS)} fps={FPS} width={1920} height={1080} />
      <Composition id="S02B-Taxonomy" component={S02B_Taxonomy} durationInFrames={18 * 30} fps={30} width={1920} height={1080} />
      <Composition id="S07-Portability" component={S07_Portability} durationInFrames={8 * 30} fps={30} width={1920} height={1080} />
      <Folder name="Prototypes">
        <Composition id="Prototype" component={Prototype} durationInFrames={675} fps={30} width={1920} height={1080} />
        <Composition id="PrototypeV2" component={PrototypeV2} durationInFrames={915} fps={30} width={1920} height={1080} />
      </Folder>
    </>
  );
};

// Standalone render of the rule-supervised fine-tuning section (expert selection → architecture → results).
const FineTuningPreview: React.FC<{ selectionScene: string }> = ({ selectionScene }) => (
  <AbsoluteFill style={{ backgroundColor: "#fff", fontFamily: FONT, color: "#1A1A1A" }}>
    <S10_FineTuning selectionScene={selectionScene} />
  </AbsoluteFill>
);
