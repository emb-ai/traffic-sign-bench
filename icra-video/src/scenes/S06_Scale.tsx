import { AbsoluteFill, Img, staticFile } from "remotion";
import { FIGURES } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Arrow, Headline, Reveal, Scene, Sub } from "../lib/ui";

export const S06_Scale: React.FC = () => {
  const c = TEXT.s06;
  const tt = T.s06;
  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 70 }}>
        <Headline>{c.headline}</Headline>
      </Reveal>

      {/* 29 × 100 × 10 = 29,000 */}
      <div style={{ position: "absolute", left: SIZE.margin, top: 190, display: "flex", alignItems: "flex-end", gap: 26 }}>
        {c.formula.map((tok, i) => {
          const isOp = c.formulaLabels[i] === "";
          return (
            <Reveal key={i} at={tt.formula + i * 0.25} style={{ textAlign: "center" }}>
              <div style={{ fontSize: isOp ? 64 : 110, fontWeight: isOp ? 400 : 900, lineHeight: 1, color: isOp ? COLORS.faint : i === c.formula.length - 1 ? COLORS.blue : COLORS.ink, fontVariantNumeric: "tabular-nums" }}>{tok}</div>
              <div style={{ fontSize: 22, color: COLORS.muted, marginTop: 8, height: 28 }}>{c.formulaLabels[i]}</div>
            </Reveal>
          );
        })}
      </div>

      {/* variation axes */}
      <div style={{ position: "absolute", left: SIZE.margin, top: 420 }}>
        <Reveal at={tt.axes - 0.3}><Sub size={26}>10 variants per map vary</Sub></Reveal>
        <div style={{ display: "flex", gap: 14, marginTop: 14, flexWrap: "wrap", width: 1000 }}>
          {c.axes.map((a, i) => (
            <Reveal key={a} at={tt.axes + i * tt.axisStep} dy={8}>
              <div style={{ fontSize: 26, padding: "10px 20px", backgroundColor: COLORS.panel, borderRadius: 10 }}>{a}</div>
            </Reveal>
          ))}
        </div>
        <Reveal at={tt.axes + c.axes.length * tt.axisStep} style={{ marginTop: 12 }}><Sub size={22}>{c.axesNote}</Sub></Reveal>
      </div>

      {/* split diagram */}
      <div style={{ position: "absolute", left: SIZE.margin, top: 700, display: "flex", alignItems: "center", gap: 26 }}>
        {c.split.map((s, i) => (
          <React.Fragment key={s}>
            {i > 0 && (
              <Reveal at={tt.split + i * tt.splitStep - 0.2}><Arrow /></Reveal>
            )}
            <Reveal at={tt.split + i * tt.splitStep} dy={10}>
              <div style={{ fontSize: 28, fontWeight: 700, padding: "18px 26px", border: `2px solid ${i === 2 ? COLORS.blue : COLORS.border}`, borderRadius: 12, color: i === 2 ? COLORS.blue : COLORS.ink }}>{s}</div>
            </Reveal>
          </React.Fragment>
        ))}
      </div>
      <Reveal at={tt.split + 3 * tt.splitStep} style={{ position: "absolute", left: SIZE.margin, top: 820 }}>
        <Headline size={44}>{c.splitText}</Headline>
        <Sub size={26} style={{ marginTop: 8 }}>{c.splitSizes}</Sub>
      </Reveal>

      {/* real overview of crop locations, small */}
      <Reveal at={0.6} style={{ position: "absolute", left: 1290, top: 190 }}>
        <Img src={staticFile(FIGURES.moscowOverview)} style={{ width: 540, height: 608, objectFit: "cover", borderRadius: SIZE.panelRadius, border: `2px solid ${COLORS.border}` }} />
        <div style={{ fontSize: 20, color: COLORS.muted, marginTop: 8 }}>26,020 crop centres on the real Moscow network</div>
      </Reveal>
      <AbsoluteFill />
    </Scene>
  );
};
import React from "react";
