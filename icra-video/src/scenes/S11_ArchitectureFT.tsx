// Architecture half of the fine-tuning section (played inside S10_FineTuning, right after the expert selection).
// One frozen real training frame → SCENE INPUTS (objects: vehicles + the sign object, which is an ordinary object
// token with its own class projection; route; local map) → SIGN-AWARE EXTENSIONS (persistent sign state; learned
// speed token read out by the SPEED head; +147,976 params) → the same elements regroup top-down:
// inputs → unchanged PlanT-2 backbone → PATH / WAYPOINTS / SPEED → training supervision from the SAME selected
// expert trajectory (real targets, dashed correspondence) → PlanT-2-FT → clean inference view.
// All data: public/finetune/arch/arch.json (real, verified by tools/prepare_arch_assets.py).
// Editable content: src/config/archScene.ts
import React from "react";
import { Img, OffthreadVideo, Sequence, staticFile } from "remotion";
import archC0 from "../../public/finetune/arch/c0.json";
import archN04 from "../../public/finetune/arch/n04.json";
import archN15 from "../../public/finetune/arch/n15.json";
import { ARCH_SCENE, FT_WARP } from "../config/archScene";
import { FT_SCENE } from "../config/fineTuningScene";
import { GROUP_SCD } from "../config/content";
import { PAPER } from "../config/paperStyle";
import { COLORS, GROUP, SIZE } from "../config/style";
import { ExpertLabel, rise, withExpertMarks } from "../lib/ui";

const C = ARCH_SCENE;
const TT = C.timing;
const K = C.colors;
const X = C.text;
type Arch = typeof archN04;
type Frame = Arch["frames"][number];
type Box = Frame["boxes"][number];
const ARCH = { c0: archC0, n04: archN04, n15: archN15 } as unknown as Record<string, Arch>;
const isEgo = (b: Box) => b.class === "car" && Math.abs(b.x) < 1e-3 && Math.abs(b.y) < 1e-3;
// the decomposed frame of the selected scene (real dump frame of its rank-1 trajectory) + labels
const sceneArch = (sid: string) => {
  const a = ARCH[sid];
  const cfg = FT_SCENE.selection.scenes[sid as keyof typeof FT_SCENE.selection.scenes];
  if (!a || !cfg) throw new Error(`no architecture data for scene ${sid}`);
  const MAIN = a.frames.find((x) => x.frame === cfg.archFrame);
  if (!MAIN) throw new Error(`frame ${cfg.archFrame} missing in arch/${sid}.json`);
  const SIGN = MAIN.boxes.find((b) => b.pdd_code);
  if (!SIGN) throw new Error(`no sign box in frame ${cfg.archFrame} of ${sid}`);
  return {
    MAIN, SIGN, CARS: MAIN.boxes.filter((b) => b.class === "car"), icon: cfg.signIcon, code: a.sign_code,
    expertName: FT_SCENE.expertNames[a.expert], expertColor: FT_SCENE.expertColors[a.expert],
  };
};
const ArchCtx = React.createContext<ReturnType<typeof sceneArch> | null>(null);
const useArch = () => {
  const v = React.useContext(ArchCtx);
  if (!v) throw new Error("ArchitectureBody: scene data missing");
  return v;
};
const mix = (a: number, b: number, m: number) => a + (b - a) * m;
type XY = { x: number; y: number };
const mixXY = (a: XY, b: XY, m: number) => ({ x: mix(a.x, b.x, m), y: mix(a.y, b.y, m) });
const fadeOut = (t: number, at: number, dur = 0.5) => 1 - rise(t, at, dur);
const pulseAt = (t: number, at: number) => rise(t, at, 0.3) * fadeOut(t, at + 0.8, 0.4);

// ─── frozen real frame (ego frame, forward up, right = right) ────────────────
export const FR = { left: SIZE.margin, top: 190, size: 830 };
const V = C.view;
const pxPerM = FR.size / (2 * V.side);
const egoToPx = (x: number, y: number): XY => ({ x: (y + V.side) * pxPerM, y: (V.fwd - x) * pxPerM });
const egoToAbs = (x: number, y: number): XY => {
  const p = egoToPx(x, y);
  return { x: FR.left + p.x, y: FR.top + p.y };
};
const pts = (arr: number[][]) => arr.map((q) => `${q[1]},${-q[0]}`).join(" "); // (x fwd, y right) → svg (y, -x)

const CarRect: React.FC<{ b: Box; fill: string; stroke?: string; sw?: number }> = ({ b, fill, stroke = "#1A1A1A", sw = 0.12 }) => {
  const [ex, ey] = b.extent as number[];
  return (
    <rect x={-ex} y={-ey} width={2 * ex} height={2 * ey} rx={0.35} fill={fill} stroke={stroke} strokeWidth={sw}
      transform={`translate(${b.y},${-b.x}) rotate(${(b.yaw * 180) / Math.PI - 90})`} />
  );
};

