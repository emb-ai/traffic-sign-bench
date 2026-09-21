"""Draw ego/aux route polylines + path-conflict points on top-down GIFs.

Monkey-patches ``TopDownRenderer._draw`` (does not edit the metadrive package).

Overlays are painted on ``_frame_canvas`` in *map* pixel space (via ``pos2pix``),
the same place MetaDrive draws green navigation routes — *before* the heading-up
crop/rotate. Drawing on ``_screen_canvas`` after rotate misaligned paths off-road.

Injection trick: ``pygame.Surface.fill``/``blit`` are read-only, so we temporarily
wrap ``_screen_canvas`` and draw when ``get_size()`` is called at the start of the
camera section in ``TopDownRenderer._draw``.

Also patches navigation drawing so ``_priority_bench_dest_along_m`` caps:

- the red destination marker (MetaDrive always used ``final_lane.length``);
- the green final-route polyline (truncated at the capped along-lane finish).
"""

from __future__ import annotations

_APPLIED = False
_ENABLED = False
_DEST_CAP_APPLIED = False

# pygame RGB
EGO_PATH_COLOR = (0, 220, 255)       # cyan
FOE_BLOCKING_COLOR = (255, 64, 220)  # magenta
FOE_OTHER_COLOR = (160, 160, 160)    # gray
CONFLICT_COLOR = (255, 220, 0)       # yellow
# Zone fills (distinct so yield vs main conflict are readable on GIFs).
YIELD_ZONE_COLOR = (40, 200, 120)    # green — ego approach / yield zone
MAIN_ZONE_COLOR = (255, 210, 40)     # yellow — aux main conflict arc
ZONE_COLOR = MAIN_ZONE_COLOR         # legacy alias
ENTRY_POINT_COLOR = (255, 230, 60)   # bright yellow — entry XY

# Generic verifier overlays used by the paper visualisation.
MONITORED_ZONE_COLOR = (55, 87, 255)   # blue — checker-active region
ALLOWED_COLOR = (36, 180, 118)         # green — compliant lane / outgoing edge
PROHIBITED_COLOR = (226, 72, 72)       # red — forbidden lane / outgoing edge
NO_STOP_COLOR = (242, 164, 55)         # amber — no-stop region
CROSSWALK_COLOR = (42, 184, 205)       # cyan — physical crossing polygon
VELOCITY_COLOR = (255, 255, 255)       # white — ego velocity vector


def _xy_list(points) -> list[tuple[float, float]]:
    out: list[tuple[float, float]] = []
    for p in points or []:
        try:
            out.append((float(p[0]), float(p[1])))
        except Exception:
            continue
    return out


def _zone_color(zone) -> tuple[int, int, int]:
    kind = str(zone.get("kind") or "").lower()
    if kind in {"yield", "ego", "approach"}:
        return YIELD_ZONE_COLOR
    return MAIN_ZONE_COLOR


def _truncate_polyline_along(polyline, dest_along: float):
    """Cut a map polyline at ``dest_along`` meters from its start."""
    pts = list(polyline)
    if dest_along is None or len(pts) < 2:
        return pts
    try:
        limit = float(dest_along)
    except (TypeError, ValueError):
        return pts
    if limit <= 0.0:
        return pts

    cut = [pts[0]]
    traveled = 0.0
    for j in range(len(pts) - 1):
        x0, y0 = float(pts[j][0]), float(pts[j][1])
        x1, y1 = float(pts[j + 1][0]), float(pts[j + 1][1])
        seg = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
        if traveled + seg >= limit:
            remain = max(0.0, limit - traveled)
            if seg > 1e-6 and remain > 1e-6:
                t = remain / seg
                cut.append((x0 + t * (x1 - x0), y0 + t * (y1 - y0)))
            break
        cut.append(pts[j + 1])
        traveled += seg
    return cut


