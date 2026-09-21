import { Video } from "@remotion/media";
import { AbsoluteFill, Img, interpolate, Sequence, staticFile, useVideoConfig } from "remotion";
import { CLIPS, FIGURES, OVERVIEW, REALMAP_SCENE } from "../config/assets";
import { NUMBERS, TEXT } from "../config/content";
import { COLORS, GROUP, SIZE } from "../config/style";
import { T } from "../config/timing";
import { clamp, CountUp, ease, Headline, Reveal, Scene, useT } from "../lib/ui";

// One continuous process on ONE real crop: full Moscow SUMO network (real)
// → highlight the crop bbox (from the scene's meta.json) → zoom → the real
// crop rendered by the project renderer → the simulator scene preview →
// a real closed-loop rollout on that crop.
const STAGE = 900; // px, left panel
const LEFT = SIZE.margin;
const TOP = 90;

// SUMO metres → pixels in the overview image
const toPx = (x: number, y: number) => ({
  x: ((x - OVERVIEW.xlim[0]) / (OVERVIEW.xlim[1] - OVERVIEW.xlim[0])) * OVERVIEW.width,
  y: ((OVERVIEW.ylim[1] - y) / (OVERVIEW.ylim[1] - OVERVIEW.ylim[0])) * OVERVIEW.height,
});

