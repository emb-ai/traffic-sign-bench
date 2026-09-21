import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { C, clamp, G } from "./ui";

// Table II of the current paper: group SCD (%) and overall SCD.
const ROWS = [
  { key: "priority", label: "Priority", base: 5.8, ft: 57.2 },
  { key: "speed", label: "Speed", base: 29.8, ft: 96.2 },
  { key: "obstacles", label: "Obstacles", base: 0.7, ft: 90.8 },
  { key: "routing", label: "Routing", base: 1.1, ft: 58.4 },
] as const;

const BAR_MAX = 760; // px for 100 %
const ease = Easing.bezier(0.16, 1, 0.3, 1);

export const Result: React.FC = () => {
  const frame = useCurrentFrame();
  const overall = interpolate(frame, [120, 175], [5.9, 72.3], { ...clamp, easing: Easing.bezier(0.2, 0.8, 0.3, 1) });

  return (
    <AbsoluteFill>
      <div style={{ position: "absolute", left: 90, top: 70, opacity: interpolate(frame, [0, 15], [0, 1], clamp) }}>
        <div style={{ fontSize: 64, fontWeight: 900 }}>Sign Compliance × Destination</div>
        <div style={{ fontSize: 30, color: C.muted, marginTop: 6 }}>Group SCD (%), closed-loop evaluation on all 29 scenario types</div>
      </div>

      {/* Legend */}
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 230,
          display: "flex",
          gap: 40,
          fontSize: 28,
          opacity: interpolate(frame, [10, 25], [0, 1], clamp),
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ width: 36, height: 20, borderRadius: 4, backgroundColor: C.baseline }} /> PlanT-2
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ width: 36, height: 20, borderRadius: 4, background: G.speed.bar }} />
          <b>PlanT-2-FT</b> (group colour)
        </span>
      </div>

      {/* Grouped bars */}
      <div style={{ position: "absolute", left: 90, top: 310 }}>
        {ROWS.map((r, i) => {
          const col = G[r.key];
          const tb = 20 + i * 6;
          const tf = 60 + i * 12;
          const wb = interpolate(frame, [tb, tb + 20], [0, r.base], { ...clamp, easing: ease });
          const wf = interpolate(frame, [tf, tf + 30], [0, r.ft], { ...clamp, easing: ease });
          return (
            <div key={r.key} style={{ display: "flex", alignItems: "center", marginBottom: 34 }}>
              <div style={{ width: 230, fontSize: 36, fontWeight: 700, color: col.text }}>{r.label}</div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 14, height: 44 }}>
                  <div style={{ width: (wb / 100) * BAR_MAX, height: 34, backgroundColor: C.baseline, borderRadius: 6 }} />
                  <span style={{ fontSize: 26, color: C.muted, fontVariantNumeric: "tabular-nums" }}>{wb.toFixed(1)}</span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 14, height: 56 }}>
                  <div style={{ width: (wf / 100) * BAR_MAX, height: 46, backgroundColor: col.bar, borderRadius: 6 }} />
                  <span
                    style={{
                      fontSize: 34,
                      fontWeight: 900,
                      fontVariantNumeric: "tabular-nums",
                      opacity: interpolate(frame, [tf, tf + 5], [0, 1], clamp),
                    }}
                  >
                    {wf.toFixed(1)}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall */}
      <div
        style={{
          position: "absolute",
          left: 1250,
          top: 300,
          width: 600,
          height: 680,
          backgroundColor: C.panel,
          borderRadius: 18,
          padding: "40px 48px",
          boxSizing: "border-box",
          opacity: interpolate(frame, [105, 120], [0, 1], clamp),
          translate: interpolate(frame, [105, 125], ["30px 0px", "0px 0px"], { ...clamp, easing: ease }),
        }}
      >
        <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: 2, color: C.muted }}>OVERALL SCD</div>
        <div style={{ marginTop: 30, fontSize: 36, color: C.muted }}>PlanT-2</div>
        <div style={{ fontSize: 100, fontWeight: 900, color: C.red, lineHeight: 1 }}>5.9%</div>
        <div style={{ fontSize: 60, color: C.muted, margin: "10px 0" }}>↓</div>
        <div style={{ fontSize: 36, fontWeight: 700 }}>PlanT-2-FT</div>
        <div style={{ fontSize: 150, fontWeight: 900, color: "#2E8B57", lineHeight: 1, fontVariantNumeric: "tabular-nums" }}>
          {overall.toFixed(1)}%
        </div>
        <div style={{ marginTop: 18, fontSize: 28, color: C.muted, opacity: interpolate(frame, [180, 195], [0, 1], clamp) }}>
          +66.4 points, macro-averaged over 29 scenario types
        </div>
      </div>
    </AbsoluteFill>
  );
};