def _draw_polyline_frame(canvas, points, color, width: int) -> None:
    import pygame

    pts = _xy_list(points)
    if len(pts) < 2:
        if len(pts) == 1:
            pix = canvas.pos2pix(pts[0][0], pts[0][1])
            pygame.draw.circle(canvas, color, pix, max(2, width))
        return
    pix_pts = [canvas.pos2pix(x, y) for x, y in pts]
    for i in range(len(pix_pts) - 1):
        pygame.draw.line(canvas, color, pix_pts[i], pix_pts[i + 1], width)


def _draw_conflict_marker_frame(canvas, point, color) -> None:
    import pygame

    try:
        cx, cy = canvas.pos2pix(float(point[0]), float(point[1]))
    except Exception:
        return
    r = 10
    pygame.draw.circle(canvas, color, (cx, cy), r, 0)
    pygame.draw.circle(canvas, (20, 20, 20), (cx, cy), r, 2)
    pygame.draw.line(canvas, (20, 20, 20), (cx - r - 3, cy), (cx + r + 3, cy), 2)
    pygame.draw.line(canvas, (20, 20, 20), (cx, cy - r - 3), (cx, cy + r + 3), 2)


def _zone_long_range(zone) -> tuple[object, float, float, float] | None:
    """Return ``(lane, s0, s1, half_width)`` clamped to the lane, or None."""
    lane = zone.get("lane")
    if lane is None:
        return None
    try:
        long_start = float(zone.get("long_start", 0.0))
        long_end = float(zone.get("long_end", getattr(lane, "length", 0.0)))
        length = float(getattr(lane, "length", 0.0))
        width = float(getattr(lane, "width", 3.5) or 3.5)
    except Exception:
        return None
    if length <= 1e-3:
        return None
    s0 = max(0.0, min(long_start, length - 1e-3))
    s1 = max(s0 + 1e-3, min(long_end, length))
    half_w = max(0.8, 0.5 * width)
    return lane, s0, s1, half_w


def _zone_polyline(zone) -> list[tuple[float, float]]:
    """Centerline sample of a longitudinal lane window."""
    info = _zone_long_range(zone)
    if info is None:
        return []
    lane, s0, s1, _half_w = info
    length = float(getattr(lane, "length", 0.0))
    pts: list[tuple[float, float]] = []
    step = 2.0
    s = s0
    while s <= s1 + 1e-6:
        try:
            p = lane.position(min(s, length - 1e-3), 0.0)
            pts.append((float(p[0]), float(p[1])))
        except Exception:
            break
        s += step
    return pts


def _zone_polygon(zone) -> list[tuple[float, float]]:
    """Lane-width ribbon for a longitudinal window (left edge then right reversed)."""
    info = _zone_long_range(zone)
    if info is None:
        return []
    lane, s0, s1, half_w = info
    length = float(getattr(lane, "length", 0.0))
    left: list[tuple[float, float]] = []
    right: list[tuple[float, float]] = []
    step = 2.0
    s = s0
    while s <= s1 + 1e-6:
        along = min(s, length - 1e-3)
        try:
            pl = lane.position(along, -half_w)
            pr = lane.position(along, half_w)
            left.append((float(pl[0]), float(pl[1])))
            right.append((float(pr[0]), float(pr[1])))
        except Exception:
            break
        s += step
    if len(left) < 2 or len(right) < 2:
        return []
    return left + list(reversed(right))


def _draw_polygon_frame(canvas, points, color, *, alpha: int = 110) -> None:
    import pygame

    pts = _xy_list(points)
    if len(pts) < 3:
        return
    pix_pts = [canvas.pos2pix(x, y) for x, y in pts]
    # Prefer a translucent fill so the road stays readable; fall back to outline.
    try:
        flags = canvas.get_flags() if hasattr(canvas, "get_flags") else 0
        if flags & pygame.SRCALPHA:
            overlay = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(overlay, (*color, int(alpha)), pix_pts)
            canvas.blit(overlay, (0, 0))
        else:
            # Opaque canvas: draw a temporary SRCALPHA layer and blit with alpha.
            try:
                overlay = pygame.Surface(canvas.get_size(), pygame.SRCALPHA)
                pygame.draw.polygon(overlay, (*color, int(alpha)), pix_pts)
                canvas.blit(overlay, (0, 0))
            except Exception:
                pass
    except Exception:
        pass
    try:
        pygame.draw.polygon(canvas, color, pix_pts, width=3)
    except TypeError:
        pygame.draw.lines(canvas, color, True, pix_pts, 3)


