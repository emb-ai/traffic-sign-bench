// Small shared presentation layer. Scientific content lives in src/config/.
import React from "react";
import { AbsoluteFill, Easing, Img, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { COLORS, SIZE } from "../config/style";
import { SCENE_FADE } from "../config/timing";

export const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
export const ease = Easing.bezier(0.16, 1, 0.3, 1);

/** Current time in seconds inside the enclosing Sequence. */
export const useT = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  return frame / fps;
};

/** 0→1 over [from, from+dur] seconds, eased. */
export const rise = (t: number, from: number, dur = 0.5) =>
  interpolate(t, [from, from + dur], [0, 1], { ...clamp, easing: ease });

/** Fade-in + small upward move. Wrap any block. */
export const Reveal: React.FC<{
  at: number;
  dur?: number;
  dy?: number;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ at, dur = 0.5, dy = 18, style, children }) => {
  const t = useT();
  const p = rise(t, at, dur);
  return (
    <div style={{ opacity: p, translate: `0px ${(1 - p) * dy}px`, ...style }}>{children}</div>
  );
};

/** Scene wrapper: white background, cross-fade at both ends. */
export const Scene: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames: d } = useVideoConfig();
  const f = SCENE_FADE * fps;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.bg,
        opacity: interpolate(frame, [0, f, d - f, d], [0, 1, 1, 0], clamp),
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

/** White card with a coloured top bar (paper Fig. 1 language). */
export const Card: React.FC<{
  bar: string;
  title?: string;
  right?: React.ReactNode;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ bar, title, right, style, children }) => (
  <div
    style={{
      position: "absolute",
      backgroundColor: COLORS.bg,
      border: `2px solid ${COLORS.border}`,
      borderRadius: SIZE.cardRadius,
      overflow: "hidden",
      boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
      ...style,
    }}
  >
    <div style={{ height: 12, backgroundColor: bar }} />
    {(title || right) && (
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "16px 24px 8px" }}>
        <div style={{ fontSize: 36, fontWeight: 700 }}>{title}</div>
        <div style={{ fontSize: 22, color: COLORS.muted, textAlign: "right" }}>{right}</div>
      </div>
    )}
    {children}
  </div>
);

/** A real simulator clip in a framed panel with a caption below. */
export const Clip: React.FC<{
  src: string;
  size: number;
  left: number;
  top: number;
  label?: React.ReactNode;
  trimBeforeSec?: number;
  loop?: boolean;
  labelColor?: string;
}> = ({ src, size, left, top, label, trimBeforeSec = 0, loop, labelColor }) => {
  const { fps } = useVideoConfig();
  return (
    <div style={{ position: "absolute", left, top, width: size }}>
      <div style={{ width: size, height: size, borderRadius: SIZE.panelRadius, overflow: "hidden", border: `2px solid ${COLORS.border}`, backgroundColor: "#fff" }}>
        {/* OffthreadVideo: reliable on NFS; @remotion/media Video was timing out on extract */}
        <OffthreadVideo
          src={staticFile(src)}
          muted
          loop={loop}
          trimBefore={Math.round(trimBeforeSec * fps)}
          style={{ width: size, height: size, display: "block", objectFit: "cover" }}
        />
      </div>
      {label && (
        <div style={{ marginTop: 10, fontSize: SIZE.small, color: labelColor ?? COLORS.muted, lineHeight: 1.3 }}>{label}</div>
      )}
    </div>
  );
};

/** Neutral placeholder for a missing scientific asset. */
export const Missing: React.FC<{ text: string; left: number; top: number; width: number; height: number }> = ({ text, left, top, width, height }) => (
  <div
    style={{
      position: "absolute",
      left,
      top,
      width,
      height,
      border: `3px dashed ${COLORS.faint}`,
      borderRadius: SIZE.panelRadius,
      backgroundColor: COLORS.panel,
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: 30,
      boxSizing: "border-box",
      textAlign: "center",
      color: COLORS.muted,
      fontSize: 24,
      lineHeight: 1.35,
    }}
  >
    [{text}]
  </div>
);

/** Icon image from public/ */
export const Icon: React.FC<{ src: string; size: number; style?: React.CSSProperties }> = ({ src, size, style }) => (
  <Img src={staticFile(src)} style={{ width: size, height: size, objectFit: "contain", ...style }} />
);

/** Big status pill: ✓ / ✕ / — */
export const Mark: React.FC<{ state: "ok" | "fail" | "unknown"; size?: number }> = ({ state, size = 56 }) => {
  const color = state === "ok" ? COLORS.green : state === "fail" ? COLORS.red : COLORS.faint;
  const glyph = state === "ok" ? "✓" : state === "fail" ? "✕" : "—";
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: size / 2,
        backgroundColor: color,
        color: "#fff",
        fontSize: size * 0.58,
        fontWeight: 900,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
      }}
    >
      {glyph}
    </div>
  );
};

/** Right-pointing arrow glyph used between pipeline stages. */
export const Arrow: React.FC<{ color?: string; size?: number; dir?: "right" | "down" }> = ({ color = COLORS.faint, size = 40, dir = "right" }) => (
  <div style={{ fontSize: size, color, lineHeight: 1, fontWeight: 400 }}>{dir === "right" ? "→" : "↓"}</div>
);

/** Animated count-up number. */
export const CountUp: React.FC<{ from: number; to: number; start: number; end: number; decimals?: number; suffix?: string; style?: React.CSSProperties }> = ({
  from,
  to,
  start,
  end,
  decimals = 0,
  suffix = "",
  style,
}) => {
  const t = useT();
  const v = interpolate(t, [start, end], [from, to], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.3, 1) });
  const txt = decimals ? v.toFixed(decimals) : Math.round(v).toLocaleString("en-US");
  return <span style={{ fontVariantNumeric: "tabular-nums", ...style }}>{txt}{suffix}</span>;
};

/** Horizontal bar that grows from 0 to value (0..100) px-scaled. */
export const Bar: React.FC<{ value: number; max?: number; width: number; height: number; color: string; at: number; dur?: number }> = ({ value, max = 100, width, height, color, at, dur = 0.8 }) => {
  const t = useT();
  const p = rise(t, at, dur);
  return <div style={{ width: (value / max) * width * p, height, backgroundColor: color, borderRadius: 6 }} />;
};

export const Headline: React.FC<{ children?: React.ReactNode; size?: number; color?: string; style?: React.CSSProperties }> = ({ children, size = SIZE.headline, color = COLORS.ink, style }) => (
  <div style={{ fontSize: size, fontWeight: 900, lineHeight: 1.08, color, ...style }}>{children}</div>
);

export const Sub: React.FC<{ children?: React.ReactNode; size?: number; style?: React.CSSProperties }> = ({ children, size = SIZE.subhead, style }) => (
  <div style={{ fontSize: size, fontWeight: 400, lineHeight: 1.3, color: COLORS.muted, ...style }}>{children}</div>
);

export const Footnote: React.FC<{ children?: React.ReactNode; top?: number }> = ({ children, top = 1020 }) => (
  <div style={{ position: "absolute", left: SIZE.margin, top, fontSize: 20, color: COLORS.faint }}>{children}</div>
);