const FrozenFrame: React.FC<{ t: number }> = ({ t }) => {
  const { MAIN, CARS, SIGN, icon, code } = useArch();
  const f = MAIN;
  const hlCars = pulseAt(t, TT.objects);
  const routeOn = rise(t, TT.route, 0.4);
  const hlRoute = pulseAt(t, TT.route);
  const bevWin = rise(t, TT.map, 0.4);
  const hlSign = pulseAt(t, TT.signObject - 0.4);
  const signP = egoToPx(SIGN.x, SIGN.y);
  const half = f.bev_m / 2;
  return (
    <div style={{ position: "absolute", left: FR.left, top: FR.top, width: FR.size, height: FR.size, borderRadius: PAPER.cardRadius, overflow: "hidden", border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, backgroundColor: "#fff" }}>
      <svg width={FR.size} height={FR.size} viewBox={`${-V.side} ${-V.fwd} ${2 * V.side} ${V.fwd + V.back}`}>
        {f.lanes.map((L, i) => <polygon key={i} points={pts(L)} fill={K.road} stroke={K.road} strokeWidth={0.15} />)}
        {f.lines.map((L, i) => <polyline key={i} points={pts(L)} fill="none" stroke={K.line} strokeWidth={0.2} />)}
        {bevWin > 0 && <rect x={-half} y={-half} width={2 * half} height={2 * half} fill="none" stroke={K.map} strokeWidth={0.35} strokeDasharray="1.2 0.8" opacity={bevWin} />}
        {routeOn > 0 && <polyline points={pts(f.route)} fill="none" stroke={K.route} strokeWidth={0.55 + 0.6 * hlRoute} strokeLinecap="round" strokeLinejoin="round" opacity={routeOn} />}
        {f.scene_vehicles.filter((v) => !v.in_input).map((v, i) => (
          <CarRect key={`sv${i}`} b={{ class: "car", pdd_code: null, x: v.x, y: v.y, yaw: v.yaw, extent: v.extent } as Box} fill="#E3E6EA" stroke="#A7AEB8" />
        ))}
        {CARS.map((b, i) => (
          <g key={i}>
            {hlCars > 0 && <CarRect b={b} fill="none" stroke={K.highlight} sw={0.9 * hlCars} />}
            <CarRect b={b} fill={isEgo(b) ? K.ego : K.car} />
          </g>
        ))}
      </svg>
      {hlSign > 0 && <div style={{ position: "absolute", left: signP.x - 36, top: signP.y - 36, width: 72, height: 72, borderRadius: 36, border: `4px solid ${K.sign}`, boxSizing: "border-box", opacity: hlSign }} />}
      <Img src={staticFile(icon)} style={{ position: "absolute", left: signP.x - 20, top: signP.y - 20, width: 40, height: 40 }} />
      {bevWin > 0 && <div style={{ position: "absolute", left: egoToPx(half, -half).x + 8, top: egoToPx(half, -half).y + 6, fontSize: 17, color: K.map, fontWeight: 700, opacity: bevWin }}>{X.localMapView}</div>}
      <div style={{ position: "absolute", left: 16, top: 14, fontSize: 20, color: COLORS.muted, backgroundColor: "rgba(255,255,255,0.88)", padding: "4px 10px", borderRadius: 6 }}>{`sign ${code}`}</div>
    </div>
  );
};

