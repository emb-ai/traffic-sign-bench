import { AbsoluteFill, Easing, OffthreadVideo, interpolate, staticFile } from "remotion";
import { COLORS } from "../config/style";
import { T } from "../config/timing";
import { Headline, Icon, Reveal, Scene, Sub, clamp, useT } from "../lib/ui";

const METRICS = [
  { label: "Driving Score", value: "100.00", note: "route completion × penalty", tone: "good" },
  { label: "Comfort", value: "88.0%", note: "smooth-frame ratio", tone: "good" },
  { label: "Efficiency", value: "295.3", note: "mean speed ratio", tone: "good" },
  { label: "Collision Rate", value: "0%", note: "no collision", tone: "good" },
] as const;

export const S01_Hook: React.FC = () => {
  const t = useT();
  const tt = T.s01;
  const violation = interpolate(t, [tt.ruleFail, tt.ruleFail + 0.45], [0, 1], {
    ...clamp,
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <Scene>
      {/* Video box */}
      <div
        style={{
          position: "absolute",
          left: 70,
          top: 64,
          width: 820,
          height: 820,
          overflow: "hidden",
          borderRadius: 24,
          border: violation > 0.05 ? `3px solid ${COLORS.red}` : `2px solid ${COLORS.border}`,
          boxShadow:
            violation > 0.05
              ? `0 18px 50px rgba(214,69,51,${0.25 * violation})`
              : "0 18px 50px rgba(0,0,0,0.10)",
          transition: "border 0.2s ease, box-shadow 0.2s ease",
        }}
      >
        <OffthreadVideo
          src={staticFile("converted/problem_crosswalk.mp4")}
          muted
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
        {violation > 0.05 && (
          <div
            style={{
              position: "absolute",
              top: 18,
              right: 18,
              background: "rgba(214,69,51,0.95)",
              color: "#fff",
              padding: "7px 16px",
              borderRadius: 10,
              fontWeight: 900,
              fontSize: 17,
              letterSpacing: 0.8,
              opacity: violation,
              boxShadow: "0 6px 16px rgba(0,0,0,0.3)",
              display: "flex",
              alignItems: "center",
              gap: 8,
            }}
          >
            <span
              style={{
                display: "inline-block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#fff",
              }}
            />
            PAUSED AT STEP 50 • VIOLATION
          </div>
        )}
      </div>

      <Reveal
        at={0.35}
        style={{
          position: "absolute",
          left: 70,
          top: 902,
          width: 820,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
        }}
      >
        <div style={{ fontSize: 27, fontWeight: 900, color: COLORS.ink }}>PlanT-2</div>
        <div style={{ fontSize: 21, fontWeight: 700, color: COLORS.muted }}>state-of-the-art planner</div>
      </Reveal>

      {/* Right Column */}
      <div style={{ position: "absolute", left: 930, top: 56, right: 70 }}>
        {/* Main headline moved higher */}
        <Reveal at={tt.headline}>
          <Headline size={62}>High metrics can hide an illegal behaviour</Headline>
        </Reveal>

        {/* Crosswalk example badge with icon */}
        <Reveal at={tt.example} style={{ marginTop: 48 }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: 30,
              padding: "8px 18px 8px 12px",
              borderRadius: 14,
              background: "#EEF4FC",
              border: "1.5px solid #C8DCF5",
            }}
          >
            <Icon src="signs/crosswalk.png" size={44} />
            <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
              <span
                style={{
                  color: COLORS.blue,
                  fontSize: 16,
                  fontWeight: 900,
                  letterSpacing: 1.2,
                  textTransform: "uppercase",
                }}
              >
                Example:
              </span>
              <span style={{ color: COLORS.ink, fontSize: 22, fontWeight: 700 }}>
                Pedestrian crossing compliance
              </span>
            </div>
          </div>
        </Reveal>

        {/* Metrics mid first-pass — shortly after the example badge */}
        <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          {METRICS.map((metric, index) => (
            <Reveal
              key={metric.label}
              at={tt.checks + index * 0.12}
              dy={14}
              style={{
                minHeight: 108,
                padding: "16px 20px",
                borderRadius: 16,
                background: metric.tone === "good" ? "#F2F8F4" : "#FFF8EA",
                border: `2px solid ${metric.tone === "good" ? "#CDE5D6" : "#EAD8A9"}`,
                boxSizing: "border-box",
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", gap: 14 }}>
                <span style={{ color: COLORS.muted, fontSize: 21, fontWeight: 700 }}>{metric.label}</span>
                <span
                  style={{
                    color: metric.tone === "good" ? COLORS.green : "#B47A16",
                    fontSize: 34,
                    fontWeight: 900,
                    fontVariantNumeric: "tabular-nums",
                  }}
                >
                  {metric.value}
                </span>
              </div>
              <div style={{ color: COLORS.muted, fontSize: 17, marginTop: 6 }}>{metric.note}</div>
            </Reveal>
          ))}
        </div>

        {/* Red violation banner appears when 2nd run stops at step 50 */}
        <div
          style={{
            marginTop: 18,
            opacity: violation,
            transform: `scale(${0.96 + 0.04 * violation}) translateY(${(1 - violation) * 8}px)`,
            transformOrigin: "center",
            borderRadius: 18,
            padding: "18px 22px",
            background: "#FFF1EF",
            border: `3px solid ${COLORS.red}`,
            display: "flex",
            alignItems: "center",
            gap: 25,
            boxShadow: `0 8px 28px rgba(214,69,51,${0.22 * violation})`,
          }}
        >
          <div
            style={{
              width: 54,
              height: 54,
              borderRadius: 27,
              background: COLORS.red,
              color: "#fff",
              display: "grid",
              placeItems: "center",
              fontSize: 34,
              fontWeight: 900,
              flexShrink: 0,
            }}
          >
            ✕
          </div>
          <div>
            <div style={{ color: COLORS.red, fontSize: 28, fontWeight: 900, display: "flex", alignItems: "center", gap: 12 }}>
              <span>Traffic-rule compliance: FAILED</span>
              <span
                style={{
                  fontSize: 15,
                  fontWeight: 800,
                  background: COLORS.red,
                  color: "#fff",
                  padding: "3px 10px",
                  borderRadius: 8,
                  letterSpacing: 0.5,
                }}
              >
                STEP 50
              </span>
            </div>
            <div style={{ color: COLORS.ink, fontSize: 20, marginTop: 4, fontWeight: 600 }}>
              Ego vehicle does not yield to pedestrian on the crosswalk.
            </div>
          </div>
        </div>
      </div>

      {/* The evaluation gap */}
      <Reveal
        at={tt.mainText}
        style={{
          position: "absolute",
          left: 930,
          right: 70,
          top: 760,
          paddingLeft: 24,
          borderLeft: `7px solid ${COLORS.blue}`,
        }}
      >
        <div style={{ color: COLORS.blue, fontSize: 20, fontWeight: 900, letterSpacing: 2.0, textTransform: "uppercase" }}>
          The evaluation gap
        </div>
        <Sub size={29} style={{ marginTop: 8, color: COLORS.ink, fontWeight: 700 }}>
          Existing simulation benchmarks do not make traffic-rule compliance systematic, scalable, and directly verifiable.
        </Sub>
      </Reveal>

      {/* Red screen boundary flash upon violation */}
      <AbsoluteFill
        style={{
          pointerEvents: "none",
          boxShadow: `inset 0 0 0 ${Math.round(8 * violation)}px rgba(214,69,51,${0.2 * violation})`,
        }}
      />
    </Scene>
  );
};
