// Scenario diversity: the corridor crop of the real-maps slide → the same map in the simulator → background traffic at
// the nuPlan density quantiles the benchmark probes (histogram + moving quantile) → its 10 real test variants → 29,000.
// Frames are square 800×800 GIF step-0 crops (ego at spawn). Editable content: src/config/diversityScene.ts
import { Img, interpolate, staticFile } from "remotion";
import hist from "../../public/diversity/nuplan_density_hist.json";
import { DIVERSITY as C } from "../config/diversityScene";
import { PAPER } from "../config/paperStyle";
import { COLORS, GROUP, SIZE } from "../config/style";
import { clamp, Headline, rise, Scene, useT } from "../lib/ui";

const TT = C.timing;
const FRAME = { x: SIZE.margin, y: 300, w: 560, h: 560 }; // simulator frames are square 800 × 800 (step 0)
const fadeOut = (t: number, at: number, dur = 0.5) => 1 - rise(t, at, dur);

const SampledAxes: React.FC<{ t: number }> = ({ t }) => (
  <div
    style={{
      position: "absolute",
      left: SIZE.margin,
      right: SIZE.margin,
      top: 190,
      height: 76,
      display: "flex",
      alignItems: "stretch",
      gap: 12,
      zIndex: 2,
    }}
  >
    <div
      style={{
        width: 156,
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        justifyContent: "center",
        opacity: rise(t, TT.header + 0.25, 0.4),
      }}
    >
      <div style={{ ...PAPER.sectionLabel, color: COLORS.blue, lineHeight: 1.25 }}>{C.axisLabel}</div>
      <div style={{ marginTop: 5, fontSize: 16, fontWeight: 700, color: COLORS.muted }}>5 controlled axes</div>
    </div>

    {C.axes.map((axis, i) => {
      const reveal = rise(t, TT.header + 0.35 + i * 0.08, 0.35);
      return (
        <div
          key={axis.number}
          style={{
            position: "relative",
            flex: 1,
            minWidth: 0,
            padding: "12px 14px 10px 48px",
            boxSizing: "border-box",
            borderRadius: 13,
            border: `1.5px solid ${axis.example ? "#AFC9EA" : "#E2E8F0"}`,
            borderTop: axis.example ? `4px solid ${COLORS.blue}` : "1.5px solid #E2E8F0",
            backgroundColor: axis.example ? "#F3F7FD" : "#FAFBFC",
            boxShadow: axis.example ? "0 6px 18px rgba(36, 88, 166, 0.10)" : "none",
            opacity: reveal,
            transform: `translateY(${(1 - reveal) * 8}px)`,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 13,
              top: 13,
              fontSize: 14,
              fontWeight: 900,
              color: axis.example ? COLORS.blue : "#A3AFBF",
              fontVariantNumeric: "tabular-nums",
            }}
          >
            {axis.number}
          </div>
          <div style={{ fontSize: 18, lineHeight: 1.1, fontWeight: 900, color: axis.example ? COLORS.blue : COLORS.ink, whiteSpace: "nowrap" }}>
            {axis.label}
          </div>
          <div style={{ marginTop: 6, fontSize: 14, lineHeight: 1.1, fontWeight: 700, color: COLORS.muted, whiteSpace: "nowrap" }}>{axis.detail}</div>
          {axis.example && (
            <div
              style={{
                position: "absolute",
                right: 10,
                top: -12,
                padding: "3px 8px",
                borderRadius: 999,
                backgroundColor: COLORS.blue,
                color: "#fff",
                fontSize: 10,
                lineHeight: 1,
                fontWeight: 900,
                letterSpacing: 1.1,
                textTransform: "uppercase",
              }}
            >
              example below ↓
            </div>
          )}
        </div>
      );
    })}
  </div>
);