def _draw_zone_frame(canvas, zone) -> None:
    color = _zone_color(zone)
    poly = _zone_polygon(zone)
    if poly:
        _draw_polygon_frame(canvas, poly, color)
    else:
        _draw_polyline_frame(canvas, _zone_polyline(zone), color, 6)


def _draw_lane_window_color(
    canvas,
    lane,
    start: float,
    end: float,
    color,
    *,
    alpha: int = 110,
) -> None:
    """Draw a checker ribbon with an explicit colour."""
    zone = {
        "lane": lane,
        "long_start": float(start),
        "long_end": float(end),
    }
    poly = _zone_polygon(zone)
    if poly:
        _draw_polygon_frame(canvas, poly, color, alpha=alpha)
    else:
        _draw_polyline_frame(canvas, _zone_polyline(zone), color, 6)


def _draw_map_arrow(canvas, start, end, color, width: int = 5) -> None:
    import math
    import pygame

    try:
        p0 = canvas.pos2pix(float(start[0]), float(start[1]))
        p1 = canvas.pos2pix(float(end[0]), float(end[1]))
    except Exception:
        return
    pygame.draw.line(canvas, color, p0, p1, width)
    dx, dy = float(p1[0] - p0[0]), float(p1[1] - p0[1])
    norm = math.hypot(dx, dy)
    if norm < 1.0:
        return
    ux, uy = dx / norm, dy / norm
    size = 13.0
    wing = 6.0
    base_x, base_y = p1[0] - ux * size, p1[1] - uy * size
    points = [
        p1,
        (base_x - uy * wing, base_y + ux * wing),
        (base_x + uy * wing, base_y - ux * wing),
    ]
    pygame.draw.polygon(canvas, color, points)


def _draw_point_marker(canvas, point, color, radius: int = 10) -> None:
    import pygame

    try:
        pix = canvas.pos2pix(float(point[0]), float(point[1]))
    except Exception:
        return
    pygame.draw.circle(canvas, color, pix, radius, 0)
    pygame.draw.circle(canvas, (255, 255, 255), pix, radius, 2)


def _draw_ego_velocity(canvas, ego) -> None:
    """Draw velocity direction; length is proportional to current speed."""
    import math

    try:
        pos = ego.position
        heading = float(ego.heading_theta)
        speed_ms = max(0.0, float(ego.speed_km_h) / 3.6)
        length_m = min(18.0, max(5.0, speed_ms * 1.25))
        end = (
            float(pos[0]) + math.cos(heading) * length_m,
            float(pos[1]) + math.sin(heading) * length_m,
        )
    except Exception:
        return
    _draw_map_arrow(canvas, pos, end, VELOCITY_COLOR, width=6)


def _network_lanes(engine):
    """Yield ``(lane_id, lane)`` from SUMO's flat road-network graph."""
    try:
        network = engine.current_map.road_network
        graph = getattr(network, "graph", {}) or {}
    except Exception:
        return
    seen = set()
    for lane_id, info in graph.items():
        lane = getattr(info, "lane", None)
        if lane is None:
            try:
                lane = network.get_lane(lane_id)
            except Exception:
                lane = None
        if lane is None or id(lane) in seen:
            continue
        seen.add(id(lane))
        yield lane_id, lane


def _lane_for_id(engine, lane_id):
    try:
        return engine.current_map.road_network.get_lane(lane_id)
    except Exception:
        return None


