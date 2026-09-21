import { Video } from "@remotion/media";
import {
  AbsoluteFill,
  Easing,
  Interactive,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { C } from "./theme";

// Numbers from the current paper (Self_Driving-3.pdf): overall SCD, macro-averaged
// over 29 scenario types. PlanT-2 5.9% -> PlanT-2-FT 72.3% (+66.4 points).
// Clip: gif_eval/dual_T_1303406452_l_r_b5c03734_v0_s1930004957_plant2_default.gif (illustrative only).

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

export const Result: React.FC = () => {
  const frame = useCurrentFrame();
  const ft = interpolate(frame, [70, 120], [5.9, 72.3], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.3, 1) });

  return (
    <AbsoluteFill style={{ opacity: interpolate(frame, [0, 12, 198, 210], [0, 1, 1, 0], clamp) }}>
      <Video
        name="Simulator clip"
        src={staticFile("clips/result_turn.mp4")}
        muted
        style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1080 }}
      />

      <AbsoluteFill style={{ left: 1160, width: 680, top: 130 }}>
        <Interactive.Div
          name="Metric label"
          style={{
            opacity: interpolate(frame, [5, 25], [0, 1], { ...clamp, easing: ease }),
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: 3,
            color: C.blue,
            textTransform: "uppercase",
          }}
        >
          Sign compliance × Destination
        </Interactive.Div>

        <Interactive.Div
          name="Baseline"
          style={{
            opacity: interpolate(frame, [15, 35], [0, 1], { ...clamp, easing: ease }),
            marginTop: 40,
          }}
        >
          <div style={{ fontSize: 44, fontWeight: 500, color: C.muted }}>PlanT-2</div>
          <div style={{ fontSize: 120, fontWeight: 700, color: C.red, lineHeight: 1 }}>5.9%</div>
        </Interactive.Div>

        <Interactive.Div
          name="Arrow"
          style={{
            opacity: interpolate(frame, [45, 60], [0, 1], clamp),
            translate: interpolate(frame, [45, 65], ["0px -20px", "0px 0px"], { ...clamp, easing: ease }),
            fontSize: 72,
            color: C.muted,
            margin: "18px 0 10px 8px",
          }}
        >
          ↓
        </Interactive.Div>

        <Interactive.Div
          name="Fine-tuned"
          style={{ opacity: interpolate(frame, [60, 75], [0, 1], { ...clamp, easing: ease }) }}
        >
          <div style={{ fontSize: 44, fontWeight: 600 }}>PlanT-2-FT</div>
          <div
            style={{
              fontSize: 150,
              fontWeight: 700,
              color: C.green,
              lineHeight: 1,
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {ft.toFixed(1)}%
            <span style={{ fontSize: 48, marginLeft: 16, color: C.ink }}>SCD</span>
          </div>
        </Interactive.Div>

        <Interactive.Div
          name="Footnote"
          style={{
            opacity: interpolate(frame, [125, 145], [0, 1], clamp),
            marginTop: 48,
            fontSize: 26,
            color: C.muted,
            lineHeight: 1.4,
          }}
        >
          +66.4 points · overall SCD, macro-averaged
          <br />
          over 29 scenario types
        </Interactive.Div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