// nuPlan histogram with the benchmark's quantile probe
const Histogram: React.FC<{ t: number; x: number; y: number; w: number; h: number }> = ({ t, x, y, w, h }) => {
  const counts = hist.counts as number[];
  const edges = hist.bin_edges as number[];
  const max = Math.max(...counts);
  const xMax = edges[edges.length - 1];
  const px = (v: number) => (v / xMax) * w;
  const L = C.levels;
  // quantile marker: appears at the first level, then slides level to level
  const k = L.map((_, i) => rise(t, TT.levels[i], 0.7));
  const at = k[0] === 0 ? L[0].value : L.reduce((v, lv, i) => (i === 0 ? lv.value : v + (lv.value - L[i - 1].value) * k[i]), 0);
  const cur = k[2] > 0.5 ? 2 : k[1] > 0.5 ? 1 : 0;
  const draw = rise(t, TT.hist, 0.8);
  return (
    <div style={{ position: "absolute", left: x, top: y, width: w }}>
      <svg width={w} height={h + 40} style={{ overflow: "visible" }}>
        {counts.map((c, i) => {
          const bh = (c / max) * h * draw;
          const x0 = px(edges[i]) + 2;
          const inBand = edges[i + 1] > L[0].value && edges[i] < L[2].value;
          return <rect key={i} x={x0} y={h - bh} width={px(edges[i + 1]) - px(edges[i]) - 4} height={bh} rx={3} fill={inBand ? "#9CB8E0" : "#D5DCE6"} />;
        })}
        <line x1={0} y1={h} x2={w} y2={h} stroke="#94A3B8" strokeWidth={2} />
        {edges.filter((e) => e % 2 === 0).map((e) => (
          <text key={e} x={px(e)} y={h + 24} fontSize={16} fill={COLORS.muted} textAnchor="middle">{e}</text>
        ))}
        {k[0] > 0 && (
          <g opacity={k[0]}>
            <line x1={px(at)} y1={-10} x2={px(at)} y2={h} stroke={COLORS.blue} strokeWidth={4} />
            <circle cx={px(at)} cy={-10} r={7} fill={COLORS.blue} />
          </g>
        )}
      </svg>
      <div style={{ fontSize: 17, color: COLORS.muted, marginTop: 4 }}>{C.histAxis}</div>
      {k[0] > 0 && (
        <div style={{ position: "absolute", left: Math.min(px(at) + 14, w - 250), top: -34, fontSize: 22, fontWeight: 900, color: COLORS.blue, whiteSpace: "nowrap", opacity: k[0] }}>
          nuPlan p{L[cur].q} · {L[cur].value.toFixed(1)} / lane
        </div>
      )}
    </div>
  );
};

