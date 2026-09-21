import { AbsoluteFill, interpolate, Sequence, useVideoConfig } from "remotion";
import { CLIPS, SIGNS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Arrow, clamp, Clip, Footnote, Headline, Icon, Reveal, Scene, Sub, useT } from "../lib/ui";

// Animated scientific figure. Every box is grounded in third_party/plant2/PlanT/model.py
// and Sec. IV-D of the current paper: object tokens (tok_emb, one projection per class,
// incl. one per sign class), sign-state token (sign_emb over class@value vocabulary),
// learnable speed_token → ego_speed_classifier, path + waypoint heads, +147,976 params.
const Box: React.FC<{ children?: React.ReactNode; color?: string; fill?: string; w?: number; small?: boolean }> = ({ children, color = COLORS.border, fill = "#fff", w, small }) => (
  <div style={{ padding: small ? "10px 16px" : "14px 22px", border: `2px solid ${color}`, borderRadius: 12, backgroundColor: fill, fontSize: small ? 22 : 26, fontWeight: 700, width: w, boxSizing: "border-box", textAlign: "center" }}>{children}</div>
);

export const S10_Architecture: React.FC = () => {
  const t = useT();
  const { fps } = useVideoConfig();
  const c = TEXT.s10;
  const tt = T.s10;
  const toExpert = interpolate(t, [tt.expert - 0.4, tt.expert + 0.3], [0, 1], clamp);
  const toRollout = interpolate(t, [tt.rollout - 0.4, tt.rollout + 0.3], [0, 1], clamp);
  const NEW = GROUP.speed.text;

  return (
    <Scene>
      <Reveal at={0.1} style={{ position: "absolute", left: SIZE.margin, top: 50 }}>
        <Headline size={54}>{c.headline}</Headline>
        <Sub size={24}>{c.sub}</Sub>
      </Reveal>

      {/* Diagram */}
      <AbsoluteFill style={{ left: SIZE.margin, top: 190, width: 1740, opacity: 1 - toExpert }}>
        {/* input row */}
        <div style={{ display: "flex", alignItems: "flex-end", gap: 18 }}>
          <Reveal at={tt.scene}>
            <div style={{ fontSize: 20, color: COLORS.muted, marginBottom: 8 }}>{c.sceneLabel}</div>
            <div style={{ display: "flex", gap: 12 }}>
              {c.baseTokens.map((b) => <Box key={b} small>{b}</Box>)}
            </div>
          </Reveal>
          <Reveal at={tt.signToken} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 30, color: COLORS.faint }}>+</span>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <Icon src={SIGNS.no_entry} size={44} />
              <Box small color={NEW}>{c.newTokens[0].title}</Box>
              <div style={{ fontSize: 18, color: COLORS.muted }}>{c.newTokens[0].note}</div>
            </div>
          </Reveal>
          <Reveal at={tt.stateToken} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 30, color: COLORS.faint }}>+</span>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <Icon src={SIGNS.speed_limit_20} size={44} />
              <Box small color={NEW}>{c.newTokens[1].title}</Box>
              <div style={{ fontSize: 18, color: COLORS.muted }}>{c.newTokens[1].note}</div>
            </div>
          </Reveal>
          <Reveal at={tt.speedToken} style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span style={{ fontSize: 30, color: COLORS.faint }}>+</span>
            <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <div style={{ height: 44 }} />
              <Box small color={NEW}>{c.newTokens[2].title}</Box>
              <div style={{ fontSize: 18, color: COLORS.muted }}>{c.newTokens[2].note}</div>
            </div>
          </Reveal>
        </div>

        {/* backbone */}
        <Reveal at={tt.baseTokens} style={{ marginTop: 26, marginLeft: 300 }}>
          <Arrow dir="down" size={40} />
          <Box w={700} color={COLORS.blue}>{c.backbone}</Box>
        </Reveal>

        {/* heads */}
        <Reveal at={tt.heads} style={{ marginTop: 22, marginLeft: 300, display: "flex", gap: 40 }}>
          {c.heads.map((h, i) => (
            <div key={h} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6 }}>
              <Arrow dir="down" size={36} />
              <Box w={200} color={i === 2 ? NEW : COLORS.border}>{h}</Box>
              <div style={{ fontSize: 18, color: COLORS.muted }}>{c.headsNote[i]}</div>
            </div>
          ))}
        </Reveal>

        <Reveal at={tt.params} style={{ position: "absolute", right: 0, top: 380 }}>
          <div style={{ fontSize: 40, fontWeight: 900, color: NEW }}>{c.params}</div>
          <div style={{ fontSize: 20, color: COLORS.muted }}>new components only · backbone unchanged</div>
        </Reveal>
      </AbsoluteFill>

      {/* Expert supervision → FT */}
      <AbsoluteFill style={{ left: SIZE.margin, top: 190, width: 1740, opacity: toExpert * (1 - toRollout) }}>
        <div style={{ display: "flex", alignItems: "center", gap: 30, marginTop: 120 }}>
          {c.expert.map((s, i) => (
            <React.Fragment key={s}>
              {i > 0 && <Arrow size={52} />}
              <Box color={i === 2 ? NEW : COLORS.border} fill={i === 2 ? COLORS.panel : "#fff"}>
                <span style={{ fontSize: 34 }}>{s}</span>
              </Box>
            </React.Fragment>
          ))}
        </div>
        <Sub size={26} style={{ marginTop: 40 }}>path + waypoint L1 losses · cross-entropy over soft two-hot speed targets · closed-loop checkpoint selection</Sub>
      </AbsoluteFill>

      {/* Rollout */}
      <Sequence from={Math.round((tt.rollout - 0.4) * fps)} premountFor={30}>
        <div style={{ opacity: toRollout }}>
          <Clip src={CLIPS.arch_rollout} size={760} left={SIZE.margin} top={170} label={c.rolloutLabel} />
          <AbsoluteFill style={{ left: 940, width: 900, top: 260 }}>
            <Headline size={56}>PlanT-2-FT in closed loop</Headline>
            <Sub size={28} style={{ marginTop: 14 }}>Sign 3.24 speed limit · the planner slows to the posted value</Sub>
          </AbsoluteFill>
        </div>
      </Sequence>
      {t >= tt.rollout - 0.4 && <Footnote>{c.footnote}</Footnote>}
    </Scene>
  );
};
import React from "react";
