import { AbsoluteFill, Img, interpolate, Sequence, staticFile, useVideoConfig } from "remotion";
import { CLIPS, FIGURES, REALMAP_SCENE, SIGNS } from "../config/assets";
import { TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { clamp, Clip, Footnote, Headline, Icon, Reveal, Scene, useT } from "../lib/ui";

// Real dual-path map. Route overlays come from the project renderer using the
// scene's meta.json (baseline = shorter, prohibited; compliant = longer).
export const S05_Routing: React.FC = () => {
  const t = useT();
  const { fps } = useVideoConfig();
  const c = TEXT.s05;
  const tt = T.s05;
  const routes = interpolate(t, [tt.baseline, tt.baseline + 0.8], [0, 1], clamp);
  const toRollout = interpolate(t, [tt.rollout, tt.rollout + 0.7], [0, 1], clamp);
  const S = 860;

  return (
    <Scene>
      <div style={{ position: "absolute", left: SIZE.margin, top: 90, width: S, height: S, borderRadius: SIZE.panelRadius, overflow: "hidden", border: `2px solid ${COLORS.border}` }}>
        <Img src={staticFile(FIGURES.cropPlain)} style={{ position: "absolute", width: S, height: S, objectFit: "cover" }} />
        <Img src={staticFile(FIGURES.cropRoutes)} style={{ position: "absolute", width: S, height: S, objectFit: "cover", opacity: routes * (1 - toRollout) }} />
        <Sequence from={Math.round(tt.rollout * fps)} premountFor={30}>
          <div style={{ opacity: toRollout }}>
            <Clip src={CLIPS.routing_rollout} size={S} left={0} top={0} loop />
          </div>
        </Sequence>
        <div style={{ position: "absolute", left: 16, bottom: 14, fontSize: 20, color: COLORS.muted, backgroundColor: "rgba(255,255,255,0.85)", padding: "4px 10px", borderRadius: 6 }}>
          {t < tt.rollout ? `real-map crop ${REALMAP_SCENE.id.split("_")[1]}` : c.rolloutLabel}
        </div>
      </div>

      <AbsoluteFill style={{ left: 1040, width: 800, top: 100 }}>
        <Reveal at={0.2} style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <Icon src={SIGNS.direction_right} size={84} />
          <div style={{ fontSize: 26, color: COLORS.muted }}>{c.sign}</div>
        </Reveal>

        <Reveal at={tt.baseline} style={{ marginTop: 44, display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ width: 64, height: 12, backgroundColor: COLORS.red, borderRadius: 6 }} />
          <div style={{ fontSize: 32, fontWeight: 700 }}>{c.baseline.label}</div>
          <div style={{ fontSize: 32, color: COLORS.muted, fontVariantNumeric: "tabular-nums" }}>{c.baseline.length}</div>
        </Reveal>
        <Reveal at={tt.compliant} style={{ marginTop: 18, display: "flex", alignItems: "center", gap: 20 }}>
          <div style={{ width: 64, height: 12, backgroundColor: COLORS.green, borderRadius: 6 }} />
          <div style={{ fontSize: 32, fontWeight: 700 }}>{c.compliant.label}</div>
          <div style={{ fontSize: 32, color: COLORS.muted, fontVariantNumeric: "tabular-nums" }}>{c.compliant.length}</div>
        </Reveal>

        <Reveal at={tt.mainText} style={{ marginTop: 60 }}>
          <Headline size={52}>{c.headline}</Headline>
          <Headline size={52} color={GROUP.routing.text}>{c.headline2}</Headline>
        </Reveal>
      </AbsoluteFill>
      <Footnote>{c.footnote}</Footnote>
    </Scene>
  );
};
