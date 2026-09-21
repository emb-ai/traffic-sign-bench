#!/usr/bin/env python3
"""Build the ICRA main-results table and SCD forest plot.

The script combines:
  * 18 locally evaluated scenario types from data/runs/_all/test;
  * 11 scenario types evaluated in Smirnova's v7/rl3 campaign;
  * one selected PlanT-2-FT checkpoint evaluated on all 29 scenario types.

Conventional diagnostics are episode-weighted across scenarios. SC, Dest,
and grouped/overall SCD are macro averages, so every scenario type has equal
weight.
The forest-plot whiskers are the sample standard deviation across the 29
scenario-level SCD values (not a confidence interval).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import shutil
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, stdev
from typing import Iterable, Mapping

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from PIL import Image, ImageChops
import numpy as np


COLORS = {
    "IDM": "#90CAF9",
    "PPO": "#E76F51",
    "CaRL": "#A1CB35",
    "PlanT-2": "#FCAD38",
}
SERIES_COLORS = {
    "idm": "#9BBCCD",
    "idm_s1": "#9BBCCD",
    "idm_s2": "#9BBCCD",
    "idm_s3": "#9BBCCD",
    "idm_s4": "#9BBCCD",
    "ppo": "#D5A098",
    "carl": "#B4C486",
    "plant2": "#D5B77F",
    "idm_rule": "#90CAF9",
    "idm_rule_s1": "#90CAF9",
    "idm_rule_s2": "#90CAF9",
    "idm_rule_s3": "#90CAF9",
    "idm_rule_s4": "#90CAF9",
    "ppo_rule": "#E76F51",
    "carl_rule": "#A1CB35",
    "plant2_rule": "#FCAD38",
    "plant2_ft": "#FFADEE",
}
CATEGORY_COLORS = {
    "Priority": "#4C78A8",
    "Speed": "#E76F51",
    "Obstacle": "#72A447",
    "Routing": "#E3A128",
}

GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("Priority", ("2.1", "2.3", "2.4", "2.5", "4.3", "5.19")),
    ("Speed", ("3.24", "4.6", "5.21", "5.31")),
    (
        "Obstacle",
        ("3.2", "4.2.1", "4.2.2", "4.2.3", "5.11.1", "5.11.2", "5.14.1", "5.14.2"),
    ),
    (
        "Routing",
        (
            "4.1.1",
            "4.1.2",
            "4.1.3",
            "4.1.4",
            "4.1.5",
            "4.1.6",
            "3.1",
            "3.18.1",
            "3.18.2",
            "5.7.1",
            "5.7.2",
        ),
    ),
)
CODE_TO_GROUP = {code: group for group, codes in GROUPS for code in codes}
ALL_CODES = tuple(code for _, codes in GROUPS for code in codes)
SCENARIO_ICON_FILES = {
    "2.1": "2.1.png",
    "2.3": "2.3.1.png",
    "2.4": "2.4.png",
    "2.5": "2.5.png",
    "4.3": "roundabout.png",
    "5.19": "5.19.png",
    "3.24": "speed_limit_40.png",
    "4.6": "4.6.png",
    "5.21": "residential_zone.jpg",
    "5.31": "zone_speed_40.png",
    "3.2": "3.2.png",
    "4.2.1": "4.2.1.png",
    "4.2.2": "4.2.2.png",
    "4.2.3": "4.2.3.png",
    "5.11.1": "5.11.1.png",
    "5.11.2": "5.11.2.png",
    "5.14.1": "5.14.1.png",
    "5.14.2": "5.14.2.png",
    "4.1.1": "4.1.1.png",
    "4.1.2": "4.1.2.png",
    "4.1.3": "4.1.3.png",
    "4.1.4": "4.1.4.png",
    "4.1.5": "4.1.5.png",
    "4.1.6": "4.1.6.png",
    "3.1": "3.1.png",
    "3.18.1": "3.18.1.png",
    "3.18.2": "3.18.2.png",
    "5.7.1": "5.7.1.png",
    "5.7.2": "5.7.2.png",
}
LOCAL_SCENARIOS = {
    "2.1": "main_road",
    "2.3": "secondary_road",
    "2.4": "yield",
    "2.5": "stop",
    "4.3": "roundabout",
    "5.19": "crosswalk",
    "3.2": "blocked_road",
    "4.1.1": "direction_straight",
    "4.1.2": "direction_right",
    "4.1.3": "direction_left",
    "4.1.4": "direction_straight_right",
    "4.1.5": "direction_straight_left",
    "4.1.6": "direction_left_right",
    "3.1": "no_entry",
    "3.18.1": "no_turn_right",
    "3.18.2": "no_turn_left",
    "5.7.1": "one_way_right",
    "5.7.2": "one_way_left",
}


@dataclass(frozen=True)
class PolicySpec:
    key: str
    family: str
    kind: str
    display: str
    latex: str
    local_name: str | None
    external_name: str | None


POLICIES: tuple[PolicySpec, ...] = (
    PolicySpec("idm", "IDM", "base", "IDM", r"IDM", "idm_default", "idm_default"),
    PolicySpec("idm_s1", "IDM", "base", "IDM-s1", r"IDM-$s_1$", "idm_s1", "idm_s1"),
    PolicySpec("idm_s2", "IDM", "base", "IDM-s2", r"IDM-$s_2$", "idm_s2", "idm_s2"),
    PolicySpec("idm_s3", "IDM", "base", "IDM-s3", r"IDM-$s_3$", "idm_s3", "idm_s3"),
    PolicySpec("idm_s4", "IDM", "base", "IDM-s4", r"IDM-$s_4$", "idm_s4", "idm_s4"),
    PolicySpec(
        "ppo", "PPO", "base", "PPO", r"PPO", "ppo_lidar_default", "ppo_lidar"
    ),
    PolicySpec("carl", "CaRL", "base", "CaRL", r"CaRL", "carl_default", "carl"),
    PolicySpec(
        "plant2", "PlanT-2", "base", "PlanT-2", r"PlanT-2", "plant2_default", "plant2"
    ),
    PolicySpec(
        "idm_rule",
        "IDM",
        "rule",
        "IDM expert",
        r"IDM$^{e}$",
        "idm_rule_default",
        "idm_rule_default",
    ),
    PolicySpec(
        "idm_rule_s1",
        "IDM",
        "rule",
        "IDM-s1 expert",
        r"IDM$^{e}$-$s_1$",
        "idm_rule_s1",
        "idm_rule_s1",
    ),
    PolicySpec(
        "idm_rule_s2",
        "IDM",
        "rule",
        "IDM-s2 expert",
        r"IDM$^{e}$-$s_2$",
        "idm_rule_s2",
        "idm_rule_s2",
    ),
    PolicySpec(
        "idm_rule_s3",
        "IDM",
        "rule",
        "IDM-s3 expert",
        r"IDM$^{e}$-$s_3$",
        "idm_rule_s3",
        "idm_rule_s3",
    ),
    PolicySpec(
        "idm_rule_s4",
        "IDM",
        "rule",
        "IDM-s4 expert",
        r"IDM$^{e}$-$s_4$",
        "idm_rule_s4",
        "idm_rule_s4",
    ),
    PolicySpec(
        "ppo_rule", "PPO", "rule", "PPO expert", r"PPO$^{e}$", "ppo_rule_default", "ppo_rule"
    ),
    PolicySpec(
        "carl_rule",
        "CaRL",
        "rule",
        "CaRL expert",
        r"CaRL$^{e}$",
        "carl_rule_default",
        "carl_rule",
    ),
    PolicySpec(
        "plant2_rule",
        "PlanT-2",
        "rule",
        "PlanT-2 expert",
        r"PlanT-2$^{e}$",
        "plant2_rule_default",
        "plant2_rule",
    ),
    PolicySpec(
        "plant2_ft",
        "PlanT-2",
        "ours",
        "PlanT-2-FT",
        r"\textbf{PlanT-2-FT}",
        None,
        None,
    ),
)

CONVENTIONAL_FIELDS = (
    "efficiency",
    "comfort",
    "collision_rate",
)

LOCAL_FIELD_MAP = {
    "efficiency": "avg_driving_efficiency",
    "comfort": "avg_comfort",
    "collision_rate": "crash_rate",
    "sign_compliance": "target_compliance_rate_event",
    "destination": "dest_rate",
    "sr_dest": "sr_and_dest",
    "n": "n",
}

EXTERNAL_FIELD_MAP = {
    "efficiency": "efficiency",
    "comfort": "comfort",
    "collision_rate": "collision_rate",
    "sign_compliance": "compliance",
    "destination": "dest",
    "sr_dest": "sr_dest",
    "n": "n",
}


def parse_args() -> argparse.Namespace:
    repo = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=repo)
    parser.add_argument(
        "--local-runs",
        type=Path,
        default=repo / "data" / "runs",
    )
    parser.add_argument(
        "--smirnova-table",
        type=Path,
        default=Path(
            "/home/jovyan/shares/SR006.nfs2/smirnova/tmp/base_v7_eff_col_comf.tsv"
        ),
    )
    parser.add_argument(
        "--plant2-ft-root",
        type=Path,
        default=Path(
            "/home/jovyan/shares/SR006.nfs2/smirnova/ft_rl3/agg/"
            "ft200_n2_eq_3e5_e8/aggregations"
        ),
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=repo / "data" / "icra27_results",
    )
    parser.add_argument(
        "--paper-images",
        type=Path,
        default=repo / "paper" / "imgs",
    )
    parser.add_argument(
        "--paper-tables",
        type=Path,
        default=repo / "paper" / "tables",
    )
    return parser.parse_args()


def read_rows(path: Path, *, delimiter: str = ",") -> list[dict[str, str]]:
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream, delimiter=delimiter))
    if not rows:
        raise ValueError(f"No data rows in {path}")
    return rows


def required_float(row: Mapping[str, str], field: str, source: Path) -> float:
    value = row.get(field)
    if value in (None, ""):
        raise ValueError(f"Missing {field!r} in {source}: {row}")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"Non-finite {field!r} in {source}: {row}")
    return result


def normalize_row(
    row: Mapping[str, str],
    field_map: Mapping[str, str],
    source: Path,
) -> dict[str, float]:
    return {
        field: required_float(row, source_field, source)
        for field, source_field in field_map.items()
    }


def copy_source(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_local_rows(runs_root: Path) -> tuple[list[dict[str, str]], dict[str, Path]]:
    rows: list[dict[str, str]] = []
    source_paths: dict[str, Path] = {}
    for code, family in LOCAL_SCENARIOS.items():
        path = (
            runs_root
            / family
            / "test"
            / "eval_out"
            / "aggregations"
            / "agg_per_baseline.csv"
        )
        source_paths[family] = path
        for source_row in read_rows(path):
            row = dict(source_row)
            row["pdd_code"] = code
            row["scenario_family"] = family
            rows.append(row)
    return rows, source_paths


def load_scenario_matrix(
    local_rows: list[dict[str, str]],
    local_description: Path,
    external_path: Path,
    ft_path: Path,
) -> list[dict[str, str | float]]:
    external_rows = read_rows(external_path, delimiter="\t")
    ft_rows = read_rows(ft_path)

    local_lookup = {
        (row["pdd_code"], row["baseline"]): row
        for row in local_rows
    }
    external_lookup = {
        (row["pdd"], row["policy"]): row
        for row in external_rows
    }
    ft_lookup = {row["pdd_code"]: row for row in ft_rows}

    matrix: list[dict[str, str | float]] = []
    for policy in POLICIES:
        seen_codes: set[str] = set()
        for code in ALL_CODES:
            if policy.kind == "ours":
                raw = ft_lookup.get(code)
                if raw is None:
                    raise ValueError(f"PlanT-2-FT is missing scenario {code} in {ft_path}")
                values = normalize_row(raw, LOCAL_FIELD_MAP, ft_path)
                source_kind = "plant2_ft"
            else:
                raw = (
                    local_lookup.get((code, policy.local_name or ""))
                    if policy.local_name
                    else None
                )
                if raw is not None:
                    values = normalize_row(raw, LOCAL_FIELD_MAP, local_description)
                    source_kind = "local"
                else:
                    raw = (
                        external_lookup.get((code, policy.external_name or ""))
                        if policy.external_name
                        else None
                    )
                    if raw is None:
                        raise ValueError(
                            f"Missing ({code}, {policy.key}) in both baseline sources"
                        )
                    values = normalize_row(raw, EXTERNAL_FIELD_MAP, external_path)
                    source_kind = "smirnova"
            seen_codes.add(code)
            matrix.append(
                {
                    "policy_key": policy.key,
                    "policy_display": policy.display,
                    "family": policy.family,
                    "kind": policy.kind,
                    "group": CODE_TO_GROUP[code],
                    "pdd_code": code,
                    "source": source_kind,
                    **values,
                }
            )
        if seen_codes != set(ALL_CODES):
            raise AssertionError(f"{policy.key}: scenario coverage mismatch")

    expected = len(POLICIES) * len(ALL_CODES)
    if len(matrix) != expected:
        raise AssertionError(f"Expected {expected} matrix rows, found {len(matrix)}")
    return matrix


def weighted_mean(rows: Iterable[Mapping[str, str | float]], field: str) -> float:
    rows = list(rows)
    denominator = sum(float(row["n"]) for row in rows)
    if denominator <= 0:
        raise ValueError(f"No observations for {field}")
    return sum(float(row[field]) * float(row["n"]) for row in rows) / denominator


def summarize(matrix: list[dict[str, str | float]]) -> list[dict[str, str | float]]:
    by_policy: dict[str, list[dict[str, str | float]]] = defaultdict(list)
    for row in matrix:
        by_policy[str(row["policy_key"])].append(row)

    summaries: list[dict[str, str | float]] = []
    for policy in POLICIES:
        rows = by_policy[policy.key]
        if {str(row["pdd_code"]) for row in rows} != set(ALL_CODES):
            raise ValueError(f"{policy.key} does not cover all 29 scenarios")
        result: dict[str, str | float] = {
            "policy_key": policy.key,
            "policy_display": policy.display,
            "family": policy.family,
            "kind": policy.kind,
            "n_episodes": sum(float(row["n"]) for row in rows),
        }
        for field in CONVENTIONAL_FIELDS:
            result[field] = weighted_mean(rows, field)
        result["sign_compliance"] = mean(
            float(row["sign_compliance"]) for row in rows
        )
        result["destination"] = mean(float(row["destination"]) for row in rows)
        sr_values = [float(row["sr_dest"]) for row in rows]
        for group, codes in GROUPS:
            values = [
                float(row["sr_dest"])
                for row in rows
                if str(row["pdd_code"]) in codes
            ]
            result[f"sr_dest_{group.lower()}"] = mean(values)
        result["sr_dest_overall"] = mean(sr_values)
        result["sr_dest_std"] = stdev(sr_values)
        result["sr_dest_min"] = min(sr_values)
        result["sr_dest_max"] = max(sr_values)
        summaries.append(result)
    return summaries


def write_tsv(path: Path, rows: list[Mapping[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def rounded_rows(
    rows: list[dict[str, str | float]],
) -> list[dict[str, str | float]]:
    output = []
    for row in rows:
        output.append(
            {
                key: round(value, 6) if isinstance(value, float) else value
                for key, value in row.items()
            }
        )
    return output


def metric_display_value(field: str, value: float) -> float:
    if field in {
        "comfort",
        "collision_rate",
        "sign_compliance",
        "destination",
        "sr_dest_priority",
        "sr_dest_speed",
        "sr_dest_obstacle",
        "sr_dest_routing",
        "sr_dest_overall",
    }:
        return 100.0 * value
    return value


def best_nonexpert(
    summaries: list[dict[str, str | float]],
) -> dict[str, float]:
    candidates = [row for row in summaries if row["kind"] in {"base", "ours"}]
    result = {}
    for field in (
        "efficiency",
        "comfort",
        "collision_rate",
        "sign_compliance",
        "destination",
        "sr_dest_priority",
        "sr_dest_speed",
        "sr_dest_obstacle",
        "sr_dest_routing",
        "sr_dest_overall",
    ):
        values = [float(row[field]) for row in candidates]
        if field == "collision_rate":
            result[field] = min(values)
        elif field == "efficiency":
            result[field] = min(values, key=lambda value: abs(value - 100.0))
        else:
            result[field] = max(values)
    return result


def latex_value(field: str, value: float, best: Mapping[str, float], kind: str) -> str:
    shown = metric_display_value(field, value)
    text = f"{shown:.1f}"
    if kind in {"base", "ours"} and math.isclose(
        value, best[field], rel_tol=0.0, abs_tol=5e-7
    ):
        return rf"\textbf{{{text}}}"
    return text


def render_latex_table(
    summaries: list[dict[str, str | float]],
    destination: Path,
) -> None:
    best = best_nonexpert(summaries)
    by_key = {str(row["policy_key"]): row for row in summaries}
    lines = [
        r"\begin{table*}[t]",
        r"\centering",
        r"\scriptsize",
        r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lccc@{\hspace{6pt}}cc@{\hspace{6pt}}ccccc@{}}",
        r"\toprule",
        r"& \multicolumn{3}{c}{\textbf{Conventional diagnostics}}",
        r"& \multicolumn{2}{c}{\textbf{Rule outcomes (\%)}}",
        r"& \multicolumn{5}{c}{\textbf{SCD (\%)}} \\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-6}\cmidrule(lr){7-11}",
        r"\textbf{Planner}",
        r"& \makecell{\textbf{Rel. speed}\\(\%)}",
        r"& \makecell{\textbf{Comf.}\\(\%) $\uparrow$}",
        r"& \makecell{\textbf{Crash}\\(\%) $\downarrow$}",
        r"& \makecell{\textbf{SC}\\$\uparrow$}",
        r"& \makecell{\textbf{Dest}\\$\uparrow$}",
        r"& \makecell{\textbf{Priority}\\$\uparrow$}",
        r"& \makecell{\textbf{Speed}\\$\uparrow$}",
        r"& \makecell{\textbf{Obstacle}\\$\uparrow$}",
        r"& \makecell{\textbf{Routing}\\$\uparrow$}",
        r"& \makecell{\textbf{Overall}\\$\uparrow$} \\",
        r"\midrule",
    ]
    metric_fields = (
        "efficiency",
        "comfort",
        "collision_rate",
        "sign_compliance",
        "destination",
        "sr_dest_priority",
        "sr_dest_speed",
        "sr_dest_obstacle",
        "sr_dest_routing",
        "sr_dest_overall",
    )
    blocks = (
        ("Standard baselines", [p for p in POLICIES if p.kind == "base"]),
        ("Our fine-tuned policy", [p for p in POLICIES if p.kind == "ours"]),
        (
            "Privileged rule-compliant baselines",
            [p for p in POLICIES if p.kind == "rule"],
        ),
    )
    for block_idx, (title, policies) in enumerate(blocks):
        if block_idx:
            # A soft gray hairline rule (0.3pt, black!25).
            # We use \noalign with \color{\hrule} because booktabs \midrule
            # hardcodes a black \hrule and screen PDF viewers snap black <0.5pt rules to 1px.
            lines.append(
                r"\noalign{\vskip 2.5pt{\color{black!25}\hrule height 0.35pt}\vskip 2.5pt}"
            )
        lines.append(
            rf"\multicolumn{{11}}{{l}}{{\textit{{{title}}}}} \\[-1pt]"
        )
        for policy in policies:
            row = by_key[policy.key]
            cells = [
                latex_value(field, float(row[field]), best, policy.kind)
                for field in metric_fields
            ]
            planner = policy.latex
            if policy.kind == "ours":
                planner = rf"\rowcolor{{black!6}} {planner}"
            lines.append(planner + " & " + " & ".join(cells) + r" \\")
    lines.extend(
        [
            r"\bottomrule",
            r"\end{tabular*}",
            r"\caption{\textbf{Closed-loop evaluation on all 29 scenario types.} "
            r"Relative speed is ego speed as a percentage of nearby-traffic speed; "
            r"100 is parity. Comf.: Comfort; SC: target-sign compliance; Dest: "
            r"destination arrival; SCD: their joint success (Eq.~\ref{eq:scd}). "
            r"Conventional diagnostics are episode-weighted; SC, Dest, and SCD "
            r"are macro-averaged over scenario types. RC is omitted because its "
            r"route-relative conventions disagree across sources; DS is omitted "
            r"because it is computed from RC. Bold denotes the best result among "
            r"standard baselines and PlanT-2-FT (for relative speed, closest to "
            r"100). Superscript $e$ denotes privileged rule-enforcing references.}",
            r"\label{tab:metrics}",
            r"\end{table*}",
        ]
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def set_plot_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["STIXGeneral", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 8.3,
            "axes.labelsize": 9.5,
            "axes.edgecolor": "#A9A7A2",
            "axes.linewidth": 0.7,
            "axes.axisbelow": True,
            "xtick.color": "#3F3F3D",
            "ytick.color": "#252522",
            "text.color": "#252522",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def forest_label(policy: PolicySpec) -> str:
    labels = {
        "idm_rule": r"IDM$^{e}$",
        "idm_rule_s1": r"IDM$^{e}$-$s_1$",
        "idm_rule_s2": r"IDM$^{e}$-$s_2$",
        "idm_rule_s3": r"IDM$^{e}$-$s_3$",
        "idm_rule_s4": r"IDM$^{e}$-$s_4$",
        "ppo_rule": r"PPO$^{e}$",
        "carl_rule": r"CaRL$^{e}$",
        "plant2_rule": r"PlanT-2$^{e}$",
        "idm_s1": r"IDM-$s_1$",
        "idm_s2": r"IDM-$s_2$",
        "idm_s3": r"IDM-$s_3$",
        "idm_s4": r"IDM-$s_4$",
    }
    return labels.get(policy.key, policy.display)


def render_forest_plot(
    summaries: list[dict[str, str | float]],
    output_dir: Path,
) -> tuple[Path, Path]:
    set_plot_style()
    by_key = {str(row["policy_key"]): row for row in summaries}
    ordered = list(POLICIES)
    y_values = list(reversed(range(len(ordered))))

    fig, ax = plt.subplots(figsize=(7.15, 4.55), facecolor="white")
    fig.subplots_adjust(left=0.205, right=0.975, top=0.805, bottom=0.145)

    # Subtle structural bands separate the three evaluation regimes.
    ax.axhspan(8.5, 16.5, color="#F7F7F5", zorder=0)
    ax.axhspan(0.5, 8.5, color="#EEF1F3", alpha=0.55, zorder=0)
    ax.axhspan(-0.5, 0.5, color="#FFF7E6", zorder=0)
    ax.axhline(8.5, color="#B8B7B2", linewidth=0.75, zorder=1)
    ax.axhline(0.5, color="#B8B7B2", linewidth=0.75, zorder=1)

    marker_for_kind = {"base": "o", "rule": "D", "ours": "*"}
    for y, policy in zip(y_values, ordered):
        row = by_key[policy.key]
        center = 100.0 * float(row["sr_dest_overall"])
        spread = 100.0 * float(row["sr_dest_std"])
        lower = center - max(0.0, center - spread)
        upper = min(100.0, center + spread) - center
        is_base = policy.kind == "base"
        ax.errorbar(
            center,
            y,
            xerr=[[lower], [upper]],
            fmt=marker_for_kind[policy.kind],
            markersize=5.2 if policy.kind != "ours" else 8.2,
            markerfacecolor="white" if is_base else COLORS[policy.family],
            markeredgecolor=COLORS[policy.family],
            markeredgewidth=1.15,
            ecolor=COLORS[policy.family],
            elinewidth=1.35,
            capsize=2.1,
            capthick=1.0,
            alpha=0.96,
            zorder=4,
        )
        ax.text(
            101.0,
            y,
            f"{center:.1f}",
            ha="left",
            va="center",
            fontsize=7.6,
            fontweight="bold" if policy.kind == "ours" else "normal",
            color="#343431",
            clip_on=False,
        )

    ax.set_yticks(y_values, [forest_label(policy) for policy in ordered])
    ax.tick_params(axis="y", length=0, pad=6, labelsize=8.1)
    ax.set_xlim(0, 105)
    ax.set_xticks((0, 20, 40, 60, 80, 100))
    ax.set_xlabel("SCD across 29 scenario types: mean ± SD (%)", labelpad=7)
    ax.xaxis.grid(True, color="#D8D7D2", linewidth=0.65)
    ax.yaxis.grid(False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)

    family_handles = [
        Patch(facecolor=color, edgecolor="none", label=family)
        for family, color in COLORS.items()
    ]
    kind_handles = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="#66645F",
            markerfacecolor="white",
            markeredgewidth=1.1,
            linestyle="none",
            label="Base",
        ),
        Line2D(
            [0],
            [0],
            marker="D",
            color="#66645F",
            markerfacecolor="#66645F",
            linestyle="none",
            label=r"Rule-compliant ($e$)",
        ),
        Line2D(
            [0],
            [0],
            marker="*",
            markersize=8,
            color="#66645F",
            markerfacecolor="#66645F",
            linestyle="none",
            label="Fine-tuned",
        ),
    ]
    fig.legend(
        handles=family_handles + kind_handles,
        loc="upper center",
        bbox_to_anchor=(0.59, 0.985),
        ncol=7,
        frameon=False,
        fontsize=7.8,
        handlelength=1.25,
        columnspacing=1.15,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "sr_dest_forest_plot.png"
    pdf_path = output_dir / "sr_dest_forest_plot.pdf"
    metadata = {
        "Title": "SCD mean and standard deviation across 29 scenario types",
        "Creator": "TrafficSignBench ICRA results builder",
    }
    fig.savefig(
        png_path,
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata={"Title": metadata["Title"]},
    )
    fig.savefig(
        pdf_path,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.05,
        metadata=metadata,
    )
    plt.close(fig)
    return png_path, pdf_path


def render_figure_tex(destination: Path) -> None:
    text = r"""\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{imgs/sr_dest_forest_plot.pdf}
