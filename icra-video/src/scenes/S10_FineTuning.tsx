// Fine-tuning section, one continuous story:
// real training scenario → 8 privileged experts → Sign Compliance / Destination → Quality → retained trajectories
// → 36,828 high-quality expert trajectories → frozen real frame (same selected trajectory, IDMe-s1)
// → base planner inputs → sign-aware extensions → PlanT-2 → expert supervision → PlanT-2-FT.
// Editable content: src/config/fineTuningScene.ts (selection half) and src/config/archScene.ts (architecture half).
import React from "react";
import { AbsoluteFill, Img, interpolate, staticFile } from "remotion";
import c0 from "../../public/finetune/scenes/c0.json";
import c4 from "../../public/finetune/scenes/c4.json";
import c7 from "../../public/finetune/scenes/c7.json";
import n04 from "../../public/finetune/scenes/n04.json";
import n15 from "../../public/finetune/scenes/n15.json";
import { ARCH_SCENE, FT_WARP } from "../config/archScene";
import { FT_SCENE } from "../config/fineTuningScene";
import { PAPER } from "../config/paperStyle";
import { COLORS, SIZE } from "../config/style";
import { clamp, Headline, Mark, rise, Scene, useT } from "../lib/ui";
import { ArchitectureBody, archStage, FR } from "./S11_ArchitectureFT";

const C = FT_SCENE;
const TT = C.timing;

// Expert-selection scene (real, verified by tools/prepare_selection_scenes.py); chosen in the config
type SceneData = typeof n04;
const SEL_SCENES = { c0, c7, c4, n04, n15 } as unknown as Record<string, SceneData>;
const SelCtx = React.createContext<SceneData>(n04 as SceneData);
const useSel = () => React.useContext(SelCtx);
type Expert = SceneData["experts"][number];
const keyOf = (e: Expert) => `${e.policy}/${e.variant}`;
const failed = (e: Expert) =>
  e.crashed || e.out_of_road || Object.keys(e.violations).length > 0 || !e.arrived_dest || e.offroad_idx !== null;
const ruleOk = (e: Expert) => Object.keys(e.violations).length === 0;
// destination column = the remaining pass conditions (reached, no crash, no off-road);
// in this scene the destination failures are the off-road IDM variants (arrived_dest = false)
// geometric off-road (tools/prepare_selection_scenes.py): the recorded run was not flagged, the map shows the exit
const geoOff = (e: Expert) => e.offroad_idx !== null;
const destOk = (e: Expert) => e.arrived_dest && !e.out_of_road && !e.crashed && !geoOff(e);
// drawable part of a track: a geometric off-road rollout stops where it leaves the road
const shownLen = (e: Expert) => (e.offroad_idx !== null ? e.offroad_idx + 1 : e.track.length);

// ─── selection half: real map + 8 real trajectories ──────────────────────────
// After the table leaves, the map settles exactly into the box of the frozen frame that follows.
const MAP = { left: FR.left, top: FR.top, size: FR.size };

// Opening layout: large map. View = bounds of the 8 real tracks + padM, widened to the panel aspect.
const introView = (sceneData: SceneData) => {
  const pts = sceneData.experts.flatMap((e) => e.track);
  const pad = C.intro.padM;
  let [x0, x1] = [Math.min(...pts.map((p) => p[0])) - pad, Math.max(...pts.map((p) => p[0])) + pad];
  let [y0, y1] = [Math.min(...pts.map((p) => p[1])) - pad, Math.max(...pts.map((p) => p[1])) + pad];
  const aspect = C.intro.map.w / C.intro.map.h;
  if ((x1 - x0) / (y1 - y0) < aspect) {
    const half = ((y1 - y0) * aspect) / 2, cx = (x0 + x1) / 2;
    [x0, x1] = [cx - half, cx + half];
  } else {
    const half = (x1 - x0) / aspect / 2, cy = (y0 + y1) / 2;
    [y0, y1] = [cy - half, cy + half];
  }
  return [x0, y0, x1, y1];
};