def _right_lane_closure(engine, initial_lane_ids, *, max_lanes: int = 2) -> list:
    """Return up to two successive lanes to the right for detour display."""
    try:
        network = engine.current_map.road_network
        graph = getattr(network, "graph", {}) or {}
    except Exception:
        return list(initial_lane_ids or ())[:max_lanes]

    queue = list(initial_lane_ids or ())
    result = []
    seen = set()
    while queue and len(result) < max_lanes:
        lane_id = queue.pop(0)
        if lane_id in seen:
            continue
        seen.add(lane_id)
        result.append(lane_id)
        info = graph.get(lane_id)
        lane = _lane_for_id(engine, lane_id)
        rights = (
            getattr(info, "right_lanes", None)
            or getattr(lane, "right_lanes", None)
            or ()
        )
        queue.extend(rights)
    return result


def _draw_speed_verifier(canvas, engine, ego, sign) -> bool:
    from traffic_bench.signs.speed.limit import SpeedLimitSign

    if not isinstance(sign, SpeedLimitSign):
        return False
    edges = [str(edge) for edge in (getattr(sign, "zone_edges", None) or [])]
    if not edges:
        sign_lane_id = getattr(sign.lane, "index", None)
        try:
            sign_edge = str(sign._sumo_edge_id_from_lane_index(sign_lane_id))
        except Exception:
            sign_edge = None
        drawn = False
        for lane_id, lane in _network_lanes(engine):
            try:
                edge_id = str(sign._sumo_edge_id_from_lane_index(lane_id))
            except Exception:
                continue
            if sign_edge is None or edge_id != sign_edge:
                continue
            _draw_lane_window_color(
                canvas,
                lane,
                float(sign.zone_start),
                float(sign.zone_end),
                NO_STOP_COLOR,
                alpha=62,
            )
            drawn = True
        if not drawn:
            _draw_lane_window_color(
                canvas,
                sign.lane,
                float(sign.zone_start),
                float(sign.zone_end),
                NO_STOP_COLOR,
                alpha=62,
            )
    else:
        first, last = str(edges[0]), str(edges[-1])
        for lane_id, lane in _network_lanes(engine):
            try:
                edge_id = str(sign._sumo_edge_id_from_lane_index(lane_id))
            except Exception:
                continue
            if edge_id not in edges:
                continue
            start = float(sign.zone_start) if edge_id == first else 0.0
            end = (
                float(sign.zone_end_s)
                if edge_id == last
                else float(getattr(lane, "length", 0.0))
            )
            _draw_lane_window_color(
                canvas, lane, start, end, NO_STOP_COLOR, alpha=62
            )
    _draw_ego_velocity(canvas, ego)
    return True


def _draw_detour_verifier(canvas, engine, ego, sign) -> bool:
    from traffic_bench.signs.detour.plate import DetourSign

    if not isinstance(sign, DetourSign):
        return False
    _draw_lane_window_color(
        canvas,
        sign.lane,
        float(sign.zone_start),
        float(sign.zone_end),
        NO_STOP_COLOR,
        alpha=72,
    )
    allowed_ids = _right_lane_closure(
        engine,
        getattr(sign, "_allowed_lane_indices", set()) or set(),
        max_lanes=2,
    )
    for lane_id in allowed_ids:
        lane = _lane_for_id(engine, lane_id)
        if lane is None:
            continue
        _draw_lane_window_color(
            canvas,
            lane,
            float(sign.zone_start),
            float(sign.zone_end),
            ALLOWED_COLOR,
            alpha=72,
        )
    try:
        obstacle = sign.lane.position(float(sign.obstacle_long), 0.0)
        _draw_point_marker(canvas, obstacle, PROHIBITED_COLOR, radius=11)
    except Exception:
        pass
    return True


def _draw_one_way_verifier(canvas, engine, ego, sign) -> bool:
    from traffic_bench.signs.dual_path.one_way import OneWayEntrySign

    if not isinstance(sign, OneWayEntrySign):
        return False
    try:
        sign._ensure_sumo_outgoing_context()
        mapped = sign._sumo_outgoing_mapped or {}
    except Exception:
        mapped = {}
    all_outgoing = set(mapped.get("all_outgoing") or ())
    by_dir = mapped.get("by_dir") or {}
    forbidden = set(by_dir.get("l") or ())
    allowed = set(by_dir.get("r") or ()) or (all_outgoing - forbidden)

    for lane_id, lane in _network_lanes(engine):
        try:
            edge_id = str(sign._sumo_edge_id_from_lane_index(lane_id))
        except Exception:
            continue
        color = (
            PROHIBITED_COLOR
            if edge_id in forbidden
            else ALLOWED_COLOR
            if edge_id in allowed
            else None
        )
        if color is None:
            continue
        length = min(22.0, float(getattr(lane, "length", 0.0)))
        _draw_lane_window_color(canvas, lane, 0.0, length, color)
    return True