\caption{\textbf{Compliance and cross-rule robustness.}
Each point is the macro-average SCD over all 29 scenario types; whiskers
show one sample standard deviation across scenario types (clipped to
$[0,100]\%$). Hollow circles denote base planners, filled diamonds their
rule-compliant counterparts, and the star denotes PlanT-2-FT. Lower dispersion
indicates more consistent behavior across heterogeneous traffic rules.}
\label{fig:sr_dest_forest}
\end{figure*}
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def crop_icon(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    alpha = rgba.getchannel("A")
    if alpha.getextrema() != (255, 255):
        bbox = alpha.getbbox()
    else:
        rgb = rgba.convert("RGB")
        difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, "white"))
        bbox = difference.convert("L").point(lambda value: 255 if value > 8 else 0).getbbox()
    return rgba.crop(bbox) if bbox else rgba


# Keep icons as rasters in the PDF. Matplotlib's OffsetImage always resamples
# to on-page pixel size before embedding, so zoomed PDFs look soft.
# AxesImage with interpolation="none" keeps the bitmap and scales it with a
# PDF transform instead. Always scale source PNGs up to this canvas; thumbnail()
# left small assets (blocked road, one-way) letterboxed and looking tiny.
ICON_CANVAS_PX = 512
ICON_Y0 = 0.08
ICON_Y1 = 0.92
ICON_HEIGHT = ICON_Y1 - ICON_Y0
ICON_BASE_HALF_WIDTH = 0.28
ICON_MAX_HALF_WIDTH = 0.48
ONE_WAY_CODES = {"5.7.1", "5.7.2"}
PORTRAIT_CODES = {"5.21", "5.31"}


