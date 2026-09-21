import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Img,
  Interactive,
  interpolate,
  Sequence,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { C } from "./theme";

// Step 1 is a placeholder (no real OSM image available locally yet).
// Steps 2-3 are real: first frame of gifs/sumo_4.2.1_78516_v0_s1701595836_plant2_default.gif,
// then the same GIF playing, so the still -> video hand-off is seamless.
const CROP_IN = 60;
const CLIP_FROM = 110;

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Step: React.FC<{ n: string; label: string; on: number; off: number }> = ({ n, label, on, off }) => {
  const frame = useCurrentFrame();
  const active = frame >= on && frame < off;
  return (
    <div
      style={{
        display: "flex",
        gap: 20,
        alignItems: "baseline",
        fontSize: 36,
        fontWeight: active ? 600 : 400,
        color: active ? C.ink : C.muted,
        opacity: interpolate(frame, [on - 20, on], [0.35, 1], clamp),
      }}
    >
      <span style={{ color: active ? C.blue : C.muted, width: 32 }}>{n}</span>
      {label}
    </div>
  );
};

export const MapPipeline: React.FC = () => {
  const frame = useCurrentFrame();
  const crops = Math.round(
    interpolate(frame, [125, 180], [0, 26020], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.3, 1) }),
  ).toLocaleString("en-US");

  return (
    <AbsoluteFill style={{ opacity: interpolate(frame, [0, 12, 228, 240], [0, 1, 1, 0], clamp) }}>
      {/* Left column: text */}
      <AbsoluteFill style={{ left: 120, width: 760, top: 150 }}>
        <Interactive.Div
          name="Headline"
          style={{ fontSize: 84, fontWeight: 700, lineHeight: 1.08 }}
        >
          Real road geometry
        </Interactive.Div>
        <Interactive.Div
          name="Headline 2"
          style={{
            opacity: interpolate(frame, [CLIP_FROM, CLIP_FROM + 18], [0, 1], { ...clamp, easing: ease }),
            fontSize: 84,
            fontWeight: 700,
            lineHeight: 1.08,
            color: C.blue,
          }}
        >
          → executable rule test
        </Interactive.Div>

        <div style={{ marginTop: 70, display: "flex", flexDirection: "column", gap: 22 }}>
          <Step n="1" label="Map region" on={0} off={CROP_IN} />
          <Step n="2" label="Real-map crop" on={CROP_IN} off={CLIP_FROM} />
          <Step n="3" label="Closed-loop scenario" on={CLIP_FROM} off={9999} />
        </div>

        <Interactive.Div
          name="Crop counter"
          style={{
            opacity: interpolate(frame, [120, 135], [0, 1], clamp),
            marginTop: 80,
            display: "flex",
            alignItems: "baseline",
            gap: 20,
          }}
        >
          <span style={{ fontSize: 72, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>{crops}</span>
          <span style={{ fontSize: 36, color: C.muted }}>real-map crops</span>
        </Interactive.Div>
      </AbsoluteFill>

      {/* Right: image stage 880x880 */}
      <AbsoluteFill
        style={{
          left: 940,
          top: 100,
          width: 880,
          height: 880,
          overflow: "hidden",
          scale: 0.711,
          translate: "-19px 32px",
          rotate: "0.2deg"
        }}
      >
        {/* Step 1 placeholder */}
        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [CROP_IN, CROP_IN + 12], [1, 0], clamp),
            backgroundColor: "#EFEFEA",
            border: `3px dashed ${C.line}`,
            justifyContent: "center",
            alignItems: "center",
            color: C.muted,
            fontSize: 30,
            textAlign: "center",
          }}
        >
          OpenStreetMap region
          <br />
          <span style={{ fontSize: 24 }}>[placeholder — real map to be added]</span>
        </AbsoluteFill>
        <div
          style={{
            position: "absolute",
            left: 308,
            top: 308,
            width: 264,
            height: 264,
            border: `5px solid ${C.blue}`,
            opacity: interpolate(frame, [15, 30, CROP_IN + 10, CROP_IN + 30], [0, 1, 1, 0], clamp),
            scale: interpolate(frame, [15, 30], [1.15, 1], { ...clamp, easing: ease }),
          }}
        />

        {/* Step 2: real crop zooms out of the highlight rectangle */}
        <Img
          name="Real-map crop"
          src={staticFile("map_crop_4_2_1.png")}
          style={{
            position: "absolute",
            width: 880,
            height: 880,
            opacity: interpolate(frame, [CROP_IN, CROP_IN + 12], [0, 1], clamp),
            scale: interpolate(frame, [CROP_IN, CROP_IN + 45], [0.3, 1], {
              ...clamp,
              easing: ease,
              output: "perceptual-scale",
            }),
          }}
        />

        {/* Step 3: the same scenario running */}
        <Sequence from={CLIP_FROM} premountFor={30}>
          <Video
            name="Scenario clip"
            src={staticFile("clips/map_scenario_4_2_1.mp4")}
            muted
            style={{ position: "absolute", width: 880, height: 880 }}
          />
        </Sequence>
        <div style={{ position: "absolute", inset: 0, border: `2px solid ${C.line}` }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
