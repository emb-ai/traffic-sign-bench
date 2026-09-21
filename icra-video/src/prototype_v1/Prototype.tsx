import { AbsoluteFill, Series } from "remotion";
import { Hook } from "./Hook";
import { MapPipeline } from "./MapPipeline";
import { Result } from "./Result";
import { C, fontFamily } from "./theme";

// 225 + 240 + 210 = 675 frames = 22.5 s at 30 fps
export const Prototype: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, fontFamily, color: C.ink }}>
      <Series>
        <Series.Sequence name="Hook" durationInFrames={225} premountFor={30}>
          <Hook />
        </Series.Sequence>
        <Series.Sequence name="MapPipeline" durationInFrames={240} premountFor={30}>
          <MapPipeline />
        </Series.Sequence>
        <Series.Sequence name="Result" durationInFrames={210} premountFor={30}>
          <Result />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