// ─── layout: A = panel next to the frozen frame, B = left-to-right architecture ─
type Slot = { x: number; y: number; w: number; h: number };
const IN_X = 110;
const GA = { scene: { x: 960, y: 196 }, ext: { x: 960, y: 520 } };
const GB = { scene: { x: IN_X, y: 185 }, ext: { x: IN_X, y: 440 } };
const SA: Record<string, Slot> = {
  objects: { x: 960, y: 260, w: 52, h: 26 },
  route: { x: 960, y: 336, w: 410, h: 154 },
  map: { x: 1390, y: 336, w: 410, h: 154 },
  state: { x: 960, y: 566, w: 840, h: 86 },
  speed: { x: 960, y: 672, w: 840, h: 86 },
};
const SB: Record<string, Slot> = {
  objects: { x: IN_X, y: 220, w: 38, h: 22 },
  route: { x: IN_X, y: 265, w: 140, h: 96 },
  map: { x: IN_X + 154, y: 265, w: 96, h: 96 },
  state: { x: IN_X, y: 480, w: 390, h: 84 },
  speed: { x: IN_X, y: 585, w: 390, h: 84 },
};
const PARAMS = { a: { x: 960, y: 782 }, b: { x: IN_X, y: 692 } };
const slot = (k: string, m: number): Slot => ({
  x: mix(SA[k].x, SB[k].x, m), y: mix(SA[k].y, SB[k].y, m), w: mix(SA[k].w, SB[k].w, m), h: mix(SA[k].h, SB[k].h, m),
});
const Caps: React.FC<{ x: number; y: number; text: string; color: string; op: number; size?: number }> = ({ x, y, text, color, op, size = 20 }) => (
  <div style={{ position: "absolute", left: x, top: y, fontSize: size, fontWeight: 900, letterSpacing: 1.6, color, opacity: op, whiteSpace: "nowrap" }}>{text}</div>
);
const Small: React.FC<{ x: number; y: number; text: string; op: number; color?: string; size?: number }> = ({ x, y, text, op, color = COLORS.muted, size = 17 }) => (
  <div style={{ position: "absolute", left: x, top: y, fontSize: size, fontWeight: 700, color, opacity: op, whiteSpace: "nowrap" }}>{text}</div>
);
const box = (s: Slot, border: string, bg = "#fff", dashed = false): React.CSSProperties => ({
  position: "absolute", left: s.x, top: s.y, width: s.w, height: s.h, borderRadius: 14, boxSizing: "border-box",
  border: `2px ${dashed ? "dashed" : "solid"} ${border}`, backgroundColor: bg, overflow: "hidden", boxShadow: PAPER.cardShadow,
});
const MiniPath: React.FC<{ route: number[][]; w: number; h: number; color: string; ppm?: number; dots?: boolean }> = ({ route, w, h, color, ppm, dots }) => {
  const s = ppm ?? Math.min(w / 16, (h - 14) / 21);
  const P = route.map((q) => [w / 2 + q[1] * s, h - 8 - q[0] * s]);
  return (
    <svg width={w} height={h} style={{ position: "absolute", left: 0, top: 0 }}>
      <rect x={w / 2 - 4} y={h - 14} width={8} height={12} rx={2} fill={K.ego} />
      {dots ? P.map((p, i) => <circle key={i} cx={p[0]} cy={p[1]} r={3.4} fill={color} />)
        : <polyline points={[[w / 2, h - 8], ...P].map((p) => p.join(",")).join(" ")} fill="none" stroke={color} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />}
    </svg>
  );
};
const Card: React.FC<{ s: Slot; m: number; color: string; title: string; sub: string; op: number; dashed?: boolean; tint?: string }> = ({ s, m, color, title, sub, op, dashed, tint = "#fff" }) => (
  <div style={{ ...box(s, color, tint, dashed), opacity: op, display: "flex", alignItems: "center", gap: 16, padding: "0 22px" }}>
    <div style={{ width: s.h - 30, height: s.h - 30, borderRadius: "50%", flexShrink: 0, boxSizing: "border-box", ...(dashed ? { border: `3.5px dashed ${color}` } : { backgroundColor: color }) }} />
    <div style={{ lineHeight: 1.15 }}>
      <div style={{ fontSize: mix(25, 20, m), fontWeight: 900, color }}>{title}</div>
      <div style={{ fontSize: mix(18, 15, m), color: COLORS.muted }}>{sub}</div>
    </div>
  </div>
);

