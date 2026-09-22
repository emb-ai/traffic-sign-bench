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

export const ARCH_SCENE = {
  // Local timeline of the architecture half of the fine-tuning section (seconds from its start).
  // It is played inside S10_FineTuning right after the expert selection (FT_SCENE.timing.archStart).
  durationSec: 19.2,

  timing: {
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
    expert: 7.7, // STEP 1: selected expert trajectory appears right after the heads
    targets: 8.0, // path / waypoint / speed targets derived from it
    match: 8.3, // prediction ···· target (training only)
    ftStart: 9.1, // orange supervision loop into PlanT-2 (draws in 1 s)
    ftModel: 10.1, // STEP 2: PlanT-2 → PlanT-2-FT inside the same diagram (label only)
    supFade: 10.6, // training-only graphics leave (expert panel, targets, dotted links, loop)
    result: 11.1, // result slide: rule compliance PlanT-2 → PlanT-2-FT (Table II)
    recenter: 99, // disabled: the diagram goes straight from PlanT-2-FT to the result slide
    _unused_recenter: 11.3, // remaining architecture slides to the centre; clean final frame holds to the end
  },


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
    metrics: [{ label: "SCD · sign compliance and destination reached", base: 5.9, ft: 72.3 }],
    groupTitle: "SCD by functional group",
    source: "Table II · held-out test scenarios",
    // cherry-picked test rollouts (reports/cherry_gifs/picked): PlanT-2 violates, PlanT-2-FT complies
    clipsTitle: "Test rollouts",
    // one pair per functional group; PlanT-2-FT = final checkpoint (nj e26) in every pair
    clips: [
      { label: "Priority · stop", base: "converted/cherry/stop_junc_249684220_plant2.mp4", ft: "converted/cherry/stop_junc_249684220_plant2_ft.mp4", rate: 1.8 },
      { label: "Speed · zone 30", base: "converted/cherry/zone_speed_limit_r76_plant2.mp4", ft: "converted/cherry/zone_speed_limit_r76_plant2_ft.mp4", rate: 1.5 },
      { label: "Obstacles · detour", base: "converted/cherry/detour_right_r102_plant2.mp4", ft: "converted/cherry/detour_right_r102_plant2_ft.mp4", rate: 1.4 },
      { label: "Routing · left or right", base: "converted/cherry/reroute_direction_left_right_r46_plant2.mp4", ft: "converted/cherry/reroute_direction_left_right_r46_plant2_ft.mp4", rate: 1.8 },
    ],
    clipsNote: "",
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
