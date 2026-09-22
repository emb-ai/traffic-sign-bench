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
      border: `1.5px solid ${COLORS.border}`,
      borderRadius: 20,
      backgroundColor: "#FFFFFF",
      boxShadow: "0 10px 28px rgba(26, 26, 26, 0.075)",
    }}
  >
    <div style={{ height: 5, background: `linear-gradient(90deg, ${COLORS.red}, #EF8B7D)` }} />
    <div
      style={{
        height: 51,
        padding: "0 14px 0 16px",
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        boxSizing: "border-box",
      }}
    >
      <span style={{ fontSize: 22, fontWeight: 900, color: COLORS.ink }}>{name}</span>
      <span
        style={{
          padding: "5px 9px",
          borderRadius: 9,
          backgroundColor: "#FFF0ED",
          fontSize: 17,
          lineHeight: 1,
          fontWeight: 900,
          color: COLORS.red,
          fontVariantNumeric: "tabular-nums",
        }}
      >
        {scd} SCD
      </span>
    </div>
    <OffthreadVideo
      src={staticFile(src)}
      muted
      style={{ width: 270, height: 268, display: "block", objectFit: "cover", borderTop: `1.5px solid ${COLORS.border}` }}
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
          top: 132,
          width: 1120,
          display: "flex",
          alignItems: "center",
          gap: 12,
        }}
      >
        <span
          style={{
            padding: "7px 12px",
            borderRadius: 10,
            backgroundColor: "#EEF3FB",
            fontSize: 20,
            lineHeight: 1,
            fontWeight: 900,
            color: COLORS.blue,
          }}
        >
          SCD
        </span>
        <span style={{ fontSize: 22, fontWeight: 900, color: COLORS.ink }}>Sign Compliance × Destination</span>
        <span style={{ width: 1, height: 24, backgroundColor: COLORS.border }} />
        <span style={{ fontSize: 19, color: COLORS.muted }}>Both conditions must hold.</span>
      </Reveal>

      <Reveal
        at={tt.clips + 0.15}
        style={{
          position: "absolute",
          left: SIZE.margin,
          top: 221,
          display: "flex",
          alignItems: "center",
          gap: 10,
          color: COLORS.muted,
          fontSize: 20,
          fontWeight: 700,
          letterSpacing: 0.2,
        }}
      >
        <Icon src="signs/yield.png" size={30} />
        {c.exampleLabel}
      </Reveal>

      {clips.map((src, i) => (
        <BaselineClipCard
          key={src}
          src={src}
          name={c.clips[i].label}
          scd={c.clips[i].scd}
          left={SIZE.margin + i * (270 + clipGap)}
          top={270}
          at={tt.clips + i * 0.25}
        />
      ))}

      <AbsoluteFill
        style={{
          left: 1278,
          top: 270,
          width: 552,
          height: 325,
          padding: "18px 24px",
          boxSizing: "border-box",
          border: `1.5px solid ${COLORS.border}`,
          borderRadius: 20,
          backgroundColor: "#FBFCFE",
          boxShadow: "0 10px 28px rgba(26, 26, 26, 0.065)",
        }}
      >
        <Reveal at={tt.numbers - 0.6} dy={8}>
          <div>
            <div style={{ fontSize: 27, lineHeight: 1, fontWeight: 900, color: COLORS.ink }}>Baselines Evaluation</div>
            <div style={{ marginTop: 5, fontSize: 16, color: COLORS.muted }}>{c.metric} · all 29 scenario types</div>
          </div>
        </Reveal>

        <div style={{ marginTop: 12 }}>
          {BASELINE_SCD.map((b, i) => (
            <Reveal
              key={b.label}
              at={tt.numbers + i * 0.13}
              dy={4}
              style={{ display: "grid", gridTemplateColumns: "74px 322px 58px", alignItems: "center", gap: 10, marginBottom: 4 }}
            >
              <span style={{ fontSize: 16, fontWeight: 700, color: COLORS.ink }}>{b.label}</span>
              <div style={{ width: 322, height: 11, borderRadius: 6, overflow: "hidden", backgroundColor: "#E6EAF0" }}>
                <Bar value={b.scd} max={100} width={322} height={11} color={COLORS.red} at={tt.numbers + i * 0.13} dur={0.7} />
              </div>
              <span style={{ fontSize: 16, fontWeight: 700, fontVariantNumeric: "tabular-nums", color: COLORS.muted, textAlign: "right" }}>
                {b.scd.toFixed(1)}%
              </span>
            </Reveal>
          ))}
        </div>

        <Reveal
          at={tt.numbers + 0.8}
          dy={0}
          style={{ marginLeft: 84, width: 322, display: "flex", justifyContent: "space-between", fontSize: 13, color: COLORS.faint }}
        >
          <span>0</span>
          <span>50</span>
          <span>100%</span>
        </Reveal>
      </AbsoluteFill>

      <Reveal
        at={tt.numbers}
        dy={10}
        style={{
          position: "absolute",
          left: SIZE.margin,
          top: 620,
          width: 1740,
          height: 112,
          boxSizing: "border-box",
          display: "flex",
          alignItems: "center",
          gap: 24,
          padding: "0 28px",
          border: "1px solid #F2D5D0",
          borderLeft: `7px solid ${COLORS.red}`,
          borderRadius: 16,
          background: "linear-gradient(90deg, #FFF5F2 0%, #FFF9F7 45%, #FFFFFF 100%)",
        }}
      >
        <div style={{ fontSize: 70, lineHeight: 1, fontWeight: 900, color: COLORS.red, fontVariantNumeric: "tabular-nums", letterSpacing: -1.5 }}>
          {c.number}
        </div>
        <div style={{ width: 1, height: 58, backgroundColor: "#EAC7C1" }} />
        <div>
          <div style={{ fontSize: 24, lineHeight: 1.15, fontWeight: 900, color: COLORS.ink }}>Overall SCD</div>
          <div style={{ marginTop: 6, fontSize: 19, lineHeight: 1.2, color: COLORS.muted }}>{c.numberLabel} · all 29 scenario types</div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 12, color: COLORS.muted }}>
        </div>
      </Reveal>

      <Reveal at={tt.question} style={{ position: "absolute", left: SIZE.margin, top: 820 }}>
        <Headline size={60}>{c.question}</Headline>
        <Sub size={28} style={{ marginTop: 12 }}>
          Explicit rule-conditioned evaluation reveals a large gap in existing planners.
        </Sub>
      </Reveal>
    </Scene>
  );
};