const Inputs: React.FC<{ t: number; m: number; clean: number }> = ({ t, m, clean }) => {
  const { MAIN, CARS, SIGN, icon, code } = useArch();
  const fly = (at: number, from: XY, to: XY) => {
    const p = rise(t, at, 0.75);
    return { p, pos: mixXY(from, to, p) };
  };
  const oS = slot("objects", m);
  const step = oS.w + 8;
  const objChips = CARS.map((b, i) => {
    const { p, pos } = fly(TT.objects + 0.25 + i * 0.07, egoToAbs(b.x, b.y), { x: oS.x + i * step, y: oS.y });
    if (p <= 0) return null;
    return (
      <div key={i} style={{ position: "absolute", left: pos.x, top: pos.y, width: oS.w, height: oS.h, borderRadius: 5, backgroundColor: isEgo(b) ? K.ego : K.car, border: "1.5px solid #1A1A1A", boxSizing: "border-box", opacity: Math.min(1, p * 3) }}>
        <div style={{ position: "absolute", right: "18%", top: "18%", bottom: "18%", width: "16%", borderRadius: 2, backgroundColor: "rgba(255,255,255,0.6)" }} />
      </div>
    );
  });
  // the sign object: same object sequence as the vehicles (red ring = its own, new class projection)
  const d = oS.h + 16;
  const sg = fly(TT.signObject, egoToAbs(SIGN.x, SIGN.y), { x: oS.x + CARS.length * step + 4, y: oS.y - 7 });
  const rS = slot("route", m);
  const rF = fly(TT.route + 0.25, egoToAbs(10, 0), rS);
  const mS = slot("map", m);
  const mF = fly(TT.map + 0.25, egoToAbs(0, 0), mS);
  const gS = mixXY(GA.scene, GB.scene, m);
  const gE = mixXY(GA.ext, GB.ext, m);
  const pr = mixXY(PARAMS.a, PARAMS.b, m);
  return (
    <>
      <Caps x={gS.x} y={gS.y} text={X.groupScene} color={K.route} op={rise(t, TT.objects - 0.4, 0.4)} size={mix(24, 18, m)} />
      <Small x={oS.x} y={oS.y - 30} text={X.rows.objects} op={rise(t, TT.objects, 0.4) * (1 - m)} size={18} />
      <Small x={rS.x} y={rS.y - 28} text={X.rows.route} op={rise(t, TT.route, 0.4) * (1 - m)} size={18} />
      <Small x={mS.x} y={mS.y - 28} text={X.rows.map} op={rise(t, TT.map, 0.4) * (1 - m)} size={18} />
      {objChips}
      {sg.p > 0 && (
        <div style={{ position: "absolute", left: sg.pos.x, top: sg.pos.y, width: d, height: d, borderRadius: "50%", border: `3px solid ${K.sign}`, boxSizing: "border-box", backgroundColor: "#fff", opacity: Math.min(1, sg.p * 2), display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Img src={staticFile(icon)} style={{ width: d - 8, height: d - 8 }} />
        </div>
      )}
      {sg.p > 0 && (
        <div style={{ position: "absolute", left: sg.pos.x + d + 8, top: sg.pos.y + d / 2 - mix(22, 17, m), lineHeight: 1.15, whiteSpace: "nowrap", opacity: rise(t, TT.signObject + 0.6, 0.4) }}>
          <div style={{ fontSize: mix(22, 17, m), fontWeight: 800, color: K.sign }}>{X.signObject}</div>
          <div style={{ fontSize: mix(17, 14, m), fontWeight: 600, color: COLORS.muted }}>{X.signObjectSub}</div>
        </div>
      )}
      {rF.p > 0 && (
        <div style={{ ...box({ x: rF.pos.x, y: rF.pos.y, w: rS.w, h: rS.h }, K.route), opacity: rF.p }}>
          <MiniPath route={MAIN.route} w={rS.w} h={rS.h} color={K.route} />
        </div>
      )}
      {mF.p > 0 && (
        <div style={{ ...box({ x: mF.pos.x, y: mF.pos.y, w: mS.w, h: mS.h }, K.map), opacity: mF.p }}>
          <Img src={staticFile(MAIN.bev)} style={{ width: "100%", height: "100%" }} />
        </div>
      )}

      <Caps x={gE.x} y={gE.y} text={X.groupAdditions} color={K.sign} op={rise(t, TT.signState - 0.3, 0.4)} size={mix(24, 18, m)} />
      <Card s={slot("state", m)} m={m} color={K.state} title={X.signState} sub={`active sign ${code} · persists`} op={rise(t, TT.signState, 0.5)} tint="rgba(214, 69, 51, 0.07)" />
      <Card s={slot("speed", m)} m={m} color={K.learned} title={X.speedToken} sub={X.speedTokenSub} op={rise(t, TT.speedToken, 0.5)} dashed />
      <div style={{
        position: "absolute", left: pr.x, top: pr.y,
        padding: mix(12, 6, m) + "px " + mix(20, 14, m) + "px",
        borderRadius: mix(14, 9, m),
        backgroundColor: "rgba(214, 69, 51, 0.08)",
        border: "1.5px solid rgba(214, 69, 51, 0.28)",
        display: "inline-flex", alignItems: "center", gap: mix(14, 8, m),
        opacity: rise(t, TT.params, 0.5) * clean,
      }}>
        <span style={{ fontSize: mix(24, 18, m), fontWeight: 900, color: K.sign }}>{X.params}</span>
        {m < 0.3 && <span style={{ fontSize: 17, fontWeight: 700, color: COLORS.muted }}>backbone unchanged</span>}
      </div>
    </>
  );
};

// ─── architecture (left → right): inputs → unchanged backbone → heads ──────
const BB = { x: 550, y: 205, w: 300, h: 580 };
const OUT = { x: 920, w: 250, h: 140, ys: [205, 425, 645] };
const TGX = 1240; // training targets, right of the heads
const EXP = { x: 1540, y: 205, w: 300, h: 580 };
const LINK_Y = 890; // gold fine-tuning link runs below the diagram

const OutGlyph: React.FC<{ k: number; color: string }> = ({ k, color }) => {
  const w = 124;
  const h = 38;
  if (k === 0) return <svg width={w} height={h}><path d={`M 4 ${h - 4} C 44 ${h - 8}, 80 ${h - 22}, ${w - 4} 4`} fill="none" stroke={color} strokeWidth={4} strokeLinecap="round" /></svg>;
  if (k === 1) return <svg width={w} height={h}>{Array.from({ length: 8 }, (_, i) => <circle key={i} cx={8 + i * 16} cy={h - 6 - i * 3.6} r={4.2} fill={color} />)}</svg>;
  return <svg width={w} height={h}>{Array.from({ length: 8 }, (_, i) => <rect key={i} x={4 + i * 15} y={4} width={11} height={h - 8} rx={2.5} fill="none" stroke={color} strokeWidth={2.4} />)}</svg>;
};

const Model: React.FC<{ t: number; clean: number }> = ({ t, clean }) => {
  const bOp = rise(t, TT.backbone, 0.6);
  const ft = rise(t, TT.ftModel, 0.6);
  const flow = rise(t, TT.backbone + 0.2, 0.5);
  const oOp = (i: number) => rise(t, TT.outputs + i * 0.25, 0.5);
  const grey = "#8A94A3";
  return (
    <>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        <defs>
          <marker id="ah" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0,1 L18,9 L0,17 z" fill={grey} /></marker>
          <marker id="ahr" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0,1 L18,9 L0,17 z" fill={K.sign} /></marker>
          <marker id="ahp" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0,1 L18,9 L0,17 z" fill={K.learned} /></marker>
        </defs>
        <g opacity={flow}>
          <line x1={SB.state.x + SB.state.w + 8} y1={SB.route.y + SB.route.h / 2} x2={BB.x - 3} y2={SB.route.y + SB.route.h / 2} stroke={grey} strokeWidth={3} markerEnd="url(#ah)" />
          <line x1={SB.state.x + SB.state.w + 8} y1={SB.state.y + SB.state.h / 2} x2={BB.x - 3} y2={SB.state.y + SB.state.h / 2} stroke={K.sign} strokeWidth={3} markerEnd="url(#ahr)" />
          <line x1={SB.state.x + SB.state.w + 8} y1={SB.speed.y + SB.speed.h / 2} x2={BB.x - 3} y2={SB.speed.y + SB.speed.h / 2} stroke={K.learned} strokeWidth={3} markerEnd="url(#ahp)" />
        </g>
        {OUT.ys.map((y, i) => (
          <line key={i} x1={BB.x + BB.w + 6} y1={y + OUT.h / 2} x2={OUT.x - 3} y2={y + OUT.h / 2} stroke={i === 2 ? K.learned : grey} strokeWidth={3} markerEnd={i === 2 ? "url(#ahp)" : "url(#ah)"} opacity={oOp(i)} />
        ))}
      </svg>
      <div style={{ position: "absolute", left: BB.x, top: BB.y, width: BB.w, height: BB.h, borderRadius: 22, backgroundColor: K.backbone, opacity: bOp, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: "#fff", boxShadow: PAPER.cardShadow }}>
        <div style={{ fontSize: 44, fontWeight: 900, color: ft > 0.5 ? "#8FE0B0" : "#fff" }}>{ft > 0.5 ? X.ftModel : X.backboneTitle}</div>
        {X.backboneSub && <div style={{ fontSize: 18, opacity: 0.88, marginTop: 8, textAlign: "center", padding: "0 14px", lineHeight: 1.3 }}>{X.backboneSub}</div>}
        <div style={{ position: "absolute", bottom: 22, fontSize: 17, fontWeight: 800, letterSpacing: 0.8, opacity: 0.85 * rise(t, TT.backbone + 0.6, 0.5) }}>{X.backboneNote}</div>
      </div>
      {X.outputs.map((o, i) => (
        <div key={o} style={{ ...box({ x: OUT.x, y: OUT.ys[i], w: OUT.w, h: OUT.h }, i === 2 ? K.learned : K.backbone), opacity: oOp(i), display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", gap: 10 }}>
          <div style={{ fontSize: 24, fontWeight: 900, letterSpacing: 1.5, color: i === 2 ? K.learned : COLORS.ink }}>{o}</div>
          <OutGlyph k={i} color={i === 2 ? K.learned : K.backbone} />
        </div>
      ))}
    </>
  );
};

// ─── training supervision: same selected expert trajectory → real targets ····· heads ──
const Supervision: React.FC<{ t: number }> = ({ t }) => {
  const { MAIN, CARS, expertName, expertColor } = useArch();
  const op = rise(t, TT.expert, 0.6) * fadeOut(t, TT.supFade, 0.6);
  if (op <= 0) return null;
  const f = MAIN;
  const ev = { fwd: 26, back: 4 };
  const s = EXP.h / (ev.fwd + ev.back);
  const side = EXP.w / 2 / s;
  const draw = rise(t, TT.expert + 0.3, 1.0);
  const fut = f.expert_future.slice(0, Math.max(2, Math.round(draw * f.expert_future.length)));
  const tOp = (i: number) => rise(t, TT.targets + i * 0.3, 0.5);
  const mOp = (i: number) => rise(t, TT.match + i * 0.25, 0.4);
  const two = f.targets.speed_two_hot;
  const gold = K.supervision;
  const bx = EXP.x - 22; // bracket between the expert panel and the targets
  const ftLink = rise(t, TT.ftStart, 1.0);
  const ftOp = rise(t, TT.ftStart, 0.3);
  return (
    <div style={{ opacity: op }}>
      <div style={{ position: "absolute", left: EXP.x, width: EXP.w, textAlign: "right", top: EXP.y - 28, fontSize: 17, fontWeight: 900, letterSpacing: 1.2, color: gold }}>{X.expertTitle}</div>
      <div style={{ ...box(EXP, gold) }}>
        <svg width={EXP.w} height={EXP.h} viewBox={`${-side} ${-ev.fwd} ${2 * side} ${ev.fwd + ev.back}`}>
          {f.lanes.map((L, i) => <polygon key={i} points={pts(L)} fill={K.road} stroke={K.road} strokeWidth={0.15} />)}
          <polyline points={pts(fut)} fill="none" stroke="#1A1A1A" strokeWidth={1.3} strokeLinecap="round" strokeLinejoin="round" />
          <polyline points={pts(fut)} fill="none" stroke={expertColor} strokeWidth={0.8} strokeLinecap="round" strokeLinejoin="round" />
          {CARS.filter(isEgo).map((b, i) => <CarRect key={i} b={b} fill={K.ego} />)}
        </svg>
        <div style={{ position: "absolute", right: 12, bottom: 10, fontSize: 16, color: COLORS.muted }}>
          <ExpertLabel name={expertName} /> · next 4 s
        </div>
      </div>
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        <defs>
          <marker id="ag" markerUnits="userSpaceOnUse" markerWidth="14" markerHeight="14" refX="13" refY="7" orient="auto"><path d="M0,1 L14,7 L0,13 z" fill={gold} /></marker>
        </defs>
        {/* expert trajectory → targets (derivation) */}
        <g opacity={tOp(0)}>
          <line x1={EXP.x - 4} y1={EXP.y + EXP.h / 2} x2={bx} y2={EXP.y + EXP.h / 2} stroke={gold} strokeWidth={3} />
          <line x1={bx} y1={OUT.ys[0] + OUT.h / 2} x2={bx} y2={OUT.ys[2] + OUT.h / 2} stroke={gold} strokeWidth={3} />
          {OUT.ys.map((y, i) => <line key={i} x1={bx} y1={y + OUT.h / 2} x2={TGX + OUT.w + 1} y2={y + OUT.h / 2} stroke={gold} strokeWidth={3} markerEnd="url(#ag)" />)}
        </g>
        {/* prediction ···· target (training correspondence, no arrowheads) */}
        {OUT.ys.map((y, i) => (
          <line key={i} x1={OUT.x + OUT.w + 6} y1={y + OUT.h / 2} x2={TGX - 6} y2={y + OUT.h / 2} stroke={gold} strokeWidth={3} strokeDasharray="3 7" strokeLinecap="round" opacity={mOp(i)} />
        ))}
      </svg>
      {X.targets.map((name, i) => (
        <div key={name} style={{ ...box({ x: TGX, y: OUT.ys[i], w: OUT.w, h: OUT.h }, gold, "#FFFBF0", true), opacity: tOp(i) }}>
          <div style={{ position: "absolute", left: 16, top: 10, fontSize: 18, fontWeight: 900, color: gold }}>{name}</div>
          {i < 2 && (
            <div style={{ position: "absolute", left: 134, top: 8, width: 96, height: 100 }}>
              <MiniPath route={i === 0 ? f.targets.path : f.targets.waypoints} w={96} h={100} color={gold} dots={i === 1} ppm={i === 0 ? 3.8 : 13} />
            </div>
          )}
          {i === 2 && (
            <div style={{ position: "absolute", left: 16, top: 46, display: "flex", alignItems: "flex-end", gap: 5 }}>
              {two.map((v, j) => (
                <div key={j} style={{ width: 13, height: 56, borderRadius: 3, border: `2px solid ${gold}`, boxSizing: "border-box", position: "relative", backgroundColor: "#fff" }}>
                  <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: `${v * 100}%`, backgroundColor: gold }} />
                </div>
              ))}
              <div style={{ fontSize: 19, fontWeight: 800, marginLeft: 10, whiteSpace: "nowrap" }}>{f.targets.speed_mps.toFixed(1)} m/s</div>
            </div>
          )}
        </div>
      ))}
      {/* training supervision → rule-supervised fine-tuning of the (unchanged) planner */}
      <svg width={1920} height={1080} style={{ position: "absolute", left: 0, top: 0 }}>
        <defs>
          <marker id="agf" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" refX="17" refY="9" orient="auto"><path d="M0,1 L18,9 L0,17 z" fill={gold} /></marker>
        </defs>
        <path d={`M ${(OUT.x + TGX + OUT.w) / 2} ${OUT.ys[2] + OUT.h + 46} L ${(OUT.x + TGX + OUT.w) / 2} ${LINK_Y} L ${BB.x + BB.w / 2} ${LINK_Y} L ${BB.x + BB.w / 2} ${BB.y + BB.h + 10}`}
          fill="none" stroke={gold} strokeWidth={3.5} markerEnd="url(#agf)" strokeDasharray={`${ftLink * 1600} 1600`} opacity={ftOp} />
      </svg>
      <div style={{ position: "absolute", left: BB.x + BB.w / 2 + 18, top: LINK_Y + 12, fontSize: 26, fontWeight: 800, color: gold, opacity: ftOp * rise(t, TT.ftStart + 0.5, 0.4), whiteSpace: "nowrap" }}>{X.ftCaption}</div>
      <div style={{ position: "absolute", left: OUT.x, width: TGX + OUT.w - OUT.x, top: OUT.ys[2] + OUT.h + 20, textAlign: "center", fontSize: 22, fontWeight: 900, letterSpacing: 1.4, color: gold, opacity: mOp(0) }}>{X.supervision}
        {X.supervisionSub && <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: 0, color: COLORS.muted, marginTop: 4 }}>{X.supervisionSub}</div>}
      </div>
    </div>
  );
};