def scenario_icon(repo: Path, code: str) -> Image.Image:
    """Return a high-res icon cropped to content with native aspect preserved.

    Square/circular signs fill a square canvas. Wide (one-way) and tall
    (residential / speed-zone) plates keep their native aspect so the display
    extent can match the physical sign instead of stretching it into a square.
    """
    filename = SCENARIO_ICON_FILES[code]
    if code in {"3.24", "4.3", "5.21", "5.31"}:
        image = Image.open(repo / "traffic_bench" / "signs" / "icons" / filename)
    else:
        image = Image.open(repo / "paper" / "imgs" / "signs" / filename)
    image = crop_icon(image)
    width, height = image.size
    aspect = width / max(height, 1)

    if (
        aspect >= 1.35
        or aspect <= 1 / 1.35
        or code in ONE_WAY_CODES
        or code in PORTRAIT_CODES
    ):
        target_h = ICON_CANVAS_PX
        target_w = max(1, int(round(target_h * aspect)))
    else:
        target_w = target_h = ICON_CANVAS_PX

    fitted = image.resize((target_w, target_h), Image.Resampling.LANCZOS)
    return fitted.convert("RGBA")


def icon_extent(
    column_index: int,
    image: Image.Image,
    code: str,
) -> tuple[float, float, float, float]:
    """Return imshow extent that preserves native aspect on the icon axis."""
    width, height = image.size
    aspect = width / max(height, 1)
    box_height = ICON_HEIGHT / 2.0 if code in ONE_WAY_CODES else ICON_HEIGHT
    y0 = 0.5 - box_height / 2.0
    y1 = 0.5 + box_height / 2.0
    half_width = min(
        ICON_MAX_HALF_WIDTH,
        aspect * box_height * ICON_BASE_HALF_WIDTH / ICON_HEIGHT,
    )
    return (
        column_index - half_width,
        column_index + half_width,
        y0,
        y1,
    )


