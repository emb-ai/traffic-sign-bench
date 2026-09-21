import { AbsoluteFill } from "remotion";
import { CLIPS } from "../config/assets";
import { GROUP_SCD, NUMBERS, TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Bar, Clip, CountUp, Footnote, Headline, Reveal, Scene, Sub } from "../lib/ui";

export const S11_Result: React.FC = () => {
  const c = TEXT.s11;
  const tt = T.s11;
  const S = 440;
  return (
    <Scene>
      <Reveal at={tt.clips}>
        <Clip src={CLIPS.result_plant2} size={S} left={SIZE.margin} top={90} loop label={<><b style={{ color: COLORS.ink }}>{c.left.name}</b> · {c.left.clip}</>} />
      </Reveal>
      <Reveal at={tt.clips + 0.3}>
        <Clip src={CLIPS.result_plant2ft} size={S} left={SIZE.margin + S + 40} top={90} loop label={<><b style={{ color: COLORS.ink }}>{c.right.name}</b> · {c.right.clip}</>} />
      </Reveal>

      {/* big numbers */}
      <AbsoluteFill style={{ left: SIZE.margin, top: 620, width: 940 }}>
        <Reveal at={tt.numbers - 0.5}><Sub size={24} style={{ color: COLORS.blue, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase" }}>{c.metric}</Sub></Reveal>
        <div style={{ display: "flex", alignItems: "flex-end", gap: 40, marginTop: 10 }}>
          <Reveal at={tt.numbers}>
            <div style={{ fontSize: 30, color: COLORS.muted }}>{c.left.name}</div>
            <div style={{ fontSize: 110, fontWeight: 900, color: COLORS.red, lineHeight: 1 }}>{c.left.value}</div>
          </Reveal>
          <Reveal at={tt.numbers + 0.8} style={{ fontSize: 70, color: COLORS.faint, paddingBottom: 10 }}>→</Reveal>
          <Reveal at={tt.numbers + 1.0}>
            <div style={{ fontSize: 30, fontWeight: 700 }}>{c.right.name}</div>
            <div style={{ fontSize: 130, fontWeight: 900, color: COLORS.green, lineHeight: 1 }}>
              <CountUp from={NUMBERS.plant2SCD} to={NUMBERS.plant2FtSCD} start={tt.numbers + 1.0} end={tt.numbers + 2.6} decimals={1} suffix="%" />
            </div>
          </Reveal>
          <Reveal at={tt.numbers + 2.6} style={{ paddingBottom: 14, fontSize: 30, color: COLORS.muted }}>{c.gain}</Reveal>
        </div>
      </AbsoluteFill>

      {/* group bars */}
      <AbsoluteFill style={{ left: 1080, width: 780, top: 90 }}>
        <Reveal at={tt.bars - 0.4}><Sub size={26} style={{ fontWeight: 700, color: COLORS.ink }}>{c.barsTitle}</Sub></Reveal>
        {GROUP_SCD.map((r, i) => {
          const col = GROUP[r.key];
          const at = tt.bars + i * tt.barStep;
          return (
            <Reveal key={r.key} at={at} dy={8} style={{ display: "flex", alignItems: "center", marginTop: 22 }}>
              <div style={{ width: 150, fontSize: 28, fontWeight: 700, color: col.text }}>{r.label}</div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, height: 30 }}>
                  <Bar value={r.base} width={520} height={20} color={COLORS.baseline} at={at} />
                  <span style={{ fontSize: 20, color: COLORS.muted, fontVariantNumeric: "tabular-nums" }}>{r.base}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, height: 40 }}>
                  <Bar value={r.ft} width={520} height={30} color={col.bar} at={at + 0.2} />
                  <span style={{ fontSize: 26, fontWeight: 900, fontVariantNumeric: "tabular-nums" }}>{r.ft}</span>
                </div>
              </div>
            </Reveal>
          );
        })}
        <Reveal at={tt.bars + 4 * tt.barStep + 0.6} style={{ marginTop: 40 }}>
          <Headline size={38}>{c.takeaway}</Headline>
        </Reveal>
      </AbsoluteFill>
      <Footnote>{c.footnote}</Footnote>
    </Scene>
  );
};
