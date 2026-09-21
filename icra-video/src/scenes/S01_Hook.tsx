import { AbsoluteFill } from "remotion";
import { CLIPS, SIGNS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Clip, Headline, Icon, Mark, Reveal, Scene, Sub, useT } from "../lib/ui";

// The rollout starts immediately (no title card). Marks appear only when the
// on-screen verifier counter of the clip itself supports them.
export const S01_Hook: React.FC = () => {
  const t = useT();
  const c = TEXT.s01;
  const tt = T.s01;
  // pair_3_1_plant2_base.mp4 is 3.07 s; loop so it stays on screen
  return (
    <Scene>
      <Clip src={CLIPS.hook_plant2_no_entry} size={900} left={SIZE.margin} top={90} loop label={c.clipLabel} />

      <AbsoluteFill style={{ left: 1080, width: 750, top: 110 }}>
        <Reveal at={tt.kicker} style={{ display: "flex", alignItems: "center", gap: 22 }}>
          <Icon src={SIGNS.no_entry} size={96} />
          <div style={{ fontSize: SIZE.small, fontWeight: 700, letterSpacing: 2, color: GROUP.routing.text, textTransform: "uppercase" }}>{c.kicker}</div>
        </Reveal>
        <Reveal at={tt.headline} style={{ marginTop: 26 }}>
          <Headline size={72}>{c.headline}</Headline>
        </Reveal>

        <div style={{ marginTop: 44 }}>
          {c.checks.map((row, i) => {
            const at = row.state === "fail" ? tt.ruleFail : tt.checks + i * 0.4;
            const state = row.state === "fail" ? "fail" : "unknown";
            return (
              <Reveal key={row.label} at={at} dy={14} style={{ display: "flex", alignItems: "center", gap: 22, backgroundColor: COLORS.panel, borderRadius: SIZE.panelRadius, padding: "16px 24px", marginBottom: 12 }}>
                <Mark state={state} />
                <div>
                  <div style={{ fontSize: 34, fontWeight: 700 }}>{row.label}</div>
                  <div style={{ fontSize: 20, color: COLORS.muted }}>{row.note}</div>
                </div>
              </Reveal>
            );
          })}
        </div>

        <Reveal at={tt.mainText} style={{ marginTop: 40 }}>
          <Sub size={31} style={{ color: COLORS.ink, fontWeight: 700 }}>{c.main}</Sub>
        </Reveal>
      </AbsoluteFill>
      {t < 0 && null}
    </Scene>
  );
};
