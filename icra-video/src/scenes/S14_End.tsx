import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { CLIPS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS } from "../config/style";
import { Headline, Reveal, Scene, Sub } from "../lib/ui";

export const S14_End: React.FC = () => {
  const c = TEXT.s14;
  return (
    <Scene>
      <OffthreadVideo src={staticFile(CLIPS.end_background)} muted loop style={{ position: "absolute", left: 0, top: -420, width: 1920, height: 1920, opacity: 0.18 }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <Reveal at={0.1} style={{ textAlign: "center" }}>
          <Headline size={96}>{c.title}</Headline>
          <Sub size={34} style={{ marginTop: 16, color: COLORS.ink }}>{c.sub}</Sub>
          <Sub size={30} style={{ marginTop: 26 }}>{c.line}</Sub>
        </Reveal>
      </AbsoluteFill>
    </Scene>
  );
};
