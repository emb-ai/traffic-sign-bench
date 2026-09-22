import { Gif } from "@remotion/gif";
import { Img, interpolate, Sequence, staticFile, useVideoConfig } from "remotion";
import { FIGURES, REAL_MAPS } from "../config/assets";
import { COLORS, GROUP } from "../config/style";
import { T } from "../config/timing";
import { clamp, CountUp, ease, rise, Scene, useT } from "../lib/ui";

const MAP = { x: 58, y: 82, w: 790, h: 916 };
const CARD = { x: 928, w: 920, h: 258, firstY: 126, gap: 286 };

const FAMILIES = [
  {
    key: "junction",
    label: "Junction",
    count: "6,457",
    purpose: "priority interactions",
    color: GROUP.priority.text,
    point: { x: 0.22, y: 0.24 },
    signAt: { x: 220, y: 98 },
    ...REAL_MAPS.junction,
  },
  {
    key: "dual-path",
    label: "Dual-path",
    count: "6,507",
    purpose: "route restrictions",
    color: GROUP.routing.text,
    point: { x: 0.78, y: 0.42 },
    signAt: { x: 176, y: 70 },
    ...REAL_MAPS.dualPath,
  },
  {
    key: "corridor",
    label: "Corridor",
    count: "13,056",
    purpose: "speed · obstacles · crosswalks",
    color: GROUP.obstacles.text,
    point: { x: 0.4, y: 0.76 },
    signAt: { x: 234, y: 86 },
    ...REAL_MAPS.corridor,
  },
] as const;

const CropCard: React.FC<{
  family: (typeof FAMILIES)[number];
  index: number;
}> = ({ family, index }) => {
  const t = useT();
  const { fps } = useVideoConfig();
  const tt = T.s03;
  const revealAt = tt.crops + index * 0.24;
  const videoAt = tt.rollouts + index * 0.22;
  const p = rise(t, revealAt, 0.65);
  const sign = rise(t, tt.signs + index * 0.16, 0.45);
  const video = rise(t, videoAt, 0.55);

  return (
    <div
      style={{
        position: "absolute",
        left: CARD.x,
        top: CARD.firstY + index * CARD.gap,
        width: CARD.w,
        height: CARD.h,
        boxSizing: "border-box",
        border: `2px solid ${COLORS.border}`,
        borderRadius: 20,
        overflow: "hidden",
        background: "#fff",
        boxShadow: `0 18px 45px rgba(28, 44, 64, ${0.05 + p * 0.08})`,
        opacity: p,
        transform: `translateX(${(1 - p) * 34}px)`,
      }}
    >
      <div style={{ position: "absolute", inset: "0 auto 0 0", width: 10, background: family.color }} />

      <div
        style={{
          position: "absolute",
          left: 28,
          top: 19,
          width: 386,
          height: 218,
          borderRadius: 13,
          overflow: "hidden",
          background: "#f8fafb",
          border: `1px solid ${COLORS.border}`,
        }}
      >
        <Img
          src={staticFile(family.crop)}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            opacity: 1 - video,
            filter: "contrast(1.2)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: family.signAt.x,
            top: family.signAt.y,
            width: 64,
            height: 64,
            padding: 7,
            boxSizing: "border-box",
            borderRadius: 16,
            background: "rgba(255,255,255,0.96)",
            border: `2px solid ${family.color}`,
            boxShadow: `0 8px 22px ${family.color}55`,
            opacity: sign * (1 - video),
            transform: `scale(${0.65 + sign * 0.35})`,
          }}
        >
          <Img src={staticFile(family.sign)} style={{ width: "100%", height: "100%", objectFit: "contain" }} />
        </div>

        <Sequence from={Math.round(videoAt * fps)} premountFor={fps}>
          <Gif
            src={staticFile(family.rollout)}
            width={386}
            height={218}
            fit="contain"
            loopBehavior="loop"
            delayRenderTimeoutInMilliseconds={120_000}
            style={{
              position: "absolute",
              inset: 0,
              background: "#fff",
              opacity: video,
            }}
          />
        </Sequence>

        <div
          style={{
            position: "absolute",
            left: 10,
            bottom: 9,
            padding: "5px 10px",
            borderRadius: 999,
            background: video > 0.5 ? "rgba(22,31,43,0.82)" : "rgba(255,255,255,0.9)",
            color: video > 0.5 ? "#fff" : COLORS.ink,
            fontSize: 15,
            fontWeight: 700,
            letterSpacing: 0.5,
          }}
        >
          {video > 0.5 ? "CLOSED-LOOP ROLLOUT" : sign > 0.5 ? "SIGN PLACED" : "REAL-MAP CROP"}
        </div>
      </div>

      <div style={{ position: "absolute", left: 447, top: 34, right: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ width: 14, height: 14, borderRadius: 7, background: family.color }} />
          <div style={{ fontSize: 21, color: family.color, fontWeight: 900, letterSpacing: 1.7, textTransform: "uppercase" }}>
            {family.label}
          </div>
        </div>
        <div style={{ marginTop: 17, fontSize: 42, fontWeight: 900, lineHeight: 1.02 }}>
          {video > 0.5 ? "Executable test" : sign > 0.5 ? "Rule instantiated" : "Geometry selected"}
        </div>
        <div style={{ marginTop: 12, fontSize: 23, color: COLORS.muted }}>{family.purpose}</div>
        <div style={{ position: "absolute", top: 161, left: 0, display: "flex", alignItems: "center", gap: 10, fontSize: 18, color: COLORS.faint }}>
          <span style={{ fontWeight: 900, color: COLORS.ink }}>{family.count}</span>
          maps in source pool
        </div>
      </div>
    </div>
  );
};