// 0 = large-map layout (opening + filtering), 1 = dataset layout
// the map keeps its large layout; the selection slide cross-fades directly into the real frame (no intermediate state)
const morphAt = (_t: number) => 0;
const mix = (a: number, b: number, m: number) => a + (b - a) * m;

const ExpertMap: React.FC<{ t: number }> = ({ t }) => {
  const sceneData = useSel();
  const sceneCfg = C.selection.scenes[sceneData.id as keyof typeof C.selection.scenes];
  const m = morphAt(t);
  const box = {
    left: mix(C.intro.map.left, MAP.left, m), top: mix(C.intro.map.top, MAP.top, m),
    w: mix(C.intro.map.w, MAP.size, m), h: mix(C.intro.map.h, MAP.size, m),
  };
  // the view changes together with the panel, so its aspect always equals the panel aspect
  const [x0, y0, x1, y1] = introView(sceneData).map((v, i) => mix(v, sceneData.view[i], m));
  const w = x1 - x0;
  const h = y1 - y0;
  const pxPerM = box.w / w;
  const u = interpolate(t, [TT.expertsAppear, TT.expertsDrawn], [0, 1], clamp);
  const maxLen = Math.max(...sceneData.experts.map((e) => e.track.length));
  const fadeAt = (at: number) => interpolate(t, [at, at + 0.5], [1, C.highlight.fadedOpacity], clamp);
  const decide = interpolate(t, [TT.selectionDecide, TT.selectionDecide + 0.6], [0, 1], clamp);
  const lineW = mix(C.intro.trackWidth, C.highlight.candidateWidth, m);
  const egoScale = mix(1.25, 1, m);
  const sign = sceneData.sign;
  const signScreen = { x: ((sign.x - x0) / w) * box.w, y: ((y1 - sign.y) / h) * box.h };
  const signPx = mix(56, 44, m);
  // frozen training frame = dump frame 16 of the rank-1 trajectory = downsampled replay index 8 (checked: same pose)
  const rank1 = sceneData.experts.find((e) => e.selected_rank === 1)!;

  // draw order: faded first, selected last
  const order = [...sceneData.experts].sort((a, b) => (a.selected_rank ? 1 : 0) - (b.selected_rank ? 1 : 0));

  return (
    <div style={{ position: "absolute", left: box.left, top: box.top, width: box.w, height: box.h, borderRadius: PAPER.cardRadius, overflow: "hidden", border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, backgroundColor: "#fff" }}>
      <svg width={box.w} height={box.h} viewBox={`${x0} ${-y1} ${w} ${h}`}>
        <g transform="scale(1,-1)">
          {sceneData.lanes.map((p, i) => (
            <polygon key={i} points={p.map((q) => q.join(",")).join(" ")} fill="#D9D9D9" stroke="#D9D9D9" strokeWidth={0.15} />
          ))}
          {sceneData.lines.map((l, i) => (
            <polyline key={i} points={l.map((q) => q.join(",")).join(" ")} fill="none" stroke="#E0B000" strokeWidth={0.22} />
          ))}
          {/* traffic (NPC) of the rank-1 replay, drawn under the ego tracks on the same clock */}
          {sceneData.npcs.map((v, j) => {
            const now = Math.min(Math.floor(u * maxLen), rank1.track.length - 1);
            const q = v.track.find((r) => r[0] === now);
            if (!q || u <= 0) return null;
            return (
              <rect key={`npc${j}`} x={-v.length / 2} y={-v.width / 2} width={v.length} height={v.width} rx={0.3} fill="#B4BCC8" stroke="#6B7480" strokeWidth={0.12}
                transform={`translate(${q[1]},${q[2]}) rotate(${(q[3] * 180) / Math.PI})`} />
            );
          })}
          {order.map((e) => {
            const k = keyOf(e);
            const n = Math.max(1, Math.min(shownLen(e), Math.floor(u * maxLen)));
            const pts = e.track.slice(0, n);
            const isSel = !!e.selected_rank;
            // after selection only the rank-1 trajectory (the one used for the frozen frame) stays
            const focus = e.selected_rank === 1 ? 1 : interpolate(t, [TT.focusSelected, TT.focusSelected + 0.6], [1, 0.12], clamp);
            const op = (failed(e) ? fadeAt(TT.failMute) : !isSel ? fadeAt(TT.selectionDecide) : 1) * focus;
            const wScreen = isSel ? interpolate(decide, [0, 1], [lineW, C.highlight.width]) : lineW;
            const head = pts[pts.length - 1];
            const d = pts.map((q) => `${q[0]},${q[1]}`).join(" ");
            return (
              <g key={k} opacity={op}>
                {/* thin white casing keeps overlapping real tracks distinguishable */}
                <polyline points={d} fill="none" stroke="#fff" strokeWidth={(wScreen + 2) / pxPerM} strokeLinejoin="round" strokeLinecap="round" opacity={1 - decide} />
                {isSel && decide > 0 && (
                  <polyline points={d} fill="none" stroke={C.highlight.casing} strokeWidth={(wScreen + 3) / pxPerM} strokeLinejoin="round" strokeLinecap="round" opacity={decide} />
                )}
                <polyline points={d} fill="none" stroke={C.expertColors[k]} strokeWidth={wScreen / pxPerM} strokeLinejoin="round" strokeLinecap="round" />
                {u > 0 && (
                  <rect x={-2.3} y={-0.95} width={4.6} height={1.9} rx={0.3} fill={C.expertColors[k]} stroke="#1A1A1A" strokeWidth={0.15}
                    transform={`translate(${head[0]},${head[1]}) rotate(${(head[2] * 180) / Math.PI}) scale(${egoScale})`} />
                )}
              </g>
            );
          })}
        </g>
      </svg>
      <Img src={staticFile(sceneCfg.signIcon)} style={{ position: "absolute", left: signScreen.x - signPx / 2, top: signScreen.y - signPx / 2, width: signPx, height: signPx }} />
      <div style={{ position: "absolute", left: 16, bottom: 12, fontSize: mix(22, 19, m), color: COLORS.muted, backgroundColor: "rgba(255,255,255,0.88)", padding: "4px 10px", borderRadius: 6 }}>
        {sceneCfg.caption}
      </div>
    </div>
  );
};

