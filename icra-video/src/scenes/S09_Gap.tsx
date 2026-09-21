import { AbsoluteFill } from "remotion";
import { CLIPS } from "../config/assets";
import { BASELINE_SCD, TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Bar, Clip, Headline, Reveal, Scene, Sub } from "../lib/ui";

export const S09_Gap: React.FC = () => {
  const c = TEXT.s09;
  const tt = T.s09;
  const clips = [CLIPS.gap_idm, CLIPS.gap_carl, CLIPS.gap_plant2];
  const S = 380;
  return (
    <Scene>
      {clips.map((src, i) => (
        <Reveal key={src} at={tt.clips + i * 0.25} dy={20}>
          <Clip src={src} size={S} left={SIZE.margin + i * (S + 30)} top={90} loop label={c.clips[i].label} />
        </Reveal>
      ))}

      <AbsoluteFill style={{ left: 1360, width: 500, top: 90 }}>
        <Reveal at={tt.numbers - 0.6}><Sub size={28}>{c.headline}</Sub></Reveal>
        <Reveal at={tt.numbers}>
          <Headline size={104} color={COLORS.red}>{c.number}</Headline>
          <Sub size={24}>{c.numberLabel}</Sub>
        </Reveal>
        <div style={{ marginTop: 30 }}>
          {BASELINE_SCD.map((b, i) => (
            <Reveal key={b.label} at={tt.numbers + 0.6 + i * 0.25} dy={6} style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 10 }}>
              <span style={{ width: 90, fontSize: 24 }}>{b.label}</span>
              <Bar value={b.scd} max={100} width={300} height={22} color={COLORS.baseline} at={tt.numbers + 0.6 + i * 0.25} />
              <span style={{ fontSize: 24, fontVariantNumeric: "tabular-nums", color: COLORS.muted }}>{b.scd}%</span>
            </Reveal>
          ))}
        </div>
      </AbsoluteFill>

      <Reveal at={tt.question} style={{ position: "absolute", left: SIZE.margin, top: 620 }}>
        <Headline size={60}>{c.question}</Headline>
        <Sub size={28} style={{ marginTop: 12 }}>Explicit rule-conditioned evaluation reveals a large gap in existing planners.</Sub>
      </Reveal>
    </Scene>
  );
};
