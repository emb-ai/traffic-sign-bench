import { AbsoluteFill, OffthreadVideo, staticFile } from "remotion";
import { CLIPS } from "../config/assets";
import { BASELINE_SCD, TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Bar, Headline, Icon, Reveal, Scene, Sub } from "../lib/ui";

const BaselineClipCard: React.FC<{
  src: string;
  name: string;
  scd: string;
  left: number;
  top: number;
  at: number;
}> = ({ src, name, scd, left, top, at }) => (
  <Reveal
    at={at}
    dy={20}
    style={{
      position: "absolute",
      left,
      top,
      width: 270,
      overflow: "hidden",
      border: `2px solid ${COLORS.border}`,
      borderRadius: 18,
      backgroundColor: COLORS.bg,
      boxShadow: "0 8px 22px rgba(26, 26, 26, 0.07)",
    }}
  >
    <div
      style={{
        height: 52,
        padding: "0 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxSizing: "border-box",
      }}
    >
      <span style={{ fontSize: 23, fontWeight: 900, color: COLORS.ink }}>{name}</span>
      <span style={{ fontSize: 20, fontWeight: 900, color: COLORS.red }}>{scd} SCD</span>
    </div>
    <OffthreadVideo
      src={staticFile(src)}
      muted
      style={{ width: 270, height: 270, display: "block", objectFit: "cover", borderTop: `2px solid ${COLORS.border}` }}
    />
  </Reveal>
);

export const S09_Gap: React.FC = () => {
  const c = TEXT.s09;
  const tt = T.s09;
  const clips = [CLIPS.gap_idm, CLIPS.gap_ppo, CLIPS.gap_carl, CLIPS.gap_plant2];
  const clipGap = 20;

  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 46 }}>
        <Headline size={60}>{c.headline}</Headline>
      </Reveal>

      <Reveal
        at={tt.clips + 0.05}
        style={{
          position: "absolute",
          left: SIZE.margin,
          top: 134,
          width: 1120,
          display: "flex",
          alignItems: "baseline",
          gap: 13,
        }}
      >
        <span style={{ fontSize: 24, fontWeight: 900, color: COLORS.ink }}>SCD = Sign Compliance × Destination</span>
        <span style={{ fontSize: 20, color: COLORS.muted }}>An episode counts only if both conditions hold.</span>
      </Reveal>

      <Reveal
        at={tt.clips + 0.15}
        style={{
          position: "absolute",
          left: SIZE.margin,
          top: 180,
          display: "flex",
          alignItems: "center",
          gap: 12,
          color: COLORS.muted,
          fontSize: 22,
          fontWeight: 700,
          letterSpacing: 0.2,
        }}
      >
        <Icon src="signs/yield.png" size={34} />
        {c.exampleLabel}
      </Reveal>

      {clips.map((src, i) => (
        <BaselineClipCard
          key={src}
          src={src}
          name={c.clips[i].label}
          scd={c.clips[i].scd}
          left={SIZE.margin + i * (270 + clipGap)}
          top={220}
          at={tt.clips + i * 0.25}
        />
      ))}

      <AbsoluteFill
        style={{
          left: 1278,
          top: 146,
          width: 552,
          height: 440,
          padding: "26px 28px",
          boxSizing: "border-box",
          border: `2px solid ${COLORS.border}`,
          borderRadius: 22,
          backgroundColor: "#FAFAFA",
          boxShadow: "0 10px 30px rgba(26, 26, 26, 0.07)",
        }}
      >
        <Reveal at={tt.numbers - 0.6} dy={8}>
          <div>
            <div style={{ fontSize: 30, fontWeight: 900, color: COLORS.ink }}>All standard baselines</div>
            <div style={{ marginTop: 5, fontSize: 18, color: COLORS.muted }}>{c.metric} · all 29 scenario types</div>
          </div>
        </Reveal>

        <div style={{ marginTop: 22 }}>
          {BASELINE_SCD.map((b, i) => (
            <Reveal
              key={b.label}
              at={tt.numbers + i * 0.13}
              dy={4}
              style={{ display: "grid", gridTemplateColumns: "82px 300px 54px", alignItems: "center", gap: 12, marginBottom: 8 }}
            >
              <span style={{ fontSize: 19, fontWeight: 700, color: COLORS.ink }}>{b.label}</span>
              <div style={{ width: 300, height: 14, borderRadius: 7, overflow: "hidden", backgroundColor: "#E7E9ED" }}>
                <Bar value={b.scd} max={100} width={300} height={14} color={COLORS.blue} at={tt.numbers + i * 0.13} dur={0.7} />
              </div>
              <span style={{ fontSize: 19, fontWeight: 700, fontVariantNumeric: "tabular-nums", color: COLORS.muted, textAlign: "right" }}>
                {b.scd.toFixed(1)}%
              </span>
            </Reveal>
          ))}
        </div>

        <Reveal
          at={tt.numbers + 0.8}
          dy={0}
          style={{ marginLeft: 94, width: 300, display: "flex", justifyContent: "space-between", fontSize: 16, color: COLORS.faint }}
        >
          <span>0</span>
          <span>50</span>
          <span>100%</span>
        </Reveal>
        <Reveal at={tt.numbers + 0.8} dy={0} style={{ marginTop: 7, fontSize: 17, color: COLORS.muted }}>
          0–100% scale
        </Reveal>
      </AbsoluteFill>

      <Reveal
        at={tt.numbers}
        dy={10}
        style={{
          position: "absolute",
          left: SIZE.margin,
          top: 575,
          height: 92,
          display: "flex",
          alignItems: "center",
          gap: 22,
          paddingLeft: 22,
          borderLeft: `7px solid ${COLORS.red}`,
        }}
      >
        <div style={{ fontSize: 76, lineHeight: 1, fontWeight: 900, color: COLORS.red, fontVariantNumeric: "tabular-nums" }}>{c.number}</div>
        <div style={{ maxWidth: 280, fontSize: 22, lineHeight: 1.25, color: COLORS.muted }}>{c.numberLabel}</div>
      </Reveal>

      <Reveal at={tt.question} style={{ position: "absolute", left: SIZE.margin, top: 755 }}>
        <Headline size={60}>{c.question}</Headline>
        <Sub size={28} style={{ marginTop: 12 }}>
          Explicit rule-conditioned evaluation reveals a large gap in existing planners.
        </Sub>
      </Reveal>
    </Scene>
  );
};
