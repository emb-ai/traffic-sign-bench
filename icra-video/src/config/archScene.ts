// ─────────────────────────────────────────────────────────────────────────────
// ARCHITECTURE HALF OF THE FINE-TUNING SECTION — every editable text, timing, colour and switch.
// Component: src/scenes/S11_ArchitectureFT.tsx (ArchitectureBody), played inside S10_FineTuning.
//
// Scientific grounding (verified 2026-09-21 against the code and the final run):
//  • Model: third_party/plant2/PlanT/model.py (HFLM.forward); final checkpoint nj_jt22_lr1e4_bs128_ld08 e26
//    (keep_ckpts/lr1e4_bs128_e26.ckpt: representation path+wps, path 20 pts, 8 waypoints, 8 speed bins,
//    input_bev = True, input_ego_speed = False).
//  • Inputs: one token per object box (class-specific projection tok_emb; every PDD sign code has its own
//    class), route token (route_emb, 20 route points), BEV raster token
//    (ResNet-18 on the road-semantics raster), sign-state token (sign_emb[sign_id], resolved once per route),
//    learned speed token (nn.Parameter, last position; read by ego_speed_classifier).
//    The base speed-limit token (speed_emb) is not shown: our dumps and the evaluation always feed 80 km/h.
//  • New parameters (147,976): 33 sign-class projections in tok_emb, sign_emb, speed_token, ego_speed_classifier.
//  • Targets (dataset.py + lit_module.py, settings from the final run's training log):
//    path  = expert's realised future over 40 frames, resampled every 1 m, 20 points (PATH_TARGET=future), L1;
//    waypoints = expert's next 8 positions (10 Hz, stride 1), L1;
//    speed = expert speed over the next frame (window 1 for 4.1.2) as a two-hot over 8 bins, cross-entropy.
//  • Data: one real training sample of the rank-1 selected trajectory (IDMe-s1) of scene c0 (sign 4.1.2),
//    ft_rl3 dump; built by tools/extract_arch_frames.py + tools/prepare_arch_assets.py.
// ─────────────────────────────────────────────────────────────────────────────

// Pace of the whole fine-tuning section: its clock runs FT_WARP times slower than real time, so reveal times AND
// every transition (e.g. the frame → architecture regrouping) are stretched together. 1 = the original silent cut.
export const FT_WARP = 1.6;
// Results slide: how long it holds after its reveal starts (real seconds).
const RESULTS_HOLD_SEC = 16;

