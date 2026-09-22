import { Easing, OffthreadVideo, interpolate, staticFile } from "remotion";
import { COLORS } from "../config/style";
import { Scene, clamp, useT } from "../lib/ui";

const CLIPS = [
  "dir_l_r_plant2_ft",
  "dir_r_plant2_ft",
  "dir_s_r_plant2_ft",
  "dual_T_1077490130_r_l_4ae62c0c_rl120_td25_sv1_v2_v2_s1148061518_carl_rule_default",
  "dual_T_1077491251_l_r_1645196a_rl90_td25_sv2_v0_v0_s2071920790_carl_rule_default",
  "dual_T_1221647944_s_l_455c08d9_td25_sv0_v0_v0_s850099808_carl_rule_default",
  "dual_T_13453364033_r_l_70c728bb_rl120_td50_sv0_v2_v2_s2135201830_carl_default",
  "dual_T_1586624975_l_s_4a76b329_rl120_td25_sv1_v0_v0_s2408151938_carl_default",
  "dual_T_271883013_r_s_cae20a3c_rl120_td50_sv1_v0_v0_s686031779_carl_rule_default",
  "dual_T_293842063_r_l_e877227f_rl120_td75_sv2_v2_v2_s3069055251_carl_rule_default",
  "dual_X_1253560025_r_s_29440a1e_v0_s118263357_carl_default",
  "dual_X_1431788659_l_r_96db86c1_v0_s2317185136_carl_default",
  "dual_X_302630317_r_s_61082039_v0_s4003151974_carl_rule_default",
  "junc_247899940_rl90_td75_sv0_v1_v1_s4282348834_carl_rule_default",
  "junc_247917340_td50_sv0_v2_v2_s3261771920_carl_default",
  "junc_248073665_td75_sv0_v0_v0_s1476704977_carl_default",
  "junc_248789403_rl90_td25_sv0_v0_v0_s2130466587_carl_rule_default",
  "junc_252847112_td50_sv1_v1_v1_s1120895108_carl_rule_default",
  "junc_35925624_rl90_td25_sv0_v0_v0_s2642426466_carl_rule_default",
  "junc_4974239205_rl120_td25_sv0_v2_v2_s1054559104_carl_rule_default",
  "junc_cluster_262102175_7803792898_rl90_td25_sv0_v2_v2_s380257321_carl_rule_default",
  "junc_cluster_331124903_331125559_9231030895_rl120_td25_sv0_v1_v1_s1379954188_carl_default",
  "no_turn_r_plant2_ft",
  "one_way_r_plant2_ft",
  "rb_0bd89cc1a9bf_rl90_td50_sv0_v1_v1_s3334807197_carl_default",
  "rb_88c79ce92004_rl120_td75_sv0_v2_v2_s1402153459_carl_default",
  "seg_1046890829_0_v2_rl90_td25_sv1_v2_v2_s3904436445_carl_rule_default",
  "seg_157600565_0_v2_rl90_td75_sv1_v2_v2_s2761483825_carl_rule_default",
  "seg_190347149_0_190347149#0_L0_s3_v0_rl120_td25_sv0_v0_v0_s342091902_plant2_default",
  "seg_25007184_0_l1_v1_rl120_td50_v1_v1_s1667659565_carl_rule_default",
  "seg_301093476_3_301093476#3_L0_s3_v1_rl120_td25_sv0_v1_v1_s2626325529_plant2_default",
  "seg_428757195_428757195_L2_s1_v0_rl120_td50_sv1_v0_v0_s3577069508_plant2_default",
  "seg_503363220_0_l0_v0_v0_s1453853010_carl_rule_default",
  "seg_56079404_0_l1_v0_rl120_td75_v0_v0_s4019781188_idm_rule_default",
  "seg_m95344495_3_l1_v2_rl120_td50_v2_v2_s2566006641_carl_rule_default",
  "speed_carl_rule",
] as const;

// 9 columns × 4 rows = 36 clips
const COLS = 9;
const ROWS = 4;
const CLIPS_GRID = CLIPS.slice(0, COLS * ROWS);

// Sized so scale=1 fills the 1920×1080 frame (all 36 tiles visible, no empty margins).
const TILE_W = 206;
const TILE_H = 264;
const GAP = 8;
const GRID_W = COLS * TILE_W + (COLS - 1) * GAP; // 1918
const GRID_H = ROWS * TILE_H + (ROWS - 1) * GAP; // 1080
const ZOOM_END = Math.min(1920 / GRID_W, 1080 / GRID_H); // ≈1.001 — full mosaic in frame

// Compact, elegant central glass card
const CARD_W = 700;
const CARD_H = 390;

