"""Regression tests for yield-conflict fast paths.

These tests verify that avoiding unnecessary path geometry does not change
which vehicles block the ego.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np

from traffic_bench.signs.junction.roundabout import RoundaboutYieldSign
from traffic_bench.signs.junction.yield_sign import YieldSign


class _TestYieldSign(YieldSign):
    @property
    def engine(self):
        return self._test_engine


def _bare_sign() -> YieldSign:
    sign = object.__new__(_TestYieldSign)
    sign._test_engine = SimpleNamespace(episode_step=0)
    sign._auto_detect = False
    sign._pg_initialized = True
    sign.main_road_lanes = [object()]
    sign._path_sticky_foes = {}
    sign._path_released_foes = set()
    sign._is_waiting_gated_aux = Mock(return_value=False)
    return sign


def _path(y: float) -> list[np.ndarray]:
    return [
        np.asarray([0.0, y]),
        np.asarray([10.0, y]),
    ]


def test_non_conflict_zone_foe_without_sticky_state_skips_path_geometry():
    sign = _bare_sign()
    ego = SimpleNamespace(id="ego")
    foe = SimpleNamespace(id="far-away")
    sign._is_vehicle_in_main_road_conflict_zone = Mock(return_value=False)
    sign._route_polyline = Mock(
        side_effect=AssertionError("irrelevant foe must not build route geometry")
    )

    assert sign._is_foe_blocking_ego(ego, foe) is False
    sign._route_polyline.assert_not_called()


def test_sticky_foe_outside_coarse_zone_remains_tracked():
    sign = _bare_sign()
    ego = SimpleNamespace(id="ego")
    foe = SimpleNamespace(id="sticky")
    conflict = np.asarray([5.0, 0.0])
    sign._path_sticky_foes[foe.id] = {"conflict_point": conflict}
    sign._is_vehicle_in_main_road_conflict_zone = Mock(return_value=False)
    sign._route_polyline = Mock(side_effect=[_path(0.0), _path(0.0)])
    sign._paths_conflict_point = Mock(return_value=conflict)
    sign._has_cleared_conflict_point = Mock(return_value=False)

    assert sign._is_foe_blocking_ego(ego, foe) is True
    assert foe.id in sign._path_sticky_foes


def test_main_traffic_check_builds_ego_path_once_for_all_foes():
    sign = _bare_sign()
    ego = SimpleNamespace(id="ego")
    foes = [SimpleNamespace(id="foe-1"), SimpleNamespace(id="foe-2")]
    ego_path = _path(0.0)
    sign._get_all_vehicles = Mock(return_value=[ego, *foes])
    sign._route_polyline = Mock(return_value=ego_path)
    sign._is_foe_blocking_ego = Mock(side_effect=[True, False])

    has_traffic, conflicting = sign._check_main_road_traffic(ego)

    assert has_traffic is True
    assert conflicting == [foes[0]]
    sign._route_polyline.assert_called_once_with(ego)
    for call in sign._is_foe_blocking_ego.call_args_list:
        assert call.kwargs["ego_path"] is ego_path


def test_geometric_conflict_is_computed_once_for_relevant_foe():
    sign = _bare_sign()
    ego = SimpleNamespace(id="ego")
    foe = SimpleNamespace(id="main-road")
    conflict = np.asarray([5.0, 0.0])
    sign._is_vehicle_in_main_road_conflict_zone = Mock(return_value=True)
    sign._route_polyline = Mock(side_effect=[_path(0.0), _path(0.0)])
    sign._paths_conflict_point = Mock(return_value=conflict)
    sign._has_cleared_conflict_point = Mock(return_value=False)

    assert sign._is_foe_blocking_ego(ego, foe) is True
    sign._paths_conflict_point.assert_called_once()


def test_roundabout_override_accepts_base_checker_path_cache():
    sign = object.__new__(RoundaboutYieldSign)
    sign._ensure_active_main_zones = Mock()
    sign._is_waiting_gated_aux = Mock(return_value=True)

    assert sign._is_foe_blocking_ego(
        SimpleNamespace(id="ego"),
        SimpleNamespace(id="held-aux"),
        ego_path=_path(0.0),
    ) is False


def test_vehicle_outside_yield_zone_skips_current_traffic_check():
    sign = _bare_sign()
    sign._test_engine = SimpleNamespace(episode_step=7)
    sign._vehicle_states = {}
    sign._is_vehicle_in_zone = Mock(return_value=False)
    sign._check_main_road_traffic = Mock(
        side_effect=AssertionError("traffic cannot affect an ego outside the zone")
    )
    ego = SimpleNamespace(id="ego")

    assert sign._is_violating(ego) is False
    sign._check_main_road_traffic.assert_not_called()


def test_leaving_yield_zone_preserves_pending_violation_without_recheck():
    sign = _bare_sign()
    sign._test_engine = SimpleNamespace(episode_step=8)
    sign._vehicle_states = {
        "ego": {
            "had_traffic_while_in_zone": True,
            "last_violation_step": 7,
            "last_violation_result": False,
        }
    }
    sign._is_vehicle_in_zone = Mock(return_value=False)
    sign._check_main_road_traffic = Mock(
        side_effect=AssertionError("pending violation needs no new traffic check")
    )
    ego = SimpleNamespace(id="ego")

    assert sign._is_violating(ego) is True
    assert sign._vehicle_states["ego"]["had_traffic_while_in_zone"] is False
    sign._check_main_road_traffic.assert_not_called()
