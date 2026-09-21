import { AbsoluteFill, Series } from "remotion";
import { Hook } from "./Hook";
import { MapPipeline } from "./MapPipeline";
import { Result } from "./Result";
import { Taxonomy } from "./Taxonomy";
import { C, Fade, fontFamily } from "./ui";

// 210 + 210 + 225 + 270 = 915 frames = 30.5 s at 30 fps
export const PrototypeV2: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: C.bg, fontFamily, color: C.ink }}>
      <Series>
        <Series.Sequence name="Hook" durationInFrames={210} premountFor={30}>
          <Fade><Hook /></Fade>
        </Series.Sequence>
        <Series.Sequence name="Taxonomy" durationInFrames={210} premountFor={30}>
          <Fade><Taxonomy /></Fade>
        </Series.Sequence>
        <Series.Sequence name="MapPipeline" durationInFrames={225} premountFor={30}>
          <Fade><MapPipeline /></Fade>
        </Series.Sequence>
        <Series.Sequence name="Result" durationInFrames={270} premountFor={30}>
          <Fade><Result /></Fade>
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
