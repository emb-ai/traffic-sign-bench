"""nohud_run.py <traffic_bench.eval args...>: run the benchmark with GIF frames rendered without the text HUD
(Step / Speed / Violations lines). Visual only: the top-down renderer's _add_text becomes a no-op, also after
the project's own HUD patch would have been applied. The simulation itself is untouched."""
import runpy
import sys

from metadrive.engine.top_down_renderer import TopDownRenderer

import traffic_bench.eval.engine.sim.top_down_text_patch as hud


def _no_text(self, text):
    return None


def _no_hud_patch(**_kwargs):
    TopDownRenderer._add_text = _no_text


TopDownRenderer._add_text = _no_text
hud.apply_top_down_violations_text_patch = _no_hud_patch

sys.argv = ["traffic_bench.eval"] + sys.argv[1:]
runpy.run_module("traffic_bench.eval", run_name="__main__")