// ─── results: Table II (overall, groups, all 17 planners) + one PlanT-2 / PlanT-2-FT test pair per group ─────
const GREEN = "#2E8B57";
const GREY = "#9AA3AE";
// real-time frame of the section at which a clip starts (the section clock runs FT_WARP× slower)
const clipFrom = (tSection: number) => Math.round((FT_SCENE.timing.archStart + tSection) * FT_WARP * 30);
const ResultsBeat: React.FC<{ t: number }> = ({ t }) => {
  const R = C.results;
  const T0 = TT.result;
  const op = rise(t, T0, 0.6);
  if (op <= 0) return null;
  const m = R.metrics[0];
  const pNum = rise(t, T0 + 0.5, 0.8);
  const barW = 440;
  return (
    <div style={{ opacity: op }}>
      {/* overall SCD */}
      <div style={{ position: "absolute", left: SIZE.margin, width: 1020, top: 200, boxSizing: "border-box", padding: "24px 32px", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, borderTop: `5px solid ${GREEN}`, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: rise(t, T0 + 0.3, 0.4) }}>
        <div style={{ ...PAPER.sectionLabel, color: COLORS.blue }}>{m.label}</div>
        <div style={{ display: "flex", alignItems: "baseline", gap: 20, marginTop: 6 }}>
          <span style={{ fontSize: 46, fontWeight: 800, color: GREY }}>{m.base.toFixed(1)}%</span>
          <span style={{ fontSize: 36, color: COLORS.faint }}>→</span>
          <span style={{ fontSize: 104, fontWeight: 900, color: GREEN, fontVariantNumeric: "tabular-nums", lineHeight: 1.05 }}>{(m.base + (m.ft - m.base) * pNum).toFixed(1)}%</span>
          <span style={{ fontSize: 30, fontWeight: 800, color: COLORS.muted, opacity: rise(t, T0 + 1.3, 0.4) }}>{m.gain}</span>
        </div>
        <div style={{ fontSize: 18, color: COLORS.muted, marginTop: 2 }}>PlanT-2 → PlanT-2-FT · all 29 scenario types</div>
      </div>

      {/* group SCD in the colours of the semantic groups */}
      <div style={{ position: "absolute", left: SIZE.margin, width: 1020, top: 420, boxSizing: "border-box", padding: "22px 32px", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: rise(t, T0 + 1.6, 0.5) }}>
        <div style={{ ...PAPER.sectionLabel, color: COLORS.blue, marginBottom: 8 }}>{R.groupTitle}</div>
        {GROUP_SCD.map((g, i) => {
          const p = rise(t, T0 + 2.0 + i * 0.2, 0.7);
          const gc = GROUP[g.key];
          return (
            <div key={g.key} style={{ display: "flex", alignItems: "center", height: 64 }}>
              <div style={{ width: 150, fontSize: 24, fontWeight: 800, color: gc.text }}>{g.label}</div>
              <div style={{ position: "relative", width: barW, height: 44 }}>
                <div style={{ position: "absolute", left: 0, top: 4, height: 15, width: (barW * g.base) / 100, backgroundColor: GREY, borderRadius: 4 }} />
                <div style={{ position: "absolute", left: 0, top: 24, height: 17, width: (barW * g.ft * p) / 100, backgroundColor: gc.bar, borderRadius: 4 }} />
              </div>
              <div style={{ marginLeft: 22, fontSize: 23, color: GREY, fontWeight: 700, width: 90, fontVariantNumeric: "tabular-nums" }}>{g.base.toFixed(1)}%</div>
              <div style={{ fontSize: 22, color: COLORS.faint, width: 40 }}>→</div>
              <div style={{ fontSize: 27, color: gc.text, fontWeight: 900, fontVariantNumeric: "tabular-nums", opacity: p }}>{g.ft.toFixed(1)}%</div>
            </div>
          );
        })}
        <div style={{ position: "absolute", right: 32, top: 22, display: "flex", gap: 22, fontSize: 18, color: COLORS.muted }}>
          <span><span style={{ display: "inline-block", width: 22, height: 10, backgroundColor: GREY, borderRadius: 3, marginRight: 8 }} />PlanT-2</span>
          <span><span style={{ display: "inline-block", width: 22, height: 10, background: `linear-gradient(90deg, ${GROUP.priority.bar} 0 25%, ${GROUP.speed.bar} 25% 50%, ${GROUP.obstacles.bar} 50% 75%, ${GROUP.routing.bar} 75%)`, borderRadius: 3, marginRight: 8 }} />PlanT-2-FT</span>
        </div>
      </div>
      <AllPlanners t={t} x={SIZE.margin} y={785} w={1020} />
      <div style={{ position: "absolute", left: SIZE.margin, top: 1030, fontSize: 17, color: COLORS.faint }}>{R.source}</div>

      {/* one test pair per functional group: PlanT-2 (top) vs PlanT-2-FT (bottom) */}
      <div style={{ position: "absolute", left: 1140, top: 200, width: 700, opacity: rise(t, T0 + 1.0, 0.5) }}>
        <div style={{ ...PAPER.sectionLabel, color: COLORS.blue, marginBottom: 10 }}>{R.clipsTitle}</div>
        <div style={{ display: "flex", gap: 13 }}>
          {R.clips.map((c) => (
            <div key={c.label} style={{ width: 165 }}>
              <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6, whiteSpace: "nowrap", color: GROUP[c.group as keyof typeof GROUP].text }}>{c.label}</div>
              {([["PlanT-2", c.base, GREY], ["PlanT-2-FT", c.ft, GREEN]] as const).map(([name, src, col]) => (
                <div key={name} style={{ marginBottom: 8 }}>
                  <div style={{ width: 165, height: 335, borderRadius: 12, overflow: "hidden", border: `3px solid ${col}`, boxSizing: "border-box", backgroundColor: "#fff" }}>
                    <Sequence from={clipFrom(T0 + 1.0)} layout="none">
                      <OffthreadVideo src={staticFile(src)} muted playbackRate={c.rate} style={{ width: 324, height: 324, marginLeft: -79 }} />
                    </Sequence>
                  </div>
                  <div style={{ fontSize: 15, fontWeight: 800, color: col, marginTop: 2 }}>{name}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// ─── overall SCD of all 17 planners on one 0–100 axis (Table II) ─────────────
const AllPlanners: React.FC<{ t: number; x: number; y: number; w: number }> = ({ t, x: X, y: Y, w: CW }) => {
  const R = C.results;
  const A = R.allPlanners;
  const T0 = TT.result + 3.2;
  const W = CW - 56;
  const x = (v: number) => (W * v) / 100;
  const dot = (v: number, i: number, col: string, at: number, r = 9) => (
    <div key={`${col}${i}`} style={{ position: "absolute", left: x(v) - r, top: 56 - r, width: 2 * r, height: 2 * r, borderRadius: r, backgroundColor: col, border: "2px solid #fff", boxSizing: "border-box", opacity: rise(t, at, 0.3) }} />
  );
  const gold = K.supervision;
  const expMax = Math.max(...A.experts);
  return (
    <div style={{ position: "absolute", left: X, width: CW, top: Y, height: 210, boxSizing: "border-box", padding: "20px 28px", borderRadius: PAPER.cardRadius, border: PAPER.cardBorder, boxShadow: PAPER.cardShadow, backgroundColor: "#fff", opacity: rise(t, T0, 0.5) }}>
      <div style={{ ...PAPER.sectionLabel, color: COLORS.blue }}>{R.allTitle}</div>
      <div style={{ position: "relative", marginTop: 8, height: 130 }}>
        <div style={{ position: "absolute", left: 0, width: W, top: 55, height: 2, backgroundColor: COLORS.border }} />
        {[0, 25, 50, 75, 100].map((v) => (
          <div key={v} style={{ position: "absolute", left: x(v) - 20, width: 40, top: 70, textAlign: "center", fontSize: 15, color: COLORS.faint }}>{v}%</div>
        ))}
        {A.standard.map((v, i) => dot(v, i, GREY, T0 + 0.2 + i * 0.04))}
        {A.experts.map((v, i) => dot(v, i, gold, T0 + 0.6 + i * 0.04))}
        {dot(A.ft, 0, GREEN, T0 + 1.1, 14)}
        <div style={{ position: "absolute", left: x(A.ft), width: x(expMax) - x(A.ft), top: 22, height: 14, borderTop: `2px solid ${GREEN}`, borderLeft: `2px solid ${GREEN}`, borderRight: `2px solid ${GREEN}`, boxSizing: "border-box", opacity: rise(t, T0 + 1.6, 0.4) }} />
        <div style={{ position: "absolute", left: 0, top: 96, fontSize: 18, fontWeight: 800, color: "#7A8594", opacity: rise(t, T0 + 0.4, 0.4) }}>{R.allLabels.standard}</div>
        <div style={{ position: "absolute", left: x(42), top: 96, fontSize: 18, fontWeight: 800, color: gold, opacity: rise(t, T0 + 0.8, 0.4) }}>{R.allLabels.experts}</div>
        <div style={{ position: "absolute", right: 0, top: -31, fontSize: 18, fontWeight: 800, color: GREEN, textAlign: "right", whiteSpace: "nowrap", opacity: rise(t, T0 + 1.6, 0.4) }}>{withExpertMarks(R.allLabels.gap)}</div>
      </div>
    </div>
  );
};

// ─── body (local time t, seconds from the start of the architecture half) ────
export const ArchitectureBody: React.FC<{ t: number; scene: string }> = ({ t, scene }) => {
  const data = React.useMemo(() => sceneArch(scene), [scene]);
  const m = rise(t, TT.archMorph, 1.6);
  const frameOp = rise(t, TT.frame - 0.5, 0.5) * fadeOut(t, TT.archMorph - 0.1, 0.6);
  // after the training graphics leave, the inference diagram (inputs x≈110 … heads x≈1150) is centred
  const shift = 250 * rise(t, TT.recenter, 0.7);
  const archOut = fadeOut(t, TT.result - 0.4, 0.5); // architecture gives way to the results
  return (
    <ArchCtx.Provider value={data}>
      {frameOp > 0 && <div style={{ opacity: frameOp }}><FrozenFrame t={t} /></div>}
      <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transform: `translateX(${shift}px)`, opacity: archOut }}>
        <Inputs t={t} m={m} clean={1} />
        {t >= TT.backbone - 0.2 && <Model t={t} clean={1} />}
      </div>
      <Supervision t={t} />
      <ResultsBeat t={t} />
    </ArchCtx.Provider>
  );
};

// titles of the architecture half (the selection half has its own)
export const archStage = (t: number): "scene" | "model" | "ft" | "final" | "result" =>
  t < TT.archMorph ? "scene" : t < TT.expert ? "model" : t < TT.supFade ? "ft" : t < TT.result - 0.2 ? "final" : "result";