def _draw_crosswalk_verifier(canvas, sign_mgr, ego) -> bool:
    drawn = False
    for rule in getattr(sign_mgr, "rules", ()) or ():
        if type(rule).__name__ != "PedestrianYieldRule":
            continue
        try:
            _engine, states = rule._get_crosswalk_state(ego)
            thresholds = rule._resolve_all_thresholds(_engine)
        except Exception:
            continue
        for state in (states or {}).values():
            try:
                polygon = state.get("polygon")
                no_stop_zone = rule._build_renderer_no_stop_zone_polygon(
                    polygon, float(thresholds["no_stop_before_m"])
                )
            except Exception:
                continue
            if no_stop_zone is not None:
                _draw_polygon_frame(
                    canvas, list(no_stop_zone), NO_STOP_COLOR, alpha=72
                )
            color = (
                PROHIBITED_COLOR
                if bool(state.get("active", False))
                else CROSSWALK_COLOR
            )
            _draw_polygon_frame(canvas, list(polygon), color, alpha=42)
            drawn = True
    return drawn


def _draw_generic_verifier_overlays(canvas, engine, sign_mgr, ego) -> None:
    """Render the exact zones/edge sets consumed by selected rule checkers."""
    _draw_crosswalk_verifier(canvas, sign_mgr, ego)
    for sign in getattr(sign_mgr, "signs", ()) or ():
        if _draw_speed_verifier(canvas, engine, ego, sign):
            continue
        if _draw_detour_verifier(canvas, engine, ego, sign):
            continue
        _draw_one_way_verifier(canvas, engine, ego, sign)


def verifier_hud_lines(sign_mgr, ego) -> dict[str, str]:
    """Concise, human-readable status for verifier demonstration GIFs."""
    if sign_mgr is None or ego is None:
        return {}

    for rule in getattr(sign_mgr, "rules", ()) or ():
        if type(rule).__name__ != "PedestrianYieldRule":
            continue
        try:
            status = rule.get_status(ego)
        except Exception:
            continue
        return {
            "Rule": "yield at occupied crossing",
            "Verifier zone": (
                f"{float(status['no_stop_before_m']):.0f} m before crossing"
            ),
            "Check": (
                f"pedestrian={'active' if status['target_active'] else 'clear'}; "
                f"must stop={'yes' if status['must_stop'] else 'no'}"
            ),
        }

    from traffic_bench.signs.detour.plate import DetourSign
    from traffic_bench.signs.dual_path.one_way import OneWayEntrySign
    from traffic_bench.signs.speed.limit import SpeedLimitSign

    for sign in getattr(sign_mgr, "signs", ()) or ():
        if isinstance(sign, SpeedLimitSign):
            try:
                inside = bool(sign.is_vehicle_in_zone(ego))
            except Exception:
                inside = False
            return {
                "Rule": f"speed <= {float(sign.speed_limit):.0f} km/h",
                "Verifier zone": "yellow road segment",
                "Check": f"inside={'yes' if inside else 'no'}",
            }
        if isinstance(sign, DetourSign):
            try:
                veh_long = float(sign.lane.local_coordinates(ego.position)[0])
                inside = float(sign.zone_start) <= veh_long <= float(sign.zone_end)
                state = (getattr(sign, "_vehicle_states_detour", {}) or {}).get(
                    ego.id, {}
                )
                changed = bool(state.get("changed_correctly", False))
            except Exception:
                inside, changed = False, False
            side = "/".join(sorted(getattr(sign, "allowed_directions", ()) or ()))
            return {
                "Rule": f"pass obstacle on {side}",
                "Verifier zone": "yellow; allowed lanes green",
                "Check": (
                    f"inside={'yes' if inside else 'no'}; "
                    f"changed={'yes' if changed else 'no'}"
                ),
            }
        if isinstance(sign, OneWayEntrySign):
            names = {"l": "left", "r": "right", "s": "straight", "t": "U-turn"}
            prohibited = names.get(
                str(getattr(sign, "not_allowed_direction", "")),
                str(getattr(sign, "not_allowed_direction", "")),
            )
            return {
                "Rule": f"forbid {prohibited} outgoing edge",
                "Verifier zone": "approach blue; red forbidden",
                "Check": "selected outgoing edge at junction exit",
            }

    return {
        "Verifier zones": "green=yield; yellow=conflict",
        "Verifier paths": "cyan=ego; magenta=conflicting traffic",
    }


