import { Img, interpolate, staticFile } from "remotion";
import { COLORS, GROUP } from "../config/style";
import { Headline, Scene, clamp, useT } from "../lib/ui";

type ConventionKey =
  | "warning"
  | "priority"
  | "prohibitory"
  | "mandatory"
  | "special"
  | "information"
  | "direction"
  | "panels";
type SemanticKey = keyof typeof GROUP;

type SignItem = {
  id: string;
  src: string;
  convention: ConventionKey;
  semantic?: SemanticKey;
};

const CATEGORIES: { key: ConventionKey; label: string; code: string; accent: string }[] = [
  { key: "warning", label: "Warning", code: "Class A", accent: "#F59E0B" },
  { key: "priority", label: "Priority", code: "Class B", accent: "#3B82F6" },
  { key: "prohibitory", label: "Prohibitory", code: "Class C", accent: "#EF4444" },
  { key: "mandatory", label: "Mandatory", code: "Class D", accent: "#2563EB" },
  { key: "special", label: "Special regulation", code: "Class E", accent: "#6366F1" },
  { key: "information", label: "Information", code: "Class F", accent: "#0D9488" },
  { key: "direction", label: "Direction", code: "Class G", accent: "#64748B" },
  { key: "panels", label: "Additional panels", code: "Class H", accent: "#94A3B8" },
];
const MAX_INITIAL_SIGNS = 6;

const implemented = (
  semantic: SemanticKey,
  convention: ConventionKey,
  names: string[],
): SignItem[] =>
  names.map((name) => ({
    id: name,
    src: `signs/${name}.${name.includes("residential_zone") ? "jpg" : "png"}`,
    convention,
    semantic,
  }));

const SIGNS: SignItem[] = [
  ...implemented("priority", "priority", ["main_road", "secondary_road", "secondary_road_left", "secondary_road_right", "yield", "stop"]),
  ...implemented("priority", "special", ["crosswalk"]),
  ...implemented("priority", "mandatory", ["roundabout"]),
  ...implemented("speed", "prohibitory", ["speed_limit_40", "end_speed_limit_40"]),
  ...implemented("speed", "special", ["zone_speed_40", "end_zone_speed_40", "residential_zone", "end_residential_zone"]),
  ...implemented("speed", "mandatory", ["min_speed"]),
  ...implemented("obstacles", "mandatory", ["detour_right", "detour_left", "detour_either", "bike_lane"]),
  ...implemented("obstacles", "prohibitory", ["no_traffic"]),
  ...implemented("obstacles", "special", ["bus_lane_road", "bike_lane_road", "bus_lane"]),
  ...implemented("routing", "mandatory", [
    "direction_straight",
    "direction_right",
    "direction_left",
    "direction_straight_right",
    "direction_straight_left",
    "direction_left_right",
  ]),
  ...implemented("routing", "prohibitory", ["no_right_turn", "no_left_turn", "no_entry"]),
  ...implemented("routing", "special", ["one_way_right", "one_way_left"]),
  { id: "warning-1.12.2", src: "taxonomy/extra/1.12.2.jpg", convention: "warning" },
  { id: "warning-1.15", src: "taxonomy/extra/1.15.jpg", convention: "warning" },
  { id: "warning-1.19", src: "taxonomy/extra/1.19.jpg", convention: "warning" },
  { id: "warning-1.29", src: "taxonomy/extra/1.29.jpg", convention: "warning" },
  { id: "warning-1.30", src: "taxonomy/extra/1.30.jpg", convention: "warning" },
  { id: "warning-1.32", src: "taxonomy/extra/1.32.jpg", convention: "warning" },
  { id: "warning-1.33", src: "taxonomy/extra/1.33.jpg", convention: "warning" },
  { id: "special-5.23.1", src: "taxonomy/extra/5.23.1.png", convention: "special" },
  { id: "information-7.1", src: "taxonomy/extra/7.1_0.jpg", convention: "information" },
  { id: "information-7.5", src: "taxonomy/extra/7.5.jpg", convention: "information" },
  { id: "information-7.7", src: "taxonomy/extra/7.7.jpg", convention: "information" },
  { id: "information-7.8", src: "taxonomy/extra/7.8.jpg", convention: "information" },
  { id: "information-7.9", src: "taxonomy/extra/7.9.jpg", convention: "information" },
  { id: "information-7.10", src: "taxonomy/extra/7.10.jpg", convention: "information" },
  { id: "direction-6.6", src: "taxonomy/extra/6.6.jpg", convention: "direction" },
  { id: "direction-6.7", src: "taxonomy/extra/6.7.jpg", convention: "direction" },
  { id: "direction-6.13", src: "taxonomy/extra/6.13.jpg", convention: "direction" },
  { id: "direction-6.14.2", src: "taxonomy/extra/6.14.2.jpg", convention: "direction" },
  { id: "direction-6.15.1", src: "taxonomy/extra/6.15.1.jpg", convention: "direction" },
  { id: "direction-6.22", src: "taxonomy/extra/6.22.jpg", convention: "direction" },
  { id: "panel-8.1.3", src: "taxonomy/extra/8.1.3.jpg", convention: "panels" },
  { id: "panel-8.11", src: "taxonomy/extra/8.11.jpg", convention: "panels" },
  { id: "panel-8.16", src: "taxonomy/extra/8.16.jpg", convention: "panels" },
  { id: "panel-8.24", src: "taxonomy/extra/8.24.jpg", convention: "panels" },
  { id: "panel-8.4.1", src: "taxonomy/extra/8.4.1.jpg", convention: "panels" },
  { id: "panel-8.6.1", src: "taxonomy/extra/8.6.1.jpg", convention: "panels" },
];