export const S03_RealMaps: React.FC = () => {
  const t = useT();
  const tt = T.s03;
  const mapIn = rise(t, tt.map, 0.8);
  const colors = rise(t, tt.counterStart, 1.0);
  const selections = rise(t, tt.selection, 0.55);
  const summaryOut = interpolate(t, [tt.selection - 0.35, tt.crops + 0.25], [1, 0], {
    ...clamp,
    easing: ease,
  });

  return (
    <Scene>
      <div
        style={{
          position: "absolute",
          left: MAP.x,
          top: MAP.y,
          width: MAP.w,
          height: MAP.h,
          borderRadius: 24,
          overflow: "hidden",
          background: "#fff",
          border: `2px solid ${COLORS.border}`,
          boxShadow: "0 20px 65px rgba(38, 57, 77, 0.12)",
          opacity: mapIn,
          transform: `translateY(${(1 - mapIn) * 20}px)`,
        }}
      >
        <Img
          src={staticFile(FIGURES.moscowOverview)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            filter: "grayscale(1) contrast(1.45) brightness(0.98)",
            opacity: 0.72 - colors * 0.32,
          }}
        />
        <Img
          src={staticFile(FIGURES.moscowOverview)}
          style={{
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            objectFit: "fill",
            filter: "contrast(1.08) saturate(1.12)",
            opacity: colors,
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: "radial-gradient(circle at 50% 48%, transparent 52%, rgba(255,255,255,0.16) 100%)",
          }}
        />

        <div
          style={{
            position: "absolute",
            left: 20,
            top: 18,
            padding: "10px 15px",
            borderRadius: 12,
            background: "rgba(255,255,255,0.92)",
            border: `1px solid ${COLORS.border}`,
            boxShadow: "0 8px 26px rgba(30,46,62,0.09)",
          }}
        >
          <div style={{ fontSize: 19, fontWeight: 900, letterSpacing: 1.4 }}>MOSCOW ROAD NETWORK</div>
          <div style={{ marginTop: 2, fontSize: 16, color: COLORS.muted }}>OpenStreetMap → SUMO</div>
        </div>

        {FAMILIES.map((family, i) => {
          const point = rise(t, tt.selection + i * 0.16, 0.42);
          const pulse = 1 + 0.1 * Math.sin((t - tt.selection) * 4.5 + i);
          return (
            <div
              key={family.key}
              style={{
                position: "absolute",
                left: family.point.x * MAP.w - 13,
                top: family.point.y * MAP.h - 13,
                width: 26,
                height: 26,
                borderRadius: 15,
                background: family.color,
                border: "5px solid #fff",
                boxSizing: "border-box",
                boxShadow: `0 0 0 ${9 * point}px ${family.color}30, 0 5px 14px rgba(0,0,0,0.22)`,
                opacity: point,
                transform: `scale(${point * pulse})`,
              }}
            />
          );
        })}

        <div
          style={{
            position: "absolute",
            left: 20,
            bottom: 18,
            display: "flex",
            gap: 9,
            opacity: colors * summaryOut,
          }}
        >
          {FAMILIES.map((family) => (
            <div
              key={family.key}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 7,
                padding: "7px 10px",
                borderRadius: 999,
                background: "rgba(255,255,255,0.93)",
                border: `1px solid ${COLORS.border}`,
                fontSize: 15,
                fontWeight: 700,
              }}
            >
              <span style={{ width: 9, height: 9, borderRadius: 5, background: family.color }} />
              {family.label}
            </div>
          ))}
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: CARD.x,
          top: 72,
          width: CARD.w,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          opacity: rise(t, 0.35, 0.55),
        }}
      >
        <div style={{ fontSize: 19, fontWeight: 900, letterSpacing: 2, color: GROUP.routing.text }}>
          REAL MAPS → EXECUTABLE TESTS
        </div>
        <div
          style={{
            padding: "8px 14px",
            borderRadius: 999,
            background: "#F3F6FA",
            fontSize: 17,
            color: COLORS.muted,
            opacity: 1 - summaryOut,
          }}
        >
          <b style={{ color: COLORS.ink }}>26,020</b> source crops
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: CARD.x,
          top: 190,
          width: 860,
          opacity: summaryOut,
          transform: `translateY(${(1 - summaryOut) * -18}px)`,
        }}
      >
        <div style={{ fontSize: 29, color: COLORS.muted, fontWeight: 700 }}>One real city. Three structural families.</div>
        <div style={{ marginTop: 22, fontSize: 106, lineHeight: 0.92, fontWeight: 900, letterSpacing: -4 }}>
          <CountUp from={0} to={26020} start={tt.counterStart} end={tt.counterEnd} />
        </div>
        <div style={{ marginTop: 14, fontSize: 38, color: COLORS.ink, fontWeight: 700 }}>sign-free map crops</div>

        <div style={{ marginTop: 48, display: "flex", flexDirection: "column", gap: 15 }}>
          {FAMILIES.map((family, i) => (
            <div
              key={family.key}
              style={{
                display: "grid",
                gridTemplateColumns: "20px 180px 120px 1fr",
                alignItems: "center",
                gap: 13,
                fontSize: 25,
                opacity: rise(t, tt.breakdown + i * 0.2, 0.45),
                transform: `translateX(${(1 - rise(t, tt.breakdown + i * 0.2, 0.45)) * 20}px)`,
              }}
            >
              <span style={{ width: 14, height: 14, borderRadius: 8, background: family.color }} />
              <b>{family.label}</b>
              <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 900 }}>{family.count}</span>
              <span style={{ color: COLORS.muted }}>{family.purpose}</span>
            </div>
          ))}
        </div>
      </div>

      <svg
        width="1920"
        height="1080"
        viewBox="0 0 1920 1080"
        style={{ position: "absolute", inset: 0, pointerEvents: "none", opacity: selections }}
      >
        {FAMILIES.map((family, i) => {
          const p = rise(t, tt.selection + i * 0.16, 0.7);
          const x1 = MAP.x + family.point.x * MAP.w;
          const y1 = MAP.y + family.point.y * MAP.h;
          const y2 = CARD.firstY + i * CARD.gap + CARD.h / 2;
          return (
            <path
              key={family.key}
              d={`M ${x1} ${y1} C ${x1 + 95} ${y1}, ${CARD.x - 95} ${y2}, ${CARD.x} ${y2}`}
              fill="none"
              stroke={family.color}
              strokeWidth={3.5}
              strokeLinecap="round"
              pathLength={1}
              strokeDasharray={1}
              strokeDashoffset={1 - p}
              opacity={0.76}
            />
          );
        })}
      </svg>

      {FAMILIES.map((family, i) => (
        <CropCard key={family.key} family={family} index={i} />
      ))}

      <div
        style={{
          position: "absolute",
          left: MAP.x + 18,
          bottom: 21,
          fontSize: 16,
          color: COLORS.muted,
          opacity: interpolate(t, [tt.rollouts, tt.rollouts + 0.6], [0, 1], clamp),
        }}
      >
        map crop → sign-conditioned scene → closed-loop rollout
      </div>
    </Scene>
  );
};