// Selection table: all 8 experts and every selection criterion in one place (real flags + real F-scores)
const COLS = { name: 170, rule: 140, dest: 140, quality: 175 };
const ROW_H = 56;

// Paper-figure selection table: Expert | Sign Compliance | Destination | Quality. Every value comes from the verified scene file.
const SelectionTable: React.FC<{ t: number }> = ({ t }) => {
  const sceneData = useSel();
  const rows = Object.keys(C.expertNames).map((k) => sceneData.experts.find((e) => keyOf(e) === k)!);
  // metric by metric while the trajectories draw: Sign Compliance row by row, then Destination row by row
  // (never before that expert's trajectory has finished drawing on the map — same clock as ExpertMap)
  const maxLen = Math.max(...sceneData.experts.map((e) => e.track.length));
  const doneAt = (e: Expert) => TT.expertsAppear + (shownLen(e) / maxLen) * (TT.expertsDrawn - TT.expertsAppear);
  const faded = C.selection.rejectedOpacity;
  const mute = interpolate(t, [TT.failMute, TT.failMute + 0.5], [1, faded], clamp);
  const decide = rise(t, TT.selectionDecide, 0.5);
  const width = 16 + COLS.name + COLS.rule + COLS.dest + COLS.quality;
  const head: React.CSSProperties = { fontSize: 18, fontWeight: 800, color: COLORS.ink, lineHeight: 1.15, boxSizing: "border-box", textAlign: "center" };
  const center: React.CSSProperties = { display: "flex", justifyContent: "center", alignItems: "center" };
  const sum = sceneData.summary_geometric; // counts with the geometric off-road check applied
  const sumPart = (n: number, label: string, at: number, first = false) => (
    <span style={{ opacity: rise(t, at, 0.4) }}>{!first && <span style={{ color: COLORS.faint, margin: "0 10px" }}>→</span>}<b>{n}</b> {label}</span>
  );
  return (
    <div style={{ position: "absolute", left: C.intro.tableLeft, top: C.intro.map.top, width }}>
      <div style={{ ...PAPER.sectionLabel, color: COLORS.blue, marginBottom: 10, opacity: rise(t, TT.expertsAppear - 0.2, 0.4) }}>{C.text.expertsTitle}</div>
      <div style={{ borderRadius: 16, border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, overflow: "hidden", backgroundColor: "#fff" }}>
      <div style={{ display: "flex", alignItems: "center", minHeight: 62, padding: "8px 0 8px 16px", backgroundColor: PAPER.headRow, borderBottom: PAPER.cardBorder }}>
        <span style={{ ...head, textAlign: "left", width: COLS.name, fontSize: 14, fontWeight: 900, letterSpacing: 1.6, color: COLORS.muted, textTransform: "uppercase", opacity: rise(t, TT.expertsAppear, 0.4) }}>{C.text.colExpert}</span>
        <span style={{ ...head, width: COLS.rule, opacity: rise(t, TT.filterStart - 0.3, 0.3) }}>{C.text.checkRule}</span>
        <span style={{ ...head, width: COLS.dest, opacity: rise(t, TT.destReveal - 0.3, 0.3) }}>{C.text.checkDest}</span>
        <span style={{ ...head, width: COLS.quality, opacity: rise(t, TT.selectionStart - 0.2, 0.3) }}>
          {C.text.qualityTitle}
          <div style={{ fontSize: 14, fontWeight: 500, color: COLORS.muted, marginTop: 3, whiteSpace: "pre-line" }}>{C.text.qualityFormula}</div>
        </span>
      </div>
      {rows.map((e, i) => {
        const k = keyOf(e);
        const isSel = !!e.selected_rank;
        const op = failed(e) ? mute : e.quality_candidate && !isSel ? interpolate(decide, [0, 1], [1, faded]) : 1;
        const qAt = TT.selectionStart + 0.1 * rows.filter((r) => r.quality_candidate).indexOf(e);
        const selOn = isSel ? decide : 0;
        return (
          <div key={k} style={{
            display: "flex", alignItems: "center", height: ROW_H, paddingLeft: 16,
            borderBottom: i < rows.length - 1 ? `1px solid ${PAPER.rowLine}` : "none",
            backgroundColor: `rgba(242, 183, 5, ${0.13 * selOn})`,
            boxShadow: selOn > 0 ? `inset 0 0 0 1px rgba(160, 120, 0, ${0.45 * selOn})` : "none",
            opacity: rise(t, TT.expertsAppear + i * 0.05, 0.25),
          }}>
            <span style={{ width: COLS.name, display: "flex", alignItems: "center", opacity: op }}>
              <span style={{ width: 28, height: 7, borderRadius: 4, backgroundColor: C.expertColors[k], marginRight: 12, flexShrink: 0 }} />
              <span style={{ position: "relative", lineHeight: 1.05 }}>
                <span style={{ fontSize: 24, fontWeight: selOn > 0.5 ? 800 : 600 }}>{C.expertNames[k]}</span>
                {isSel && <span style={{ position: "absolute", left: 0, top: 27, fontSize: 12, fontWeight: 800, letterSpacing: 1.6, color: "#8A6A00", opacity: selOn, whiteSpace: "nowrap" }}>{C.text.selectedLabel}</span>}
              </span>
            </span>
            <span style={{ ...center, width: COLS.rule, opacity: op * rise(t, TT.filterStart + i * 0.08, 0.25) }}><Mark state={ruleOk(e) ? "ok" : "fail"} size={28} /></span>
            <span style={{ ...center, width: COLS.dest, opacity: op * rise(t, Math.max(doneAt(e), TT.destReveal + i * 0.08), 0.3) }}><Mark state={destOk(e) ? "ok" : "fail"} size={28} /></span>
            <span style={{ ...center, width: COLS.quality, fontSize: 23, fontVariantNumeric: "tabular-nums", opacity: op }}>
              {e.quality_candidate && e.f1 !== null && !geoOff(e) ? (
                <span style={{ fontWeight: selOn > 0.5 ? 800 : 600, opacity: rise(t, qAt, 0.3) }}>{e.f1.toFixed(3)}</span>
              ) : (
                <span style={{ color: COLORS.muted, opacity: rise(t, TT.selectionStart, 0.3) }}>—</span>
              )}
            </span>
          </div>
        );
      })}
      </div>
      <div style={{ fontSize: 22, color: COLORS.ink, marginTop: 18 }}>
        {sumPart(sum.successful, C.text.sumSuccessful, TT.failMute + 0.3, true)}
        {sumPart(sum.quality_candidates, C.text.sumCandidates, TT.selectionStart + 0.3)}
        {sumPart(sum.retained, C.text.sumRetained, TT.selectionDecide + 0.3)}
      </div>
    </div>
  );
};

