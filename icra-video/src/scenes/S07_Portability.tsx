import { AbsoluteFill, Img, staticFile } from "remotion";
import { FIGURES, FLAGS } from "../config/assets";
import { COUNTRIES, TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Headline, Reveal, Scene, Sub } from "../lib/ui";

// Country sign graphics: old-paper Fig. 4 (visual reference only).
// All numbers: current paper, Table I.
export const S07_Portability: React.FC = () => {
  const c = TEXT.s07;
  const tt = T.s07;
  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 60 }}>
        <Headline>{c.headline}</Headline>
      </Reveal>

      <Reveal at={tt.figure} style={{ position: "absolute", left: SIZE.margin, top: 170 }}>
        <div style={{ width: 1740, height: 520, overflow: "hidden", borderRadius: SIZE.panelRadius }}>
          <Img src={staticFile(FIGURES.signCountries)} style={{ width: 1740, marginTop: -70 }} />
        </div>
        <div style={{ fontSize: 20, color: COLORS.muted, marginTop: 6 }}>{c.figureNote}</div>
      </Reveal>

      <div style={{ position: "absolute", left: SIZE.margin, top: 730, display: "flex", gap: 22 }}>
        {COUNTRIES.map((k, i) => (
          <Reveal key={k.key} at={tt.flags + i * tt.flagStep} dy={10}>
            <div style={{ width: 200, padding: "16px 0", backgroundColor: COLORS.panel, borderRadius: 12, textAlign: "center", borderTop: `6px solid ${k.vienna ? COLORS.blue : COLORS.faint}` }}>
              <Img src={staticFile(FLAGS[k.key as keyof typeof FLAGS])} style={{ height: 30, borderRadius: 3 }} />
              <div style={{ fontSize: 22, color: COLORS.muted, marginTop: 6 }}>{k.label}</div>
              <div style={{ fontSize: 44, fontWeight: 900, fontVariantNumeric: "tabular-nums" }}>{k.pct}%</div>
            </div>
          </Reveal>
        ))}
        <Reveal at={tt.flags + 6 * tt.flagStep} style={{ alignSelf: "center", marginLeft: 10, fontSize: 20, color: COLORS.muted, lineHeight: 1.5 }}>
          <div><span style={{ display: "inline-block", width: 14, height: 14, backgroundColor: COLORS.blue, borderRadius: 3, marginRight: 8 }} />{c.vienna}</div>
          <div><span style={{ display: "inline-block", width: 14, height: 14, backgroundColor: COLORS.faint, borderRadius: 3, marginRight: 8 }} />{c.nonVienna}</div>
        </Reveal>
      </div>

      <Reveal at={tt.result} style={{ position: "absolute", left: SIZE.margin, top: 930 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 24 }}>
          <Headline size={56} color={COLORS.blue}>{c.result}</Headline>
          <Sub size={28}>{c.resultSub}</Sub>
        </div>
        <Sub size={22} style={{ marginTop: 6 }}>{c.sub}</Sub>
      </Reveal>
      <AbsoluteFill />
    </Scene>
  );
};
