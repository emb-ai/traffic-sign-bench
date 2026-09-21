import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame } from "remotion";
import { C, Card, clamp, G } from "./ui";

// Mirrors Fig. 1 of the current paper: 34 signs, 4 groups, 29 scenario types.
// Icons: traffic_bench/signs/icons (the project's own). Bottom images: the real
// "verifier example" panels cropped from Fig. 1.
const GROUPS = [
  {
    key: "priority",
    title: "Priority",
    signs: 8,
    scen: 6,
    example: "crosswalk",
    icons: ["main_road", "secondary_road", "yield", "stop", "crosswalk", "roundabout"],
  },
  {
    key: "speed",
    title: "Speed",
    signs: 7,
    scen: 4,
    example: "speed limit",
    icons: ["speed_limit_40", "end_speed_limit_40", "min_speed", "zone_speed_40", "end_zone_speed_40"],
  },
  {
    key: "obstacles",
    title: "Obstacles",
    signs: 8,
    scen: 8,
    example: "detour",
    icons: ["detour_right", "detour_left", "detour_either", "bus_lane", "bike_lane", "bus_lane_road", "bike_lane_road"],
  },
  {
    key: "routing",
    title: "Routing",
    signs: 11,
    scen: 11,
    example: "one way",
    icons: [
      "direction_straight",
      "direction_right",
      "direction_left",
      "direction_straight_right",
      "direction_straight_left",
      "direction_left_right",
      "no_right_turn",
      "no_left_turn",
      "no_entry",
      "one_way_right",
      "one_way_left",
    ],
  },
] as const;

const ease = Easing.bezier(0.16, 1, 0.3, 1);

export const Taxonomy: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill>
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 70,
          fontSize: 64,
          fontWeight: 900,
          opacity: interpolate(frame, [0, 15], [0, 1], clamp),
        }}
      >
        34 traffic signs
        <span style={{ fontWeight: 400, color: C.muted }}> · 4 groups · 29 scenario types</span>
      </div>

      {GROUPS.map((g, i) => {
        const col = G[g.key];
        const start = 12 + i * 12;
        return (
          <Card
            key={g.key}
            bar={col.bar}
            title={g.title}
            right={
              <span style={{ color: col.text }}>
                <b>{g.signs} signs</b>
                <br />
                {g.scen} scenarios
              </span>
            }
            style={{
              left: 90 + i * 442,
              top: 215,
              width: 410,
              height: 730,
              opacity: interpolate(frame, [start, start + 14], [0, 1], clamp),
              translate: interpolate(frame, [start, start + 20], ["0px 50px", "0px 0px"], { ...clamp, easing: ease }),
            }}
          >
            <div
              style={{
                margin: "6px 18px 0",
                height: 330,
                backgroundColor: C.panel,
                borderRadius: 16,
                display: "flex",
                flexWrap: "wrap",
                alignContent: "center",
                justifyContent: "center",
                gap: 12,
                padding: 14,
              }}
            >
              {g.icons.map((icon, j) => {
                const t = start + 18 + j * 3;
                return (
                  <Img
                    key={icon}
                    src={staticFile(`signs/${icon}.png`)}
                    style={{
                      width: 76,
                      height: 76,
                      objectFit: "contain",
                      opacity: interpolate(frame, [t, t + 6], [0, 1], clamp),
                      scale: interpolate(frame, [t, t + 12], [0.5, 1], {
                        ...clamp,
                        easing: Easing.spring({ damping: 12 }),
                      }),
                    }}
                  />
                );
              })}
            </div>

            <div
              style={{
                opacity: interpolate(frame, [70 + i * 8, 85 + i * 8], [0, 1], clamp),
                margin: "26px 18px 0",
              }}
            >
              <div style={{ fontSize: 22, color: C.muted, borderTop: `2px dotted ${C.border}`, paddingTop: 12 }}>
                <b style={{ color: C.ink }}>verifier example:</b> {g.example}
              </div>
              <Img
                src={staticFile(`fig1/${g.key}.png`)}
                style={{ width: 370, marginTop: 12, borderRadius: 8 }}
              />
            </div>
          </Card>
        );
      })}
    </AbsoluteFill>
  );
};
