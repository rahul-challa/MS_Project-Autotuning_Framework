#!/usr/bin/env python3
"""
Parameter evolution and comparison plots for the autotuning report.

Generates:
- report/images/param_trajectories.png  : value of each parameter vs tuning round
- report/images/param_match_bar.png     : predicted vs actual value per parameter

Data source: data/results/sequential_autotuning_results.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SEQ_RESULTS_PATH = REPO_ROOT / "data" / "results" / "sequential_autotuning_results.json"
IMAGES_DIR = REPO_ROOT / "report" / "images"


def _load_sequential_results() -> Dict:
    if not SEQ_RESULTS_PATH.exists():
        raise FileNotFoundError(
            f"Sequential autotuning results not found at {SEQ_RESULTS_PATH}.\n"
            "Run `autotune autotune` (or `autotune`) once before generating these plots."
        )
    with SEQ_RESULTS_PATH.open("r") as f:
        return json.load(f)


def plot_param_trajectories(data: Dict) -> Path:
    """Plot parameter value vs tuning round for each parameter."""
    tuning = data.get("tuning_info", {})
    param_order: List[str] = tuning.get("param_order", [])
    round_results: List[Dict] = tuning.get("round_results", [])

    if not param_order or not round_results:
        raise ValueError("tuning_info.param_order or tuning_info.round_results missing/empty.")

    # Build per-parameter series over rounds
    series: Dict[str, List[float]] = {p: [] for p in param_order}
    rounds: List[int] = []

    # round_results entries can contain 'round' and optionally 'restart'
    for rr in round_results:
        r = int(rr.get("round", len(rounds) + 1))
        if r not in rounds:
            rounds.append(r)
        cfg = rr.get("best_config") or rr.get("final_config") or {}
        for p in param_order:
            series[p].append(cfg.get(p))

    # Normalize lengths (in case of irregular logging)
    max_len = max(len(v) for v in series.values())
    for p in param_order:
        if len(series[p]) < max_len:
            series[p].extend([series[p][-1]] * (max_len - len(series[p])))
    if len(rounds) < max_len:
        rounds = list(range(1, max_len + 1))

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # 4x4 grid of subplots (for 16 parameters)
    n_params = len(param_order)
    n_rows, n_cols = 4, 4
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 10), sharex=True)
    axes = axes.flatten()

    for idx, p in enumerate(param_order):
        ax = axes[idx]
        ax.plot(rounds[: len(series[p])], series[p], marker="o", linewidth=1.5)
        ax.set_title(p, fontsize=9)
        ax.grid(True, alpha=0.2)

    for ax in axes[n_params:]:
        ax.axis("off")

    fig.suptitle("Parameter values across tuning rounds", fontsize=14)
    for ax in axes[-n_cols:]:
        ax.set_xlabel("Round")
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    out_path = IMAGES_DIR / "param_trajectories.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def plot_param_match_bar(data: Dict) -> Path:
    """Bar chart: predicted vs actual value per parameter."""
    best_config: Dict = data.get("best_config", {})
    actual_params: Dict = data.get("actual_parameters", {})

    # Use union of keys to show where actual is missing
    all_params = sorted(set(best_config.keys()) | set(actual_params.keys()))
    x = np.arange(len(all_params))

    pred_vals = [best_config.get(p, np.nan) for p in all_params]
    act_vals = [actual_params.get(p, np.nan) for p in all_params]

    width = 0.38
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(x - width / 2, act_vals, width, label="Actual")
    ax.bar(x + width / 2, pred_vals, width, label="Predicted")

    ax.set_xticks(x)
    ax.set_xticklabels(all_params, rotation=45, ha="right")
    ax.set_ylabel("Parameter value")
    ax.set_title("Predicted vs actual parameters (final configuration)")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.2)

    plt.tight_layout()
    out_path = IMAGES_DIR / "param_match_bar.png"
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return out_path


def main() -> int:
    data = _load_sequential_results()
    traj_path = plot_param_trajectories(data)
    bar_path = plot_param_match_bar(data)
    print(f"Wrote {traj_path}")
    print(f"Wrote {bar_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