// reveal times of the architecture half (section-clock seconds; real seconds = × FT_WARP)
const BASE_TIMING = {
  frame: 0.0, // real training frame (cross-fades in from the scenario map); it stays frozen
  objects: 0.5, // SCENE INPUTS: vehicles → object tokens
  signObject: 1.15, // the plate joins the SAME object sequence (own class projection)
  route: 1.8,
  map: 2.45, // local map raster (one BEV token)
  signState: 3.1, // SIGN-AWARE EXTENSIONS: persistent sign state (sign_emb, paper Sec. IV-D)
  speedToken: 3.75, // learned speed token (feeds the discrete ego-speed head)
  params: 4.2,
  archMorph: 4.9, // frame leaves, the same elements regroup into the architecture
  backbone: 6.1,
  outputs: 6.9,
  expert: 7.7, // selected expert trajectory appears right after the heads
  targets: 8.0, // path / waypoint / speed targets derived from it
  match: 8.3, // prediction ···· target (training only)
  ftStart: 9.1, // orange supervision loop into PlanT-2 (draws in 1 s)
  ftModel: 9.8, // PlanT-2 → PlanT-2-FT label cross-fade (see Model in S11_ArchitectureFT)
  supFade: 10.6, // training-only graphics leave (expert panel, targets, dotted links, loop)
  result: 11.1, // results: Table II numbers + one large PlanT-2 / PlanT-2-FT before/after pair
  recenter: 99, // disabled: the diagram goes straight from PlanT-2-FT to the results
};
export const ARCH_SCENE = {
  // Local timeline of the architecture half of the fine-tuning section (seconds from its start).
  // It is played inside S10_FineTuning right after the expert selection (FT_SCENE.timing.archStart).
  // section-clock seconds (see FT_WARP)
  durationSec: BASE_TIMING.result + RESULTS_HOLD_SEC / FT_WARP,

  timing: BASE_TIMING,

  // Dump frame of the IDMe-s1 trajectory that is decomposed (ego, 5 vehicles, plate 10 m ahead)
  frames: { main: 16 },
  // Ego-frame window of the large real frame (metres): forward / backward / to each side
  view: { fwd: 46, back: 22, side: 34 },

  text: {
    frameCaption: "real training frame · IDMe-s1 · sign 4.1.2",
    groupScene: "SCENE INPUTS",
    groupAdditions: "SIGN-AWARE EXTENSIONS",
    rows: { objects: "objects", route: "route", map: "local map" },
    signObject: "sign object",
    signObjectSub: "own object class per sign code",
    signState: "learned sign token", // paper: persistent sign-state token (sign_emb)
    signStateSub: "active class + posted value (4.1.2)",
    speedToken: "learned speed token",
    speedTokenSub: "feeds the discrete ego-speed head",
    localMapView: "local map view",
    params: "+147,976 params · +0.4%",
    backboneTitle: "PlanT-2",
    backboneSub: "",
    backboneNote: "backbone unchanged",
    outputs: ["PATH", "WAYPOINTS", "EGO SPEED"],
    expertTitle: "SELECTED EXPERT TRAJECTORY",
    targets: ["path target", "waypoint target", "speed target"],
    supervision: "TRAINING SUPERVISION",
    supervisionSub: "",
    ftCaption: "rule-supervised fine-tuning",
    ftModel: "PlanT-2-FT",
  },

  // Paper Table II (test scenarios), PlanT-2 vs PlanT-2-FT; group rows = GROUP_SCD in content.ts
  results: {
    metrics: [{ label: "SCD · sign compliance and destination reached", base: 5.9, ft: 72.3, gain: "+66.4 points" }],
    groupTitle: "SCD by functional group",
    source: "Table II · held-out test scenarios",
    // Table II overall SCD of all 17 evaluated planners (paper Sec. V-A: "within 7.7 points of the strongest
    // privileged expert (80.0%)")
    allTitle: "Overall SCD · all 17 planners",
    allPlanners: {
      standard: [7.2, 9.0, 9.0, 8.8, 8.9, 3.2, 2.9, 5.9], // IDM, IDM-s1..s4, PPO, CaRL, PlanT-2
      experts: [76.9, 64.8, 64.6, 64.3, 64.8, 77.4, 80.0, 67.3], // IDMe, IDMe-s1..s4, PPOe, CaRLe, PlanT-2e
      ft: 72.3,
    },
    // One uncluttered before/after pair from gifs/plant2/direction_s_l.
    clipsTitle: "Held-out rollout · same direction task",
    clips: [
      {
        group: "routing",
        label: "Mandatory direction · straight or left",
        base: "converted/plant2_direction_straight_left_base.mp4",
        ft: "converted/plant2_direction_straight_left_ft.mp4",
        rate: 1,
      },
    ],
    allLabels: {
      standard: "standard planners 2.9–9.0%",
      experts: "privileged experts 64.3–80.0%",
      gap: "PlanT-2-FT 72.3% · 7.7 points below the best expert, CaRLe 80.0%",
    },
  },

  colors: {
    road: "#DADADA",
    line: "#E0B000",
    car: "#8C97A6",
    ego: "#2458A6",
    route: "#2458A6",
    map: "#7D8A99",
    sign: "#D64533",
    state: "#D64533",
    learned: "#7B5EA7",
    backbone: "#23303F",
    expert: "#64B5CD", // IDMe-s1 colour in the selection scene
    supervision: "#C98A00",
    highlight: "#F2B705",
    ft: "#2E8B57",
    sceneGroupBg: "rgba(36, 88, 166, 0.06)",
    stateGroupBg: "rgba(214, 69, 51, 0.07)",
    learnedGroupBg: "rgba(123, 94, 167, 0.08)",
  },

  assets: {
    signIcon: "signs/direction_right.png", // 4.1.2 (project icon)
  },
};
