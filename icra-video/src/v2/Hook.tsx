import { Video } from "@remotion/media";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, Card, clamp, G } from "./ui";

// Real clip: gifs/sumo_3.24_258301_v0_s4035757764_plant2_default.gif (20 km/h limit).
// Verifier counter 0 -> 1 at clip time ~5.5 s; at 1.25x playback that is frame ~132 here.
const VIOLATION_FRAME = 135;
const ease = Easing.bezier(0.16, 1, 0.3, 1);

const Check: React.FC<{ label: string; mark: string; color: string; note: string; from: number }> = ({
  label,
  mark,
  color,
  note,
  from,
}) => {
  const frame = useCurrentFrame();
  return (
    <div
      style={{
        opacity: interpolate(frame, [from, from + 14], [0, 1], { ...clamp, easing: ease }),
        translate: interpolate(frame, [from, from + 14], ["24px 0px", "0px 0px"], { ...clamp, easing: ease }),
        display: "flex",
        alignItems: "center",
        gap: 26,
        backgroundColor: C.panel,
        borderRadius: 16,
        padding: "20px 28px",
        marginBottom: 16,
      }}
    >
      <div
        style={{
          width: 64,
          height: 64,
          borderRadius: 32,
          backgroundColor: color,
          color: "white",
          fontSize: 38,
          fontWeight: 900,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {mark}
      </div>
      <div>
        <div style={{ fontSize: 40, fontWeight: 700 }}>{label}</div>
        <div style={{ fontSize: 22, color: C.muted }}>{note}</div>
      </div>
    </div>
  );
};

export const Hook: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      <Card
        bar={G.speed.bar}
        title="Speed"
        right={<span style={{ color: G.speed.text }}>verifier example: speed limit</span>}
        style={{
          left: 90,
          top: 50,
          width: 900,
          height: 980,
          opacity: interpolate(frame, [0, 15], [0, 1], clamp),
          translate: interpolate(frame, [0, 20], ["0px 30px", "0px 0px"], { ...clamp, easing: ease }),
        }}
      >
        <div style={{ margin: "0 20px", borderRadius: 12, overflow: "hidden", border: `1px solid ${C.border}` }}>
          <Video
            name="Simulator clip"
            src={staticFile("clips/hook_speed_3_24.mp4")}
            playbackRate={1.25}
            muted
            style={{ width: 856, height: 856, display: "block" }}
          />
        </div>
      </Card>

      <AbsoluteFill style={{ left: 1080, width: 760, top: 190 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 30 }}>
          <Img
            src={staticFile("signs/speed_limit_20.png")}
            style={{
              width: 150,
              height: 150,
              scale: interpolate(frame, [12, 30], [0.6, 1], { ...clamp, easing: Easing.spring({ damping: 14 }) }),
              opacity: interpolate(frame, [12, 20], [0, 1], clamp),
            }}
          />
          <div style={{ opacity: interpolate(frame, [20, 36], [0, 1], { ...clamp, easing: ease }) }}>
            <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: 2, color: G.speed.text }}>
              TRAFFICSIGNBENCH
            </div>
            <div style={{ fontSize: 76, fontWeight: 900, lineHeight: 1.02 }}>
              Speed limit
              <br />
              20 km/h
            </div>
          </div>
        </div>

        <div style={{ marginTop: 60 }}>
          <Check label="Destination" mark="—" color={C.baseline} note="placeholder" from={45} />
          <Check label="Collision-free" mark="—" color={C.baseline} note="placeholder" from={58} />
          <Check
            label="Rule compliant"
            mark="✕"
            color={C.red}
            note="verifier: speed above the posted limit"
            from={VIOLATION_FRAME}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
