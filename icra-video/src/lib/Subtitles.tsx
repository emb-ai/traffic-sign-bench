import { useT } from "./ui";
import { COLORS } from "../config/style";

export type SubLine = { from: number; to: number; text: string };

/** Draft subtitle overlay. Replace config/subtitles.ts after the final voice-over. */
export const Subtitles: React.FC<{ lines: SubLine[] }> = ({ lines }) => {
  const t = useT();
  const line = lines.find((l) => t >= l.from && t < l.to);
  if (!line) return null;
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom: 36, display: "flex", justifyContent: "center" }}>
      <div style={{ fontSize: 30, color: "#fff", backgroundColor: "rgba(20,20,20,0.82)", padding: "10px 22px", borderRadius: 8, maxWidth: 1500, textAlign: "center" }}>{line.text}</div>
    </div>
  );
};
export const _c = COLORS;
