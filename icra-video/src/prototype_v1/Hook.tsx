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

// Real clip: gifs/sumo_3.24_258301_v0_s4035757764_plant2_default.gif (sign 3.24, 20 km/h).
// On-screen verifier counter goes 0 -> 1 at clip time ~5.5 s and ends at 2.
// Played at 1.25x, so the first violation lands at ~4.4 s (frame ~132) of this scene.
const VIOLATION_FRAME = 135;

const ease = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

const Row: React.FC<{
  label: string;
  mark: string;
  color: string;
  note: string;
  from: number;
}> = ({ label, mark, color, note, from }) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [from, from + 15], [0, 1], { ...clamp, easing: ease }),
        translate: interpolate(frame, [from, from + 15], ["0px 16px", "0px 0px"], { ...clamp, easing: ease }),
        display: "flex",
        alignItems: "baseline",
        justifyContent: "space-between",
        borderTop: `2px solid ${C.line}`,
        padding: "22px 0",
      }}
    >
      <div>
        <div style={{ fontSize: 46, fontWeight: 500 }}>{label}</div>
        <div style={{ fontSize: 24, color: C.muted, marginTop: 6 }}>{note}</div>
      </div>
      <div style={{ fontSize: 64, fontWeight: 700, color }}>{mark}</div>
    </div>
  );
};

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        opacity: interpolate(frame, [0, 12, 213, 225], [0, 1, 1, 0], clamp),
      }}
    >
      <Video
        name="Simulator clip"
        src={staticFile("clips/hook_speed_3_24.mp4")}
        playbackRate={1.25}
        muted
        style={{ position: "absolute", left: 0, top: 0, width: 1080, height: 1080 }}
      />

    </AbsoluteFill>
  );
};
