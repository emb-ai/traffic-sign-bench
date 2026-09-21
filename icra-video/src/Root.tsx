import { Composition, Folder } from "remotion";
import { FPS, TOTAL_FRAMES } from "./config/timing";
import { FullVideo } from "./FullVideo";
import { INTRO_FRAMES, IntroVideo } from "./IntroVideo";
import { Prototype } from "./prototype_v1/Prototype";
import { PrototypeV2 } from "./v2/PrototypeV2";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition id="ICRA-Full" component={FullVideo} durationInFrames={TOTAL_FRAMES} fps={FPS} width={1920} height={1080} />
      <Composition id="ICRA-Intro" component={IntroVideo} durationInFrames={INTRO_FRAMES} fps={FPS} width={1920} height={1080} />
      <Folder name="Prototypes">
        <Composition id="Prototype" component={Prototype} durationInFrames={675} fps={30} width={1920} height={1080} />
        <Composition id="PrototypeV2" component={PrototypeV2} durationInFrames={915} fps={30} width={1920} height={1080} />
      </Folder>
    </>
  );
};