export const S03_RealMaps: React.FC = () => {
  const t = useT();
  const { fps } = useVideoConfig();
  const c = TEXT.s03;
  const tt = T.s03;

  const [bx0, by0, bx1, by1] = REALMAP_SCENE.bbox;
  const p0 = toPx(bx0, by1); // top-left in image px
  const p1 = toPx(bx1, by0); // bottom-right
  const bw = p1.x - p0.x;
  const bh = p1.y - p0.y;
  const cx = (p0.x + p1.x) / 2;
  const cy = (p0.y + p1.y) / 2;

  // Scale of the overview: fit the stage at start, then zoom until the bbox fills ~600 px
  const s0 = STAGE / OVERVIEW.height;
  const s1 = 620 / Math.max(bw, bh);
  const zoom = interpolate(t, [tt.zoomStart, tt.zoomEnd], [0, 1], { ...clamp, easing: ease });
  const s = s0 * Math.pow(s1 / s0, zoom);
  // Keep image top-left aligned at zoom 0, keep bbox centre at stage centre at zoom 1
  const tx0 = (STAGE - OVERVIEW.width * s0) / 2;
  const ty0 = 0;
  const tx1 = STAGE / 2 - cx * s1;
  const ty1 = STAGE / 2 - cy * s1;
  const tx = interpolate(zoom, [0, 1], [tx0, tx1]);
  const ty = interpolate(zoom, [0, 1], [ty0, ty1]);
  // highlight rectangle in stage px
  const rx = tx + p0.x * s;
  const ry = ty + p0.y * s;
  const rw = Math.max(bw * s, 14);
  const rh = Math.max(bh * s, 14);

  const overviewOpacity = interpolate(t, [tt.cropRender, tt.cropRender + 1.2], [1, 0], clamp);
  const cropOpacity = interpolate(t, [tt.cropRender, tt.cropRender + 1.0], [0, 1], clamp);
  const previewOpacity = interpolate(t, [tt.scenePreview, tt.scenePreview + 0.8], [0, 1], clamp);
  const rolloutOpacity = interpolate(t, [tt.rollout, tt.rollout + 0.6], [0, 1], clamp);

  const step = t < tt.highlight ? 0 : t < tt.cropRender + 0.5 ? 1 : t < tt.scenePreview ? 2 : t < tt.rollout ? 3 : 4;

  return (
    <Scene>
      {/* LEFT: the stage */}
      <div style={{ position: "absolute", left: LEFT, top: TOP, width: STAGE, height: STAGE, overflow: "hidden", borderRadius: SIZE.panelRadius, border: `2px solid ${COLORS.border}`, backgroundColor: "#fff" }}>
        <div style={{ position: "absolute", left: 0, top: 0, opacity: overviewOpacity }}>
          <Img
            src={staticFile(FIGURES.moscowOverview)}
            style={{ position: "absolute", left: tx, top: ty, width: OVERVIEW.width * s, height: OVERVIEW.height * s }}
          />
          <div
            style={{
              position: "absolute",
              left: rx - 4,
              top: ry - 4,
              width: rw + 8,
              height: rh + 8,
              border: `4px solid ${COLORS.blue}`,
              borderRadius: 4,
              boxShadow: "0 0 0 2px rgba(255,255,255,0.9)",
              opacity: interpolate(t, [tt.highlight, tt.highlight + 0.4], [0, 1], clamp),
            }}
          />
        </div>
        <Img src={staticFile(FIGURES.cropPlain)} style={{ position: "absolute", left: 0, top: 0, width: STAGE, height: STAGE, objectFit: "cover", opacity: cropOpacity }} />
        <Img src={staticFile(FIGURES.scenePreview)} style={{ position: "absolute", left: 0, top: 0, width: STAGE, height: STAGE, objectFit: "contain", backgroundColor: "#fff", opacity: previewOpacity }} />
        <Sequence from={Math.round(tt.rollout * fps)} premountFor={30}>
          <Video src={staticFile(CLIPS.realmap_rollout)} muted loop style={{ position: "absolute", left: 0, top: 0, width: STAGE, height: STAGE, opacity: rolloutOpacity }} />
        </Sequence>
        <div style={{ position: "absolute", left: 16, bottom: 14, fontSize: 20, color: COLORS.muted, backgroundColor: "rgba(255,255,255,0.85)", padding: "4px 10px", borderRadius: 6 }}>
          {step === 0 ? c.mapCaption : step === 4 ? c.rolloutLabel : c.steps[step]}
        </div>
      </div>

      {/* RIGHT: text */}
      <AbsoluteFill style={{ left: 1080, width: 760, top: 110 }}>
        <Headline size={60}>{c.headline}</Headline>
        <Reveal at={tt.rollout - 0.5}>
          <Headline size={60} color={GROUP.routing.text}>{c.headline2}</Headline>
        </Reveal>

        <div style={{ marginTop: 44, display: "flex", flexDirection: "column", gap: 14 }}>
          {c.steps.map((label, i) => {
            const active = i === step;
            const done = i < step;
            return (
              <div key={label} style={{ display: "flex", gap: 16, alignItems: "baseline", fontSize: 27, fontWeight: active ? 700 : 400, color: active ? COLORS.ink : done ? COLORS.muted : COLORS.faint }}>
                <span style={{ width: 28, color: active ? COLORS.blue : "inherit" }}>{i + 1}</span>
                {label}
              </div>
            );
          })}
        </div>

        <Reveal at={tt.counterStart} style={{ marginTop: 50, display: "flex", alignItems: "baseline", gap: 18 }}>
          <CountUp from={0} to={26020} start={tt.counterStart} end={tt.counterEnd} style={{ fontSize: 96, fontWeight: 900, lineHeight: 1 }} />
          <span style={{ fontSize: 30, color: COLORS.muted }}>{c.cropsLabel}</span>
        </Reveal>

        <div style={{ marginTop: 26, display: "flex", flexDirection: "column", gap: 8 }}>
          {c.breakdown.map((b, i) => (
            <Reveal key={b.label} at={tt.breakdown + i * 0.3} dy={8} style={{ display: "flex", gap: 14, fontSize: 25, alignItems: "baseline" }}>
              <span style={{ width: 12, height: 12, borderRadius: 6, backgroundColor: i === 0 ? GROUP.priority.bar : i === 1 ? GROUP.routing.bar : GROUP.obstacles.bar, translate: "0px -2px" }} />
              <b style={{ width: 130 }}>{b.label}</b>
              <span style={{ width: 100, fontVariantNumeric: "tabular-nums" }}>{b.n}</span>
              <span style={{ color: COLORS.muted, fontSize: 22 }}>{b.use}</span>
            </Reveal>
          ))}
        </div>
      </AbsoluteFill>
      {NUMBERS.crops && null}
    </Scene>
  );
};