const conventionPosition = (sign: SignItem) => {
  const categoryIndex = CATEGORIES.findIndex((category) => category.key === sign.convention);
  const categorySigns = SIGNS.filter((candidate) => candidate.convention === sign.convention);
  const index = categorySigns.findIndex((candidate) => candidate.id === sign.id);
  return {
    x: 44 + categoryIndex * 227 + 28 + (index % 2) * 88,
    y: 426 + Math.floor(index / 2) * 94,
  };
};

const semanticPosition = (sign: SignItem) => {
  if (!sign.semantic) return conventionPosition(sign);
  const groups = Object.keys(GROUP) as SemanticKey[];
  const groupIndex = groups.indexOf(sign.semantic);
  const groupSigns = SIGNS.filter((candidate) => candidate.semantic === sign.semantic);
  const index = groupSigns.findIndex((candidate) => candidate.id === sign.id);
  return {
    x: 70 + groupIndex * 455 + 44 + (index % 4) * 84,
    y: 500 + Math.floor(index / 4) * 94,
  };
};

const GROUP_DETAILS: Record<SemanticKey, { scenarios: number; capability: string }> = {
  priority: { scenarios: 6, capability: "right-of-way reasoning" },
  speed: { scenarios: 4, capability: "longitudinal control" },
  obstacles: { scenarios: 8, capability: "safe obstacle handling" },
  routing: { scenarios: 11, capability: "rule-aware route choice" },
};

const semanticGroups = (Object.keys(GROUP) as SemanticKey[]).map((key) => {
  const details = GROUP_DETAILS[key];
  return {
    key,
    signs: SIGNS.filter((sign) => sign.semantic === key).length,
    ...details,
  };
});