export const S16_Diversity: React.FC = () => {
  const t = useT();
  const phaseB = rise(t, TT.zoom + 0.5, 0.6) * fadeOut(t, TT.tiles - 0.5, 0.5); // single-map part
  const cropOp = rise(t, TT.crop, 0.4) * fadeOut(t, TT.zoom + 0.7, 0.5);
  // the crop card morphs into the frame box, the map inside zooms towards the ego's corridor
  const mv = rise(t, TT.zoom - 0.3, 0.9);
  const CROP0 = { x: SIZE.margin, y: 300, w: 920, h: 404 };
  const box = { x: CROP0.x + (FRAME.x - CROP0.x) * mv, y: CROP0.y + (FRAME.y - CROP0.y) * mv, w: CROP0.w + (FRAME.w - CROP0.w) * mv, h: CROP0.h + (FRAME.h - CROP0.h) * mv };
  const zoom = interpolate(t, [TT.zoom - 0.3, TT.zoom + 1.0], [1, 2.6], clamp);
  const L = C.levels;
  const lvl = L.map((_, i) => rise(t, TT.levels[i], 0.6));
  const RX = FRAME.x + FRAME.w + 90;
  const RW = 1920 - SIZE.margin - RX;
  const tileW = 210;
  const tileH = tileW; // square step-0 frames
  const gridX = SIZE.margin;
  return (
    <Scene>
      <div style={{ position: "absolute", left: SIZE.margin, right: SIZE.margin, top: 44, opacity: rise(t, TT.header, 0.4), zIndex: 2 }}>
        <div style={{ display: "inline-block", padding: "4px 14px", borderRadius: 999, ...PAPER.pill, color: COLORS.blue, fontSize: 13, fontWeight: 900, letterSpacing: 2.2, textTransform: "uppercase", marginBottom: 8 }}>{C.kicker}</div>
        <Headline size={50}>{C.title}</Headline>
        <div style={{ marginTop: 6, color: COLORS.muted, fontSize: 24, fontWeight: 700 }}>{C.subtitle}</div>
      </div>
      <SampledAxes t={t} />

      {/* the corridor crop of the previous slide moves into the frame box and zooms into the simulator view of the map */}
      {cropOp > 0 && (
        <div style={{ position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h, borderRadius: PAPER.cardRadius, overflow: "hidden", border: `2px solid ${GROUP.obstacles.bar}`, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: cropOp }}>
          <Img src={staticFile(C.crop.src)} style={{ position: "absolute", left: "50%", top: "50%", width: 920, height: 404, marginLeft: -460, marginTop: -202, objectFit: "contain", transform: `scale(${zoom})` }} />
          <div style={{ position: "absolute", left: 16, top: 12, fontSize: 18, fontWeight: 900, letterSpacing: 1.4, color: GROUP.obstacles.text, textTransform: "uppercase", opacity: 1 - mv }}>{C.crop.label}</div>
          <Img src={staticFile(C.crop.sign)} style={{ position: "absolute", right: 16, top: 12, width: 48, height: 48, opacity: 1 - mv }} />
        </div>
      )}

      {phaseB > 0 && (
        <div style={{ opacity: phaseB }}>
          <div style={{ position: "absolute", left: FRAME.x, top: FRAME.y, width: FRAME.w, height: FRAME.h, borderRadius: PAPER.cardRadius, overflow: "hidden", border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, backgroundColor: "#fff" }}>
            <Img src={staticFile(C.emptyFrame)} style={{ position: "absolute", width: "100%", height: "100%" }} />
            {L.map((lv, i) => (
              <Img key={lv.q} src={staticFile(lv.frame)} style={{ position: "absolute", width: "100%", height: "100%", opacity: lvl[i] }} />
            ))}
          </div>
          <div style={{ position: "absolute", left: RX, top: FRAME.y, width: RW, boxSizing: "border-box", padding: "24px 32px 28px", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, borderTop: `5px solid ${COLORS.blue}`, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: rise(t, TT.hist - 0.2, 0.5) }}>
            <div style={{ ...PAPER.sectionLabel, color: COLORS.blue }}>{C.histTitle}</div>
            <div style={{ marginTop: 7, fontSize: 20, fontWeight: 700, color: COLORS.ink }}>{C.histSubtitle}</div>
            <div style={{ position: "relative", height: 370, marginTop: 38 }}>
              <Histogram t={t} x={0} y={24} w={RW - 64} h={270} />
            </div>
            {/* density slider: the three probes the benchmark uses */}
            <div style={{ display: "flex", gap: 16, marginTop: 6 }}>
              {L.map((lv, i) => {
                const on = lvl[i] > 0.5 && (i === 2 || lvl[i + 1] <= 0.5);
                return (
                  <div key={lv.q} style={{ flex: 1, padding: "12px 16px", borderRadius: 12, border: `2px solid ${on ? COLORS.blue : "#E2E8F0"}`, backgroundColor: on ? "#EEF4FC" : "#fff", opacity: 0.4 + 0.6 * rise(t, TT.levels[0] - 0.3, 0.4) }}>
                    <div style={{ fontSize: 22, fontWeight: 900, color: on ? COLORS.blue : COLORS.ink }}>{lv.name}</div>
                    <div style={{ fontSize: 17, color: COLORS.muted, fontWeight: 700 }}>nuPlan p{lv.q} · {lv.value.toFixed(1)} / lane</div>
                  </div>
                );
              })}
            </div>
            <div style={{ fontSize: 19, fontWeight: 700, color: "#475569", marginTop: 18, lineHeight: 1.35, opacity: rise(t, TT.levels[1], 0.5) }}>{C.agentsNote}</div>
          </div>
        </div>
      )}

      {/* the map multiplies into its 10 real test variants → 29 × 100 × 10 */}
      {t >= TT.tiles - 0.2 && (
        <>
          <div
            style={{
              position: "absolute",
              left: gridX,
              top: 330,
              width: 1122,
              height: 32,
              display: "flex",
              alignItems: "center",
              gap: 12,
              borderBottom: `2px solid #DCE7F5`,
              opacity: rise(t, TT.tiles - 0.15, 0.4),
            }}
          >
            <span
              style={{
                padding: "4px 10px",
                borderRadius: 999,
                backgroundColor: COLORS.blue,
                color: "#fff",
                fontSize: 14,
                lineHeight: 1,
                fontWeight: 900,
                letterSpacing: 1.4,
                textTransform: "uppercase",
              }}
            >
              {C.gridKicker}
            </span>
            <span style={{ fontSize: 23, fontWeight: 900, color: COLORS.ink }}>{C.gridTitle}</span>
            <span style={{ fontSize: 17, fontWeight: 700, color: COLORS.muted }}>{C.gridNote}</span>
          </div>

          {C.tiles.map((tl, i) => {
            const p = rise(t, TT.tiles + i * TT.tileStep, 0.4);
            const col = i % 5;
            const row = Math.floor(i / 5);
            return (
              <div key={tl.src} style={{ position: "absolute", left: gridX + col * (tileW + 18), top: 376 + row * (tileH + 66), width: tileW, opacity: p, transform: `scale(${0.9 + 0.1 * p})` }}>
                <div style={{ width: tileW, height: tileH, borderRadius: 12, overflow: "hidden", border: PAPER.cardBorder, boxShadow: PAPER.cardShadow }}>
                  <Img src={staticFile(tl.src)} style={{ width: "100%", height: "100%" }} />
                </div>
                <div style={{ fontSize: 15, fontWeight: 800, color: COLORS.ink, marginTop: 5, whiteSpace: "nowrap" }}>{tl.caption}</div>
                <div style={{ fontSize: 14, fontWeight: 600, color: COLORS.muted, whiteSpace: "nowrap" }}>{tl.agents}</div>
              </div>
            );
          })}
          <div
            style={{
              position: "absolute",
              left: 1224,
              top: 584,
              width: 66,
              textAlign: "center",
              fontSize: 54,
              lineHeight: 1,
              fontWeight: 900,
              color: COLORS.blue,
              opacity: rise(t, TT.tiles + 10 * TT.tileStep, 0.4),
            }}
          >
            →
          </div>

          <div style={{ position: "absolute", left: 1300, top: 412, width: 1920 - SIZE.margin - 1300, boxSizing: "border-box", padding: "28px 32px", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, borderTop: `5px solid ${COLORS.blue}`, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: rise(t, TT.formula, 0.5) }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
              {C.formula.map((f, i) => (
                <div key={f.label} style={{ display: "flex", alignItems: "flex-start", gap: 14, opacity: rise(t, TT.formula + 0.3 * i, 0.4) }}>
                  {i > 0 && <span style={{ fontSize: 44, color: COLORS.faint, fontWeight: 700 }}>×</span>}
                  <div>
                    <div style={{ fontSize: 56, fontWeight: 900, color: COLORS.ink, lineHeight: 1 }}>{f.value}</div>
                    <div style={{ fontSize: 16, fontWeight: 700, color: COLORS.muted, marginTop: 6, width: 100 }}>{f.label}</div>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ borderTop: `1px solid ${PAPER.rowLine}`, marginTop: 20, paddingTop: 16, opacity: rise(t, TT.formula + 1.0, 0.5) }}>
              <div style={{ fontSize: 84, fontWeight: 900, color: COLORS.blue, lineHeight: 1 }}>= {C.total}</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: COLORS.ink, marginTop: 6 }}>{C.totalLabel}</div>
              <div style={{ fontSize: 20, fontWeight: 700, color: COLORS.muted, marginTop: 4 }}>{C.split}</div>
            </div>
          </div>
        </>
      )}
    </Scene>
  );
};