def _draw_path_conflict_overlays_on_frame(renderer) -> None:
    """Draw overlays onto ``_frame_canvas`` (pre-camera map pixels)."""
    engine = getattr(renderer, "engine", None)
    if engine is None or not hasattr(engine, "traffic_sign_manager"):
        return
    sign_mgr = engine.traffic_sign_manager
    if sign_mgr is None:
        return
    ego = getattr(renderer, "current_track_agent", None)
    canvas = getattr(renderer, "_frame_canvas", None)
    if ego is None or canvas is None:
        return

    _draw_generic_verifier_overlays(canvas, engine, sign_mgr, ego)

    from traffic_bench.signs.junction import YieldSign

    for sign in getattr(sign_mgr, "signs", []) or []:
        if not isinstance(sign, YieldSign):
            continue
        try:
            overlay = sign.get_top_down_path_conflict_overlay(ego)
        except Exception:
            continue
        if not overlay:
            continue

        # Zones under paths so routes stay readable.
        for zone in overlay.get("zones") or []:
            _draw_zone_frame(canvas, zone)

        entry_pt = overlay.get("entry_point")
        if entry_pt is not None:
            _draw_conflict_marker_frame(canvas, entry_pt, ENTRY_POINT_COLOR)

        _draw_polyline_frame(canvas, overlay.get("ego_path"), EGO_PATH_COLOR, 5)

        for foe in overlay.get("foes") or []:
            # Magenta for tracked foes in the nearest main arc (thicker if blocking).
            color = FOE_BLOCKING_COLOR
            width = 5 if foe.get("blocking") else 3
            _draw_polyline_frame(canvas, foe.get("path"), color, width)
            pt = foe.get("conflict_point")
            if pt is not None:
                _draw_conflict_marker_frame(canvas, pt, CONFLICT_COLOR)


def set_path_conflict_overlay_enabled(enabled: bool) -> None:
    """Enable/disable path-conflict GIF overlays at runtime."""
    global _ENABLED
    _ENABLED = bool(enabled)


def is_path_conflict_overlay_enabled() -> bool:
    return bool(_ENABLED)


class _ScreenCanvasHook:
    """Proxy that draws path overlays on first ``get_size()`` (camera section)."""

    __slots__ = ("_real", "_renderer", "_drawn")

    def __init__(self, real, renderer):
        object.__setattr__(self, "_real", real)
        object.__setattr__(self, "_renderer", renderer)
        object.__setattr__(self, "_drawn", False)

    def get_size(self):
        if not object.__getattribute__(self, "_drawn"):
            object.__setattr__(self, "_drawn", True)
            try:
                _draw_path_conflict_overlays_on_frame(
                    object.__getattribute__(self, "_renderer")
                )
            except Exception:
                pass
        return object.__getattribute__(self, "_real").get_size()

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_real"), name)


def _dest_along_for_agent(agent):
    """Return capped destination longitude when priority_bench set one."""
    if agent is None:
        return None
    for obj in (agent, getattr(agent, "navigation", None)):
        if obj is None:
            continue
        raw = getattr(obj, "_priority_bench_dest_along_m", None)
        if raw is None:
            continue
        try:
            val = float(raw)
        except (TypeError, ValueError):
            continue
        if val > 0.0:
            return val
    return None


