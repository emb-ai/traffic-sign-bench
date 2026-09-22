// ─────────────────────────────────────────────────────────────────────────────
// FINE-TUNING SECTION — every editable text, timing, colour, asset and switch.
// Component: src/scenes/S10_FineTuning.tsx (used by ICRA-Full and FineTuning-Preview).
//
// Scientific grounding (verified 2026-09-21):
//  • Part A data = ONE real training scene of the oracle collection
//    (direction_right / sign 4.1.2, scene dual_X_cluster_1879284932_1879285091, seed 3976813657):
//    all 8 privileged experts, their real outcomes, replays and the real top-2 pick
//    (collaborator data, read-only; extracted by tools/extract_expert_scene.py).
//  • Selection logic = traffic_bench/oracle/select/filter.py (select_expert_per_scene, top_n=2):
//      pass = no crash, no off-road, no target-sign violation, destination reached;
//      IDM family (5 variants) → one variant competes (code: best F-score; paper: fastest — identical here,
//      only IDMe-s1 succeeds); Q = F_β(time efficiency, comfort), β = 0.25; keep the top 2.
//  • Paper Sec. IV-C: 36,828 successful demonstrations over the 23,200 training scenes; fine-tuning uses a
//    balanced subset of 23,842 trajectories.
//  • Second half (architecture, frozen frame of the rank-1 trajectory IDMe-s1): src/config/archScene.ts.
// ─────────────────────────────────────────────────────────────────────────────

import { ARCH_SCENE } from "./archScene";

