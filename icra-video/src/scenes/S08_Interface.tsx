import { AbsoluteFill, interpolate } from "remotion";
import { CLIPS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Arrow, clamp, Clip, Headline, Mark, Reveal, Scene, Sub, useT } from "../lib/ui";

// Checker states are taken from the clips' own on-screen verifier counter:
// expert clip ends with Violations: 0, PlanT-2 clip ends with Violations: 1.
export const S08_Interface: React.FC = () => {
  const t = useT();
  const c = TEXT.s08;
  const tt = T.s08;
  const showHud = t >= tt.hud;
  const scdOpacity = interpolate(t, [tt.scd - 0.3, tt.scd + 0.3], [0, 1], clamp);
  const chainOpacity = 1 - scdOpacity;
  const S = 520;

  return (
    <Scene>
      <Clip src={CLIPS.checker_compliant} size={S} left={SIZE.margin} top={100} loop label={c.clipLeft} />
      <Clip src={CLIPS.checker_violation} size={S} left={SIZE.margin + S + 40} top={100} loop label={c.clipRight} />
      {showHud && (
        <>
          <Reveal at={tt.hud} style={{ position: "absolute", left: SIZE.margin + 16, top: 100 + S - 64 }}>
            <div style={{ fontSize: 26, fontWeight: 900, color: "#fff", backgroundColor: COLORS.green, padding: "8px 16px", borderRadius: 8 }}>{c.compliant}</div>
          </Reveal>
          <Reveal at={tt.hud + 0.3} style={{ position: "absolute", left: SIZE.margin + S + 56, top: 100 + S - 64 }}>
            <div style={{ fontSize: 26, fontWeight: 900, color: "#fff", backgroundColor: COLORS.red, padding: "8px 16px", borderRadius: 8 }}>{c.violation}</div>
          </Reveal>
        </>
      )}

      {/* chain */}
      <AbsoluteFill style={{ left: 1260, width: 600, top: 100, opacity: chainOpacity }}>
        {c.chain.map((s, i) => (
          <div key={s}>
            {i > 0 && (
              <Reveal at={tt.chain + i * tt.chainStep - 0.2} style={{ paddingLeft: 40 }}><Arrow dir="down" size={44} /></Reveal>
            )}
            <Reveal at={tt.chain + i * tt.chainStep} dy={10}>
              <div style={{ fontSize: 32, fontWeight: 700, padding: "18px 28px", border: `2px solid ${i === 1 ? COLORS.blue : COLORS.border}`, borderRadius: 12, backgroundColor: i === 3 ? COLORS.panel : "#fff", display: "inline-block" }}>{s}</div>
            </Reveal>
          </div>
        ))}
        <Reveal at={tt.chain + 4 * tt.chainStep} style={{ marginTop: 26 }}>
          <Sub size={24} style={{ color: COLORS.blue, fontWeight: 700 }}>{c.smallLabel}</Sub>
        </Reveal>
      </AbsoluteFill>

      {/* SCD explanation */}
      <AbsoluteFill style={{ left: 1260, width: 620, top: 100, opacity: scdOpacity }}>
        <Headline size={36}>{c.scdTitle}</Headline>
        <div style={{ display: "flex", gap: 24, marginTop: 26, fontSize: 22, color: COLORS.muted }}>
          <span style={{ width: 200 }}>{c.scdLabels.obey}</span>
          <span style={{ width: 240 }}>{c.scdLabels.dest}</span>
          <span style={{ width: 90, fontWeight: 700, color: COLORS.ink }}>{c.scdLabels.scd}</span>
        </div>
        {c.scdRows.map((r, i) => (
          <Reveal key={i} at={tt.scd + i * tt.scdStep} dy={10} style={{ display: "flex", gap: 24, alignItems: "center", marginTop: 18, padding: "12px 0", borderTop: `2px solid ${COLORS.border}` }}>
            <span style={{ width: 200 }}><Mark state={r.obey ? "ok" : "fail"} size={48} /></span>
            <span style={{ width: 240 }}><Mark state={r.dest ? "ok" : "fail"} size={48} /></span>
            <span style={{ width: 90 }}><Mark state={r.scd ? "ok" : "fail"} size={56} /></span>
          </Reveal>
        ))}
      </AbsoluteFill>

      <Reveal at={0.2} style={{ position: "absolute", left: SIZE.margin, top: 760 }}>
        <Headline size={44}>Automatic online rule verification during the rollout</Headline>
        <Sub size={26} style={{ marginTop: 8 }}>Each of the 34 signs has a verifier; the planner receives structured sign semantics and plans a trajectory.</Sub>
      </Reveal>
    </Scene>
  );
};
