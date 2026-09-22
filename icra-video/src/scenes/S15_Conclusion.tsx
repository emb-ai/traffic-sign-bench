// Conclusion: the paper's main findings as four cards (benchmark → evaluation → fine-tuning → open challenge),
// in the header/card style of the fine-tuning section. Editable content: src/config/conclusionScene.ts
import { Img, staticFile } from "remotion";
import { CONCLUSION as C } from "../config/conclusionScene";
import { PAPER } from "../config/paperStyle";
import { COLORS, SIZE } from "../config/style";
import { Headline, rise, Scene, useT } from "../lib/ui";

export const S15_Conclusion: React.FC = () => {
  const t = useT();
  const W = (1920 - 2 * SIZE.margin - 3 * 30) / 4;
  return (
    <Scene>
      <div style={{ position: "absolute", left: SIZE.margin, right: SIZE.margin, top: 44, opacity: rise(t, C.timing.header, 0.4) }}>
        <div style={{ display: "inline-block", padding: "4px 14px", borderRadius: 999, ...PAPER.pill, color: COLORS.blue, fontSize: 13, fontWeight: 900, letterSpacing: 2.2, textTransform: "uppercase", marginBottom: 8 }}>{C.kicker}</div>
        <Headline size={50}>{C.title}</Headline>
        <div style={{ marginTop: 6, color: COLORS.muted, fontSize: 24, fontWeight: 700 }}>{C.subtitle}</div>
      </div>
      {C.cards.map((c, i) => {
        const p = rise(t, C.timing.card0 + i * C.timing.cardStep, 0.6);
        return (
          <div key={c.kicker} style={{
            position: "absolute", left: SIZE.margin + i * (W + 30), top: 290, width: W, height: 480, boxSizing: "border-box", padding: "28px 28px",
            backgroundColor: "#fff", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, borderTop: `6px solid ${c.color}`, boxShadow: PAPER.cardShadow,
            opacity: p, transform: `translateY(${(1 - p) * 20}px)`,
          }}>
            <div style={{ ...PAPER.sectionLabel, color: c.color }}>{c.kicker}</div>
            <div style={{ fontSize: c.value.length > 10 ? 50 : 64, fontWeight: 900, color: c.color, lineHeight: 1.1, marginTop: 26, fontVariantNumeric: "tabular-nums" }}>{c.value}</div>
            <div style={{ fontSize: 22, fontWeight: 800, color: COLORS.ink, marginTop: 8 }}>{c.unit}</div>
            <div style={{ fontSize: 23, fontWeight: 700, color: "#475569", marginTop: 26, lineHeight: 1.35 }}>{c.body}</div>
            {c.icons.length > 0 && (
              <div style={{ position: "absolute", left: 28, bottom: 28, display: "flex", gap: 14 }}>
                {c.icons.map((src) => <Img key={src} src={staticFile(src)} style={{ width: 56, height: 56 }} />)}
              </div>
            )}
          </div>
        );
      })}
    </Scene>
  );
};