// ─── opening: the three steps of this section ───────────────────────────────
const STEP_COLORS = [COLORS.blue, ARCH_SCENE.colors.supervision, ARCH_SCENE.colors.ft];
const IntroBeat: React.FC<{ t: number }> = ({ t }) => {
  const out = 1 - rise(t, TT.introOut, 0.5);
  if (out <= 0) return null;
  const cardW = 520;
  const gap = 90;
  const left = (1920 - (3 * cardW + 2 * gap)) / 2;
  return (
    <div style={{ opacity: out }}>
      {C.text.introSteps.map((st, i) => {
        const p = rise(t, TT.introSteps + i * TT.introStepGap, 0.5);
        const col = STEP_COLORS[i];
        const x = left + i * (cardW + gap);
        return (
          <React.Fragment key={st.n}>
            <div style={{
              position: "absolute", left: x, top: 340, width: cardW, height: 400, boxSizing: "border-box", padding: "28px 32px",
              backgroundColor: "#fff", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, borderTop: `5px solid ${col}`, boxShadow: PAPER.cardShadow,
              opacity: p, transform: `translateY(${(1 - p) * 18}px)`,
            }}>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <div style={{ width: 44, height: 44, borderRadius: 22, backgroundColor: col, color: "#fff", fontSize: 24, fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center" }}>{st.n}</div>
                <div style={{ fontSize: 34, fontWeight: 900, color: COLORS.ink }}>{st.title}</div>
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: "#475569", marginTop: 22, lineHeight: 1.3 }}>{st.body}</div>
              {/* small pictogram: the 8 expert colours / the selected trajectory / the fine-tuned planner */}
              <div style={{ position: "absolute", left: 32, bottom: 86, display: "flex", gap: 8, alignItems: "center" }}>
                {i === 0 && Object.values(C.expertColors).map((c) => <span key={c} style={{ width: 38, height: 8, borderRadius: 4, backgroundColor: c }} />)}
                {i === 1 && <>
                  {Object.values(C.expertColors).slice(0, 6).map((c) => <span key={c} style={{ width: 30, height: 6, borderRadius: 3, backgroundColor: c, opacity: C.highlight.fadedOpacity * 3 }} />)}
                  <span style={{ width: 60, height: 10, borderRadius: 5, backgroundColor: C.expertColors["idm_rule/s1"], boxShadow: `0 0 0 2.5px ${C.highlight.casing}` }} />
                </>}
                {i === 2 && <span style={{ padding: "8px 18px", borderRadius: 10, backgroundColor: ARCH_SCENE.colors.backbone, color: "#8FE0B0", fontSize: 20, fontWeight: 900 }}>PlanT-2-FT</span>}
              </div>
              <div style={{ position: "absolute", left: 32, right: 32, bottom: 26, paddingTop: 12, borderTop: `1px solid ${PAPER.rowLine}`, fontSize: 21, fontWeight: 800, color: col }}>{st.foot}</div>
            </div>
            {i < 2 && (
              <div style={{ position: "absolute", left: x + cardW + 18, top: 510, fontSize: 48, color: COLORS.faint, opacity: rise(t, TT.introSteps + (i + 1) * TT.introStepGap - 0.2, 0.4) }}>→</div>
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

// ─── 36,828: under the selection table (same slide) ──────────────────────────
const DatasetBeat: React.FC<{ t: number }> = ({ t }) => (
  <div style={{ position: "absolute", left: C.intro.tableLeft, top: 852, width: 660 }}>
    <div style={{ borderTop: `1px solid ${COLORS.border}`, paddingTop: 14, opacity: rise(t, TT.datasetCountReveal, 0.5) }}>
      <div style={{ fontSize: 20, color: COLORS.muted, fontWeight: 700 }}>{C.text.datasetAcross}</div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 14 }}>
        <span style={{ fontSize: 58, fontWeight: 900, lineHeight: 1.1, color: COLORS.ink }}>{C.text.datasetNumber}</span>
        <span style={{ fontSize: 24, fontWeight: 800, color: COLORS.ink }}>{C.text.datasetLabel}</span>
      </div>
    </div>
    <div style={{ display: "flex", alignItems: "baseline", gap: 12, opacity: rise(t, TT.datasetFT, 0.5) }}>
      <span style={{ fontSize: 24, fontWeight: 800, color: ARCH_SCENE.colors.supervision }}>{C.text.datasetFT}</span>
    </div>
  </div>
);

export const S10_FineTuning: React.FC<{ selectionScene?: string }> = ({ selectionScene }) => {
  const sel = SEL_SCENES[selectionScene ?? C.selection.scene];
  if (!sel) throw new Error(`unknown selection scene ${selectionScene ?? C.selection.scene}`);
  const t = useT() / FT_WARP; // section clock: the whole section, transitions included, plays FT_WARP× slower
  const tl = t - TT.archStart; // local time of the architecture half
  const partA = rise(t, TT.expertsAppear - 0.5, 0.5) * (1 - rise(t, TT.archStart - 0.5, 0.5));
  const tableOp = 1;
  const stage = t < TT.expertsAppear - 0.4 ? "intro" : t < TT.archStart - 0.2 ? "collect" : archStage(tl);
  // headline changes (opening → step 1 → architecture half) are softened
  const cueAt = (x: number) => (t < x - 0.4 || t > x + 0.2 ? 1 : 0.35);
  const titleOp = cueAt(TT.archStart) * cueAt(TT.expertsAppear - 0.4);

  return (
    <SelCtx.Provider value={sel}>
    <Scene>
      {/* header in the style of the latest slides: pill kicker, 50 px headline, muted subtitle */}
      <div style={{ position: "absolute", left: SIZE.margin, right: SIZE.margin, top: 44, opacity: rise(t, TT.title, 0.4) * titleOp }}>
        <div style={{ display: "inline-block", padding: "4px 14px", borderRadius: 999, ...PAPER.pill, color: COLORS.blue, fontSize: 13, fontWeight: 900, letterSpacing: 2.2, textTransform: "uppercase", marginBottom: 8 }}>{C.text.kickers[stage]}</div>
        <Headline size={50}>{C.text.titles[stage]}</Headline>
        <div style={{ marginTop: 6, color: COLORS.muted, fontSize: 24, fontWeight: 700 }}>{C.text.subtitles[stage]}</div>
      </div>


      <IntroBeat t={t} />

      {partA > 0 && (
        <AbsoluteFill style={{ opacity: partA }}>
          <ExpertMap t={t} />
          {tableOp > 0 && <div style={{ opacity: tableOp }}><SelectionTable t={t} /></div>}
          {t >= TT.datasetCountReveal - 0.2 && tableOp > 0 && <div style={{ opacity: tableOp }}><DatasetBeat t={t} /></div>}
        </AbsoluteFill>
      )}

      {tl >= -0.6 && <ArchitectureBody t={tl} scene={sel.id} />}
    </Scene>
    </SelCtx.Provider>
  );
};
