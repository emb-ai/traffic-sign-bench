import { Video } from "@remotion/media";
import { AbsoluteFill, Easing, Img, interpolate, Sequence, staticFile, useCurrentFrame } from "remotion";
import { C, Card, clamp, G } from "./ui";

// Paper, Sec. III-C: sign-free fragments from real Moscow maps (OpenStreetMap),
// 26,020 crops = 6,457 junctions + 6,507 dual-path + 13,056 corridors;
// 29 scenario types, 23,200 train / 5,800 test.
// Visual: first frame of gifs/sumo_4.2.1_78516_v0_s1701595836_plant2_default.gif, then the clip.
const CLIP_FROM = 70;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

const FAMILIES = [
  { label: "Junctions", n: 6457, use: "priority", color: G.priority.bar },
  { label: "Dual-path", n: 6507, use: "routing", color: G.routing.bar },
  { label: "Corridors", n: 13056, use: "speed · obstacles · crosswalk", color: G.obstacles.bar },
];
const TOTAL = 26020;
const BAR_W = 760;

export const MapPipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const count = Math.round(
    interpolate(frame, [20, 80], [0, TOTAL], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.3, 1) }),
  ).toLocaleString("en-US");

  let acc = 0;
  return (
    <AbsoluteFill>
      <Card
        bar={G.routing.bar}
        title={frame < CLIP_FROM ? "Real-map crop" : "Closed-loop scenario"}
        right={<span style={{ color: C.muted }}>OpenStreetMap · Moscow</span>}
        style={{
          left: 90,
          top: 50,
          width: 900,
          height: 980,
          opacity: interpolate(frame, [0, 15], [0, 1], clamp),
        }}
      >
        <div
          style={{
            position: "relative",
            margin: "0 20px",
            width: 856,
            height: 856,
            borderRadius: 12,
            overflow: "hidden",
            border: `1px solid ${C.border}`,
          }}
        >
          <Img
            src={staticFile("map_crop_4_2_1.png")}
            style={{
              position: "absolute",
              width: 856,
              height: 856,
              scale: interpolate(frame, [0, CLIP_FROM], [1.35, 1], { ...clamp, easing: ease }),
            }}
          />
          <Sequence from={CLIP_FROM} premountFor={30}>
            <Video
              name="Scenario clip"
              src={staticFile("clips/map_scenario_4_2_1.mp4")}
              muted
              style={{ position: "absolute", width: 856, height: 856 }}
            />
          </Sequence>
        </div>
      </Card>

      <AbsoluteFill style={{ left: 1070, width: 780, top: 110 }}>
        <div style={{ fontSize: 30, fontWeight: 700, color: C.muted }}>Real road geometry</div>
        <div style={{ fontSize: 30, fontWeight: 700, color: G.routing.text }}>→ executable rule test</div>

        <div style={{ marginTop: 40, fontSize: 130, fontWeight: 900, lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
          {count}
        </div>
        <div style={{ fontSize: 36, color: C.muted }}>real-world map crops</div>

        {/* Stacked bar of the three structural families */}
        <div style={{ position: "relative", marginTop: 50, width: BAR_W, height: 56, backgroundColor: C.panel, borderRadius: 10, overflow: "hidden" }}>
          {FAMILIES.map((f, i) => {
            const x = (acc / TOTAL) * BAR_W;
            const w = (f.n / TOTAL) * BAR_W;
            acc += f.n;
            const t = 60 + i * 18;
            return (
              <div
                key={f.label}
                style={{
                  position: "absolute",
                  left: x,
                  top: 0,
                  height: 56,
                  width: w * interpolate(frame, [t, t + 20], [0, 1], { ...clamp, easing: ease }),
                  backgroundColor: f.color,
                  borderRight: "3px solid white",
                }}
              />
            );
          })}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 14, marginTop: 26 }}>
          {FAMILIES.map((f, i) => (
            <div
              key={f.label}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 16,
                fontSize: 30,
                opacity: interpolate(frame, [66 + i * 18, 80 + i * 18], [0, 1], clamp),
              }}
            >
              <div style={{ width: 22, height: 22, borderRadius: 11, backgroundColor: f.color }} />
              <b style={{ width: 170 }}>{f.label}</b>
              <span style={{ width: 130, fontVariantNumeric: "tabular-nums" }}>{f.n.toLocaleString("en-US")}</span>
              <span style={{ color: C.muted, fontSize: 24 }}>{f.use}</span>
            </div>
          ))}
        </div>

        <div
          style={{
            marginTop: 50,
            fontSize: 30,
            color: C.muted,
            opacity: interpolate(frame, [140, 155], [0, 1], clamp),
          }}
        >
          <b style={{ color: C.ink }}>29 scenario types</b> · 23,200 train / 5,800 test
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
