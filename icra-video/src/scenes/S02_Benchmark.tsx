import { AbsoluteFill } from "remotion";
import { CLIPS, GROUP_ICONS } from "../config/assets";
import { GROUPS, TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { Card, Clip, Headline, Icon, Reveal, Scene, Sub, useT } from "../lib/ui";

const CLIP_FOR = {
  priority: CLIPS.group_priority_yield,
  speed: CLIPS.group_speed_limit,
  obstacles: CLIPS.group_obstacles_detour,
  routing: CLIPS.group_routing_one_way,
} as const;
const TRIM_FOR = { priority: 3, speed: 2, obstacles: 0, routing: 0 } as const;

export const S02_Benchmark: React.FC = () => {
  const t = useT();
  const c = TEXT.s02;
  const tt = T.s02;
  const cardW = 410;
  const gap = 32;
  const x0 = SIZE.margin;
  return (
    <Scene>
      <Reveal at={tt.title} style={{ position: "absolute", left: SIZE.margin, top: 60 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 26 }}>
          <Headline>{c.title}</Headline>
          <Sub>{c.subtitle}</Sub>
        </div>
      </Reveal>

      {GROUPS.map((g, i) => {
        const col = GROUP[g.key];
        const at = tt.cards + i * tt.cardStep;
        return (
          <Reveal key={g.key} at={at} dy={40}>
            <Card
              bar={col.bar}
              title={col.label}
              right={
                <span style={{ color: col.text }}>
                  <b>{g.signs} signs</b> · {g.scenarios} scenarios
                </span>
              }
              style={{ left: x0 + i * (cardW + gap), top: 160, width: cardW, height: 720 }}
            >
              <div style={{ margin: "4px 16px 0", height: 150, backgroundColor: COLORS.panel, borderRadius: SIZE.panelRadius, display: "flex", flexWrap: "wrap", alignContent: "center", justifyContent: "center", gap: 8, padding: 10, boxSizing: "border-box" }}>
                {GROUP_ICONS[g.key].map((icon, j) => (
                  <Reveal key={icon} at={at + 0.3 + j * 0.06} dy={6}>
                    <Icon src={`signs/${icon}.png`} size={56} />
                  </Reveal>
                ))}
              </div>
              <div style={{ margin: "14px 16px 0", fontSize: 20, color: COLORS.muted }}>
                <b style={{ color: COLORS.ink }}>example:</b> {g.example}
              </div>
              <Clip src={CLIP_FOR[g.key]} size={cardW - 32} left={16} top={300} loop trimBeforeSec={TRIM_FOR[g.key]} />
            </Card>
          </Reveal>
        );
      })}

      <AbsoluteFill style={{ top: 910, left: SIZE.margin, flexDirection: "row", gap: 90 }}>
        {c.stats.map((s, i) => (
          <Reveal key={s.label} at={tt.numbers + i * 0.4} style={{ display: "flex", alignItems: "baseline", gap: 16 }}>
            <span style={{ fontSize: 84, fontWeight: 900, lineHeight: 1 }}>{s.value}</span>
            <span style={{ fontSize: 30, color: COLORS.muted }}>{s.label}</span>
          </Reveal>
        ))}
      </AbsoluteFill>
      {t < 0 && null}
    </Scene>
  );
};