def wilson_interval(rate: float, n: float, z: float = 1.959963984540054) -> tuple[float, float]:
    """Return a two-sided 95% Wilson interval for a binary episode rate."""
    if n <= 0:
        raise ValueError("Wilson interval requires n > 0")
    denominator = 1.0 + z * z / n
    center = (rate + z * z / (2.0 * n)) / denominator
    half_width = (
        z
        * math.sqrt(rate * (1.0 - rate) / n + z * z / (4.0 * n * n))
        / denominator
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def policy_marker(policy: PolicySpec) -> str:
    return "o" if policy.kind == "base" else "s"


def style_scenario_axis(axis: mpl.axes.Axes) -> None:
    axis.set_xlim(-0.52, len(ALL_CODES) - 0.48)
    axis.set_ylim(0, 118)
    axis.set_yticks((0, 25, 50, 75, 100))
    axis.set_ylabel("SCD (%)", fontsize=10.5)
    axis.set_xticks([])
    axis.tick_params(axis="y", labelsize=8.5, length=2.5, width=0.6)
    axis.yaxis.grid(True, color="#D9D9D5", linewidth=0.55)
    axis.xaxis.grid(False)
    axis.spines["top"].set_visible(False)
    axis.spines["right"].set_visible(False)
    axis.spines["bottom"].set_color("#AAA9A5")
    axis.spines["left"].set_color("#AAA9A5")
    axis.spines["bottom"].set_linewidth(0.6)
    axis.spines["left"].set_linewidth(0.6)

    offset = 0
    for group_index, (_, codes) in enumerate(GROUPS):
        end = offset + len(codes)
        if group_index % 2:
            axis.axvspan(offset - 0.5, end - 0.5, color="#F6F6F4", zorder=0)
        if end < len(ALL_CODES):
            axis.axvline(end - 0.5, color="#B5B4AF", linewidth=0.8, zorder=1)
        offset = end


def plot_policy_panel(
    axis: mpl.axes.Axes,
    policies: list[PolicySpec],
    lookup: Mapping[tuple[str, str], Mapping[str, str | float]],
) -> None:
    count = len(policies)
    offsets = [(index - (count - 1) / 2.0) * 0.068 for index in range(count)]
    handles: list[Line2D] = []
    for policy, x_offset in zip(policies, offsets):
        centers: list[float] = []
        lower_errors: list[float] = []
        upper_errors: list[float] = []
        for code in ALL_CODES:
            row = lookup[(policy.key, code)]
            rate = float(row["sr_dest"])
            low, high = wilson_interval(rate, float(row["n"]))
            centers.append(100.0 * rate)
            lower_errors.append(100.0 * max(0.0, rate - low))
            upper_errors.append(100.0 * max(0.0, high - rate))

        marker = policy_marker(policy)
        color = SERIES_COLORS[policy.key]
        if policy.kind == "base":
            marker_size = 2.6
            edge_color = color
            edge_width = 0.25
            error_width = 0.42
            cap_size = 0.8
            cap_width = 0.36
            opacity = 0.68
            z_order = 2
        elif policy.kind == "rule":
            marker_size = 3.35
            edge_color = "#282825"
            edge_width = 0.35
            error_width = 0.82
            cap_size = 1.25
            cap_width = 0.68
            opacity = 0.96
            z_order = 3
        else:
            marker_size = 4.5
            edge_color = "#B13B9D"
            edge_width = 0.5
            error_width = 1.0
            cap_size = 1.45
            cap_width = 0.82
            opacity = 1.0
            z_order = 4
        axis.errorbar(
            [index + x_offset for index in range(len(ALL_CODES))],
            centers,
            yerr=[lower_errors, upper_errors],
            fmt=marker,
            markersize=marker_size,
            markerfacecolor=color,
            markeredgecolor=edge_color,
            markeredgewidth=edge_width,
            ecolor=color,
            elinewidth=error_width,
            capsize=cap_size,
            capthick=cap_width,
            alpha=opacity,
            linestyle="none",
            zorder=z_order,
        )
        handles.append(
            Line2D(
                [0],
                [0],
                marker=marker,
                markersize=5.8 if policy.kind == "ours" else 4.8,
                markerfacecolor=color,
                markeredgecolor=edge_color,
                markeredgewidth=edge_width,
                color="none",
                alpha=opacity,
                label=scenario_legend_label(policy),
            )
        )

    axis.legend(
        handles=handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 1.0),
        ncol=count,
        frameon=False,
        fontsize=10.5,
        handletextpad=0.25,
        columnspacing=0.65,
        borderaxespad=0.0,
    )


