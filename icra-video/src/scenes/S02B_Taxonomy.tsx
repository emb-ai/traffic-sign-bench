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

const CATEGORIES: { key: ConventionKey; label: string }[] = [
  { key: "warning", label: "Warning" },
  { key: "priority", label: "Priority" },
  { key: "prohibitory", label: "Prohibitory" },
  { key: "mandatory", label: "Mandatory" },
  { key: "special", label: "Special regulation" },
  { key: "information", label: "Information" },
  { key: "direction", label: "Direction" },
  { key: "panels", label: "Additional panels" },
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
    x: 57 + categoryIndex * 228 + (index % 2) * 91,
    y: 238 + Math.floor(index / 2) * 102,
  };
};

const semanticPosition = (sign: SignItem) => {
  if (!sign.semantic) return conventionPosition(sign);
  const groups = Object.keys(GROUP) as SemanticKey[];
  const groupIndex = groups.indexOf(sign.semantic);
  const groupSigns = SIGNS.filter((candidate) => candidate.semantic === sign.semantic);
  const index = groupSigns.findIndex((candidate) => candidate.id === sign.id);
  return {
    x: 104 + groupIndex * 455 + (index % 4) * 80,
    y: 332 + Math.floor(index / 4) * 90,
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
      <div style={{ position: "absolute", left: 70, right: 70, top: 42, textAlign: "left" }}>
        <div style={{ opacity: 1 - regroupPhase }}>
          <Headline size={55}>From a national sign system to verifiable traffic rules</Headline>
          <div style={{ marginTop: 10, color: COLORS.muted, fontSize: 25 }}>
            A Vienna-Convention reference system · eight functional classes
          </div>
        </div>
        <div style={{ position: "absolute", inset: 0, opacity: regroupPhase }}>
          <Headline size={55}>34 implemented signs → 4 capability-based groups</Headline>
          <div style={{ marginTop: 10, color: COLORS.muted, fontSize: 25 }}>
            Reorganized by the planning capability demanded of the ego vehicle
          </div>
        </div>
      </div>

      {CATEGORIES.map((category, index) => (
        <div
          key={category.key}
          style={{
            position: "absolute",
            left: 40 + index * 228,
            top: 178,
            width: 210,
            height: 445,
            borderRadius: 16,
            background: "#FAFAFA",
            border: `1px solid ${COLORS.border}`,
            opacity: initialLabels,
          }}
        >
          <div style={{ height: 7, background: index < 5 ? "#AFC2D9" : "#D3D8DE", borderRadius: "16px 16px 0 0" }} />
          <div style={{ paddingTop: 12, textAlign: "center", color: COLORS.ink, fontSize: category.key === "special" || category.key === "panels" ? 18 : 20, fontWeight: 900 }}>
            {category.label}
          </div>
          {SIGNS.filter((sign) => sign.convention === category.key).length > MAX_INITIAL_SIGNS && (
            <div style={{ position: "absolute", left: 0, right: 0, bottom: 14, textAlign: "center", color: COLORS.muted, fontSize: 30, fontWeight: 900 }}>
              · · ·
            </div>
          )}
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
              top: 200,
              width: 410,
              height: 450,
              borderRadius: 20,
              background: "#fff",
              border: `2px solid ${COLORS.border}`,
              boxShadow: "0 8px 28px rgba(0,0,0,0.07)",
              opacity: groupCards,
              transform: `translateY(${(1 - groupCards) * 26}px)`,
            }}
          >
            <div style={{ height: 12, borderRadius: "18px 18px 0 0", background: color.bar }} />
            <div style={{ display: "flex", justifyContent: "space-between", padding: "17px 24px" }}>
              <span style={{ fontSize: 34, fontWeight: 900 }}>{color.label}</span>
              <span style={{ color: color.text, fontSize: 20, fontWeight: 900, textAlign: "right" }}>
                {signs} signs<br />{scenarios} tests
              </span>
            </div>
            <div style={{ position: "absolute", left: 24, right: 24, bottom: 20, borderTop: `2px solid ${COLORS.panel}`, paddingTop: 12, color: COLORS.muted, fontSize: 19, fontWeight: 700 }}>
              {capability}
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

      <div
        style={{
          position: "absolute",
          left: 170,
          right: 170,
          bottom: 70,
          padding: "20px 34px",
          borderRadius: 18,
          background: "#F4F6F8",
          border: `2px solid ${COLORS.border}`,
          textAlign: "center",
          opacity: filterPhase * (1 - selectionPhase),
          transform: `translateY(${(1 - filterPhase) * 16}px)`,
        }}
      >
        <div style={{ color: COLORS.blue, fontSize: 22, fontWeight: 900, letterSpacing: 1.8, textTransform: "uppercase" }}>From catalogue to executable rules</div>
        <div style={{ marginTop: 8, color: COLORS.ink, fontSize: 29, lineHeight: 1.25, fontWeight: 700 }}>
          Retain signs with explicit obligations and machine-verifiable outcomes. Exclude signs whose meaning is primarily advisory, contextual, or conditional.
        </div>
      </div>

      <div
        style={{
          position: "absolute",
          left: 280,
          right: 280,
          bottom: 66,
          padding: "20px 34px",
          borderRadius: 18,
          background: "#EEF6FF",
          border: "2px solid #B8D4F4",
          textAlign: "center",
          opacity: selectionPhase * (1 - regroupPhase),
        }}
      >
        <span style={{ color: COLORS.blue, fontSize: 38, fontWeight: 900 }}>34 signs.</span>
        <span style={{ color: COLORS.ink, fontSize: 27, fontWeight: 700 }}> Every rule executable. Every violation automatically verifiable.</span>
      </div>

      <div
        style={{
          position: "absolute",
          left: 260,
          right: 260,
          top: 770,
          textAlign: "center",
          color: COLORS.muted,
          fontSize: 27,
          fontWeight: 700,
          opacity: regroupPhase,
        }}
      >
        34 signs · 29 functional test types · explicit rule logic
      </div>
    </Scene>
  );
};
