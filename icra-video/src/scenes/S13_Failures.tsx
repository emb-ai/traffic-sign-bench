import { AbsoluteFill } from "remotion";
import { TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Headline, Missing, Reveal, Scene, Sub } from "../lib/ui";

export const S13_Failures: React.FC = () => {
  const c = TEXT.s13;
  const tt = T.s13;
  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 60 }}>
        <Headline>{c.headline}</Headline>
      </Reveal>
      <Reveal at={0.3}>
        <Missing text={c.missing} left={SIZE.margin} top={190} width={700} height={700} />
      </Reveal>

      <AbsoluteFill style={{ left: 900, width: 940, top: 200 }}>
        <Reveal at={tt.numbers}>
          <div style={{ fontSize: 130, fontWeight: 900, color: COLORS.blue, lineHeight: 1 }}>{c.a.value}</div>
          <Sub size={32} style={{ color: COLORS.ink }}>{c.a.label}</Sub>
        </Reveal>
        <Reveal at={tt.numbers + 1.2} style={{ marginTop: 40 }}>
          <div style={{ fontSize: 96, fontWeight: 900, color: COLORS.red, lineHeight: 1 }}>{c.b.value}</div>
          <Sub size={32} style={{ color: COLORS.ink }}>{c.b.label}</Sub>
        </Reveal>
        <Reveal at={tt.numbers + 2.2} style={{ marginTop: 26 }}>
          <Sub size={22}>{c.compliance}</Sub>
        </Reveal>
        <Reveal at={tt.text} style={{ marginTop: 50 }}>
          <Headline size={44}>{c.text}</Headline>
        </Reveal>
      </AbsoluteFill>
    </Scene>
  );
};
