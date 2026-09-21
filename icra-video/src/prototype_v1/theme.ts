import { loadFont } from "@remotion/google-fonts/Inter";

export const { fontFamily } = loadFont("normal", {
  weights: ["400", "500", "600", "700"],
  subsets: ["latin"],
});

export const C = {
  bg: "#FAFAF7",
  ink: "#141414",
  muted: "#707070",
  line: "#D8D8D2",
  red: "#B8322A",
  green: "#2E7D4F",
  blue: "#2458A6",
};
