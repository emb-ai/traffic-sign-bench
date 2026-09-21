// ─────────────────────────────────────────────────────────────────────────────
// STYLE — typography, colours, margins. Edit here, not inside scenes.
// Visual language follows Fig. 1 of the current paper (white cards, coloured
// group bar, light-grey inner panels, Lato-like sans). Group colours were
// sampled from the paper figure.
// ─────────────────────────────────────────────────────────────────────────────
import { loadFont } from "@remotion/google-fonts/Lato";

export const FONT = loadFont("normal", { weights: ["400", "700", "900"], subsets: ["latin"] }).fontFamily;

export const COLORS = {
  bg: "#FFFFFF",
  ink: "#1A1A1A",
  muted: "#7A7A7A",
  faint: "#B5B5B5",
  border: "#E2E2E2",
  panel: "#F4F4F4",
  red: "#D64533", // violation / prohibited
  green: "#2E8B57", // compliant
  blue: "#2458A6", // route / information
  baseline: "#BDBDBD", // grey bars for baseline planners
};

// Semantic groups, as in Fig. 1
export const GROUP = {
  priority: { bar: "#90CAF9", text: "#3C8DD8", label: "Priority" },
  speed: { bar: "#E76F51", text: "#E05A3A", label: "Speed" },
  obstacles: { bar: "#A1CB35", text: "#7EA72A", label: "Obstacles" },
  routing: { bar: "#FCAD38", text: "#E8961F", label: "Routing" },
} as const;

export const SIZE = {
  margin: 90, // safe margin from frame edge
  headline: 64,
  subhead: 34,
  body: 30,
  small: 24,
  hero: 150, // very large numbers
  cardRadius: 18,
  panelRadius: 14,
};

// Show draft subtitles at the bottom of the frame (from config/subtitles.ts)
export const SHOW_SUBTITLES = false;