def scenario_legend_label(policy: PolicySpec) -> str:
    """Collapse IDM ego-variants to a short family name in the scenario legend."""
    if policy.family == "IDM" and policy.kind == "base":
        return "IDM"
    if policy.family == "IDM" and policy.kind == "rule":
        return r"IDM$^{e}$"
    return forest_label(policy)


def best_idm_policy(
    policies: list[PolicySpec],
    lookup: Mapping[tuple[str, str], Mapping[str, str | float]],
) -> PolicySpec:
    return max(
        (policy for policy in policies if policy.family == "IDM"),
        key=lambda policy: mean(
            float(lookup[(policy.key, code)]["sr_dest"]) for code in ALL_CODES
        ),
    )


def render_scenario_forest_plot(
    matrix: list[dict[str, str | float]],
    repo: Path,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Render per-scenario SCD means and episode-level confidence intervals."""
    set_plot_style()
    lookup = {
        (str(row["policy_key"]), str(row["pdd_code"])): row
        for row in matrix
    }
    base_candidates = [policy for policy in POLICIES if policy.kind == "base"]
    rule_candidates = [policy for policy in POLICIES if policy.kind == "rule"]
    standard = [best_idm_policy(base_candidates, lookup)]
    standard += [policy for policy in base_candidates if policy.family != "IDM"]
    privileged = [best_idm_policy(rule_candidates, lookup)]
    privileged += [policy for policy in rule_candidates if policy.family != "IDM"]
    ours = [policy for policy in POLICIES if policy.kind == "ours"]
    visible_policies = standard + ours + privileged

    figure = plt.figure(figsize=(12.2, 3.2), facecolor="white")
    grid = figure.add_gridspec(
        2,
        1,
        height_ratios=(1.0, 0.105),
        left=0.064,
        right=0.995,
        bottom=0.055,
        top=0.985,
        hspace=0.015,
    )
    forest_ax = figure.add_subplot(grid[0, 0])
    icon_ax = figure.add_subplot(grid[1, 0], sharex=forest_ax)

    style_scenario_axis(forest_ax)
    plot_policy_panel(forest_ax, visible_policies, lookup)

    icon_ax.set_xlim(-0.52, len(ALL_CODES) - 0.48)
    icon_ax.set_ylim(0.0, 1.0)
    icon_ax.axis("off")
    for column_index, code in enumerate(ALL_CODES):
        # interpolation="none" is required for PDF: otherwise Matplotlib
        # downsamples icons to ~20px before embedding and zoom looks soft.
        icon = scenario_icon(repo, code)
        icon_ax.imshow(
            np.asarray(icon),
            extent=icon_extent(column_index, icon, code),
            aspect="auto",
            interpolation="none",
            zorder=2,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    png_path = output_dir / "per_scenario_sr_dest_forest.png"
    pdf_path = output_dir / "per_scenario_sr_dest_forest.pdf"
    title = "Per-scenario SCD with 95% confidence intervals"
    metadata = {"Title": title, "Creator": "TrafficSignBench ICRA results builder"}
    figure.savefig(
        png_path,
        dpi=600,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata={"Title": title},
    )
    figure.savefig(
        pdf_path,
        facecolor="white",
        bbox_inches="tight",
        pad_inches=0.04,
        metadata=metadata,
    )
    plt.close(figure)
    return png_path, pdf_path


def render_scenario_forest_tex(destination: Path) -> None:
    text = r"""\begin{figure*}[t]
\centering
\includegraphics[width=\textwidth]{imgs/per_scenario_sr_dest_forest.pdf}
\caption{\textbf{Per-scenario traffic-rule compliance.}
Points show SCD across 29 scenario types; whiskers are 95\% Wilson
confidence intervals over episodes. Circles denote standard baselines, squares
denote privileged rule-compliant baselines (superscript $e$), and the pink
square denotes PlanT-2-FT. For visual clarity, only the strongest of the five
IDM variants by overall SCD is shown within each regime.}
\label{fig:per_scenario_sr_dest}
\end{figure*}
"""
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")


def render_data_readme(
    destination: Path,
    source_records: list[dict[str, str]],
    ft_tag: str,
) -> None:
    lines = [
        "# ICRA 2027 result inputs",
        "",
        "This directory is regenerated by `scripts/build_icra_results.py`.",
        "",
        "Aggregation contract:",
        "- conventional diagnostics: episode-weighted across scenario types;",
        "- SC, Dest, and grouped/overall SCD: unweighted macro averages over scenario types;",
        "- forest whiskers: sample SD (ddof=1) of the 29 scenario-level SCD rates;",
        "- per-scenario whiskers: 95% Wilson intervals over binary episode outcomes;",
        "- table values intentionally omit confidence intervals.",
        "",
        f"PlanT-2-FT checkpoint: `{ft_tag}`.",
        "",
        "Copied immutable inputs and SHA-256 checksums are listed in `source_manifest.tsv`.",
        "Derived tables are `per_scenario_metrics.tsv`, `main_table_metrics.tsv`, and",
        "`forest_plot_sr_dest.tsv`.",
        "",
        "The paired Dest--SC and family-balanced within-type metric analyses are",
        "regenerated by `scripts/plot_paired_metric_discordance.py`; derived",
        "statistics are `paired_dest_sc.tsv` and `metric_associations.tsv`.",
    ]
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo = args.repo_root.resolve()
    local_runs = args.local_runs.resolve()
    external_path = args.smirnova_table.resolve()
    ft_root = args.plant2_ft_root.resolve()
    ft_per_sign = ft_root / "agg_per_sign_baseline.csv"
    ft_overall = ft_root / "agg_per_baseline.csv"

    source_dir = args.data_dir / "sources"
    local_rows, local_source_paths = load_local_rows(local_runs)
    copied_sources = (
        (
            external_path,
            source_dir / "smirnova_v7_rl3_metrics.tsv",
            "smirnova_11_scenarios",
        ),
        (
            ft_per_sign,
            source_dir / "plant2_ft_per_sign_baseline.csv",
            "plant2_ft_29_scenarios",
        ),
        (
            ft_overall,
            source_dir / "plant2_ft_overall_baseline.csv",
            "plant2_ft_overall_audit",
        ),
    )
    source_records: list[dict[str, str]] = []
    for family, source in local_source_paths.items():
        if not source.is_file():
            raise FileNotFoundError(source)
        destination = source_dir / "local" / f"{family}.csv"
        copy_source(source, destination)
        source_records.append(
            {
                "role": f"local_{family}",
                "original_path": str(source),
                "copied_path": str(destination.relative_to(repo)),
                "sha256": sha256(destination),
            }
        )
    for source, destination, role in copied_sources:
        if not source.is_file():
            raise FileNotFoundError(source)
        copy_source(source, destination)
        source_records.append(
            {
                "role": role,
                "original_path": str(source),
                "copied_path": str(destination.relative_to(repo)),
                "sha256": sha256(destination),
            }
        )

    matrix = load_scenario_matrix(
        local_rows,
        local_runs,
        external_path,
        ft_per_sign,
    )
    for row in matrix:
        ci_low, ci_high = wilson_interval(float(row["sr_dest"]), float(row["n"]))
        row["sr_dest_ci95_lo"] = ci_low
        row["sr_dest_ci95_hi"] = ci_high
    summaries = summarize(matrix)
    matrix_fields = [
        "policy_key",
        "policy_display",
        "family",
        "kind",
        "group",
        "pdd_code",
        "source",
        "n",
        *CONVENTIONAL_FIELDS,
        "sign_compliance",
        "destination",
        "sr_dest",
        "sr_dest_ci95_lo",
        "sr_dest_ci95_hi",
    ]
    summary_fields = [
        "policy_key",
        "policy_display",
        "family",
        "kind",
        "n_episodes",
        *CONVENTIONAL_FIELDS,
        "sign_compliance",
        "destination",
        "sr_dest_priority",
        "sr_dest_speed",
        "sr_dest_obstacle",
        "sr_dest_routing",
        "sr_dest_overall",
        "sr_dest_std",
        "sr_dest_min",
        "sr_dest_max",
    ]
    forest_fields = [
        "policy_key",
        "policy_display",
        "family",
        "kind",
        "sr_dest_overall",
        "sr_dest_std",
        "sr_dest_min",
        "sr_dest_max",
    ]
    write_tsv(
        args.data_dir / "per_scenario_metrics.tsv",
        rounded_rows(matrix),
        matrix_fields,
    )
    write_tsv(
        args.data_dir / "main_table_metrics.tsv",
        rounded_rows(summaries),
        summary_fields,
    )
    write_tsv(
        args.data_dir / "forest_plot_sr_dest.tsv",
        rounded_rows(summaries),
        forest_fields,
    )
    write_tsv(
        args.data_dir / "source_manifest.tsv",
        source_records,
        ["role", "original_path", "copied_path", "sha256"],
    )

    table_path = args.paper_tables / "metrics.tex"
    render_latex_table(summaries, table_path)
    figure_paths = render_forest_plot(summaries, args.paper_images)
    figure_tex = args.paper_images / "sr_dest_forest_plot.tex"
    render_figure_tex(figure_tex)
    scenario_forest_paths = render_scenario_forest_plot(matrix, repo, args.paper_images)
    scenario_forest_tex = args.paper_images / "per_scenario_sr_dest_forest.tex"
    render_scenario_forest_tex(scenario_forest_tex)
    render_data_readme(
        args.data_dir / "README.md",
        source_records,
        ft_root.parent.name,
    )

    print(f"Validated {len(POLICIES)} policies x {len(ALL_CODES)} scenarios")
    print(f"Wrote {args.data_dir / 'main_table_metrics.tsv'}")
    print(f"Wrote {args.data_dir / 'per_scenario_metrics.tsv'}")
    print(f"Wrote {table_path}")
    for path in (
        *figure_paths,
        figure_tex,
        *scenario_forest_paths,
        scenario_forest_tex,
    ):
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