export const S02B_Taxonomy: React.FC = () => {
  const t = useT();
  const filterPhase = interpolate(t, [4.2, 5.2], [0, 1], clamp);
  const selectionPhase = interpolate(t, [7.7, 8.7], [0, 1], clamp);
  const regroupPhase = interpolate(t, [10.0, 13.2], [0, 1], clamp);
  const initialLabels = interpolate(t, [9.8, 11.0], [1, 0], clamp);
  const groupCards = interpolate(t, [10.2, 11.5], [0, 1], clamp);

  return (
    <Scene>
      <div style={{ position: "absolute", left: 70, right: 70, top: 40, textAlign: "left" }}>
        <div style={{ opacity: 1 - regroupPhase }}>
          <div
            style={{
              display: "inline-block",
              padding: "4px 14px",
              borderRadius: 999,
              background: "#EEF4FC",
              border: "1.5px solid #C8DCF5",
              color: COLORS.blue,
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: 2.2,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Vienna Convention Taxonomy
          </div>
          <Headline size={50}>Generalizability of TrafficSignBench</Headline>
          <div style={{ marginTop: 6, color: COLORS.muted, fontSize: 23, fontWeight: 700 }}>
            Comprehensive coverage across all 8 international functional classes
          </div>
        </div>
        <div style={{ position: "absolute", inset: 0, opacity: regroupPhase }}>
          <div
            style={{
              display: "inline-block",
              padding: "4px 14px",
              borderRadius: 999,
              background: "#EAF7EF",
              border: "1.5px solid #B4E2C5",
              color: COLORS.green,
              fontSize: 13,
              fontWeight: 900,
              letterSpacing: 2.2,
              textTransform: "uppercase",
              marginBottom: 8,
            }}
          >
            Closed-Loop Scenario Formulation
          </div>
          <Headline size={50}>34 Implemented Signs → 4 Semantic Groups</Headline>
          <div style={{ marginTop: 6, color: COLORS.muted, fontSize: 23, fontWeight: 700 }}>
            Reorganize into 4 semantic groups based on the high-level capability demanded of the ego vehicle
          </div>
        </div>
      </div>

      {CATEGORIES.map((category, index) => (
        <div
          key={category.key}
          style={{
            position: "absolute",
            left: 44 + index * 227,
            top: 338,
            width: 212,
            height: 430,
            borderRadius: 18,
            background: "#FFFFFF",
            border: "1.5px solid #E2E8F0",
            boxShadow: "0 8px 24px rgba(15, 23, 42, 0.04)",
            opacity: initialLabels,
            overflow: "hidden",
          }}
        >
          {/* Top color accent */}
          <div style={{ height: 6, background: category.accent }} />

          {/* Header section with Class code and Label */}
          <div style={{ paddingTop: 10, paddingBottom: 6, textAlign: "center", borderBottom: "1px solid #F1F5F9" }}>
            <div style={{ color: category.accent, fontSize: 11, fontWeight: 900, letterSpacing: 1.5, textTransform: "uppercase" }}>
              {category.code}
            </div>
            <div
              style={{
                color: COLORS.ink,
                fontSize: category.key === "special" || category.key === "panels" ? 15 : 17,
                fontWeight: 900,
                marginTop: 2,
                lineHeight: 1.15,
                height: 28,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: "0 6px",
              }}
            >
              {category.label}
            </div>
          </div>

          {/* Ellipsis indicator for EVERY category (demonstrates sample of broad convention) */}
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              bottom: 18,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              gap: 5,
            }}
          >
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8" }} />
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8" }} />
            <span style={{ width: 6, height: 6, borderRadius: "50%", background: "#94A3B8" }} />
          </div>
        </div>
      ))}

      {semanticGroups.map(({ key, signs, scenarios, capability }, index) => {
        const color = GROUP[key];
        return (
          <div
            key={key}
            style={{
              position: "absolute",
              left: 70 + index * 455,
              top: 338,
              width: 410,
              height: 440,
              borderRadius: 22,
              background: "#FFFFFF",
              border: `2px solid ${COLORS.border}`,
              boxShadow: "0 12px 36px rgba(15, 23, 42, 0.08)",
              opacity: groupCards,
              transform: `translateY(${(1 - groupCards) * 26}px)`,
              overflow: "hidden",
            }}
          >
            <div style={{ height: 10, background: color.bar }} />
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", padding: "18px 24px 14px" }}>
              <div>
                <span style={{ fontSize: 34, fontWeight: 900, color: COLORS.ink }}>{color.label}</span>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ color: color.text, fontSize: 20, fontWeight: 900 }}>{signs} signs</div>
                <div style={{ color: COLORS.muted, fontSize: 14, fontWeight: 700 }}>{scenarios} testing scenarios</div>
              </div>
            </div>
            {/* Capability pill placed directly ABOVE the content (sign icons) */}
            <div
              style={{
                margin: "0 22px",
                padding: "8px 14px",
                borderRadius: 12,
                background: "#F8FAFC",
                border: "1px solid #E2E8F0",
                color: COLORS.muted,
                fontSize: 16,
                fontWeight: 700,
                textAlign: "center",
              }}
            >
              demands <span style={{ color: COLORS.ink, fontWeight: 900 }}>{capability}</span>
            </div>
          </div>
        );
      })}

      {SIGNS.map((sign, index) => {
        const from = conventionPosition(sign);
        const to = semanticPosition(sign);
        const selected = Boolean(sign.semantic);
        const categorySigns = SIGNS.filter((candidate) => candidate.convention === sign.convention);
        const conventionIndex = categorySigns.findIndex((candidate) => candidate.id === sign.id);
        const initiallyVisible = conventionIndex < MAX_INITIAL_SIGNS;
        const initialPresence = initiallyVisible ? 1 : selected ? regroupPhase : 0;
        const grey = selected ? 0 : filterPhase;
        const excludedOpacity = selected ? 1 : interpolate(t, [7.7, 9.5], [1, 0], clamp);
        const reveal = interpolate(t, [0.8 + index * 0.012, 1.15 + index * 0.012], [0, 1], clamp);
        const x = from.x + (to.x - from.x) * regroupPhase;
        const y = from.y + (to.y - from.y) * regroupPhase;
        const size = 68 - regroupPhase * 4;
        return (
          <Img
            key={sign.id}
            src={staticFile(sign.src)}
            style={{
              position: "absolute",
              left: x,
              top: y,
              width: size,
              height: size,
              objectFit: "contain",
              borderRadius: 6,
              opacity: reveal * excludedOpacity * initialPresence,
              filter: `grayscale(${grey}) saturate(${1.2 - grey * 1.1}) contrast(${1.08 - grey * 0.08})`,
              transform: `scale(${0.82 + reveal * 0.18})`,
              zIndex: 2,
            }}
          />
        );
      })}

      {/* Filter banner */}
      <div
        style={{
          position: "absolute",
          left: 70,
          right: 70,
          top: 208,
          padding: "12px 28px",
          borderRadius: 16,
          background: "rgba(255, 255, 255, 0.96)",
          backdropFilter: "blur(12px)",
          boxShadow: "0 12px 32px rgba(15, 23, 42, 0.09)",
          border: "1.5px solid #C8DCF5",
          textAlign: "left",
          opacity: filterPhase * (1 - selectionPhase),
          transform: `translateY(${(1 - filterPhase) * -12}px)`,
        }}
      >
        <div style={{ color: COLORS.blue, fontSize: 13, fontWeight: 900, letterSpacing: 2, textTransform: "uppercase" }}>
          Taxonomy Filtering · Enforceable Semantics
        </div>
        <div style={{ marginTop: 4, color: COLORS.ink, fontSize: 24, lineHeight: 1.25, fontWeight: 700 }}>
          Retain signs that impose <span style={{ color: COLORS.blue, fontWeight: 900 }}>explicit, mandatory obligations</span> with verifiable rule logic
        </div>
      </div>

      {/* Selection banner
      <div
        style={{
          position: "absolute",
          left: 70,
          right: 70,
          top: 208,
          padding: "16px 28px",
          borderRadius: 16,
          background: "linear-gradient(135deg, #F0F7FF 0%, #E3F0FF 100%)",
          border: "2px solid #B8D4F4",
          boxShadow: "0 12px 32px rgba(36, 88, 166, 0.1)",
          textAlign: "left",
          opacity: selectionPhase * (1 - regroupPhase),
          transform: `translateY(${(1 - selectionPhase) * -12}px)`,
        }}
      >
        <span style={{ color: COLORS.blue, fontSize: 30, fontWeight: 900 }}>34 Retained Signs.</span>
        <span style={{ color: COLORS.ink, fontSize: 23, fontWeight: 700 }}>
          {" "}All implemented in simulation with explicitly defined, verifiable rule logic.
        </span>
      </div> */}

      {/* High-impact unboxed KPI headline row (Best Paper Award styling) */}
      <div
        style={{
          position: "absolute",
          left: 70,
          right: 70,
          top: 200,
          display: "flex",
          alignItems: "center",
          gap: 65,
          opacity: regroupPhase,
          transform: `translateY(${(1 - regroupPhase) * -10}px)`,
        }}
      >
        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span
            style={{
              fontSize: 62,
              fontWeight: 900,
              color: COLORS.blue,
              fontVariantNumeric: "tabular-nums",
              letterSpacing: -2,
              lineHeight: 1,
            }}
          >
            34
          </span>
          <span style={{ fontSize: 25, fontWeight: 800, color: COLORS.ink, letterSpacing: -0.4 }}>
            signs
          </span>
        </div>

        <div style={{ width: 1.5, height: 36}} />

        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span
            style={{
              fontSize: 62,
              fontWeight: 900,
              color: COLORS.blue,
              fontVariantNumeric: "tabular-nums",
              letterSpacing: -2,
              lineHeight: 1,
            }}
          >
            29
          </span>
          <span style={{ fontSize: 25, fontWeight: 800, color: COLORS.ink, letterSpacing: -0.4 }}>
            testing scenarios
          </span>
        </div>

        <div style={{ width: 1.5, height: 36}} />

        <div style={{ display: "flex", alignItems: "baseline", gap: 12 }}>
          <span
            style={{
              fontSize: 62,
              fontWeight: 900,
              color: COLORS.blue,
              fontVariantNumeric: "tabular-nums",
              letterSpacing: -2,
              lineHeight: 1,
            }}
          >
            4
          </span>
          <span style={{ fontSize: 25, fontWeight: 800, color: COLORS.ink, letterSpacing: -0.4 }}>
            semantic groups
          </span>
        </div>


      </div>
    </Scene>
  );
};
