import { AbsoluteFill, interpolate, Sequence, useVideoConfig } from "remotion";
import { CLIPS, SIGNS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { clamp, Clip, Footnote, Headline, Icon, Reveal, Scene, Sub, useT } from "../lib/ui";

// Real yield rollout (gated convoy on the main road) and a real crosswalk
// rollout of the rule-compliant expert (pedestrian timing presets).
export const S04_Targeted: React.FC = () => {
  const t = useT();
  const { fps } = useVideoConfig();
  const c = TEXT.s04;
  const tt = T.s04;
  const cw = t >= tt.crosswalkStart;
  const swap = interpolate(t, [tt.crosswalkStart - 0.4, tt.crosswalkStart + 0.4], [0, 1], clamp);

  return (
    <Scene>
      <div style={{ position: "absolute", left: SIZE.margin, top: 90, width: 820, height: 820, opacity: 1 - swap }}>
        <Clip src={CLIPS.yield_convoy} size={820} left={0} top={0} trimBeforeSec={tt.yieldClipTrim} label={c.yieldClipLabel} />
      </div>
      <Sequence from={Math.round((tt.crosswalkStart - 0.5) * fps)} premountFor={30}>
        <div style={{ position: "absolute", left: SIZE.margin, top: 90, width: 820, height: 820, opacity: swap }}>
          <Clip src={CLIPS.crosswalk_expert} size={820} left={0} top={0} trimBeforeSec={2} label={c.crosswalkClipLabel} />
        </div>
      </Sequence>

      <AbsoluteFill style={{ left: 1000, width: 840, top: 100 }}>
        <Headline size={54}>{c.headline}</Headline>
        <Sub size={26} style={{ marginTop: 14 }}>{c.sub}</Sub>

        <div style={{ marginTop: 44, opacity: cw ? 0.35 : 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Icon src={SIGNS.yield} size={64} />
            <div style={{ fontSize: 34, fontWeight: 700, color: GROUP.priority.text }}>{c.yieldTitle}</div>
          </div>
          {c.yieldSteps.map((s, i) => (
            <Reveal key={s} at={0.8 + i * 2.6} dy={10} style={{ display: "flex", gap: 14, marginTop: 14, fontSize: 27, alignItems: "baseline" }}>
              <span style={{ color: COLORS.blue, fontWeight: 700 }}>{i + 1}</span>
              <span>{s}</span>
            </Reveal>
          ))}
        </div>

        <Reveal at={tt.crosswalkStart} style={{ marginTop: 44 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <Icon src={SIGNS.crosswalk} size={64} />
            <div style={{ fontSize: 34, fontWeight: 700, color: GROUP.priority.text }}>{c.crosswalkTitle}</div>
          </div>
          {c.crosswalkSteps.map((s, i) => (
            <Reveal key={s} at={tt.crosswalkStart + 0.6 + i * 1.6} dy={10} style={{ display: "flex", gap: 14, marginTop: 14, fontSize: 27, alignItems: "baseline" }}>
              <span style={{ color: COLORS.blue, fontWeight: 700 }}>•</span>
              <span>{s}</span>
            </Reveal>
          ))}
        </Reveal>
      </AbsoluteFill>
      <Footnote>{c.footnote}</Footnote>
    </Scene>
  );
};