export const FT_SCENE = {
  // Total length of the section in seconds. ICRA-Full total must stay < 180 s.
  // Total length of the section: selection half (0 → timing.archStart) + architecture half
  // (ARCH_SCENE.durationSec, see archScene.ts). ICRA-Full picks it up through timing.ts.
  get durationSec() {
    return Math.ceil(this.timing.archStart + ARCH_SCENE.durationSec);
  },

  // Reveal times of the selection half (seconds from the start of the section)
  timing: {
    title: 0.0,
    expertsAppear: 0.3, // 8 rows + 8 trajectories start drawing
    filterStart: 1.0, // "Sign Compliance" column, row by row
    destReveal: 2.0, // "Destination" column, row by row (not before that trajectory finishes)
    expertsDrawn: 3.2, // all trajectories fully drawn
    failMute: 3.5, // unsuccessful rows and trajectories become muted
    selectionStart: 3.9, // Quality for the successful candidates
    selectionDecide: 4.6, // top 2 retained: warm rows + thicker/darker trajectories
    focusSelected: 5.4, // on the map only the rank-1 trajectory stays
    datasetCountReveal: 5.8, // under the table: across training scenarios → 36,828
    datasetFT: 6.6, // "→ rule-supervised fine-tuning"
    freezeMark: 7.2, // the training frame used next is marked on the selected trajectory
    archStart: 8.4, // the selection slide cross-fades into that frame
  },







  text: {
    kicker: "Rule-supervised fine-tuning",
    titles: {
      collect: "How training trajectories are collected",
      scene: "From scene to planner input",
      model: "Sign-aware PlanT-2",
      ft: "Rule-supervised fine-tuning",
      final: "Sign-aware PlanT-2-FT",
      result: "Fine-tuning raises rule compliance",
    },
    subtitles: {
      collect: "8 privileged experts per training scenario, filtered by sign compliance, destination and quality",
      scene: "The real scene becomes structured planner inputs",
      model: "Small sign-aware extensions on an unchanged PlanT-2 backbone",
      ft: "Selected expert trajectories supervise path, waypoints and speed",
      final: "Rule-supervised fine-tuning of PlanT-2",
      result: "PlanT-2 vs PlanT-2-FT on the test scenarios",
    },
    expertsTitle: "8 privileged expert planners",
    checkRule: "Sign Compliance",
    checkDest: "Destination",
    colExpert: "Expert",
    qualityTitle: "Quality",
    // paper Sec. IV-C: Q = F_beta(normalised speed, comfort), beta = 0.25, top 2 per scene
    qualityFormula: "F-score (speed, comfort),\nβ = 0.25",
    selectedLabel: "SELECTED",
    sumSuccessful: "successful",
    sumCandidates: "quality candidates",
    sumRetained: "selected",
    datasetAcross: "Across training scenarios",
    datasetNumber: "36,828",
    datasetLabel: "high-quality expert trajectories",
    datasetFT: "→ rule-supervised fine-tuning",
  },

  // Display names of the 8 privileged experts (paper naming, superscript e written as "e")
  expertNames: {
    "idm_rule/default": "IDMe",
    "idm_rule/s1": "IDMe-s1",
    "idm_rule/s2": "IDMe-s2",
    "idm_rule/s3": "IDMe-s3",
    "idm_rule/s4": "IDMe-s4",
    "ppo_rule/default": "PPOe",
    "carl_rule/default": "CaRLe",
    "plant2_rule/default": "PlanT-2e",
  } as Record<string, string>,

  // Expert-selection scenario (Part A). Scene files: public/finetune/scenes/<id>.json, built and verified
  // against the real pick record by tools/prepare_selection_scenes.py. Part B still uses the c0 input frames.
  selection: {
    scene: "c0",
    rejectedOpacity: 0.45, // rejected rows / trajectories stay readable
    scenes: {
      c0: { caption: "sign 4.1.2", signIcon: "signs/direction_right.png", freezeTrackIndex: 8, archFrame: 16 },
      c7: { caption: "sign 4.1.6", signIcon: "signs/direction_left_right.png", freezeTrackIndex: 0, archFrame: 0 },
      c4: { caption: "sign 4.3", signIcon: "signs/roundabout.png", freezeTrackIndex: 0, archFrame: 0 },
      // n04 / n15: one_way_right (5.7.1). n04 has real traffic (NPC tracks from the rank-1 replay), n15 has none.
      n04: { caption: "sign 5.7.1", signIcon: "signs/one_way_right.png", freezeTrackIndex: 6, archFrame: 12 },
      n15: { caption: "sign 5.7.1", signIcon: "signs/one_way_right.png", freezeTrackIndex: 12, archFrame: 24 },
    },
  },

  // Candidate colours: one distinct, restrained colour per expert (muted palette, no red/grey
  // so no line reads as "failure" or "road"); selected trajectories use the highlight style below
  expertColors: {
    "idm_rule/default": "#4C72B0", // blue
    "idm_rule/s1": "#64B5CD", // cyan
    "idm_rule/s2": "#8172B3", // violet
    "idm_rule/s3": "#937860", // brown
    "idm_rule/s4": "#C9B458", // olive
    "ppo_rule/default": "#55A868", // green
    "carl_rule/default": "#DD8452", // orange
    "plant2_rule/default": "#D884BE", // pink
  } as Record<string, string>,

  // Opening + selection beats (0 → datasetCountReveal): large map on the left, ONE selection table on
  // the right (Expert | Rule obeyed? | Destination reached? | Quality). Just before datasetCountReveal
  // the map morphs into the square left panel used by the dataset stage.
  intro: {
    map: { left: 90, top: 192, w: 1060, h: 840 }, // px on the 1920×1080 frame
    padM: 7, // metres of road around the 8 trajectories (view is then widened to the panel aspect)
    tableLeft: 1185, // selection table, runs to the right safe margin
    trackWidth: 4.2, // px
    morphSec: 0.8, // map morphs into the frozen-frame box (same place as the frame), ends at datasetCountReveal
  },

  highlight: {
    width: 7, // px on screen for selected trajectories
    casing: "#1A1A1A", // dark outline under selected trajectories
    candidateWidth: 3.2,
    fadedOpacity: 0.1,
  },


  // Visibility switches
  show: {
    qualityValues: true, // show the F-score numbers
  },
};