export const S02_Benchmark: React.FC = () => {
  const t = useT();

  // Pull back until the full mosaic fills the frame — stop there (no letterbox margins).
  const camera = interpolate(t, [0, 7.2], [5.4, ZOOM_END], {
    ...clamp,
    easing: Easing.bezier(0.4, 0.0, 0.2, 1),
  });

  // Frosted glass card emerges as the mosaic starts to open up
  const cardOpacity = interpolate(t, [0.7, 1.4], [0, 1], clamp);
  const cardScale = interpolate(t, [0.7, 1.4], [0.94, 1], {
    ...clamp,
    easing: Easing.bezier(0.22, 1, 0.36, 1),
  });

  return (
    <Scene>
      {/* 4 × 9 mosaic of 36 diverse benchmark rollouts */}
      <div
        style={{
          position: "absolute",
          left: (1920 - GRID_W) / 2,
          top: (1080 - GRID_H) / 2,
          width: GRID_W,
          height: GRID_H,
          transform: `scale(${camera})`,
          transformOrigin: "center",
        }}
      >
        {CLIPS_GRID.map((clip, index) => {
          const row = Math.floor(index / COLS);
          const col = index % COLS;
          return (
            <div
              key={clip}
              style={{
                position: "absolute",
                left: col * (TILE_W + GAP),
                top: row * (TILE_H + GAP),
                width: TILE_W,
                height: TILE_H,
                borderRadius: 10,
                overflow: "hidden",
                boxShadow: "0 8px 24px rgba(0,0,0,0.18)",
                border: "2.5px solid white",
              }}
            >
              <OffthreadVideo
                src={staticFile(`converted/solution/${clip}.mp4`)}
                muted
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </div>
          );
        })}
      </div>

      {/* Atmospheric darkening overlay */}
      <div style={{ position: "absolute", inset: 0, background: "rgba(10,18,27,0.22)" }} />

      {/* Sleek, highly transparent central glass card */}
      <div
        style={{
          position: "absolute",
          left: (1920 - CARD_W) / 2,
          top: (1080 - CARD_H) / 2,
          width: CARD_W,
          height: CARD_H,
          borderRadius: 24,
          background: "rgba(255, 255, 255, 0.55)",
          backdropFilter: "blur(4px)",
          boxShadow: "0 24px 70px rgba(10, 25, 45, 0.20)",
          border: "1.5px solid rgba(255, 255, 255, 0.50)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "20px 32px",
          boxSizing: "border-box",
          opacity: cardOpacity,
          transform: `scale(${cardScale})`,
        }}
      >
        {/* Line 1: 'To address this gap,' in italics */}
        <div
          style={{
            color: COLORS.blue,
            fontSize: 22,
            fontStyle: "italic",
            fontWeight: 700,
            lineHeight: 1.2,
            marginBottom: 4,
            textShadow: "0 1px 8px rgba(255,255,255,0.9)",
          }}
        >
          To address this gap,
        </div>

        {/* Line 2: 'WE INTRODUCE' */}
        <div
          style={{
            color: "#2C3E50",
            fontSize: 14,
            fontWeight: 900,
            letterSpacing: 3,
            textTransform: "uppercase",
            marginBottom: 8,
            textShadow: "0 1px 6px rgba(255,255,255,0.9)",
          }}
        >
          we introduce
        </div>

        {/* Grand headline */}
        <div
          style={{
            fontSize: 56,
            lineHeight: 1.05,
            fontWeight: 900,
            color: COLORS.ink,
            letterSpacing: -1,
            textShadow: "0 2px 12px rgba(255,255,255,0.9)",
          }}
        >
          TrafficSignBench
        </div>

        {/* Core benchmark mission */}
        <div
          style={{
            marginTop: 8,
            maxWidth: 780,
            fontSize: 20,
            lineHeight: 1.3,
            color: COLORS.ink,
            fontWeight: 700,
            textShadow: "0 1px 8px rgba(255,255,255,0.9)",
          }}
        >
          The first large-scale benchmark to jointly combine
        </div>

        {/* 3 Strong Scientific Pillars */}
        <div style={{ marginTop: 14, display: "flex", gap: 10, justifyContent: "center" }}>
          {[
            {
              title: "Broad Taxonomy",
              sub: "34 traffic signs",
              bg: "rgba(234, 242, 255, 0.75)",
              border: "rgba(184, 212, 244, 0.9)",
              color: COLORS.blue,
            },
            {
              title: "Rule Checkers",
              sub: "automatic & verifiable",
              bg: "rgba(234, 247, 239, 0.75)",
              border: "rgba(180, 226, 197, 0.9)",
              color: COLORS.green,
            },
            {
              title: "Targeted Scenarios",
              sub: "29,000 closed-loop",
              bg: "rgba(255, 244, 229, 0.75)",
              border: "rgba(246, 211, 164, 0.9)",
              color: "#B96E12",
            },
          ].map((pillar, index) => {
            const pOpacity = interpolate(t, [1.7 + index * 0.28, 2.05 + index * 0.28], [0, 1], clamp);
            return (
              <div
                key={pillar.title}
                style={{
                  opacity: pOpacity,
                  transform: `translateY(${(1 - pOpacity) * 10}px)`,
                  padding: "8px 16px",
                  borderRadius: 14,
                  background: pillar.bg,
                  backdropFilter: "blur(6px)",
                  border: `1.5px solid ${pillar.border}`,
                  textAlign: "center",
                  minWidth: 185,
                  boxShadow: "0 4px 12px rgba(0,0,0,0.06)",
                }}
              >
                <div style={{ color: pillar.color, fontSize: 17, fontWeight: 900 }}>{pillar.title}</div>
                <div style={{ color: COLORS.muted, fontSize: 13, fontWeight: 700, marginTop: 2 }}>{pillar.sub}</div>
              </div>
            );
          })}
        </div>

        {/* Quantitative validation numbers */}
        <div
          style={{
            marginTop: 16,
            paddingTop: 14,
            borderTop: "1.5px solid rgba(0,0,0,0.12)",
            display: "flex",
            gap: 36,
            alignItems: "center",
            justifyContent: "center",
            opacity: interpolate(t, [2.7, 3.2], [0, 1], clamp),
          }}
        >
          {[
            ["34", "traffic signs"],
            ["29,000", "closed-loop scenarios"],
            ["17", "planners evaluated"],
          ].map(([value, label]) => (
            <div key={label} style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
              <span
                style={{
                  color: COLORS.ink,
                  fontSize: 32,
                  fontWeight: 900,
                  fontVariantNumeric: "tabular-nums",
                  textShadow: "0 1px 6px rgba(255,255,255,0.8)",
                }}
              >
                {value}
              </span>
              <span style={{ color: COLORS.muted, fontSize: 15, fontWeight: 700 }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </Scene>
  );
};