def _backup_and_truncate_final_route(renderer, along: float) -> list[tuple[dict, object]]:
    """Temporarily truncate the last checkpoint polyline; return restore pairs."""
    agent = getattr(renderer, "current_track_agent", None)
    nav = getattr(agent, "navigation", None) if agent is not None else None
    checkpoints = getattr(nav, "checkpoints", None) if nav is not None else None
    if not checkpoints:
        return []

    last_id = checkpoints[-1]
    backups: list[tuple[dict, object]] = []
    for block in getattr(getattr(renderer, "map", None), "blocks", []) or []:
        map_data = getattr(block, "map_data", None)
        if not isinstance(map_data, dict):
            continue
        lane_info = map_data.get(last_id)
        if not isinstance(lane_info, dict):
            continue
        polyline = lane_info.get("polyline")
        if polyline is None or len(polyline) < 2:
            continue
        backups.append((lane_info, polyline))
        lane_info["polyline"] = _truncate_polyline_along(polyline, along)
    return backups


def apply_top_down_destination_cap_patch() -> None:
    """Honor ``_priority_bench_dest_along_m`` for dest mark + green final route."""
    global _DEST_CAP_APPLIED
    if _DEST_CAP_APPLIED:
        return

    from metadrive.engine.top_down_renderer import TopDownRenderer

    _orig_draw = TopDownRenderer._draw

    def _patched_draw(self, *args, **kwargs):
        agent = getattr(self, "current_track_agent", None)
        nav = getattr(agent, "navigation", None) if agent is not None else None
        final = getattr(nav, "final_lane", None) if nav is not None else None
        along = _dest_along_for_agent(agent)
        if along is None:
            return _orig_draw(self, *args, **kwargs)

        orig_position = None
        if final is not None:
            orig_position = final.position

            def _capped_position(longitudinal, lateral=0.0, *rest, **kw):
                try:
                    length = float(getattr(final, "length", 0.0) or 0.0)
                except Exception:
                    length = 0.0
                try:
                    req = float(longitudinal)
                except (TypeError, ValueError):
                    return orig_position(longitudinal, lateral, *rest, **kw)
                # Prefer the priority_bench cap whenever MetaDrive asks near lane end
                # (or any request past the cap).
                cap = (
                    min(float(along), max(0.5, length - 1e-3))
                    if length > 1e-3
                    else float(along)
                )
                if length > 1e-3 and (abs(req - length) < 1e-2 or req > cap):
                    req = cap
                return orig_position(req, lateral, *rest, **kw)

            final.position = _capped_position  # type: ignore[method-assign]

        backups = _backup_and_truncate_final_route(self, float(along))
        try:
            return _orig_draw(self, *args, **kwargs)
        finally:
            if final is not None and orig_position is not None:
                final.position = orig_position  # type: ignore[method-assign]
            for lane_info, polyline in backups:
                lane_info["polyline"] = polyline

    TopDownRenderer._draw = _patched_draw
    _DEST_CAP_APPLIED = True


def apply_top_down_path_conflict_overlay_patch() -> None:
    """Monkey-patch ``TopDownRenderer._draw`` once (idempotent).

    Drawing only runs when ``set_path_conflict_overlay_enabled(True)``.
    Also installs the destination-cap patch (red finish marker + green route trim).
    """
    global _APPLIED
    apply_top_down_destination_cap_patch()
    if _APPLIED:
        return

    from metadrive.engine.top_down_renderer import TopDownRenderer

    # Destination-cap patch already wrapped _draw; wrap again for overlays.
    _orig_draw = TopDownRenderer._draw

    def _patched_draw(self, *args, **kwargs):
        if not _ENABLED:
            return _orig_draw(self, *args, **kwargs)
        real_screen = self._screen_canvas
        self._screen_canvas = _ScreenCanvasHook(real_screen, self)
        try:
            return _orig_draw(self, *args, **kwargs)
        finally:
            self._screen_canvas = real_screen

    TopDownRenderer._draw = _patched_draw
    _APPLIED = True
