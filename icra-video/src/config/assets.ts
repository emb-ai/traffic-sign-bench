// ─────────────────────────────────────────────────────────────────────────────
// ASSETS — every file used by the video, relative to public/.
// All simulator clips are REAL project rollouts converted GIF → MP4 with ffmpeg
// (fps=30, 800×800, no speed change). Provenance in ASSET_INDEX.md.
// "Replace only the Routing video" = change one path here.
// ─────────────────────────────────────────────────────────────────────────────

export const CLIPS = {
  // Hook: PlanT-2 baseline entering a no-entry road (docs demo pair, sign 3.1)
  hook_plant2_no_entry: "converted/pair_3_1_plant2_base.mp4",
  // Benchmark overview cards (one clip per semantic group)
  group_priority_yield: "converted/ft_n2_yield_junc_1015545863.mp4",
  group_speed_limit: "converted/plant2_speed_3_24_seg_258301.mp4",
  group_obstacles_detour: "converted/ft_n2_detour_right_seg_1241471060.mp4",
  group_routing_one_way: "converted/pair_5_7_1_plant2_expert.mp4",
  // Real maps: rollout on the SAME crop as the map images below
  realmap_rollout: "converted/eval0912_direction_right_dual_T_1303406452.mp4",
  // Targeted generation
  yield_convoy: "converted/ft_n2_yield_junc_1057163165.mp4",
  crosswalk_expert: "converted/expert_idm_rule_crosswalk_seg_1103897132.mp4",
  // Routing: fine-tuned rollout on the dual-path map
  routing_rollout: "converted/ft_augA_direction_right_dual_T_1303406452.mp4",
  // Interface / checker
  checker_compliant: "converted/pair_5_15_1_plant2_expert.mp4",
  checker_violation: "converted/pair_5_15_1_plant2_base.mp4",
  // Existing planner gap
  gap_idm: "converted/pair_3_1_idm_base.mp4",
  gap_carl: "converted/pair_5_7_1_carl_base.mp4",
  gap_plant2: "converted/pair_5_15_1_plant2_base.mp4",
  // Architecture → rollout
  arch_rollout: "converted/ft_n2_speed_limit_seg_1011196718.mp4",
  // Main result
  result_plant2: "converted/pair_3_1_plant2_base.mp4",
  result_plant2ft: "converted/ft_n2_no_entry_dual_T_1221647944.mp4",
  // Ablation: only the "sign input present" side exists as real footage
  ablation_present: "converted/ft_n2_detour_right_seg_1241471060.mp4",
  // End frame background
  end_background: "converted/ft_n2_roundabout_rb_032ea693fcab.mp4",
};

export const FIGURES = {
  // Real Moscow SUMO network + all crop centres (rendered from project data)
  moscowOverview: "figures/moscow_crops_overview.png",
  // Real-map crop of dual-path T-junction 1303406452 (project renderer)
  cropPlain: "figures/map_dual_T_1303406452_plain.png",
  cropRoutes: "figures/map_dual_T_1303406452_routes.png",
  scenePreview: "figures/scene_preview_dual_T_1303406452.png",
  // Paper figures
  taxonomy: "figures/taxonomy_fig1.png",
  signCountries: "figures/sign_countries_oldpaper.png", // old paper Fig. 4 (visual only)
  geographic: "figures/geographic_diversity.png",
};

// Pixel <-> SUMO-metre mapping of moscowOverview (from render_overview.py json)
export const OVERVIEW = {
  width: 4000,
  height: 4502,
  xlim: [-444.3222, 37722.3322] as const,
  ylim: [3149.7478, 46111.2222] as const,
};

// Crop bbox (SUMO xy, metres) of the scene used in scenes 03 and 05 (meta.json)
export const REALMAP_SCENE = {
  id: "dual_T_1303406452_l_r_b5c03734",
  bbox: [35174.4, 15038.23, 35530.34, 15334.34] as const,
  center: [35446.025, 15206.125] as const,
  baselineLengthM: 94.93,
  compliantLengthM: 313.26,
};

export const REAL_MAPS = {
  junction: {
    crop: "real_maps/junction.png",
    rollout: "real_maps/junction.gif",
    sign: "signs/yield.png",
  },
  dualPath: {
    crop: "real_maps/dual_path.png",
    rollout: "real_maps/dual_path.gif",
    sign: "signs/direction_straight.png",
  },
  corridor: {
    crop: "real_maps/corridor.png",
    rollout: "real_maps/corridor.gif",
    sign: "signs/detour_right.png",
  },
} as const;

export const SIGNS = {
  no_entry: "signs/no_entry.png",
  yield: "signs/yield.png",
  speed_limit_20: "signs/speed_limit_20.png",
  detour_right: "signs/detour_right.png",
  one_way_right: "signs/one_way_right.png",
  direction_right: "signs/direction_right.png",
  crosswalk: "signs/crosswalk.png",
  stop: "signs/stop.png",
  main_road: "signs/main_road.png",
  roundabout: "signs/roundabout.png",
};

export const FLAGS = {
  germany: "flags/germany.png",
  france: "flags/france.png",
  italy: "flags/italy.png",
  turkey: "flags/turkey.png",
  uk: "flags/uk.png",
  china: "flags/china.png",
};

// Group icon sets shown in scene 02 (project sign icons from gifs/icons → public/signs)
export const GROUP_ICONS = {
  priority: ["main_road", "secondary_road", "yield", "stop", "crosswalk", "roundabout"],
  speed: ["speed_limit_40", "end_speed_limit_40", "min_speed", "zone_speed_40", "end_zone_speed_40"],
  obstacles: ["detour_right", "detour_left", "detour_either", "bus_lane", "bike_lane", "bus_lane_road", "bike_lane_road"],
  routing: [
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
};
