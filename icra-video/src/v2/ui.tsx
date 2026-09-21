import { loadFont } from "@remotion/google-fonts/Lato";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";

// Paper style (Fig. 1 of Self_Driving-3.pdf): Lato-like sans, white cards with a
// coloured top bar, light-grey inner panels. Group colours sampled from Fig. 1.
export const { fontFamily } = loadFont("normal", {
  weights: ["400", "700", "900"],
  subsets: ["latin"],
});

export const G = {
  priority: { bar: "#90CAF9", text: "#3C8DD8" },
  speed: { bar: "#E76F51", text: "#E05A3A" },
  obstacles: { bar: "#A1CB35", text: "#7EA72A" },
  routing: { bar: "#FCAD38", text: "#E8961F" },
};

export const C = {
  bg: "#FFFFFF",
  ink: "#1A1A1A",
  muted: "#7A7A7A",
  border: "#E2E2E2",
  panel: "#F4F4F4",
  red: "#D64533",
  baseline: "#BDBDBD",
};

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

// Scene-level fade in/out
export const Fade: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { durationInFrames: d } = useVideoConfig();
  return (
    <AbsoluteFill style={{ opacity: interpolate(frame, [0, 10, d - 10, d], [0, 1, 1, 0], clamp) }}>
      {children}
    </AbsoluteFill>
  );
};

// White card with a coloured top bar, as in the paper's taxonomy figure
export const Card: React.FC<{
  bar: string;
  title: string;
  right?: React.ReactNode;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ bar, title, right, style, children }) => (
  <div
    style={{
      position: "absolute",
      backgroundColor: C.bg,
      border: `2px solid ${C.border}`,
      borderRadius: 18,
      overflow: "hidden",
      boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
      ...style,
    }}
  >
    <div style={{ height: 12, backgroundColor: bar }} />
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "flex-start",
        padding: "18px 26px 10px",
      }}
    >
      <div style={{ fontSize: 40, fontWeight: 700 }}>{title}</div>
      <div style={{ textAlign: "right", fontSize: 22, lineHeight: 1.25 }}>{right}</div>
    </div>
    {children}
  </div>
);
